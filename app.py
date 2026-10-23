import streamlit as st
import pandas as pd
import os
import subprocess
import json
import yaml
import csv
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Lana | Multi-Influencer Studio", layout="wide", page_icon="🌸")

# --- PATH CONFIGURATION ---
CREATORS_DIR = "creators"

def ensure_creator_dir(creator_name):
    """Ensures the creator directory and essential subfolders exist."""
    base_path = os.path.join(CREATORS_DIR, creator_name)
    os.makedirs(base_path, exist_ok=True)
    os.makedirs(os.path.join(base_path, "assets"), exist_ok=True)
    os.makedirs(os.path.join(base_path, "history"), exist_ok=True)
    return base_path

def get_creator_paths(creator_name):
    base_path = ensure_creator_dir(creator_name)
    return {
        "base": base_path,
        "config": os.path.join(base_path, "config.json"),
        "bible": os.path.join(base_path, "brand_bible.yaml"),
        "calendar": os.path.join(base_path, "calendar.csv"),
        "audience": os.path.join(base_path, "audience_profile.yaml"),
        "assets": os.path.join(base_path, "assets"),
        "history": os.path.join(base_path, "history"),
        "log": os.path.join(base_path, "generation.log")
    }

# --- TEMPLATES ---
DEFAULT_CONFIG = {
    "profile": {"name": "Unknown", "niche": "General", "photo_path": ""},
    "api_keys": {"instagram": "", "tiktok": "", "youtube": ""},
    "system_prompts": {
        "viral_hook": "Create a high-energy, attention-grabbing hook that stops the scroll. Use psychological triggers, a strong promise of value, and a tone that perfectly matches the creator's niche. Focus on the first 3 seconds.",
        "conversion_style": "Write a compelling call-to-action that feels natural and authentic. Drive the user toward the desired goal (link in bio, comment, or share) using a mix of urgency and soft-selling, keeping the influencer's unique voice."
    },
    "voice_tuning": {"irony": 50, "emoji_frequency": 50, "tone": "Neutral"},
    "fish_audio_voice_id": ""
}

DEFAULT_BIBLE = {
    "brand_bible": {
        "visual_identity": {
            "influencer_name": "Unknown",
            "face_reference": "Hyper-realistic facial features",
            "hair": "Natural",
            "style": "Modern aesthetic",
            "lighting": "Cinematic lighting"
        }
    }
}

DEFAULT_AUDIENCE = {
    "audience_profile": {
        "demographics": {"age_range": "18-34", "gender": "All", "location": "Global", "economic_status": "Medium"},
        "psychographics": {"interests": [], "values": []},
        "pain_points": [],
        "funnel_strategy": {
            "ToFu": {"format": "Reels", "goal": "Reach", "hook_strategy": "Visual impact"},
            "MoFu": {"format": "Stories", "goal": "Engagement", "hook_strategy": "Authenticity"},
            "BoFu": {"format": "Posts", "goal": "Conversion", "hook_strategy": "Value education"}
        }
    }
}

def regenerate_essential_files(creator_name, paths):
    """Robustly regenerates missing essential files using templates."""
    # 1. Config
    if not os.path.exists(paths["config"]):
        os.makedirs(os.path.dirname(paths["config"]), exist_ok=True)
        cfg = DEFAULT_CONFIG.copy()
        cfg["profile"]["name"] = creator_name
        with open(paths["config"], "w") as f:
            json.dump(cfg, f, indent=2)
    else:
        # Ensure system prompts are never empty
        with open(paths["config"], "r") as f:
            cfg = json.load(f)

        updated = False
        prompts = cfg.get("system_prompts", {})
        if not prompts.get("viral_hook"):
            prompts["viral_hook"] = DEFAULT_CONFIG["system_prompts"]["viral_hook"]
            updated = True
        if not prompts.get("conversion_style"):
            prompts["conversion_style"] = DEFAULT_CONFIG["system_prompts"]["conversion_style"]
            updated = True

        if updated:
            cfg["system_prompts"] = prompts
            with open(paths["config"], "w") as f:
                json.dump(cfg, f, indent=2)

    # 2. Calendar
    if not os.path.exists(paths["calendar"]):
        os.makedirs(os.path.dirname(paths["calendar"]), exist_ok=True)
        df_init = pd.DataFrame(columns=['date', 'pillar', 'concept', 'hook', 'caption', 'format', 'visual_prompt', 'product_id', 'qa_status', 'qa_stage', 'qa_notes', 'image_path', 'production_status', 'publish_status', 'published_at', 'content_id', 'funnel_stage', 'monetization_link'])
        df_init.to_csv(paths["calendar"], index=False)

    # 3. Brand Bible
    if not os.path.exists(paths["bible"]):
        os.makedirs(os.path.dirname(paths["bible"]), exist_ok=True)
        with open(paths["bible"], "w") as f:
            yaml.dump(DEFAULT_BIBLE, f)

    # 4. Audience Profile
    if not os.path.exists(paths["audience"]):
        os.makedirs(os.path.dirname(paths["audience"]), exist_ok=True)
        with open(paths["audience"], "w") as f:
            yaml.dump(DEFAULT_AUDIENCE, f)

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

