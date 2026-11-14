#!/usr/bin/env python3
"""
LLM qualitative audit for hk-daily-places — 3 Gemini keys + Groq,
rotating (gemini-1, groq, gemini-2, gemini-3, one call each).

Scores each PUBLISHED article on the four qualitative criteria from the
24-article sample (see the sample report):
  Q1 originality / first-hand value (0-10)
  Q2 usefulness / actionability (0-10)
  Q3 accuracy / trust (0-10)
  Q4 value-add over a search result (0-10)
Total = (Q1 + Q2 + Q3 + Q4) x 2.5 -> /100, verdict KEEP / IMPROVE / REWRITE.

This is the qualitative half of the audit. The deterministic half is
tools/audit/audit.py (length, markers, TF-IDF duplicates, links) — it
measures what a script can count. This script asks a model to *judge*
the article, which a script cannot do. Both halves write to different
columns and are independent: the deterministic job writes audit_score /
audit_status / audited_at; this job writes audit_llm_score / audit_llm_at
and never touches the deterministic columns.

Two columns, not one: audit_llm_score holds the score, audit_llm_at holds
when it was written. The LLM "one month no checked" rule cannot reuse
audited_at — that timestamp belongs to the deterministic run, which
rewrites it every 30 days — so without its own timestamp the LLM selector
could never tell when a post was last LLM-scored.

Model (verified 2026-11-14 against Google's official deprecations page,
https://ai.google.dev/gemini-api/docs/deprecations):
  gemini-2.5-flash is DEPRECATED, no longer selectable in AI Studio, and
  access is limited to users who have actively used it in the past; from
  1 Dec 2026 its requests auto-route to gemini-3.5-flash-lite. This
  project's key was created 2026-11-14 with no prior usage, so 2.5-flash
  would most likely return 404. The default model is therefore
  gemini-3.5-flash-lite (Google's stated replacement, released 2026-07-21,
  no shutdown announced). Override with env GEMINI_MODEL if needed.
  Endpoint: POST https://generativelanguage.googleapis.com/v1beta/models/
  {model}:generateContent, API key in the x-goog-api-key header.
  Keys come ONLY from env GEMINI_API_KEY / GEMINI_API_KEY2 /
  GEMINI_API_KEY3 (rotation slots gemini-1 / gemini-2 / gemini-3).
  They are NEVER printed, logged, or included in any report or
  error message — the log shows only the slot label (gemini-1, ...).

  Groq (added 2026-11-14) is the rotation slot between gemini-1 and
  gemini-2. OpenAI-compatible chat completions at POST
  https://api.groq.com/openai/v1/chat/completions, key in the
  Authorization Bearer header, response_format json_object, temperature
  0. Default model qwen/qwen3.8-27b (Qwen3.8 27B) — a free-tier model
  on Groq (30 RPM, 1,000 requests/day, 200K tokens/day; verified
  2026-11-14 against Groq's rate-limits docs). qwen/qwen3-32b was
  retired from the free plan on 2026-07-17, so it is NOT the default.
  Override with env GROQ_MODEL. Key comes ONLY from env GROQ_API_KEY
  (a GitHub repo secret for the Actions run — the EC2 .env copy does
  not reach Actions). The `groq` SDK is NOT used: the script calls the
  endpoint with stdlib urllib, exactly like the Gemini path.

Cadence (same as the deterministic audit):
  --only-due scores only posts that are due: never LLM-scored
  (audit_llm_score IS NULL) or last LLM-scored at least --rescore-days
  days ago (default 30; exactly 30 days old counts as due).
  --max-articles N caps how many due posts are scored per run (default:
  no cap — all due posts). The cap was 50 while the free-tier limit
  was unmeasured; the 2026-11-14 runs proved the cap is per-minute
  (10 RPM), not daily, and 6s spacing stays under it, so a full run
  scores everything due (a ~241-post backlog takes ~40 minutes).
  Since 2026-11-15 the run rotates four endpoints call by call, in
  this fixed order: gemini-1 (GEMINI_API_KEY), groq (GROQ_API_KEY),
  gemini-2 (GEMINI_API_KEY2), gemini-3 (GEMINI_API_KEY3), then
  repeat. Each endpoint then sees a call every 12s, so the gap
  BETWEEN calls is 3s — well under Gemini's 10 RPM cap (a call every
  6s) and Groq's 30 RPM. With only one endpoint live (the others'
  keys missing, dead, or --providers) the gap is that endpoint's own
  safe spacing: Groq 3s (30 RPM cap), Gemini 6s (10 RPM cap).
  --providers groq runs Groq only; --providers gemini runs the three
  Gemini keys in slot order (gemini-1, gemini-2, gemini-3). In steady
  state that is ~1 new post/day plus rolling re-checks (posts whose
  audit_llm_at is 30+ days old). Three Gemini keys triple the daily
  Gemini budget (~200 calls/key/day, so ~600/day) on top of Groq's
  ~200K tokens/day (~64 posts/day).

Quota safety:
  - 3-second gap between calls while two or more endpoints are
    live (each endpoint then sees a call every 12s or more — at or
    below its free-tier cap); 6s when only one Gemini endpoint is
    live. The first real run (2026-11-14) hit HTTP 429 after only 11
    calls made ~2s apart — consistent with a 10-requests/minute
    free-tier cap, not a daily quota.
  - On HTTP 429 the run FAILS OVER: the same article is retried on
    the NEXT endpoint in the rotation after the 3s call gap — it
    never waits out the same endpoint. The 429'd endpoint is marked
    dead for the run when the server-suggested delay looks like a
    daily cap (>= 120s; Gemini's daily-cap 429 suggested 300s on
    2026-11-14), or put on cooldown for the suggested delay when it
    looks like a per-minute cap; 3 consecutive 429s kill it either
    way. Up to 10 attempts per article, then the article is recorded
    as failed and the run moves on. The run only STOPS scoring
    cleanly when ALL endpoints are dead (scores already obtained are
    kept and written, the report is finished, and the script exits 0
    with a printed "quota reached after N posts" note naming how many
    429s were spent). The remaining due posts are picked up by the
    next run.
  - On HTTP 404 (model not available — e.g. a deprecated model name)
    or 401 (wrong key) the affected provider is disabled the same
    way, not the run; only if both providers are unusable does the
    run abort with exit 2 and a clear message, so no quota is spent
    on calls that cannot succeed.
  - Any other per-post failure (invalid model JSON, other HTTP errors)
    records that post as failed and the run continues.

Column guard: in DB mode the script first checks information_schema
that audit_llm_score and audit_llm_at exist on `places`. If either is
missing it prints a clear error ("columns not created yet — run the EC2
rebuild first") and exits 2 without calling the API or writing
anything, so no quota is burned on a doomed run.

What this script does NOT do (unless --write-scores is given):
  - No writes to the database (SELECT only; the connection is opened
    read-only). Never deletes or modifies articles.
  - Never prints or logs GEMINI_API_KEY, GROQ_API_KEY, or DATABASE_URL.
  - Never touches production publishing or any cron/workflow.

With --write-scores it additionally UPDATEs places.audit_llm_score and
audit_llm_at per slug (parameterized, one transaction per post,
committed the moment that post is scored — so a cancelled run keeps
the posts it already scored instead of losing them all). It never
updates audit_score, audit_status, audited_at, title, description,
or any other column. --dry-run prints the due count and the first
prompt preview, makes NO API calls, and writes nothing.

Each JSON row carries content_hash (sha256 of slug + title +
description; same formula as audit.py) so a future run can skip
re-scoring unchanged posts.

Usage:
  python llm_audit.py --from-seed ../../src/main/resources/seed/bulk-places.json --mock-llm
  python llm_audit.py --from-seed ../../src/main/resources/seed/bulk-places.json --mock-llm --dry-run
  python llm_audit.py --mock-llm --max-articles 5 --from-seed ../../src/main/resources/seed/bulk-places.json
  python llm_audit.py --only-due                        # DB + Gemini API (no cap)
  python llm_audit.py --only-due --write-scores                # write scores back

Env:
  DATABASE_URL   Neon Postgres connection string (?sslmode=require)
                 — only needed when --from-seed is not given.
  GEMINI_API_KEY  Gemini API key 1 (rotation slot gemini-1) — only
                  needed for real API calls (not with --mock-llm).
                  Never paste it anywhere.
  GEMINI_API_KEY2 Gemini API key 2 (slot gemini-2); GEMINI_API_KEY3
                  key 3 (slot gemini-3). A missing key simply drops
                  its slot from the rotation (logged once at startup).
  GEMINI_MODEL    Model name (default: gemini-3.5-flash-lite), shared
                  by all three Gemini keys.
  GROQ_API_KEY    Groq API key (starts with gsk_) — rotation slot
                  groq, between gemini-1 and gemini-2; if it is
                  missing the run is Gemini-only. Only needed for
                  real API calls.
  GROQ_MODEL      Model name (default: qwen/qwen3.8-27b).

Outputs (tools/audit/output-llm/):
  llm-report.md      human-readable report (the main deliverable)
  llm-report.json    machine-readable per-article rows
  snapshot-<date>.json frozen slug list + category counts for this run

Requires: psycopg2-binary. Only Python stdlib otherwise (urllib for the
Gemini and Groq REST calls — no extra dependency; the `groq` SDK is
not needed).
"""
import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import psycopg2

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
DEFAULT_OUTPUT_DIR = SCRIPT_DIR / "output-llm"

