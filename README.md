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
   - Pre-configured entry point at [backend/main.py](module_1_back_end/backend/main.py).

3. **AI & NLP Module (`AI/`)**:
   - Natural Language Processing engine powered by **Ollama (`llama3.2:3b`)**.
   - Handles intent classification (Greeting, Location Query, Guidance Request, Facility Info, Opening Hours, General Help, Destination Recommendation).
   - Manages multi-turn conversation context and entity extraction.
   - Includes standalone interactive CLI tester at [AI/main.py](AI/main.py).

---

## 📁 Repository Structure

```text
Workshop-2/
├── app/                              # Android application (Kotlin / Gradle)
│   ├── src/main/java/.../            # Activities, ViewModels, and ApiService
│   └── src/main/res/                 # Layouts, drawables, and themes
├── AI/                               # Conversational AI & NLP engine
│   ├── nlp_module.py                 # Core Ollama integration & intent processor
│   ├── main.py                       # CLI testing interface
│   └── __init__.py
├── module_1_back_end/                # Backend API service
│   ├── backend/
│   │   ├── api/v1/                   # FastAPI route handlers
│   │   │   ├── assistant.py          # /api/v1/assistant/query
│   │   │   ├── destinations.py       # Destination listings
│   │   │   ├── health.py             # Server health check
│   │   │   └── router.py             # Consolidated API router
│   │   ├── core/                     # Configuration settings
│   │   ├── knowledge_base/           # Location and venue data
│   │   └── main.py                   # FastAPI application instance
│   └── requirements.txt              # Backend dependencies
├── requirements.txt                  # Root-level Python requirements
├── run_backend.bat                   # Batch script to launch FastAPI backend
├── run_ngrok.bat                     # Batch script to start ngrok tunnel
├── run_all.bat                       # Batch script to start backend + ngrok
├── build.gradle.kts                  # Root Gradle build configuration
├── settings.gradle.kts               # Gradle project modules
└── README.md                         # Project documentation
```

---

## 🛠️ Prerequisites

Ensure the following tools are installed on your machine:

1. **Python 3.10+**
2. **Ollama**:
   - Download from [ollama.com](https://ollama.com).
   - Pull the required LLM model:
     ```bash
     ollama pull llama3.2:3b
     ```
3. **Android Studio** (Ladybug or later recommended) with **JDK 17+** and **Android SDK 34+**.
4. *(Optional for remote mobile testing)* **ngrok**:
   - Download from [ngrok.com](https://ngrok.com) for public URL tunneling.

---

## 🚀 Getting Started

### 1. Set Up Python Dependencies

From the repository root directory:

```bash
# Optional: create a virtual environment
python -m venv venv
venv\Scripts\activate      # Windows

# Install required packages
pip install -r requirements.txt
```

### 2. Verify AI & NLP Engine (CLI Mode)

You can test the NLP conversational engine in your terminal before running the backend:

```bash
python AI/main.py
```

Type any guidance question (e.g. `"Where is the library?"`) to see structured intent recognition and response generation.

### 3. Run the Backend Server

Start the backend using the provided batch script:
- Double-click **`run_backend.bat`**, OR
- Run manually in terminal:
  ```bash
  cd module_1_back_end
  python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
  ```

API documentation will be available at:
- Swagger UI: `http://localhost:8000/docs`
- Redoc: `http://localhost:8000/redoc`

---

## 📱 Connecting the Android App

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
| `GET` | `/api/v1/destinations` | List available campus destinations and landmarks |
| `POST` | `/api/v1/route` | Compute navigation route between points |
| `POST` | `/api/v1/recommend` | Destination recommendation endpoint |

---

## 🧹 Pull Request Checklist

Before submitting a Pull Request to `main`:
- [x] No IDE configuration files (`.idea/`, `local.properties`) committed.
- [x] No build artifacts or cache files (`.gradle/`, `build/`, `__pycache__/`) committed.
- [x] `requirements.txt` contains all necessary dependencies (`fastapi`, `uvicorn`, `ollama`, `pydantic`, `requests`).
- [x] Python modules include valid `__init__.py` files.
- [x] Android app compiles cleanly and connects to backend endpoints.