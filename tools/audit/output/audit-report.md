# hk-daily-places — Content Audit Report (2026-11-14)

- Source: seed:src/main/resources/seed/bulk-places.json (200 articles)
- Categories: {'MOVIE': 70, 'SHOPPING': 60, 'HIKING': 70}
- Mean total score: 26.2 / 100
- Status: PASS 0 / NEEDS_IMPROVEMENT 0 / FAIL 200
- Reconciliation (D11): DB/seed rows 200, state-file slugs 241, sitemap URLs None (skipped (run with --check-live))

Scores are internal yardsticks (A 30 / B 25 / C 20 / D 15 / E 10; 80+ PASS / 60–79 NEEDS_IMPROVEMENT / <60 FAIL) — not Google's criteria. Mandatory rejection rules override the number. Every score carries its evidence in the JSON rows.

## Score distribution by category

| Category | n | Mean | PASS | NEEDS | FAIL |
|---|---|---|---|---|---|
| HIKING | 70 | 24.0 | 0 | 0 | 70 |
| MOVIE | 70 | 32.0 | 0 | 0 | 70 |
| SHOPPING | 60 | 21.9 | 0 | 0 | 60 |

## Rejection flags (counts)

- R-SOURCES: 200
- R-THIN: 200
- R-NO-VALUE: 200
- R-IMAGE: 60

## Lowest-quality articles (bottom 30)

- **MegaBox：九龍灣巨型商場** (`megabox`, SHOPPING) — total 18 [FAIL] A0/B0/C16/D0/E2
  - 49 chars (length pts 0/15); analysis wording found: none (marker pts 0/15)
  - practical markers 0/5: found none; missing ['價錢', '$', '折', '交通', '地址']
  - flagged TF-IDF pair (>= 0.3): ['telford-plaza']
  - 0 external link(s) in description (none); no source link at all
  - 49 chars, 2 sentence(s), 1 paragraph(s); image: wikimedia
  - Rejection: R-SOURCES: no identifiable source link in description; R-THIN: description is 49 chars — critically incomplete for its stated subject; R-NO-VALUE: no identifiable original analysis (A=0)
- **將軍澳中心：將軍澳站上蓋** (`park-central`, SHOPPING) — total 18 [FAIL] A0/B0/C16/D0/E2
  - 56 chars (length pts 0/15); analysis wording found: none (marker pts 0/15)
  - practical markers 0/5: found none; missing ['價錢', '$', '折', '交通', '地址']
  - flagged TF-IDF pair (>= 0.3): ['the-lohas', 'popcorn-mall']
  - 0 external link(s) in description (none); no source link at all
  - 56 chars, 2 sentence(s), 1 paragraph(s); image: wikimedia
  - Rejection: R-SOURCES: no identifiable source link in description; R-THIN: description is 56 chars — critically incomplete for its stated subject; R-NO-VALUE: no identifiable original analysis (A=0)
- **PopCorn：將軍澳海濱商場** (`popcorn-mall`, SHOPPING) — total 18 [FAIL] A0/B0/C16/D0/E2
  - 56 chars (length pts 0/15); analysis wording found: none (marker pts 0/15)
  - practical markers 0/5: found none; missing ['價錢', '$', '折', '交通', '地址']
  - flagged TF-IDF pair (>= 0.3): ['park-central']
  - 0 external link(s) in description (none); no source link at all
  - 56 chars, 2 sentence(s), 1 paragraph(s); image: wikimedia
  - Rejection: R-SOURCES: no identifiable source link in description; R-THIN: description is 56 chars — critically incomplete for its stated subject; R-NO-VALUE: no identifiable original analysis (A=0)
- **蚺蛇尖：香港三尖之首** (`sharp-peak`, HIKING) — total 18 [FAIL] A0/B0/C16/D0/E2
  - 60 chars (length pts 0/15); analysis wording found: none (marker pts 0/15)
  - practical markers 0/8: found none; missing ['公里', '分鐘', '小時', '難度', '巴士', '港鐵', '起點', '終點']
  - flagged TF-IDF pair (>= 0.3): ['castle-peak']
  - 0 external link(s) in description (none); no source link at all
  - 60 chars, 2 sentence(s), 1 paragraph(s); image: wikimedia
  - Rejection: R-SOURCES: no identifiable source link in description; R-THIN: description is 60 chars — critically incomplete for its stated subject; R-NO-VALUE: no identifiable original analysis (A=0)
