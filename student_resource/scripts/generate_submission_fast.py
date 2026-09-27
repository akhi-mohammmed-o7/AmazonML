"""
Submission Generator — Country-Partitioned Batched Approach.
Amazon ML Challenge 2026.

Strategy: Process one country at a time.
  For each country {US, India, France, ...}:
    1. Load all S1 entities for that country (small fraction of 1.7M)
    2. Load all S2+S3 candidates for that country into a CandidateBlocker
    3. Score every S1 against its blocked candidates
    4. Append results to the output files

This keeps RAM bounded to ~max(one country's S2+S3 candidates) at a time.
US is the largest partition but still fits in memory since we only store metadata.
"""

import csv
import os
import sys
import time
from collections import defaultdict

sys.path.insert(0, os.path.abspath("student_resource"))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from src.baseline import compute_pair_similarity
from src.blocking import CandidateBlocker

MATCH_THRESHOLD = 0.55
MAX_CANDIDATES  = 30


def scan_countries(filepath):
    """Quick scan to find all unique country values in a TSV."""
    countries = set()
    with open(filepath, "r", encoding="utf-8") as f:
        rdr = csv.reader(f, delimiter="\t")
        next(rdr)
        for row in rdr:
            if len(row) >= 4:
                c = row[3].strip()
                if c:
                    countries.add(c)
    return countries


def load_entities_by_country(filepath, target_country):
    """Load all rows matching target_country from a TSV. Returns dict of id->(name,addr,ctry)."""
    entities = {}
    with open(filepath, "r", encoding="utf-8") as f:
        rdr = csv.reader(f, delimiter="\t")
        next(rdr)
        for row in rdr:
            if len(row) < 4:
                continue
            if row[3].strip() == target_country:
                entities[row[0]] = (row[1], row[2], row[3].strip())
    return entities


def index_candidates_by_country(filepath, target_country, blocker):
    """Stream a candidate file, indexing only rows matching target_country."""
    n = 0
    with open(filepath, "r", encoding="utf-8") as f:
        rdr = csv.reader(f, delimiter="\t")
        next(rdr)
        for row in rdr:
            if len(row) < 4:
                continue
            if row[3].strip() == target_country:
                blocker.index_candidate(row[0], row[1], row[2], row[3].strip())
                n += 1
    return n


