import time
import srt
import random 
from functools import wraps 
from google import genai
from google.genai import types
from google.genai import errors 

# ⚠️ STRICT CONFIGURATION: DEFAULT MODEL UPDATED
# User Mandate: Default is now 3.0 Flash Preview.
DEFAULT_MODEL_ID = "gemini-3.0-flash-preview" 

# --- EXPONENTIAL BACKOFF DECORATOR (New in v2.0) ---
def exponential_backoff(max_retries=5, base_delay=1, max_delay=60):
    """
    Decorator for exponential backoff with jitter to handle API Rate Limits.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                
                except errors.ClientError as e:
                    # Check if it is a 429 (Resource Exhausted)
                    if e.code == 429 or "429" in str(e):
                        wait_time = min(max_delay, (base_delay * 2 ** retries))
                        wait_time += random.uniform(0, 1) # Add Jitter
                        print(f"⚠️ API Busy (429). Retrying in {wait_time:.2f}s...")
                        time.sleep(wait_time)
                        retries += 1
                    else:
                        raise e 
                        
                except errors.ServerError as e:
                    # 503 Service Unavailable / Overloaded
                    wait_time = min(max_delay, (base_delay * 2 ** retries))
                    print(f"⚠️ Server Error (5xx). Retrying in {wait_time:.2f}s...")
                    time.sleep(wait_time)
                    retries += 1

                except Exception as e:
                    error_str = str(e).lower()
                    if "429" in error_str or "resource exhausted" in error_str or "quota" in error_str:
                        wait_time = min(max_delay, (base_delay * 2 ** retries))
                        print(f"⚠️ API Busy (Generic). Retrying in {wait_time:.2f}s...")
                        time.sleep(wait_time)
                        retries += 1
                    else:
                        raise e
            raise Exception("Max retries exceeded. API is currently overloaded.")
        return wrapper
    return decorator

# --- HELPER: ROBUST PROCESSING WAITER ---
def _wait_for_processing(client, myfile):
    print(f"⏳ Waiting for video processing: {myfile.name}")
    for _ in range(150): 
        if myfile.state.name == "ACTIVE":
            print(f"✅ Video Active: {myfile.name}")
            return myfile
        elif myfile.state.name == "FAILED":
            raise Exception("Video processing failed on Google servers.")
        time.sleep(2)
        myfile = client.files.get(name=myfile.name)
    raise Exception("Video processing timed out (5-minute limit reached).")

# --- SAFETY CONFIGURATOR ---
def _configure_safety(user_filters):
    if not user_filters: user_filters = {}

    api_settings = {
        "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
        "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
        "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
        "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
    }
    
    prompt_rules = []

    if user_filters.get("gore"):
        api_settings["HARM_CATEGORY_DANGEROUS_CONTENT"] = "BLOCK_NONE"
        api_settings["HARM_CATEGORY_HARASSMENT"] = "BLOCK_NONE"
        prompt_rules.append("- **CONTEXT MODE: VIOLENCE ALLOWED.** You are authorized to process/describe violent or dangerous content objectively for analysis.")
    else:
        prompt_rules.append("- **SAFETY MODE: STRICT.** Strictly filter out or summarize descriptions of gore and violence.")

    if user_filters.get("nsfw"):
        api_settings["HARM_CATEGORY_SEXUALLY_EXPLICIT"] = "BLOCK_NONE"
        prompt_rules.append("- **CONTEXT MODE: NSFW ALLOWED.** You are authorized to process nudity or mature themes if relevant to the narrative.")
    else:
        prompt_rules.append("- **SAFETY MODE: FAMILY FRIENDLY.** Strictly block or refuse to describe sexually explicit content.")

    if user_filters.get("profanity"):
        prompt_rules.append("- **LANGUAGE:** Transcribe profanity exactly as spoken. Do not censor.")
    else:
        prompt_rules.append("- **LANGUAGE:** Replace strong profanity with asterisks (e.g., f***).")

    final_safety_conf = [
        types.SafetySetting(category=k, threshold=v) for k, v in api_settings.items()
    ]
    
    return final_safety_conf, "\n".join(prompt_rules)

# --- UPDATED: Subtitle Gen ---
@exponential_backoff()
def generate_subtitles_backend(api_key, video_path, target_language="English", include_sfx=False, user_filters=None, model_id=DEFAULT_MODEL_ID):
    client = genai.Client(api_key=api_key)
    
    print(f"☁️ DEBUG: Starting Upload for {video_path}...") 
    try:
        myfile = client.files.upload(file=video_path)
        myfile = _wait_for_processing(client, myfile)
    except Exception as e:
        print(f"❌ DEBUG: Upload Failed: {e}") 
        return f"Error Uploading: {e}"

    safety_conf, safety_prompt_instructions = _configure_safety(user_filters)

    if include_sfx:
        sfx_instruction = "- **Context Mode: ON**. You MUST transcribe significant non-speech sounds in brackets."
    else:
        sfx_instruction = "- **Context Mode: OFF**. Do NOT subtitle sound effects."

    system_prompt = f"""
    You are an expert Context-Aware Subtitler.
    IMPORTANT NOTE: IGNORE ANY SUBTITLES ALREADY IN THE VIDEO.
    SAFETY INSTRUCTIONS (FROM USER):
    {safety_prompt_instructions}

    DEFINITIONS:
    - **Matrix Language**: The prevalent language spoken in the video
    - **Foreign Language**: Any language that is NOT the Matrix Language.
    - **Significant SFX**: Non-speech sounds that are crucial for understanding the scene.
    - **Insignificant SFX**: Background noises that do not add meaningful context.

    RULES:
    1. **Identify Matrix Language**: Listen to the full context of the video
    2. **Identify text on screen**: If it is subtitle text already present, IGNORE it.
    3. **Translate ALL speech and relevant screen text to {target_language}**
    4. **Tagging logic**:
             - Matrix Language: keep as plain text
             - Foreign Language: prefix with (language name) + <i>italics</i>
    5. **Sound Effect Logic**: {sfx_instruction}
    6. **Timing**: Ensure subtitles are perfectly timed.
    7. **Output Format**: Return ONLY the valid SRT formatted subtitles.
    """

    user_prompt = f"Video Processed. Target: {target_language}. Task: Generate Subtitles."

    print(f"🔄 DEBUG: Generating with model {model_id}...") 
    response = client.models.generate_content(
        model=model_id, 
        contents=[myfile, user_prompt],
        config={
            "system_instruction": system_prompt,
            "temperature": 0.2,
            "safety_settings": safety_conf,
        }
    )
    
    if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
        text_parts = []
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'text') and part.text:
                text_parts.append(part.text)
        full_text = "".join(text_parts)
        if full_text:
            return full_text
    
    if response.text:
        return response.text
        
    reason = "Unknown"
    if response.candidates and response.candidates[0].finish_reason:
        reason = response.candidates[0].finish_reason.name
    
    print(f"⛔ DEBUG: Blocked! Finish Reason: {reason}")
    return f"Error: Content blocked by Safety Filters. Reason: {reason}"


# --- UPDATED: Chapters ---
@exponential_backoff()
def generate_smart_chapters(api_key, video_path, model_id=DEFAULT_MODEL_ID):
    client = genai.Client(api_key=api_key)
    try:
        myfile = client.files.upload(file=video_path)
        myfile = _wait_for_processing(client, myfile)
    except Exception as e:
        return [("00:00", f"Error: {e}")]

    prompt = "Analyze video. Generate Smart Chapters. Format STRICTLY: 'MM:SS - Chapter Title'. Start with 00:00."

    response = client.models.generate_content(
        model=model_id, 
        contents=[myfile, prompt],
        config={"temperature": 0.1}
    )
    
    final_text = ""
    if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'text') and part.text:
                    final_text += part.text
    if not final_text and response.text:
        final_text = response.text

    chapters = []
    if final_text:
        raw_lines = final_text.strip().split('\n')
        for line in raw_lines:
            if " - " in line:
                parts = line.split(" - ", 1)
                if len(parts) == 2:
                    chapters.append((parts[0].strip(), parts[1].strip()))
    return chapters

# --- UPDATED: VX Assistant (Handles Multiple Files) ---
@exponential_backoff()
def vx_assistant_fix(api_key, video_input, current_srt, current_chapters, user_instruction, user_filters=None, model_id=DEFAULT_MODEL_ID):
    client = genai.Client(api_key=api_key)
    
    processed_files = []
    try:
        if isinstance(video_input, list):
            for idx, path in enumerate(video_input):
                print(f"Processing video {idx+1}/{len(video_input)}: {path}")
                myfile = client.files.upload(file=path)
                myfile = _wait_for_processing(client, myfile)
                processed_files.append(myfile)
        else:
            myfile = client.files.upload(file=video_input)
            myfile = _wait_for_processing(client, myfile)
            processed_files.append(myfile)
            
    except Exception as e:
        return f"ANSWER: Error accessing video files: {e}"

    safety_conf, safety_prompt_instructions = _configure_safety(user_filters)

    system_prompt = f"""
    You are VX Assistant, a Multimodal Video Expert.
    
    YOUR SAFETY PROTOCOLS:
    {safety_prompt_instructions}
    
    TASK: Determine User Intent and Output ONE of these formats.
    
    SPECIAL INSTRUCTION FOR MULTIPLE VIDEOS:
    If multiple videos are provided, you are performing "Relative Video Intelligence". 
    You must compare, contrast, or find chronological connections between the videos provided.
    
    OUTPUT FORMATS:
    1. **EDIT SUBTITLES** (Only valid for Single Video Mode):
       - Output: "PATCH:" followed by the full corrected SRT block.
       
    2. **EDIT CHAPTERS** (Only valid for Single Video Mode):
       - Output: "CHAPTERS:" followed by the new list.
       
    3. **QUESTION**: General Q&A or Cross-Context Reasoning.
       - Output: "ANSWER:" followed by your helpful response.

    4. **NAVIGATION**:
       - Output: "SEEK:MM:SS" (Note: If multiple videos, specify which video, e.g., "SEEK:Video 1:MM:SS")

    5. **CONTENT SCAN**:
       - Output: "(NAME) FOUND IN VIDEO (X) TIMES: [TIMESTAMPS]".
    """
    
    srt_ctx = current_srt if current_srt else "(No subtitles)"
    if current_chapters:
        chap_ctx = "\n".join([f"{ts} - {title}" for ts, title in current_chapters])
    else:
        chap_ctx = "(No chapters generated yet)"

    user_prompt = f"""
    [CURRENT CHAPTERS]
    {chap_ctx}

    [CURRENT SRT SAMPLE]
    {srt_ctx}

    [USER INSTRUCTION]
    {user_instruction}
    """

    content_payload = processed_files + [user_prompt]

    try:
        response = client.models.generate_content(
            model=model_id, 
            contents=content_payload,
            config={
                "system_instruction": system_prompt, 
                "temperature": 0.2,
                "safety_settings": safety_conf
            }
        )
        
        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            full_text = ""
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'text') and part.text:
                    full_text += part.text
            if full_text:
                return full_text
                
        if response.text:
            return response.text
        else:
            reason = "Unknown"
            if response.candidates and response.candidates[0].finish_reason:
                reason = response.candidates[0].finish_reason.name
            return f"ANSWER: I cannot answer this. (Reason: {reason}). Check your Safety Settings."

    except Exception as e:
        return f"ANSWER: Error: {e}"

def clean_and_repair_srt(raw_text):
    if not raw_text: return "Error: Empty response."
    try:
        clean_raw = raw_text.replace("PATCH:", "").replace("```srt", "").replace("```", "").strip()
        if "-->" not in clean_raw:
             return clean_raw 

        subtitle_generator = srt.parse(clean_raw)
        subtitles = list(subtitle_generator)
        return srt.compose(subtitles)
        
    except Exception as e:
        print(f"❌ DEBUG: SRT Parse Failed: {e}")
        return f"Error Repairing SRT: {e}"