# Official Requirements — Amazon ML Challenge 2026

**Generated:** 2026-09-26  
**Source:** [README.md](file:///c:/Users/mohda/OneDrive/Desktop/hactons/amazonml/6ab10eb3b23ba_student_resource/student_resource/README.md) (VERIFIED)

---

## 1. Problem Statement

**OFFICIAL FACT:** This is a **Business Entity Resolution** challenge.

Business identity data arrives from **3 independent sources** — each contributing partial, noisy fragments about the same real-world business entities. There are **no common identifiers** across sources.

**Task:** Given noisy business records from 3 sources, determine which records across sources refer to the **same real-world business entity**.

---

## 2. Objective

**OFFICIAL FACT:** Source 1 is the **deduplicated reference source**.

For **every** Source 1 entity, find all matching records from Source 2 and Source 3.

A Source 1 entity may match **zero, one, or many** records from Source 2 and Source 3.

---

## 3. Input Data

**OFFICIAL FACT:** All files are **tab-separated (.tsv)**.

Each source file has 4 columns:

| Column | Description |
|--------|-------------|
| `entity_id` | Unique ID. Prefix indicates source: `S1-`, `S2-`, `S3-` |
| `business_name` | Name of business (noisy: abbreviations, typos, transliterations) |
| `business_address` | Address (noisy: partial, format variations, landmarks) |
| `country` | Country label. Training: `US`, `India`. Test: **additionally `France`** |

**OFFICIAL FACT:** There is NO separate source column — source is encoded in the `entity_id` prefix and the filename.

### Noise Patterns (OFFICIAL):
- **Names:** abbreviations (Corp/Corporation, Pvt/Private, Ltd/Limited), DBA names, `&` vs `and`, word-order transpositions, typos
- **Addresses:** abbreviations (Rd/Road, St/Street), transliteration variants, missing components, landmark references, component reordering

---

## 4. Output Requirements

**OFFICIAL FACT:** Two tab-separated files in `output/` folder:

### 4a. `matching_results.tsv` — SCORED on leaderboard

| Column | Description |
|--------|-------------|
| `source1_entity_id` | S1 entity ID |
| `matched_entity_ids` | Comma-separated S2/S3 IDs (empty for singletons) |

### 4b. `candidate_pairs.tsv` — NOT scored, used for pipeline audit

| Column | Description |
|--------|-------------|
| `source1_entity_id` | S1 entity ID |
| `candidate_entity_ids` | Comma-separated candidate S2/S3 IDs from blocking |

### Rules (OFFICIAL):
- Every S1 entity in test must have exactly one row
- Empty `matched_entity_ids` for singletons (no matches)
- No duplicate IDs within a list
- Only S2/S3 IDs that exist in test set
- No S1 self-matches
- Tab-separated, no pandas index
- Final matches must be a subset of candidates

---

## 5. Evaluation Metric

**OFFICIAL FACT:** **F_β Score (β = 0.5)** — precision-heavy

```
F_0.5 = (1.25 × Precision × Recall) / (0.25 × Precision + Recall)
```

- **Macro-averaged:** F_0.5 computed per S1 entity, then averaged across ALL S1 entities
- **Singletons included:** correctly predicting empty list → 1.0; false merge on singleton → 0.0
- **Precision-weighted:** precision counts 2× more than recall (false merges are worse than missed links)

---

## 6. Leaderboard

**OFFICIAL FACT:**
- **Public LB:** scored on a subset of test set (real-time feedback)
- **Private LB:** scored on remaining test set (revealed after challenge)
- **Final rankings:** based on Private LB
- You submit predictions for the FULL test set; the split is applied during scoring

---

## 7. Constraints & Rules

| Rule | Detail | Source |
|------|--------|--------|
| Format | Tab-separated, exact column names | OFFICIAL |
| Model license | MIT or Apache 2.0, up to 8B parameters | OFFICIAL |
| External data | **STRICTLY PROHIBITED** — no APIs, geocoding, business databases, web scraping | OFFICIAL |
| Validation | Must pass `utils/validate_submission.py` | OFFICIAL |
| Final package | ZIP with `output/`, `code/`, `Documentation_template.md` | OFFICIAL |

---

## 8. Final Submission Package Structure

```
<team_name>_submission.zip
├── output/
│   ├── matching_results.tsv
│   └── candidate_pairs.tsv
├── code/
│   └── business_entity_resolution/
│       ├── src/
│       ├── README.md
│       └── requirements.txt
└── Documentation_template.md
```

---

## 9. Key Strategic Insights (from Official Tips)

**OFFICIAL TIPS (verified from README):**
1. Invest in strong blocking — it determines recall upper bound
2. Explore string similarity features (Jaccard, Levenshtein, TF-IDF cosine)
3. Pay attention to country-specific address patterns
4. Consider precision-recall trade-off (F_0.5 rewards precision)
5. Don't neglect singletons — correctly predicting "no match" earns 1.0
6. Validate output format before submitting

---

## 10. Items NOT Specified

- No submission limit number stated in README
- No specific deadline mentioned in README
- No page limit for documentation (prioritize clarity and depth)
- No restriction on programming language (but Python implied by examples)
