"""Report an Issue page: submit a new civic issue.

Submitted issues are persisted to a local JSON file through
``data.complaint_storage`` so they survive Streamlit reruns and local app
restarts. This local JSON storage is for local development only and is NOT
reliable permanent cloud storage on Streamlit Community Cloud.
"""

from __future__ import annotations

from datetime import date

import base64
import io
import json
import os
import pandas as pd
import requests
import streamlit as st
from PIL import Image

from data.complaint_storage import append_complaint, load_user_complaints


# --- Automatic Priority Engine ---

_PRIORITY_LEVELS = ("Low", "Medium", "High", "Critical")

# Base priority assigned by category (before description keywords are considered).
_CATEGORY_BASE_PRIORITY = {
    "Pothole": "Medium",
    "Street Light": "Medium",
    "Graffiti": "Low",
    "Trash Collection": "Low",
    "Water Main": "High",
    "Park Maintenance": "Low",
    "Traffic Signal": "High",
    "Sidewalk": "Medium",
}

# Keywords that always elevate to Critical (safety hazards).
_CRITICAL_KEYWORDS = (
    "exposed wire", "live wire", "downed power line", "electrical hazard",
    "gas leak", "smell gas", "gas odor",
    "flooding", "flood", "water main break", "burst pipe",
    "dangerous intersection", "traffic signal not working", "signal out",
    "traffic light out", "traffic lights out",
    "structural collapse", "building collapse", "bridge collapse",
    "fire", "burning", "smoke", "explosion",
    "injury", "injured", "hurt", "accident", "emergency",
    "life-threatening", "life threatening",
)

# Keywords that elevate to High (when base is Low or Medium).
_HIGH_KEYWORDS = (
    "pothole", "sinkhole", "large pothole", "deep pothole",
    "broken water main", "no water", "water pressure low",
    "street light out", "lights out", "multiple lights out",
    "dark area", "pitch dark",
    "trip hazard", "cracked sidewalk", "broken sidewalk",
    "broken equipment", "unsafe playground", "dangerous tree",
    "urgent", "immediate", "asap", "serious",
    "hate speech", "offensive graffiti", "profanity",
)

# Keywords that elevate to Medium (when base is Low).
_MEDIUM_KEYWORDS = (
    "street light", "single light out", "light outage",
    "missed pickup", "trash not collected", "garbage not collected",
    "overflowing trash", "overflowing garbage",
    "overgrown", "weeds", "litter",
    "broken bench", "damaged bench", "graffiti",
)

# Keywords that reduce to Low (minor issues).
_LOW_KEYWORDS = (
    "minor graffiti", "tagging", "spray paint", "small graffiti",
    "minor crack", "small crack", "slight crack",
    "minor", "small", "slight", "minimal",
)


def _determine_priority(category: str, description: str) -> tuple[str, str]:
    """Determine complaint priority from category and description.

    Uses transparent rule-based logic: category sets a base priority, and
    description keywords can elevate or reduce it. Critical keywords always
    override to Critical.

    Args:
        category: The complaint category.
        description: The complaint description.

    Returns:
        A tuple of (priority, reason) where priority is one of
        Low/Medium/High/Critical and reason explains the decision.
    """
    desc_lower = (description or "").lower().strip()

    # Base priority from category
    base_priority = _CATEGORY_BASE_PRIORITY.get(category, "Medium")
    priority = base_priority
    reasons = [f"Category '{category}' base priority: {base_priority}."]

    # Critical keywords override everything
    for keyword in _CRITICAL_KEYWORDS:
        if keyword in desc_lower:
            return "Critical", (
                f"{reasons[0]} Description mentions '{keyword}' — "
                f"elevated to Critical due to potential safety hazard."
            )

    # Check description for elevation/reduction keywords
    high_found = [kw for kw in _HIGH_KEYWORDS if kw in desc_lower]
    medium_found = [kw for kw in _MEDIUM_KEYWORDS if kw in desc_lower]
    low_found = [kw for kw in _LOW_KEYWORDS if kw in desc_lower]

    # Elevate priority based on description
    if high_found and priority in ("Low", "Medium"):
        priority = "High"
        reasons.append(
            f"Description mentions '{high_found[0]}' — elevated to High."
        )
    elif medium_found and priority == "Low":
        priority = "Medium"
        reasons.append(
            f"Description mentions '{medium_found[0]}' — elevated to Medium."
        )

    # Reduce priority based on description (only if not already elevated by high keywords)
    if low_found and priority in ("Medium", "High") and not high_found:
        priority = "Low"
        reasons.append(
            f"Description mentions '{low_found[0]}' — reduced to Low (minor issue)."
        )

    if not desc_lower:
        reasons.append("No description provided; using category-based priority.")

    reason = " ".join(reasons)
    return priority, reason


