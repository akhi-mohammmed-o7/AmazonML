# Dataset Catalog — Amazon ML Challenge 2026

**Generated:** 2026-09-26  
**Status:** COMPLETE (row counts verified from actual files)

---

## Dataset Overview

| Dataset | File | Rows (excl. header) | Columns | Size | Purpose |
|---------|------|---------------------|---------|------|---------|
| Train Source 1 | `train_source1.tsv` | **2,206,821** | 4 | 210 MB | Reference entities (deduplicated) |
| Train Source 2 | `train_source2.tsv` | **5,034,616** | 4 | 489 MB | Noisy business records |
| Train Source 3 | `train_source3.tsv` | **5,285,603** | 4 | 504 MB | Noisy business records |
| Train Ground Truth | `train_ground_truth.tsv` | **2,206,821** | 2 | 127 MB | Matching labels (1 row per S1 entity) |
| Test Source 1 | `test_source1.tsv` | **1,732,544** | 4 | 175 MB | Reference entities to predict for |
| Test Source 2 | `test_source2.tsv` | **4,887,273** | 4 | 509 MB | Test candidate records |
| Test Source 3 | `test_source3.tsv` | **5,082,316** | 4 | 506 MB | Test candidate records |

**Total records:** ~26.4 million across all files

---

## Column Schema (All Source Files)

| Column | Data Type | Description | Nullable? |
|--------|-----------|-------------|-----------|
| `entity_id` | string | Unique ID with prefix `S1-`/`S2-`/`S3-` | No (identifier) |
| `business_name` | string | Business name (noisy) | Possibly empty |
| `business_address` | string | Business address (noisy) | Possibly empty |
| `country` | string | Country label (`US`, `India`, `France` in test) | Possibly empty |

## Ground Truth Schema

| Column | Data Type | Description | Nullable? |
|--------|-----------|-------------|-----------|
| `source1_entity_id` | string | S1 entity ID | No |
| `matched_entity_ids` | string | Comma-separated S2/S3 IDs, empty for singletons | Yes (empty = singleton) |

---

## Sample Records

### Source 1 (Reference — Clean)
```
S1-925783039    Orelee's Barbershop    1795 Westchester Drive, High Point, NC    US
S1-755362802    Prabhav Business Center    797, Lake Town Block A, Kolkata, Howrah, West Bengal    India
```

### Source 2 (Noisy)
```
S2-764573417    -- Holloway Peak Inc Seafood    105 ELM ST, MORGANTON, NC    US
S2-49942811     Delta Tetlecommunication Inc    914 PIERPONT AVE, CLEVELAND, OH    US
```
**Observed:** Non-ASCII/garbled characters in Indian business names (likely Devanagari script encoding issues)

### Source 3 (Noisy)
```
S3-202863386    wilfordhancock.com    Mack Rd, Haltom City, Texas    US
S3-859268022    International South Consultants Private Ltd    [EMPTY ADDRESS]    India
```
**Observed:** Website-style names, empty addresses, garbled characters in addresses

### Ground Truth
```
S1-965667       S2-681193310,S2-743505751,S3-775321672,S3-11291185,S3-860443364   (5 matches)
S1-302869473    [EMPTY]                                                            (singleton)
S1-86989137     S3-274817120,S3-312496301                                          (S3 only)
```
**Observed:** Variable number of matches (0 to 6+ per S1 entity), some S1 entities match only S2, some only S3, some both

---

## Key Observations

1. **Scale:** ~2.2M reference entities, ~10.3M candidate entities (S2+S3 combined train) — blocking is CRITICAL
2. **Ground truth is complete:** 2,206,821 ground truth rows = 2,206,821 S1 train entities (1:1 correspondence)
3. **Encoding issues:** Source 2 and 3 contain garbled non-ASCII characters (likely Devanagari/Indic script)
4. **Missing data:** Source 3 has empty `business_address` fields
5. **Country distribution:** Training = {US, India}; Test adds **France** (unseen country!)
6. **ID format:** Numeric IDs after prefix (e.g., S1-925783039) — not sequential
7. **Singletons exist:** Some S1 entities have no matches at all

---

## Data Scale Warning

⚠️ **Naive Cartesian product** of S1 × (S2+S3):
- Train: 2.2M × 10.3M = ~22.7 TRILLION pairs — IMPOSSIBLE without blocking
- Test: 1.7M × 9.9M = ~17.2 TRILLION pairs — IMPOSSIBLE without blocking

**Blocking/candidate generation is the #1 engineering priority.**