- **新港城：馬鞍山大地標** (`sunshine-city`, SHOPPING) — total 18 [FAIL] A0/B0/C16/D0/E2
  - 43 chars (length pts 0/15); analysis wording found: none (marker pts 0/15)
  - practical markers 0/5: found none; missing ['價錢', '$', '折', '交通', '地址']
  - flagged TF-IDF pair (>= 0.3): ['heng-on-plaza']
  - 0 external link(s) in description (none); no source link at all
  - 43 chars, 2 sentence(s), 1 paragraph(s); image: wikimedia
  - Rejection: R-SOURCES: no identifiable source link in description; R-THIN: description is 43 chars — critically incomplete for its stated subject; R-NO-VALUE: no identifiable original analysis (A=0)
- **德福廣場：九龍灣港鐵上蓋** (`telford-plaza`, SHOPPING) — total 18 [FAIL] A0/B0/C16/D0/E2
  - 56 chars (length pts 0/15); analysis wording found: none (marker pts 0/15)
  - practical markers 0/5: found none; missing ['價錢', '$', '折', '交通', '地址']
  - flagged TF-IDF pair (>= 0.3): ['megabox']
  - 0 external link(s) in description (none); no source link at all
  - 56 chars, 2 sentence(s), 1 paragraph(s); image: wikimedia
  - Rejection: R-SOURCES: no identifiable source link in description; R-THIN: description is 56 chars — critically incomplete for its stated subject; R-NO-VALUE: no identifiable original analysis (A=0)
- **日出康城：將軍澳新商場** (`the-lohas`, SHOPPING) — total 18 [FAIL] A0/B0/C16/D0/E2
  - 51 chars (length pts 0/15); analysis wording found: none (marker pts 0/15)
  - practical markers 0/5: found none; missing ['價錢', '$', '折', '交通', '地址']
  - flagged TF-IDF pair (>= 0.3): ['park-central']
  - 0 external link(s) in description (none); no source link at all
  - 51 chars, 2 sentence(s), 1 paragraph(s); image: wikimedia
  - Rejection: R-SOURCES: no identifiable source link in description; R-THIN: description is 51 chars — critically incomplete for its stated subject; R-NO-VALUE: no identifiable original analysis (A=0)
- **荃灣廣場：荃灣海濱商場** (`tsuen-wan-plaza`, SHOPPING) — total 18 [FAIL] A0/B0/C16/D0/E2
  - 46 chars (length pts 0/15); analysis wording found: none (marker pts 0/15)
  - practical markers 0/5: found none; missing ['價錢', '$', '折', '交通', '地址']
  - flagged TF-IDF pair (>= 0.3): ['citywalk-tsuen-wan']
  - 0 external link(s) in description (none); no source link at all
  - 46 chars, 2 sentence(s), 1 paragraph(s); image: wikimedia
  - Rejection: R-SOURCES: no identifiable source link in description; R-THIN: description is 46 chars — critically incomplete for its stated subject; R-NO-VALUE: no identifiable original analysis (A=0)
- **屯門市廣場：屯門心臟** (`tuen-mun-town-plaza`, SHOPPING) — total 18 [FAIL] A0/B0/C16/D0/E2
  - 49 chars (length pts 0/15); analysis wording found: none (marker pts 0/15)
  - practical markers 0/5: found none; missing ['價錢', '$', '折', '交通', '地址']
  - flagged TF-IDF pair (>= 0.3): ['pui-to-shan']
  - 0 external link(s) in description (none); no source link at all
  - 49 chars, 2 sentence(s), 1 paragraph(s); image: wikimedia
  - Rejection: R-SOURCES: no identifiable source link in description; R-THIN: description is 49 chars — critically incomplete for its stated subject; R-NO-VALUE: no identifiable original analysis (A=0)
- **青山：香港三尖之西** (`castle-peak`, HIKING) — total 21 [FAIL] A0/B3/C16/D0/E2
  - 57 chars (length pts 0/15); analysis wording found: none (marker pts 0/15)
  - practical markers 1/8: found ['小時']; missing ['公里', '分鐘', '難度', '巴士', '港鐵', '起點', '終點']
  - flagged TF-IDF pair (>= 0.3): ['sharp-peak', 'high-junk-peak']
  - 0 external link(s) in description (none); no source link at all
  - 57 chars, 2 sentence(s), 1 paragraph(s); image: wikimedia
  - Rejection: R-SOURCES: no identifiable source link in description; R-THIN: description is 57 chars — critically incomplete for its stated subject; R-NO-VALUE: no identifiable original analysis (A=0)
