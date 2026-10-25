"""Budget and project progress section."""

from __future__ import annotations

import pandas as pd
import streamlit as st


def render_budget_projects(projects) -> None:
    """Render a budget summary and project progress table."""
    if projects is None or projects.empty:
        st.info("No project data available.")
        return

    required = {"project_id", "name", "budget", "spent", "progress", "status", "location"}
    missing = required - set(projects.columns)
    if missing:
        st.error(f"Project data is missing required columns: {', '.join(sorted(missing))}")
        return

    df = projects.copy()

    total_budget = float(df["budget"].sum())
    total_spent = float(df["spent"].sum())
    active_count = int((df["status"] == "Active").sum())

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Budget (sample)", f"${total_budget:,.0f}")
    col2.metric("Total Spent (sample)", f"${total_spent:,.0f}")
    col3.metric("Active Projects", active_count)

    remaining = total_budget - total_spent
    st.markdown(f"**Remaining budget (sample): ${remaining:,.0f}**")
    st.progress(min(total_spent / total_budget, 1.0) if total_budget else 0.0)

    st.divider()
    st.subheader("Project Progress")

    for _, row in df.iterrows():
        progress = float(row["progress"])
        with st.container():
            st.markdown(
                f"""
                <div class="project-row">
                    <div class="project-info">
                        <div class="project-name"><strong>{row['project_id']}</strong> — {row['name']}</div>
                        <div class="project-meta">{row['category']} &bull; {row['location']}</div>
                    </div>
                    <div class="project-status">{row['status']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.progress(progress / 100.0, text=f"{progress:.0f}% complete &bull; "
                         f"${row['spent']:,.0f} spent of ${row['budget']:,.0f}")
