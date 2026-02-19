# Welt VX 3.0.0
**Redefining Viewer Experience with Relative Video Intelligence.**

Welt VX is an agentic AI video intelligence environment. It transcends standard media players by treating video files as dynamic, interactive data sources. Powered by Gemini 3 Flash/Pro, Welt VX allows users to analyze, repair, and navigate multiple videos simultaneously through a natural language interface.

Developed by **Akshansh Hardaha (Antares)**.

---

## 🧠 The Architecture: 1+7 Task Force
Welt VX does not rely on a single monolithic prompt. It utilizes an **Orchestrator Agent** that routes user intent to one of 7 highly specialized AI tools:

1. **The Orchestrator:** Determines user intent and routes payload data.
2. **The Scribe:** Transcribes and translates multi-lingual audio with environmental context (SFX).
3. **The Architect:** Analyzes narrative arcs to generate timestamped "Smart Chapters".
4. **The Mechanic:** Executes human-in-the-loop repairs on subtitle logic, spelling, and timing.
5. **The Detective:** Performs forensic safety scans and locates specific objects/people across video frames.
6. **The Librarian:** Auto-labels and organizes multiple video files based on deep content analysis.
7. **The Navigator:** Interprets vague scene descriptions and jumps the video player to exact timestamps.
8. **The Guide:** Answers general questions and provides cross-video comparative summaries (Relative Video Intelligence).

## 🚀 Core Technologies
* **Frontend:** Streamlit
* **AI Engine:** Google GenAI SDK (`gemini-3-flash-preview` / `gemini-3-pro-preview`)
* **Database:** Google Cloud Firestore (Feedback & State Logging)
* **Subtitles:** Python `srt` module

---

## 🛠️ Installation & Setup

### 1. Local Development
Clone the repository and install the required dependencies:

```bash
git clone [https://github.com/your-repo/welt-vx.git](https://github.com/your-repo/welt-vx.git)
cd welt-vx
pip install -r requirements.txt

```

### 2. Secrets Configuration

Welt VX relies on a secure `.streamlit/secrets.toml` file to manage API keys and database connections.

1. Create a `.streamlit` folder in the root directory.
2. Create a file named `secrets.toml` inside it.
3. Configure your keys as follows:

```toml
APP_PASSWORD = "Your_Hackathon_Access_Code"
GEMINI_API_KEY = "Your_Google_AI_Studio_Key"

[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "..."
client_id = "..."
auth_uri = "[https://accounts.google.com/o/oauth2/auth](https://accounts.google.com/o/oauth2/auth)"
token_uri = "[https://oauth2.googleapis.com/token](https://oauth2.googleapis.com/token)"
auth_provider_x509_cert_url = "[https://www.googleapis.com/oauth2/v1/certs](https://www.googleapis.com/oauth2/v1/certs)"
client_x509_cert_url = "..."

```

### 3. Launching the Environment

Run the application using Streamlit:

```bash
streamlit run welt.py

```

---

## 🔐 Proprietary Notice

**PROPRIETARY AND CONFIDENTIAL.**
This source code is provided exclusively for evaluation purposes by the official judges of the Gemini API Developer Competition. It may not be copied, forked, distributed, or used for commercial purposes without explicit permission. See the `LICENSE` file for full terms.

```

```
