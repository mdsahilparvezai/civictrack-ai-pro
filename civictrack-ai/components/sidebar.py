"""Main navigation sidebar for CivicTrack AI Pro."""

from __future__ import annotations

import streamlit as st

PAGES = [
    "Dashboard",
    "Report an Issue",
    "Issue Explorer",
    "Budget & Projects",
    "AI Assistant",
]


def render_sidebar() -> str:
    """Render the sidebar navigation and return the selected page label."""
    with st.sidebar:
        st.markdown(
            '<div class="sidebar-brand">CivicTrack AI Pro</div>',
            unsafe_allow_html=True,
        )
        st.caption("Civic Infrastructure Monitoring")

        selection = st.radio(
            "Navigation",
            PAGES,
            label_visibility="collapsed",
        )

        st.divider()
        st.markdown(
            '<div class="sidebar-note">'
            '<strong>Data notice:</strong> This dashboard uses clearly labeled '
            'sample/synthetic data for demonstration. It is not verified official '
            'government data.'
            "</div>",
            unsafe_allow_html=True,
        )

    return selection
