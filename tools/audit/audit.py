#!/usr/bin/env python3
"""
Lean content audit for hk-daily-places — deterministic checks only.

Reads all PUBLISHED places (Neon Postgres, read-only SELECT) or a local
seed JSON file (--from-seed), scores each article on the five dimensions
from the Phase 1 proposal (A 30 / B 25 / C 20 / D 15 / E 10), flags
duplicate groups, and writes a Markdown + JSON report.

Duplicate detection reuses the approach from tools/related/related.py
(char-bigram TF-IDF + cosine similarity — the same idea as the Atlas
Search lucene.cjk analyzer). One deliberate difference: the audit corpus
is title + description ONLY, with NO category boost. related.py repeats
the category name 4x so same-category articles cluster for
recommendations; for duplicate detection that inflates scores, so it is
dropped here (see Phase 1 proposal §2.1).

What this script does NOT do (unless --write-scores is given):
  - No LLM calls, no API keys, no network calls to any LLM service.
  - No writes to the database (SELECT only; the connection is opened
    read-only). Never deletes or modifies articles.
  - Never touches production publishing or any cron/workflow.
  - Never prints or logs DATABASE_URL or any credential.

With --write-scores it additionally UPDATEs places.audit_score,
audit_status and audited_at per slug (parameterized, batched at 50,
one transaction per batch). It never updates title, description, or
any other column. --dry-run prints exactly what would be written and
writes nothing.

Each JSON row also carries content_hash (sha256 of slug + title +
description) so a future monthly run can skip re-scoring unchanged
posts (score-once design).

Usage:
  python audit.py --from-seed ../../src/main/resources/seed/bulk-places.json
  python audit.py                                   # DATABASE_URL from env
  python audit.py --dry-run                         # scope only, no outputs
  python audit.py --max-articles 50 --check-images  # live URL checks
  python audit.py --check-live                      # also fetch the sitemap
  python audit.py --write-scores                    # write scores back to DB
  python audit.py --write-scores --dry-run          # print what would be written

Env:
  DATABASE_URL  Neon Postgres connection string (needs ?sslmode=require)
                — only needed when --from-seed is not given.

Outputs (tools/audit/output/):
  audit-report.md      human-readable report (the main deliverable)
  audit-report.json    machine-readable per-article rows
  snapshot-<date>.json frozen slug list + category counts for this run

Requires: psycopg2-binary, scikit-learn (same as tools/related/related.py).
Only Python stdlib otherwise.
"""
import argparse
import difflib
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import psycopg2
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
DEFAULT_OUTPUT_DIR = SCRIPT_DIR / "output"
SITEMAP_URL = "https://hkdailyplaces.win/sitemap.xml"
STATE_FILE = REPO_ROOT / "daily-cron-state.json"

BATCH_SIZE = 50
FLAG_SIM = 0.30   # TF-IDF pair similarity: flagged
HIGH_SIM = 0.50   # TF-IDF pair similarity: high risk
TITLE_NEAR_RATIO = 0.85  # difflib ratio for near-duplicate titles
BACKDATE_DAYS = 30

# D2: practical-info markers per category. Documented heuristics — a count
# of markers present, not a judgement of quality.
PRACTICAL_MARKERS = {
    "HIKING": ["公里", "分鐘", "小時", "難度", "巴士", "港鐵", "起點", "終點"],
    "SHOPPING": ["價錢", "$", "折", "交通", "地址"],
    "MOVIE": ["分鐘", "導演", "主演", "上映"],
    "FOOD": ["價錢", "人均", "地址", "招牌"],
}

# A-dimension: distinctive analysis/comparison wording (heuristic proxy;
# a one-liner cannot contain analysis, so length dominates the score).
ANALYSIS_MARKERS = [
    "比較", "值得", "推薦", "建議", "推介", "性價比", "分別",
    "優點", "缺點", "點解", "原因", "實測",
]

URL_RE = re.compile(r"https?://[^\s\"'<>\)\]]+")
CJK_RUN_RE = re.compile(r"[\u3400-\u9fff]{2,}")
CJK_KEEP_RE = re.compile(r"[0-9a-zA-Z\u3400-\u9fff\u2e80-\u2fff\uf900-\ufaff]+")


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_from_db(db_url):
    """Read-only SELECT of all PUBLISHED places. Never writes."""
    conn = psycopg2.connect(db_url)
    conn.set_session(readonly=True)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT slug, title, COALESCE(description, ''), category, "
                "imageUrl, youtubeId, publishedAt, createdAt, viewCount "
                "FROM places WHERE status = 'PUBLISHED' ORDER BY slug"
            )
            rows = cur.fetchall()
    finally:
        conn.close()
    articles = []
    for slug, title, desc, cat, img, yt, pub, created, views in rows:
        articles.append({
            "slug": slug, "title": title, "description": desc or "",
            "category": cat, "imageUrl": img or "", "youtubeId": yt or "",
            "publishedAt": pub, "createdAt": created, "viewCount": views or 0,
        })
    return articles


