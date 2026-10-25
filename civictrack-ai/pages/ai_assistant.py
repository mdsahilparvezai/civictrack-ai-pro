"""AI Assistant page (coming soon)."""

from __future__ import annotations

import streamlit as st


def render_ai_assistant_page(complaints, projects) -> None:
    """Render the AI Assistant placeholder page."""
    del complaints, projects  # unused until AI features are implemented

    st.title("AI Assistant")
    st.caption("Coming soon.")

    st.info(
        "The AI Assistant is not yet implemented. This section is reserved "
        "for future AI-powered features such as issue summarization, "
        "anomaly detection, and natural-language queries over civic data. "
        "No AI functionality is present in this release."
    )

    st.divider()
    st.subheader("Planned capabilities")
    st.markdown(
        "- Summarize recent complaints by category\n"
        "- Flag unusual spikes in reported issues\n"
        "- Answer natural-language questions about project budgets\n"
        "- Draft responses to residents reporting issues"
    )
    st.caption(
        "These are planned features only. None are implemented or backed by "
        "real AI models in this release."
    )
