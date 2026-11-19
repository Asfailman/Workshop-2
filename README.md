# AI Guidance Bot (Workshop 2)

An intelligent conversational guidance and campus navigation system combining a modern **Android mobile client**, an **Ollama-powered NLP assistant**, and a **FastAPI backend microservice**.

---

## 📌 Architecture Overview

```text
┌───────────────────────┐
│   Android Mobile App  │ (Kotlin, MVVM, OkHttp, Material Design)
│        (app/)         │
└──────────┬────────────┘
           │ HTTP POST (JSON)
           ▼
┌───────────────────────┐
│    FastAPI Backend    │ (FastAPI, Uvicorn, Pydantic)
│  (module_1_back_end/) │
└──────────┬────────────┘
           │ Python Bridge
           ▼
┌───────────────────────┐
│   AI / NLP Module     │ (Ollama, llama3.2:3b, Multi-turn Context)
│        (AI/)          │
└───────────────────────┘
```

The system is organized into three main layers:

1. **Android App (`app/`)**:
   - Modern chat interface built with Kotlin and Material components.
   - Communicates with the backend using [ApiService.kt](app/src/main/java/com/example/aiguidance_bot/data/ApiService.kt).
   - Supports contextual quick actions, bot suggestions, and guidance requests.

2. **Backend Service (`module_1_back_end/`)**:
   - FastAPI server exposing RESTful endpoints for Android clients.
   - Manages routing, destination lookup, and forwards queries to the AI module.
   - Pre-configured entry point at [backend/main.py](module_1_back_end/backend/main.py) and runnable via [run_backend.py](run_backend.py).

3. **AI & NLP Module (`AI/`)**:
   - Natural Language Processing engine powered by **Ollama (`llama3.2:3b`)**.
   - Handles intent classification (Greeting, Location Query, Guidance Request, Facility Info, Opening Hours, General Help, Destination Recommendation).
   - Manages multi-turn conversation context and entity extraction.
   - Includes standalone interactive CLI tester at [AI/main.py](AI/main.py).

---

## 🛠️ Prerequisites & Initial Setup

Ensure the following tools are installed on your machine:

1. **Python 3.10+**
2. **Ollama**:
   - Download from [https://ollama.com](https://ollama.com).
   - Pull the required LLM model:
     ```powershell
     ollama run llama3.2:3b
     ```
   *(Keep Ollama running in the background while working with the AI or Backend).*
3. **Android Studio** (Ladybug or later recommended) with **JDK 17+** and **Android SDK 34+**.
4. *(Optional for remote mobile testing)* **ngrok**:
   - Download from [ngrok.com](https://ngrok.com) for public URL tunneling.

---

## 🚀 Getting Started

### 1. Set Up Python Dependencies

From the repository root directory (`Workshop-2`):

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

# Install required packages
pip install -r requirements.txt
```

### 2. Verify AI & NLP Engine (CLI Mode)

You can test the conversational AI logic standalone in your terminal before running the backend:

```powershell
cd AI
python main.py
```

Type any guidance question (e.g. `"Where is the library?"`) to inspect prompt behavior, intent classification, and entity extraction.

### 3. Run the Backend Server

Start the backend using any of the following options:

- **Option A (Python script):**
  ```powershell
  python run_backend.py
  ```
- **Option B (Batch script):**
  - Double-click **`run_backend.bat`**, OR
- **Option C (Manual uvicorn command):**
  ```powershell
  cd module_1_back_end
  python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
  ```

Interactive API documentation will be available at:
- **Swagger UI:** `http://localhost:8000/docs`
- **Redoc:** `http://localhost:8000/redoc`

#### How to Test via Swagger:
1. Open `http://localhost:8000/docs` in your browser.
2. Select `POST /api/v1/assistant/query` > **Try it out**.
3. Send a test JSON request:
   ```json
   {
     "session_id": "test_session",
     "message": "Where is the library?",
     "current_location_id": "MAIN_ENTRANCE"
   }
   ```
4. Verify you receive the generated AI reply and extracted destination.

---

## 📱 Connecting the Android App

### ApiService.kt Location
```text
app/src/main/java/com/example/aiguidance_bot/data/ApiService.kt
```

### Option A: Testing on Local Wi-Fi
1. Find your PC's local IP address (e.g., run `ipconfig`).
2. In `app/src/main/java/com/example/aiguidance_bot/data/ApiService.kt`, set:
   ```kotlin
   private val apiUrl = "http://YOUR_PC_LOCAL_IP:8000/api/v1/assistant/query"
   ```
3. Ensure your phone and PC are connected to the same Wi-Fi network.

### Option B: Testing with Public URL (ngrok) — Recommended
1. Run **`run_all.bat`** (or run `run_ngrok.bat` alongside `run_backend.bat`).
2. Copy your public `https://...` ngrok forwarding URL.
3. In `ApiService.kt`, set:
   ```kotlin
   private val apiUrl = "https://your-ngrok-subdomain.ngrok-free.dev/api/v1/assistant/query"
   ```
4. Build and install the app in Android Studio. You can now test from any network or mobile data.

---

## 📡 Key API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/health` | Service health status check |
| `POST` | `/api/v1/assistant/query` | Main query endpoint for Android assistant messages |
| `POST` | `/api/v1/assistant/reset` | Reset dialogue context for a specific session |
| `GET` | `/api/v1/destinations` | List available campus destinations and landmarks |
| `GET` | `/api/v1/destinations/{id}` | Retrieve specific destination details |
| `POST` | `/api/v1/route` | Compute navigation route between points |
| `POST` | `/api/v1/recommend` | Destination recommendation endpoint |

---

## 👥 Team Roles (Module 1)

* **Member 1 (Android UI):** Consumes `POST /api/v1/assistant/query` and manages the user interface.
* **Member 2 (AI / NLP):** Maintains `AI/nlp_module.py` and model responses.
* **Member 3 (Backend API):** Maintains `module_1_back_end/` endpoints, session handling, and knowledge base.
* **Member 4 (Integration):** Validates API contracts and coordinates multi-module integration.

---

## ⚠️ Common Issues & Troubleshooting

* **Error: `ConnectionRefusedError` or `Ollama service unavailable`**:
  Make sure Ollama is open and running on your machine, and that you ran `ollama run llama3.2:3b`.
* **Port Conflict**:
  If port `8000` is already in use by another application, change the port in `run_backend.py` (e.g. `port=8080`) or pass `--port 8080` to uvicorn.

---

## 🧹 Pull Request Checklist

Before submitting a Pull Request to `main`:
- [x] No IDE configuration files (`.idea/`, `local.properties`) committed.
- [x] No build artifacts or cache files (`.gradle/`, `build/`, `__pycache__/`) committed.
- [x] `requirements.txt` contains all necessary dependencies (`fastapi`, `uvicorn`, `ollama`, `pydantic`, `requests`).
- [x] Python modules include valid `__init__.py` files.
- [x] Android app compiles cleanly and connects to backend endpoints.