BATCH_SIZE = 50  # (kept for the deterministic audit; the LLM writer is
# per-post since 2026-11-14 and no longer batches)
# No per-run cap by default (2026-11-14: the 50 cap was removed once
# the runs proved the free-tier limit is 10 RPM, not daily — 6s spacing
# stays under it, so a full run scores everything due).
DEFAULT_MAX_ARTICLES = None
# Delay between calls. With FOUR endpoints rotating (2026-11-15:
# gemini-1, groq, gemini-2, gemini-3, in that fixed order), a 3s gap
# between successive calls means each endpoint sees a call every
# 12s — well under Gemini's 10 RPM free-tier cap (a call every 6s)
# and Groq's 30 RPM, so the 3s gap is the throughput limit, not the
# per-endpoint caps. With a single endpoint live (the others' keys
# missing, dead, cooling, or --providers), the gap is that endpoint's
# own safe spacing: Groq 3s (its free-tier cap is 30 RPM, so 3s =
# 20 RPM is safe) or Gemini 6s (10 RPM cap; the Gemini-only run hit
# 429 after 11 calls ~2s apart, and 6s spacing stays under it. API
# latency adds more).
CALL_DELAY_DUAL_SECONDS = 3
CALL_DELAY_SINGLE_SECONDS = {"groq": 3, "gemini": 6}


def live_delay(live_providers):
    """Gap before the next call: 3s while two or more endpoints are
    live (each then sees a call every 12s or more); with only one
    live, that endpoint's own safe spacing (Groq 3s, Gemini 6s)."""
    if len(live_providers) > 1:
        return CALL_DELAY_DUAL_SECONDS
    if live_providers:
        return CALL_DELAY_SINGLE_SECONDS[live_providers[0].name]
    return CALL_DELAY_DUAL_SECONDS
# Attempts per post. A failed call (HTTP 429, bad key/model, invalid
# model JSON, network error) is retried on the NEXT endpoint in the
# rotation after the 3s call gap — never by waiting out the same
# endpoint. 10 attempts is enough to cycle the four endpoints twice
# plus margin; a post that fails 10 times is recorded as failed and
# the run moves on. When every endpoint is dead the run stops cleanly
# (see Rotator / AllEndpointsDead).
MAX_ATTEMPTS_PER_POST = 10
# How a 429 is classified. The server usually suggests a delay
# (Retry-After header or retryDelay in the error body). A delay of
# 120s or more reads as a DAILY cap (Gemini's daily-cap 429 suggested
# 300s on 2026-11-14); the endpoint is then dead for the run. A
# shorter delay reads as a PER-MINUTE cap: the endpoint cools down
# for that many seconds and is skipped until then. No delay at all
# defaults to 60s of cooldown. An endpoint that 429s 3 times in a
# row is dead regardless — a daily cap that suggests short delays
# would otherwise be retried all night.
DAILY_QUOTA_DELAY_SECONDS = 120
DEFAULT_COOLDOWN_SECONDS = 60
MAX_429_WAIT_SECONDS = 300
MAX_CONSEC_429 = 3
# Counts of 429s hit during the run (for the report meta).
# waited_429 is the total of the server-suggested delays we were
# told to wait (we fail over instead of sleeping them).
RATE_STATE = {"retries_429": 0, "waited_429": 0}

# Database connect timeout (seconds). The 2026-11-14 dual-provider run
# sat silent after "Checking LLM columns exist on places…" for minutes
# with no log output — a psycopg2.connect with no timeout can hang
# indefinitely on a stalled connection, and the run then looks dead
# instead of failing fast. 30s is generous for a warm Neon instance
# (the deterministic job connects in ~1s) and turns a stall into a
# visible error.
DB_CONNECT_TIMEOUT_SECONDS = 30

# Live progress logging: GitHub Actions shows the script's stdout, but
# Python buffers it when piped and the run goes quiet for minutes
# (3s spacing + API latency + up to 240s of 429 waits), which looks
# stalled. log() timestamps every line (local time + seconds since
# the script started) and flushes, so the Actions log shows what the
# run is doing while it is doing it.
_T0 = time.monotonic()


def log(msg):
    now = datetime.now(timezone.utc).astimezone().strftime("%H:%M:%S")
    print(f"[{now} +{time.monotonic() - _T0:.0f}s] {msg}", flush=True)

# Verified 2026-11-14 (see header): gemini-2.5-flash is deprecated and
# restricted to prior users; gemini-3.5-flash-lite is Google's stated
# replacement for this use. Override with env GEMINI_MODEL.
DEFAULT_MODEL = "gemini-3.5-flash-lite"
GEMINI_ENDPOINT = ("https://generativelanguage.googleapis.com/v1beta/"
                   "models/{model}:generateContent")

# Groq (added 2026-11-14): qwen/qwen3.8-27b (Qwen3.8 27B) is a
# free-tier model on Groq (30 RPM, 1,000 requests/day, 200K tokens/
# day). qwen/qwen3-32b was retired from the free plan on 2026-07-17
# and is NOT the default. Override with env GROQ_MODEL.
DEFAULT_GROQ_MODEL = "qwen/qwen3.8-27b"
GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"

