import streamlit as st
import os
import time
from dotenv import load_dotenv
import weltengine 
import json # --- Added for v3.0.0 (Librarian parsing) ---

# --- SETUP ---
load_dotenv()
APP_VERSION = "v3.0.0" # Updated to v3.0.0

st.set_page_config(page_title=f"Welt VX {APP_VERSION}", page_icon="welt_icon.png", layout="wide")

# --- 1. IP PROTECTION (PASSWORD GATE) (Added in v3.0.0) ---
def check_password():
    """Returns `True` if the user had the correct password."""
    def password_entered():
        if st.session_state["password"] == st.secrets.get("APP_PASSWORD", "WeltVX_2026"):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Enter Hackathon Access Code", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Enter Hackathon Access Code", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    else:
        return True

if not check_password():
    st.stop()

# --- CUSTOM CSS (Strictly Preserved + Additive Theme Support) ---
def apply_studio_style(theme="Dark Mode"):
    # Determine Colors (Additive for v3.0.0 Theme toggle)
    if theme == "Dark Mode":
        c_bg, c_txt, c_card, c_brd, c_pop_bg, c_pop_txt = "#0e0e0e", "#e5e5e5", "#161616", "#333", "#161616", "#ffffff"
    else:
        c_bg, c_txt, c_card, c_brd, c_pop_bg, c_pop_txt = "#f5f5dc", "#4b3621", "#faf0e6", "#d2b48c", "#faf0e6", "#4b3621"

    st.markdown(f"""
        <style>
            .stApp {{ background-color: {c_bg} !important; color: {c_txt} !important; }}
            p, h1, h2, h3, h4, h5, h6, span, label, div {{ color: {c_txt}; }}
            
            /* --- 1. ALERT BLOCKS --- */
            div[data-testid="stAlert"] {{
                background-color: #082a10 !important;
                border: 1px solid #1a5c20 !important;
                border-left: 5px solid #46d369 !important;
                color: #ffffff !important;
                border-radius: 8px;
            }}
            div[data-testid="stAlert"] > div, div[data-testid="stAlert"] p {{ color: #ffffff !important; }}
            div[data-testid="stAlert"] svg {{ fill: #46d369 !important; color: #46d369 !important; }}

            /* --- 2. INPUT FOCUS --- */
            input:focus, textarea:focus, div[data-baseweb="select"] > div:focus-within {{
                border-color: #46d369 !important;
                box-shadow: 0 0 0 1px #46d369 !important;
            }}
            input, textarea, .stSelectbox {{ color: {c_txt} !important; background-color: {c_card} !important; border-color: {c_brd} !important; }}

            /* --- CRITICAL FIX: OPAQUE DROPDOWNS (Added in v3.0.0) --- */
            div[data-baseweb="popover"], div[data-baseweb="menu"] {{ 
                background-color: {c_pop_bg} !important; 
                border: 1px solid {c_brd} !important; 
                color: {c_pop_txt} !important; 
                opacity: 1 !important; 
            }}
            div[data-baseweb="option"] {{ color: {c_pop_txt} !important; background-color: {c_pop_bg} !important; }}

            /* --- 3. UI ELEMENTS --- */
            .control-deck {{
                background-color: {c_card};
                padding: 15px;
                border-radius: 12px;
                border: 1px solid {c_brd};
                margin-top: 10px;
            }}
            div[data-testid="stButton"] button {{
                border-radius: 8px;
                font-weight: 600;
                border: 1px solid {c_brd};
                background-color: {c_card};
                color: {c_txt} !important;
                transition: all 0.2s;
            }}
            div[data-testid="stButton"] button:hover {{
                border-color: #46d369;
                color: #46d369 !important;
                background-color: #0d1f0d !important;
            }}
            
            /* Primary Button (Netflix Red / Green Logic) */
            div[data-testid="stButton"] button[kind="primary"] {{
                background-color: #E50914 !important; 
                border-color: #E50914 !important;
                color: white !important;
            }}
            div[data-testid="stButton"] button[kind="primary"]:hover {{
                background-color: #b00610 !important;
                border-color: #b00610 !important;
            }}
            
            /* --- 4. MATERIAL ICONS --- */
            span[data-testid="stIconMaterial"] {{ color: inherit !important; }}
            
            /* Link Styling */
            a.policy-link {{ color: #46d369 !important; text-decoration: underline !important; font-weight: bold; }}
            
            /* Video Player Styling */
            [data-testid="stVideo"] {{ 
                border-radius: 12px; 
                border: 1px solid {c_brd}; 
                box-shadow: 0px 5px 30px rgba(70, 211, 105, 0.15); 
            }}
            
            /* Spinner */
            .stSpinner > div {{ border-top-color: #E50914 !important; }}
        </style>
    """, unsafe_allow_html=True)


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

