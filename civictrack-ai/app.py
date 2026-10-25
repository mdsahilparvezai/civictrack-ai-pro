"""CivicTrack AI Pro - main Streamlit application.

Civic infrastructure monitoring and public spending transparency dashboard.

Entry point: streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

from components.budget_projects import render_budget_projects
from components.charts import render_category_chart, render_status_chart
from components.complaints_table import render_complaints_table
from components.kpi_cards import render_kpi_cards
from components.sidebar import render_sidebar
from data.sample_data import compute_kpi_metrics, load_complaints, load_projects

from pages.ai_assistant import render_ai_assistant_page
from pages.budget_projects import render_budget_projects_page
from pages.dashboard import render_dashboard_page
from pages.issue_explorer import render_issue_explorer_page
from pages.report_issue import render_report_issue_page

PAGE_ROUTES = {
    "Dashboard": render_dashboard_page,
    "Report an Issue": render_report_issue_page,
    "Issue Explorer": render_issue_explorer_page,
    "Budget & Projects": render_budget_projects_page,
    "AI Assistant": render_ai_assistant_page,
}


def main() -> None:
    st.set_page_config(
        page_title="CivicTrack AI Pro",
        page_icon="\U0001F3E6",  # classical building
        layout="wide",
        initial_sidebar_state="expanded",
    )

    _inject_css()

    # Load datasets (labeled as sample/synthetic inside data module).
    try:
        complaints = load_complaints()
        projects = load_projects()
    except Exception as exc:  # noqa: BLE001 - surface data load errors to user
        st.error(f"Failed to load dataset: {exc}")
        st.stop()

    # Merge session-submitted issues so all pages see them
    try:
        reported = st.session_state.get("reported_issues", [])
        if reported:
            import pandas as _pd

            reported_df = _pd.DataFrame(reported)
            # Ensure expected columns exist
            for col in ["issue_id", "category", "location", "priority", "status", "date_reported", "description"]:
                if col not in reported_df.columns:
                    reported_df[col] = None
            # Align column order/types loosely
            complaints = _pd.concat([complaints, reported_df[complaints.columns.intersection(reported_df.columns)]], ignore_index=True)
            # If reported has extra columns not in complaints, try to append with NaN for missing
            missing_cols = [c for c in complaints.columns if c not in reported_df.columns]
            if missing_cols and not reported_df.empty:
                for c in missing_cols:
                    reported_df[c] = None
                complaints = _pd.concat([complaints, reported_df[complaints.columns]], ignore_index=True)
    except Exception:
        pass

    selection = render_sidebar()

    page_fn = PAGE_ROUTES.get(selection)
    if page_fn is None:
        st.error("Page not found.")
        return

    try:
        page_fn(complaints=complaints, projects=projects)
    except Exception as exc:  # noqa: BLE001 - surface render errors to user
        st.error(f"An error occurred while rendering '{selection}': {exc}")


def _inject_css() -> None:
    """Apply a clean, professional civic-tech visual design."""
    st.markdown(
        """
        <style>
        :root {
            --ink: #0f172a;
            --muted: #64748b;
            --line: #e2e8f0;
            --primary: #1e3a8a;
            --primary-soft: #eff6ff;
            --radius: 12px;
        }

        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            max-width: 1300px;
        }

        h1, h2, h3 {
            font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
            color: var(--ink);
            letter-spacing: -0.01em;
        }

        h1 {
            font-size: 1.75rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
        }

        h2 {
            font-size: 1.25rem;
            font-weight: 600;
            margin-top: 1.5rem;
            margin-bottom: 0.75rem;
        }

        .sidebar-brand {
            font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--ink);
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .sidebar-note {
            font-size: 0.75rem;
            color: var(--muted);
            line-height: 1.4;
            padding-top: 0.5rem;
        }

        .kpi-card {
            background: #ffffff;
            border: 1px solid var(--line);
            border-radius: var(--radius);
            padding: 16px 14px;
            display: flex;
            align-items: center;
            gap: 12px;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
        }

        .kpi-icon {
            font-size: 1.75rem;
            line-height: 1;
        }

        .kpi-value {
            font-size: 1.75rem;
            font-weight: 700;
            color: var(--ink);
            line-height: 1.1;
        }

        .kpi-label {
            font-size: 0.75rem;
            color: var(--muted);
            text-transform: uppercase;
            letter-spacing: 0.06em;
            font-weight: 600;
        }

        .stDataFrame, .stTable {
            border: 1px solid var(--line);
            border-radius: var(--radius);
        }

        .complaint-row {
            display: flex;
            align-items: center;
            gap: 16px;
            padding: 10px 12px;
            border: 1px solid var(--line);
            border-radius: var(--radius);
            margin-bottom: 8px;
            background: #ffffff;
        }

        .issue-id {
            font-weight: 700;
            color: var(--ink);
            width: 120px;
            font-size: 0.85rem;
        }

        .issue-category {
            color: var(--muted);
            width: 150px;
            font-size: 0.85rem;
        }

        .issue-location {
            color: var(--ink);
            flex: 1;
            font-size: 0.85rem;
        }

        .issue-priority,
        .issue-status {
            width: 110px;
            font-size: 0.8rem;
        }

        .status-badge,
        .priority-badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 999px;
            font-size: 0.7rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            white-space: nowrap;
        }

        .project-row {
            display: flex;
            align-items: center;
            gap: 16px;
            padding: 10px 12px;
            border: 1px solid var(--line);
            border-radius: var(--radius);
            margin-bottom: 8px;
            background: #ffffff;
        }

        .project-info {
            flex: 1;
        }

        .project-name {
            font-weight: 600;
            color: var(--ink);
            font-size: 0.9rem;
        }

        .project-meta {
            color: var(--muted);
            font-size: 0.78rem;
        }

        .project-status {
            width: 120px;
            font-size: 0.8rem;
            font-weight: 600;
            color: var(--muted);
            text-align: right;
        }

        .stMetric {
            background: #ffffff;
            border: 1px solid var(--line);
            border-radius: var(--radius);
            padding: 12px 14px;
        }

        .stProgress > div > div {
            background-color: var(--primary);
        }

        a {
            color: var(--primary);
        }

        [data-testid="stSidebarNav"] { display: none; }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
