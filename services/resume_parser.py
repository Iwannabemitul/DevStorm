"""
Resume text extraction and deterministic skill mapping.

This module is intentionally free of any LLM calls -- extracting *candidate*
skill phrases from free-form resume text still goes through
`analysis_service.extract_skills_via_llm`, which calls `LLMEngine`. What
lives here is the deterministic part: getting raw text out of a .pdf/.txt
upload, and mapping a list of extracted tokens onto the curated
`ALL_TECH_SKILLS` catalog case-insensitively, with de-duplication.
"""
from __future__ import annotations

import io
from typing import Iterable, List, Tuple

import PyPDF2


def extract_text_from_upload(filename: str, file_bytes: bytes) -> str:
    """Extract raw text from an uploaded .pdf or .txt file's bytes."""
    if filename.lower().endswith(".pdf"):
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return file_bytes.decode("utf-8", errors="ignore")


def dedupe_tokens(tokens: Iterable[str]) -> List[str]:
    """Trim, drop blanks, and de-duplicate while preserving first-seen order."""
    seen = set()
    deduped = []
    for raw in tokens:
        token = raw.strip()
        if not token:
            continue
        key = token.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(token)
    return deduped


def map_tokens_to_skill_catalog(
    tokens: Iterable[str], catalog: Iterable[str]
) -> Tuple[List[str], List[str]]:
    """Map extracted tokens onto the curated skill catalog, case-insensitively.

    Returns (known_matches, custom_tokens):
      - known_matches: tokens that matched a catalog entry, normalized to the
        catalog's canonical casing/spelling, de-duplicated, order-preserved.
      - custom_tokens: de-duplicated tokens with no catalog match, so the UI
        can still offer them as free-text additions.
    """
    lookup = {skill.lower(): skill for skill in catalog}

    known_matches: List[str] = []
    custom_tokens: List[str] = []

    for token in dedupe_tokens(tokens):
        canonical = lookup.get(token.lower())
        if canonical:
            if canonical not in known_matches:
                known_matches.append(canonical)
        elif token not in custom_tokens:
            custom_tokens.append(token)

    return known_matches, custom_tokens


def split_comma_list(raw_text: str) -> List[str]:
    """Split a comma-separated string (e.g. LLM skill extraction output, or a
    manual 'Add custom skills' text field) into clean tokens."""
    if not raw_text:
        return []
    return dedupe_tokens(raw_text.split(","))
