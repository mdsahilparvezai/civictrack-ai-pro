"""Budget & Projects page: budget summary and project progress."""

from __future__ import annotations

import streamlit as st

from components.budget_projects import render_budget_projects


def render_budget_projects_page(complaints, projects) -> None:
    """Render the budget and projects page."""
    del complaints  # unused on this page

    st.title("Budget & Projects")
    st.caption("Track civic project budgets and delivery progress.")

    render_budget_projects(projects)
