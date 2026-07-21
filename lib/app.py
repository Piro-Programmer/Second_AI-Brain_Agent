import streamlit as st
import os
import json
import lib.config as config

st.title("SecondSelf — Verification Dashboard")

st.sidebar.header("Stats")
if os.path.exists(config.RAW_DIR):
    folders = [f for f in os.listdir(config.RAW_DIR) if os.path.isdir(os.path.join(config.RAW_DIR, f))]
    st.sidebar.metric("Raw Captures", len(folders))
else:
    st.sidebar.metric("Raw Captures", 0)

st.write("Below are the items you have captured so far in your `raw/` folder:")

if os.path.exists(config.RAW_DIR):
    folders = sorted([f for f in os.listdir(config.RAW_DIR) if os.path.isdir(os.path.join(config.RAW_DIR, f))], reverse=True)
    if not folders:
        st.info("No captures found yet. Run `python capture.py` to add some!")
    for folder in folders:
        folder_path = os.path.join(config.RAW_DIR, folder)
        content_path = os.path.join(folder_path, "content.md")
        meta_path = os.path.join(folder_path, "meta.json")

        if os.path.exists(content_path) and os.path.exists(meta_path):
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)

                with open(content_path, "r", encoding="utf-8") as f:
                    content = f.read()

                title = f"{meta['timestamp']} - {meta['source_type'].upper()}"
                if meta.get("url"):
                    title += f" ({meta['url']})"
                elif meta.get("original_filename"):
                    title += f" ({meta['original_filename']})"

                with st.expander(title):
                    st.text(content)
            except Exception as e:
                st.error(f"Error loading capture {folder}: {e}")
else:
    st.info("No captures directory found. Run `python capture.py` to create it!")
