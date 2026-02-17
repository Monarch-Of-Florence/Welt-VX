import streamlit as st
import os
import time
from dotenv import load_dotenv
import weltengine 

# --- SETUP ---
load_dotenv()
APP_VERSION = "v2.0.0" # Updated Version

st.set_page_config(page_title=f"Welt VX {APP_VERSION}", page_icon="welt_icon.png", layout="wide")

# --- CUSTOM CSS (PRESERVED FROM v1.5.0) ---
def apply_studio_style():
    st.markdown("""
        <style>
            .stApp { background-color: #0e0e0e; color: #e5e5e5; }
            
            /* --- 1. ALERT BLOCKS --- */
            div[data-testid="stAlert"] {
                background-color: #082a10 !important;
                border: 1px solid #1a5c20 !important;
                border-left: 5px solid #46d369 !important;
                color: #ffffff !important;
                border-radius: 8px;
            }
            div[data-testid="stAlert"] > div, div[data-testid="stAlert"] p { color: #ffffff !important; }
            div[data-testid="stAlert"] svg { fill: #46d369 !important; color: #46d369 !important; }

            /* --- 2. INPUT FOCUS --- */
            input:focus, textarea:focus, div[data-baseweb="select"] > div:focus-within {
                border-color: #46d369 !important;
                box-shadow: 0 0 0 1px #46d369 !important;
            }

            /* --- 3. UI ELEMENTS --- */
            .control-deck {
                background-color: #161616;
                padding: 15px;
                border-radius: 12px;
                border: 1px solid #333;
                margin-top: 10px;
            }
            div[data-testid="stButton"] button {
                border-radius: 8px;
                font-weight: 600;
                border: 1px solid #333;
                background-color: #1a1a1a;
                color: white;
                transition: all 0.2s;
            }
            div[data-testid="stButton"] button:hover {
                border-color: #46d369;
                color: #46d369;
                background-color: #0d1f0d;
            }
            
            /* Primary Button (Netflix Red / Green Logic) */
            div[data-testid="stButton"] button[kind="primary"] {
                background-color: #E50914; 
                border-color: #E50914;
                color: white;
            }
            div[data-testid="stButton"] button[kind="primary"]:hover {
                background-color: #b00610;
                border-color: #b00610;
            }
            
            /* --- 4. MATERIAL ICONS --- */
            span[data-testid="stIconMaterial"] { color: inherit !important; }
            
            /* Link Styling */
            a.policy-link { color: #46d369 !important; text-decoration: underline !important; font-weight: bold; }
            
            /* Video Player Styling */
            [data-testid="stVideo"] { 
                border-radius: 12px; 
                border: 1px solid #1a1a1a; 
                box-shadow: 0px 5px 30px rgba(70, 211, 105, 0.15); 
            }
            
            /* Spinner */
            .stSpinner > div { border-top-color: #E50914 !important; }
        </style>
    """, unsafe_allow_html=True)

apply_studio_style()

# --- SESSION STATE ---
if "messages" not in st.session_state: st.session_state.messages = []
if "chapters" not in st.session_state: st.session_state.chapters = []
if "video_start_time" not in st.session_state: st.session_state.video_start_time = 0
if "show_assistant" not in st.session_state: st.session_state.show_assistant = False 
if "last_video_id" not in st.session_state: st.session_state.last_video_id = ""
if "form_reset_id" not in st.session_state: st.session_state.form_reset_id = 0 
if "input_mode" not in st.session_state: st.session_state.input_mode = "normal" 
if "safety_settings" not in st.session_state:
    st.session_state.safety_settings = {"nsfw": False, "gore": False, "profanity": False}
if "active_video_library" not in st.session_state: st.session_state.active_video_library = [] 