# The four qualitative criteria, as defined in the 24-article sample
# report (llm-sample-report-2026-11-14.md). The prompt below uses these
# definitions verbatim-ish.
RUBRIC = {
    "q1": ("Originality / first-hand value — any personal experience, "
           "own opinion, unique angle, or judgement a reader couldn't "
           "get from a search snippet?"),
    "q2": ("Usefulness / actionability — can a reader plan a visit or "
           "make a decision from this? (route, distance, time, price, "
           "hours, transport, tips)"),
    "q3": ("Accuracy / trust — facts specific and checkable, or vague "
           "and unverifiable? Any visible risk? (Judge specificity, do "
           "not fact-check each claim against external sources.)"),
    "q4": ("Value-add over a search result — does it synthesise, select "
           "or curate something the top Google result or an embedded "
           "video doesn't give?"),
}
VALID_VERDICTS = ("KEEP", "IMPROVE", "REWRITE")

PROMPT_TEMPLATE = """You are scoring one article from a Hong Kong daily-guide website for a content-quality audit. Score the article on four criteria, each 0-10 (integers only). Be strict: a one-sentence description with only generic facts deserves low scores; a complete guide with prices, transport, tips and its own angle deserves high scores. Do not invent facts about the article; score only what is in front of you.

Q1 Originality / first-hand value: {q1}
Q2 Usefulness / actionability: {q2}
Q3 Accuracy / trust: {q3}
Q4 Value-add over a search result: {q4}

Verdict: KEEP if the article is already decent (minor fixes only), IMPROVE if it is salvageable with edits, REWRITE if it needs real rework or the format does not fit the site.

Article category: {category}
Article title: {title}
Article text:
{description}

Reply with STRICT JSON only, no other text:
{{"q1": int, "q2": int, "q3": int, "q4": int, "reasons": {{"q1": "...", "q2": "...", "q3": "...", "q4": "..."}}, "verdict": "KEEP"|"IMPROVE"|"REWRITE"}}"""


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_from_db(db_url):
    """Read-only SELECT of all PUBLISHED places. Never writes."""
    conn = psycopg2.connect(db_url,
                            connect_timeout=DB_CONNECT_TIMEOUT_SECONDS)
    conn.set_session(readonly=True)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT slug, title, COALESCE(description, ''), category, "
                "audit_llm_score, audit_llm_at "
                "FROM places WHERE status = 'PUBLISHED' ORDER BY slug"
            )
            rows = cur.fetchall()
    finally:
        conn.close()
    articles = []
    for (slug, title, desc, cat, score, scored_at) in rows:
        articles.append({
            "slug": slug, "title": title, "description": desc or "",
            "category": cat, "auditLlmScore": score,
            "auditLlmAt": scored_at,
        })
    return articles


def load_from_seed(path):
    """Local test mode: seed JSON has no LLM columns, so every row counts
    as never LLM-scored (due under --only-due)."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    items = data if isinstance(data, list) else data.get("places", data)
    articles = []
    for it in items:
        articles.append({
            "slug": it.get("slug", ""), "title": it.get("title", ""),
            "description": it.get("description", "") or "",
            "category": it.get("category", ""),
            "auditLlmScore": None, "auditLlmAt": None,
        })
    articles.sort(key=lambda a: a["slug"])
    return articles


def _parse_dt(value):
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _naive_local(dt):
    """Return a naive local datetime for comparison. audit_llm_at is a
    timestamp without time zone in the DB, so it arrives naive; if a
    caller passes an aware datetime, convert it to local naive first."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt
    return dt.astimezone().replace(tzinfo=None)


def is_due_llm(article, rescore_days, now):
    """Pure due-selection predicate (unit-testable, no DB).

    A post is due when it has never been LLM-scored (audit_llm_score is
    NULL, or audit_llm_at is NULL — the two are written together, so a
    NULL in either means no trustworthy previous LLM check) or its last
    LLM check is at least rescore_days old.

    Boundary: a check exactly rescore_days ago counts as due — the post
    has gone a full rescore_days without a fresh LLM check. So the rule
    is age >= rescore_days. One second under rescore_days is NOT due.

    NOTE: this deliberately reads audit_llm_score / audit_llm_at, NOT
    audit_score / audited_at — those belong to the deterministic run,
    which rewrites audited_at every 30 days.
    """
    if article.get("auditLlmScore") is None:
        return True
    scored_at = _naive_local(article.get("auditLlmAt"))
    if scored_at is None:
        return True
    return (_naive_local(now) - scored_at) >= timedelta(days=rescore_days)


def check_llm_columns(db_url):
    """Column guard: returns the set of LLM columns that exist on
    `places`. Must contain both audit_llm_score and audit_llm_at
    before any API call is made; if either is missing, the EC2 rebuild
    has not created them yet and the run must not start (no quota
    burned on a doomed run)."""
    conn = psycopg2.connect(db_url,
                            connect_timeout=DB_CONNECT_TIMEOUT_SECONDS)
    conn.set_session(readonly=True)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'places' AND column_name IN "
                "('audit_llm_score', 'audit_llm_at')"
            )
            return {row[0] for row in cur.fetchall()}
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Gemini API (urllib only — no extra dependency)
# ---------------------------------------------------------------------------

class QuotaReached(Exception):
    """Raised on HTTP 429: stop using THIS endpoint for now. Carries
    retry_delay — the seconds the server suggested waiting
    (Retry-After header or retryDelay in the error body), or None
    when it gave none. The caller decides from it whether the
    endpoint looks daily-capped (dead for the run) or per-minute-
    capped (cooldown)."""

    def __init__(self, message, retry_delay=None):
        super().__init__(message)
        self.retry_delay = retry_delay


def _parse_retry_delay(error):
    """Seconds the server asks us to wait after a 429, or None.

    Prefers the Retry-After response header, then the retryDelay in
    the error body's details (google.rpc.RetryInfo, e.g. "58s").
    Returns None when neither is present or parseable.
    """
    try:
        raw = error.headers.get("Retry-After")
        if raw is not None and str(raw).strip().isdigit():
            return int(str(raw).strip())
    except Exception:
        pass
    try:
        body = error.read()
        if body:
            payload = json.loads(body.decode("utf-8", "replace"))
            for detail in (payload.get("error") or {}).get("details", []):
                delay = detail.get("retryDelay")
                if isinstance(delay, str) and delay.endswith("s"):
                    value = delay[:-1]
                    try:
                        return int(float(value))
                    except ValueError:
                        pass
    except Exception:
        pass
    return None


class ModelUnavailable(Exception):
    """Raised on HTTP 404: the model is not available for this project."""


def build_prompt(article):
    """One scoring prompt per article, with the rubric definitions."""
    return PROMPT_TEMPLATE.format(
        q1=RUBRIC["q1"], q2=RUBRIC["q2"], q3=RUBRIC["q3"], q4=RUBRIC["q4"],
        category=article["category"], title=article["title"],
        description=article["description"] or "(empty description)")


def _missing_closing_braces(text):
    """Net unclosed '{' in text, ignoring braces inside double-quoted
    strings (backslash escapes respected). Used to repair a reply the
    model left unclosed."""
    depth = 0
    in_string = False
    escaped = False
    for ch in text:
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
    return max(0, depth)