- **釣魚翁：西貢三尖膽小勿近** (`high-junk-peak`, HIKING) — total 21 [FAIL] A0/B3/C16/D0/E2
  - 56 chars (length pts 0/15); analysis wording found: none (marker pts 0/15)
  - practical markers 1/8: found ['小時']; missing ['公里', '分鐘', '難度', '巴士', '港鐵', '起點', '終點']
  - flagged TF-IDF pair (>= 0.3): ['castle-peak']
  - 0 external link(s) in description (none); no source link at all
  - 56 chars, 2 sentence(s), 1 paragraph(s); image: wikimedia
  - Rejection: R-SOURCES: no identifiable source link in description; R-THIN: description is 56 chars — critically incomplete for its stated subject; R-NO-VALUE: no identifiable original analysis (A=0)
- **姜山：大嶼中部連走** (`keung-shan`, HIKING) — total 21 [FAIL] A0/B3/C16/D0/E2
  - 59 chars (length pts 0/15); analysis wording found: none (marker pts 0/15)
  - practical markers 1/8: found ['小時']; missing ['公里', '分鐘', '難度', '巴士', '港鐵', '起點', '終點']
  - flagged TF-IDF pair (>= 0.3): ['kwun-yam-shan-lantau']
  - 0 external link(s) in description (none); no source link at all
  - 59 chars, 2 sentence(s), 1 paragraph(s); image: wikimedia
  - Rejection: R-SOURCES: no identifiable source link in description; R-THIN: description is 59 chars — critically incomplete for its stated subject; R-NO-VALUE: no identifiable original analysis (A=0)
- **谷埔：客家圍村加紅樹林** (`kuk-po`, HIKING) — total 21 [FAIL] A0/B3/C16/D0/E2
  - 53 chars (length pts 0/15); analysis wording found: none (marker pts 0/15)
  - practical markers 1/8: found ['小時']; missing ['公里', '分鐘', '難度', '巴士', '港鐵', '起點', '終點']
  - flagged TF-IDF pair (>= 0.3): ['lai-chi-wo']
  - 0 external link(s) in description (none); no source link at all
  - 53 chars, 2 sentence(s), 1 paragraph(s); image: wikimedia
  - Rejection: R-SOURCES: no identifiable source link in description; R-THIN: description is 53 chars — critically incomplete for its stated subject; R-NO-VALUE: no identifiable original analysis (A=0)
- **觀音山：大嶼中部觀景台** (`kwun-yam-shan-lantau`, HIKING) — total 21 [FAIL] A0/B3/C16/D0/E2
  - 56 chars (length pts 0/15); analysis wording found: none (marker pts 0/15)
  - practical markers 1/8: found ['小時']; missing ['公里', '分鐘', '難度', '巴士', '港鐵', '起點', '終點']
  - flagged TF-IDF pair (>= 0.3): ['keung-shan']
  - 0 external link(s) in description (none); no source link at all
  - 56 chars, 2 sentence(s), 1 paragraph(s); image: wikimedia
  - Rejection: R-SOURCES: no identifiable source link in description; R-THIN: description is 56 chars — critically incomplete for its stated subject; R-NO-VALUE: no identifiable original analysis (A=0)
- **荔枝窩：三百年客家圍村** (`lai-chi-wo`, HIKING) — total 21 [FAIL] A0/B3/C16/D0/E2
  - 59 chars (length pts 0/15); analysis wording found: none (marker pts 0/15)
  - practical markers 1/8: found ['小時']; missing ['公里', '分鐘', '難度', '巴士', '港鐵', '起點', '終點']
  - flagged TF-IDF pair (>= 0.3): ['kuk-po']
  - 0 external link(s) in description (none); no source link at all
  - 59 chars, 2 sentence(s), 1 paragraph(s); image: wikimedia
  - Rejection: R-SOURCES: no identifiable source link in description; R-THIN: description is 59 chars — critically incomplete for its stated subject; R-NO-VALUE: no identifiable original analysis (A=0)
