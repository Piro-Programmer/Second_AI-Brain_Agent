import streamlit as st
import streamlit_authenticator as stauth

import lib.config as config
import lib.db as db
from lib import password_reset
from capture import capture_note
from brain_pipeline import run_full_pipeline
from ask import ask, get_notes_by_id
from lib.build_graph import build_graph
from lib.llm import LLMError
from lib.graph_view import build_graph_html

# -----------------------------------------------------------------------------
# 1. Page Config & Custom Styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="SecondSelf // AI Second Brain",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Glassmorphic Dark UI Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
    }

    /* Main container background */
    .stApp {
        background: radial-gradient(circle at 50% 0%, #1a1d2e 0%, #0f1016 100%);
        color: #f8fafc;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: rgba(15, 16, 22, 0.95);
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }

    /* Custom metric cards */
    div[data-testid="metric-container"] {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 0.8rem 1rem;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        background-color: transparent;
        border-bottom: 1px solid rgba(255,255,255,0.1);
    }

    .stTabs [data-baseweb="tab"] {
        height: 50px;
        font-family: 'Outfit', sans-serif;
        font-size: 1.1rem;
        font-weight: 600;
        color: #94a3b8;
    }

    .stTabs [aria-selected="true"] {
        color: #6366f1 !important;
        border-bottom: 2px solid #6366f1 !important;
    }

    /* Answer Box Styling */
    .answer-box {
        background: rgba(99, 102, 241, 0.08);
        border: 1px solid rgba(99, 102, 241, 0.25);
        border-radius: 16px;
        padding: 1.5rem;
        margin-top: 1rem;
        margin-bottom: 2rem;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
    }

    /* Category Badges */
    .badge-Projects { background: rgba(255, 107, 107, 0.15); color: #FF6B6B; border: 1px solid #FF6B6B; padding: 2px 8px; border-radius: 6px; font-size: 0.8rem; font-weight: 600; }
    .badge-Areas { background: rgba(78, 205, 196, 0.15); color: #4ECDC4; border: 1px solid #4ECDC4; padding: 2px 8px; border-radius: 6px; font-size: 0.8rem; font-weight: 600; }
    .badge-Resources { background: rgba(69, 183, 209, 0.15); color: #45B7D1; border: 1px solid #45B7D1; padding: 2px 8px; border-radius: 6px; font-size: 0.8rem; font-weight: 600; }
    .badge-Archives { background: rgba(150, 206, 180, 0.15); color: #96CEB4; border: 1px solid #96CEB4; padding: 2px 8px; border-radius: 6px; font-size: 0.8rem; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Authentication Layer
# -----------------------------------------------------------------------------
# Users live in the database (Supabase Postgres in the cloud, SQLite locally), so accounts
# survive restarts and redeploys. streamlit-authenticator works on an in-memory credentials
# dict; db.sync_credentials() writes any change back to the database.
credentials = db.load_credentials()
authenticator = stauth.Authenticate(credentials, "secondself_auth_cookie", db.get_cookie_key(), 30)

def render_forgot_password():
    st.markdown("#### Forgot your password?")
    st.caption("We'll email you a 6-digit code. Use it below to set a new password.")
    with st.form("forgot_request", clear_on_submit=False):
        who = st.text_input("Username or email", key="reset_request_who")
        if st.form_submit_button("Email me a reset code") and who.strip():
            try:
                st.info(password_reset.request_reset(who))
                st.session_state["reset_for"] = who.strip()
            except Exception as e:
                print(f"Password reset email failed: {e}")
                st.error("Couldn't send the email right now. Please try again later.")

    with st.form("forgot_confirm", clear_on_submit=False):
        who = st.text_input("Username or email", value=st.session_state.get("reset_for", ""),
                            key="reset_confirm_who")
        code = st.text_input("6-digit code", max_chars=6)
        new_pw = st.text_input("New password", type="password", help=password_reset.PASSWORD_RULES)
        repeat_pw = st.text_input("Repeat new password", type="password")
        if st.form_submit_button("Set new password"):
            ok, message = password_reset.confirm_reset(who, code, new_pw, repeat_pw)
            (st.success if ok else st.error)(message)

if not st.session_state.get("authentication_status"):
    login_tab, register_tab, forgot_tab = st.tabs(["Login", "Register", "Forgot password"])
    with login_tab:
        authenticator.login("main")
    with register_tab:
        st.caption(f"Password must be {password_reset.PASSWORD_RULES}.")
        try:
            new_email, new_username, _ = authenticator.register_user("main")
            if new_email:
                db.sync_credentials(credentials)
                st.success("Account created. Open the **Login** tab to sign in.")
        except Exception as e:
            st.error(e)
    with forgot_tab:
        render_forgot_password()

if st.session_state.get("authentication_status") is False:
    st.error("Username/password is incorrect")
    st.stop()
elif st.session_state.get("authentication_status") is None:
    st.warning("Please enter your username and password")
    st.stop()

username = st.session_state["username"]
config.set_user(username)
authenticator.logout('Logout', 'sidebar')

# -----------------------------------------------------------------------------
# 2. Cached Data Loaders (cleared whenever notes change)
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_graph_data(username):
    return build_graph(username)

@st.cache_data(show_spinner=False)
def get_all_notes_cached(username):
    # Drop embeddings: the UI never needs them and they bloat the cache
    return {k: {**n, "embedding": None} for k, n in get_notes_by_id(username).items()}

@st.cache_data(show_spinner=False)
def count_unprocessed(username):
    return len(db.get_notes(username, processed=False))

# -----------------------------------------------------------------------------
# 3. Sidebar: Quick Capture & Pipeline Engine
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🧠 SecondSelf")
    st.caption("The Autonomous AI Second Brain")
    st.divider()

    # Quick Capture Form
    st.subheader("⚡ Quick Capture")
    with st.form("capture_form", clear_on_submit=True):
        new_note_text = st.text_area("Capture note, idea, or link...", height=100, placeholder="Type an idea, summary, or paste text...")
        submitted_capture = st.form_submit_button("📥 Save note", use_container_width=True)
        if submitted_capture and new_note_text.strip():
            capture_note(new_note_text.strip(), username)
            count_unprocessed.clear()
            st.success("Saved! Click **🚀 Process & Link** to file it.")

    waiting = count_unprocessed(username)
    if waiting:
        st.caption(f"📥 {waiting} note(s) waiting to be processed")

    st.divider()

    # Brain Orchestration Engine
    st.subheader("⚙️ Brain Engine")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 Process & Link", use_container_width=True, help="Run Classify -> Auto-Link -> Rebuild Graph"):
            with st.spinner("Organizing, filing, and mapping brain..."):
                run_full_pipeline(username)
                st.cache_data.clear()
            st.success("Brain updated!")
    with col2:
        if st.button("🔄 Refresh UI", use_container_width=True, help="Reload caches and update views"):
            st.cache_data.clear()
            st.rerun()

    st.divider()

    # Knowledge Stats
    st.subheader("📊 Brain Metrics")
    graph_data = load_graph_data(username)
    all_notes = get_all_notes_cached(username)

    m_col1, m_col2 = st.columns(2)
    with m_col1:
        st.metric("Total Notes", graph_data["metadata"].get("node_count", len(all_notes)))
    with m_col2:
        st.metric("Graph Edges", graph_data["metadata"].get("edge_count", 0))

    # PARA Breakdown
    para_counts = {"Projects": 0, "Areas": 0, "Resources": 0, "Archives": 0}
    for n in all_notes.values():
        p = n.get("para", "Resources")
        if p in para_counts:
            para_counts[p] += 1

    p1, p2 = st.columns(2)
    with p1:
        st.metric("🔴 Projects", para_counts["Projects"])
        st.metric("🔵 Resources", para_counts["Resources"])
    with p2:
        st.metric("🟢 Areas", para_counts["Areas"])
        st.metric("🟣 Archives", para_counts["Archives"])

# -----------------------------------------------------------------------------
# 4. Main App Header & Tabs
# -----------------------------------------------------------------------------
st.title("🧠 SecondSelf // Your Personal AI Second Brain")
st.caption("Capture anything. AI automatically classifies, auto-links, maps to a live knowledge graph, and synthesizes answers in plain English.")

tab_graph, tab_ask, tab_library, tab_account = st.tabs(["🌌 Brain Graph", "🔮 Ask The Oracle", "📚 Note Library", "👤 Account Dashboard"])

# -----------------------------------------------------------------------------
# TAB 1: INTERACTIVE BRAIN GRAPH (vis-network)
# -----------------------------------------------------------------------------
with tab_graph:
    st.markdown("### Interactive Knowledge Network")
    st.write("Hover over any node to view its summary and tags. Drag nodes to explore relationships.")

    if not graph_data["nodes"]:
        st.warning("No notes in your brain yet. Capture a note, then click **🚀 Process & Link** in the sidebar to build your graph!")
    else:
        # Generate inline HTML for vis-network
        html_code = build_graph_html(graph_data)
        st.iframe(html_code, height=620)

        # Node Details Inspector below graph
        st.markdown("#### 🔍 Explore Node Details")
        node_options = {f"[{n.get('para', 'Resources')}] {n.get('summary', 'Untitled')}": n.get("id", str(k)) for k, n in all_notes.items()}
        selected_node_label = st.selectbox("Select a note to inspect full contents:", ["-- Select Note --"] + sorted(list(node_options.keys())))

        if selected_node_label != "-- Select Note --":
            selected_id = node_options[selected_node_label]
            note_obj = all_notes.get(selected_id)
            if note_obj:
                with st.expander(f"📄 Full Note: {note_obj.get('summary', 'Untitled')}", expanded=True):
                    c1, c2 = st.columns([1, 4])
                    with c1:
                        st.markdown(f"**Category:** `<span class='badge-{note_obj.get('para', 'Resources')}'>{note_obj.get('para', 'Resources')}</span>`", unsafe_allow_html=True)
                        st.markdown(f"**ID:** `{str(note_obj.get('id', 'N/A'))[:8]}...`")
                        if note_obj["tags"]:
                            st.markdown(f"**Tags:** {', '.join(note_obj['tags'])}")
                    with c2:
                        st.markdown(note_obj.get("content", ""))

# -----------------------------------------------------------------------------
# TAB 2: ASK THE ORACLE (RAG Q&A)
# -----------------------------------------------------------------------------
with tab_ask:
    st.markdown("### 🔮 Ask Your Second Brain")
    st.write("Ask any question in plain English. SecondSelf retrieves the most relevant notes using semantic vector embeddings and synthesizes a direct answer using Groq LLM.")

    q_col1, q_col2 = st.columns([4, 1])
    with q_col1:
        user_question = st.text_input("Question:", placeholder="e.g., What do I know about Git commands? What are my career goals?")
    with q_col2:
        top_k_val = st.slider("Top-K Notes", min_value=1, max_value=10, value=5)

    ask_button = st.button("⚡ Synthesize Answer", type="primary", use_container_width=True)

    if ask_button and user_question.strip():
        with st.spinner("Searching semantic embeddings and generating answer..."):
            try:
                result = ask(user_question.strip(), top_k=top_k_val, username=username)
            except LLMError as e:
                print(e)
                st.error("The AI model is unavailable right now. Please try again in a minute.")
                st.stop()

        st.markdown("### Answer")
        # Plain st.markdown renders formatting but escapes raw HTML, so note text can't inject markup
        with st.container(border=True):
            st.markdown(result["answer"])

        st.markdown(f"### 📚 Sources Cited ({len(result['sources'])} notes)")
        if not result["sources"]:
            st.info(f"No notes exceeded the similarity threshold ({config.SIMILARITY_RETRIEVAL_MIN:.2f}) for this query.")
        else:
            for idx, src in enumerate(result["sources"], 1):
                src_note = all_notes.get(src["id"])
                score_pct = int(src["relevance_score"] * 100)

                with st.expander(f"{idx}. [{src.get('para', 'Resources')}] {src.get('summary', 'Untitled')} — (Relevance: {src['relevance_score']:.4f})"):
                    sc1, sc2 = st.columns([1, 4])
                    with sc1:
                        st.metric("Similarity", f"{score_pct}%")
                        st.markdown(f"**Category:** `{src.get('para', 'Resources')}`")
                        st.markdown(f"**ID:** `{str(src.get('id', 'N/A'))[:8]}...`")
                    with sc2:
                        if src_note:
                            st.markdown("---")
                            st.markdown(src_note.get("content", ""))
                        else:
                            st.write("Content preview unavailable.")

# -----------------------------------------------------------------------------
# TAB 3: NOTE LIBRARY
# -----------------------------------------------------------------------------
with tab_library:
    st.markdown("### 📚 Accumulated Note Library")

    lib_col1, lib_col2 = st.columns([1, 3])
    with lib_col1:
        filter_para = st.selectbox("Filter by PARA Category:", ["All", "Projects", "Areas", "Resources", "Archives"])
    with lib_col2:
        search_query = st.text_input("Filter by Keyword in Title:", placeholder="Search titles...")

    filtered_notes = list(all_notes.values())
    if filter_para != "All":
        filtered_notes = [n for n in filtered_notes if n.get("para") == filter_para]
    if search_query.strip():
        filtered_notes = [n for n in filtered_notes if search_query.lower() in n.get("summary", "").lower()]

    st.caption(f"Showing {len(filtered_notes)} note(s)")

    for note in sorted(filtered_notes, key=lambda x: x.get("summary", "")):
        with st.expander(f"[{note.get('para', 'Resources')}] {note.get('summary', 'Untitled')}"):
            st.caption(f"Captured {note['created_at']:%d %b %Y, %H:%M} · {note['source_type']}")
            if note["tags"]:
                st.markdown(f"**Tags:** `{', '.join(note['tags'])}`")
            st.divider()
            st.markdown(note["content"])
            if st.button("🗑️ Delete note", key=f"delete_{note['id']}"):
                db.delete_note(username, note["id"])
                st.cache_data.clear()
                st.rerun()

# -----------------------------------------------------------------------------
# TAB 4: ACCOUNT DASHBOARD
# -----------------------------------------------------------------------------
with tab_account:
    st.markdown("### 👤 Account Dashboard")
    
    acc_col1, acc_col2 = st.columns([1, 1])
    
    with acc_col1:
        st.markdown("#### User Profile")
        user_info = credentials['usernames'].get(username, {})
        st.text_input("Name", value=f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip(), disabled=True)
        st.text_input("Email", value=user_info.get('email', ''), disabled=True)
        st.text_input("Username", value=st.session_state["username"], disabled=True)
        
        st.markdown("#### Storage Metrics")
        st.metric("Total Brain Notes", graph_data["metadata"].get("node_count", len(all_notes)))
        st.metric("Knowledge Graph Edges", graph_data["metadata"].get("edge_count", 0))

    with acc_col2:
        st.markdown("#### Account Management")
        
        try:
            if authenticator.reset_password(username, location="main", key="Reset Password"):
                db.sync_credentials(credentials)
                st.success("Password modified successfully")
        except Exception as e:
            st.error(e)
            
        st.divider()
        try:
            if authenticator.update_user_details(username, location="main", key="Update User Details"):
                db.sync_credentials(credentials)
                st.success("Entries updated successfully")
        except Exception as e:
            st.error(e)

    st.divider()
    # Add a prominent logout button on the dashboard as well
    authenticator.logout('Logout from Dashboard', 'main', key='Logout_Dashboard')
