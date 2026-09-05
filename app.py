"""Streamlit UI for the NovaCell RAG chatbot."""
import uuid

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage

import refund_data
from chain import answer_stream
from config import GROQ_API_KEY, HISTORY_TURNS
from intent import classify_intent
from logger import log_answer, log_feedback
from refund_agent import continue_refund_flow, start_refund_flow

SAMPLE_QUESTIONS = [
    "Why is my mobile internet so slow?",
    "I see a charge on my bill I don't recognize, what is it?",
    "How do I activate roaming before I travel abroad?",
    "My SIM card isn't recognized, what do I do?",
    "How do I check my current data balance?",
    "I hear an echo during phone calls, how do I fix it?",
    "What's the difference between the Unlimited and Unlimited Plus plans?",
    "I want a refund of ₹499.",
]

st.set_page_config(page_title="NovaCell Support Assistant", page_icon="📶")


def init_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "pending_question" not in st.session_state:
        st.session_state.pending_question = None
    if "pending_refund" not in st.session_state:
        st.session_state.pending_refund = None


def build_history() -> list:
    """Last HISTORY_TURNS exchanges from *prior* turns, as LangChain messages.
    Must be called before the current turn is appended to session state."""
    recent = st.session_state.messages[-(HISTORY_TURNS * 2):]
    history = []
    for msg in recent:
        if msg["role"] == "user":
            history.append(HumanMessage(content=msg["content"]))
        else:
            history.append(AIMessage(content=msg["content"]))
    return history


def render_sources(sources: list[dict]):
    if not sources:
        return
    with st.expander("Sources"):
        for s in sources:
            st.markdown(f"**[{s['source']}] {s['id']}**")
            st.caption(s["content"])


def render_feedback(message_id: str):
    col1, col2, _ = st.columns([1, 1, 10])
    up_key = f"up_{message_id}"
    down_key = f"down_{message_id}"
    feedback_key = f"feedback_state_{message_id}"

    if feedback_key not in st.session_state:
        st.session_state[feedback_key] = None

    with col1:
        if st.button("👍", key=up_key):
            st.session_state[feedback_key] = "up"
            log_feedback(message_id, "up")
    with col2:
        if st.button("👎", key=down_key):
            st.session_state[feedback_key] = "down"
            log_feedback(message_id, "down")

    if st.session_state[feedback_key]:
        st.caption(f"Feedback recorded: {st.session_state[feedback_key]}")


def render_history():
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                render_sources(msg.get("sources", []))
                render_feedback(msg["id"])


def handle_question(question: str):
    history = build_history()
    st.session_state.messages.append({"role": "user", "content": question, "id": str(uuid.uuid4())})

    with st.chat_message("user"):
        st.markdown(question)

    message_id = str(uuid.uuid4())
    with st.chat_message("assistant"):
        if st.session_state.pending_refund is not None:
            with st.spinner("Working on your refund request..."):
                try:
                    answer, new_pending = continue_refund_flow(question, history, st.session_state.pending_refund)
                except Exception:
                    answer = "Sorry, something went wrong handling your refund request. Please try again."
                    new_pending = None
            st.session_state.pending_refund = new_pending
            st.markdown(answer)
            sources = []
            render_feedback(message_id)
        elif classify_intent(question, history) == "refund_request":
            with st.spinner("Working on your refund request..."):
                try:
                    answer, new_pending = start_refund_flow(question, history)
                except Exception:
                    answer = "Sorry, something went wrong handling your refund request. Please try again."
                    new_pending = None
            st.session_state.pending_refund = new_pending
            st.markdown(answer)
            sources = []
            render_feedback(message_id)
        else:
            token_stream, sources = answer_stream(question, history=history)
            answer = st.write_stream(token_stream)
            render_sources(sources)
            render_feedback(message_id)

    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "sources": sources, "id": message_id}
    )
    log_answer(message_id, question, answer, sources)


def main():
    init_state()

    st.title("📶 NovaCell Support Assistant")
    st.caption("Answers are grounded in NovaCell's FAQ, resolved tickets, and guides only.")

    with st.sidebar:
        st.subheader("Sample questions")
        for q in SAMPLE_QUESTIONS:
            if st.button(q, key=f"sample_{q}", use_container_width=True):
                st.session_state.pending_question = q

        st.divider()
        if st.button("🗑️ Clear conversation", use_container_width=True):
            st.session_state.messages = []
            st.session_state.pending_question = None
            st.session_state.pending_refund = None
            refund_data.reset_store()
            st.rerun()

    if not GROQ_API_KEY:
        st.error("GROQ_API_KEY is not set. Copy .env.example to .env and add your key.")
        return

    render_history()

    typed_question = st.chat_input("Ask a question about your mobile service...")

    question = None
    if st.session_state.pending_question:
        question = st.session_state.pending_question
        st.session_state.pending_question = None
    elif typed_question:
        question = typed_question

    if question:
        handle_question(question)


if __name__ == "__main__":
    main()