# Custom CSS for SaaS look and Smartphone Mockup
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

    /* Smartphone Mockup CSS */
    .phone-container {
        width: 300px;
        height: 600px;
        background: #111;
        border-radius: 40px;
        border: 12px solid #333;
        margin: 0 auto;
        position: relative;
        overflow: hidden;
        box-shadow: 0 20px 40px rgba(0,0,0,0.3);
    }
    .phone-notch {
        width: 120px;
        height: 25px;
        background: #333;
        position: absolute;
        top: 0;
        left: 50%;
        transform: translateX(-50%);
        border-bottom-left-radius: 15px;
        border-bottom-right-radius: 15px;
        z-index: 10;
    }
    .phone-screen {
        width: 100%;
        height: 100%;
        background: #fff;
        overflow-y: auto;
        position: relative;
    }
    .phone-image {
        width: 100%;
        height: auto;
        display: block;
    }
    .phone-ui {
        padding: 15px;
        font-family: sans-serif;
        color: #333;
    }
    .phone-ui-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 15px;
    }
    .phone-profile-pic {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: #ddd;
    }
    .phone-ui-footer {
        display: flex;
        gap: 10px;
        margin-top: 10px;
        font-size: 1.2rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR: CREATOR MANAGEMENT ---
st.sidebar.title("👤 Creator Hub")

# List available creators
if not os.path.exists(CREATORS_DIR):
    os.makedirs(CREATORS_DIR)

existing_creators = [d for d in os.listdir(CREATORS_DIR) if os.path.isdir(os.path.join(CREATORS_DIR, d))]
if not existing_creators:
    # Fallback if empty
    existing_creators = ["lana"]

active_creator = st.sidebar.selectbox("Seleziona Influencer", options=existing_creators)
paths = get_creator_paths(active_creator)

# SECURITY CHECK: Regenerate missing essential files for the active creator
regenerate_essential_files(active_creator, paths)

st.sidebar.divider()
st.sidebar.subheader("➕ Aggiungi Creator")
new_creator_name = st.sidebar.text_input("Nome Creator")
new_creator_niche = st.sidebar.text_input("Nicchia")

if st.sidebar.button("Crea Profilo"):
    if new_creator_name:
        # Use the central function to ensure directories
        c_path = ensure_creator_dir(new_creator_name.lower())
        paths_new = get_creator_paths(new_creator_name.lower())
        regenerate_essential_files(new_creator_name.lower(), paths_new)

        # Override config with niche
        with open(paths_new["config"], "r") as f:
            config = json.load(f)
        config["profile"]["name"] = new_creator_name
        config["profile"]["niche"] = new_creator_niche
        with open(paths_new["config"], "w") as f:
            json.dump(config, f, indent=2)

        st.sidebar.success(f"Creator {new_creator_name} creato!")
        st.rerun()

st.title(f"🌸 {active_creator.capitalize()} | Content Studio")
st.markdown(f"Professional Influencer Management Dashboard - **{active_creator}**")

# Load data
calendar_path = paths["calendar"]
if os.path.exists(calendar_path):
    df = pd.read_csv(calendar_path)
else:
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
        'qa_stage': ['proposal', 'proposal', 'proposal'],
        'qa_notes': ['', '', ''],
        'image_path': ['', '', ''],
        'production_status': ['pending', 'pending', 'pending'],
        'publish_status': ['draft', 'draft', 'draft'],
        'published_at': ['', '', ''],
        'content_id': [f'{active_creator[:3].upper()}_{100+i}' for i in range(3)],
        'funnel_stage': ['ToFu', 'MoFu', 'BoFu'],
        'monetization_link': ['', '', '']
    }
    df = pd.DataFrame(default_data)
    df.to_csv(calendar_path, index=False)

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
tab_hub, tab_calendar, tab_studio, tab_publish = st.tabs(["👤 Creator Hub", "📅 Calendario & QA", "🎨 Studio Asset", "🚀 Coda di Pubblicazione"])