def generate_submission(s1_path, s2_path, s3_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    match_path = os.path.join(out_dir, "matching_results.tsv")
    cand_path  = os.path.join(out_dir, "candidate_pairs.tsv")

    print("=" * 60, flush=True)
    print("AMAZON ML 2026 — COUNTRY-PARTITIONED SUBMISSION", flush=True)
    print("=" * 60, flush=True)
    t0 = time.time()

    # Step 0: Discover countries from S1
    print("\n[Step 0] Scanning countries in S1...", flush=True)
    countries = scan_countries(s1_path)
    print(f"  Found {len(countries)} countries: {sorted(countries)}", flush=True)

    # Collect all results: s1_id -> (cand_list, match_list)
    all_results = {}
    all_s1_ids = []
    total_matched = 0
    total_singleton = 0

    for ci, country in enumerate(sorted(countries), 1):
        print(f"\n{'='*60}", flush=True)
        print(f"[Country {ci}/{len(countries)}] Processing: {country}", flush=True)
        print(f"{'='*60}", flush=True)
        tc = time.time()

        # 1. Load S1 entities for this country
        print(f"  Loading S1 entities for {country}...", flush=True)
        s1_entities = load_entities_by_country(s1_path, country)
        print(f"  S1: {len(s1_entities):,} entities ({time.time()-tc:.1f}s)", flush=True)
        all_s1_ids.extend(sorted(s1_entities.keys()))

        # 2. Build candidate index for this country
        blocker = CandidateBlocker()
        print(f"  Indexing S2 candidates for {country}...", flush=True)
        t_idx = time.time()
        n_s2 = index_candidates_by_country(s2_path, country, blocker)
        print(f"  S2: {n_s2:,} indexed ({time.time()-t_idx:.1f}s)", flush=True)

        print(f"  Indexing S3 candidates for {country}...", flush=True)
        t_idx2 = time.time()
        n_s3 = index_candidates_by_country(s3_path, country, blocker)
        print(f"  S3: {n_s3:,} indexed ({time.time()-t_idx2:.1f}s)", flush=True)

        total_cands = len(blocker.candidate_metadata)
        print(f"  Total candidates indexed: {total_cands:,}", flush=True)

        # 3. Score all S1 entities against candidates
        print(f"  Scoring {len(s1_entities):,} S1 entities...", flush=True)
        t_score = time.time()
        n_done = 0

        for s1_id, (s1_name, s1_addr, s1_ctry) in s1_entities.items():
            candidates = blocker.retrieve_candidates(
                s1_name, s1_addr, s1_ctry, max_candidates=MAX_CANDIDATES
            )

            matches = []
            for cid in candidates:
                c_name, c_addr, _ = blocker.candidate_metadata[cid]
                score = compute_pair_similarity(s1_name, s1_addr, c_name, c_addr)
                if score >= MATCH_THRESHOLD:
                    matches.append(cid)

            all_results[s1_id] = (candidates, matches)
            if matches:
                total_matched += 1
            else:
                total_singleton += 1

            n_done += 1
            if n_done % 100_000 == 0:
                elapsed = time.time() - t_score
                print(f"    {n_done:,}/{len(s1_entities):,} scored | "
                      f"{elapsed:.0f}s | {n_done/elapsed:,.0f} ent/s", flush=True)

        t_country = time.time() - tc
        print(f"  {country} done: {len(s1_entities):,} entities in {t_country:.1f}s "
              f"({len(s1_entities)/t_country:,.0f} ent/s)", flush=True)

        # Free memory for this country
        del blocker
        del s1_entities

    # Step 4: Write output files
    print(f"\n[Step 4] Writing output files...", flush=True)
    n_total = len(all_results)

    with open(match_path, "w", encoding="utf-8", newline="") as fm, \
         open(cand_path, "w", encoding="utf-8", newline="") as fc:

        mw = csv.writer(fm, delimiter="\t")
        cw = csv.writer(fc, delimiter="\t")
        mw.writerow(["source1_entity_id", "matched_entity_ids"])
        cw.writerow(["source1_entity_id", "candidate_entity_ids"])

        for s1_id in sorted(all_results.keys()):
            cands, matches = all_results[s1_id]
            cw.writerow([s1_id, ",".join(cands)])
            mw.writerow([s1_id, ",".join(matches)])

    t_total = time.time() - t0
    print("\n" + "=" * 60, flush=True)
    print("SUBMISSION COMPLETE", flush=True)
    print("=" * 60, flush=True)
    print(f"  S1 entities processed : {n_total:,}", flush=True)
    print(f"  Entities with matches : {total_matched:,}  ({total_matched/n_total*100:.1f}%)", flush=True)
    print(f"  Singletons            : {total_singleton:,}  ({total_singleton/n_total*100:.1f}%)", flush=True)
    print(f"  Total elapsed         : {t_total:.1f}s  ({t_total/60:.1f} min)", flush=True)
    print(f"  matching_results.tsv  : {os.path.getsize(match_path)/1e6:.2f} MB", flush=True)
    print(f"  candidate_pairs.tsv   : {os.path.getsize(cand_path)/1e6:.2f} MB", flush=True)
    print("=" * 60, flush=True)


if __name__ == "__main__":
    generate_submission(
        s1_path="student_resource/dataset/test/test_source1.tsv",
        s2_path="student_resource/dataset/test/test_source2.tsv",
        s3_path="student_resource/dataset/test/test_source3.tsv",
        out_dir="student_resource/output",
    )
