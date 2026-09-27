# Validation Strategy — Amazon ML Challenge 2026

**Generated:** 2026-09-26  
**Status:** COMPLETE (Stratified held-out set of 50,000 entities created)

---

## 1. Objective

To establish a strictly leakage-free, reproducible, competition-representative local validation framework that allows us to evaluate candidate blocking recall and matching model precision using the exact official macro $F_{0.5}$ metric before submitting to the leaderboard.

---

## 2. Validation Methodology & Leakage Prevention

### Anti-Leakage Protocol:
1. **Entity-Aware Partitioning:** All matches for a Source 1 entity are strictly bound to that entity. By sampling at the Source 1 entity level, there is zero risk of an entity being partially in train and partially in validation.
2. **Stratified Sampling:**
   - **Country:** Preserves the ~60% US / 40% India training distribution.
   - **Singleton Ratio:** Preserves the exact 5.58% singleton (0 true matches) ratio to ensure singleton penalty/reward dynamics accurately reflect leaderboard scoring.
3. **Fixed Random Seed:** Seed `42` is fixed for 100% reproducibility.

---

## 3. Dataset Characteristics

| Metric | Full Training Set | Held-out Validation Split |
|--------|-------------------|---------------------------|
| **Total S1 Reference Records** | 2,206,821 | **49,999** |
| **US Entities** | 1,323,633 (59.98%) | 29,998 (59.99%) |
| **India Entities** | 883,188 (40.02%) | 20,001 (40.01%) |
| **Singletons (0 matches)** | 123,247 (5.58%) | 2,793 (5.58%) |
| **Multi-Source Matched Entities** | 2,083,574 (94.42%) | 47,206 (94.42%) |

Files generated under `student_resource/data/processed/`:
- `val_source1.tsv`: Reference entities with columns `entity_id`, `business_name`, `business_address`, `country`.
- `val_ground_truth.tsv`: Labels with columns `source1_entity_id`, `matched_entity_ids`.

---

## 4. Evaluation Protocol

All models and candidate blocking techniques are evaluated using `student_resource/src/evaluate.py`:
- **Primary Metric:** Macro $F_{0.5}$ (weights Precision 2× over Recall)
- **Secondary Metrics:** Macro Precision, Macro Recall, Singleton Accuracy, Blocking Candidate Reduction Ratio, and Recall Ceiling.