# --- AI Photo-Based Issue Reporting ---

# Vision model for photo analysis. Configurable via the VISION_MODEL
# environment variable. qwen3.5:4b has vision capability in this environment
# but has NOT been end-to-end tested with a real image. If unavailable, set
# VISION_MODEL to an alternative (e.g. qwen2.5-vl:7b).
VISION_MODEL = os.environ.get("VISION_MODEL", "qwen3.5:4b")
VISION_TIMEOUT_SECONDS = 120

# Ollama endpoint. Configurable via the OLLAMA_URL environment variable.
# Defaults to localhost for local development. On Streamlit Community Cloud,
# localhost will NOT reach a user's personal Ollama instance; set OLLAMA_URL
# to a reachable backend or leave unset to disable photo analysis gracefully.
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/chat")

_VALID_IMAGE_TYPES = ("jpg", "jpeg", "png")

_COMPLAINT_CATEGORIES = (
    "Pothole",
    "Street Light",
    "Graffiti",
    "Trash Collection",
    "Water Main",
    "Park Maintenance",
    "Traffic Signal",
    "Sidewalk",
)


def _image_to_base64(uploaded_file) -> str:
    """Convert an uploaded file to a base64-encoded string."""
    uploaded_file.seek(0)
    return base64.b64encode(uploaded_file.read()).decode("utf-8")


def _validate_image_file(uploaded_file) -> tuple[bool, str | None]:
    """Validate that the uploaded file is a readable image.

    Returns (is_valid, error_message).
    """
    if uploaded_file is None:
        return False, "No file uploaded."

    ext = uploaded_file.name.lower().rsplit(".", 1)[-1] if "." in uploaded_file.name else ""
    if ext not in _VALID_IMAGE_TYPES:
        return False, (
            f"Unsupported file type '{ext}'. Please upload JPG, JPEG, or PNG."
        )

    try:
        img = Image.open(uploaded_file)
        img.verify()
        uploaded_file.seek(0)
        return True, None
    except Exception as exc:
        return False, f"Could not read image file: {exc}"