# --- NEW SESSION STATE VARIABLES (v3.0.0) ---
if "is_processing" not in st.session_state: st.session_state.is_processing = False
if "theme_mode" not in st.session_state: st.session_state.theme_mode = "Dark Mode"
if "video_display_names" not in st.session_state: st.session_state.video_display_names = {}

# Apply dynamic styling based on state
apply_studio_style(st.session_state.theme_mode)

# --- SIDEBAR: CONFIGURATION (Minimalist & Filters Restored) ---
def setup_sidebar():
    with st.sidebar:
        st.image("welt_icon.png", width=50) 
        st.header("Welt VX Settings")

        # Added for v3.0.0 - Theme Toggle
        st.session_state.theme_mode = st.radio(
            "Interface Theme", 
            ["Dark Mode", "Light Mode"], 
            horizontal=True, 
            disabled=st.session_state.is_processing
        )
        
        # Section 1: User Account
        with st.expander("Account & API", expanded=True):
            api_mode = st.radio(
                "API Source",
                ["Use Free Tier (Shared)", "Use My Own Key (Paid/Private)"],
                index=0,
                disabled=st.session_state.is_processing
            )
            
            final_key = None
            sel_model = "gemini-3-flash-preview" # Default

            if api_mode == "Use My Own Key (Paid/Private)":
                user_key_input = st.text_input(
                    "Enter Google AI Studio Key",
                    type="password",
                    help="Your key is not stored permanently.",
                    disabled=st.session_state.is_processing
                )
                if user_key_input:
                    final_key = user_key_input
                
                sel_model = st.selectbox(
                    "Select Model",
                    [
                        "gemini-2.5-flash",
                        "gemini-2.5-pro", 
                        "gemini-3-flash-preview", 
                        "gemini-3-pro-preview"
                    ],
                    index=2, # Default to 3 Flash Preview
                    disabled=st.session_state.is_processing
                )
            else:
                try:
                    final_key = st.secrets["GEMINI_API_KEY"]
                except:
                    st.error("No Shared Key Found in Secrets.")
                
                st.info("Using shared free tier (Gemini 3 Flash Preview).")

        # Section 2: Content Filters (All 3 Restored)
        with st.expander("Safety & Filters"):
            st.caption("Welt VX uses standard safety filters by default.")
            
            # The "Self-Attestation" Check
            age_verified = st.checkbox("I confirm I am 18+ and want to view unfiltered content.", disabled=st.session_state.is_processing)
            
            if age_verified:
                st.session_state.safety_settings["nsfw"] = st.checkbox("Allow NSFW (18+)", value=st.session_state.safety_settings["nsfw"], disabled=st.session_state.is_processing)
                st.session_state.safety_settings["gore"] = st.checkbox("Allow Gore/Violence", value=st.session_state.safety_settings["gore"], disabled=st.session_state.is_processing)
                st.session_state.safety_settings["profanity"] = st.checkbox("Allow Profanity", value=st.session_state.safety_settings["profanity"], disabled=st.session_state.is_processing)
            else:
                # Reset if unchecked
                st.session_state.safety_settings["nsfw"] = False
                st.session_state.safety_settings["gore"] = False
                st.session_state.safety_settings["profanity"] = False

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
        lang = st.selectbox("Target Language", ["English", "Hindi", "Japanese", "Spanish", "German"], disabled=st.session_state.is_processing)
    with c2:
        st.write("") 
        st.write("") 
        sfx = st.checkbox("Include SFX", value=False, help="Include [Context] and [Sound Effects]", disabled=st.session_state.is_processing)
    
    st.divider()
    
    if st.button(":material/bolt: Generate Subtitles", type="primary", use_container_width=True, disabled=st.session_state.is_processing):
        if current_video_path:
            st.session_state.is_processing = True # Lock State
            with st.spinner(f"Initializing Scribe Agent ({selected_model_id})..."):
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
            st.session_state.is_processing = False # Unlock State
            st.rerun()
        else:
            st.error("Video source not found.")

# --- MAIN APP LOGIC ---
st.title("Welt VX")
st.caption(f"Redefine Viewer Experience with Relative Video Intelligence • {APP_VERSION}")
st.subheader("Studio")

MASTER_DEMO_PATH = "master_demo.webm" 

uploaded_files = st.file_uploader(
    "Upload Video Context", 
    type=["mp4", "mov", "avi", "webm"],
    help="Upload one or multiple videos for cross-context reasoning.", 
    label_visibility="collapsed",
    accept_multiple_files=True,
    disabled=st.session_state.is_processing
)