# --- TAB 0: CREATOR HUB ---
with tab_hub:
    st.subheader(f"Creator Profile: {active_creator}")

    try:
        with open(paths["config"], "r") as f:
            config = json.load(f)
        with open(paths["bible"], "r") as f:
            bible = yaml.safe_load(f)
    except Exception as e:
        st.error(f"Error loading creator files: {e}")
        config, bible = {}, {}

    c_col1, c_col2 = st.columns([1, 2])
    with c_col1:
        st.image("https://via.placeholder.com/150", caption=f"Profile Photo: {active_creator}")
        st.markdown(f"**Nicchia:** {config.get('profile', {}).get('niche', 'N/A')}")

    with c_col2:
        st.markdown("### 📜 Visual Bible & Rules")
        st.json(bible)

    st.divider()

    # BRAND VOICE TUNER
    st.markdown("### 🎙️ Brand Voice Tuner")
    v_col1, v_col2, v_col3 = st.columns(3)
    voice_cfg = config.get("voice_tuning", {"irony": 50, "emoji_frequency": 50, "tone": "Neutral"})

    with v_col1:
        irony_val = st.slider("Irony Level", 0, 100, int(voice_cfg.get("irony", 50)))
    with v_col2:
        emoji_val = st.slider("Emoji Frequency", 0, 100, int(voice_cfg.get("emoji_frequency", 50)))
    with v_col3:
        tone_val = st.select_slider("Tone", options=["Formal", "Professional", "Neutral", "Friendly", "Confidential"],
                                   value=voice_cfg.get("tone", "Neutral"))

    # --- FISH AUDIO INTEGRATION ---
    st.markdown("### 🔊 Voice Identity (Fish Audio)")
    voice_id_val = st.text_input("Fish Audio Voice ID", value=config.get("fish_audio_voice_id", ""))

    if st.button("Test Voice Generation"):
        if not voice_id_val:
            st.error("Inserisci un Voice ID per testare la voce.")
        else:
            with st.spinner("Generating test audio..."):
                import subprocess
                env = os.environ.copy()
                env["FISH_API_KEY"] = os.getenv("FISH_API_KEY", "")
                result = subprocess.run(['python', 'voice_generator.py', '--test', '--voice_id', voice_id_val],
                                      capture_output=True, text=True, env=env)
                if result.returncode == 0:
                    st.success("Test audio generated!")
                    # In a real scenario, we would play the audio using st.audio()
                    # a test file is usually saved in a temp location or the assets folder
                    st.info("Check assets folder for 'test_voice.mp3'")
                else:
                    st.error(f"Error: {result.stderr}")

    if st.button("Save Voice ID"):
        config["fish_audio_voice_id"] = voice_id_val
        with open(paths["config"], "w") as f:
            json.dump(config, f, indent=2)
        st.success("Voice ID saved!")

    if st.button("Save Voice Settings"):
        config["voice_tuning"] = {"irony": irony_val, "emoji_frequency": emoji_val, "tone": tone_val}
        with open(paths["config"], "w") as f:
            json.dump(config, f, indent=2)
        st.success("Voice tuning saved!")

    st.divider()
    st.markdown("### ⚙️ System Prompts")
    prompts = config.get("system_prompts", {})
    new_viral = st.text_area("Viral Hook Prompt", value=prompts.get("viral_hook", ""))
    new_conv = st.text_area("Conversion Style Prompt", value=prompts.get("conversion_style", ""))

    if st.button("Salva Prompt"):
        config["system_prompts"] = {"viral_hook": new_viral, "conversion_style": new_conv}
        with open(paths["config"], "w") as f:
            json.dump(config, f, indent=2)
        st.success("Prompts aggiornati!")

