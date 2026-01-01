# AI Submission Issue Context & Diagnosis

## Observed Problem
Upon submitting a game for AI coaching, the frontend transitioned to the "AI Processing" (Waiting) screen, but nothing happened for an extended period. No game entry updates were visible in the backend, and the session appeared to hang indefinitely.

The browser console showed:
```
Uncaught runtime errors:
×
ERROR
API Error: Not Found
request@http://localhost:3000/static/js/bundle.js:57458:24
```

## Investigation Notes & Research

### Frontend API Mapping Analysis
I conducted a thorough comparison between the frontend service calls and the backend router definitions to identify any discrepancies.

| Frontend Function | Method | Path | Backend Match | Status |
| :--- | :--- | :--- | :--- | :--- |
| `getGames()` | GET | `/games` | `router.get("")` | Match |
| `createGame()` | POST | `/games` | `router.post("")` | Match |
| `getGame(id)` | GET | `/games/{id}` | `router.get("/{game_id}")` | Match |
| `deleteGame(id)` | DELETE | `/games/{id}` | `router.delete("/{game_id}")` | Match |
| `addAnnotation()` | POST | `/games/{id}/annotations` | `router.post("/{game_id}/annotations")` | Match |
| `submitGame()` | POST | `/games/{id}/submit` | `router.post("/{game_id}/submit")` | Match |
| `getNextQuestion()` | GET | `/games/{id}/next-question` | `router.get("/{game_id}/next-question")` | Match |
| `answerQuestion()` | POST | `/questions/{id}/answer` | `router.post("/questions/{question_id}/answer")` | Match |
| `getReflection()` | GET | `/games/{id}/reflection` | **MISSING** | **404 NOT FOUND** |
| `getPciUsage()` | GET | `/pci/usage` | `router.get("/usage")` | Match |
| `getPciSettings()` | GET | `/pci/settings` | `router.get("/settings")` | Match |
| `getAvailableModels()`| GET | `/pci/available-models`| `router.get("/available-models")`| Match |
| `updatePciSettings()` | POST | `/pci/settings` | `router.post("/settings")` | Match |
| `approvePciSession()` | POST | `/pci/approvals/{id}/decision` | `router.post("/approvals/{approval_id}/decision")` | Match |

### Root Cause Diagnosis
Detailed log analysis and code inspection revealed two critical issues:

1.  **Missing Reflection Endpoint**: The frontend `FinalReflection` view calls `getReflection(gameId)` which targets `/games/${id}/reflection`. This endpoint was completely missing from `backend/api/games/router.py`, causing a 404 "Not Found" error when the frontend attempted to finalize the session. This explains the "API Error: Not Found" in the console.
2.  **Redis Connectivity Stalling Pipeline**:
    ```text
    redis.exceptions.ConnectionError: Error Multiple exceptions: [Errno 61] Connect call failed ('127.0.0.1', 6379), [Errno 61] Connect call failed ('::1', 6379, 0, 0) connecting to localhost:6379.
    ```
    The background task stalled while attempting to acquire a Redis lock. This prevented the game state from transitioning from `SUBMITTED` to `COACHING`, which in turn caused the frontend polling mechanism to stay on the waiting screen forever.

## Applied Remediation

### 1. Backend: Implemented Reflection Endpoint & Lifecycle State Machine
- Added the missing `GET /games/{game_id}/reflection` endpoint in `backend/api/games/router.py`.
- **Automatic State Progression**: Updated `answer_question` in `router.py` to automatically transition game state to `COMPLETED` when the last question is answered.
- **Robust Orchestration State**: Ensured `AIOrchestrator` explicitly sets state to `COACHING` after successful pipeline completion to trigger frontend transitions.

### 2. Backend: Robust AI Orchestration
- **Immediate State Transition**: The `AIOrchestrator` now transitions the game to `COACHING` state **immediately** before attempting to acquire the Redis lock. This ensures that even if Redis fails, the frontend polling will detect the state change.
- **Graceful Connection Handling**: Added explicit `try-except` blocks around the Redis locking logic. If a `ConnectionError` occurs, the system logs a `CRITICAL` error but continues to execute the pipeline rather than hanging.

### 3. Frontend & Backend: Enhanced Observability
- **Backend Logging**: Added detailed request/call_next logging middleware in `backend/api/main.py`.
- **Frontend Logging**: Added URL-aware error logging in `web/src/services/api.ts` to log the full URL on failure.

### 4. UI Component Leak Fix
Implemented a strict routing isolation check in `App.tsx` that monitors `hashchange` events and explicitly disables PCI elements if the route contains `/game/`.

## Diagnosis Verification Plan
- **Log Verification**: Observe backend logs for `DEBUG: Incoming request: GET /games/{id}/reflection` and `DEBUG: Response status: 200`.
- **State Flow Test**: Verify that the game transitions from `SUBMITTED` to `COACHING` even when Redis is down.
- **PCI Isolation Test**: Navigate to a game route and ensure the "Parent Control" nav link or PCI-specific headers are suppressed.
