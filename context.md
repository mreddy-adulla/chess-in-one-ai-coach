# Project Context: Chess-in-One AI Coach

## Implementation Status
The core logic and UI layers for the **Frontend (Web & Android)** and the **Backend (FastAPI)** have been established based on authoritative specifications.

### 1. Frontend Implementation
- **Web (React + TS):** Implemented all core views (`GameList`, `CreateGame`, `GameEntry`, `AIProcessing`, `GuidedQuestioning`, `FinalReflection`) and API service layer.
- **Android (Kotlin):** Implemented all core activities and Retrofit service layer.
- **Compliance:** Verified zero gamification, gated AI visibility, and backend-authoritative state transitions.

### 2. Backend Implementation (`/backend`)
- **Framework:** FastAPI.
- **Database:** PostgreSQL.
- **AI Orchestrator:** Manages the Socratic coaching loop.
- **AI Provider:** Configured to use **Gemini Vertex API** as the default provider.
- **Security:** JWT-based authentication with role-based access control (Child vs. Parent).

---

## Next Phase: Environment Setup, Build, and Deploy

### 0. Environment Setup
- **Python:** Use virtualenv in `backend/venv`. To activate: `source backend/venv/bin/activate`.
- **Node.js:** Use `nvm` to manage Node.js versions. Node.js v24.12.0 is available.
- **Commands:** Always prepend Node commands with nvm initialization: `export NVM_DIR="$HOME/.nvm" && [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh" && nvm use default && ...`
- **Scripts:**
    - `web_install.sh`: Installs frontend dependencies.
    - `run_web.sh`: Starts the React development server.
    - `run_backend.sh`: Starts the FastAPI server.
    - `backend/scripts/init_db.py`: Initializes the SQLite database.

### 1. Web App Setup
- **Dependencies:** Run `./web_install.sh`.
- **Config:** `web/src/services/api.ts` is configured to use `http://localhost:8000` by default.
- **Build:** Execute build scripts for production-ready static assets.

### 2. Backend Setup & AI Configuration
- **Environment:** Initialize Python virtualenv and install `backend/requirements.txt` (already done in `backend/venv`).
- **AI Provider:** Ensure `GOOGLE_APPLICATION_CREDENTIALS` and Vertex AI project details are set in `backend/.env`.
- **Default Model:** Gemini Vertex AI (e.g., `gemini-pro`).
- **Database:** SQLite is used locally (`chess_coach.db`). Run `backend/venv/bin/python backend/scripts/init_db.py` to reset/init.

### 3. Deployment Strategy
- **Infrastructure:** Docker-based deployment using `backend/api.Dockerfile` and `backend/docker-compose.yml`.
- **Networking:** Tailscale Funnel for secure production access.
- **Parent Control:** Ensure PCI (Web-only) is properly isolated and requires Parent JWT.

---

## Critical Reference Files
- `docs/implementation/frontend_api_mapping.md`: Authoritative API contract.
- `backend/api/ai/prompts/socratic_coach.md`: The canonical AI coaching prompt.
- `web/package.json`: Frontend dependencies.
- `backend/requirements.txt`: Backend dependencies.
- `backend/.env`: Environment secrets (DB, AI Keys).
