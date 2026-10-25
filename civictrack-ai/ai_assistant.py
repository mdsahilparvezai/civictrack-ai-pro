"""CivicTrack AI Assistant - answers questions using local Ollama.

This module pairs the keyword-based complaint retriever in ``ai_retrieval``
with a local Ollama chat model (qwen3.5:4b). It retrieves the most relevant
complaints for a user's question, sends only those records as evidence to the
model, and returns both the model's answer and the source records.

Design notes:
- Ollama must be running locally (``ollama serve``) with the
  ``qwen3.5:4b`` model pulled (``ollama pull qwen3.5:4b``).
- The model is instructed to answer strictly from the supplied evidence and
  to cite issue IDs, so it cannot invent complaint details.
- All failures (blank input, no matches, connection/HTTP errors, timeouts)
  are caught and converted into friendly messages instead of raw tracebacks.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

import requests

from ai_retrieval import retrieve_complaints

# Local Ollama chat endpoint. Ollama listens on 11434 by default.
OLLAMA_URL = "http://localhost:11434/api/chat"
# Model to use. Must be pulled locally first (e.g. `ollama pull qwen3.5:4b`).
OLLAMA_MODEL = "qwen3.5:4b"
# Seconds to wait for the Ollama server to respond. Raised from 120 to 300
# because qwen3.5:4b can take a while to generate even short answers.
REQUEST_TIMEOUT_SECONDS = 300
# Maximum number of complaint records sent to the model as evidence.
EVIDENCE_LIMIT = 5
# Maximum tokens the model may generate. Keeps answers short and predictable.
NUM_PREDICT = 180
# How long Ollama keeps the model loaded in memory after a request, so the
# next question does not pay the model-load cost again.
KEEP_ALIVE = "10m"
# Whether to send `think: false` to disable chain-of-thought reasoning.
# Some models/API versions reject this option, so it is sent first without it
# and retried with it if the server asks for it.
THINK_OFF = False


def _json_safe(value: Any) -> Any:
    """Convert a value into something ``json.dumps`` can serialize.

    Complaint records come from a pandas DataFrame, so they may contain
    numpy scalars, ``datetime.date`` objects, or ``NaN`` values. This helper
    turns them into plain JSON-safe types (str, int, float, None, list, dict)
    before we send them to Ollama.
    """
    # pandas/numpy NaN -> None
    try:
        if value is None:
            return None
        if isinstance(value, float) and value != value:
            return None
    except Exception:
        pass

    if isinstance(value, (str, int, float, bool)) or value is None:
        return value

    # datetime.date / datetime.datetime -> ISO string
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            return str(value)

    # numpy scalar types -> native Python scalars
    if hasattr(value, "item"):
        try:
            return _json_safe(value.item())
        except Exception:
            pass

    # Lists and dicts: recurse so every nested value is JSON-safe.
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_safe(val) for key, val in value.items()}

    return str(value)


def _build_system_prompt() -> str:
    """Build the system instructions that constrain the model's behaviour."""
    return (
        "You are CivicTrack AI, a careful civic-data assistant. "
        "You will be given a user question and a list of complaint records as "
        "evidence. Answer the question using ONLY the supplied evidence. "
        "Cite the relevant issue IDs (e.g. CT-1001) when you reference a "
        "complaint. If the evidence does not contain enough information to "
        "answer, say so clearly and do NOT invent details, numbers, or "
        "complaints that were not provided. Do not speculate about data outside "
        "the evidence. Keep your answer concise and factual. "
        "Reply in two sentences or fewer."
    )


def _build_user_prompt(question: str, sources: List[Dict[str, Any]]) -> str:
    """Build the user message containing the question and the evidence."""
    safe_sources = _json_safe(sources)
    evidence_json = json.dumps(safe_sources, indent=2)

    return (
        f"User question: {question}\n\n"
        f"Relevant complaint evidence (issue records only):\n"
        f"{evidence_json}\n\n"
        "Answer the user question using only the evidence above."
    )