- **浪茄灣：西貢第一灘** (`long-ke-wan`, HIKING) — total 21 [FAIL] A0/B3/C16/D0/E2
  - 61 chars (length pts 0/15); analysis wording found: none (marker pts 0/15)
  - practical markers 1/8: found ['小時']; missing ['公里', '分鐘', '難度', '巴士', '港鐵', '起點', '終點']
  - flagged TF-IDF pair (>= 0.3): ['maclehose-trail-1']
  - 0 external link(s) in description (none); no source link at all
  - 61 chars, 2 sentence(s), 1 paragraph(s); image: wikimedia
  - Rejection: R-SOURCES: no identifiable source link in description; R-THIN: description is 61 chars — critically incomplete for its stated subject; R-NO-VALUE: no identifiable original analysis (A=0)
- **杯渡山：屯門市肺** (`pui-to-shan`, HIKING) — total 21 [FAIL] A0/B3/C16/D0/E2
  - 55 chars (length pts 0/15); analysis wording found: none (marker pts 0/15)
  - practical markers 1/8: found ['小時']; missing ['公里', '分鐘', '難度', '巴士', '港鐵', '起點', '終點']
  - flagged TF-IDF pair (>= 0.3): ['tuen-mun-town-plaza']
  - 0 external link(s) in description (none); no source link at all
  - 55 chars, 2 sentence(s), 1 paragraph(s); image: wikimedia
  - Rejection: R-SOURCES: no identifiable source link in description; R-THIN: description is 55 chars — critically incomplete for its stated subject; R-NO-VALUE: no identifiable original analysis (A=0)
- **淘大商場：牛頭角街坊商場** (`amoy-plaza`, SHOPPING) — total 22 [FAIL] A0/B0/C20/D0/E2
  - 40 chars (length pts 0/15); analysis wording found: none (marker pts 0/15)
  - practical markers 0/5: found none; missing ['價錢', '$', '折', '交通', '地址']
  - no duplicate evidence: unique title, no TF-IDF pair >= 0.3
  - 0 external link(s) in description (none); no source link at all
  - 40 chars, 2 sentence(s), 1 paragraph(s); image: wikimedia
  - Rejection: R-SOURCES: no identifiable source link in description; R-THIN: description is 40 chars — critically incomplete for its stated subject; R-NO-VALUE: no identifiable original analysis (A=0)
- **apm：觀塘夜貓商場** (`apm-mall`, SHOPPING) — total 22 [FAIL] A0/B0/C20/D0/E2
  - 42 chars (length pts 0/15); analysis wording found: none (marker pts 0/15)
  - practical markers 0/5: found none; missing ['價錢', '$', '折', '交通', '地址']
  - no duplicate evidence: unique title, no TF-IDF pair >= 0.3
  - 0 external link(s) in description (none); no source link at all
  - 42 chars, 2 sentence(s), 1 paragraph(s); image: wikimedia
  - Rejection: R-SOURCES: no identifiable source link in description; R-THIN: description is 42 chars — critically incomplete for its stated subject; R-NO-VALUE: no identifiable original analysis (A=0)
- **旺角中心：潮流小店集中地** (`argyle-centre`, SHOPPING) — total 22 [FAIL] A0/B0/C20/D0/E2
  - 46 chars (length pts 0/15); analysis wording found: none (marker pts 0/15)
  - practical markers 0/5: found none; missing ['價錢', '$', '折', '交通', '地址']
  - no duplicate evidence: unique title, no TF-IDF pair >= 0.3
  - 0 external link(s) in description (none); no source link at all
  - 46 chars, 2 sentence(s), 1 paragraph(s); image: wikimedia
  - Rejection: R-SOURCES: no identifiable source link in description; R-THIN: description is 46 chars — critically incomplete for its stated subject; R-NO-VALUE: no identifiable original analysis (A=0)
- **甕缸群島：六角柱石海岸** (`bluff-island`, HIKING) — total 22 [FAIL] A0/B0/C20/D0/E2
  - 54 chars (length pts 0/15); analysis wording found: none (marker pts 0/15)
  - practical markers 0/8: found none; missing ['公里', '分鐘', '小時', '難度', '巴士', '港鐵', '起點', '終點']
  - no duplicate evidence: unique title, no TF-IDF pair >= 0.3
  - 0 external link(s) in description (none); no source link at all
  - 54 chars, 2 sentence(s), 1 paragraph(s); image: wikimedia
  - Rejection: R-SOURCES: no identifiable source link in description; R-THIN: description is 54 chars — critically incomplete for its stated subject; R-NO-VALUE: no identifiable original analysis (A=0)
