"""Report an Issue page: submit a new civic issue.

Submitted issues are persisted to a local JSON file through
``data.complaint_storage`` so they survive Streamlit reruns and local app
restarts. This local JSON storage is for local development only and is NOT
reliable permanent cloud storage on Streamlit Community Cloud.
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from data.complaint_storage import append_complaint, load_user_complaints


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

    with st.form("report_issue_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            category = st.selectbox(
                "Category",
                [
                    "Pothole",
                    "Street Light",
                    "Graffiti",
                    "Trash Collection",
                    "Water Main",
                    "Park Maintenance",
                    "Traffic Signal",
                    "Sidewalk",
                ],
            )
            location = st.text_input("Location", placeholder="e.g. Main St & 5th Ave")
        with col2:
            priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"])
            date_reported = st.date_input("Date Reported", value=date.today())

        description = st.text_area(
            "Description",
            placeholder="Describe the issue in detail...",
        )
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