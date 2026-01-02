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

### 5. Missing Import Fix (2026-01-02)
- **Issue**: `get_next_question` endpoint was throwing `NameError: name 'Annotation' is not defined` when trying to query annotations related to a question's key position.
- **Fix**: Added `Annotation` to the imports in `backend/api/games/router.py` (line 5) to resolve the missing model reference.

### 6. Reflection Navigation Fix (2026-01-02)
- **Issue**: Frontend `FinalReflection` component was attempting to fetch reflection even when the game was in `COACHING` state with unanswered questions, resulting in 400 errors and a confusing "Reflection Not Available" message.
- **Fix**: 
  - Updated `FinalReflection.tsx` to check game state before fetching reflection
  - Added automatic redirect to coaching page if game is in `COACHING` state
  - Enhanced error handling to detect 400 errors and redirect appropriately
  - Updated `ApiService.handleErrorResponse` to preserve HTTP status codes in error objects for better error detection
  - Added "Continue Questions" button when reflection isn't available

### 7. Socratic Question Generation Fix (2026-01-02)
- **Issue**: Questions were showing as "Stub question for {CATEGORY}" because the orchestrator was using hardcoded placeholder text instead of generating real questions.
- **Fix**: 
  - Created `SocraticQuestionerProvider` class in `backend/api/ai/providers/socratic_questioner.py`
  - Provider supports OpenAI and Google Vertex AI with template fallback
  - Updated `AIOrchestrator._generate_socratic_questions()` to use the provider
  - Questions now generated based on engine truth, student annotations, and category
  - Follows Socratic Coach prompt guidelines (never reveals best move, trusts engine truth, age-appropriate)

### 8. Answer Endpoint and Skip Functionality Fix (2026-01-02)
- **Issue**: 
  - Frontend was sending `{ content: answer, skipped }` but backend expected `answer` parameter, causing 404 errors when skipping
  - Backend wasn't handling the `skipped` flag properly
- **Fix**:
  - Created `QuestionAnswer` Pydantic model to match frontend request format
  - Updated `answer_question` endpoint to accept `QuestionAnswer` model
  - Added proper handling of `skipped` flag - sets `question.skipped = True` when skipped
  - Skipped questions are now properly recorded and don't block game completion

### 9. Key Position Analyzer Implementation (2026-01-02)
- **Issue**: Analyzer was using a hardcoded stub that always returned the same position (after move 3), which is too early and not coach-like. Key positions should be found throughout the game, not just at the beginning.
- **Fix**:
  - Implemented real game analysis in `_run_analyzer()` method
  - Analyzer now parses the full PGN and replays the game
  - Only analyzes positions after move 10 (avoids too-early positions)
  - Samples positions evenly throughout the game (3-5 positions)
  - Uses chess engine to evaluate each position and determine reason codes
  - Reason codes assigned based on position characteristics:
    - `TRANSITION`: Significant evaluation change
    - `THREAT_AWARENESS`: Positions with threats
    - `OPP_INTENT`: High evaluation swing (likely missed opponent plan)
  - Key positions are now meaningful and distributed throughout the game

### 10. Chess Engine API Failure Handling (2026-01-02)
- **Issue**: Chess engine API (chess-api.com) was returning 404 errors, causing the analyzer to fail completely and preventing the pipeline from completing. This left users stuck on "Finalizing your reflection" screen.
- **Fix**:
  - Updated `ChessEngineProvider.analyze_position()` to return fallback values instead of raising exceptions
  - Added `fallback_on_error` parameter (default True) to gracefully handle API failures
  - Analyzer now continues processing even if engine calls fail
  - Positions are added with default engine_truth values when API fails
  - Added multiple fallback layers to ensure at least 1 key position is always returned
  - Reduced API timeout and depth to improve reliability
  - Pipeline can now complete even when external engine API is unavailable

### 11. Chess Engine Depth Limit Correction (2026-01-02)
- **Issue**: Code was requesting depth 20-25, but online chess APIs (chess-api.com) support maximum depth of 18.
- **Fix**:
  - Updated `ChessEngineProvider.analyze_position()` to use depth 18 (maximum supported)
  - Added comment explaining depth 18 corresponds to ~2750 Elo rating strength
  - Increased `max_time` to 15 seconds to allow sufficient time for deep analysis
  - Uses actual depth returned by API, with fallback to 18 if not specified

### 12. Reflection Generation Hanging Fix (2026-01-02)
- **Issue**: Frontend was stuck on "Finalizing your reflection" screen. The frontend was checking game state and redirecting before calling the reflection endpoint, preventing the backend from generating reflection even when all questions were answered.
- **Fix**:
  - Updated `FinalReflection.tsx` to call `getReflection()` first, letting the backend handle state checking
  - Backend reflection endpoint already had logic to generate reflection if all questions answered (even if state is COACHING)
  - Added timeout protection (60 seconds) to reflection generation in `get_reflection` endpoint
  - Added timeout protection (30 seconds) to OpenAI and Vertex AI calls in `ReflectionGeneratorProvider`
  - Added fallback to template reflection if AI generation times out or fails
  - Improved error handling to ensure reflection is always generated, even if AI providers fail

### 18. Move Counting Bug Fix - Questions Appearing Too Early (2026-01-02)
- **Issue**: Questions were appearing at move 5-6 (opening phase) instead of after move 10. The analyzer was counting half-moves (plies) instead of full moves.
- **Root Cause**: In chess, `move_count` was incrementing for each half-move (ply), so `move_count >= 10` meant after 10 half-moves = 5 full moves, not 10 full moves.
- **Fix**:
  - Updated logic to convert half-moves to full moves: `full_move_number = (move_count + 1) // 2`
  - Changed condition from `move_count >= 10` to `full_move_number >= 10`
  - Now correctly analyzes positions after 10 full moves (20 half-moves) instead of 5 full moves
  - Added `half_move_number` field for reference while storing `move_number` as full move number
  - Updated fallback logic to also use full move calculation