- **鶴咀：燈塔蟹洞加鯨魚骨** (`cape-daguilar`, HIKING) — total 22 [FAIL] A0/B0/C20/D0/E2
  - 53 chars (length pts 0/15); analysis wording found: none (marker pts 0/15)
  - practical markers 0/8: found none; missing ['公里', '分鐘', '小時', '難度', '巴士', '港鐵', '起點', '終點']
  - no duplicate evidence: unique title, no TF-IDF pair >= 0.3
  - 0 external link(s) in description (none); no source link at all
  - 53 chars, 2 sentence(s), 1 paragraph(s); image: wikimedia
  - Rejection: R-SOURCES: no identifiable source link in description; R-THIN: description is 53 chars — critically incomplete for its stated subject; R-NO-VALUE: no identifiable original analysis (A=0)
- **長沙灣廣場：時裝批發城** (`cheung-sha-wan-plaza`, SHOPPING) — total 22 [FAIL] A0/B0/C20/D0/E2
  - 51 chars (length pts 0/15); analysis wording found: none (marker pts 0/15)
  - practical markers 0/5: found none; missing ['價錢', '$', '折', '交通', '地址']
  - no duplicate evidence: unique title, no TF-IDF pair >= 0.3
  - 0 external link(s) in description (none); no source link at all
  - 51 chars, 2 sentence(s), 1 paragraph(s); image: wikimedia
  - Rejection: R-SOURCES: no identifiable source link in description; R-THIN: description is 51 chars — critically incomplete for its stated subject; R-NO-VALUE: no identifiable original analysis (A=0)
- **春秧街：北角電車街市** (`chun-yeung-street`, SHOPPING) — total 22 [FAIL] A0/B0/C20/D0/E2
  - 58 chars (length pts 0/15); analysis wording found: none (marker pts 0/15)
  - practical markers 0/5: found none; missing ['價錢', '$', '折', '交通', '地址']
  - no duplicate evidence: unique title, no TF-IDF pair >= 0.3
  - 0 external link(s) in description (none); no source link at all
  - 58 chars, 2 sentence(s), 1 paragraph(s); image: wikimedia
  - Rejection: R-SOURCES: no identifiable source link in description; R-THIN: description is 58 chars — critically incomplete for its stated subject; R-NO-VALUE: no identifiable original analysis (A=0)
- **太古城中心：港島東大地標** (`cityplaza`, SHOPPING) — total 22 [FAIL] A0/B0/C20/D0/E2
  - 44 chars (length pts 0/15); analysis wording found: none (marker pts 0/15)
  - practical markers 0/5: found none; missing ['價錢', '$', '折', '交通', '地址']
  - no duplicate evidence: unique title, no TF-IDF pair >= 0.3
  - 0 external link(s) in description (none); no source link at all
  - 44 chars, 2 sentence(s), 1 paragraph(s); image: wikimedia
  - Rejection: R-SOURCES: no identifiable source link in description; R-THIN: description is 44 chars — critically incomplete for its stated subject; R-NO-VALUE: no identifiable original analysis (A=0)
- **愉景新城：荃灣老牌大商場** (`discovery-park`, SHOPPING) — total 22 [FAIL] A0/B0/C20/D0/E2
  - 47 chars (length pts 0/15); analysis wording found: none (marker pts 0/15)
  - practical markers 0/5: found none; missing ['價錢', '$', '折', '交通', '地址']
  - no duplicate evidence: unique title, no TF-IDF pair >= 0.3
  - 0 external link(s) in description (none); no source link at all
  - 47 chars, 2 sentence(s), 1 paragraph(s); image: wikimedia
  - Rejection: R-SOURCES: no identifiable source link in description; R-THIN: description is 47 chars — critically incomplete for its stated subject; R-NO-VALUE: no identifiable original analysis (A=0)
- **東港城：坑口地標** (`east-point-city`, SHOPPING) — total 22 [FAIL] A0/B0/C20/D0/E2
  - 49 chars (length pts 0/15); analysis wording found: none (marker pts 0/15)
  - practical markers 0/5: found none; missing ['價錢', '$', '折', '交通', '地址']
  - no duplicate evidence: unique title, no TF-IDF pair >= 0.3
  - 0 external link(s) in description (none); no source link at all
  - 49 chars, 2 sentence(s), 1 paragraph(s); image: wikimedia
  - Rejection: R-SOURCES: no identifiable source link in description; R-THIN: description is 49 chars — critically incomplete for its stated subject; R-NO-VALUE: no identifiable original analysis (A=0)
