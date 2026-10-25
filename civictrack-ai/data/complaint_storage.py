"""Persistent JSON storage for user-submitted complaints.

This module provides safe JSON load/save functions for complaints submitted
through the Report an Issue page. Storage is a single local JSON file and is
intended for local development only. It is NOT reliable permanent cloud storage
and will not survive a redeploy on Streamlit Community Cloud.

The storage path is resolved relative to this module's location so the file is
found regardless of the current working directory. It can be overridden at
runtime (for example in tests) by assigning to ``complaint_storage.STORAGE_PATH``.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from data.sample_data import load_complaints

# Path to the JSON file that stores user-submitted complaints.
# Resolve relative to this module so it works from any working directory.
STORAGE_PATH: Path = Path(__file__).resolve().parent / "user_complaints.json"

# Expected keys for a stored complaint record. Extra keys are allowed but the
# core fields must be present and of the correct type.
_REQUIRED_KEYS = ("issue_id", "category", "location", "priority", "status")
_OPTIONAL_KEYS = ("date_reported", "description")


def _validate_records(records: Any) -> List[Dict[str, Any]]:
    """Validate that ``records`` is a list of complaint dicts.

    Raises:
        TypeError: if ``records`` is not a list.
        ValueError: if any record is not a dict or is missing required keys.
    """
    if not isinstance(records, list):
        raise TypeError(
            f"Complaint storage must contain a JSON list, got {type(records).__name__}."
        )

    validated: List[Dict[str, Any]] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(
                f"Complaint record at index {index} is not a JSON object "
                f"(got {type(record).__name__})."
            )
        missing = [key for key in _REQUIRED_KEYS if key not in record]
        if missing:
            raise ValueError(
                f"Complaint record at index {index} is missing required key(s): "
                f"{', '.join(missing)}."
            )
        issue_id = record.get("issue_id")
        if not isinstance(issue_id, str) or not issue_id.strip():
            raise ValueError(
                f"Complaint record at index {index} has an invalid 'issue_id': "
                f"{issue_id!r}."
            )
        validated.append(record)
    return validated


def load_user_complaints() -> List[Dict[str, Any]]:
    """Load user-submitted complaints from the JSON storage file.

    Returns:
        An empty list if the file does not exist.

    Raises:
        OSError: if the file cannot be read.
        ValueError/TypeError: if the JSON is malformed or the structure is invalid.
    """
    path = STORAGE_PATH
    if not path.exists():
        return []

    try:
        with open(path, "r", encoding="utf-8") as handle:
            raw = json.load(handle)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Complaint storage file {path} contains malformed JSON: {exc.msg} "
            f"at line {exc.lineno}, column {exc.colno}."
        ) from exc
    except OSError as exc:
        raise OSError(
            f"Failed to read complaint storage file {path}: {exc.strerror or exc}."
        ) from exc

    return _validate_records(raw)


def save_user_complaints(records: List[Dict[str, Any]]) -> None:
    """Atomically save user-submitted complaints to the JSON storage file.

    The write is atomic: data is first written to a temporary file in the same
    directory and then renamed into place with ``os.replace``. This prevents
    partial or corrupted writes if the process is interrupted.

    Raises:
        ValueError/TypeError: if ``records`` is not a valid list of complaint dicts.
        OSError: if the file cannot be written.
    """
    validated = _validate_records(records)
    path = STORAGE_PATH
    directory = path.parent

    # Ensure the parent directory exists (it normally does, but be safe).
    directory.mkdir(parents=True, exist_ok=True)

    # Write to a temp file in the same directory, then atomically replace.
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=str(directory),
            prefix=".tmp_complaints_",
            suffix=".json",
            delete=False,
        ) as handle:
            json.dump(validated, handle, indent=2, ensure_ascii=False)
            handle.flush()
            os.fsync(handle.fileno())
            temp_path = handle.name

        os.replace(temp_path, path)
    except OSError:
        # Clean up the temp file if something went wrong before the replace.
        try:
            if "temp_path" in locals() and Path(temp_path).exists():
                Path(temp_path).unlink()
        except OSError:
            pass
        raise


def append_complaint(record: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Append a single complaint record to persistent storage.

    Duplicate records (same ``issue_id``) are ignored to prevent duplicate
    entries when Streamlit reruns the form on submit.

    Args:
        record: A complaint dict containing at least the required keys.

    Returns:
        The full list of stored complaints after the append.

    Raises:
        ValueError: if ``record`` is not a dict or is missing required keys.
        OSError: if the storage file cannot be read or written.
    """
    if not isinstance(record, dict):
        raise ValueError(
            f"Complaint record must be a dict, got {type(record).__name__}."
        )
    missing = [key for key in _REQUIRED_KEYS if key not in record]
    if missing:
        raise ValueError(
            f"Complaint record is missing required key(s): {', '.join(missing)}."
        )

    issue_id = record.get("issue_id")
    if not isinstance(issue_id, str) or not issue_id.strip():
        raise ValueError("Complaint record has an invalid 'issue_id'.")

    existing = load_user_complaints()

    # Prevent duplicate issue_id records.
    for existing_record in existing:
        if existing_record.get("issue_id") == issue_id:
            return existing

    existing.append(record)
    save_user_complaints(existing)
    return existing


def get_combined_complaints() -> pd.DataFrame:
    """Return the combined sample-plus-submitted complaints as a DataFrame.

    Loads the existing sample complaints through
    ``data.sample_data.load_complaints()``, merges them with user-submitted
    complaints, and preserves the existing columns and sample data. Sample
    complaint IDs are never overwritten by user submissions.

    Returns:
        A pandas DataFrame containing sample complaints followed by
        user-submitted complaints.
    """
    sample_df = load_complaints()
    user_records = load_user_complaints()

    if not user_records:
        return sample_df

    user_df = pd.DataFrame(user_records)

    # Align columns: ensure every sample column exists in the user frame and
    # every user column exists in the sample frame, filling missing values.
    for column in sample_df.columns:
        if column not in user_df.columns:
            user_df[column] = None
    for column in user_df.columns:
        if column not in sample_df.columns:
            sample_df[column] = None

    combined = pd.concat(
        [sample_df, user_df[sample_df.columns]],
        ignore_index=True,
    )
    return combined