"""Issue Explorer page: searchable and filterable complaints table."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.complaints_table import render_complaints_table


def render_issue_explorer_page(complaints, projects) -> None:
    """Render the issue explorer page."""
    del projects  # unused on this page

    st.title("Issue Explorer")
    st.caption("Browse, search, and filter civic complaints.")

    # Merge session-submitted issues if not already merged
    try:
        reported = st.session_state.get("reported_issues", [])
        if reported:
            reported_df = pd.DataFrame(reported)
            for col in ["issue_id", "category", "location", "priority", "status", "date_reported", "description"]:
                if col not in reported_df.columns:
                    reported_df[col] = None
            if complaints is None or (hasattr(complaints, "empty") and complaints.empty):
                merged = reported_df
            else:
                # Ensure all columns present
                for col in complaints.columns:
                    if col not in reported_df.columns:
                        reported_df[col] = None
                for col in reported_df.columns:
                    if col not in complaints.columns:
                        complaints[col] = None
                merged = pd.concat([complaints, reported_df[complaints.columns]], ignore_index=True)
            complaints = merged
    except Exception:
        pass

    render_complaints_table(complaints, limit=50, key_prefix="explorer")
