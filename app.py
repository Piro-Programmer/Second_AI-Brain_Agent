import os
import sys
import json
import glob
import frontmatter
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime

import lib.config as config
from lib.io import ensure_dir
from capture import capture_note
from pipeline import run_full_pipeline
from ask import ask, get_wiki_note_by_id

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
# 2. Cached Data Loaders
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_graph_data():
    if os.path.exists(config.GRAPH_PATH):
        try:
            with open(config.GRAPH_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"nodes": [], "edges": [], "metadata": {"node_count": 0, "edge_count": 0}}

@st.cache_data(show_spinner=False)
def get_all_notes_cached():
    return get_wiki_note_by_id()

@st.cache_resource(show_spinner=False)
def load_embeddings_db():
    from lib.embeddings import load_embeddings
    return load_embeddings(os.path.join(config.DATA_DIR, "embeddings.pkl"))

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
        submitted_capture = st.form_submit_button("📥 Save to Raw", use_container_width=True)
        if submitted_capture and new_note_text.strip():
            capture_note(new_note_text.strip())
            st.success("Saved to raw/ buffer!")
            
    st.divider()
    
    # Brain Orchestration Engine
    st.subheader("⚙️ Brain Engine")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 Process & Link", use_container_width=True, help="Run Classify -> Auto-Link -> Rebuild Graph"):
            with st.spinner("Organizing, filing, and mapping brain..."):
                run_full_pipeline()
                st.cache_data.clear()
                st.cache_resource.clear()
            st.success("Brain updated!")
    with col2:
        if st.button("🔄 Refresh UI", use_container_width=True, help="Reload caches and update views"):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.rerun()
            
    st.divider()
    
    # Knowledge Stats
    st.subheader("📊 Brain Metrics")
    graph_data = load_graph_data()
    all_notes = get_all_notes_cached()
    
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

tab_graph, tab_ask, tab_library = st.tabs(["🌌 Brain Graph", "🔮 Ask The Oracle", "📚 Note Library"])

# -----------------------------------------------------------------------------
# TAB 1: INTERACTIVE BRAIN GRAPH (vis-network)
# -----------------------------------------------------------------------------
with tab_graph:
    st.markdown("### Interactive Knowledge Network")
    st.write("Hover over any node to view its summary and tags. Drag nodes to explore relationships.")
    
    if not graph_data["nodes"]:
        st.warning("No nodes found in graph.json. Click **🚀 Process & Link** in the sidebar to build your graph!")
    else:
        # Generate inline HTML for vis-network
        html_code = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
            <style>
                body {{
                    margin: 0;
                    padding: 0;
                    background-color: #0f1016;
                    color: #f8fafc;
                    font-family: 'Inter', sans-serif;
                }}
                #mynetwork {{
                    width: 100%;
                    height: 600px;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 12px;
                    background: radial-gradient(circle at 50% 50%, #1e2030 0%, #0f1016 100%);
                }}
            </style>
        </head>
        <body>
            <div id="mynetwork"></div>
            <script type="text/javascript">
                const graphData = {json.dumps(graph_data)};
                
                const nodes = new vis.DataSet(graphData.nodes.map(n => ({{
                    id: n.id,
                    label: n.label.length > 25 ? n.label.substring(0, 25) + '...' : n.label,
                    title: `<div style="padding:10px; background:#1a1c28; color:#fff; border-radius:8px; border:1px solid #6366f1; max-width:250px;">
                              <b style="color:${{n.color}}">[${{n.para}}]</b><br/>
                              <b>${{n.label}}</b><br/><br/>
                              <span style="font-size:0.85em; color:#94a3b8;">${{n.preview || ''}}</span>
                            </div>`,
                    color: {{
                        background: n.color || '#45B7D1',
                        border: '#ffffff',
                        highlight: {{ background: '#6366f1', border: '#ffffff' }},
                        hover: {{ background: n.color || '#45B7D1', border: '#ffffff' }}
                    }},
                    font: {{ color: '#f8fafc', face: 'Inter', size: 13 }},
                    shape: 'dot',
                    size: n.size || 16
                }})));

                const edges = new vis.DataSet(graphData.edges.map(e => ({{
                    from: e.from || e.source,
                    to: e.to || e.target,
                    color: {{ color: 'rgba(255, 255, 255, 0.25)', highlight: '#6366f1' }},
                    width: 1.5,
                    smooth: {{ type: 'continuous' }}
                }})));

                const container = document.getElementById('mynetwork');
                const data = {{ nodes: nodes, edges: edges }};
                const options = {{
                    physics: {{
                        barnesHut: {{
                            gravitationalConstant: -3000,
                            centralGravity: 0.3,
                            springLength: 150,
                            springConstant: 0.04,
                            damping: 0.09
                        }},
                        stabilization: {{ iterations: 150 }}
                    }},
                    interaction: {{
                        hover: true,
                        tooltipDelay: 100,
                        zoomView: true,
                        dragView: true
                    }}
                }};
                
                new vis.Network(container, data, options);
            </script>
        </body>
        </html>
        """
        components.html(html_code, height=620, scrolling=False)
        
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
                        if note_obj.get("post", {}).get("tags"):
                            st.markdown(f"**Tags:** {', '.join(note_obj['post'].get('tags', []))}")
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
            result = ask(user_question.strip(), top_k=top_k_val)
            
        st.markdown("### Answer")
        st.markdown(f'<div class="answer-box">{result["answer"]}</div>', unsafe_allow_html=True)
        
        st.markdown(f"### 📚 Sources Cited ({len(result['sources'])} notes)")
        if not result["sources"]:
            st.info("No notes exceeded the similarity threshold (0.30) for this query.")
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
            st.markdown(f"**UUID:** `{note.get('id', 'N/A')}`")
            if note["post"].get("tags"):
                st.markdown(f"**Tags:** `{', '.join(note['post'].get('tags', []))}`")
            if note["post"].get("aliases"):
                st.markdown(f"**Obsidian Aliases:** `{', '.join(note['post'].get('aliases', []))}`")
            st.divider()
            st.markdown(note["content"])
