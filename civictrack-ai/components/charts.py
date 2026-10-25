"""Interactive chart components for CivicTrack AI Pro."""

from __future__ import annotations

import plotly.express as px
import streamlit as st


def render_category_chart(complaints) -> None:
    """Render a bar chart of complaints by category."""
    if complaints is None or complaints.empty or "category" not in complaints.columns:
        st.info("No complaint data available to display the category chart.")
        return

    counts = complaints["category"].value_counts().sort_values(ascending=False)
    chart_data = counts.reset_index()
    chart_data.columns = ["category", "count"]

    fig = px.bar(
        chart_data,
        x="category",
        y="count",
        title="Complaints by Category",
        color_discrete_sequence=["#1e3a8a"],
        labels={"category": "Category", "count": "Number of Complaints"},
    )
    fig.update_layout(
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, sans-serif", size=12, color="#334155"),
        title_font=dict(size=16, color="#0f172a"),
        margin=dict(t=60, b=40, l=40, r=20),
        xaxis_title=None,
        yaxis_title="Complaints",
    )
    fig.update_traces(marker_line_color="rgba(0,0,0,0)", marker_line_width=0)
    st.plotly_chart(fig, use_container_width=True)


def render_status_chart(complaints) -> None:
    """Render a donut chart of complaints by status."""
    if complaints is None or complaints.empty or "status" not in complaints.columns:
        st.info("No complaint data available to display the status chart.")
        return

    counts = complaints["status"].value_counts()
    chart_data = counts.reset_index()
    chart_data.columns = ["status", "count"]

    color_map = {
        "Open": "#ef4444",
        "In Progress": "#f59e0b",
        "Resolved": "#22c55e",
        "Closed": "#64748b",
    }
    colors = [color_map.get(s, "#94a3b8") for s in chart_data["status"]]

    fig = px.pie(
        chart_data,
        names="status",
        values="count",
        title="Complaints by Status",
        color_discrete_sequence=colors,
        hole=0.45,
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, sans-serif", size=12, color="#334155"),
        title_font=dict(size=16, color="#0f172a"),
        margin=dict(t=60, b=20, l=20, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    st.plotly_chart(fig, use_container_width=True)