- **圓方：九龍站上蓋名店城** (`elements-mall`, SHOPPING) — total 22 [FAIL] A0/B0/C20/D0/E2
  - 44 chars (length pts 0/15); analysis wording found: none (marker pts 0/15)
  - practical markers 0/5: found none; missing ['價錢', '$', '折', '交通', '地址']
  - no duplicate evidence: unique title, no TF-IDF pair >= 0.3
  - 0 external link(s) in description (none); no source link at all
  - 44 chars, 2 sentence(s), 1 paragraph(s); image: wikimedia
  - Rejection: R-SOURCES: no identifiable source link in description; R-THIN: description is 44 chars — critically incomplete for its stated subject; R-NO-VALUE: no identifiable original analysis (A=0)
- **又一城：九龍塘貴氣商場** (`festival-walk`, SHOPPING) — total 22 [FAIL] A0/B0/C20/D0/E2
  - 43 chars (length pts 0/15); analysis wording found: none (marker pts 0/15)
  - practical markers 0/5: found none; missing ['價錢', '$', '折', '交通', '地址']
  - no duplicate evidence: unique title, no TF-IDF pair >= 0.3
  - 0 external link(s) in description (none); no source link at all
  - 43 chars, 2 sentence(s), 1 paragraph(s); image: wikimedia
  - Rejection: R-SOURCES: no identifiable source link in description; R-THIN: description is 43 chars — critically incomplete for its stated subject; R-NO-VALUE: no identifiable original analysis (A=0)
- **花墟：旺角花市** (`flower-market`, SHOPPING) — total 22 [FAIL] A0/B0/C20/D0/E2
  - 48 chars (length pts 0/15); analysis wording found: none (marker pts 0/15)
  - practical markers 0/5: found none; missing ['價錢', '$', '折', '交通', '地址']
  - no duplicate evidence: unique title, no TF-IDF pair >= 0.3
  - 0 external link(s) in description (none); no source link at all
  - 48 chars, 2 sentence(s), 1 paragraph(s); image: wikimedia
  - Rejection: R-SOURCES: no identifiable source link in description; R-THIN: description is 48 chars — critically incomplete for its stated subject; R-NO-VALUE: no identifiable original analysis (A=0)

## Duplicate groups (TF-IDF, no category boost)

Pairs ≥ 0.3: 12 (0 high-risk ≥ 0.5); clusters: 10

- Cluster: castle-peak, high-junk-peak, sharp-peak
- Cluster: park-central, popcorn-mall, the-lohas
- Cluster: citywalk-tsuen-wan, tsuen-wan-plaza
- Cluster: heng-on-plaza, sunshine-city
- Cluster: keung-shan, kwun-yam-shan-lantau
- Cluster: kuk-po, lai-chi-wo
- Cluster: long-ke-wan, maclehose-trail-1
- Cluster: megabox, telford-plaza
- Cluster: pui-to-shan, tuen-mun-town-plaza
- Cluster: weathering-with-you, your-name-2016
- `long-ke-wan` ↔ `maclehose-trail-1` — 0.434 (flag), shared terms: 浪茄, 茄灣, 第一, 灘 , 一段
- `castle-peak` ↔ `sharp-peak` — 0.416 (flag), shared terms: 港三, 三尖, 尖之, 青山, 香港
- `keung-shan` ↔ `kwun-yam-shan-lantau` — 0.388 (flag), shared terms: 中部, 大嶼, 嶼中, 觀音, 音山
- `citywalk-tsuen-wan` ↔ `tsuen-wan-plaza` — 0.347 (flag), shared terms: 荃灣,  荃, ：荃, 商場, 場 
- `heng-on-plaza` ↔ `sunshine-city` — 0.33 (flag), shared terms: 鞍山, 馬鞍, ：馬, 商場, 係馬
- `kuk-po` ↔ `lai-chi-wo` — 0.33 (flag), shared terms: 客家, 家圍, 圍村, 賣客, 店賣
- `megabox` ↔ `telford-plaza` — 0.324 (flag), shared terms: 龍灣, 九龍, ：九, ox, bo
- `park-central` ↔ `the-lohas` — 0.323 (flag), shared terms: 將軍, 軍澳, ：將, 站上, 上蓋
- `pui-to-shan` ↔ `tuen-mun-town-plaza` — 0.322 (flag), shared terms: 屯門, 門市, ：屯, 公路, 市中
- `castle-peak` ↔ `high-junk-peak` — 0.321 (flag), shared terms: 三尖, 青山, 港三, 釣魚, 魚翁
- `weathering-with-you` ↔ `your-name-2016` — 0.321 (flag), shared terms: 海誠, 新海, ：新, 名字, 的名
- `park-central` ↔ `popcorn-mall` — 0.319 (flag), shared terms: 將軍, 軍澳, ：將, 澳站, 海濱