# --- TAB 1: CALENDARIO & QA ---
with tab_calendar:
    st.subheader("Content Pipeline")

    # KANBAN VIEW TOGGLE
    view_mode = st.radio("Visualizzazione", ["Table", "Kanban"], horizontal=True)

    if view_mode == "Table":
        def color_status(val):
            if val == 'approved': return 'background-color: #d4edda; color: #155724'
            elif val == 'rejected': return 'background-color: #f8d7da; color: #721c24'
            else: return 'background-color: #fff3cd; color: #856404'

        st.dataframe(df.style.map(color_status, subset=['qa_status']), use_container_width=True)
    else:
        # Kanban View
        cols = st.columns(4)
        kanban_cols = [
            {"name": "Proposal", "filter": lambda r: r['qa_stage'] == 'proposal'},
            {"name": "Preview", "filter": lambda r: r['qa_stage'] == 'preview' and r['production_status'] == 'pending'},
            {"name": "Asset Ready", "filter": lambda r: r['qa_stage'] == 'preview' and r['production_status'] == 'ready'},
            {"name": "Final", "filter": lambda r: r['qa_stage'] == 'final'},
        ]

        for i, k_col in enumerate(kanban_cols):
            with cols[i]:
                st.markdown(f"**{k_col['name']}**")
                filtered_df = df[df.apply(k_col['filter'], axis=1)]
                for _, row in filtered_df.iterrows():
                    st.markdown(f"""
                    <div style="background:white; padding:10px; border-radius:5px; border-left: 5px solid #ff4b4b; margin-bottom:10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);">
                        <strong>{row['concept']}</strong><br>
                        <small>{row['format']}</small>
                    </div>
                    """, unsafe_allow_html=True)

    st.markdown("### 🛠️ Two-Stage QA Flow")

    # Proposal Approval (Stage 1)
    st.markdown("#### 📝 Stage 1: Proposal Review")
    proposal_df = df[df['qa_stage'] == 'proposal']
    if not proposal_df.empty:
        selected_proposal_idx = st.selectbox("Select proposal to review", options=proposal_df.index, format_func=lambda x: f"Row {x}: {df.iloc[x]['concept']}")

        row = df.iloc[selected_proposal_idx]
        st.info(f"**Reviewing Concept:** {row['concept']} | **Hook:** {row['hook']} | **Caption:** {row['caption']}")

        p_c1, p_c2 = st.columns(2)
        with p_c1:
            if st.button("✅ Approve Proposal", key="app_prop", use_container_width=True):
                df.at[selected_proposal_idx, 'qa_status'] = 'approved'
                df.at[selected_proposal_idx, 'qa_stage'] = 'preview'
                os.makedirs(os.path.dirname(calendar_path), exist_ok=True)
                df.to_csv(calendar_path, index=False)
                st.success("Moved to Preview Stage!")
                st.rerun()
        with p_c2:
            if st.button("❌ Reject Proposal", key="rej_prop", use_container_width=True):
                df.at[selected_proposal_idx, 'qa_status'] = 'rejected'
                os.makedirs(os.path.dirname(calendar_path), exist_ok=True)
                df.to_csv(calendar_path, index=False)
                st.error("Proposal Rejected!")
                st.rerun()

        if st.button("⚡ Approve All Proposals", use_container_width=True):
            df.loc[df['qa_stage'] == 'proposal', 'qa_status'] = 'approved'
            df.loc[df['qa_stage'] == 'proposal', 'qa_stage'] = 'preview'
            os.makedirs(os.path.dirname(calendar_path), exist_ok=True)
            df.to_csv(calendar_path, index=False)
            st.success("All proposals moved to Preview!")
            st.rerun()
    else:
        st.write("No pending proposals.")

    st.divider()

    # Preview Approval (Stage 2)
    st.markdown("#### 🎨 Stage 2: Visual Asset Preview")
    preview_df = df[(df['qa_stage'] == 'preview') & (df['production_status'] == 'ready')]
    if not preview_df.empty:
        selected_preview_idx = st.selectbox("Select asset to preview", options=preview_df.index, format_func=lambda x: f"Row {x}: {df.iloc[x]['concept']}")

        preview_row = df.iloc[selected_preview_idx]

        # SMARTPHONE MOCKUP
        full_img_path = os.path.join(paths["base"], preview_row['image_path']) if not os.path.isabs(preview_row['image_path']) else preview_row['image_path']

        st.markdown(f"""
            <div class="phone-container">
                <div class="phone-notch"></div>
                <div class="phone-screen">
                    <div class="phone-ui-header">
                        <div class="phone-profile-pic"></div>
                        <strong>{active_creator.capitalize()}</strong>
                    </div>
                    <img src="https://via.placeholder.com/300x400?text=Asset+Preview" class="phone-image">
                    <div class="phone-ui">
                        <div class="phone-ui-footer">
                            <span>❤️</span> <span>💬</span> <span>✈️</span>
                        </div>
                        <p><strong>{active_creator}</strong> {preview_row['caption']}</p>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        # Note: Streamlit doesn't allow direct local file paths in HTML <img> for security.
        # To fix this properly, we would use st.image, but to keep the mockup we use a placeholder
        # or the user can implement a base64 encoder. For this implementation, the CSS structure is provided.
        st.image(full_img_path, width=300, caption="Actual Asset File")

        v_c1, v_c2 = st.columns(2)
        with v_c1:
            if st.button("✅ Final Approval", key="app_prev", use_container_width=True):
                df.at[selected_preview_idx, 'qa_stage'] = 'final'
                os.makedirs(os.path.dirname(calendar_path), exist_ok=True)
                df.to_csv(calendar_path, index=False)
                st.success("Final Approval Granted!")
                st.rerun()
        with v_c2:
            if st.button("❌ Request Redo", key="rej_prev", use_container_width=True):
                df.at[selected_preview_idx, 'production_status'] = 'pending'
                os.makedirs(os.path.dirname(calendar_path), exist_ok=True)
                df.to_csv(calendar_path, index=False)
                st.warning("Asset sent back to production.")
                st.rerun()
    else:
        st.write("No assets ready for preview.")

# --- TAB 2: STUDIO ASSET ---
with tab_studio:
    st.subheader("Visual Asset Production")

    if st.button("🚀 Generate All Ready Assets", use_container_width=True):
        with st.spinner(f"Generating assets for {active_creator}..."):
            env = os.environ.copy()
            env["GEMINI_API_KEY"] = gemini_api_key
            result = subprocess.run(['python', 'asset_generator.py', '--creator', active_creator], capture_output=True, text=True, env=env)
            if result.returncode == 0:
                st.success("Assets generated successfully!")
                st.rerun()
            else:
                st.error(f"Generation Error: {result.stderr}")

    st.divider()

    # LIVE SYSTEM LOG
    st.markdown("### 📜 Generation Log")
    log_path = paths["log"]
    if os.path.exists(log_path):
        if st.button("🔄 Refresh Log"):
            st.rerun()
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            last_lines = "".join(lines[-15:])
            st.code(last_lines if last_lines else "Log is empty.")
    else:
        st.info("No generation log available yet.")

    st.divider()

    gallery_cols = st.columns(3)
    asset_idx = 0
    for idx, row in df.iterrows():
        if pd.notna(row['image_path']) and row['image_path'] != "":
            with gallery_cols[asset_idx % 3]:
                fmt = str(row['format']).lower()
                path_val = row['image_path']

                full_path = os.path.join(paths["base"], path_val) if not os.path.isabs(path_val) else path_val

                with st.expander(f"📦 {row['concept']}", expanded=True):
                    if fmt == 'carousel':
                        paths_list = path_val.split(',')
                        st.caption("Carousel Sequence")
                        c_slides = st.columns(len(paths_list))
                        for i, p in enumerate(paths_list):
                            f_p = os.path.join(paths["base"], p)
                            if os.path.exists(f_p):
                                c_slides[i].image(f_p, use_container_width=True)
                    elif fmt == 'short_video':
                        st.caption("Short-form Video")
                        if os.path.exists(full_path):
                            st.video(full_path)
                    else:
                        st.caption("Single Asset")
                        if os.path.exists(full_path):
                            st.image(full_path, use_container_width=True)
                asset_idx += 1

# --- TAB 3: CODA DI PUBBLICAZIONE ---
with tab_publish:
    st.subheader("Publishing Control Center")

    ready_to_publish = df[(df['qa_stage'] == 'final') & (df['production_status'] == 'ready') & (df['publish_status'] == 'draft')]

    if not ready_to_publish.empty:
        st.markdown("### 📤 Ready to Push")
        st.table(ready_to_publish[['date', 'concept', 'format', 'image_path']])

        p_col1, p_col2, p_col3 = st.columns(3)
        with p_col1:
            if st.button("🚀 Avvia Pubblicazione Schedulata", use_container_width=True):
                with st.spinner("Pushing to platforms..."):
                    result = subprocess.run(['python', 'publisher.py', '--creator', active_creator], capture_output=True, text=True)
                    st.text(result.stdout)
                    if result.returncode == 0:
                        st.success("Published!")
                        st.rerun()
        with p_col2:
            if st.button("⚡ Forza Pubblicazione Immediata", use_container_width=True):
                with st.spinner("Forcing all ready assets..."):
                    result = subprocess.run(['python', 'publisher.py', '--force', '--creator', active_creator], capture_output=True, text=True)
                    st.text(result.stdout)
                    if result.returncode == 0:
                        st.success("Forced publication complete!")
                    st.rerun()
        with p_col3:
            # EXTERNAL EXPORT
            if st.button("📥 Export for Scheduler", use_container_width=True):
                export_df = ready_to_publish[['date', 'caption', 'image_path', 'funnel_stage']]
                export_filename = f"export_{active_creator}_scheduler.csv"
                export_df.to_csv(export_filename, index=False)
                st.success(f"Exported to {export_filename}!")
                with open(export_filename, "rb") as file:
                    st.download_button("Download CSV", data=file, file_name=export_filename, mime="text/csv")
    else:
        st.info("The queue is currently empty. Finalize the QA process for more posts.")
