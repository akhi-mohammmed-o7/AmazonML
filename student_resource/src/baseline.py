"""
Baseline Matching Engine for Amazon ML Challenge 2026.

Combines:
- Candidate Generation (Blocking) via inverted indexing
- String & Token Similarity Scoring (Jaccard, Character Tri-gram Dice)
- Address Number Matching & Missing-Address Handling
- Macro F_0.5 Calibrated Thresholding
"""

from typing import Dict, List, Set, Tuple
from src.preprocessing import (
    clean_text,
    extract_name_tokens,
    extract_numbers,
    normalize_address,
    normalize_business_name,
)


def jaccard_similarity(tokens1: Set[str], tokens2: Set[str]) -> float:
    """Compute Jaccard token similarity."""
    if not tokens1 or not tokens2:
        return 0.0
    intersection = len(tokens1 & tokens2)
    return intersection / (len(tokens1 | tokens2))


def ngram_dice_similarity(s1: str, s2: str, n: int = 3) -> float:
    """Compute character n-gram Dice coefficient (robust to OCR typos)."""
    if not s1 or not s2:
        return 0.0
    if len(s1) < n or len(s2) < n:
        return 1.0 if s1 == s2 else 0.0
    ng1 = {s1[i : i + n] for i in range(len(s1) - n + 1)}
    ng2 = {s2[i : i + n] for i in range(len(s2) - n + 1)}
    total = len(ng1) + len(ng2)
    if total == 0:
        return 0.0
    return 2.0 * len(ng1 & ng2) / total


def compute_pair_similarity(
    s1_name: str,
    s1_addr: str,
    cand_name: str,
    cand_addr: str
) -> float:
    """
    Compute pairwise similarity between a Source 1 entity and a candidate.
    Weights name similarity and address similarity.
    """
    # 1. Name Similarity
    s1_name_clean = normalize_business_name(s1_name)
    cand_name_clean = normalize_business_name(cand_name)

    s1_name_toks = set(extract_name_tokens(s1_name, min_len=2))
    cand_name_toks = set(extract_name_tokens(cand_name, min_len=2))

    name_jaccard = jaccard_similarity(s1_name_toks, cand_name_toks)
    name_dice = ngram_dice_similarity(s1_name_clean, cand_name_clean, n=3)
    name_score = max(name_jaccard, name_dice)

    # If names are exact match after normalization, high boost
    if s1_name_clean == cand_name_clean and s1_name_clean:
        name_score = max(name_score, 0.95)

    # 2. Address Similarity
    s1_addr_clean = normalize_address(s1_addr)
    cand_addr_clean = normalize_address(cand_addr)

    # Check if candidate has missing address (~3.3% of S2/S3)
    if not cand_addr_clean or not s1_addr_clean:
        # Solely rely on name similarity when address is unavailable
        return name_score * 0.90  # Slight penalty for lack of address verification

    s1_addr_toks = set(s1_addr_clean.split())
    cand_addr_toks = set(cand_addr_clean.split())
    addr_jaccard = jaccard_similarity(s1_addr_toks, cand_addr_toks)

    # Check address numbers (house numbers, postal codes)
    s1_nums = extract_numbers(s1_addr)
    cand_nums = extract_numbers(cand_addr)
    num_match = 1.0 if (s1_nums and cand_nums and (s1_nums & cand_nums)) else 0.0

    addr_score = 0.6 * addr_jaccard + 0.4 * num_match

    # Composite weighted score
    return 0.55 * name_score + 0.45 * addr_score