def _analyze_image_with_vision(image_bytes: bytes, filename: str) -> dict:
    """Send an image to Ollama's vision model for civic issue analysis.

    Returns a dict with keys: category, description, priority, reason, or
    an "error" key if analysis fails.
    """
    b64 = base64.b64encode(image_bytes).decode("utf-8")

    prompt = (
        "Analyze this civic infrastructure issue image. Respond with ONLY a "
        "JSON object containing: "
        '"category": one of "Pothole", "Street Light", "Graffiti", '
        '"Trash Collection", "Water Main", "Park Maintenance", '
        '"Traffic Signal", "Sidewalk"; '
        '"description": a concise, factual description based on visible '
        'evidence; "priority": "Low", "Medium", "High", or "Critical"; '
        '"reason": a short explanation for the priority. '
        "If you cannot identify the issue from the image, respond with "
        '{"error": "unclear"}.'
    )

    payload = {
        "model": VISION_MODEL,
        "messages": [
            {"role": "user", "content": prompt, "images": [b64]}
        ],
        "stream": False,
    }

    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=VISION_TIMEOUT_SECONDS,
            headers={"Content-Type": "application/json"},
        )
    except requests.exceptions.Timeout:
        return {"error": "timeout"}
    except requests.exceptions.ConnectionError:
        return {"error": "connection"}
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}

    if response.status_code != 200:
        # Surface Ollama's own error text (e.g. "model '...' not found")
        # instead of a bare http_<status> code, so failures are actionable.
        detail = None
        try:
            body = response.json()
        except Exception:  # noqa: BLE001 - response may be plain text
            body = None
        if isinstance(body, dict):
            for key in ("error", "message", "detail"):
                value = body.get(key)
                if value:
                    detail = str(value).strip()
                    break
        elif isinstance(body, str) and body.strip():
            detail = body.strip()
        if detail:
            # Keep the message short and single-line.
            detail = " ".join(detail.split())[:200]
            return {"error": detail}
        return {"error": f"http_{response.status_code}"}
    try:
        data = response.json()
    except Exception:
        return {"error": "invalid_response"}

    message = data.get("message") if isinstance(data, dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    if not content:
        return {"error": "empty_response"}

    # Extract JSON from the model response (may be wrapped in markdown)
    content = content.strip()
    if content.startswith("```json"):
        content = content[7:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()

    try:
        result = json.loads(content)
    except Exception:
        return {"error": "invalid_json", "raw": content[:200]}

    # If the model signals it cannot identify the issue, surface that directly.
    if isinstance(result, dict) and result.get("error") == "unclear":
        return result

    # Validate required fields
    required = ("category", "description", "priority", "reason")
    if not all(k in result for k in required):
        return {"error": "missing_fields", "raw": content[:200]}

    if result.get("category") not in _COMPLAINT_CATEGORIES:
        return {"error": "invalid_category", "raw": content[:200]}

    if result.get("priority") not in ("Low", "Medium", "High", "Critical"):
        return {"error": "invalid_priority", "raw": content[:200]}

    return result


def render_report_issue_page(complaints, projects) -> None:
    """Render the issue reporting form."""
    del projects  # unused on this page

    st.title("Report an Issue")
    st.caption("Submit a new civic infrastructure issue.")

    st.info(
        "This is a demonstration form. Submitted issues are saved to a local "
        "JSON file on this machine for the duration of local development. "
        "This is NOT reliable permanent cloud storage and will not survive a "
        "redeploy on Streamlit Community Cloud."
    )

    # --- Session state for AI-populated fields ---
    if "report_category" not in st.session_state:
        st.session_state["report_category"] = _COMPLAINT_CATEGORIES[0]
    if "report_description" not in st.session_state:
        st.session_state["report_description"] = ""

    # --- Photo upload ---
    st.subheader("Attach a Photo (optional)")
    uploaded_file = st.file_uploader(
        "Upload a photo of the issue",
        type=["jpg", "jpeg", "png"],
        help="JPG, JPEG, or PNG. A vision-capable Ollama model "
        f"({VISION_MODEL}) must be running for AI analysis.",
    )

    ai_analysis = None
    if uploaded_file is not None:
        is_valid, error_msg = _validate_image_file(uploaded_file)
        if not is_valid:
            st.error(error_msg)
        else:
            # Display preview
            st.image(uploaded_file, caption="Uploaded image", use_container_width=True)

            # Analyze with vision model
            uploaded_file.seek(0)
            image_bytes = uploaded_file.read()
            with st.spinner("Analyzing image with AI..."):
                ai_analysis = _analyze_image_with_vision(image_bytes, uploaded_file.name)

            if ai_analysis and "error" not in ai_analysis:
                st.success("Image analyzed successfully.")
                # Populate session state so widgets reflect AI suggestions
                st.session_state["report_category"] = ai_analysis["category"]
                st.session_state["report_description"] = ai_analysis["description"]
                # Also set priority so the priority display reflects it
                st.session_state["ai_suggested_priority"] = ai_analysis["priority"]
                st.session_state["ai_suggested_reason"] = ai_analysis["reason"]
            elif ai_analysis and ai_analysis.get("error") == "unclear":
                st.warning(
                    "The AI could not identify the issue from this image. "
                    "Please enter the details manually below."
                )
            else:
                err = ai_analysis.get("error", "unknown") if ai_analysis else "unknown"
                st.warning(
                    f"AI image analysis unavailable ({err}). "
                    "Ollama may not be running or may not be reachable from "
                    "this deployment. You can still enter the details "
                    "manually below."
                )
                if err == "connection":
                    st.info(
                        "To enable photo analysis, run Ollama locally and set "
                        "the `OLLAMA_URL` environment variable to your Ollama "
                        f"endpoint (default: `http://localhost:11434/api/chat`), "
                        f"and ensure a vision-capable model is pulled "
                        f"(e.g. `{VISION_MODEL}`). On Streamlit Community "
                        "Cloud, `localhost` will not reach a personal "
                        "computer's Ollama instance."
                    )
                else:
                    st.info(
                        f"To enable photo analysis, pull and run a vision "
                        f"model: `ollama pull {VISION_MODEL}` and "
                        "`ollama serve`. You can still enter the details "
                        "manually below."
                    )

    # --- Live inputs for category and description ---
    col1, col2 = st.columns(2)
    with col1:
        category_index = (
            _COMPLAINT_CATEGORIES.index(st.session_state["report_category"])
            if st.session_state["report_category"] in _COMPLAINT_CATEGORIES
            else 0
        )
        category = st.selectbox(
            "Category",
            _COMPLAINT_CATEGORIES,
            index=category_index,
        )
        # Reset AI-suggested priority when user manually changes category
        previous_category = st.session_state.get("report_category", category)
        if category != previous_category:
            st.session_state.pop("ai_suggested_priority", None)
            st.session_state.pop("ai_suggested_reason", None)
        st.session_state["report_category"] = category

        description = st.text_area(
            "Description",
            key="report_description",
            placeholder="Describe the issue in detail...",
        )
        # No manual sync needed: st.text_area(key=...) automatically reads from
        # and writes to st.session_state["report_description"]. Modifying that
        # key after the widget is instantiated raises a Streamlit error.
    with col2:
        date_reported = st.date_input("Date Reported", value=date.today())

    # Determine priority: use AI suggestion if available, otherwise compute
    ai_priority = st.session_state.get("ai_suggested_priority")
    ai_reason = st.session_state.get("ai_suggested_reason")
    if ai_priority and ai_reason:
        priority = ai_priority
        priority_reason = ai_reason
    else:
        priority, priority_reason = _determine_priority(category, description)

    st.info(
        f"**Suggested Priority:** {priority}\n\n{priority_reason}"
    )

    # --- Submission form ---
    with st.form("report_issue_form", clear_on_submit=True):
        location = st.text_input("Location", placeholder="e.g. Main St & 5th Ave")
        submitted = st.form_submit_button("Submit Issue", type="primary")

    if submitted:
        if not location or not description:
            st.error("Please provide both a location and a description.")
            return

        # Sequence the new ID against the persisted store so IDs stay unique
        # across Streamlit reruns and app restarts.
        existing_count = len(load_user_complaints())
        new_id = f"CT-{int(date.today().strftime('%y%m%d'))}-{existing_count + 1:03d}"
        # The JSON storage module uses the standard-library json encoder, which
        # cannot serialize datetime.date objects, so store the date as an
        # ISO-8601 string. The field key is preserved.
        new_issue = {
            "issue_id": new_id,
            "category": category,
            "location": location,
            "priority": priority,
            "status": "Open",
            "date_reported": date_reported.isoformat(),
            "description": description,
        }

        try:
            append_complaint(new_issue)
        except Exception as exc:  # noqa: BLE001 - surface storage errors to user
            st.error(f"Could not save the reported issue: {exc}")
            return

        st.success(f"Issue {new_id} reported successfully.")
        st.balloons()

    # Show persisted user-submitted issues (survives reruns and restarts).
    saved_issues = load_user_complaints()
    if saved_issues:
        st.divider()
        st.subheader("Persistently Saved Issues")
        session_df = pd.DataFrame(saved_issues)
        st.dataframe(
            session_df[["issue_id", "category", "location", "priority", "status"]],
            use_container_width=True,
            hide_index=True,
        )