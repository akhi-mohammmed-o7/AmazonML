"""
Candidate Generation (Blocking) Module for Amazon ML Challenge 2026.

Reduces comparison space from O(N * M) to O(K) candidates per entity using:
1. Hard country partitioning (100% precision preservation, verified empirically).
2. Distinctive name token inverted indexing.
3. Number / Street token inverted indexing.
"""

from collections import defaultdict
import re
from typing import Dict, List, Set, Tuple

from src.preprocessing import (
    clean_text,
    extract_name_tokens,
    extract_numbers,
    normalize_address,
    normalize_business_name,
)

# Common words to exclude from index keys to prevent explosion
STOP_TOKENS = {
    'pvt', 'ltd', 'inc', 'corp', 'llc', 'llp', 'co', 'and', 'the', 'of', 'in',
    'at', 'by', 'for', 'with', 'street', 'road', 'avenue', 'boulevard', 'lane',
    'drive', 'court', 'place', 'floor', 'apt', 'suite', 'unit', 'building',
    'bldg', 'near', 'opp', 'opposite', 'behind', 'block', 'sector', 'nagar',
    'road', 'dist', 'state', 'india', 'us', 'usa', 'france'
}


class CandidateBlocker:
    """Multi-key inverted index blocker partitioned by country."""

    def __init__(self):
        # country -> token -> set of candidate entity_ids
        self.name_index = defaultdict(lambda: defaultdict(set))
        self.num_index = defaultdict(lambda: defaultdict(set))
        self.candidate_metadata = {}

    def index_candidate(self, entity_id: str, name: str, address: str, country: str):
        """Add an S2 or S3 candidate record to the inverted index."""
        self.candidate_metadata[entity_id] = (name, address, country)

        # 1. Name tokens
        name_tokens = extract_name_tokens(name, min_len=3)
        for tok in name_tokens:
            if tok not in STOP_TOKENS:
                self.name_index[country][tok].add(entity_id)

        # 2. Number tokens in address
        numbers = extract_numbers(address)
        for num in numbers:
            # Index distinctive numbers (e.g. house numbers, PIN codes)
            if len(num) >= 2 and num not in STOP_TOKENS:
                self.num_index[country][num].add(entity_id)

    def retrieve_candidates(
        self,
        name: str,
        address: str,
        country: str,
        max_candidates: int = 50
    ) -> List[str]:
        """Retrieve candidate IDs for an S1 entity within the same country."""
        country_name_idx = self.name_index.get(country, {})
        country_num_idx = self.num_index.get(country, {})

        candidate_scores = defaultdict(int)

        # Query name tokens
        s1_name_tokens = extract_name_tokens(name, min_len=3)
        for tok in s1_name_tokens:
            if tok not in STOP_TOKENS and tok in country_name_idx:
                for cid in country_name_idx[tok]:
                    candidate_scores[cid] += 3  # Higher weight for name match

        # Query number tokens
        s1_numbers = extract_numbers(address)
        for num in s1_numbers:
            if len(num) >= 2 and num in country_num_idx:
                for cid in country_num_idx[num]:
                    candidate_scores[cid] += 2  # Address number match

        if not candidate_scores:
            return []

        # Sort candidates by match frequency/score and return top K
        sorted_candidates = sorted(
            candidate_scores.keys(),
            key=lambda c: candidate_scores[c],
            reverse=True
        )
        return sorted_candidates[:max_candidates]
