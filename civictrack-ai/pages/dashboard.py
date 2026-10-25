"""Dashboard page: KPI cards, charts, recent complaints, budget preview."""

from __future__ import annotations

import streamlit as st

from components.budget_projects import render_budget_projects
from components.charts import render_category_chart, render_status_chart
from components.complaints_table import render_complaints_table
from components.kpi_cards import render_kpi_cards
from data.sample_data import compute_kpi_metrics


def render_dashboard_page(complaints, projects) -> None:
    """Render the main dashboard page."""
    st.title("Dashboard")
    st.caption("Overview of civic infrastructure issues and project delivery.")

    metrics = compute_kpi_metrics(complaints, projects)
    render_kpi_cards(metrics)

    st.divider()

    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        render_category_chart(complaints)
    with col_chart2:
        render_status_chart(complaints)

    st.divider()

    st.subheader("Recent Complaints")
    render_complaints_table(complaints, limit=8, key_prefix="dashboard_recent")

    st.divider()

    st.subheader("Budget & Projects Preview")
    render_budget_projects(projects)