# --- SIDEBAR: CONFIGURATION (New in v2.0) ---
def setup_sidebar():
    with st.sidebar:
        st.image("welt_icon.png", width=50) 
        st.header("Welt VX Settings")
        
        # Section 1: User Account / API Key
        with st.expander("👤 Account & API", expanded=True):
            api_mode = st.radio(
                "API Source",
                ["Use Free Tier (Shared)", "Use My Own Key (Paid/Private)"],
                index=0
            )
            
            final_key = None
            sel_model = "gemini-3.0-flash-preview" # Updated Default

            if api_mode == "Use My Own Key (Paid/Private)":
                user_key_input = st.text_input(
                    "Enter Google AI Studio Key",
                    type="password",
                    help="Your key is not stored permanently."
                )
                if user_key_input:
                    final_key = user_key_input
                
                # UPDATED MODEL SELECTION
                sel_model = st.selectbox(
                    "Select Model",
                    [
                        "gemini-2.5-flash",
                        "gemini-2.5-pro", 
                        "gemini-3.0-flash-preview", 
                        "gemini-3.0-pro-preview"
                    ],
                    index=2 # Default to 3.0 Flash Preview
                )
            else:
                try:
                    final_key = st.secrets["GEMINI_API_KEY"]
                except:
                    st.error("No Shared Key Found in Secrets.")
                
                st.info("Using shared free tier (Gemini 3.0 Flash Preview).")

        # Section 2: Content Filters
        with st.expander("🛡️ Safety & Filters"):
            st.caption("Welt VX uses standard safety filters by default.")
            
            age_verified = st.checkbox("I confirm I am 18+ and want to view unfiltered content.")
            
            disable_safety = False
            if age_verified:
                disable_safety = st.toggle("Disable NSFW Safety Filters", value=False)
                if disable_safety:
                    st.warning("⚠️ Filters Disabled. Proceed at your own risk.")
                    st.session_state.safety_settings["nsfw"] = True
                else:
                    st.session_state.safety_settings["nsfw"] = False
            else:
                st.session_state.safety_settings["nsfw"] = False

        return final_key, sel_model

# Initialize Sidebar
api_key, selected_model_id = setup_sidebar()

if not api_key:
    st.warning("Please configure an API Key in the Sidebar.")
    st.stop()

# --- MODAL 1: SUBTITLE STUDIO ---
@st.dialog("Subtitle Generator")
def open_subtitle_window(current_video_path):
    st.caption("Configure generation settings")
    c1, c2 = st.columns([2, 1])
    with c1:
        lang = st.selectbox("Target Language", ["English", "Hindi", "Japanese", "Spanish", "German"])
    with c2:
        st.write("") 
        st.write("") 
        sfx = st.checkbox("Include SFX", value=False, help="Include [Context] and [Sound Effects]")
    
    st.divider()
    
    if st.button(":material/bolt: Generate Subtitles", type="primary", use_container_width=True):
        if current_video_path:
            with st.spinner(f"Initializing Agent ({selected_model_id})..."):
                res = weltengine.generate_subtitles_backend(
                    api_key, 
                    current_video_path, 
                    lang, 
                    sfx, 
                    user_filters=st.session_state.safety_settings,
                    model_id=selected_model_id 
                )
                final_srt = weltengine.clean_and_repair_srt(res)
                with open("subtitles.srt", "w", encoding="utf-8") as f: f.write(final_srt)
                st.rerun()
        else:
            st.error("Video source not found.")

# --- MAIN APP LOGIC ---
st.title("Welt VX")
st.caption(f"Redefine Viewer Experience with Relative Video Intelligence • {APP_VERSION}")
st.subheader("Studio")

MASTER_DEMO_PATH = "master_demo.webm" 

# UPDATED: Multi-File Uploader
uploaded_files = st.file_uploader(
    "Upload Video Context", 
    type=["mp4", "mov", "avi", "webm"],
    help="Upload one or multiple videos for cross-context reasoning.", 
    label_visibility="collapsed",
    accept_multiple_files=True
)

use_demo = False
if not uploaded_files and os.path.exists(MASTER_DEMO_PATH):
    use_demo = st.checkbox("Or use the pre-loaded Demo Video")

start_processing = False
new_upload_signature = ""

# Handle File Processing
if uploaded_files:
    new_upload_signature = "_".join([f.name for f in uploaded_files])
    
    if new_upload_signature != st.session_state.last_video_id:
        st.session_state.active_video_library = [] 
        
        for idx, u_file in enumerate(uploaded_files):
            temp_name = f"temp_video_{idx}.mp4"
            with open(temp_name, "wb") as f: f.write(u_file.getbuffer())
            st.session_state.active_video_library.append(temp_name)
        
        start_processing = True

elif use_demo:
    new_upload_signature = "Demo_Video_Master"
    if new_upload_signature != st.session_state.last_video_id:
        st.session_state.active_video_library = [MASTER_DEMO_PATH]
        start_processing = True

