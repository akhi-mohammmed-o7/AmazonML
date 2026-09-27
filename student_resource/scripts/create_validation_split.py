"""
Validation Split Generator.

Creates a stratified, leakage-free held-out validation set from the training data.
- Preserves the country distribution (US vs India).
- Preserves the ground-truth singleton vs matched ratio.
- Holds out 50,000 Source 1 entities for fast, reproducible local validation.
"""

import csv
import os
import random
import sys

# Ensure UTF-8 output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


def create_validation_split(
    train_s1_path: str,
    train_gt_path: str,
    output_dir: str,
    val_size: int = 50000,
    seed: int = 42
):
    random.seed(seed)
    os.makedirs(output_dir, exist_ok=True)

    print(f"Reading training entities from {train_s1_path}...")
    s1_records = {}
    with open(train_s1_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        header = next(reader)
        for row in reader:
            if len(row) >= 4:
                # entity_id, business_name, business_address, country
                s1_records[row[0]] = (row[1], row[2], row[3])

    print(f"Loaded {len(s1_records):,} Source 1 training records.")

    print(f"Reading ground truth from {train_gt_path}...")
    ground_truth = {}
    with open(train_gt_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        gt_header = next(reader)
        for row in reader:
            s1_id = row[0]
            matches = row[1] if len(row) > 1 else ""
            ground_truth[s1_id] = matches

    # Stratify by country and singleton status
    strata = {}
    for s1_id, (name, addr, ctry) in s1_records.items():
        is_singleton = 1 if not ground_truth.get(s1_id, "").strip() else 0
        key = (ctry, is_singleton)
        if key not in strata:
            strata[key] = []
        strata[key].append(s1_id)

    total_entities = len(s1_records)
    val_ids = set()

    for key, id_list in strata.items():
        prop = len(id_list) / total_entities
        n_sample = int(round(prop * val_size))
        sampled = random.sample(id_list, min(n_sample, len(id_list)))
        val_ids.update(sampled)

    print(f"Selected {len(val_ids):,} validation entities across strata: {list(strata.keys())}")

    # Write val_source1.tsv
    val_s1_path = os.path.join(output_dir, "val_source1.tsv")
    with open(val_s1_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["entity_id", "business_name", "business_address", "country"])
        for s1_id in sorted(val_ids):
            name, addr, ctry = s1_records[s1_id]
            writer.writerow([s1_id, name, addr, ctry])

    # Write val_ground_truth.tsv
    val_gt_path = os.path.join(output_dir, "val_ground_truth.tsv")
    with open(val_gt_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["source1_entity_id", "matched_entity_ids"])
        for s1_id in sorted(val_ids):
            writer.writerow([s1_id, ground_truth.get(s1_id, "")])

    print(f"Validation set successfully saved:")
    print(f"  - {val_s1_path}")
    print(f"  - {val_gt_path}")


if __name__ == "__main__":
    train_s1 = "student_resource/dataset/train/train_source1.tsv"
    train_gt = "student_resource/dataset/train/train_ground_truth.tsv"
    out_dir = "student_resource/data/processed"
    create_validation_split(train_s1, train_gt, out_dir, val_size=50000, seed=42)