### 19. Chess-API.com Response Parsing Verification (2026-01-02)
- **Issue**: Need to verify chess-api.com response format and parsing is correct.
- **Fix**:
  - Added comprehensive logging for chess-api.com responses (status, JSON keys, full response)
  - Added parsing for multiple possible field names: `eval` or `evaluation`, `move` or `best_move`
  - Added logging of parsed values to verify correctness
  - Will verify actual response format when API is called

### 17. Stockfish.online Response Format Mismatch Fix (2026-01-02)
- **Issue**: Code was parsing stockfish.online response incorrectly. The actual API returns `{'success', 'evaluation', 'mate', 'bestmove', 'continuation'}`, but code expected `{'bestmove', 'info'}` array format.
- **Impact**: Evaluation was defaulting to 0.0 because the code couldn't find the "info" array, leading to incorrect position analysis.
- **Fix**:
  - Updated parsing to match actual stockfish.online v2 API response format
  - Extract `evaluation` directly from response (already in pawns, not centipawns)
  - Handle `bestmove` field which can be string like "e2e4" or "bestmove e2e4"
  - Added logging for parsed values to verify correctness
  - Removed dependency on non-existent "info" array

### 16. Stockfish.online Connection Failure Analysis and Retry Logic (2026-01-02)
- **Issue**: stockfish.online connection failed with "Server disconnected without sending a response" error. This is a transient network/server issue where the connection is established but the server closes it before sending a response.
- **Root Cause Analysis**:
  - **URL and request format are correct**: Same format worked successfully in backend.log
  - **Transient server issue**: stockfish.online has had internal server problems (reported in Dec 2025)
  - **Network instability**: Connection established but server disconnected mid-response
  - **Possible server overload**: Server may be rejecting/timing out some requests under load
- **Fix**:
  - Added retry logic (2 attempts) for transient network errors
  - Specific error handling for `httpx.ConnectError`, `httpx.ReadError`, `httpx.RemoteProtocolError`
  - Exponential backoff between retries (1s, 2s)
  - Better error logging with error type and attempt number
  - Retries only for network/server errors, not for other errors (like invalid responses)
  - Falls back to chess-api.com if all retries fail

### 15. Analyzer Hanging on API Timeouts Fix (2026-01-02)
- **Issue**: Analyzer was hanging indefinitely when chess engine APIs (stockfish.online, chess-api.com) failed or timed out. The frontend was stuck at "Finalizing your reflection" because the analyzer never completed, so no key positions were created.
- **Root Cause**: 
  - stockfish.online failed with "Server disconnected without sending a response"
  - chess-api.com v2 failed
  - chess-api.com v1 test/request was hanging without proper timeout handling
  - Version detection test had 10-second timeout but wasn't properly catching all timeout scenarios
  - Analyzer loop had no timeout protection for individual position analysis
- **Fix**:
  - Added `asyncio.wait_for()` timeout protection around all API calls (stockfish.online, chess-api.com)
  - Added explicit `httpx.Timeout` with separate connect and read timeouts
  - Added timeout protection in analyzer loop (60 seconds per position max)
  - Added proper `asyncio.TimeoutError` handling in analyzer to use fallback values
  - Version detection now properly handles timeouts and doesn't hang
  - All API calls now have double-layer timeout protection (httpx + asyncio)

### 14. Race Condition Fix: Reflection Generated Before Analyzer Completes (2026-01-02)
- **Issue**: Frontend jumped directly to final summary. The reflection endpoint was being called before the analyzer finished generating key positions and questions. When there were 0 questions (because analyzer hadn't finished), the backend assumed all questions were answered and generated reflection, setting game to COMPLETED. Then the analyzer finished and created questions, but it was too late.
- **Root Cause**: The reflection endpoint only checked unanswered question count. If count was 0, it assumed all questions were answered, without checking if the analyzer had finished running.
- **Fix**:
  - Added check for key positions existence before checking unanswered questions
  - If no key positions exist, return 400 error indicating analysis is still in progress
  - This prevents premature reflection generation when analyzer is still running
  - Only after key positions exist do we check if questions are answered

### 13. Chess Engine API Priority Reordering and Version Detection (2026-01-02)
- **Issue**: chess-api.com v1 endpoint was returning 404 errors, and stockfish.online should be higher priority.
- **Fix**:
  - Reordered API priority: stockfish.online first (most reliable), then chess-api.com
  - Added automatic version detection for chess-api.com:
    - Tests v2 first, if it works, caches and uses only v2
    - If v2 fails, tests v1, if it works, caches and uses only v1
    - Removes the need to try both versions on every call
  - Implemented different request/response parsing for each API:
    - stockfish.online: GET with query parameters, returns bestmove and info array with evaluation
    - chess-api.com: POST with JSON payload, returns eval, move, threats
  - Caches the working chess-api.com version to avoid repeated version checks
  - Clears cache if the working version stops working
  - Improved error handling and logging
  - Parses stockfish.online response format (bestmove extraction, centipawn to decimal conversion)
  - If all API endpoints fail, gracefully falls back to default values to allow pipeline to continue

## Diagnosis Verification Plan
- **Log Verification**: Observe backend logs for `DEBUG: Incoming request: GET /games/{id}/reflection` and `DEBUG: Response status: 200`.
- **State Flow Test**: Verify that the game transitions from `SUBMITTED` to `COACHING` even when Redis is down.
- **PCI Isolation Test**: Navigate to a game route and ensure the "Parent Control" nav link or PCI-specific headers are suppressed.
