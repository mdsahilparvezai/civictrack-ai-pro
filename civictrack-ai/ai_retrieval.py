"""Simple keyword-based complaint retrieval for the AI Assistant.

This module answers natural-language questions by searching the combined
sample-plus-user complaint dataset. For this first version it uses simple
case-insensitive keyword matching and ranks the most relevant complaints
first. It is intentionally dependency-free (standard library + pandas only),
so no external packages or model downloads are required.

The functions here are pure data helpers: they read the shared complaint
DataFrame through ``data.complaint_storage.get_combined_complaints()`` and
return plain Python dictionaries, which is what the AI Assistant page needs
to feed context into a local Ollama model.
"""

from __future__ import annotations

from typing import Dict, List

import pandas as pd

from data.complaint_storage import get_combined_complaints

# Fields searched when matching a user question against complaint records.
# These mirror the columns produced by data.sample_data.load_complaints().
_SEARCHABLE_FIELDS = (
    "issue_id",
    "category",
    "location",
    "priority",
    "status",
    "description",
)

# Common question words that should NOT influence matching scores.
_STOP_WORDS = frozenset(
    {
        "a",
        "an",
        "are",
        "as",
        "at",
        "be",
        "by",
        "complaint",
        "complaints",
        "for",
        "from",
        "have",
        "i",
        "in",
        "is",
        "it",
        "me",
        "my",
        "of",
        "on",
        "or",
        "reported",
        "s",
        "the",
        "to",
        "was",
        "what",
        "which",
        "who",
        "will",
        "with",
        "you",
        "your",
    }
)

# Status intent keywords mapped to canonical status values.
_STATUS_MAP = {
    "open": "Open",
    "opens": "Open",
    "resolve": "Resolved",
    "resolved": "Resolved",
    "resolve": "Resolved",
    "closes": "Closed",
    "closed": "Closed",
}

# Category intent keywords mapped to canonical category values.
# Synonyms cover how residents typically describe issues.
_CATEGORY_MAP = {
    "pothole": "Pothole",
    "potholes": "Pothole",
    "streetlight": "Street Light",
    "street light": "Street Light",
    "streetlight": "Street Light",
    "light": "Street Light",
    "lights": "Street Light",
    "garbage": "Trash Collection",
    "trash": "Trash Collection",
    "trash collection": "Trash Collection",
    "rubbish": "Trash Collection",
    "litter": "Trash Collection",
    "road": "Pothole",
    "roads": "Pothole",
    "street": "Pothole",
    "drainage": "Water Main",
    "drain": "Water Main",
    "water": "Water Main",
    "leak": "Water Main",
    "park": "Park Maintenance",
    "park maintenance": "Park Maintenance",
    "bench": "Park Maintenance",
    "traffic": "Traffic Signal",
    "signal": "Traffic Signal",
    "sidewalk": "Sidewalk",
    "sidewalks": "Sidewalk",
    "graffiti": "Graffiti",
}


def _tokenize(text: str) -> List[str]:
    """Split ``text`` into lowercase word tokens, dropping common question words.

    Empty or whitespace-only input returns an empty list so callers can
    short-circuit before doing any work.
    """
    if not text or not text.strip():
        return []
    # Keep only word characters and simple apostrophes; everything else
    # (punctuation, newlines) becomes a separator.
    cleaned = "".join(ch if ch.isalnum() or ch == "'" else " " for ch in text.lower())
    return [token for token in cleaned.split() if token and token not in _STOP_WORDS]


def _detect_status(text: str) -> str | None:
    """Return the canonical status mentioned in ``text`` (e.g. ``Open``).

    Returns ``None`` when no status keyword is present.
    """
    lowered = text.lower()
    for keyword, status in _STATUS_MAP.items():
        if keyword in lowered:
            return status
    return None


def _detect_category(text: str) -> str | None:
    """Return the canonical category mentioned in ``text`` (e.g. ``Pothole``).

    Returns ``None`` when no category keyword is present.
    """
    lowered = text.lower()
    # Multi-word keys first so ``trash collection`` beats ``trash``.
    for keyword in sorted(_CATEGORY_MAP, key=len, reverse=True):
        if keyword in lowered:
            return _CATEGORY_MAP[keyword]
    return None


