"""Report an Issue page: submit a new civic issue (sample data only)."""

from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st


def render_report_issue_page(complaints, projects) -> None:
    """Render the issue reporting form."""
    del projects  # unused on this page

    st.title("Report an Issue")
    st.caption("Submit a new civic infrastructure issue. Sample data only.")

    st.info(
        "This is a demonstration form. Submitted issues are stored in the "
        "current session only and are part of the sample/synthetic dataset."
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

        new_id = f"CT-{int(date.today().strftime('%y%m%d'))}-{len(st.session_state.get('reported_issues', [])) + 1:03d}"
        new_issue = {
            "issue_id": new_id,
            "category": category,
            "location": location,
            "priority": priority,
            "status": "Open",
            "date_reported": date_reported,
            "description": description,
        }

        # Persist within this session only
        if "reported_issues" not in st.session_state:
            st.session_state["reported_issues"] = []
        st.session_state["reported_issues"].append(new_issue)

        st.success(f"Issue {new_id} reported successfully (sample session data).")
        st.balloons()

    # Show session-submitted issues
    if st.session_state.get("reported_issues"):
        st.divider()
        st.subheader("Issues Reported This Session")
        session_df = pd.DataFrame(st.session_state["reported_issues"])
        st.dataframe(
            session_df[["issue_id", "category", "location", "priority", "status"]],
            use_container_width=True,
            hide_index=True,
        )