## Same-place pairs (shared CJK 3-gram in titles)

- `long-ke-wan` ↔ `maclehose-trail-1` — TF-IDF 0.434, shared: 浪茄灣
- `castle-peak` ↔ `sharp-peak` — TF-IDF 0.416, shared: 三尖之, 港三尖
- `keung-shan` ↔ `kwun-yam-shan-lantau` — TF-IDF 0.388, shared: 大嶼中, 山大嶼, 嶼中部
- `heng-on-plaza` ↔ `sunshine-city` — TF-IDF 0.33, shared: 馬鞍山
- `kuk-po` ↔ `lai-chi-wo` — TF-IDF 0.33, shared: 客家圍, 家圍村
- `megabox` ↔ `telford-plaza` — TF-IDF 0.324, shared: 九龍灣
- `park-central` ↔ `the-lohas` — TF-IDF 0.323, shared: 將軍澳
- `pui-to-shan` ↔ `tuen-mun-town-plaza` — TF-IDF 0.322, shared: 屯門市
- `weathering-with-you` ↔ `your-name-2016` — TF-IDF 0.321, shared: 新海誠
- `park-central` ↔ `popcorn-mall` — TF-IDF 0.319, shared: 將軍澳
- `spider-man-no-way-home` ↔ `spider-verse-2018` — TF-IDF 0.291, shared: 蜘蛛俠
- `park-central` ↔ `po-lam-plaza` — TF-IDF 0.29, shared: 將軍澳
- `po-lam-plaza` ↔ `the-lohas` — TF-IDF 0.285, shared: 將軍澳
- `choi-ming-plaza` ↔ `heng-on-plaza` — TF-IDF 0.277, shared: 坊商場, 街坊商
- `fa-yuen-street` ↔ `sneaker-street` — TF-IDF 0.269, shared: 花園街

## Slug series

- `hongkong-trail*`: hongkong-trail-1, hongkong-trail-8 — max within-group TF-IDF 0.146, mean 0.146 (a series is legitimate only if the descriptions differ; check the pair scores above)
- `maclehose-trail*`: maclehose-trail-1, maclehose-trail-2, maclehose-trail-3, maclehose-trail-4, maclehose-trail-7, maclehose-trail-8 — max within-group TF-IDF 0.187, mean 0.141 (a series is legitimate only if the descriptions differ; check the pair scores above)
- `wilson-trail*`: wilson-trail-1, wilson-trail-3 — max within-group TF-IDF 0.184, mean 0.184 (a series is legitimate only if the descriptions differ; check the pair scores above)

## Expansion candidates (highest total score — closest to PASS)

- **《阿飛正傳》：王家衛成名作** (`days-of-being-wild`, MOVIE) — total 41 [FAIL] — needs first-hand material: own visit/photos, prices, route notes, personal judgement to lift A and D above the heuristic ceiling
- **《春光乍洩》：阿根廷嘅愛情流浪** (`happy-together`, MOVIE) — total 41 [FAIL] — needs first-hand material: own visit/photos, prices, route notes, personal judgement to lift A and D above the heuristic ceiling
- **《少林足球》：功夫加足球** (`shaolin-soccer`, MOVIE) — total 41 [FAIL] — needs first-hand material: own visit/photos, prices, route notes, personal judgement to lift A and D above the heuristic ceiling
- **《毒舌大狀》：票房破億喜劇** (`a-guilty-conscience`, MOVIE) — total 34 [FAIL] — needs first-hand material: own visit/photos, prices, route notes, personal judgement to lift A and D above the heuristic ceiling
- **《桃姐》：主僕情金像經典** (`a-simple-life`, MOVIE) — total 34 [FAIL] — needs first-hand material: own visit/photos, prices, route notes, personal judgement to lift A and D above the heuristic ceiling
- **《芭比》：粉紅女權喜劇** (`barbie-2023`, MOVIE) — total 34 [FAIL] — needs first-hand material: own visit/photos, prices, route notes, personal judgement to lift A and D above the heuristic ceiling
- **《幻愛》：思覺失調愛情故事** (`beyond-the-dream`, MOVIE) — total 34 [FAIL] — needs first-hand material: own visit/photos, prices, route notes, personal judgement to lift A and D above the heuristic ceiling
- **《媽樣年華》：師奶追夢輕喜劇** (`bird-of-paradise-2026`, MOVIE) — total 34 [FAIL] — needs first-hand material: own visit/photos, prices, route notes, personal judgement to lift A and D above the heuristic ceiling
- **《十月圍城》：群星保衛孫中山** (`bodyguards-and-assassins`, MOVIE) — total 34 [FAIL] — needs first-hand material: own visit/photos, prices, route notes, personal judgement to lift A and D above the heuristic ceiling
- **《重慶森林》：王家衛都市寓言** (`chungking-express`, MOVIE) — total 34 [FAIL] — needs first-hand material: own visit/photos, prices, route notes, personal judgement to lift A and D above the heuristic ceiling