# --- LOCAL FILE MODE FALLBACK (Added in v3.0.0) ---
local_mode = st.toggle("Enable Local Path Mode (Bypass 200MB Upload Limit)", disabled=st.session_state.is_processing)
local_path_input = ""
if local_mode:
    local_path_input = st.text_input("Enter absolute file path (e.g. C:/Videos/evidence.mp4)", disabled=st.session_state.is_processing)

use_demo = False
if not uploaded_files and not local_path_input and os.path.exists(MASTER_DEMO_PATH):
    use_demo = st.checkbox("Or use the pre-loaded Demo Video", disabled=st.session_state.is_processing)

start_processing = False
new_upload_signature = ""

# Handle File Processing
if uploaded_files:
    new_upload_signature = "_".join([f.name for f in uploaded_files])
    
    if new_upload_signature != st.session_state.last_video_id:
        st.session_state.active_video_library = [] 
        st.session_state.video_display_names = {} # Reset Librarian Names
        
        for idx, u_file in enumerate(uploaded_files):
            temp_name = f"temp_video_{idx}.mp4"
            with open(temp_name, "wb") as f: f.write(u_file.getbuffer())
            st.session_state.active_video_library.append(temp_name)
            st.session_state.video_display_names[temp_name] = u_file.name # Additive mapping
        
        start_processing = True

elif local_path_input:
    new_upload_signature = local_path_input
    if new_upload_signature != st.session_state.last_video_id:
        st.session_state.active_video_library = [local_path_input]
        st.session_state.video_display_names = {local_path_input: "Local Evidence File"}
        start_processing = True

