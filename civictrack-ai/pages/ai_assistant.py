
"""Chat interface for the CivicTrack AI assistant."""

from __future__ import annotations

import streamlit as st

from ai_assistant import ask_civictrack


def render_ai_assistant_page(complaints, projects) -> None:
    """Render the CivicTrack AI chat page."""
    del complaints, projects

    st.title("CivicTrack AI Assistant")
    st.caption("Ask questions about civic complaints using local AI.")

    if "civictrack_chat_history" not in st.session_state:
        st.session_state["civictrack_chat_history"] = []

    if st.button("Clear chat", key="clear_civictrack_chat"):
        st.session_state["civictrack_chat_history"] = []
        st.rerun()

    for message in st.session_state["civictrack_chat_history"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            if message.get("sources"):
                with st.expander("Complaint sources"):
                    for source in message["sources"]:
                        st.write(
                            f"- {source.get('issue_id', 'Unknown ID')} | "
                            f"{source.get('category', 'Unknown category')} | "
                            f"{source.get('status', 'Unknown status')}"
                        )

    question = st.chat_input(
        "Ask about open potholes, complaint status, or locations..."
    )

    if question:
        st.session_state["civictrack_chat_history"].append(
            {"role": "user", "content": question}
        )

        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Searching complaints and contacting local AI..."):
                try:
                    result = ask_civictrack(question)
                    answer = result.get(
                        "answer", "I couldn't generate an answer. Please try again."
                    )
                    sources = result.get("sources", [])
                except Exception as exc:
                    st.error(f"Assistant error: {exc}")
                    answer = (
                        "I couldn't complete the request. Check that Ollama "
                        "is running, then try again."
                    )
                    sources = []

            st.markdown(answer)

            if sources:
                with st.expander("Complaint sources"):
                    for source in sources:
                        st.write(
                            f"- {source.get('issue_id', 'Unknown ID')} | "
                            f"{source.get('category', 'Unknown category')} | "
                            f"{source.get('status', 'Unknown status')}"
                        )

        st.session_state["civictrack_chat_history"].append(
            {
                "role": "assistant",
                "content": answer,
                "sources": sources,
            }
        )
