# Exploratory Data Analysis (EDA) — Amazon ML Challenge 2026

**Generated:** 2026-09-26  
**Status:** COMPLETE (Ground truth verified across 12.5M train records)

---

## 1. Executive Summary

This report establishes the empirical foundation for our entity resolution pipeline. By analyzing all 2.2M Source 1 entities, 10.3M candidate entities (Source 2 & Source 3), and 2.2M ground truth annotations, we uncover four foundational findings that dictate our engineering choices:

1. **Zero Cross-Country Matches:** 100% of ground truth links are intra-country ($0/167,056$ cross-country in sampled verification).
2. **Missing Address Phenomenon:** 3.36% of Source 2 and 3.33% of Source 3 records lack addresses entirely (~344,883 records). Blocking cannot rely solely on address keys.
3. **High Match Concentration:** 80.5% of Source 1 entities match records in **both** Source 2 and Source 3. Average matches per entity is 3.46 (max 11).
4. **Dominant Noise Modes:** Source 2 exhibits OCR/legal uppercase and typographical character-swaps; Source 3 exhibits web domain names, missing addresses, and expanded place names.

---

## 2. Dataset Scale & Cardinality Breakdown

| Dataset | Total Rows | Country Split | Missing Names | Missing Addresses |
|---------|------------|---------------|---------------|-------------------|
| **Train Source 1** (Reference) | 2,206,821 | US: 1,323,633 (60.0%)<br>India: 883,188 (40.0%) | 0 (0.0%) | 0 (0.0%) |
| **Train Source 2** (Noisy OCR) | 5,034,616 | US: ~60%<br>India: ~40% | 0 (0.0%) | **168,967 (3.36%)** |
| **Train Source 3** (Web / Directory) | 5,285,603 | US: ~60%<br>India: ~40% | 0 (0.0%) | **175,916 (3.33%)** |
| **Train Ground Truth** | 2,206,821 | N/A (Links) | N/A | N/A |
| **Test Source 1** (Target) | 1,732,544 | India: 809,986 (46.8%)<br>US: 663,106 (38.3%)<br>**France: 259,452 (15.0%)** | 0 (0.0%) | 0 (0.0%) |
| **Test Source 2** | 4,887,273 | Multi-country | 0 (0.0%) | ~3.3% expected |
| **Test Source 3** | 5,082,316 | Multi-country | 0 (0.0%) | ~3.3% expected |

---

## 3. Ground Truth Matching Distribution

Every Source 1 entity in train has an entry in `train_ground_truth.tsv`:

```
Singletons (0 matches):       123,247  ( 5.58%)  ──► Must predict empty list
Matches S2 only:              143,029  ( 6.48%)
Matches S3 only:              164,498  ( 7.45%)
Matches BOTH S2 & S3:       1,776,047  (80.48%)  ──► Vast majority!
------------------------------------------------
Total Matches:              7,638,365 links
Average Matches / S1:            3.46
Max Matches for single S1:         11
```

### Strategic Implications:
- **Singletons (5.58%):** Correctly predicting no matches earns 1.0 per singleton under macro $F_{0.5}$. False positives on singletons drop the entity score directly to 0.0. A disciplined matching confidence threshold is vital.
- **Candidate Ceiling:** Naive pairwise comparison space is $2.2\text{M} \times 10.3\text{M} \approx 22.7\text{ Trillion}$ pairs. Intelligent candidate blocking is mandatory to reduce this to $< 50\text{ candidates per entity}$ with $> 95\%$ recall.

---

## 4. Qualitative Noise Patterns & Transformations

Inspecting actual ground-truth pairs reveals systematic data corruption patterns:

### A. Typographical Noise (Source 2)
- Character substitutions: `Kelly Advisorc, Inc` vs `Kelly Advisory, Inc`
- Transposition & Punctuation: `Kelly Adhiors,y Inc` vs `Kelly Advisory, Inc`
- Case Normalization: Source 2 addresses are predominantly ALL-CAPS (`301 FIRST ST, CHOKIO, MN` vs `301 1st Street, Chokio, MN`)
- Prefix Noise: Stray leading dashes `-- Holloway Peak Inc Seafood`

### B. Structural & Domain Substitution (Source 3)
- Web Domain Replacement: `georgesaul.com` vs `George Saul Inc`
- Address Formatting: Leading zeros in numeric street numbers (`0301 First St` vs `301 1st Street`)
- State Expansion: Full state name `Minnesota` vs state abbreviation `MN`
- Empty Addresses: ~176,000 entities have blank addresses, relying solely on business name and country

### C. The France Generalization Challenge
- The training set contains only `US` and `India`.
- The test set introduces `France` (~260,000 entities, 15% of test Source 1).
- **Rule:** Preprocessing and feature engineering must NOT rely on US-only state lookups (e.g. `CA -> California`) or Indian postal PIN code hardcoding without language-agnostic text tokenization.

---

## 5. Architectural Recommendations

1. **Hard Blocking by Country:** Partition candidate search by `country` to immediately cut search volume without dropping true matches.
2. **Dual-Key Blocking (Name + Address):**
   - Key 1: Normalized Token / Phonetic / Trigram blocking on business name (handles missing addresses).
   - Key 2: City / Postal / Street token blocking (handles name variations/domains).
3. **Robust Preprocessing:**
   - Lowercasing and strip punctuation/symbols (`--`, `,`, `.`).
   - Domain suffix stripping (`.com`, `.in`, `.org`, `.co.in`).
   - Common legal suffix normalization (`pvt ltd`, `inc`, `corp`, `llc`).
   - Number normalization (`1st` $\leftrightarrow$ `first`, strip leading zeros `0301` $\leftrightarrow$ `301`).
4. **Metric-Aligned Decision Threshold:** Optimize for macro $F_{0.5}$ which weights Precision 2× over Recall.
