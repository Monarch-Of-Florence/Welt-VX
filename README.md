# Welt VX (Viewer Experience)

### The Multimodal Localization Agent powered by Gemini 3.

![Python](https://img.shields.io/badge/Python-3.10%2B-green)
![Gemini](https://img.shields.io/badge/AI-Gemini_3_Flash-orange)
![Streamlit](https://img.shields.io/badge/UI-Streamlit_Cinema-red)

**Welt VX** is an Agentic System designed to enable real-time reasoning and accessibility for video content in a context-aware environment. It leverages Gemini 3's multimodal capabilities to generate accurate subtitles, identify important narrative moments, and create smart chapters that speed up navigation. The system features a **Human-in-the-Loop (HITL)** Support Agent that enables semantic seeking, content scanning, and personalized refinement of all generated assets.

---

## 🚀 Key Features

### 1. 🧠 Matrix Language Logic (Context-Aware Translation)
Unlike standard translators that flatten dialogue, Welt VX distinguishes between the **Matrix Language** (the dominant narrative language) and **Embedded Languages**.
- **Matrix Language:** Rendered as standard text.
- **Embedded Language:** Automatically tagged and *italicized* to preserve the director's original intent.

### 2. 👁️ Multimodal Reasoning
Using **Gemini 3 Flash Preview**, the agent "watches" video pixels to caption visual sound effects that audio-only models miss.
- *Visual Cues:* `[Phone lights up]`, `[Door slams]`, `[Character nods]`.
- *Ambient Audio:* Translates non-speech audio cues (music, ambience) to enhance accessibility (e.g., `[Rain starts pouring]`).

### 3. 🤖 VX Assistant (Human-in-the-Loop)
A specialized **Support Agent** resides in the sidebar for real-time, conversational refinement.
- **Semantic Seek:** "Jump to the scene where the protagonist confronts the antagonist." (The agent identifies the relevant timestamp).
- **Natural Language Repair:** "Fix the typo at 00:45." (The agent edits the code; no regeneration needed).
- **Visual Q&A:** "What is the equipment used by this doctor at 12:59?"
- **Chapter Editing:** "Split the chapter at 15:30 into two."
- **Content Scanning:** "Search for all instances of 'Red Car'." (Returns a list of timestamps).
- **Suggestion Chips:** Context-aware buttons (Seek, Fix, Scan) that auto-fill complex commands, reducing manual typing.

### 4. 📑 Smart Chapters
The agent observes scene changes and narrative shifts to automatically generate a clickable, timestamped **Table of Contents**.

---

## 🛠️ Architecture

The project follows a **Modular Agentic Architecture** using Gemini 3 Flash Preview as the cognitive engine and a custom Streamlit interface for state management. The core pipeline consists of:

1.  **Orchestrator:** The workflow brain that manages specialized sub-agents via an **Intent Routing Mechanism**.
2.  **Multimodal Sub-Agent:** Processes both audio and visual inputs to create accurate, context-aware captions.
3.  **Navigation Agent:** Analyzes the video to identify key moments and generates smart chapters.
4.  **Support Agent:** A HITL agent that handles recursive edits, semantic seeking, and content scanning.

### **The Stability Stack**
* **Validation Layer:** Uses the `srt` library to ensure all generated subtitles are frame-perfect and synchronized.
* **Parsing Layer:** Converts raw Gemini output into structured formats (JSON/SRT) to prevent UI errors.
* **Stability Layer:** Implements retry logic and error handling to ensure robustness against API failures.

### **Minimalistic Interface**
The UI is designed for focus and utility:
* **Cinema Mode:** The video player occupies the majority of the screen with real-time subtitle overlays.
* **Control Center:** Interactive controls for generation, settings, and the Support Agent are organized neatly below the player.
* **Modal Interactions:** Complex tasks (customization, repairs) use modals to keep the main view uncluttered.

---

## 💻 Installation & Setup

**1. Clone the repository**
```bash
git clone [https://github.com/Monarch-Of-Florence/WeltVX.git](https://github.com/Monarch-Of-Florence/WeltVX.git)
cd welt-vx
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Set up Gemini API Key**
- Get your Gemini API key from Google AI Studio
- Create a `.env` file in the root directory and add your Gemini API key: 
```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

**4. Run the Application**
```bash
streamlit run welt.py
```

## ⚠️ Important Notes

- **Cloud Limitations:** The live demo hosted on Streamlit Community Cloud is optimized for video files up to **200 MB** due to free-tier RAM constraints. Uploading larger files may cause the app to restart ("Over Capacity").
- **Local Power:** The underlying configuration allows for uploads up to **500 MB**. For large-scale testing, it is highly recommended to **clone the repository** and run the application locally to bypass these cloud resource constraints.
- **Privacy:** All uploaded videos are processed in temporary storage and are not permanently saved.
