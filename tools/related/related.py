#!/usr/bin/env python3
"""
Related-places recommender for hk-daily-places.

Offline batch job (runs on GitHub Actions weekly):
  1. SELECT slug/title/description of all PUBLISHED places from Postgres (Neon)
  2. TF-IDF over character bigrams (same idea as the Atlas Search lucene.cjk analyzer)
  3. Cosine similarity -> top-5 related slugs per article (excluding itself,
     below MIN_SCORE is dropped: 寧缺勿錯, fewer is better than wrong)
  4. UPDATE places SET related_slugs = '<json array>' (idempotent: full recompute)

Usage:
  python related.py            # dry run: print recommendations, write nothing
  python related.py --write    # actually UPDATE the DB

Env:
  DATABASE_URL  Neon Postgres connection string (needs ?sslmode=require)
"""
import json
import os
import sys

import psycopg2
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

MIN_SCORE = 0.06   # below this, a "related" article is not shown (tune after first real run)
TOP_N = 5

# Category display names, prepended to the corpus so same-category articles
# get a baseline similarity boost (tune: change the repeat count).
CATEGORY_NAMES = {
    "HIKING": "行山",
    "SHOPPING": "購物",
    "MOVIE": "睇戲",
    "FOOD": "食乜嘢",
}
CATEGORY_BOOST_REPEAT = 4


def load_articles(conn):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT slug, title, COALESCE(description, ''), category "
            "FROM places WHERE status = 'PUBLISHED' ORDER BY slug"
        )
        return cur.fetchall()


def build_corpus(rows):
    # Title repeated once so title words weigh more than description words;
    # category name repeated so same-category articles cluster together.
    corpus = []
    for _, title, desc, category in rows:
        cat = CATEGORY_NAMES.get(category, "")
        prefix = (cat + " ") * CATEGORY_BOOST_REPEAT if cat else ""
        corpus.append(f"{prefix}{title} {title} {desc}".strip())
    return corpus


def recommend(corpus):
    vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(2, 2))
    matrix = vectorizer.fit_transform(corpus)
    sim = cosine_similarity(matrix)
    n = len(corpus)
    results = []
    for i in range(n):
        scored = [(sim[i][j], j) for j in range(n) if j != i and sim[i][j] >= MIN_SCORE]
        scored.sort(reverse=True)
        results.append([j for _, j in scored[:TOP_N]])
    return results


def main():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL env var is not set", file=sys.stderr)
        sys.exit(1)
    write = "--write" in sys.argv

    conn = psycopg2.connect(db_url)
    try:
        rows = load_articles(conn)
        print(f"Loaded {len(rows)} published articles")
        if len(rows) < 2:
            print("Not enough articles to recommend anything.")
            return
        recs = recommend(build_corpus(rows))

        updates = []
        for (slug, title, _, _), idxs in zip(rows, recs):
            related = [rows[j][0] for j in idxs]
            updates.append((json.dumps(related, ensure_ascii=False), slug))
            rel_titles = [rows[j][1] for j in idxs]
            print(f"\n{title}")
            for t in rel_titles:
                print(f"  -> {t}")
            if not rel_titles:
                print("  (no related article above threshold)")

        if write:
            with conn.cursor() as cur:
                cur.executemany(
                    "UPDATE places SET related_slugs = %s WHERE slug = %s", updates
                )
            conn.commit()
            print(f"\nWrote related_slugs for {len(updates)} articles.")
        else:
            print("\nDry run only (no --write): nothing was written to the DB.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
