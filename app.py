import streamlit as st
import pandas as pd
import os
import json
from database import Engine, Session, ContentItem
from worker import VIOSWorker

st.set_page_config(page_title="VIOS | Control Center", layout="wide", page_icon="🚀")

# --- STYLING ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stMetric { background-color: #161b22; border-radius: 10px; border: 1px solid #30363d; }
    .status-draft { color: #8b949e; }
    .status-scripting { color: #58a6ff; }
    .status-rendering { color: #d29922; }
    .status-scheduled { color: #bc8cff; }
    .status-published { color: #3fb950; }
    .status-error { color: #f85149; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 VIOS Autonomous Control Center")
st.markdown("Real-time monitoring of the Virtual Influencer Content Pipeline")

# --- METRICS ---
with Session(Engine) as session:
    all_items = session.exec(ContentItem.select()).all()
    df_items = pd.DataFrame([
        {"ID": i.id, "Status": i.status, "Creator": i.creator_name, "Error": i.error_log}
        for i in all_items
    ])

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Content", len(df_items))
col2.metric("Pending Rendering", len(df_items[df_items['Status'] == 'SCRIPTING']))
col3.metric("Ready to Publish", len(df_items[df_items['Status'] == 'SCHEDULED']))
col4.metric("Errors", len(df_items[df_items['Status'] == 'ERROR']))

st.divider()

# --- MONITORING TAB ---
tab_queue, tab_controls, tab_logs = st.tabs(["📦 Content Queue", "⚙️ Engine Controls", "📜 System Logs"])

with tab_queue:
    st.subheader("Current Production Pipeline")
    if not df_items.empty:
        # Custom coloring for status
        def color_status(val):
            colors = {
                "DRAFT": "status-draft",
                "SCRIPTING": "status-scripting",
                "RENDERING": "status-rendering",
                "SCHEDULED": "status-scheduled",
                "PUBLISHED": "status-published",
                "ERROR": "status-error"
            }
            return f"color: {colors.get(val, 'white')}"

        # Creating a stylized table
        for _, row in df_items.iterrows():
            with st.expander(f"Item {row['ID']} - {row['Status']}"):
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.markdown(f"**Creator:** {row['Creator']}")
                    if row['Error']:
                        st.error(f"Last Error: {row['Error']}")
                with col_b:
                    if row['Status'] == "ERROR":
                        if st.button(f"Retry {row['ID']}", key=f"retry_{row['ID']}"):
                            with Session(Engine) as s:
                                item = s.get(ContentItem, row['ID'])
                                item.status = "DRAFT"
                                s.add(item)
                                s.commit()
                                st.rerun()
    else:
        st.info("No content in the pipeline. Add items to database to start.")

with tab_controls:
    st.subheader("Worker Orchestration")

    if st.button("⚡ Force Pipeline Cycle Now", use_container_width=True):
        # Trigger a manual run of the worker cycle
        worker = VIOSWorker()
        worker.run_pipeline_cycle()
        st.success("Manual cycle triggered successfully!")

    st.divider()
    st.markdown("### 🧪 System Diagnostics")
    if st.button("Test Telegram Notification", use_container_width=True):
        from resilience import notify_telegram
        notify_telegram("🧪 VIOS System Test: Dashboard is active and connected!")
        st.success("Notification sent!")

with tab_logs:
    st.subheader("Execution Logs")
    # Mocking logs from the worker
    log_file = "worker.log" # In a real scenario, this would be a real file
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            st.code(f.read(), language="text")
    else:
        st.info("No log file found. Check the terminal for real-time worker output.")

# --- FOOTER ---
st.divider()
st.caption("VIOS v2.0 | Industrial-Grade Autonomous Content Engine")
