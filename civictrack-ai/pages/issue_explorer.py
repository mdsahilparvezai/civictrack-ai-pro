"""Issue Explorer page: searchable and filterable complaints table."""

from __future__ import annotations

import streamlit as st

from components.complaints_table import render_complaints_table


def render_issue_explorer_page(complaints, projects) -> None:
    """Render the issue explorer page."""
    del projects  # unused on this page

    st.title("Issue Explorer")
    st.caption("Browse, search, and filter civic complaints.")

    # The complaints DataFrame is supplied by app.py and already contains
    # sample complaints plus persisted user-submitted complaints, so no
    # session-state merging is needed here.
    render_complaints_table(complaints, limit=50, key_prefix="explorer")
