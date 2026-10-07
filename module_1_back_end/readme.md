# Module 1 Backend (Member 3)

Backend skeleton for Module 1: **Conversational AI and Intelligent Guidance**.

This repository covers ONLY Module 1.

## Scope of this Backend

- Receive user message from Android (Member 1).
- Pass message to AI/NLP logic (Member 2).
- Look up destination information from the Knowledge Base.
- Return a guidance reply to Android.

## Status

- API contract: DRAFT (not final)
- Backend logic: NOT IMPLEMENTED (placeholders only)
- Knowledge base: EMPTY (locations.json is `[]`)

## How to Run

### Option 1 (Easiest — from workspace root `Workshop-2/`):

    python run_backend.py

### Option 2 (From inside `module_1_back_end/`):

    cd module_1_back_end
    python -m uvicorn backend.main:app --reload

Then open:

    http://127.0.0.1:8000/docs


## File Structure

    module-1-backend/
    ├── backend/
    │   ├── main.py                  FastAPI entrypoint
    │   ├── core/
    │   │   └── config.py            env / robot IP settings
    │   ├── api/v1/
    │   │   ├── router.py            includes all routes
    │   │   ├── health.py            GET /api/v1/health
    │   │   ├── assistant.py         POST /api/v1/assistant/query
    │   │   └── destinations.py      GET  /api/v1/destinations/{id}
    │   ├── services/
    │   │   ├── assistant_service.py      Member 2 plugs AI/NLP here
    │   │   └── destination_service.py    KB lookup logic
    │   └── knowledge_base/
    │       ├── loader.py            reads JSON
    │       ├── repository.py        search / get locations
    │       └── data/
    │           └── locations.json   room/lab data (currently empty)
    ├── docs/
    │   └── api_contract_draft.md    DRAFT contract (not final)
    ├── tools/
    │   └── robot_control.py         OPTIONAL Python tool
    ├── requirements.txt
    └── README.md

## API Endpoints (Module 1 only)

| Method | Path                            | Purpose                             | Owner       |
|--------|---------------------------------|-------------------------------------|-------------|
| GET    | `/api/v1/health`                | Check backend is alive              | Member 3    |
| POST   | `/api/v1/assistant/query`       | User message → AI reply + guidance  | Member 2+3  |
| GET    | `/api/v1/destinations/{id}`     | Look up a room/lab from KB          | Member 3    |

All non-health endpoints currently return `501 Not Implemented`.

## Team Roles (Module 1)

- **Member 1** — Android UI + user input + calls `POST /assistant/query`
- **Member 2** — AI/NLP logic inside `assistant_service.py`
- **Member 3** — Backend API + Knowledge Base (this repo)
- **Member 4** — Integration, contract coordination

## Rules

1. API contract is **DRAFT**. Do not finalize alone. Member 4 coordinates.
2. Do not rename fields silently — it breaks Member 1 and Member 2.
3. `tools/` is OPTIONAL Python for experiments only. Do not import it into `backend/`.
4. Every member tests their own part before handing over for integration.
5. Push your work to your own branch: `member3-backend`.