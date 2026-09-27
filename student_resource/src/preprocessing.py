"""
Data Preprocessing and Text Normalization Module.

Handles:
- Unicode normalization (diacritics, accents like French é, è, etc.)
- Website domain stripping (e.g., georgesaul.com -> georgesaul)
- Legal entity suffix normalization (e.g., Pvt Ltd, LLC, Inc, Corp)
- Address term standardization (e.g., St -> street, Rd -> road)
- Number token extraction
"""

import re
import unicodedata
from typing import List, Set, Tuple

# Domain extension pattern
DOMAIN_PATTERN = re.compile(
    r'\b(?:https?://)?(?:www\.)?([a-z0-9\-]+)\.(?:com|org|net|in|co\.in|co|io|fr|gov|edu)\b',
    re.IGNORECASE
)

# Common legal suffixes to normalize or strip
LEGAL_SUFFIXES = [
    (r'\b(private\s+limited|pvt\.?\s*ltd\.?|pvt\s+ltd)\b', ' pvt ltd '),
    (r'\b(limited|ltd\.?)\b', ' ltd '),
    (r'\b(incorporated|inc\.?)\b', ' inc '),
    (r'\b(corporation|corp\.?)\b', ' corp '),
    (r'\b(limited\s+liability\s+company|llc\.?|l\.l\.c\.?)\b', ' llc '),
    (r'\b(limited\s+liability\s+partnership|llp\.?|l\.l\.p\.?)\b', ' llp '),
    (r'\b(company|co\.?)\b', ' co '),
]

# Address abbreviation mappings
ADDRESS_ABBREVIATIONS = [
    (r'\b(st\.?|str\.?)\b', ' street '),
    (r'\b(rd\.?)\b', ' road '),
    (r'\b(ave\.?|av\.?)\b', ' avenue '),
    (r'\b(blvd\.?)\b', ' boulevard '),
    (r'\b(dr\.?)\b', ' drive '),
    (r'\b(ln\.?)\b', ' lane '),
    (r'\b(ct\.?)\b', ' court '),
    (r'\b(pl\.?)\b', ' place '),
    (r'\b(pkwy\.?)\b', ' parkway '),
    (r'\b(apt\.?|apartment)\b', ' apt '),
    (r'\b(ste\.?|suite)\b', ' suite '),
    (r'\b(flr\.?|floor)\b', ' floor '),
    (r'\b(p\.?\s*o\.?\s*box)\b', ' pobox '),
]


def strip_accents(text: str) -> str:
    """Normalize unicode characters, stripping accents (e.g. é -> e)."""
    if not text:
        return ""
    nfkd = unicodedata.normalize('NFKD', text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def clean_text(text: str) -> str:
    """Basic text sanitization: strip accents, lowercase, remove special characters."""
    if not text or not isinstance(text, str):
        return ""
    text = strip_accents(text).lower()
    # Replace common separators with spaces
    text = re.sub(r'[\/\\,\.\-_:;\(\)\[\]\{\}<>\'\"`\?!@#\$%\^&\*\+=~]', ' ', text)
    # Collapse multiple whitespaces
    return " ".join(text.split())


def normalize_business_name(name: str) -> str:
    """
    Standardize a business name.
    1. Removes domain artifacts (e.g., website.com -> website)
    2. Strips accents and lowercases
    3. Normalizes legal suffixes
    4. Cleans stray symbols
    """
    if not name:
        return ""
    # Strip domain extensions if the name looks like a domain
    name = DOMAIN_PATTERN.sub(r'\1', name)
    cleaned = clean_text(name)

    for pattern, replacement in LEGAL_SUFFIXES:
        cleaned = re.sub(pattern, replacement, cleaned)

    return " ".join(cleaned.split())


def normalize_address(address: str) -> str:
    """
    Standardize an address.
    1. Expands common abbreviations (st -> street, rd -> road)
    2. Normalizes leading zeros in numbers (e.g. 0301 -> 301)
    3. Collapses whitespace
    """
    if not address:
        return ""
    cleaned = clean_text(address)

    for pattern, replacement in ADDRESS_ABBREVIATIONS:
        cleaned = re.sub(pattern, replacement, cleaned)

    # Normalize leading zeros in numeric tokens (e.g., 0301 -> 301)
    tokens = [tok.lstrip('0') if tok.isdigit() and tok != '0' else tok for tok in cleaned.split()]
    return " ".join(tokens)


def extract_numbers(text: str) -> Set[str]:
    """Extract all standalone numeric tokens (house numbers, postal codes)."""
    if not text:
        return set()
    nums = re.findall(r'\b\d+\b', text)
    return {n.lstrip('0') or '0' for n in nums}


def extract_name_tokens(name: str, min_len: int = 2) -> List[str]:
    """Extract meaningful name tokens excluding generic legal terms."""
    normalized = normalize_business_name(name)
    stopwords = {'pvt', 'ltd', 'inc', 'corp', 'llc', 'llp', 'co', 'and', 'the', 'of', 'in'}
    return [tok for tok in normalized.split() if len(tok) >= min_len and tok not in stopwords]
