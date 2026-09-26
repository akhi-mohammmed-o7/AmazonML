# Amazon ML Challenge 2026 — Business Entity Resolution

[![Competition](https://img.shields.io/badge/Amazon%20ML%20Challenge-2026-orange.svg)](https://unstop.com)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)]()

## 📌 Problem Overview
This repository contains our end-to-end, scientifically validated machine learning solution for the **Amazon ML Challenge 2026: Business Entity Resolution**.

Given business records across 3 independent data sources with noisy and inconsistent fields, the task is to resolve which records across sources refer to the exact same real-world business entity.

- **Source 1:** Deduplicated reference source (ground-truth hub).
- **Source 2 & Source 3:** Noisy business records (OCR artifacts, character transpositions, web domains, missing addresses).
- **Evaluation Metric:** Macro-averaged $F_{0.5}$ score (weights precision 2× over recall).

---

## 📂 Repository Structure

```
├── .gitignore
├── README.md                                 # Top-level overview
├── ps amazonml.pdf                           # Official problem statement
└── student_resource/
    ├── README.md                             # Official competition requirements
    ├── Documentation_template.md             # Official methodology submission write-up
    ├── PROJECT_STATUS.md                     # Live phase tracking
    ├── dataset/                              # Raw TSVs (ignored by git due to 3.3GB+ size)
    │   ├── train/
    │   └── test/
    ├── reports/                              # Analysis & architectural reports
    │   ├── workspace_inventory.md            # Comprehensive workspace file catalog
    │   ├── official_requirements.md          # Ground-truth verified requirements
    │   ├── dataset_catalog.md                # Row counts & schemas
    │   ├── dataset_schema.json               # Machine-readable schema metadata
    │   ├── data_relationships.md             # Cardinality & geographic partitioning analysis
    │   └── eda_report.md                     # Empirical findings & noise analysis
    ├── src/                                  # Core pipeline source code
    │   ├── preprocessing.py
    │   ├── blocking.py
    │   ├── feature_engineering.py
    │   ├── train.py
    │   └── predict.py
    ├── scripts/                              # Execution scripts
    └── utils/
        └── validate_submission.py            # Official submission format validator
```

---

## 🔬 Key Empirical Discoveries
1. **Zero Cross-Country Matches:** 100% of ground-truth matches are strictly intra-country ($0/167,056$ sampled pairs cross borders). Country serves as a zero-leakage, zero-recall-loss hard block.
2. **Missing Address Phenomenon:** ~3.3% of Source 2 and Source 3 records (~345k entities) completely lack address fields, requiring multi-key blocking.
3. **Unseen Country in Test:** Test set contains 259,452 entities from **France** (15.0% of test Source 1) that never appear in the training set.
4. **Cardinality:** 80.5% of reference entities match records in both Source 2 and Source 3 (average 3.46 matches per entity; 5.58% singletons).

---

## 🚀 Setup & Reproduction
Instructions to reproduce the pipeline from scratch:
1. Place raw TSV datasets into `student_resource/dataset/train/` and `student_resource/dataset/test/`.
2. Install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r student_resource/requirements.txt
   ```
3. Run the submission validator:
   ```bash
   python student_resource/utils/validate_submission.py --matching student_resource/output/matching_results.tsv --candidate student_resource/output/candidate_pairs.tsv --test-dir student_resource/dataset/test
   ```
