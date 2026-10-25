"""KPI card component for the dashboard."""

from __future__ import annotations

import streamlit as st


def render_kpi_cards(metrics: dict) -> None:
    """Render four KPI cards: complaints, pending, resolved, active projects."""
    cards = [
        ("Total Complaints", metrics.get("total_complaints", 0), "📋"),
        ("Pending Issues", metrics.get("pending_issues", 0), "⏳"),
        ("Resolved Issues", metrics.get("resolved_issues", 0), "✅"),
        ("Active Projects", metrics.get("active_projects", 0), "🏗️"),
    ]

    cols = st.columns(len(cards))
    for col, (label, value, icon) in zip(cols, cards):
        with col:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-icon">{icon}</div>
                    <div class="kpi-value">{value:,}</div>
                    <div class="kpi-label">{label}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
