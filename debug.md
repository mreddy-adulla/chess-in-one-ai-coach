# Debug Context: Chess-in-One AI Coach

## Current Status
- **Backend (FastAPI)**: 
    - Running on port 8080.
    - CORS configured to allow all origins.
    - Auth middleware updated to allow OPTIONS and return JSON error responses instead of raising exceptions.
    - Database initialized with SQLite (`chess_coach.db`).
    - Basic routes for `/games` implemented (list, create, get).
- **Frontend (React)**:
    - Running on port 3000 (dev server).
    - Styling partially fixed with Tailwind CSS generation.
    - `GameEntry.tsx` implemented with `react-chessboard`, move tree, and voice review skeleton.
    - `GuidedQuestioning.tsx` implemented with `react-chessboard`.
    - Local dev token injected into `ApiService`.

## Identified Issues & Blockers
1. **PCI GUI Serving**: The backend is failing to serve static files from `web/build` because of path resolution issues or missing directories in the build.
2. **CORS/401**: Although fixed in code, authentication remains strict. A dev token has been generated and used.
3. **Styling**: Tailwind CSS integration is still sensitive and might need a proper build-time integration instead of manual generation.
4. **Blank Screen**: `pci-gui` returns a blank screen due to absolute paths in the React build. `"homepage": "."` was added to `package.json` to address this.

## Recent Changes
- Updated `backend/api/main.py` with SPA support for `/pci-gui`.
- Updated `backend/api/auth/middleware.py` to handle preflights and avoid crash-on-auth-failure.
- Updated `backend/api/games/router.py` to handle date string conversion for SQLite.
- Added `web_install.sh`, `run_web.sh`, `run_backend.sh`, `env.sh`.
- Added `backend/scripts/generate_token.py`.

## Next Steps
- Fix static file mounting in `main.py`.
- Finalize Tailwind build process.
- Implement missing Socratic logic in backend `orchestrator.py`.
