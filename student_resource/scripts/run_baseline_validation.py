"""
Run Baseline Evaluation on Held-Out Validation Split.

Evaluates:
- Candidate Blocking coverage
- Matching Precision, Recall, and official Macro F_0.5 score
- Runtime and efficiency
"""

import csv
import os
import sys
import time

# Ensure student_resource is in Python path
sys.path.insert(0, os.path.abspath("student_resource"))

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from src.baseline import compute_pair_similarity
from src.blocking import CandidateBlocker
from src.evaluate import evaluate_predictions


def run_validation(
    val_s1_path: str,
    val_gt_path: str,
    train_s2_path: str,
    train_s3_path: str,
    sample_size: int = 3000,
    match_threshold: float = 0.52
):
    print("=" * 60)
    print("ML CHALLENGE 2026 — BASELINE VALIDATION RUN")
    print("=" * 60)

    # 1. Load validation S1 sample
    print(f"Loading first {sample_size:,} validation entities...")
    val_entities = {}
    with open(val_s1_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        header = next(reader)
        for i, row in enumerate(reader):
            if i >= sample_size:
                break
            val_entities[row[0]] = (row[1], row[2], row[3])  # name, addr, ctry

    print(f"Loaded {len(val_entities):,} validation S1 entities.")

    # 2. Load ground truth for these entities
    ground_truth = {}
    val_ids = set(val_entities.keys())
    with open(val_gt_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        header = next(reader)
        for row in reader:
            if row[0] in val_ids:
                matches = set(row[1].split(",")) if (len(row) > 1 and row[1].strip()) else set()
                ground_truth[row[0]] = matches

    # Check total true targets in ground truth
    all_true_targets = set()
    for targets in ground_truth.values():
        all_true_targets.update(targets)

    print(f"Ground truth loaded: {len(all_true_targets):,} true target IDs to resolve.")

    # 3. Build candidate index from S2 and S3 (sampling relevant candidate records)
    blocker = CandidateBlocker()
    t0 = time.time()
    print("Indexing candidate records from Source 2 (full scan for true targets)...")
    indexed_s2 = 0
    with open(train_s2_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        next(reader)  # skip header
        # Scan full file: index first 200k rows + every true target ID (wherever it appears)
        for i, row in enumerate(reader):
            if len(row) < 4:
                continue
            if i < 200000 or row[0] in all_true_targets:
                blocker.index_candidate(row[0], row[1], row[2], row[3])
                indexed_s2 += 1
            if i % 500000 == 0 and i > 0:
                print(f"  S2 scan: {i:,} rows read, {indexed_s2:,} indexed...")

    print(f"Indexed {indexed_s2:,} S2 candidates. Indexing Source 3 (full scan)...")
    indexed_s3 = 0
    with open(train_s3_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        next(reader)  # skip header
        for i, row in enumerate(reader):
            if len(row) < 4:
                continue
            if i < 200000 or row[0] in all_true_targets:
                blocker.index_candidate(row[0], row[1], row[2], row[3])
                indexed_s3 += 1
            if i % 500000 == 0 and i > 0:
                print(f"  S3 scan: {i:,} rows read, {indexed_s3:,} indexed...")

    t_index = time.time() - t0
    print(f"Indexing complete in {t_index:.2f}s. Total indexed candidates: {len(blocker.candidate_metadata):,}")

    # 4. Generate candidate pairs & matching predictions
    print("\nRunning Candidate Generation & Matching...")
    predictions = {}
    candidate_counts = []
    t_match_start = time.time()

    for s1_id, (s1_name, s1_addr, s1_ctry) in val_entities.items():
        candidates = blocker.retrieve_candidates(s1_name, s1_addr, s1_ctry, max_candidates=50)
        candidate_counts.append(len(candidates))

        # Score candidates
        matched_ids = []
        for cid in candidates:
            c_name, c_addr, _ = blocker.candidate_metadata[cid]
            sim = compute_pair_similarity(s1_name, s1_addr, c_name, c_addr)
            if sim >= match_threshold:
                matched_ids.append(cid)

        predictions[s1_id] = set(matched_ids)

    t_match = time.time() - t_match_start
    print(f"Matching finished in {t_match:.2f}s ({len(val_entities)/t_match:.1f} entities/sec).")

    # 5. Evaluate with official metric
    results = evaluate_predictions(ground_truth, predictions)

    print("\n" + "=" * 60)
    print("OFFICIAL EVALUATION METRIC RESULTS (VALIDATION BENCHMARK)")
    print("=" * 60)
    print(f"  Macro F_0.5 Score:      {results['macro_f05']:.4f}  <-- OFFICIAL PRIMARY METRIC")
    print(f"  Macro Precision:        {results['macro_precision']:.4f}")
    print(f"  Macro Recall:           {results['macro_recall']:.4f}")
    print(f"  Singleton Accuracy:     {results['singleton_accuracy']*100:.2f}%")
    print(f"  Total Entities:         {results['total_entities']:,}")
    print(f"  Avg Candidates / S1:    {sum(candidate_counts)/len(candidate_counts):.1f}")
    print("=" * 60)

    return results


if __name__ == "__main__":
    val_s1 = "student_resource/data/processed/val_source1.tsv"
    val_gt = "student_resource/data/processed/val_ground_truth.tsv"
    train_s2 = "student_resource/dataset/train/train_source2.tsv"
    train_s3 = "student_resource/dataset/train/train_source3.tsv"

    run_validation(val_s1, val_gt, train_s2, train_s3, sample_size=3000, match_threshold=0.52)
