"""
Submission Generator for Amazon ML Challenge 2026.

Generates:
- output/matching_results.tsv (final entity matches, scored on leaderboard)
- output/candidate_pairs.tsv (candidate set from blocking stage)

Follows all official challenge formatting rules:
- UTF-8 tab-separated (.tsv)
- Exact headers: [source1_entity_id, matched_entity_ids] and [source1_entity_id, candidate_entity_ids]
- Exactly one row per test Source 1 entity
- Comma-separated IDs with no spaces, empty string for singletons
- No self-matches, no duplicates within a list
"""

import csv
import os
import sys
import time

sys.path.insert(0, os.path.abspath("student_resource"))

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from src.baseline import compute_pair_similarity
from src.blocking import CandidateBlocker


def generate_submission(
    test_s1_path: str,
    test_s2_path: str,
    test_s3_path: str,
    output_dir: str,
    index_candidate_limit: int = 5_000_000,
    match_threshold: float = 0.55
):
    os.makedirs(output_dir, exist_ok=True)
    matching_path = os.path.join(output_dir, "matching_results.tsv")
    candidate_path = os.path.join(output_dir, "candidate_pairs.tsv")

    print("=" * 60)
    print("ML CHALLENGE 2026 — SUBMISSION GENERATION PIPELINE")
    print("=" * 60)

    # 1. Build index from test S2 and S3 candidates
    blocker = CandidateBlocker()
    t0 = time.time()
    print(f"Building candidate index from test sources (limit: {index_candidate_limit:,} per source)...")

    n_s2 = 0
    with open(test_s2_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        next(reader)
        for i, row in enumerate(reader):
            if i >= index_candidate_limit:
                break
            if len(row) < 4:
                continue
            blocker.index_candidate(row[0], row[1], row[2], row[3])
            n_s2 += 1
            if n_s2 % 500000 == 0:
                print(f"  S2: {n_s2:,} indexed ({time.time() - t0:.1f}s)...")

    n_s3 = 0
    with open(test_s3_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        next(reader)
        for i, row in enumerate(reader):
            if i >= index_candidate_limit:
                break
            if len(row) < 4:
                continue
            blocker.index_candidate(row[0], row[1], row[2], row[3])
            n_s3 += 1
            if n_s3 % 500000 == 0:
                print(f"  S3: {n_s3:,} indexed ({time.time() - t0:.1f}s)...")

    print(f"Indexed {n_s2:,} S2 and {n_s3:,} S3 test records in {time.time() - t0:.2f}s.")
    print(f"Total active candidate index size: {len(blocker.candidate_metadata):,}")

    # 2. Process all Test Source 1 entities and stream output
    print(f"\nProcessing all Source 1 test records from {test_s1_path}...")
    t1 = time.time()
    total_processed = 0
    matched_count = 0
    singleton_count = 0

    with open(test_s1_path, "r", encoding="utf-8") as f_in, \
         open(matching_path, "w", encoding="utf-8", newline="") as f_match, \
         open(candidate_path, "w", encoding="utf-8", newline="") as f_cand:

        reader = csv.reader(f_in, delimiter="\t")
        header = next(reader)

        match_writer = csv.writer(f_match, delimiter="\t")
        cand_writer = csv.writer(f_cand, delimiter="\t")

        # Official exact headers
        match_writer.writerow(["source1_entity_id", "matched_entity_ids"])
        cand_writer.writerow(["source1_entity_id", "candidate_entity_ids"])

        for row in reader:
            total_processed += 1
            s1_id = row[0]
            s1_name = row[1] if len(row) > 1 else ""
            s1_addr = row[2] if len(row) > 2 else ""
            s1_ctry = row[3] if len(row) > 3 else ""

            # Retrieve candidates (max 20 per S1)
            candidates = blocker.retrieve_candidates(s1_name, s1_addr, s1_ctry, max_candidates=20)

            # Score candidates
            matches = []
            for cid in candidates:
                c_name, c_addr, _ = blocker.candidate_metadata[cid]
                score = compute_pair_similarity(s1_name, s1_addr, c_name, c_addr)
                if score >= match_threshold:
                    matches.append(cid)

            # Ensure final matches are a strict subset of candidates
            cand_str = ",".join(candidates)
            match_str = ",".join(matches)

            cand_writer.writerow([s1_id, cand_str])
            match_writer.writerow([s1_id, match_str])

            if matches:
                matched_count += 1
            else:
                singleton_count += 1

            if total_processed % 200000 == 0:
                elapsed = time.time() - t1
                print(f"  Processed {total_processed:,} entities ({elapsed:.1f}s, {total_processed/elapsed:.0f} rows/s)...")

    t_total = time.time() - t1
    print("\n" + "=" * 60)
    print("SUBMISSION GENERATION COMPLETE")
    print("=" * 60)
    print(f"  Total S1 entities processed:  {total_processed:,}")
    print(f"  Entities with matches:        {matched_count:,}")
    print(f"  Singletons (empty match list):{singleton_count:,}")
    print(f"  Elapsed runtime:              {t_total:.2f}s ({total_processed/t_total:.0f} entities/sec)")
    print(f"  Matching output file:         {matching_path}")
    print(f"  Candidate output file:        {candidate_path}")
    print("=" * 60)


if __name__ == "__main__":
    test_s1 = "student_resource/dataset/test/test_source1.tsv"
    test_s2 = "student_resource/dataset/test/test_source2.tsv"
    test_s3 = "student_resource/dataset/test/test_source3.tsv"
    out_dir = "student_resource/output"

    generate_submission(test_s1, test_s2, test_s3, out_dir, index_candidate_limit=5_000_000, match_threshold=0.55)
