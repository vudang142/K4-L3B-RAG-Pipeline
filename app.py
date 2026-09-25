"""
RAG Chatbot - Du lịch Ẩm thực Hà Nội
"""

import streamlit as st
from dotenv import load_dotenv

from src.task10_generation import generate_with_citation

load_dotenv()

st.set_page_config(
    page_title="RAG Chatbot - Du lịch Ẩm thực Hà Nội",
    page_icon="🍜",
    layout="wide",
)

if "messages" not in st.session_state:
    st.session_state.messages = []

if "retrieval_info" not in st.session_state:
    st.session_state.retrieval_info = {}


def format_sources(sources: list[dict]) -> str:
    """Format sources để hiển thị."""
    if not sources:
        return "Không có nguồn"

    lines = []
    for i, src in enumerate(sources, 1):
        metadata = src.get("metadata", {})
        title = metadata.get("title", "N/A")
        source = metadata.get("source", "N/A")
        score = src.get("score", 0)
        method = src.get("retrieval_method", "unknown")
        content_preview = src.get("content", "")[:100] + "..."
        lines.append(f"**{i}. {title}** ({source})\n   - Score: {score:.3f} | Method: {method}\n   - {content_preview}")

    return "\n\n".join(lines)


with st.sidebar:
    st.title("🍜 RAG Chatbot")
    st.caption("Hỏi đáp về Du lịch & Ẩm thực Hà Nội")
    top_k = st.slider("Số chunks", 3, 10, 5)
    st.divider()
    st.markdown("**Hướng dẫn:**")
    st.markdown("- Nhập câu hỏi về du lịch, ẩm thực Hà Nội")
    st.markdown("- Bot sẽ trả lời kèm nguồn trích dẫn")
    st.markdown("- Dùng **bold** để highlight claims")

st.title("🍜 RAG Chatbot - Du lịch & Ẩm thực Hà Nội")
st.caption("Hệ thống hỏi đáp thông minh với trích dẫn nguồn")

# Display chat history
for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        # Show sources for assistant messages
        if message["role"] == "assistant" and idx in st.session_state.retrieval_info:
            info = st.session_state.retrieval_info[idx]
            with st.expander("📚 Nguồn tham khảo", expanded=False):
                st.markdown(f"**Phương pháp retrieval:** {info.get('method', 'N/A')}")
                st.markdown(f"**Số nguồn:** {len(info.get('sources', []))}")
                st.markdown("---")
                st.markdown(format_sources(info.get('sources', [])))

# Chat input
query = st.chat_input("Nhập câu hỏi của bạn...")

if query:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": query})

    with st.chat_message("user"):
        st.markdown(query)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Đang tìm kiếm và tạo câu trả lời..."):
            try:
                result = generate_with_citation(query, top_k=top_k)

                # Display answer
                st.markdown(result["answer"])

                # Store retrieval info
                msg_idx = len(st.session_state.messages) - 1
                st.session_state.retrieval_info[msg_idx] = {
                    "sources": result.get("sources", []),
                    "method": result.get("retrieval_source", "unknown"),
                }

                # Show sources in expander
                with st.expander("📚 Nguồn tham khảo", expanded=False):
                    st.markdown(f"**Phương pháp retrieval:** {result.get('retrieval_source', 'N/A')}")
                    st.markdown(f"**Số nguồn:** {len(result.get('sources', []))}")
                    st.markdown("---")
                    st.markdown(format_sources(result.get('sources', [])))

                # Add to history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result["answer"]
                })

            except Exception as e:
                error_msg = f"Xin lỗi, đã xảy ra lỗi: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })

# Clear chat button
if st.button("🗑️ Xóa cuộc trò chuyện"):
    st.session_state.messages = []
    st.session_state.retrieval_info = {}
    st.rerun()