def ask_civictrack(question: str) -> Dict[str, Any]:
    """Answer a civic question using retrieved complaints and local Ollama.

    Args:
        question: A natural-language question, e.g. "What potholes are open?".

    Returns:
        A dict with two keys:
          - ``answer``: a human-readable string answer.
          - ``sources``: the list of complaint records used as evidence.

        On any failure (blank question, no matches, connection/HTTP error,
        timeout), ``answer`` contains a helpful message and ``sources`` is an
        empty list. Raw exception tracebacks are never exposed to callers.
    """
    # --- 1. Validate the question -------------------------------------------------
    if not question or not str(question).strip():
        return {
            "answer": "Please enter a question about civic complaints "
                      "(for example, 'What open potholes are reported on Main Street?').",
            "sources": [],
        }

    question = str(question).strip()

    # --- 2. Retrieve relevant complaint evidence ----------------------------------
    try:
        sources = retrieve_complaints(question, limit=EVIDENCE_LIMIT)
    except Exception:
        # Retrieval failures are non-fatal: answer without evidence.
        sources = []

    # --- 3. No matching evidence: be honest, do not invent ------------------------
    if not sources:
        return {
            "answer": (
                "No relevant complaint records were found for your question, "
                "so there is no evidence to base an answer on. Please try a "
                "different question or check the Issue Explorer for the "
                "available complaints."
            ),
            "sources": [],
        }

    # --- 4. Build a compact evidence payload --------------------------------------
    # Only the fields the model needs to answer and cite issue IDs are kept,
    # which reduces the request size and speeds up generation.
    compact_sources = [
        {key: record.get(key) for key in ("issue_id", "category", "location",
                                          "priority", "status", "description")}
        for record in sources
    ]

    # --- 5. Call the local Ollama model -------------------------------------------
    # The request is sent twice at most: first WITH `think: false` to disable
    # chain-of-thought reasoning (qwen3.5 supports it), and once WITHOUT it if
    # the server rejects the option. This keeps thinking off when supported
    # without breaking on models or API versions that do not support it.
    base_payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": _build_system_prompt()},
            {"role": "user", "content": _build_user_prompt(question, compact_sources)},
        ],
        "stream": False,
        # Limit answer length so responses are short and predictable.
        "num_predict": NUM_PREDICT,
        # Keep the model loaded in memory to avoid reload cost on the next call.
        "keep_alive": KEEP_ALIVE,
    }

    response = None
    think_attempts = (True, False)  # try with think:false, then without
    for use_think in think_attempts:
        payload = dict(base_payload)
        if use_think:
            payload["think"] = False
        try:
            response = requests.post(
                OLLAMA_URL,
                json=payload,
                timeout=REQUEST_TIMEOUT_SECONDS,
                headers={"Content-Type": "application/json"},
            )
        except requests.exceptions.Timeout:
            return {
                "answer": (
                    "The local Ollama service did not respond within "
                    f"{REQUEST_TIMEOUT_SECONDS} seconds. The model "
                    f"{OLLAMA_MODEL} may be slow on this machine; try a shorter "
                    "question or restart `ollama serve`."
                ),
                "sources": sources,
            }
        except requests.exceptions.ConnectionError:
            return {
                "answer": (
                    "Could not connect to the local Ollama service at "
                    f"{OLLAMA_URL}. Please start it with `ollama serve` and ensure "
                    f"the model {OLLAMA_MODEL} is pulled "
                    "(`ollama pull qwen3.5:4b`)."
                ),
                "sources": sources,
            }
        except Exception:  # noqa: BLE001 - surface a generic message
            return {
                "answer": (
                    "Something went wrong while contacting the AI service. "
                    "Please try again."
                ),
                "sources": sources,
            }

        # If the server rejected the `think` option specifically, retry without
        # it before treating the request as a real failure.
        if response.status_code == 400 and use_think:
            body_text = ""
            try:
                body_text = response.text or ""
            except Exception:
                body_text = ""
            lowered = body_text.lower()
            if "think" in lowered or "unknown" in lowered or "unsupported" in lowered:
                continue  # retry the next iteration without `think`
        break

    # --- 6. Handle unsuccessful HTTP responses ------------------------------------
    if response.status_code != 200:
        return {
            "answer": (
                f"The AI service returned an error (status {response.status_code}). "
                "Please check the Ollama server logs and try again."
            ),
            "sources": sources,
        }

    # --- 7. Parse the Ollama response ---------------------------------------------
    try:
        data = response.json()
    except Exception:
        return {
            "answer": (
                "The AI service returned an unreadable (non-JSON) response. "
                "Please try again."
            ),
            "sources": sources,
        }

    # Ollama's /api/chat returns {"message": {"content": "..."}, ...}
    message = data.get("message") if isinstance(data, dict) else None
    content = message.get("content") if isinstance(message, dict) else None

    if not content:
        return {
            "answer": (
                "The AI service returned an empty response. This can happen if "
                "the model was unloaded; please try again."
            ),
            "sources": sources,
        }

    return {
        "answer": str(content).strip(),
        "sources": sources,
    }