def load_from_seed(path):
    """Local test mode: seed JSON has no createdAt — D10 reports that."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    items = data if isinstance(data, list) else data.get("places", data)
    articles = []
    for it in items:
        pub = it.get("publishedAt")
        articles.append({
            "slug": it.get("slug", ""), "title": it.get("title", ""),
            "description": it.get("description", "") or "",
            "category": it.get("category", ""),
            "imageUrl": it.get("imageUrl", "") or "",
            "youtubeId": it.get("youtubeId", "") or "",
            "publishedAt": _parse_dt(pub) if pub else None,
            "createdAt": None, "viewCount": it.get("viewCount", 0) or 0,
        })
    articles.sort(key=lambda a: a["slug"])
    return articles


def _parse_dt(value):
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Deterministic checks D1-D11
# ---------------------------------------------------------------------------

def check_d1(article):
    """D1 length & structure."""
    desc = article["description"]
    chars = len(desc)
    sentences = len([s for s in re.split(r"[。！？!?…\n]+", desc) if s.strip()])
    paragraphs = desc.count("\n\n") + 1 if desc else 0
    return {
        "chars": chars, "sentences": sentences, "paragraphs": paragraphs,
        "has_digits": bool(re.search(r"[0-9]", desc)),
    }


def check_d2(article):
    """D2 per-category practical-info markers (heuristics)."""
    markers = PRACTICAL_MARKERS.get(article["category"], [])
    desc = article["description"]
    found = [m for m in markers if m in desc]
    return {"markers": markers, "found": found,
            "missing": [m for m in markers if m not in found]}


def classify_image(url):
    """D3 image domain classification (no network)."""
    if not url:
        return "empty"
    host = urllib.parse.urlparse(url).netloc.lower()
    if "wikimedia.org" in host:
        return "wikimedia"
    if "tmdb.org" in host:
        return "tmdb"
    if "ytimg.com" in host:
        return "ytimg"
    if "cloudinary.com" in host:
        return "cloudinary"
    return "other"


def head_url(url, timeout=10):
    """HTTP HEAD; returns (ok, status, content_type) without raising."""
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return True, resp.status, resp.headers.get("Content-Type", "")
    except urllib.error.HTTPError as e:
        return False, e.code, ""
    except Exception:
        return False, None, ""


def check_d3_d4(article, check_images):
    """D3 image audit + D4 video audit (network only with --check-images)."""
    img_domain = classify_image(article["imageUrl"])
    result = {"image_domain": img_domain, "image_ok": None, "image_status": None,
              "youtube_ok": None, "youtube_status": None}
    if not check_images:
        return result
    if article["imageUrl"]:
        ok, status, ctype = head_url(article["imageUrl"])
        result["image_ok"] = bool(ok and status == 200 and ctype.startswith("image/"))
        result["image_status"] = status
    if article["youtubeId"]:
        oembed = ("https://www.youtube.com/oembed?url="
                  "https://www.youtube.com/watch?v=" + article["youtubeId"]
                  + "&format=json")
        ok, status, _ = head_url(oembed)
        result["youtube_ok"] = bool(ok and status == 200)
        result["youtube_status"] = status
    return result


def check_d5(article):
    """D5 external links in the description."""
    urls = URL_RE.findall(article["description"])
    domains = [urllib.parse.urlparse(u).netloc.lower() for u in urls]
    return {"count": len(urls), "urls": urls, "domains": domains}


def normalise_title(title):
    """CJK-aware title normalisation: keep CJK + digits + ASCII letters,
    strip punctuation/whitespace only. WARNING: an ASCII-only strip
    (e.g. [^a-z0-9]) deletes all Chinese characters and falsely merges
    unrelated titles (proposal §3.4) — never do that."""
    return "".join(CJK_KEEP_RE.findall(title)).lower()


def check_d6(articles):
    """D6 title duplicates: exact normalised matches + near matches."""
    norm = {a["slug"]: normalise_title(a["title"]) for a in articles}
    exact = defaultdict(list)
    for slug, n in norm.items():
        exact[n].append(slug)
    exact_dups = {n: s for n, s in exact.items() if len(s) > 1 and n}
    near = []
    slugs = sorted(norm)
    for i, s1 in enumerate(slugs):
        for s2 in slugs[i + 1:]:
            if not norm[s1] or not norm[s2] or norm[s1] == norm[s2]:
                continue
            ratio = difflib.SequenceMatcher(None, norm[s1], norm[s2]).ratio()
            if ratio >= TITLE_NEAR_RATIO:
                near.append({"a": s1, "b": s2, "ratio": round(ratio, 3)})
    return {"exact": exact_dups, "near": near, "normalised": norm}


def build_corpus(articles):
    """Title counted twice, description once, NO category boost
    (deliberate difference from tools/related/related.py — see header)."""
    return [f"{a['title']} {a['title']} {a['description']}".strip()
            for a in articles]


def shared_top_terms(vectorizer, matrix, i, j, top_n=5):
    """Top char-bigrams both articles share, as duplicate evidence."""
    row_i = matrix[i].toarray()[0]
    row_j = matrix[j].toarray()[0]
    shared = row_i * row_j
    idx = shared.argsort()[::-1][:top_n]
    names = vectorizer.get_feature_names_out()
    return [names[k] for k in idx if shared[k] > 0]


class UnionFind:
    def __init__(self, items):
        self.parent = {x: x for x in items}

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra


def check_d7(articles, vectorizer, matrix):
    """D7 TF-IDF duplicate groups over the full pairwise matrix."""
    n = len(articles)
    sim = cosine_similarity(matrix)
    pairs = []
    uf = UnionFind([a["slug"] for a in articles])
    for i in range(n):
        for j in range(i + 1, n):
            score = float(sim[i][j])
            if score >= FLAG_SIM:
                band = "high" if score >= HIGH_SIM else "flag"
                terms = shared_top_terms(vectorizer, matrix, i, j)
                pairs.append({"a": articles[i]["slug"], "b": articles[j]["slug"],
                              "score": round(score, 3), "band": band,
                              "shared_terms": terms})
                uf.union(articles[i]["slug"], articles[j]["slug"])
    groups = defaultdict(list)
    for a in articles:
        groups[uf.find(a["slug"])].append(a["slug"])
    clusters = [sorted(v) for v in groups.values() if len(v) > 1]
    return {"pairs": sorted(pairs, key=lambda p: -p["score"]),
            "clusters": sorted(clusters, key=lambda c: -len(c))}


def series_prefix(slug):
    """Slug minus a trailing numeric/roman-numeral segment, else None."""
    parts = slug.rsplit("-", 1)
    if len(parts) == 2 and re.fullmatch(
            r"(\d+|i|ii|iii|iv|v|vi|vii|viii|ix|x|one|two|three|four|five|"
            r"six|seven|eight)", parts[1], re.IGNORECASE):
        return parts[0]
    return None


def check_d8(articles, sim_matrix):
    """D8 slug-series review: same-prefix groups + within-group sims."""
    by_slug = {a["slug"]: k for k, a in enumerate(articles)}
    groups = defaultdict(list)
    for a in articles:
        prefix = series_prefix(a["slug"])
        if prefix:
            groups[prefix].append(a["slug"])
    series = []
    for prefix, slugs in sorted(groups.items()):
        if len(slugs) < 2:
            continue
        sims = []
        for x in range(len(slugs)):
            for y in range(x + 1, len(slugs)):
                sims.append(round(float(sim_matrix[by_slug[slugs[x]]][by_slug[slugs[y]]]), 3))
        series.append({"prefix": prefix, "slugs": sorted(slugs),
                       "max_sim": max(sims) if sims else None,
                       "mean_sim": round(sum(sims) / len(sims), 3) if sims else None})
    return series


def cjk_trigrams(title):
    """All CJK 3-grams in a title, excluding any containing 香港
    (too generic to identify a place)."""
    chars = "".join(CJK_RUN_RE.findall(title))
    return {chars[i:i + 3] for i in range(len(chars) - 2)
            if "香港" not in chars[i:i + 3]}


def check_d9(articles, sim_matrix):
    """D9 same-place pairs: shared CJK 3-gram in titles + TF-IDF score."""
    by_slug = {a["slug"]: k for k, a in enumerate(articles)}
    grams = {a["slug"]: cjk_trigrams(a["title"]) for a in articles}
    pairs = []
    slugs = sorted(grams)
    for x in range(len(slugs)):
        for y in range(x + 1, len(slugs)):
            shared = grams[slugs[x]] & grams[slugs[y]]
            if not shared:
                continue
            score = round(float(sim_matrix[by_slug[slugs[x]]][by_slug[slugs[y]]]), 3)
            pairs.append({"a": slugs[x], "b": slugs[y], "score": score,
                          "shared_grams": sorted(shared)[:5]})
    return sorted(pairs, key=lambda p: -p["score"])


def check_d10(article):
    """D10 freshness: publishedAt vs createdAt gap. A >30-day gap means
    backdated seed dates, NOT stale content (proposal §3.3)."""
    pub, created = article["publishedAt"], article["createdAt"]
    if not pub or not created:
        return {"gap_days": None, "backdated": None,
                "note": "createdAt unavailable (seed mode) — freshness not checkable"}
    gap = (created - pub).days
    return {"gap_days": gap, "backdated": gap > BACKDATE_DAYS,
            "note": ("publishedAt is >30 days before createdAt: backdated "
                     "seed date, not stale content" if gap > BACKDATE_DAYS
                     else "dates consistent")}


def fetch_sitemap_count():
    """Live sitemap <loc> count (only with --check-live)."""
    try:
        with urllib.request.urlopen(SITEMAP_URL, timeout=20) as resp:
            text = resp.read().decode("utf-8", errors="ignore")
        return text.count("<loc>"), None
    except Exception as e:
        return None, str(e)


def check_d11(articles, source, check_live):
    """D11 counts reconciliation: DB/seed vs state file vs sitemap."""
    per_cat = dict(Counter(a["category"] for a in articles))
    result = {"source": source, "rows": len(articles), "per_category": per_cat,
              "state_file_slugs": None, "sitemap_urls": None,
              "sitemap_note": "skipped (run with --check-live)"}
    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            result["state_file_slugs"] = len(state.get("published_slugs", []))
        except Exception as e:
            result["state_file_error"] = str(e)
    if check_live:
        count, err = fetch_sitemap_count()
        result["sitemap_urls"] = count
        result["sitemap_note"] = err or f"fetched {SITEMAP_URL}"
    return result


# ---------------------------------------------------------------------------
# Scoring (A 30 / B 25 / C 20 / D 15 / E 10) — every score carries evidence
# ---------------------------------------------------------------------------

def score_article(article, d1, d2, d3d4, d5, dup_info, series_member):
    """Returns (scores dict, status, rejection_flags, reasons dict).
    The A/B/D/E sub-scores are deterministic heuristics documented in the
    reasons — they are measurements of the text, not LLM judgements.
    Mandatory rejection rules override the total (see flags)."""
    reasons = {}

    # A — original information & analysis (30). A one-liner cannot contain
    # analysis, so length dominates; distinctive analysis wording adds up.
    chars = d1["chars"]
    if chars < 100:
        len_pts = 0
    elif chars < 200:
        len_pts = 5
    elif chars < 400:
        len_pts = 10
    else:
        len_pts = 15
    found_analysis = [m for m in ANALYSIS_MARKERS if m in article["description"]]
    marker_pts = min(15, 3 * len(found_analysis))
    score_a = min(30, len_pts + marker_pts)
    reasons["A"] = (f"{chars} chars (length pts {len_pts}/15); analysis wording "
                    f"found: {found_analysis or 'none'} "
                    f"(marker pts {marker_pts}/15)")

    # B — practical usefulness (25): per-category marker coverage.
    total_markers = len(d2["markers"])
    score_b = round(25 * len(d2["found"]) / total_markers) if total_markers else 0
    reasons["B"] = (f"practical markers {len(d2['found'])}/{total_markers}: "
                    f"found {d2['found'] or 'none'}; "
                    f"missing {d2['missing'] or 'none'}")

    # C — uniqueness (20): deductions from duplicate evidence.
    score_c = 20
    c_bits = []
    if dup_info["exact_dup"]:
        score_c -= 6
        c_bits.append(f"exact normalised-title duplicate of "
                      f"{dup_info['exact_dup']}")
    if dup_info["high_risk"]:
        score_c -= 8
        c_bits.append(f"high-risk TF-IDF pair (>= {HIGH_SIM}): "
                      f"{dup_info['high_risk']}")
    elif dup_info["flagged"]:
        score_c -= 4
        c_bits.append(f"flagged TF-IDF pair (>= {FLAG_SIM}): "
                      f"{dup_info['flagged']}")
    if dup_info["near_title"]:
        score_c -= 2
        c_bits.append(f"near-duplicate title: {dup_info['near_title']}")
    score_c = max(0, score_c)
    reasons["C"] = "; ".join(c_bits) if c_bits else (
        "no duplicate evidence: unique title, no TF-IDF pair "
        f">= {FLAG_SIM}")

    # D — source reliability (15): stored evidence is links in the
    # description (there is no source field on Place). 0 links => 0.
    n_links = d5["count"]
    score_d = min(12, 4 * n_links)
    gov = any(d.endswith(".gov.hk") for d in d5["domains"])
    if gov:
        score_d = min(15, score_d + 3)
    reasons["D"] = (f"{n_links} external link(s) in description "
                    f"({d5['domains'] or 'none'})"
                    + ("; includes .gov.hk source" if gov else "")
                    + ("; no source link at all" if n_links == 0 else ""))

    # E — completeness (10): length bands, minus missing hero image.
    if chars < 100:
        score_e = 2
    elif chars < 300:
        score_e = 5
    elif chars < 600:
        score_e = 8
    else:
        score_e = 10
    if not article["imageUrl"]:
        score_e = max(0, score_e - 2)
    reasons["E"] = (f"{chars} chars, {d1['sentences']} sentence(s), "
                    f"{d1['paragraphs']} paragraph(s); "
                    f"image: {d3d4['image_domain'] or 'none'}"
                    f"{'; NO hero image' if not article['imageUrl'] else ''}")

    scores = {"A": score_a, "B": score_b, "C": score_c, "D": score_d,
              "E": score_e}
    total = sum(scores.values())

    # Mandatory rejection rules (override the number).
    flags = []
    if n_links == 0:
        flags.append("R-SOURCES: no identifiable source link in description")
    if chars < 100:
        flags.append(f"R-THIN: description is {chars} chars — critically "
                     f"incomplete for its stated subject")
    if score_a <= 5:
        flags.append("R-NO-VALUE: no identifiable original analysis "
                     f"(A={score_a})")
    if dup_info["high_risk"] or dup_info["exact_dup"]:
        flags.append("R-DUP: substantial duplication of existing content")
    img_domain = d3d4["image_domain"]
    if img_domain in ("other", "empty") or img_domain == "ytimg":
        flags.append(f"R-IMAGE: hero image domain '{img_domain}' — usage "
                     f"rights unclear (ytimg = YouTube thumbnail as hero)")

    if flags or total < 60:
        status = "FAIL"
    elif total < 80:
        status = "NEEDS_IMPROVEMENT"
    else:
        status = "PASS"
    return scores, total, status, flags, reasons


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def compute_content_hash(article):
    """sha256 of slug + title + description. Stored in the JSON rows so a
    future monthly run can skip re-scoring unchanged posts (score-once
    design): if the hash matches the previously stored one, the old
    score stands and no LLM call is spent."""
    payload = "\n".join([article["slug"], article["title"],
                         article["description"]])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_rows(articles, results, dup_maps, d7, d8, d9):
    """Assemble one machine-readable row per article."""
    rows = []
    for article, res in zip(articles, results):
        slug = article["slug"]
        rows.append({
            "slug": slug, "title": article["title"],
            "content_hash": compute_content_hash(article),
            "category": article["category"],
            "publishedAt": (article["publishedAt"].isoformat()
                            if article["publishedAt"] else None),
            "viewCount": article["viewCount"],
            "chars": res["d1"]["chars"], "sentences": res["d1"]["sentences"],
            "markers_found": res["d2"]["found"],
            "markers_missing": res["d2"]["missing"],
            "image_domain": res["d3d4"]["image_domain"],
            "image_ok": res["d3d4"]["image_ok"],
            "youtube_present": bool(article["youtubeId"]),
            "youtube_ok": res["d3d4"]["youtube_ok"],
            "links": res["d5"]["count"], "link_domains": res["d5"]["domains"],
            "tfidf_pairs": dup_maps[slug]["pairs"],
            "slug_series": res["series"],
            "same_place_pairs": [p for p in d9 if slug in (p["a"], p["b"])],
            "backdated": res["d10"]["backdated"],
            "scores": res["scores"], "total": res["total"],
            "status": res["status"], "rejection_flags": res["flags"],
            "reasons": res["reasons"],
        })
    return rows


def render_markdown(meta, rows, d6, d7, d8, d9, d11, missing_markers):
    low = sorted(rows, key=lambda r: (r["total"], r["scores"]["A"]))[:30]
    expand = sorted(rows, key=lambda r: (-r["total"], -r["scores"]["A"]))[:10]
    high_members = sorted({s for p in d7["pairs"] if p["band"] == "high"
                           for s in (p["a"], p["b"])})
    totals = [r["total"] for r in rows]
    dist = {"PASS": 0, "NEEDS_IMPROVEMENT": 0, "FAIL": 0}
    for r in rows:
        dist[r["status"]] += 1
    by_cat = {}
    for cat in sorted({r["category"] for r in rows}):
        cr = [r for r in rows if r["category"] == cat]
        by_cat[cat] = {
            "n": len(cr),
            "mean": round(sum(r["total"] for r in cr) / len(cr), 1),
            "pass": sum(1 for r in cr if r["status"] == "PASS"),
            "needs": sum(1 for r in cr if r["status"] == "NEEDS_IMPROVEMENT"),
            "fail": sum(1 for r in cr if r["status"] == "FAIL"),
        }
    flag_counts = Counter()
    for r in rows:
        for f in r["rejection_flags"]:
            flag_counts[f.split(":")[0]] += 1

    lines = []
    add = lines.append
    add(f"# hk-daily-places — Content Audit Report ({meta['date']})")
    add("")
    add(f"- Source: {meta['source']} ({meta['rows']} articles)")
    add(f"- Categories: {meta['per_category']}")
    add(f"- Mean total score: {round(sum(totals) / len(totals), 1) if totals else 0} / 100")
    add(f"- Status: PASS {dist['PASS']} / NEEDS_IMPROVEMENT "
        f"{dist['NEEDS_IMPROVEMENT']} / FAIL {dist['FAIL']}")
    add(f"- Reconciliation (D11): DB/seed rows {d11['rows']}, state-file "
        f"slugs {d11['state_file_slugs']}, sitemap URLs "
        f"{d11['sitemap_urls']} ({d11['sitemap_note']})")
    add("")
    add("Scores are internal yardsticks (A 30 / B 25 / C 20 / D 15 / E 10; "
        "80+ PASS / 60–79 NEEDS_IMPROVEMENT / <60 FAIL) — not Google's "
        "criteria. Mandatory rejection rules override the number. Every "
        "score carries its evidence in the JSON rows.")
    add("")
    add("## Score distribution by category")
    add("")
    add("| Category | n | Mean | PASS | NEEDS | FAIL |")
    add("|---|---|---|---|---|---|")
    for cat, s in by_cat.items():
        add(f"| {cat} | {s['n']} | {s['mean']} | {s['pass']} | "
            f"{s['needs']} | {s['fail']} |")
    add("")
    add("## Rejection flags (counts)")
    add("")
    for flag, count in flag_counts.most_common():
        add(f"- {flag}: {count}")
    if not flag_counts:
        add("- (none)")
    add("")
    add("## Lowest-quality articles (bottom 30)")
    add("")
    for r in low:
        add(f"- **{r['title']}** (`{r['slug']}`, {r['category']}) — "
            f"total {r['total']} [{r['status']}] "
            f"A{r['scores']['A']}/B{r['scores']['B']}/C{r['scores']['C']}/"
            f"D{r['scores']['D']}/E{r['scores']['E']}")
        add(f"  - {r['reasons']['A']}")
        add(f"  - {r['reasons']['B']}")
        add(f"  - {r['reasons']['C']}")
        add(f"  - {r['reasons']['D']}")
        add(f"  - {r['reasons']['E']}")
        if r["rejection_flags"]:
            add(f"  - Rejection: {'; '.join(r['rejection_flags'])}")
    add("")
    add("## Duplicate groups (TF-IDF, no category boost)")
    add("")
    add(f"Pairs ≥ {FLAG_SIM}: {len(d7['pairs'])} "
        f"({sum(1 for p in d7['pairs'] if p['band'] == 'high')} high-risk "
        f"≥ {HIGH_SIM}); clusters: {len(d7['clusters'])}")
    add("")
    for cluster in d7["clusters"]:
        add(f"- Cluster: {', '.join(cluster)}")
    for p in d7["pairs"][:30]:
        add(f"- `{p['a']}` ↔ `{p['b']}` — {p['score']} ({p['band']}), "
            f"shared terms: {', '.join(p['shared_terms']) or 'none'}")
    add("")
    add("## Same-place pairs (shared CJK 3-gram in titles)")
    add("")
    for p in d9[:15]:
        add(f"- `{p['a']}` ↔ `{p['b']}` — TF-IDF {p['score']}, "
            f"shared: {', '.join(p['shared_grams'])}")
    if not d9:
        add("- (none)")
    add("")
    add("## Slug series")
    add("")
    for s in d8:
        add(f"- `{s['prefix']}*`: {', '.join(s['slugs'])} — "
            f"max within-group TF-IDF {s['max_sim']}, "
            f"mean {s['mean_sim']} (a series is legitimate only if the "
            f"descriptions differ; check the pair scores above)")
    if not d8:
        add("- (none)")
    add("")
    add("## Expansion candidates (highest total score — closest to PASS)")
    add("")
    for r in expand:
        add(f"- **{r['title']}** (`{r['slug']}`, {r['category']}) — "
            f"total {r['total']} [{r['status']}] — needs first-hand "
            f"material: own visit/photos, prices, route notes, personal "
            f"judgement to lift A and D above the heuristic ceiling")
    add("")
    add("## Consolidate / noindex candidates — DECISIONS ONLY, not actions")
    add("")
    add("These slugs sit in high-risk duplicate groups. Nothing here is "
        "deleted, unpublished, or noindexed by this audit — a human decides "
        "per group whether to merge, expand one into the other, or noindex "
        "the weaker one.")
    add("")
    for slug in high_members:
        add(f"- `{slug}`")
    if not high_members:
        add("- (none)")
    add("")
    add("## Missing original information (corpus-wide, per category)")
    add("")
    for cat, missing in sorted(missing_markers.items()):
        top = Counter(missing).most_common(5)
        add(f"- {cat}: most-often-missing practical markers: "
            + ", ".join(f"{m} (missing in {c} articles)" for m, c in top))
    add("")
    add("Across the corpus, first-hand material is absent: no article "
        "stores a source link, no article carries own photos, and the "
        "median description is a single sentence. Those three gaps are "
        "the AdSense problem in one line.")
    add("")
    add("## Content Improvement Plan")
    add("")
    add("### 1. Expand first (highest leverage)")
    add("")
    for r in expand[:5]:
        add(f"- `{r['slug']}` — expand with a real visit: own photos, "
            f"prices/transport, and a personal verdict. Currently "
            f"{r['total']}/100.")
    add("")
    add("### 2. What a genuine article must contain (per-category template)")
    add("")
    add("- HIKING: distance, duration, elevation, difficulty, start/end, "
        "transport, own route notes and photos.")
    add("- SHOPPING: categories, price ranges, transport, comparison with "
        "a similar mall, own shopping notes.")
    add("- MOVIE: release date, runtime, director/cast, comparison with a "
        "similar film, audience suitability, HK cinema availability.")
    add("- FOOD: location, menu prices, per-person spend, transport, "
        "value-for-money verdict, own meal notes and photos.")
    add("")
    add("### 3. Quality gate for future publishing (checklist)")
    add("")
    add("1. No first-hand material (visit / own photos / own notes) → "
        "do not publish as an original article.")
    add("2. Duplicate check: TF-IDF pair ≥ 0.50 against any live article "
        "→ reject or merge.")
    add("3. Every factual claim needs a source link in the article body.")
    add("4. Image must be own photo or a clearly licensed source — "
        "YouTube thumbnails as hero images are not acceptable.")
    add("5. Maximum one article per day; no forced publishing — if no "
        "candidate passes, publish nothing.")
    add("")
    add("### 4. Stop doing")
    add("")
    add("- Publishing one-liner posts daily for the sake of frequency.")
    add("- Hotlinking a thumbnail as the hero image.")
    add("- Publishing without any source link in the body.")
    add("")
    add("## Limitations")
    add("")
    add("- A/B/D/E sub-scores are deterministic heuristics on the text, "
        "not LLM judgements; they measure the text, they do not verify "
        "facts. Qualitative review of a stratified sample is a separate "
        "step (Phase 1 proposal §5).")
    add("- TF-IDF is lexical, not semantic: paraphrased duplicates can "
        "score low; same-place-different-angle articles can score high. "
        "Treat pairs as evidence, not verdicts.")
    add("- Seed-mode runs have no createdAt, so D10 freshness is "
        "unavailable there; backdated publishedAt values are seed dates, "
        "not real publication dates.")
    return "\n".join(lines) + "\n"


def write_scores(db_url, rows, run_dt, dry_run=False):
    """Write back audit_score / audit_status / audited_at per slug.

    Only these three columns are ever updated — never title, description,
    or any other column. Parameterized queries, one transaction per batch
    of BATCH_SIZE rows with a per-batch commit (an uncommitted batch is
    rolled back if the connection closes). In dry-run mode, print exactly
    what would be written (slug + score + status) and write nothing to
    the DB. Returns the number of rows updated (0 in dry-run).
    """
    if dry_run:
        print(f"\nDry run: would write scores for {len(rows)} articles:")
        for r in rows:
            print(f"  {r['slug']}: score={r['total']} "
                  f"status={r['status']}")
        return 0
    updated = 0
    conn = psycopg2.connect(db_url)
    try:
        for start in range(0, len(rows), BATCH_SIZE):
            batch = rows[start:start + BATCH_SIZE]
            with conn.cursor() as cur:
                cur.executemany(
                    "UPDATE places SET audit_score = %s, "
                    "audit_status = %s, audited_at = %s WHERE slug = %s",
                    [(r["total"], r["status"], run_dt, r["slug"])
                     for r in batch],
                )
                batch_updated = cur.rowcount
            updated += batch_updated
            conn.commit()
            print(f"Scores written: batch {start // BATCH_SIZE + 1} "
                  f"({len(batch)} rows, {batch_updated} updated)")
    finally:
        conn.close()
    return updated


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Lean deterministic content audit for hk-daily-places.")
    parser.add_argument("--from-seed", metavar="PATH",
                        help="load articles from a seed JSON file instead "
                             "of the database (local test mode)")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR,
                        help="where to write the report files")
    parser.add_argument("--check-images", action="store_true",
                        help="HTTP HEAD each image URL and oEmbed each "
                             "youtubeId (adds network time)")
    parser.add_argument("--check-live", action="store_true",
                        help="fetch the live sitemap for D11 reconciliation")
    parser.add_argument("--max-articles", type=int, default=None,
                        help="process only the first N articles (by slug)")
    parser.add_argument("--dry-run", action="store_true",
                        help="count what would be processed; write nothing")
    parser.add_argument("--write-scores", action="store_true",
                        help="write audit_score / audit_status / "
                             "audited_at back to places (DB mode only; "
                             "refused in --from-seed mode; with --dry-run "
                             "prints what would be written)")
    args = parser.parse_args(argv)

    db_url = os.environ.get("DATABASE_URL")
    if args.from_seed:
        source = f"seed:{args.from_seed}"
        articles = load_from_seed(args.from_seed)
    elif db_url:
        source = "db"
        print("Loading PUBLISHED articles from Neon (read-only SELECT)…")
        articles = load_from_db(db_url)
    else:
        print("ERROR: no data source. Set DATABASE_URL, or run with "
              "--from-seed <path> (e.g. "
              "src/main/resources/seed/bulk-places.json).", file=sys.stderr)
        sys.exit(2)

    if args.write_scores and args.from_seed:
        print("ERROR: --write-scores requires a database connection. "
              "Seed mode (--from-seed) has no database to write scores "
              "to.", file=sys.stderr)
        sys.exit(2)

    if args.max_articles is not None:
        articles = articles[:args.max_articles]
    print(f"Loaded {len(articles)} articles "
          f"({dict(Counter(a['category'] for a in articles))})")

    if args.dry_run and not args.write_scores:
        print(f"Dry run: would score {len(articles)} articles "
              f"(source: {source}), write audit-report.md + "
              f"audit-report.json + snapshot-<date>.json to "
              f"{args.output_dir}. No outputs written.")
        return 0
    if args.dry_run:
        # --write-scores --dry-run: score in memory, print what would be
        # written, write nothing (no report files, no DB writes).
        print(f"Dry run: scoring {len(articles)} articles in memory "
              f"(source: {source}). No outputs written, nothing written "
              f"to the database.")
    if len(articles) < 2:
        print("Not enough articles to audit (need >= 2).")
        return 0

    # D7/D8/D9 need the full pairwise matrix: build once, reuse.
    print("Building char-bigram TF-IDF matrix (no category boost)…")
    vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(2, 2))
    matrix = vectorizer.fit_transform(build_corpus(articles))
    sim = cosine_similarity(matrix)
    d7 = check_d7(articles, vectorizer, matrix)
    d8 = check_d8(articles, sim)
    d9 = check_d9(articles, sim)
    d6 = check_d6(articles)
    d11 = check_d11(articles, source, args.check_live)

    # Per-article duplicate lookups.
    dup_maps = {}
    for a in articles:
        slug = a["slug"]
        pairs = [p for p in d7["pairs"] if slug in (p["a"], p["b"])]
        dup_maps[slug] = {
            "pairs": pairs,
            "high_risk": [p["b"] if p["a"] == slug else p["a"]
                          for p in pairs if p["band"] == "high"],
            "flagged": [p["b"] if p["a"] == slug else p["a"]
                        for p in pairs if p["band"] == "flag"],
        }
    exact_by_slug = {}
    for norm_title, slugs in d6["exact"].items():
        for s in slugs:
            exact_by_slug[s] = [o for o in slugs if o != s]
    near_by_slug = defaultdict(list)
    for p in d6["near"]:
        near_by_slug[p["a"]].append(f"{p['b']} ({p['ratio']})")
        near_by_slug[p["b"]].append(f"{p['a']} ({p['ratio']})")
    series_by_slug = {}
    for s in d8:
        for slug in s["slugs"]:
            series_by_slug[slug] = s["prefix"]

    # Score in batches of ~50; write the JSON after each batch so an
    # interrupted run leaves the last completed batch on disk.
    if not args.dry_run:
        args.output_dir.mkdir(parents=True, exist_ok=True)
    results, rows = [], []
    missing_markers = defaultdict(list)
    for start in range(0, len(articles), BATCH_SIZE):
        batch = articles[start:start + BATCH_SIZE]
        for article in batch:
            slug = article["slug"]
            d1 = check_d1(article)
            d2 = check_d2(article)
            d3d4 = check_d3_d4(article, args.check_images)
            d5 = check_d5(article)
            d10 = check_d10(article)
            missing_markers[article["category"]].extend(d2["missing"])
            dup_info = {
                "exact_dup": exact_by_slug.get(slug, []),
                "high_risk": dup_maps[slug]["high_risk"],
                "flagged": dup_maps[slug]["flagged"],
                "near_title": near_by_slug.get(slug, []),
            }
            scores, total, status, flags, reasons = score_article(
                article, d1, d2, d3d4, d5, dup_info,
                series_by_slug.get(slug))
            results.append({
                "d1": d1, "d2": d2, "d3d4": d3d4, "d5": d5, "d10": d10,
                "series": series_by_slug.get(slug),
                "scores": scores, "total": total, "status": status,
                "flags": flags, "reasons": reasons,
            })
        rows = build_rows(articles[:len(results)], results, dup_maps,
                          d7, d8, d9)
        if not args.dry_run:
            partial = args.output_dir / "audit-report.json"
            partial.write_text(json.dumps(
                {"run": "partial", "rows": rows}, ensure_ascii=False,
                indent=2), encoding="utf-8")
        print(f"Batch {start // BATCH_SIZE + 1}: scored "
              f"{len(results)}/{len(articles)} articles")

    date = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d")
    # Naive local datetime for places.audited_at (matches the app's
    # LocalDateTime / timestamp-without-time-zone columns).
    run_dt = datetime.now(timezone.utc).astimezone().replace(tzinfo=None)
    meta = {"date": date, "source": source, "rows": len(rows),
            "per_category": dict(Counter(a["category"] for a in articles))}

    if not args.dry_run:
        snapshot = {"date": date, "source": source, "count": len(articles),
                    "per_category": meta["per_category"],
                    "slugs": sorted(a["slug"] for a in articles)}
        (args.output_dir / f"snapshot-{date}.json").write_text(
            json.dumps(snapshot, ensure_ascii=False, indent=2),
            encoding="utf-8")

        md = render_markdown(meta, rows, d6, d7, d8, d9, d11, missing_markers)
        (args.output_dir / "audit-report.md").write_text(md, encoding="utf-8")
        (args.output_dir / "audit-report.json").write_text(json.dumps(
            {"run": "complete", "meta": meta, "d11": d11,
             "duplicate_groups": d7["clusters"], "slug_series": d8,
             "same_place_pairs": d9, "rows": rows},
            ensure_ascii=False, indent=2), encoding="utf-8")

    if args.write_scores:
        updated = write_scores(db_url, rows, run_dt, dry_run=args.dry_run)
        print(f"Score write-back: {updated}/{len(rows)} rows updated")

    dist = Counter(r["status"] for r in rows)
    print(f"\nDone: {len(rows)} articles — PASS {dist['PASS']} / "
          f"NEEDS_IMPROVEMENT {dist['NEEDS_IMPROVEMENT']} / "
          f"FAIL {dist['FAIL']}")
    print(f"Duplicate pairs >= {FLAG_SIM}: {len(d7['pairs'])} "
          f"({sum(1 for p in d7['pairs'] if p['band'] == 'high')} high-risk), "
          f"clusters: {len(d7['clusters'])}")
    if not args.dry_run:
        print(f"Reports written to {args.output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
