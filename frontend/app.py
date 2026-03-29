"""
Streamlit Frontend for the AI Research Assistant.
Premium dark-themed chat interface with document management.
"""
import streamlit as st
import requests
import time

# ─── CONFIG ──────────────────────────────────────────────────────────────────
API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="AI Research Assistant",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CUSTOM CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Global */
    .stApp {
        font-family: 'Inter', sans-serif;
    }

    /* Main header */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0;
        letter-spacing: -0.5px;
    }

    .sub-header {
        color: #8892b0;
        font-size: 1rem;
        font-weight: 300;
        margin-top: -10px;
        margin-bottom: 24px;
    }

    /* Chat messages */
    .user-msg {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 14px 20px;
        border-radius: 18px 18px 4px 18px;
        margin: 8px 0;
        max-width: 85%;
        margin-left: auto;
        font-size: 0.95rem;
        line-height: 1.6;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }

    .ai-msg {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: #e6e6e6;
        padding: 14px 20px;
        border-radius: 18px 18px 18px 4px;
        margin: 8px 0;
        max-width: 85%;
        font-size: 0.95rem;
        line-height: 1.6;
        backdrop-filter: blur(10px);
    }

    /* Source cards */
    .source-card {
        background: rgba(102, 126, 234, 0.08);
        border: 1px solid rgba(102, 126, 234, 0.2);
        border-radius: 12px;
        padding: 12px 16px;
        margin: 6px 0;
        font-size: 0.85rem;
        transition: all 0.2s ease;
    }

    .source-card:hover {
        border-color: rgba(102, 126, 234, 0.5);
        background: rgba(102, 126, 234, 0.12);
    }

    .source-filename {
        color: #667eea;
        font-weight: 600;
        font-size: 0.9rem;
    }

    .source-meta {
        color: #8892b0;
        font-size: 0.8rem;
        margin-top: 4px;
    }

    .source-preview {
        color: #a8b2d1;
        font-size: 0.82rem;
        margin-top: 6px;
        font-style: italic;
    }

    /* Document list in sidebar */
    .doc-item {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 10px 14px;
        margin: 6px 0;
        transition: all 0.2s ease;
    }

    .doc-item:hover {
        border-color: rgba(102, 126, 234, 0.4);
    }

    .doc-name {
        color: #ccd6f6;
        font-weight: 500;
        font-size: 0.88rem;
    }

    .doc-meta {
        color: #8892b0;
        font-size: 0.75rem;
    }

    /* Stats */
    .stat-box {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.15), rgba(118, 75, 162, 0.15));
        border: 1px solid rgba(102, 126, 234, 0.2);
        border-radius: 14px;
        padding: 20px;
        text-align: center;
    }

    .stat-number {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .stat-label {
        color: #8892b0;
        font-size: 0.85rem;
        margin-top: 4px;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        border-right: 1px solid rgba(255, 255, 255, 0.06);
    }

    /* Upload area */
    [data-testid="stFileUploader"] {
        border-radius: 12px;
    }

    /* Pulse animation for processing */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    .processing {
        animation: pulse 1.5s infinite;
        color: #667eea;
    }
</style>
""", unsafe_allow_html=True)


# ─── HELPERS ─────────────────────────────────────────────────────────────────
def api_get(endpoint):
    try:
        r = requests.get(f"{API_URL}{endpoint}", timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.ConnectionError:
        st.error("⚠️ Backend not running. Start it with: `uvicorn backend.main:app --reload`")
        return None
    except Exception as e:
        st.error(f"API Error: {e}")
        return None


def api_post(endpoint, **kwargs):
    try:
        r = requests.post(f"{API_URL}{endpoint}", timeout=60, **kwargs)
        r.raise_for_status()
        return r.json()
    except requests.ConnectionError:
        st.error("⚠️ Backend not running. Start it with: `uvicorn backend.main:app --reload`")
        return None
    except Exception as e:
        st.error(f"API Error: {e}")
        return None


def api_delete(endpoint):
    try:
        r = requests.delete(f"{API_URL}{endpoint}", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API Error: {e}")
        return None


# ─── SESSION STATE ───────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

if "doc_count" not in st.session_state:
    st.session_state.doc_count = 0


# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📄 Document Manager")
    st.markdown("---")

    # File Upload
    st.markdown("### Upload Documents")
    uploaded_files = st.file_uploader(
        "Drag & drop files here",
        type=["pdf", "txt", "md", "csv"],
        accept_multiple_files=True,
        help="Supported: PDF, TXT, MD, CSV",
    )

    if uploaded_files:
        for uploaded_file in uploaded_files:
            with st.spinner(f"📥 Indexing **{uploaded_file.name}**..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                result = api_post("/upload", files=files)
                if result:
                    st.success(f"✅ **{result['filename']}** — {result['chunks']} chunks indexed")

    st.markdown("---")

    # Document List
    st.markdown("### 📚 Your Documents")
    docs = api_get("/documents")

    if docs is not None:
        st.session_state.doc_count = len(docs)
        if len(docs) == 0:
            st.info("No documents uploaded yet.")
        for doc in docs:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"""
                <div class="doc-item">
                    <div class="doc-name">📄 {doc['filename']}</div>
                    <div class="doc-meta">{doc['chunk_count']} chunks · ID: {doc['doc_id'][:8]}...</div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                if st.button("🗑️", key=f"del_{doc['doc_id']}", help=f"Delete {doc['filename']}"):
                    result = api_delete(f"/documents/{doc['doc_id']}")
                    if result:
                        st.toast(f"Deleted {doc['filename']}", icon="🗑️")
                        st.rerun()
    else:
        st.info("Connect to backend to see documents.")

    st.markdown("---")

    # Stats
    stats = api_get("/stats")
    if stats:
        st.markdown("### 📊 Stats")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""
            <div class="stat-box">
                <div class="stat-number">{stats['total_documents']}</div>
                <div class="stat-label">Documents</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="stat-box">
                <div class="stat-number">{stats['total_chunks']}</div>
                <div class="stat-label">Chunks</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")
    st.markdown("### 🎯 Chat Context")
    doc_options = {"All Documents": None}
    if docs is not None:
        for d in docs:
            doc_options[d['filename']] = d['doc_id']
    
    selected_doc_name = st.selectbox(
        "Ask about specific document:",
        options=list(doc_options.keys()),
        index=0,
        help="Select a document to narrow down the AI's search context."
    )
    st.session_state.selected_doc_id = doc_options[selected_doc_name]


# ─── MAIN CHAT AREA ─────────────────────────────────────────────────────────
st.markdown('<div class="main-header">🔬 AI Research Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Ask anything about your uploaded documents — powered by RAG + Gemini</div>', unsafe_allow_html=True)

# Display chat messages
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f'<div class="user-msg">{msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="ai-msg">{msg["content"]}</div>', unsafe_allow_html=True)
        # Show sources if available
        if msg.get("sources"):
            with st.expander(f"📎 Sources ({len(msg['sources'])} references)", expanded=False):
                for src in msg["sources"]:
                    relevance_pct = int(src["relevance"] * 100)
                    st.markdown(f"""
                    <div class="source-card">
                        <div class="source-filename">📄 {src['filename']}</div>
                        <div class="source-meta">Page {src['page'] + 1} · Relevance: {relevance_pct}%</div>
                        <div class="source-preview">{src['preview']}</div>
                    </div>
                    """, unsafe_allow_html=True)

