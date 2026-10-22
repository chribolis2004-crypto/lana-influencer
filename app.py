import streamlit as st
import pandas as pd
import os
import subprocess

st.set_page_config(page_title="Lana | Content Studio", layout="wide", page_icon="🌸")

# --- API KEY MANAGEMENT ---
def get_gemini_api_key():
    try:
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        pass

    if os.getenv("GEMINI_API_KEY"):
        return os.getenv("GEMINI_API_KEY")

    return None

# Retrieve the key at the start
api_key_val = get_gemini_api_key()

if not api_key_val:
    st.sidebar.warning("🔑 API Key mancante")
    user_key = st.sidebar.text_input("Inserisci la tua GEMINI_API_KEY", type="password")
    if user_key:
        gemini_api_key = user_key
    else:
        st.sidebar.error("L'app è bloccata. Inserisci la chiave API nella sidebar per continuare.")
        st.stop()
else:
    gemini_api_key = api_key_val

# Custom CSS for SaaS look
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    div[data-testid="stExpander"] {
        background-color: #ffffff;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🌸 Lana | Content Studio")
st.markdown("Professional Influencer Management Dashboard")

# Load data
if os.path.exists('content_calendar.csv'):
    df = pd.read_csv('content_calendar.csv')
else:
    # Create a default content calendar if not found
    st.info("📅 Content calendar not found. Creating a new one with sample data...")
    default_data = {
        'date': ['2026-10-25', '2026-10-26', '2026-10-27'],
        'pillar': ['fashion', 'beauty', 'lifestyle'],
        'concept': ['Autumn Vibes', 'Skin Glow', 'Morning Coffee'],
        'hook': ['Must-have autumn looks', 'Get the perfect glow', 'My secret routine'],
        'caption': ['Elevate your style', 'Dewy skin secrets', 'Slow morning vibes'],
        'format': ['close_up', 'carousel', 'short_video'],
        'visual_prompt': ['Lana in a beige blazer', 'Close up of skin', 'Lana drinking matcha'],
        'product_id': ['', '', ''],
        'qa_status': ['pending', 'pending', 'pending'],
        'qa_notes': ['', '', ''],
        'image_path': ['', '', ''],
        'production_status': ['pending', 'pending', 'pending'],
        'publish_status': ['draft', 'draft', 'draft'],
        'published_at': ['', '', ''],
        'content_id': ['LAN_100', 'LAN_101', 'LAN_102']
    }
    df = pd.DataFrame(default_data)
    df.to_csv('content_calendar.csv', index=False)

# --- SECTION 1: KPI DASHBOARD ---
st.subheader("Analytics Overview")
col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)

total_posts = len(df)
approved_posts = len(df[df['qa_status'] == 'approved'])
assets_generated = len(df[df['production_status'] == 'ready'])
in_queue = len(df[(df['qa_status'] == 'approved') & (df['production_status'] == 'pending')])

col_kpi1.metric("Total Posts", total_posts)
col_kpi2.metric("Approved", approved_posts, delta=f"{(approved_posts/total_posts*100 if total_posts>0 else 0):.1f}%")
col_kpi3.metric("Assets Ready", assets_generated)
col_kpi4.metric("In Production Queue", in_queue)

st.divider()

# --- SECTION 2: WORKSPACE TABS ---
tab_calendar, tab_studio, tab_publish = st.tabs(["📅 Calendario & QA", "🎨 Studio Asset", "🚀 Coda di Pubblicazione"])