if start_processing:
    if os.path.exists("subtitles.srt"): os.remove("subtitles.srt")
    st.session_state.messages = []
    st.session_state.chapters = []
    st.session_state.video_start_time = 0
    st.session_state.last_video_id = new_upload_signature
    st.session_state.input_mode = "normal" 
    st.rerun()

# --- LAYOUT ---
if st.session_state.active_video_library:
    
    # NEW: Selector if multiple videos exist
    current_view_path = st.session_state.active_video_library[0]
    if len(st.session_state.active_video_library) > 1:
        st.info(f"📂 Relative Context Active: {len(st.session_state.active_video_library)} Videos Loaded.")
        selected_idx = st.selectbox(
            "Select Video to View/Analyze", 
            range(len(st.session_state.active_video_library)),
            format_func=lambda x: f"Video {x+1}"
        )
        current_view_path = st.session_state.active_video_library[selected_idx]

    if st.session_state.show_assistant:
        col_video, col_assist = st.columns([2.5, 1.2]) 
    else:
        col_video, col_assist = st.columns([1, 0.001]) 

    # --- LEFT COLUMN (Player & Controls) ---
    with col_video:
        subs = "subtitles.srt" if os.path.exists("subtitles.srt") else None
        st.video(current_view_path, subtitles=subs, start_time=st.session_state.video_start_time)

        with st.container(border=True):
            c1, c2, c3 = st.columns(3) 
            
            with c1:
                if st.button(":material/subtitles: Subtitles", use_container_width=True):
                    open_subtitle_window(current_view_path)
            
            with c2:
                if st.button(":material/segment: Smart Chapters", use_container_width=True):
                    with st.spinner("Analyzing Narrative Arc..."):
                        st.session_state.chapters = weltengine.generate_smart_chapters(
                            api_key, 
                            current_view_path, 
                            model_id=selected_model_id
                        )
                        st.rerun()
            
            with c3:
                label = ":material/close: Close Assistant" if st.session_state.show_assistant else ":material/smart_toy: VX Assistant"
                type_color = "secondary" if st.session_state.show_assistant else "primary"
                if st.button(label, type=type_color, use_container_width=True):
                    st.session_state.show_assistant = not st.session_state.show_assistant
                    st.rerun()

        if st.session_state.chapters:
            st.markdown("#### :material/menu_book: Chapters") 
            with st.container(height=200):
                for ts, title in st.session_state.chapters:
                    if st.button(f"{ts} - {title}", key=ts, use_container_width=True):
                        try:
                            parts = [int(p.strip()) for p in ts.split(":") if p.strip().isdigit()]
                            
                            if len(parts) == 3: # HH:MM:SS
                                sec = parts[0]*3600 + parts[1]*60 + parts[2]
                            elif len(parts) == 2: # MM:SS
                                sec = parts[0]*60 + parts[1]
                            else:
                                sec = 0
                            
                            st.session_state.video_start_time = sec
                            st.rerun()
                        except (ValueError, IndexError):
                            st.toast(f"⚠️ Formatting error in timestamp: {ts}", icon="⚠️")

    # --- RIGHT COLUMN (VX Assistant) ---
    if st.session_state.show_assistant:
        with col_assist:
            h1, h2 = st.columns([3, 1])
            with h1: st.markdown("#### Assistant")
            with h2: 
                if st.button(":material/delete:", help="Clear Chat"):
                    st.session_state.messages = []
                    st.session_state.input_mode = "normal" 
                    st.rerun()
            
            chat_box = st.container(height=500)
            
            if not st.session_state.messages and st.session_state.input_mode == "normal":
                with chat_box:
                    st.info(f"I am analyzing {len(st.session_state.active_video_library)} video(s) using {selected_model_id}.")
                    
                    sc1, sc2 = st.columns(2)
                    with sc1:
                        if st.button(":material/search: Jump to Part", use_container_width=True):
                            st.session_state.input_mode = "jump_to_part"
                            st.rerun()
                    with sc2:
                        if st.button(":material/security: Safety Scan", use_container_width=True):
                            st.session_state.input_mode = "safety_scan"
                            st.rerun()
                    
                    sc3, sc4 = st.columns(2)
                    with sc3:
                         if st.button("Video Summary", use_container_width=True):
                            st.session_state.messages.append({"role": "user", "content": "Summarize the video context."})
                            st.rerun()
                    with sc4:
                         if st.button(":material/build: Fix Subs", use_container_width=True):
                            st.session_state.input_mode = "repair_subs"
                            st.rerun()
            else:
                 with chat_box:
                    for msg in st.session_state.messages:
                        with st.chat_message(msg["role"]): st.markdown(msg["content"])
            
            if st.session_state.input_mode == "safety_scan":
                scan_query = st.chat_input("What content should I detect? (e.g. Weapons, Brands)", key="scan_input")
                if scan_query:
                    full_prompt = f"Scan the video specifically for: {scan_query}. Provide timestamps if found."
                    st.session_state.messages.append({"role": "user", "content": full_prompt})
                    st.session_state.input_mode = "normal" 
                    st.rerun()
                    
            elif st.session_state.input_mode == "repair_subs":
                repair_query = st.chat_input("Describe the issue (e.g. 'Fix spelling in intro' or 'Change 00:10 to Hello')", key="repair_input")
                if repair_query:
                    full_prompt = f"Fix Subtitles: {repair_query}"
                    st.session_state.messages.append({"role": "user", "content": full_prompt})
                    st.session_state.input_mode = "normal" 
                    st.rerun()
            
            elif st.session_state.input_mode == "jump_to_part":
                jump_query = st.chat_input("Where do you want to go? (e.g. 'The explosion scene', 'When they meet')", key="jump_input")
                if jump_query:
                    full_prompt = f"Jump to timestamp: {jump_query}"
                    st.session_state.messages.append({"role": "user", "content": full_prompt})
                    st.session_state.input_mode = "normal"
                    st.rerun()
                    
            else:
                if prompt := st.chat_input("Ask Welt..."):
                    st.session_state.messages.append({"role": "user", "content": prompt})
                    st.rerun()

            if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
                 with chat_box:
                    with st.chat_message("assistant"):
                        with st.spinner(f"Thinking ({selected_model_id})..."):
                            current_srt = ""
                            if os.path.exists("subtitles.srt"):
                                with open("subtitles.srt", "r", encoding="utf-8") as f: current_srt = f.read()
                            
                            last_user_msg = st.session_state.messages[-1]["content"]
                            
                            response = weltengine.vx_assistant_fix(
                                api_key, 
                                st.session_state.active_video_library, 
                                current_srt, 
                                st.session_state.chapters, 
                                last_user_msg, 
                                user_filters=st.session_state.safety_settings,
                                model_id=selected_model_id 
                            )
                            
                            final_msg = ""
                            if response.startswith("PATCH:"):
                                with open("subtitles.srt", "w", encoding="utf-8") as f: 
                                    f.write(weltengine.clean_and_repair_srt(response))
                                final_msg = "✅ Subtitles patched based on your feedback."
                            
                            elif response.startswith("CHAPTERS:"):
                                lines = response.replace("CHAPTERS:", "").strip().split('\n')
                                st.session_state.chapters = [tuple(l.split(" - ", 1)) for l in lines if " - " in l]
                                final_msg = "✅ Smart Chapters updated."
                            
                            elif response.startswith("SEEK:"):
                                try:
                                    raw = response.replace("SEEK:", "").strip()
                                    parts = raw.split(" ", 1)
                                    ts = parts[0].strip().replace("[", "").replace("]", "")
                                    desc = parts[1] if len(parts) > 1 else "Jumping..."
                                    
                                    t_parts = ts.split(":")
                                    if len(t_parts) == 3: sec = int(t_parts[0])*3600 + int(t_parts[1])*60 + int(t_parts[2])
                                    elif len(t_parts) == 2: sec = int(t_parts[0])*60 + int(t_parts[1])
                                    else: sec = 0
                                    
                                    st.session_state.video_start_time = sec
                                    final_msg = f"🎥 **Jumped to {ts}**: {desc}"
                                    
                                    st.session_state.messages.append({"role": "assistant", "content": final_msg})
                                    st.rerun()
                                    
                                except Exception: 
                                    final_msg = "⚠️ Seek failed."
                            
                            else:
                                final_msg = response.replace("ANSWER:", "").strip()
                
                 st.session_state.messages.append({"role": "assistant", "content": final_msg})
                 st.rerun()