def _score_row(row: pd.Series, question: str) -> int:
    """Score a complaint row against a question.

    Scoring rewards strong, explicit matches and penalizes weak keyword-only
    matches so that a question like ``open pothole`` returns open potholes
    rather than resolved potholes or unrelated records.

    Weights:
        status match      : 5 points
        category match    : 4 points
        location match    : 3 points
        description match : 2 points
        issue_id match    : 1 point

    Returns ``0`` when the row does not meaningfully match the question.
    """
    lowered = question.lower()
    status = str(row.get("status", "")).lower()
    category = str(row.get("category", "")).lower()
    location = str(row.get("location", "")).lower()
    description = str(row.get("description", "")).lower()
    issue_id = str(row.get("issue_id", "")).lower()

    score = 0

    # Strong matches first.
    if status and status in lowered:
        score += 5
    if category and category in lowered:
        score += 4
    if location and location in lowered:
        score += 3
    if description and description in lowered:
        score += 2
    if issue_id and issue_id in lowered:
        score += 1

    # Location partial-word match: abbreviations (St vs Street) can break
    # exact substring matching, so check if any significant question word
    # appears in the location string.
    if score == 0 or location:
        qwords = [w for w in lowered.split() if w and w not in _STOP_WORDS]
        location_words = location.split()
        if any(qw in location_words for qw in qwords):
            score = max(score, 3)

    # Weak keyword match on description only (not status/category names that
    # would otherwise bleed across intents).
    if score == 0:
        description_words = [w for w in description.split() if w not in _STOP_WORDS]
        for keyword in question.split():
            kw = keyword.lower()
            if kw and kw not in _STOP_WORDS and kw in description_words:
                score += 1

    return score


def retrieve_complaints(question: str, limit: int = 5) -> List[Dict]:
    """Search complaints by keyword and return the most relevant first.

    Args:
        question: A natural-language question, e.g. "potholes on Main Street".
        limit: Maximum number of complaint records to return.

    Returns:
        A list of complaint records as dictionaries. Each record keeps its
        original fields (issue_id, category, location, priority, status,
        date_reported, description, ...) plus an internal ``_match_score``
        key used for ranking. The score is included so callers can see how
        strongly each record matched the question.

        Returns an empty list when there is nothing to search or no matches.
    """
    if not question or not question.strip():
        return []

    # Load the shared dataset (sample + persisted user complaints).
    try:
        complaints = get_combined_complaints()
    except Exception:
        return []

    # Guard against an empty or None DataFrame.
    if complaints is None or complaints.empty:
        return []

    # Detect explicit intents from the question so we do not surface
    # records that contradict them (e.g. resolved potholes when asked for
    # open potholes).
    wanted_status = _detect_status(question)
    wanted_category = _detect_category(question)

    # Score every row.
    scored = []
    for _, row in complaints.iterrows():
        score = _score_row(row, question)
        if score <= 0:
            continue

        # Hard-filter: if the question asks for a specific status, exclude
        # records with a different status. This keeps resolved complaints out
        # of ``open ...`` results unless the question asks for comparison.
        if wanted_status is not None:
            row_status = str(row.get("status", "")).strip()
            if row_status != wanted_status:
                continue

        # Hard-filter: if the question asks for a specific category, exclude
        # records with a different category.
        if wanted_category is not None:
            row_category = str(row.get("category", "")).strip()
            if row_category != wanted_category:
                continue

        scored.append((score, row))

    if not scored:
        return []

    # Rank highest score first. For ties, preserve original row order.
    scored.sort(key=lambda pair: pair[0], reverse=True)

    # Convert the top matches into plain dictionaries with ``_match_score``.
    results: List[Dict] = []
    for score, row in scored[:limit]:
        record = {col: _to_native(row[col]) for col in complaints.columns}
        record["_match_score"] = score
        results.append(record)

    return results


def _to_native(value):
    """Convert pandas/numpy scalar values into native Python types.

    This makes the returned dictionaries safe to serialize (e.g. to JSON) and
    easy to read. NaN values become None.
    """
    try:
        # pandas NA / numpy NaN -> None
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        # pd.isna can raise on array-like inputs; fall through to identity.
        pass

    # numpy scalar types (int64, float64, etc.) -> python int/float/str
    if hasattr(value, "item") and not isinstance(value, (str, bytes, dict, list)):
        try:
            return value.item()
        except (AttributeError, ValueError):
            pass
    return value