def _extract_json(text):
    """Parse the model's reply. Candidates, most faithful first: the
    raw text; the {...} block (a short preamble is tolerated); the
    block with its missing closing braces appended — the model
    sometimes puts the verdict inside "reasons" and drops the closing
    brace, so the object is one '}' short. Strict validation still
    runs afterwards, so a repaired parse cannot smuggle a bad score
    through."""
    if "{" not in text:
        raise ValueError("no JSON object in model reply")
    candidates = [text]
    match = re.search(r"\{.*\}", text, re.DOTALL)
    block = match.group(0) if match else text
    if block != text:
        candidates.append(block)
    missing = _missing_closing_braces(block)
    if missing > 0:
        candidates.append(block + "}" * missing)
    last_error = None
    for candidate in candidates:
        try:
            return json.loads(candidate)
        except (json.JSONDecodeError, TypeError) as e:
            last_error = e
    raise last_error


def validate_llm_result(data):
    """Validate the parsed model JSON. Returns (q1..q4 dict, reasons
    dict, verdict) or raises ValueError with a short, key-free reason."""
    if not isinstance(data, dict):
        raise ValueError("model reply is not a JSON object")
    scores = {}
    for key in ("q1", "q2", "q3", "q4"):
        value = data.get(key)
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{key} is not an integer")
        if not 0 <= value <= 10:
            raise ValueError(f"{key} out of range 0-10: {value}")
        scores[key] = value
    reasons = data.get("reasons")
    if not isinstance(reasons, dict):
        raise ValueError("reasons is not an object")
    for key in ("q1", "q2", "q3", "q4"):
        if not isinstance(reasons.get(key), str) or not reasons[key].strip():
            raise ValueError(f"reasons.{key} is missing or empty")
    verdict = data.get("verdict")
    if verdict is None and isinstance(reasons, dict):
        # The model sometimes nests the verdict inside "reasons"
        # (and drops the closing brace — see _extract_json). It is
        # still the model's own word, just one level deeper; reading
        # it here is not deriving a verdict. If it is present but an
        # invalid value, the check below still rejects it.
        verdict = reasons.get("verdict")
    if verdict not in VALID_VERDICTS:
        raise ValueError(f"verdict not in {VALID_VERDICTS}: {verdict!r}")
    return scores, reasons, verdict


def mock_llm_result(article):
    """Canned valid JSON for --mock-llm (no API call). Scores are derived
    from the article's content hash so each article gets a stable,
    varied, valid score — this exercises parsing, verdict logic and
    report writing. THESE ARE NOT REAL SCORES: a mock run must never be
    mistaken for an LLM-scored run (the report header says so)."""
    digest = hashlib.sha256(
        (article["slug"] + article["title"]).encode("utf-8")).digest()
    scores = {key: 2 + (digest[i] % 9) for i, key in enumerate(
        ("q1", "q2", "q3", "q4"))}
    total = sum(scores.values())
    verdict = "KEEP" if total >= 32 else ("IMPROVE" if total >= 24
                                          else "REWRITE")
    return {"q1": scores["q1"], "q2": scores["q2"], "q3": scores["q3"],
            "q4": scores["q4"],
            "reasons": {key: f"mock reason for {key} (test only)"
                        for key in ("q1", "q2", "q3", "q4")},
            "verdict": verdict}


def _urlopen_json_once(req, provider, model):
    """POST a prepared request once and return the parsed JSON payload.
    Shared by the Gemini and Groq callers.

    On HTTP 429 raises QuotaReached immediately — the caller retries
    the same article on the NEXT endpoint after the 3s call gap
    (failover); it does NOT wait out the same endpoint. The
    server-suggested delay (Retry-After header, or the retryDelay in
    the error body) is carried on the exception so the caller can
    tell a daily cap from a per-minute cap. On HTTP 404 raises
    ModelUnavailable (a deprecated or wrong model name). Any other
    HTTPError is re-raised. The API key is never included in any
    exception message or log.
    """
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 429:
            delay = _parse_retry_delay(e)
            RATE_STATE["retries_429"] += 1
            if delay is not None:
                RATE_STATE["waited_429"] += delay
            raise QuotaReached(
                f"HTTP 429 from {provider}: free-tier quota hit"
                + (f" (server suggests waiting {delay}s)"
                   if delay is not None else ""),
                retry_delay=delay)
        if e.code == 404:
            raise ModelUnavailable(
                f"HTTP 404 from {provider} model {model}: the model "
                "is not available (a deprecated or wrong model "
                "name). Check "
                f"{'GEMINI_MODEL' if provider == 'gemini' else 'GROQ_MODEL'}.")
        raise


class AllEndpointsDead(Exception):
    """Raised when every endpoint is dead for the run: stop scoring
    cleanly, keep what we have."""


class Provider:
    """One endpoint for a run: a provider type (name: "gemini" or
    "groq"), a human label ("gemini-1", "groq", "gemini-2",
    "gemini-3" — the label is what the log shows, never the key),
    the call function, the key, the model, and how many API calls it
    made (for the report meta).

    Availability state for the run: dead (daily cap, bad key/model,
    or 3 consecutive 429s — never tried again this run) and
    cooldown_until (a per-minute cap: skip until this monotonic
    time). is_live(now) is True only when neither applies.
    """
    def __init__(self, label, name, call, key, model):
        self.label = label
        self.name = name
        self.call = call
        self.key = key
        self.model = model
        self.calls = 0
        self.dead = False
        self.cooldown_until = 0.0
        self.consec_429 = 0

    def is_live(self, now):
        return not self.dead and now >= self.cooldown_until

    def note_429(self, retry_delay, now):
        """Record a 429 on this endpoint. Returns "dead" or
        "cooldown". A server-suggested delay >=
        DAILY_QUOTA_DELAY_SECONDS reads as a daily cap (dead). Anything
        shorter is a per-minute cap: cool down for the suggested
        delay (default 60s when none was given, capped at
        MAX_429_WAIT_SECONDS). Three 429s in a row kill the endpoint
        regardless — a daily cap that suggests short delays must not
        be retried all night."""
        self.consec_429 += 1
        if (retry_delay is not None
                and retry_delay >= DAILY_QUOTA_DELAY_SECONDS):
            self.dead = True
            return "dead"
        if self.consec_429 >= MAX_CONSEC_429:
            self.dead = True
            return "dead"
        delay = retry_delay if retry_delay is not None \
            else DEFAULT_COOLDOWN_SECONDS
        self.cooldown_until = now + min(delay, MAX_429_WAIT_SECONDS)
        return "cooldown"

    def note_success(self):
        self.consec_429 = 0


class Rotator:
    """Cycles through the run's endpoints in their fixed order
    (gemini-1, groq, gemini-2, gemini-3 — tom's order, 2026-11-15).
    next_endpoint() returns the next live one, skipping dead or
    cooling endpoints; if every endpoint is cooling it waits for the
    earliest cooldown to end, and if all are dead it raises
    AllEndpointsDead. wait_gap() enforces the 3s gap between
    successive API calls (the live endpoints' own floor when only
    one is left)."""
    def __init__(self, endpoints):
        self.endpoints = endpoints
        self.turn = 0
        self.first_call = True

    def live_now(self):
        now = time.monotonic()
        return [e for e in self.endpoints if e.is_live(now)]

    def next_endpoint(self):
        live = self.live_now()
        if not live:
            now = time.monotonic()
            cooling = [e for e in self.endpoints if not e.dead]
            if cooling:
                wait = min(e.cooldown_until for e in cooling) - now
                if wait > 0:
                    log(f"  all endpoints cooling — waiting {wait:.0f}s "
                        f"for the earliest cooldown")
                    time.sleep(min(wait, MAX_429_WAIT_SECONDS))
                    live = self.live_now()
            if not live:
                raise AllEndpointsDead(
                    "all endpoints are dead for this run (daily quota "
                    "or bad key/model on each)")
        for _ in range(len(self.endpoints)):
            ep = self.endpoints[self.turn % len(self.endpoints)]
            self.turn += 1
            if ep.is_live(time.monotonic()):
                return ep
        raise AllEndpointsDead("no live endpoint (unexpected)")

    def wait_gap(self):
        if self.first_call:
            self.first_call = False
            return
        time.sleep(live_delay(self.live_now()))