# --- TAB 1: CALENDARIO & QA ---
with tab_calendar:
    st.subheader("Content Pipeline")

    def color_status(val):
        if val == 'approved': return 'background-color: #d4edda; color: #155724'
        elif val == 'rejected': return 'background-color: #f8d7da; color: #721c24'
        else: return 'background-color: #fff3cd; color: #856404'

    st.dataframe(df.style.map(color_status, subset=['qa_status']), use_container_width=True)

    st.markdown("### 🛠️ Quick Quality Action")
    selected_index = st.selectbox("Select post to review", options=df.index, format_func=lambda x: f"Row {x}: {df.iloc[x]['concept']}")

    # Contextual row data for the reviewer
    row = df.iloc[selected_index]
    st.info(f"**Reviewing:** {row['concept']} | **Format:** {row['format']} | **Status:** {row['qa_status']}")

    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        if st.button("✅ Approve Post", use_container_width=True):
            df.at[selected_index, 'qa_status'] = 'approved'
            df.at[selected_index, 'qa_notes'] = "Manually approved"
            df.to_csv('content_calendar.csv', index=False)
            st.success("Approved!")
            st.rerun()
    with c2:
        if st.button("❌ Reject Post", use_container_width=True):
            df.at[selected_index, 'qa_status'] = 'rejected'
            df.at[selected_index, 'qa_notes'] = "Needs correction"
            df.to_csv('content_calendar.csv', index=False)
            st.error("Rejected!")
            st.rerun()
    with c3:
        st.text_input("QA Note", value=row['qa_notes'] if pd.notna(row['qa_notes']) else "")

# --- TAB 2: STUDIO ASSET ---
with tab_studio:
    st.subheader("Visual Asset Production")

    # Action button positioned at the top
    if st.button("🚀 Generate All Ready Assets", use_container_width=True):
        with st.spinner("Google Gemini is creating your assets..."):
            # We inject the API key into the environment for the subprocess
            env = os.environ.copy()
            env["GEMINI_API_KEY"] = gemini_api_key
            result = subprocess.run(['python', 'asset_generator.py'], capture_output=True, text=True, env=env)
            if result.returncode == 0:
                st.success("Assets generated successfully!")
                st.rerun()
            else:
                st.error(f"Generation Error: {result.stderr}")

    st.divider()

    # Gallery View
    gallery_cols = st.columns(3)
    asset_idx = 0
    for idx, row in df.iterrows():
        if pd.notna(row['image_path']) and row['image_path'] != "":
            with gallery_cols[asset_idx % 3]:
                fmt = str(row['format']).lower()
                path_val = row['image_path']

                # Professional Card-like container
                with st.expander(f"📦 {row['concept']}", expanded=True):
                    if fmt == 'carousel':
                        paths = path_val.split(',')
                        st.caption("Carousel Sequence")
                        # Sub-grid for carousel slides
                        c_slides = st.columns(len(paths))
                        for i, p in enumerate(paths):
                            if os.path.exists(p):
                                c_slides[i].image(p, use_container_width=True)
                    elif fmt == 'short_video':
                        st.caption("Short-form Video")
                        if os.path.exists(path_val):
                            st.video(path_val)
                    else:
                        st.caption("Single Asset")
                        st.image(path_val, use_container_width=True)
                asset_idx += 1

# --- TAB 3: CODA DI PUBBLICAZIONE ---
with tab_publish:
    st.subheader("Publishing Control Center")

    ready_to_publish = df[(df['qa_status'] == 'approved') & (df['production_status'] == 'ready') & (df['publish_status'] == 'draft')]

    if not ready_to_publish.empty:
        st.markdown("### 📤 Ready to Push")
        st.table(ready_to_publish[['date', 'concept', 'format', 'image_path']])

        p_col1, p_col2 = st.columns(2)
        with p_col1:
            if st.button("🚀 Avvia Pubblicazione Schedulata", use_container_width=True):
                with st.spinner("Pushing to platforms..."):
                    result = subprocess.run(['python', 'publisher.py'], capture_output=True, text=True)
                    st.text(result.stdout)
                    if result.returncode == 0:
                        st.success("Published!")
                        st.rerun()
        with p_col2:
            if st.button("⚡ Forza Pubblicazione Immediata", use_container_width=True):
                with st.spinner("Forcing all ready assets..."):
                    result = subprocess.run(['python', 'publisher.py', '--force'], capture_output=True, text=True)
                    st.text(result.stdout)
                    if result.returncode == 0:
                        st.success("Forced publication complete!")
                    st.rerun()
    else:
        st.info("The queue is currently empty. Approve more posts and generate assets to fill the pipeline.")
