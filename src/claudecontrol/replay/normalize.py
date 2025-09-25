"""
Normalization utilities for matching and comparison
Handles ANSI codes, whitespace, timestamps, and other volatile data
"""

import re
from typing import List, Tuple, Optional


# ANSI escape sequence pattern
ANSI_RE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

# Common volatile patterns to scrub
VOLATILE_PATTERNS: List[Tuple[re.Pattern, str]] = [
    # ISO timestamps
    (re.compile(r'\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?\b'), '<TIMESTAMP>'),
    # Unix timestamps (10-13 digits)
    (re.compile(r'\b1[0-9]{9,12}\b'), '<UNIX_TIME>'),
    # Hex IDs (7-40 chars, like git commits)
    (re.compile(r'\b[0-9a-f]{7,40}\b'), '<HEX_ID>'),
    # UUIDs
    (re.compile(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', re.I), '<UUID>'),
    # Memory addresses
    (re.compile(r'\b0x[0-9a-fA-F]+\b'), '<ADDR>'),
    # PIDs (3-7 digit numbers in isolation)
    (re.compile(r'\bpid[:\s]*(\d{3,7})\b', re.I), 'pid:<PID>'),
    # Temporary file paths
    (re.compile(r'/tmp/[^\s]+'), '<TMPFILE>'),
    # Random temp names
    (re.compile(r'\b(tmp|temp)[_-]?[a-zA-Z0-9]{6,}\b', re.I), '<TEMPNAME>'),
]

# Patterns for paths that should be normalized
PATH_PATTERNS = [
    (re.compile(r'/home/[^/]+'), '/home/<USER>'),
    (re.compile(r'/Users/[^/]+'), '/Users/<USER>'),
    (re.compile(r'C:\\Users\\[^\\]+'), 'C:\\Users\\<USER>'),
]


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from text"""
    return ANSI_RE.sub('', text)


def collapse_whitespace(text: str) -> str:
    """Collapse multiple whitespace characters to single space"""
    # Replace tabs with spaces
    text = text.replace('\t', ' ')
    # Collapse multiple spaces
    text = re.sub(r' +', ' ', text)
    # Remove trailing whitespace from lines
    lines = text.splitlines()
    lines = [line.rstrip() for line in lines]
    return '\n'.join(lines)


def scrub_volatile(text: str, patterns: Optional[List[Tuple[re.Pattern, str]]] = None) -> str:
    """Replace volatile patterns with placeholders"""
    if patterns is None:
        patterns = VOLATILE_PATTERNS

    for pattern, replacement in patterns:
        text = pattern.sub(replacement, text)

    return text


def normalize_paths(text: str) -> str:
    """Normalize user-specific paths"""
    for pattern, replacement in PATH_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def normalize_line_endings(text: str) -> str:
    """Normalize line endings to \n"""
    text = text.replace('\r\n', '\n')
    text = text.replace('\r', '\n')
    return text


def full_normalize(text: str,
                   strip_ansi_codes: bool = True,
                   collapse_ws: bool = True,
                   scrub_volatiles: bool = True,
                   normalize_path: bool = True) -> str:
    """Apply all normalizations"""
    if strip_ansi_codes:
        text = strip_ansi(text)
    if collapse_ws:
        text = collapse_whitespace(text)
    if scrub_volatiles:
        text = scrub_volatile(text)
    if normalize_path:
        text = normalize_paths(text)

    text = normalize_line_endings(text)
    return text


def normalize_for_matching(text: str) -> str:
    """Standard normalization for matching operations"""
    return full_normalize(text)


def normalize_for_display(text: str) -> str:
    """Light normalization for display (preserve formatting)"""
    return normalize_line_endings(text)


class Normalizer:
    """Configurable normalizer for matching contexts"""

    def __init__(self,
                 strip_ansi: bool = True,
                 collapse_ws: bool = False,
                 scrub_volatile: bool = True,
                 normalize_paths: bool = True,
                 custom_patterns: Optional[List[Tuple[re.Pattern, str]]] = None):
        self.strip_ansi = strip_ansi
        self.collapse_ws = collapse_ws
        self.scrub_volatile = scrub_volatile
        self.normalize_paths = normalize_paths
        self.custom_patterns = custom_patterns or []

    def normalize(self, text: str) -> str:
        """Apply configured normalizations"""
        if self.strip_ansi:
            text = strip_ansi(text)
        if self.collapse_ws:
            text = collapse_whitespace(text)
        if self.scrub_volatile:
            patterns = VOLATILE_PATTERNS + self.custom_patterns
            text = scrub_volatile(text, patterns)
        if self.normalize_paths:
            text = normalize_paths(text)

        return normalize_line_endings(text)

    def build_key(self, *parts: str) -> str:
        """Build a normalized key from multiple parts"""
        normalized_parts = [self.normalize(str(p)) for p in parts if p]
        return "|".join(normalized_parts)