def call_gemini(prompt, api_key, model):
    """One generateContent call. Returns the raw model text. 429/404
    handling lives in _urlopen_json_once (shared with Groq). A 401
    (wrong key) raises ModelUnavailable so the run can drop that
    endpoint and continue on the others."""
    url = GEMINI_ENDPOINT.format(model=model)
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3,
                             "maxOutputTokens": 600,
                             "responseMimeType": "application/json"},
    }).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, method="POST",
        headers={"Content-Type": "application/json",
                 "x-goog-api-key": api_key})
    try:
        payload = _urlopen_json_once(req, "gemini", model)
    except urllib.error.HTTPError as e:
        if e.code == 401:
            raise ModelUnavailable(
                "HTTP 401 from Gemini: the API key is invalid. "
                "Check the key (GitHub secrets GEMINI_API_KEY / "
                "GEMINI_API_KEY2 / GEMINI_API_KEY3 for Actions runs).")
        raise
    candidates = payload.get("candidates") or []
    if not candidates:
        raise ValueError("Gemini reply has no candidates")
    parts = (candidates[0].get("content") or {}).get("parts") or []
    text = "".join(p.get("text", "") for p in parts).strip()
    if not text:
        raise ValueError("Gemini reply has no text")
    return text


def call_groq(prompt, api_key, model):
    """One Groq chat-completions call (OpenAI-compatible endpoint,
    stdlib urllib — the `groq` SDK is NOT needed). Returns the raw
    model text.

    temperature 0 (deterministic scoring, same intent as Gemini's
    0.3), response_format json_object so the model returns strict
    JSON, max_completion_tokens 1024 (the audit JSON is ~300-500
    tokens; this leaves room without wasting quota). 429/404 handling
    is shared with Gemini via _urlopen_json_once. A 401 (wrong
    key) raises ModelUnavailable so the run can drop that endpoint
    and continue on the others instead of failing every other call.
    """
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_completion_tokens": 1024,
        "response_format": {"type": "json_object"},
    }).encode("utf-8")
    req = urllib.request.Request(
        GROQ_ENDPOINT, data=body, method="POST",
        headers={"Content-Type": "application/json",
                 # Cloudflare in front of api.groq.com returns 403
                 # (error 1010) for the Python-urllib default
                 # User-Agent (verified 2026-11-14); any non-blocked
                 # UA passes — this one identifies the project.
                 "User-Agent": "hk-daily-places-audit/1.0",
                 "Authorization": f"Bearer {api_key}"})
    try:
        payload = _urlopen_json_once(req, "groq", model)
    except urllib.error.HTTPError as e:
        if e.code == 401:
            raise ModelUnavailable(
                "HTTP 401 from Groq: the GROQ_API_KEY is invalid. "
                "Check the key (GitHub secret GROQ_API_KEY for "
                "Actions runs).")
        raise
    choices = payload.get("choices") or []
    if not choices:
        raise ValueError("Groq reply has no choices")
    content = ((choices[0].get("message") or {}).get("content") or "")
    text = content.strip()
    if not text:
        raise ValueError("Groq reply has no text")
    return text


def _raw_excerpt(text):
    """Excerpt of a raw model reply for failure diagnosis. Short replies
    are kept whole; long ones keep the head and the tail — the verdict
    sits at the end of the JSON, so the tail is where a missing verdict
    actually shows. Newlines are flattened to spaces so the excerpt
    stays on one log line. NOTE: this is returned as plain text, never
    through repr() — a repr would escape apostrophes as \\' and make a
    plain "wouldn't" look like a backslash escape the model never
    wrote."""
    flat = text.replace("\r\n", " ").replace("\n", " ").replace("\r", " ")
    if len(flat) <= 1200:
        return flat
    return flat[:600] + " ...[truncated]... " + flat[-600:]


def score_article_rotating(article, rotator, position, total_posts):
    """Score one article across the rotation. Returns
    (scores, total, verdict, reasons, error).

    Tries endpoints in turn, up to MAX_ATTEMPTS_PER_POST attempts.
    Every attempt is logged with the endpoint label, so the Actions
    log shows exactly which key scored (or 429'd on) each post. A
    429 fails over to the next endpoint after the 3s call gap; the
    429'd endpoint is marked dead or cooling by note_429. A 404/401
    (ModelUnavailable) drops that endpoint for the run. Invalid model
    JSON and other per-call errors move to the next endpoint too and
    count as an attempt. After 10 failed attempts the post is
    recorded as failed (error carries each attempt's reason). When
    every endpoint is dead, raises AllEndpointsDead instead of
    returning — the run stops cleanly with what it has.
    """
    prompt = build_prompt(article)
    # Per-attempt errors, each carrying its raw reply (or the endpoint
    # label for call errors) — the attempts can fail differently, and
    # the record is the only evidence of what happened to the post.
    attempt_errors = []
    for attempt in range(MAX_ATTEMPTS_PER_POST):
        endpoint = rotator.next_endpoint()
        rotator.wait_gap()
        endpoint.calls += 1
        log(f"-> [{position}/{total_posts}] {article['slug']} "
            f"({article['category']}) — calling {endpoint.label} "
            f"({endpoint.model}) "
            f"[attempt {attempt + 1}/{MAX_ATTEMPTS_PER_POST}]...")
        try:
            text = endpoint.call(prompt, endpoint.key, endpoint.model)
        except QuotaReached as e:
            outcome = endpoint.note_429(e.retry_delay, time.monotonic())
            delay_note = (f"server suggested {e.retry_delay}s"
                          if e.retry_delay is not None
                          else "no delay suggested")
            attempt_errors.append(
                f"attempt {attempt + 1} [{endpoint.label}]: HTTP 429 "
                f"({outcome}; {delay_note})")
            log(f"  {endpoint.label}: HTTP 429 ({outcome}) — failing "
                f"over to the next endpoint")
            continue
        except ModelUnavailable as e:
            endpoint.dead = True
            attempt_errors.append(
                f"attempt {attempt + 1} [{endpoint.label}]: {e}")
            log(f"  {endpoint.label} disabled for this run: {e}")
            continue
        except Exception as e:
            detail = type(e).__name__
            code = getattr(e, "code", None)
            if code is not None:
                detail = f"{detail} {code}"
            attempt_errors.append(
                f"attempt {attempt + 1} [{endpoint.label}]: call "
                f"failed: {detail}")
            continue
        try:
            data = _extract_json(text)
            scores, reasons, verdict = validate_llm_result(data)
            endpoint.note_success()
            return (scores, round(sum(scores.values()) * 2.5, 1),
                    verdict, reasons, None)
        except (ValueError, json.JSONDecodeError) as e:
            attempt_errors.append(
                f"attempt {attempt + 1} [{endpoint.label}]: invalid "
                f"model output: {e} (raw reply: {_raw_excerpt(text)})")
            log(f"  {endpoint.label}: invalid model output — failing "
                f"over to the next endpoint")
            continue
    return None, None, None, None, " | ".join(attempt_errors)


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def compute_content_hash(article):
    """sha256 of slug + title + description — the SAME formula as
    audit.py, so the deterministic and LLM rows agree on identity and a
    future run can skip re-scoring unchanged posts."""
    payload = "\n".join([article["slug"], article["title"],
                         article["description"]])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def verdict_of_total(total):
    """Band implied by the numeric total (same bands as the deterministic
    audit: 80+ / 60-79 / <60). Recorded next to the model's own verdict;
    a mismatch is flagged in the row, not silently resolved."""
    if total >= 80:
        return "KEEP"
    if total >= 60:
        return "IMPROVE"
    return "REWRITE"


