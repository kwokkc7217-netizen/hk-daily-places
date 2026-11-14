# Content Audit — `tools/audit/audit.py`

Lean, deterministic content audit for hk-daily-places. Scores every
PUBLISHED article on five dimensions (A 30 / B 25 / C 20 / D 15 / E 10),
flags duplicate groups with char-bigram TF-IDF (reused from
`tools/related/related.py`, **without** its category boost), and writes a
Markdown + JSON report.

**No LLM calls. No API keys.** The database connection is read-only
unless `--write-scores` is given — and then it only ever updates the
three audit columns (`audit_score`, `audit_status`, `audited_at`),
never title or description.

## Daily design (score-once + rolling 30-day re-check)

The GitHub Actions workflow (`content-audit-daily`) runs this script
every day at 11:00 HKT with `--only-due --write-scores`:

* **All** PUBLISHED articles are loaded every run — the TF-IDF
  duplicate matrix needs the full corpus.
* Only **due** posts are scored and written back. Due means either:
  1. never checked (`audit_score IS NULL`), or
  2. last checked at least `--rescore-days` days ago (default 30; a
     check exactly 30 days old counts as due).
* The first daily run scores the whole corpus (~241 posts, all
  unchecked); afterwards it settles to roughly one new post a day plus
  rolling re-checks as older scores pass 30 days.
* The Gemini API key is **not** used by this script or its workflow —
  deterministic checks only. LLM scoring is a separate step.

To test the selection locally without a database, seed rows have no
audit columns, so they all count as due:

```bash
~/workspace/tools/pyvenv/bin/python tools/audit/audit.py \
  --from-seed src/main/resources/seed/bulk-places.json --only-due --dry-run
```

## Run it

Use the project venv (has `psycopg2-binary` + `scikit-learn`):

```bash
cd ~/workspace/hk-daily-places
~/workspace/tools/pyvenv/bin/python tools/audit/audit.py --help
```

### 1. Local test (no database, no credentials)

```bash
~/workspace/tools/pyvenv/bin/python tools/audit/audit.py \
  --from-seed src/main/resources/seed/bulk-places.json
```

### 2. Real audit (Neon, read-only)

```bash
export DATABASE_URL='postgres://...?sslmode=require'   # never paste this anywhere
~/workspace/tools/pyvenv/bin/python tools/audit/audit.py
```

Without `DATABASE_URL` and without `--from-seed`, the script exits with
code 2 and a clear error — it never guesses a connection string.

### Useful flags

| Flag | What it does |
|---|---|
| `--dry-run` | Count what would be processed; write nothing |
| `--max-articles N` | Process only the first N articles (by slug) |
| `--check-images` | HTTP HEAD each `imageUrl` + oEmbed each `youtubeId` (slower; without it, image/video checks are domain-only) |
| `--check-live` | Fetch the live sitemap for D11 reconciliation (counts `<loc>` entries) |
| `--output-dir DIR` | Where reports go (default `tools/audit/output/`) |
| `--write-scores` | Write `audit_score` / `audit_status` / `audited_at` back to `places` (DB mode only; refused in `--from-seed` mode; with `--dry-run` prints what would be written, writes nothing) |
| `--only-due` | Score only due posts (never checked, or audited at least `--rescore-days` ago). Full corpus is still loaded for duplicate detection |
| `--rescore-days N` | With `--only-due`: re-check posts last audited at least N days ago (default 30; exactly N days old counts as due) |

## Outputs (`tools/audit/output/`)

| File | Contents |
|---|---|
| `audit-report.md` | Human-readable report: score distribution, bottom-30 articles with reasons, duplicate groups with evidence, expansion candidates, consolidate/noindex candidates (decisions only — nothing is acted on), missing-original-info list, Content Improvement Plan |
| `audit-report.json` | Machine-readable rows (one per scored article) + duplicate groups; `meta.selection` records the selection rule used |
| `snapshot-<date>.json` | Frozen slug list + category counts for this run, plus the due subset (`due_slugs`) and the selection rule |

Scores are internal yardsticks, not Google's criteria. Every score
carries its evidence in the JSON rows. Mandatory rejection rules
(no sources, critically thin, no identifiable original value, substantial
duplication, unclear image rights) override the total score.

## Checks implemented (proposal §4.2, D1–D11)

D1 length/structure · D2 per-category practical-info markers (regex
heuristics) · D3 image domain + optional HEAD check · D4 YouTube oEmbed
check · D5 external links in description · D6 CJK-aware title duplicates
(punctuation/whitespace stripped only — **never** an ASCII-only strip,
which falsely merges unrelated Chinese titles) · D7 TF-IDF duplicate
groups (≥ 0.30 flagged, ≥ 0.50 high-risk, union-find clusters) ·
D8 slug-series review · D9 same-place pairs (shared CJK 3-grams) ·
D10 freshness (publishedAt vs createdAt; >30-day gaps are backdated
seed dates, not stale content) · D11 counts reconciliation (rows vs
`daily-cron-state.json` vs sitemap).

Processing is batched (~50 articles); `audit-report.json` is rewritten
after each batch, so an interrupted run leaves the last completed batch
on disk. Re-running is idempotent — outputs are overwritten.

## Do not commit the outputs

`tools/audit/output/` is working output, not source. The report files are
copied to the goal workspace for review; do not commit them to the repo.

## What this is not

* No LLM scoring — qualitative review (originality, real usefulness) is a
  separate step; see the Phase 1 proposal
  (`~/workspace/goals/hk-daily-places-content-audit-engine/files/phase-1-inspection-proposal.md`
  §5).
* No quality gate — the gate for future publishing is a later step, in
  the cron worker where generation actually happens.
* No production changes — this script never deletes, modifies, or
  unpublishes anything.