# Chat input
if prompt := st.chat_input("Ask a question about your documents..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.markdown(f'<div class="user-msg">{prompt}</div>', unsafe_allow_html=True)

    # Query the RAG engine
    with st.spinner("🔍 Searching documents & generating answer..."):
        # Send up to the last 6 messages as history
        history_msgs = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[:-1][-6:]]
        
        payload = {
            "question": prompt,
            "history": history_msgs
        }
        if st.session_state.get("selected_doc_id"):
            payload["doc_id"] = st.session_state.selected_doc_id
        result = api_post("/query", json=payload)

    if result:
        answer = result["answer"]
        sources = result.get("sources", [])

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "sources": sources,
        })

        st.markdown(f'<div class="ai-msg">{answer}</div>', unsafe_allow_html=True)

        if sources:
            with st.expander(f"📎 Sources ({len(sources)} references)", expanded=True):
                for src in sources:
                    relevance_pct = int(src["relevance"] * 100)
                    st.markdown(f"""
                    <div class="source-card">
                        <div class="source-filename">📄 {src['filename']}</div>
                        <div class="source-meta">Page {src['page'] + 1} · Relevance: {relevance_pct}%</div>
                        <div class="source-preview">{src['preview']}</div>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        error_msg = "Sorry, something went wrong. Make sure the backend is running."
        st.session_state.messages.append({"role": "assistant", "content": error_msg})
        st.markdown(f'<div class="ai-msg">{error_msg}</div>', unsafe_allow_html=True)

# Empty state
if not st.session_state.messages:
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="stat-box">
            <div style="font-size: 2rem; margin-bottom: 8px;">📄</div>
            <div class="doc-name">Upload Documents</div>
            <div class="source-meta" style="margin-top: 6px;">PDF, TXT, MD, CSV files supported</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="stat-box">
            <div style="font-size: 2rem; margin-bottom: 8px;">🔍</div>
            <div class="doc-name">Ask Questions</div>
            <div class="source-meta" style="margin-top: 6px;">AI searches your docs for answers</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="stat-box">
            <div style="font-size: 2rem; margin-bottom: 8px;">📎</div>
            <div class="doc-name">Get Sources</div>
            <div class="source-meta" style="margin-top: 6px;">Every answer cites its sources</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("")
    st.markdown("**💡 Try asking:**")
    suggestions = [
        "What are the key findings in my document?",
        "Summarize the main points",
        "What does the document say about...",
    ]
    cols = st.columns(3)
    for i, suggestion in enumerate(suggestions):
        with cols[i]:
            if st.button(suggestion, key=f"suggestion_{i}", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": suggestion})
                st.rerun()