elif use_demo:
    new_upload_signature = "Demo_Video_Master"
    if new_upload_signature != st.session_state.last_video_id:
        st.session_state.active_video_library = [MASTER_DEMO_PATH]
        st.session_state.video_display_names = {MASTER_DEMO_PATH: "Master Demo"}
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
    
    current_view_path = st.session_state.active_video_library[0]
    if len(st.session_state.active_video_library) > 1:
        st.info(f"📂 Relative Context Active: {len(st.session_state.active_video_library)} Videos Loaded.")
        selected_idx = st.selectbox(
            "Select Video to View/Analyze", 
            range(len(st.session_state.active_video_library)),
            format_func=lambda x: st.session_state.video_display_names.get(st.session_state.active_video_library[x], f"Video {x+1}"),
            disabled=st.session_state.is_processing
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
                if st.button(":material/subtitles: Subtitles", use_container_width=True, disabled=st.session_state.is_processing):
                    open_subtitle_window(current_view_path)
            
            with c2:
                if st.button(":material/segment: Smart Chapters", use_container_width=True, disabled=st.session_state.is_processing):
                    st.session_state.is_processing = True # Lock
                    with st.spinner("Architect Analyzing Narrative Arc..."):
                        st.session_state.chapters = weltengine.generate_smart_chapters(
                            api_key, 
                            current_view_path, 
                            model_id=selected_model_id
                        )
                    st.session_state.is_processing = False # Unlock
                    st.rerun()
            
            with c3:
                label = ":material/close: Close Assistant" if st.session_state.show_assistant else ":material/smart_toy: VX Assistant"
                type_color = "secondary" if st.session_state.show_assistant else "primary"
                if st.button(label, type=type_color, use_container_width=True, disabled=st.session_state.is_processing):
                    st.session_state.show_assistant = not st.session_state.show_assistant
                    st.rerun()

        if st.session_state.chapters:
            st.markdown("#### :material/menu_book: Chapters") 
            with st.container(height=200):
                for ts, title in st.session_state.chapters:
                    if st.button(f"{ts} - {title}", key=ts, use_container_width=True, disabled=st.session_state.is_processing):
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
                if st.button(":material/delete:", help="Clear Chat", disabled=st.session_state.is_processing):
                    st.session_state.messages = []
                    st.session_state.input_mode = "normal" 
                    st.rerun()
            
            chat_box = st.container(height=500)
            
            if not st.session_state.messages and st.session_state.input_mode == "normal":
                with chat_box:
                    st.info(f"Orchestrator online. Analyzing {len(st.session_state.active_video_library)} video(s) using {selected_model_id}.")
                    
                    sc1, sc2 = st.columns(2)
                    with sc1:
                        if st.button(":material/search: Jump to Part", use_container_width=True, disabled=st.session_state.is_processing):
                            st.session_state.input_mode = "jump_to_part"
                            st.rerun()
                    with sc2:
                        if st.button(":material/security: Safety Scan", use_container_width=True, disabled=st.session_state.is_processing):
                            st.session_state.input_mode = "safety_scan"
                            st.rerun()
                    
                    sc3, sc4 = st.columns(2)
                    with sc3:
                         if st.button("Video Summary", use_container_width=True, disabled=st.session_state.is_processing):
                            st.session_state.messages.append({"role": "user", "content": "Summarize the video"})
                            st.rerun()
                    with sc4:
                         if st.button(":material/build: Fix Subs", use_container_width=True, disabled=st.session_state.is_processing):
                            st.session_state.input_mode = "repair_subs"
                            st.rerun()
                    
                    # Additive Chip for v3.0.0
                    if len(st.session_state.active_video_library) > 1:
                        if st.button("🏷️ Auto-Label Videos", use_container_width=True, disabled=st.session_state.is_processing):
                            st.session_state.messages.append({"role": "user", "content": "Auto-label and rename these videos based on their content."})
                            st.rerun()
            else:
                 with chat_box:
                    for msg in st.session_state.messages:
                        with st.chat_message(msg["role"]): st.markdown(msg["content"])
            
            if st.session_state.input_mode == "safety_scan":
                scan_query = st.chat_input("What content should I detect? (e.g. Weapons, Brands)", key="scan_input", disabled=st.session_state.is_processing)
                if scan_query:
                    full_prompt = f"Scan the video specifically for: {scan_query}. Provide timestamps if found."
                    st.session_state.messages.append({"role": "user", "content": full_prompt})
                    st.session_state.input_mode = "normal" 
                    st.rerun()
                    
            elif st.session_state.input_mode == "repair_subs":
                repair_query = st.chat_input("Describe the issue (e.g. 'Fix spelling in intro')", key="repair_input", disabled=st.session_state.is_processing)
                if repair_query:
                    full_prompt = f"Fix Subtitles: {repair_query}"
                    st.session_state.messages.append({"role": "user", "content": full_prompt})
                    st.session_state.input_mode = "normal" 
                    st.rerun()
            
            elif st.session_state.input_mode == "jump_to_part":
                jump_query = st.chat_input("Where do you want to go? (e.g. 'The explosion scene')", key="jump_input", disabled=st.session_state.is_processing)
                if jump_query:
                    full_prompt = f"Jump to timestamp: {jump_query}"
                    st.session_state.messages.append({"role": "user", "content": full_prompt})
                    st.session_state.input_mode = "normal"
                    st.rerun()
                    
            else:
                if prompt := st.chat_input("Ask Welt...", disabled=st.session_state.is_processing):
                    st.session_state.messages.append({"role": "user", "content": prompt})
                    st.rerun()

            if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
                 with chat_box:
                    with st.chat_message("assistant"):
                        st.session_state.is_processing = True # Lock
                        with st.spinner(f"Orchestrator Routing ({selected_model_id})..."):
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
                            
                            # --- 1+7 PARSING LOGIC (Expanded for v3.0.0) ---
                            if response.startswith("PATCH:"):
                                with open("subtitles.srt", "w", encoding="utf-8") as f: 
                                    f.write(weltengine.clean_and_repair_srt(response))
                                final_msg = "✅ The Mechanic patched the subtitles based on your feedback."
                                # Call feedback logger (new in v3)
                                weltengine.log_feedback(current_srt, response, "Mechanic")
                            
                            elif response.startswith("CHAPTERS:"):
                                lines = response.replace("CHAPTERS:", "").strip().split('\n')
                                st.session_state.chapters = [tuple(l.split(" - ", 1)) for l in lines if " - " in l]
                                final_msg = "✅ The Architect updated the Smart Chapters."
                            
                            elif response.startswith("RENAME:"): # Added for v3.0.0
                                try:
                                    raw_json = response.replace("RENAME:", "").strip().replace("```json", "").replace("```", "")
                                    new_names = json.loads(raw_json)
                                    for i, new_name in enumerate(new_names):
                                        if i < len(st.session_state.active_video_library):
                                            file_key = st.session_state.active_video_library[i]
                                            st.session_state.video_display_names[file_key] = new_name
                                    final_msg = "🏷️ The Librarian successfully auto-labeled the video files."
                                except Exception as e:
                                    final_msg = f"⚠️ Librarian formatting error: {e}"
                                    
                            elif response.startswith("SCAN_RESULT:"): # Added for v3.0.0
                                final_msg = "🔎 **Detective Report:**\n" + response.replace("SCAN_RESULT:", "").strip()

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
                                    final_msg = f"🎥 **Navigator Jumped to {ts}**: {desc}"
                                    
                                    st.session_state.messages.append({"role": "assistant", "content": final_msg})
                                    st.session_state.is_processing = False
                                    st.rerun()
                                    
                                except Exception: 
                                    final_msg = "⚠️ Navigator Seek failed."
                            
                            else:
                                final_msg = response.replace("ANSWER:", "").strip()
                
                 st.session_state.messages.append({"role": "assistant", "content": final_msg})
                 st.session_state.is_processing = False # Unlock
                 st.rerun()