## Consolidate / noindex candidates — DECISIONS ONLY, not actions

These slugs sit in high-risk duplicate groups. Nothing here is deleted, unpublished, or noindexed by this audit — a human decides per group whether to merge, expand one into the other, or noindex the weaker one.

- (none)

## Missing original information (corpus-wide, per category)

- HIKING: most-often-missing practical markers: 難度 (missing in 70 articles), 港鐵 (missing in 70 articles), 起點 (missing in 70 articles), 分鐘 (missing in 67 articles), 巴士 (missing in 66 articles)
- MOVIE: most-often-missing practical markers: 分鐘 (missing in 70 articles), 導演 (missing in 67 articles), 主演 (missing in 25 articles)
- SHOPPING: most-often-missing practical markers: $ (missing in 60 articles), 折 (missing in 60 articles), 地址 (missing in 60 articles), 交通 (missing in 58 articles), 價錢 (missing in 55 articles)

Across the corpus, first-hand material is absent: no article stores a source link, no article carries own photos, and the median description is a single sentence. Those three gaps are the AdSense problem in one line.

## Content Improvement Plan

### 1. Expand first (highest leverage)

- `days-of-being-wild` — expand with a real visit: own photos, prices/transport, and a personal verdict. Currently 41/100.
- `happy-together` — expand with a real visit: own photos, prices/transport, and a personal verdict. Currently 41/100.
- `shaolin-soccer` — expand with a real visit: own photos, prices/transport, and a personal verdict. Currently 41/100.
- `a-guilty-conscience` — expand with a real visit: own photos, prices/transport, and a personal verdict. Currently 34/100.
- `a-simple-life` — expand with a real visit: own photos, prices/transport, and a personal verdict. Currently 34/100.

### 2. What a genuine article must contain (per-category template)

- HIKING: distance, duration, elevation, difficulty, start/end, transport, own route notes and photos.
- SHOPPING: categories, price ranges, transport, comparison with a similar mall, own shopping notes.
- MOVIE: release date, runtime, director/cast, comparison with a similar film, audience suitability, HK cinema availability.
- FOOD: location, menu prices, per-person spend, transport, value-for-money verdict, own meal notes and photos.

### 3. Quality gate for future publishing (checklist)

1. No first-hand material (visit / own photos / own notes) → do not publish as an original article.
2. Duplicate check: TF-IDF pair ≥ 0.50 against any live article → reject or merge.
3. Every factual claim needs a source link in the article body.
4. Image must be own photo or a clearly licensed source — YouTube thumbnails as hero images are not acceptable.
5. Maximum one article per day; no forced publishing — if no candidate passes, publish nothing.

### 4. Stop doing

- Publishing one-liner posts daily for the sake of frequency.
- Hotlinking a thumbnail as the hero image.
- Publishing without any source link in the body.

## Limitations

- A/B/D/E sub-scores are deterministic heuristics on the text, not LLM judgements; they measure the text, they do not verify facts. Qualitative review of a stratified sample is a separate step (Phase 1 proposal §5).
- TF-IDF is lexical, not semantic: paraphrased duplicates can score low; same-place-different-angle articles can score high. Treat pairs as evidence, not verdicts.
- Seed-mode runs have no createdAt, so D10 freshness is unavailable there; backdated publishedAt values are seed dates, not real publication dates.
