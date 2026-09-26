# PROJECT STATUS — Amazon ML Challenge 2026

**Last Updated:** 2026-09-26

---

## Phase Checklist

- [x] Workspace inspected
- [x] Official documentation read
- [x] Dataset structure understood
- [x] Reports created: workspace_inventory.md, official_requirements.md, dataset_catalog.md, dataset_schema.json
- [x] Data quality analyzed (`reports/data_relationships.md`)
- [x] EDA completed (`reports/eda_report.md`)
- [ ] Preprocessing completed (`src/preprocessing.py`, `reports/preprocessing.md`)
- [ ] Validation strategy established (`reports/validation_strategy.md`)
- [ ] Baseline implemented
- [ ] Baseline evaluated
- [ ] Feature engineering completed (`reports/feature_dictionary.md`)
- [ ] Candidate generation / blocking completed (`src/blocking.py`, `reports/blocking_analysis.md`)
- [ ] Model experiments completed
- [ ] Error analysis completed (`reports/error_analysis.md`)
- [ ] Final model selected
- [ ] Test predictions generated
- [ ] Submission generated
- [ ] Submission validated (`utils/validate_submission.py`)
- [ ] Documentation completed (`Documentation_template.md`)
- [ ] Reproducibility tested

---

## Current Status: PHASES 1–4 COMPLETED

### Key Empirical Findings:
1. **Zero Cross-Country Matches:** Matches are 100% intra-country ($0/167,056$ sampled cross-country pairs). Country is a strict, loss-free blocking key.
2. **Missing Addresses:** ~3.3% of S2 and S3 records lack addresses completely (~344k records). Blocking cannot depend solely on addresses.
3. **Cardinality:** 80.5% of S1 entities match both S2 and S3. 5.58% are singletons. Total matches: 7,638,365. Average matches per entity: 3.46.
4. **Unseen Country in Test:** Test has 259,452 France entities (15.0% of test). All rules must generalize across languages.

### Next Step:
- Establish the **Validation Strategy** (`reports/validation_strategy.md`) and design **Data Preprocessing** (`src/preprocessing.py`, `reports/preprocessing.md`).