def build_rows(to_score, results):
    """Assemble one machine-readable row per scored article."""
    rows = []
    for article, res in zip(to_score, results):
        rows.append({
            "slug": article["slug"], "title": article["title"],
            "content_hash": compute_content_hash(article),
            "category": article["category"],
            "q1": res["scores"]["q1"], "q2": res["scores"]["q2"],
            "q3": res["scores"]["q3"], "q4": res["scores"]["q4"],
            "total": res["total"], "verdict": res["verdict"],
            "verdict_band": verdict_of_total(res["total"]),
            "verdict_mismatch": res["verdict"] != verdict_of_total(
                res["total"]),
            "reasons": res["reasons"],
        })
    return rows


def render_markdown(meta, rows, failed, quota_note, mock):
    totals = [r["total"] for r in rows]
    dist = Counter(r["verdict"] for r in rows)
    by_cat = {}
    for cat in sorted({r["category"] for r in rows}):
        cr = [r for r in rows if r["category"] == cat]
        by_cat[cat] = {
            "n": len(cr),
            "mean": round(sum(r["total"] for r in cr) / len(cr), 1),
            "keep": sum(1 for r in cr if r["verdict"] == "KEEP"),
            "improve": sum(1 for r in cr if r["verdict"] == "IMPROVE"),
            "rewrite": sum(1 for r in cr if r["verdict"] == "REWRITE"),
        }
    low = sorted(rows, key=lambda r: r["total"])[:10]
    high = sorted(rows, key=lambda r: -r["total"])[:10]

    lines = []
    add = lines.append
    add(f"# hk-daily-places — LLM Qualitative Audit Report ({meta['date']})")
    add("")
    if mock:
        add("**MOCK RUN — these are NOT real LLM scores.** Scores were "
            "generated from a canned response for testing only. Do not "
            "use them for decisions, and do not write them back.")
        add("")
    add(f"- Source: {meta['source']} (loaded {meta['loaded']} articles, "
        f"scored {meta['scored']}, failed {len(failed)})")
    if meta.get("write_scores"):
        add(f"- Written to DB: {meta.get('written', 0)}/"
            f"{meta['scored']} (per post, as scored)")
        if meta.get("write_note"):
            add(f"  - {meta['write_note']}")
    add(f"- Selection: {meta['selection']['rule']}")
    add(f"- Model: {meta['model']}")
    if meta.get("providers") and not mock:
        add("- Provider calls: " + ", ".join(
            f"{name} {info['calls']} ({info['model']})"
            for name, info in meta["providers"].items()))
    add(f"- Categories: {meta['per_category']}")
    add(f"- Mean LLM score: "
        f"{round(sum(totals) / len(totals), 1) if totals else 0} / 100")
    add(f"- Verdicts: KEEP {dist['KEEP']} / IMPROVE {dist['IMPROVE']} / "
        f"REWRITE {dist['REWRITE']}")
    if quota_note:
        add(f"- Quota: {quota_note}")
    add("")
    add("Scores are model judgements on the four qualitative criteria "
        "(Q1 originality / Q2 usefulness / Q3 accuracy / Q4 value-add, "
        "each 0-10; total = sum x 2.5). They are one model's opinion, not "
        "a measurement — the 24-article agent sample is the calibration "
        "reference. The deterministic total (audit_score) is a different "
        "yardstick and is not comparable 1:1.")
    add("")
    add("## Score distribution by category")
    add("")
    add("| Category | n | Mean | KEEP | IMPROVE | REWRITE |")
    add("|---|---|---|---|---|---|")
    for cat, s in by_cat.items():
        add(f"| {cat} | {s['n']} | {s['mean']} | {s['keep']} | "
            f"{s['improve']} | {s['rewrite']} |")
    add("")
    add("## Highest-scored articles (top 10)")
    add("")
    for r in high:
        add(f"- **{r['title']}** (`{r['slug']}`, {r['category']}) — "
            f"total {r['total']} [{r['verdict']}] "
            f"Q1 {r['q1']} / Q2 {r['q2']} / Q3 {r['q3']} / Q4 {r['q4']}")
        for key in ("q1", "q2", "q3", "q4"):
            add(f"  - {key.upper()}: {r['reasons'][key]}")
    add("")
    add("## Lowest-scored articles (bottom 10)")
    add("")
    for r in low:
        add(f"- **{r['title']}** (`{r['slug']}`, {r['category']}) — "
            f"total {r['total']} [{r['verdict']}] "
            f"Q1 {r['q1']} / Q2 {r['q2']} / Q3 {r['q3']} / Q4 {r['q4']}")
        for key in ("q1", "q2", "q3", "q4"):
            add(f"  - {key.upper()}: {r['reasons'][key]}")
    add("")
    add("## Failed (no score — will be retried by a later run)")
    add("")
    for entry in failed:
        add(f"- `{entry['slug']}` — {entry['error']}")
    if not failed:
        add("- (none)")
    add("")
    add("## Limitations")
    add("")
    add("- One model, one pass per article: scores are judgements, not "
        "measurements. A second rater (or a re-score after an edit) can "
        "disagree.")
    add("- The model scores only the stored title + description; it does "
        "not see the hero image, the branch list, or the embedded video "
        "— so it cannot catch a wrong hero image (the sample found one "
        "by hand).")
    add("- The model may reward fluent, specific-sounding text even when "
        "a fact is wrong; Q3 judges specificity, it does not fact-check "
        "each claim against a source.")
    add("- Free-tier content may be used by the provider to improve its "
        "products; only public article text is ever sent.")
    return "\n".join(lines) + "\n"


