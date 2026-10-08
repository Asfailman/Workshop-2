# Workshop-2: Module 1 - Conversational AI & Intelligent Guidance

Welcome to the project repository! This guide provides everything team members need to get started, install dependencies, and run both the AI module and the Backend service.

---

## 📌 What to Do First (Prerequisites & Initial Setup)

Before running the code, complete these 3 setup steps:

### 1. Install & Set Up Ollama (For AI)
The conversational AI runs locally via Ollama with the `llama3.2:3b` model.
1. Download and install Ollama from [https://ollama.com](https://ollama.com).
2. Open your terminal or PowerShell and pull/run the required model:
   ```powershell
   ollama run llama3.2:3b
   ```
   *(Keep Ollama running in the background while working with the AI or Backend).*

### 2. Set Up Python Virtual Environment
We recommend using Python 3.10 or higher.
From the project root directory (`Workshop-2`):
```powershell
# Create virtual environment
python -m venv venv

# Activate it:
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Windows (Command Prompt):
.\venv\Scripts\activate.bat
# macOS / Linux:
source venv/bin/activate
```

### 3. Install All Project Dependencies
With your virtual environment active, run:
```powershell
pip install -r requirements.txt
```

---

## 🚀 How to Run the Project

### Option A: Run the Backend Server (Recommended)
This starts the FastAPI server that bridges the Android client and the AI:
```powershell
python run_backend.py
```
* **Swagger UI / Interactive API Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **Local Server URL:** `http://127.0.0.1:8000` (Network: `http://0.0.0.0:8000`)

#### How to Test via Swagger:
1. Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) in your browser.
2. Click on `POST /api/v1/assistant/query` > **Try it out**.
3. Send a test JSON request:
   ```json
   {
     "session_id": "member_test",
     "message": "Where is Lab 3?",
     "current_location_id": "MAIN_ENTRANCE"
   }
   ```
4. Verify you receive the generated AI reply and extracted destination.

---

### Option B: Test the AI Module Standalone (CLI Mode)
If you are developing or testing only the NLP/AI logic without starting the server:
```powershell
cd AI
python main.py
```
You can chat with the assistant directly in your terminal to inspect prompt behavior, intent classification, and entity extraction.

---

## 📂 Project Structure

```
Workshop-2/
├── AI/                           # Member 2: AI / NLP logic
│   ├── nlp_module.py             # Core Ollama integration & prompt engineering
│   ├── main.py                   # Standalone CLI chat test
│   └── NLP_Desc.md               # AI design specification
├── module_1_back_end/            # Member 3: Backend API & Knowledge Base
│   ├── backend/
│   │   ├── main.py               # FastAPI application entrypoint
│   │   ├── api/v1/               # API endpoints (health, assistant, destinations)
│   │   ├── schemas/              # Pydantic request/response models
│   │   ├── services/             # Business logic & AI bridge (assistant_service.py)
│   │   └── knowledge_base/       # Campus location data and lookup
│   ├── docs/                     # API contracts & documentation
│   └── readme.md                 # Backend documentation
├── run_backend.py                # One-click script to start backend server
├── requirements.txt              # All dependencies for the repository
└── README.md                     # This onboarding guide
```

---

## 👥 Team Roles (Module 1)

* **Member 1 (Android UI):** Consumes `POST /api/v1/assistant/query` and manages the user interface.
* **Member 2 (AI / NLP):** Maintains `AI/nlp_module.py` and model responses.
* **Member 3 (Backend API):** Maintains `module_1_back_end/` endpoints, session handling, and knowledge base.
* **Member 4 (Integration):** Validates API contracts and coordinates multi-module integration.

---

## ⚠️ Notes & Common Issues

* **Error: `ConnectionRefusedError` or `Ollama service unavailable`**:
  Make sure Ollama is open and running in your taskbar, and that you ran `ollama run llama3.2:3b`.
* **Port Conflict**:
  If port `8000` is occupied, change the port in `run_backend.py` (e.g. `port=8080`).