def write_one_llm_score(conn, slug, total, run_dt):
    """Write one article's LLM score the moment it is scored.

    ONLY audit_llm_score / audit_llm_at are ever updated — never
    audit_score, audit_status, audited_at, title, description, or any
    other column. Parameterized query, one transaction per post
    (commit immediately). Returns the number of rows updated (1 on
    success, 0 if the slug is not in the table).

    Per-post (2026-11-14): the old bulk write happened only after the
    whole scoring loop, so a cancelled run lost every score it had
    already computed (run 43610628143: 18 posts scored, 0 written).
    Writing per post means a cancelled run keeps what it scored, and
    the next run only re-scores the rest.
    """
    with conn.cursor() as cur:
        cur.execute("UPDATE places SET audit_llm_score = %s, "
                    "audit_llm_at = %s WHERE slug = %s",
                    (total, run_dt, slug))
        updated = cur.rowcount
    conn.commit()
    return updated


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(
        description="LLM qualitative audit for hk-daily-places "
                    "(3 Gemini keys + Groq, rotating).")
    parser.add_argument("--from-seed", metavar="PATH",
                        help="load articles from a seed JSON file instead "
                             "of the database (local test mode)")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR,
                        help="where to write the report files")
    parser.add_argument("--max-articles", type=int, default=DEFAULT_MAX_ARTICLES,
                        help="score at most N due posts per run (default: "
                             "no cap — score everything due)")
    parser.add_argument("--dry-run", action="store_true",
                        help="count what would be processed and print the "
                             "first prompt preview; makes NO API calls "
                             "and writes nothing (no report, no DB)")
    parser.add_argument("--write-scores", action="store_true",
                        help="write audit_llm_score / audit_llm_at back "
                             "to places (DB mode only; refused in "
                             "--from-seed mode; with --dry-run prints "
                             "what would be written)")
    parser.add_argument("--only-due", action="store_true",
                        help="score only due posts: never LLM-scored "
                             "(audit_llm_score IS NULL) or last "
                             "LLM-scored at least --rescore-days ago. "
                             "Without it, all loaded articles are scored.")
    parser.add_argument("--rescore-days", type=int, default=30,
                        help="with --only-due: re-score posts whose last "
                             "LLM audit is at least this many days old "
                             "(default 30; exactly N days old counts as "
                             "due)")
    parser.add_argument("--mock-llm", action="store_true",
                        help="use a canned valid JSON response instead of "
                             "the Gemini API (tests the full path "
                             "without a key or quota)")
    parser.add_argument("--providers", type=str, default="both",
                        choices=["both", "gemini", "groq"],
                        help="which LLM provider(s) to use: both "
                             "(rotate gemini-1, groq, gemini-2, "
                             "gemini-3, default), gemini only (the "
                             "three Gemini keys in slot order), or "
                             "groq only. Useful when one provider's "
                             "daily quota is spent — e.g. --providers "
                             "groq after Gemini hits its daily cap.")
    args = parser.parse_args(argv)

    if args.rescore_days < 0:
        parser.error("--rescore-days must be >= 0")
    if args.max_articles is not None and args.max_articles < 0:
        parser.error("--max-articles must be >= 0")

    gemini_model = os.environ.get("GEMINI_MODEL") or DEFAULT_MODEL
    groq_model = os.environ.get("GROQ_MODEL") or DEFAULT_GROQ_MODEL
    db_url = os.environ.get("DATABASE_URL")
    # Endpoints, in rotation order (2026-11-15, tom): gemini-1, groq,
    # gemini-2, gemini-3, then repeat. --providers filters them
    # (both / gemini / groq). An endpoint whose key is missing simply
    # drops out of the rotation (logged once at startup); a requested
    # provider whose MAIN key is missing still exits 2 naming it.
    gemini_eps = []
    if args.providers in ("both", "gemini"):
        for label, env_name in (("gemini-1", "GEMINI_API_KEY"),
                                ("gemini-2", "GEMINI_API_KEY2"),
                                ("gemini-3", "GEMINI_API_KEY3")):
            key = os.environ.get(env_name)
            if key:
                gemini_eps.append(Provider(label, "gemini", call_gemini,
                                           key, gemini_model))
            else:
                print(f"NOTE: {env_name} is not set — {label} is not "
                      f"in the rotation.")
    groq_eps = []
    if args.providers in ("both", "groq"):
        groq_key = os.environ.get("GROQ_API_KEY")
        if groq_key:
            groq_eps.append(Provider("groq", "groq", call_groq, groq_key,
                                     groq_model))
    if not args.mock_llm and not gemini_eps and not groq_eps:
        if args.providers == "groq":
            print("ERROR: --providers groq but no GROQ_API_KEY is "
                  "set. Add the key (GitHub secret GROQ_API_KEY for "
                  "Actions runs) or drop --providers.", file=sys.stderr)
        elif args.providers == "gemini":
            print("ERROR: --providers gemini but no GEMINI_API_KEY "
                  "(GEMINI_API_KEY2 / GEMINI_API_KEY3) is set. Add a "
                  "key or drop --providers.", file=sys.stderr)
        else:
            print("ERROR: no LLM API key. Set GEMINI_API_KEY and/or "
                  "GROQ_API_KEY (GEMINI_API_KEY2 / GEMINI_API_KEY3 "
                  "optional, for extra Gemini quota), or run with "
                  "--mock-llm to test without a key.", file=sys.stderr)
        sys.exit(2)
    endpoints = []
    if gemini_eps:
        endpoints.append(gemini_eps[0])  # gemini-1 first
    endpoints.extend(groq_eps)           # then groq
    endpoints.extend(gemini_eps[1:])     # then gemini-2, gemini-3
    g_labels = [p.label for p in endpoints if p.name == "gemini"]
    q_labels = [p.label for p in endpoints if p.name == "groq"]
    parts = []
    if g_labels:
        parts.append(f"{gemini_model} ({'/'.join(g_labels)})")
    if q_labels:
        parts.append(f"{groq_model} ({'/'.join(q_labels)})")
    model_label = " + ".join(parts) if parts else "mock"

    if args.from_seed:
        source = f"seed:{args.from_seed}"
        articles = load_from_seed(args.from_seed)
    elif db_url:
        source = "db"
        print("Checking LLM columns exist on places…")
        existing = check_llm_columns(db_url)
        missing = {"audit_llm_score", "audit_llm_at"} - existing
        if missing:
            print("ERROR: the LLM audit columns are not created yet: "
                  f"missing {sorted(missing)} on places. Run the EC2 "
                  "rebuild first (git pull + docker build + recreate), "
                  "then re-run. No API call was made.", file=sys.stderr)
            sys.exit(2)
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
    if args.write_scores and args.mock_llm:
        print("ERROR: --write-scores with --mock-llm is refused — mock "
              "scores are test data and must never be written to the "
              "database.", file=sys.stderr)
        sys.exit(2)
    # (Endpoints were built above, in rotation order gemini-1, groq,
    # gemini-2, gemini-3 — see `endpoints` / `model_label`.)

    print(f"Loaded {len(articles)} articles "
          f"({dict(Counter(a['category'] for a in articles))})")

    # Due-selection: only the due subset is scored (and capped). run_now
    # is computed once so every due decision in this run uses the same
    # clock. --max-articles applies to the DUE subset, not the loaded
    # corpus — the run scores the first N due posts (by slug).
    run_now = datetime.now(timezone.utc).astimezone()
    if args.only_due:
        due = [a for a in articles
               if is_due_llm(a, args.rescore_days, run_now)]
        selection = {
            "mode": "due-only", "rescore_days": args.rescore_days,
            "rule": (f"due only — never LLM-scored "
                     f"(audit_llm_score IS NULL) OR LLM-scored at least "
                     f"{args.rescore_days} days ago"),
        }
        print(f"Due selection: {len(due)} of {len(articles)} due "
              f"({selection['rule']})")
    else:
        due = list(articles)
        selection = {"mode": "all", "rescore_days": None,
                     "rule": "all loaded articles"}

    to_score = due[:args.max_articles] if args.max_articles is not None \
        else due
    if args.max_articles is not None and len(due) > len(to_score):
        print(f"Cap: scoring {len(to_score)} of {len(due)} due posts "
              f"(--max-articles {args.max_articles}); the remaining "
              f"{len(due) - len(to_score)} stay due for the next run.")

    if args.dry_run:
        print(f"Dry run: would score {len(to_score)} articles "
              f"(source: {source}), write llm-report.md + "
              f"llm-report.json + snapshot-<date>.json to "
              f"{args.output_dir}. No API calls, no outputs written.")
        if to_score:
            print("\n--- First prompt preview (first due article) ---")
            print(build_prompt(to_score[0]))
            print("--- End of prompt preview ---")
        return 0

    if not to_score:
        print("Nothing due — nothing to score.")
        return 0

    # Score one article at a time, alternating providers call by call,
    # with a delay between calls. A provider that dies (quota after
    # its 429 retries, or a bad key/model) is disabled and the article
    # is retried on the other provider; the loop only stops when BOTH
    # providers are gone (scores so far are kept).
    #
    # Per-post write-back (2026-11-14): the write connection opens
    # before scoring, and each score is committed the moment it is
    # computed — a cancelled run keeps the posts it already scored.
    # Opening it here also fails fast if the DB is unreachable,
    # instead of after 200 scored posts. When --write-scores is off
    # or the run is a dry run, write_conn stays None and nothing is
    # written.
    # Naive local datetime for places.audit_llm_at (matches the app's
    # LocalDateTime / timestamp-without-time-zone columns; reuses the
    # same clock as the due-selection above).
    run_dt = run_now.replace(tzinfo=None)
    write_conn = None
    written = 0
    write_note = None
    if args.write_scores:
        write_conn = psycopg2.connect(
            db_url, connect_timeout=DB_CONNECT_TIMEOUT_SECONDS)

    def write_now(slug, total):
        """Commit one score immediately. On the first DB failure, log
        once and stop trying — the remaining posts stay due for the
        next run instead of crashing the loop."""
        nonlocal written, write_note, write_conn
        if write_conn is None:
            return
        try:
            written += write_one_llm_score(write_conn, slug, total,
                                           run_dt)
        except Exception as e:
            log(f"  WARNING: write-back failed for {slug} ({e}) — "
                f"stopping per-post writes; the remaining posts stay "
                f"due for the next run")
            write_conn = None
            write_note = (f"per-post write-back stopped after "
                          f"{written} posts: {e}")

    # Score one article at a time, rotating endpoints call by call.
    # A 429 fails over to the next endpoint after the 3s gap; an
    # endpoint that dies (daily cap, bad key/model, or 3 consecutive
    # 429s) drops out of the rotation; the loop only stops when ALL
    # endpoints are dead (scores so far are kept).
    #
    # Per-post write-back (2026-11-14): the write connection opens
    # before scoring, and each score is committed the moment it is
    # computed — a cancelled run keeps the posts it already scored.
    # Opening it here also fails fast if the DB is unreachable,
    # instead of after 200 scored posts. When --write-scores is off
    # or the run is a dry run, write_conn stays None and nothing is
    # written.
    rotator = Rotator(endpoints)
    rotation = " → ".join(p.label for p in endpoints) or "mock"
    gap = live_delay(endpoints)
    est_secs = len(to_score) * (gap + 3)
    log(f"Scoring {len(to_score)} articles with {model_label}, "
        f"rotation {rotation} (gap {gap}s, 429 fails over to the next "
        f"key after {gap}s, up to {MAX_ATTEMPTS_PER_POST} attempts per "
        f"post; est. ~{est_secs // 60}m{est_secs % 60}s)")
    results, failed = [], []
    quota_note = None
    for index, article in enumerate(to_score):
        call_t0 = time.monotonic()
        if args.mock_llm:
            # Mock mode: the canned response needs no endpoint.
            data = mock_llm_result(article)
            scores, reasons, verdict = validate_llm_result(data)
            total = round(sum(scores.values()) * 2.5, 1)
            results.append({"scores": scores, "total": total,
                            "verdict": verdict, "reasons": reasons})
            write_now(article["slug"], total)
            log(f"  [{index + 1}/{len(to_score)}] {article['slug']}: "
                f"{total} [{verdict}] "
                f"({time.monotonic() - call_t0:.1f}s)")
            continue
        try:
            scores, total, verdict, reasons, error = \
                score_article_rotating(article, rotator, index + 1,
                                       len(to_score))
        except AllEndpointsDead as e:
            quota_note = (f"quota reached after {len(results)} "
                          f"posts ({e}; "
                          f"{RATE_STATE['retries_429']} 429s hit "
                          f"across the run, "
                          f"{RATE_STATE['waited_429']}s of server-"
                          f"suggested waits failed over); remaining "
                          f"{len(to_score) - len(results)} due posts "
                          f"will be picked up by the next run")
            print(f"\n{quota_note}")
            break
        if error is not None:
            failed.append({"slug": article["slug"], "error": error})
            log(f"  {article['slug']}: FAILED ({error}) "
                f"({time.monotonic() - call_t0:.1f}s)")
            continue
        results.append({"scores": scores, "total": total,
                        "verdict": verdict, "reasons": reasons})
        write_now(article["slug"], total)
        log(f"  [{index + 1}/{len(to_score)}] {article['slug']}: "
            f"{total} [{verdict}] "
            f"({time.monotonic() - call_t0:.1f}s)")

    if write_conn is not None:
        write_conn.close()

    # Rows must align with results: failed slugs (and any posts not
    # reached after a quota stop) are excluded, in slug order.
    scored_articles = [a for a in to_score
                       if a["slug"] not in {f["slug"] for f in failed}][:len(results)]
    rows = build_rows(scored_articles, results)

    date = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d")
    meta = {"date": date, "source": source, "rows": len(rows),
            "loaded": len(articles), "scored": len(rows),
            "written": written, "write_note": write_note,
            "write_scores": args.write_scores,
            "selection": selection, "model": model_label,
            "providers": {p.label: {"provider": p.name,
                                    "model": p.model, "calls": p.calls}
                          for p in endpoints},
            "mock": args.mock_llm,
            "retries_429": RATE_STATE["retries_429"],
            "waited_429_seconds": RATE_STATE["waited_429"],
            "per_category": dict(Counter(a["category"] for a in articles))}

    args.output_dir.mkdir(parents=True, exist_ok=True)
    snapshot = {"date": date, "source": source, "count": len(articles),
                "per_category": meta["per_category"],
                "loaded": len(articles), "scored": len(rows),
                "selection": selection, "model": model_label,
                "mock": args.mock_llm,
                "slugs": sorted(a["slug"] for a in articles),
                "due_slugs": sorted(a["slug"] for a in due),
                "scored_slugs": sorted(r["slug"] for r in rows),
                "failed_slugs": sorted(f["slug"] for f in failed)}
    (args.output_dir / f"snapshot-{date}.json").write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")

    md = render_markdown(meta, rows, failed, quota_note, args.mock_llm)
    (args.output_dir / "llm-report.md").write_text(md, encoding="utf-8")
    (args.output_dir / "llm-report.json").write_text(json.dumps(
        {"run": "complete", "meta": meta, "quota_note": quota_note,
         "failed": failed, "rows": rows},
        ensure_ascii=False, indent=2), encoding="utf-8")

    if args.write_scores:
        print(f"LLM score write-back: {written}/{len(rows)} rows "
              f"written to the DB (per post, as scored)")

    dist = Counter(r["verdict"] for r in rows)
    log(f"Done in {time.monotonic() - _T0:.0f}s: {len(rows)} articles "
        f"scored, {len(failed)} failed — "
        f"KEEP {dist['KEEP']} / IMPROVE {dist['IMPROVE']} / "
        f"REWRITE {dist['REWRITE']}")
    if quota_note:
        print(f"Quota: {quota_note}")
    print(f"Reports written to {args.output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
