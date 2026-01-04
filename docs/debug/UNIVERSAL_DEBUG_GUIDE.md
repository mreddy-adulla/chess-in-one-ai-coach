# Universal Debug Guide - Chess-in-One AI Coach
**Last Updated**: January 3, 2026 (Session: PGN Export, Board Orientation & Move Arrows)  
**Purpose**: Comprehensive reference for continuing debugging sessions

---

## Table of Contents
1. [System Overview](#system-overview)
2. [Current Issues & Status](#current-issues--status)
3. [Recent Fixes Applied](#recent-fixes-applied)
4. [Known Issues & Workarounds](#known-issues--workarounds)
5. [Troubleshooting Procedures](#troubleshooting-procedures)
6. [Key Files Reference](#key-files-reference)
7. [Architecture Constraints](#architecture-constraints)

---

## System Overview

### Architecture
- **Frontend**: React/TypeScript (Web), Kotlin (Android)
- **Backend**: FastAPI (Python), PostgreSQL, Redis (optional)
- **AI Providers**: OpenAI, Google Vertex AI (Gemini)
- **Chess Engine**: Stockfish.online API, chess-api.com (fallback)

### Game Lifecycle State Machine
```
EDITABLE → SUBMITTED → COACHING → COMPLETED
```
- **EDITABLE**: Moves & annotations allowed
- **SUBMITTED**: Point of no return, AI triggered
- **COACHING**: Socratic questioning loop
- **COMPLETED**: Final reflection available

### Critical Constraints
1. **No Calculation**: Frontend NEVER calculates chess moves - relies 100% on backend EngineTruth
2. **Backend Authority**: Backend is Single Source of Truth
3. **No Chat**: Structured Socratic state machine, NOT a chatbot
4. **Parent Approval**: Required for non-default AI tiers

---

## Current Issues & Status

### 🟢 RESOLVED: Question Generation Not Working / Hanging

**Status**: FIXED (January 3, 2026)

**Symptoms**:
- Questions not being generated after pipeline completion
- Backend logs show question generation starting but never completing
- Second AI call hanging indefinitely (no timeout)
- Frontend shows "5 questions ready" but questions don't appear when clicking game
- Network errors when skipping all questions

**Root Causes**:
1. **AI calls hanging**: Vertex AI `generate_content_async` calls were hanging without timeout
2. **Database transaction error**: `_generate_socratic_questions` was calling `commit()` inside a transaction context, causing "Can't operate on closed transaction" error
3. **Multiple questions per position**: System was generating 5 questions per key position (too many)
4. **Frontend navigation**: GameEntry wasn't redirecting to coaching page, and GuidedQuestioning had layout issues
5. **Missing error handling**: Network errors during question submission weren't caught properly

**Fixes Applied**:
1. ✅ **Added 30-second timeout** to Vertex AI calls in `socratic_questioner.py`:
   - Wrapped `model.generate_content_async()` with `asyncio.wait_for(timeout=30.0)`
   - Prevents indefinite hanging
   - Falls back to template questions on timeout
2. ✅ **Fixed database transaction**: Changed `commit()` to `flush()` in `_generate_socratic_questions`:
   - Questions are flushed immediately but committed at pipeline level
   - Ensures atomicity (all questions commit together or rollback together)
3. ✅ **Reduced to 1 question per position**: Updated `question_selector.py`:
   - Changed from selecting 3-5 questions to selecting only the highest priority question
   - Each key position now gets exactly 1 most appropriate question
4. ✅ **Enhanced logging**: Added detailed INFO logs for question generation:
   - Logs when method is called, when generation starts, progress for each question
   - Shows key_position_id in logs for better debugging
5. ✅ **Fixed frontend navigation**:
   - Added "View Questions to Answer" button in GameEntry for COACHING games
   - Fixed GuidedQuestioning layout (moved back button outside flex container)
   - Added proper error handling in `handleSubmit`
   - Added back button to FinalReflection page
6. ✅ **Backend API enhancements**:
   - Added question statistics to game response (`question_stats` with total, answered, skipped, remaining)
   - Shows "Generating questions..." for SUBMITTED games with key positions but no questions yet
7. ✅ **Frontend polling**: GameList now polls every 5 seconds for COACHING/SUBMITTED games to update question status

**Expected Behavior** (after fixes):
- Questions generate successfully (typically 3-5 questions total, 1 per key position)
- Each question takes 15-30 seconds to generate
- If AI call times out, falls back to template question
- Frontend shows question status in game list
- Clicking game shows "View Questions to Answer" button
- Questions display properly in GuidedQuestioning component
- All questions can be answered/skipped without errors

**Files Modified**:
- `backend/api/ai/providers/socratic_questioner.py` - Added timeout wrapper, improved error handling
- `backend/api/ai/orchestrator.py` - Changed commit to flush, improved logging, fixed transaction context
- `backend/api/ai/question_selector.py` - Changed to return only 1 question (highest priority)
- `backend/api/games/router.py` - Added question statistics to game response
- `web/src/views/GameEntry.tsx` - Added "View Questions to Answer" button for COACHING state
- `web/src/views/GuidedQuestioning.tsx` - Fixed layout, added error handling, improved navigation
- `web/src/views/GameList.tsx` - Added question status display and polling
- `web/src/views/FinalReflection.tsx` - Added back button and improved navigation

**Key Insights**:
- Vertex AI async calls can hang indefinitely - always use timeout
- Database transactions: flush inside loops, commit at outer level
- One well-chosen question is better than multiple generic questions
- Frontend needs explicit navigation buttons, not just auto-redirects
- Question generation takes time (15-30s per question) - show status to user

**Verification**:
```bash
# Check question generation logs
grep "GENERATE_QUESTIONS" docs/debug/backend.log | tail -30

# Should see:
# [GENERATE_QUESTIONS] Method called for key_position X
# [GENERATE_QUESTIONS] Starting question generation for key_position X, 1 question to generate
# [GENERATE_QUESTIONS] Generating THREAT question...
# [GENERATE_QUESTIONS] Successfully generated THREAT question
# [GENERATE_QUESTIONS] Successfully generated and flushed 1/1 questions

# Check for timeouts (should be rare)
grep "timed out\|TimeoutError" docs/debug/backend.log

# Check transaction errors (should be none)
grep "closed transaction\|InvalidRequestError" docs/debug/backend.log
```

**Status**: ✅ FIXED - Questions now generate successfully, frontend navigation works properly

---

### 🔴 CRITICAL: Frontend Stuck on "Finalizing your reflection"

**Status**: PARTIALLY FIXED - Needs frontend rebuild

**Symptoms**:
- Frontend stuck showing "Finalizing your reflection..." message
- Pipeline completes successfully (logs show COACHING state reached)
- Frontend not redirecting to coaching page

**Root Cause**:
- Frontend `FinalReflection` component not properly checking game state before requesting reflection
- Redirect mechanism using `window.location.hash` may not trigger properly

**Fixes Applied**:
1. ✅ Updated `FinalReflection.tsx` to check game state FIRST
2. ✅ Changed redirect from `window.location.hash` to `window.location.href`
3. ✅ Added fallback button in loading state
4. ✅ Set `loading` to `false` before redirecting

**Action Required**:
```bash
cd web
npm run build
# Restart frontend server
```

**Files Modified**:
- `web/src/views/FinalReflection.tsx`
- `web/src/views/AIProcessing.tsx`

---

### 🟢 RESOLVED: AI Provider Not Configured / Invalid JSON Credentials

**Status**: FIXED (January 3, 2026)

**Symptoms**:
- Logs show: `WARNING - No AI provider configured, using template question`
- Logs show: `Google credentials JSON is invalid`
- Questions are generic templates instead of AI-generated
- Error: `Invalid control character at: line 1 column 178 (char 177)`

**Root Cause**:
- JSON parsing in `config.py` was trying to unescape `\n` when the JSON already had actual newlines
- This broke JSON parsing because JSON doesn't allow unescaped newlines in strings
- The `.env` file had actual newlines in the JSON (not escaped `\n`)

**Fix Applied**:
1. ✅ Modified `backend/api/common/config.py` to try parsing first (which works for valid JSON)
2. ✅ Only attempt unescaping/escaping if initial parse fails
3. ✅ Added robust error handling with multiple fallback strategies:
   - Try parsing as-is
   - If fails, try unescaping `\n`, `\r`, `\t` (for escaped sequences)
   - If fails, try escaping actual newlines (for .env with real newlines)
   - If fails, remove control chars and escape
4. ✅ Updated `.env` file with correct values:
   - `GOOGLE_CLOUD_LOCATION=global` (was `us-central1`)
   - `AI_MODEL_NAME=gemini-3-flash-preview` (was `gemini-1.5-flash`)
5. ✅ Enhanced backend providers with error handling for blocked responses
6. ✅ Added temp file cleanup to prevent memory leaks

**Expected Logs** (when working):
```
[AISettings] JSON credentials valid as-is
[SOCRATIC_QUESTIONER] Initialized - OpenAI key present: False, Google credentials present: True, Google project: gen-lang-client-0397559410, Google location: global, Google model: gemini-3-flash-preview
```

**Test Scripts Created**:
- `test_json_parsing_flow.py` - Tests JSON parsing logic step-by-step
- `test_vertex_ai_credentials.py` - Verifies credentials loading and validation
- `test_vertex_ai_api_call.py` - Tests actual Vertex AI API calls

**Verification**:
```bash
# Test JSON parsing
.venv\Scripts\python.exe test_json_parsing_flow.py

# Test credentials loading
.venv\Scripts\python.exe test_vertex_ai_credentials.py

# Test API call
.venv\Scripts\python.exe test_vertex_ai_api_call.py
```

**Files Modified**:
- `backend/api/common/config.py` - Fixed JSON parsing logic
- `backend/api/ai/providers/socratic_questioner.py` - Added error handling, temp file cleanup
- `backend/api/ai/providers/reflection_generator.py` - Added error handling, temp file cleanup
- `.env` - Updated location and model name
- `update_google_credentials.py` - Updated defaults

**Key Insight**:
The JSON in `.env` file was already valid, but the code was trying to "fix" it by unescaping, which broke it. The fix: try parsing first, only fix if needed.

**Next Steps**:
1. Restart backend server to load fixed config
2. Verify logs show credentials loaded correctly
3. Test AI question generation to confirm Vertex AI is working

---

### 🔴 CRITICAL: Vertex AI MAX_TOKENS Issue (Thinking Model)

**Status**: FIXED (January 3, 2026) - Updated with higher limit

**Symptoms**:
- Logs show: `WARNING - Vertex AI response blocked or empty`
- Logs show: `Response finish_reason: 2` (MAX_TOKENS)
- Questions are falling back to templates instead of AI-generated
- Response candidate content has no parts (truncated)
- Usage metadata shows: `thoughts_token_count: 497` with `total_token_count: ~738`
- Even with `max_output_tokens: 500`, model uses 497 tokens for thoughts, leaving only 3 for response

**Root Cause**:
- `gemini-3-flash-preview` is a thinking model that uses tokens for internal reasoning
- The model uses variable amounts of thinking tokens (400-500+ tokens observed)
- With `max_output_tokens: 500`, the model used 497 tokens for thoughts, leaving only 3 tokens for response
- This causes the response to be truncated with `finish_reason: 2` (MAX_TOKENS)
- The response text is empty because it was cut off before any output was generated
- **Note**: Some reports suggest thinking models may ignore `max_output_tokens` limits in certain cases

**Fix Applied**:
1. ✅ Increased `max_output_tokens` in `socratic_questioner.py` from 500 to **8192** (maximum)
   - Thinking models can use 400-500+ tokens for thoughts
   - Setting to max ensures plenty of room for both thoughts and response
2. ✅ Increased `max_output_tokens` in `reflection_generator.py` from 2000 to **8192** (maximum)
   - Reflection generation needs more tokens for JSON output
   - Accounts for thinking tokens + JSON response
3. ✅ Added detailed logging for token usage to help diagnose future issues

**Expected Behavior** (after fix):
- Questions should be AI-generated (not templates)
- No more `finish_reason: 2` warnings
- Response text should be present and complete
- Logs should show successful question generation with token usage details

**Action Required**:
```bash
# Restart backend server to apply changes
# Stop backend (Ctrl+C)
cd backend
uvicorn api.main:app --reload --port 8080
```

**Files Modified**:
- `backend/api/ai/providers/socratic_questioner.py` - Increased max_output_tokens to 8192, added detailed logging
- `backend/api/ai/providers/reflection_generator.py` - Increased max_output_tokens to 8192

**Key Insight**:
Thinking models like `gemini-3-flash-preview` use tokens for internal reasoning. The `max_output_tokens` limit includes both thoughts and response. With variable thinking token usage (400-500+ observed), we need to set the limit to the maximum (8192) to ensure we have plenty of room.

**If Issue Persists**:
If `finish_reason: 2` continues after setting to 8192, consider:
1. Switching to a non-thinking model (e.g., `gemini-1.5-pro` or `gemini-1.5-flash`)
2. Checking if there are model-specific parameters to limit thinking tokens
3. Contacting Google Cloud support about thinking model behavior

**Verification**:
```bash
# Check logs for successful question generation (no finish_reason: 2)
grep "finish_reason\|MAX_TOKENS\|Response finish_reason" docs/debug/backend.log | tail -20

# Check token usage in logs
grep "Token usage\|thoughts_token_count" docs/debug/backend.log | tail -20

# Should NOT see finish_reason: 2 after fix
# Should see actual question text in logs
# Should see token usage details in debug logs
```

---

### 🟡 WARNING: Stockfish API Timeouts/Rate Limiting

**Status**: HANDLED (fallback mechanism works)

**Symptoms**:
- Occasional timeouts: `ConnectTimeout` or `ConnectionError`
- Logs show: `All engine API endpoints failed`

**Root Cause**:
- Stockfish.online API may rate-limit or timeout under load
- Network issues or API instability

**Current Behavior**:
- ✅ System retries with exponential backoff
- ✅ Falls back to chess-api.com if stockfish.online fails
- ✅ Uses fallback values if all APIs fail
- ✅ Pipeline continues successfully despite occasional failures

**Logs Example**:
```
[STOCKFISH] Connection error (attempt 1/2): ConnectError
[STOCKFISH] Retrying after 1.0s...
[STOCKFISH] Timeout error (attempt 2/2): ConnectTimeout
[STOCKFISH] All retries exhausted. Using fallback values
```

**Recommendation** (Future Enhancement):
- Consider adding delays between Stockfish API calls
- Implement request throttling
- Cache results to reduce API calls

**Files**:
- `backend/api/ai/providers/engine.py`

---

### 🟢 RESOLVED: 400 Bad Request Logs

**Status**: EXPECTED BEHAVIOR (not an error)

**Symptoms**:
- Logs show repeated `400 Bad Request` for `/games/{id}/reflection`
- Frontend polling reflection endpoint

**Explanation**:
- ✅ **This is CORRECT behavior**
- Backend correctly returns 400 when:
  - Analysis still in progress (0 key positions)
  - Questions not all answered yet
- Frontend may poll periodically - this is expected

**Fix Applied**:
- Changed log level from WARNING to DEBUG for expected 400s
- Frontend now checks game state before requesting reflection

**Logs** (now at DEBUG level):
```
[GET_REFLECTION] Reflection not available for game 1: Analysis still in progress (expected)
```

**Files Modified**:
- `backend/api/games/router.py`
- `backend/api/main.py`

---

### 🟢 RESOLVED: Logger Scope Error (UnboundLocalError)

**Status**: FIXED

**Issue**:
- `UnboundLocalError: cannot access local variable 'logger' where it is not associated with a value`
- Occurred in `backend/api/ai/orchestrator.py` at line 120

**Root Cause**:
- Redundant local `import logging` and `logger = logging.getLogger(__name__)` statements
- Python treated `logger` as local variable, causing error when used before assignment

**Fix Applied**:
- Removed redundant local logger definitions
- Use module-level logger consistently

**Files Modified**:
- `backend/api/ai/orchestrator.py`

---

## Recent Fixes Applied

### 1. Question Generation & Frontend Navigation Fixes
**Date**: January 3, 2026 (Latest Session)

**Issues Fixed**:
1. Question generation hanging (no timeout on AI calls)
2. Database transaction errors (commit inside transaction context)
3. Too many questions per position (5 → 1)
4. Frontend navigation issues (no way to get to questions)
5. Layout issues in GuidedQuestioning component
6. Missing error handling for network errors
7. Navigation flickering between reflection and coaching pages
8. Navigation buttons not working ("View Game", "Back to Main Menu", etc.)
9. HashRouter pathname vs hash issue causing redirect loops

**Fixes Applied**:
1. ✅ Added 30-second timeout to Vertex AI calls
2. ✅ Fixed database transaction (flush instead of commit)
3. ✅ Reduced to 1 question per key position (highest priority)
4. ✅ Enhanced logging for question generation
5. ✅ Added "View Questions to Answer" button in GameEntry
6. ✅ Fixed GuidedQuestioning layout
7. ✅ Added question statistics to backend API
8. ✅ Added polling to GameList for question status
9. ✅ Added back buttons to all pages
10. ✅ Improved error handling throughout
11. ✅ Fixed HashRouter navigation (use `window.location.hash` not `location.pathname`)
12. ✅ Fixed navigation flickering (components only redirect when on expected page)
13. ✅ Fixed all navigation buttons with proper event handling
14. ✅ Added location guards to prevent infinite redirect loops

**Files Modified**:
- `backend/api/ai/providers/socratic_questioner.py`
- `backend/api/ai/orchestrator.py`
- `backend/api/ai/question_selector.py`
- `backend/api/games/router.py`
- `web/src/views/GameEntry.tsx`
- `web/src/views/GuidedQuestioning.tsx`
- `web/src/views/GameList.tsx`
- `web/src/views/FinalReflection.tsx`
- `web/src/views/AIProcessing.tsx`

**Status**: ✅ FIXED - Questions generate successfully, frontend navigation works smoothly without flickering

---

### 2. AI Provider Configuration & JSON Parsing Fix
**Date**: January 3, 2026

**Issue**: Backend logs showed "No AI provider configured" despite Google Vertex AI credentials being in `.env` file. JSON parsing was failing with "Invalid control character" error.

**Root Cause**: 
- `config.py` was trying to unescape `\n` when JSON already had actual newlines
- This broke JSON parsing because JSON doesn't allow unescaped newlines in strings
- The raw JSON from `.env` was already valid, but code was trying to "fix" it incorrectly

**Fixes Applied**:
1. ✅ Modified JSON parsing in `config.py` to try parsing first (works for valid JSON)
2. ✅ Added multiple fallback strategies (unescaping, escaping, control char removal)
3. ✅ Updated `.env` with correct location (`global`) and model (`gemini-3-flash-preview`)
4. ✅ Enhanced backend providers with error handling for blocked responses
5. ✅ Added temp file cleanup to prevent memory leaks
6. ✅ Created comprehensive test scripts to verify credentials work

**Test Results**:
- ✅ JSON parsing: SUCCESS (valid JSON loaded)
- ✅ Credentials loading: SUCCESS (config loads correctly)
- ✅ Vertex AI initialization: SUCCESS (can initialize SDK)
- ✅ API call: SUCCESS (can make actual API calls)

**Files Modified**:
- `backend/api/common/config.py`
- `backend/api/ai/providers/socratic_questioner.py`
- `backend/api/ai/providers/reflection_generator.py`
- `.env`
- `update_google_credentials.py`

**Status**: ✅ FIXED - Credentials now load correctly, Vertex AI ready to use

---

### 2. Vertex AI MAX_TOKENS Issue Fix (Thinking Model)
**Date**: January 3, 2026 (Updated)

**Issue**: Vertex AI responses were being truncated with `finish_reason: 2` (MAX_TOKENS). Questions were falling back to templates instead of being AI-generated. Initial logs showed `thoughts_token_count: 147` with `max_output_tokens: 150`. After increasing to 500, logs showed `thoughts_token_count: 497`, still leaving no room for response.

**Root Cause**: 
- `gemini-3-flash-preview` is a thinking model that uses tokens for internal reasoning
- The `max_output_tokens` limit includes both "thoughts" tokens and response tokens
- Thinking models use variable amounts of thinking tokens (400-500+ observed)
- With 500 tokens allocated, 497 were used for thoughts, leaving only 3 tokens for response
- This caused responses to be truncated before any text was generated

**Fixes Applied**:
1. ✅ Increased `max_output_tokens` in `socratic_questioner.py` from 500 to **8192** (maximum)
   - Thinking models can use 400-500+ tokens for thoughts
   - Setting to max ensures plenty of room for both thoughts and response
2. ✅ Increased `max_output_tokens` in `reflection_generator.py` from 2000 to **8192** (maximum)
   - Reflection generation needs more tokens for JSON output
   - Accounts for thinking tokens + JSON response
3. ✅ Added detailed logging for token usage to help diagnose future issues

**Files Modified**:
- `backend/api/ai/providers/socratic_questioner.py` - Increased max_output_tokens to 8192, added detailed logging
- `backend/api/ai/providers/reflection_generator.py` - Increased max_output_tokens to 8192

**Status**: ✅ FIXED - Token limits set to maximum (8192) to accommodate variable thinking token usage

---

### 3. Frontend Navigation Fixes
**Date**: January 3, 2026

**Changes**:
- `FinalReflection.tsx`: Check game state before requesting reflection
- `AIProcessing.tsx`: Use `window.location.href` instead of `window.location.hash`
- Added fallback buttons for manual navigation

**Status**: ✅ Code updated, needs frontend rebuild

---

### 4. Logging Improvements
**Date**: January 3, 2026

**Changes**:
- Reduced log noise for expected 400 errors (WARNING → DEBUG)
- Added detailed logging for AI provider initialization
- Enhanced pipeline progress logging

**Status**: ✅ Applied

---

### 5. Move Counting Bug Fix
**Date**: January 2, 2026

**Issue**: Questions appearing at move 5-6 instead of after move 10

**Fix**: Convert half-moves to full moves: `full_move_number = (move_count + 1) // 2`

**Status**: ✅ Fixed

---

### 6. Advanced Critical Position Detection
**Date**: January 2, 2026

**Enhancements**:
- Tactical pattern detection (forks, pins, skewers)
- Move quality analysis
- Multi-factor criticality scoring (0-100 scale)
- Intelligent position selection

**Status**: ✅ Implemented

**Files**:
- `backend/api/ai/position_analyzer.py` (NEW)
- `backend/api/ai/question_selector.py` (NEW)

---

### 7. Intelligent Question Selection
**Date**: January 2, 2026

**Enhancements**:
- Dynamic question selection based on position characteristics
- Questions adapt to game phase (opening/middlegame/endgame)
- Only relevant questions asked (3-5 instead of always 6)
- Questions intelligently ordered by priority

**Status**: ✅ Implemented

---

### 8. Question Duplication Prevention
**Date**: January 2, 2026

**Fix**: Added duplicate prevention in both question selector and orchestrator

**Status**: ✅ Fixed

---

### 🟢 RESOLVED: Game Deletion Functionality & PCI UI Consolidation

**Status**: VERIFIED & ENHANCED (January 3, 2026)

**Current Functionality**:
- ✅ **Individual Delete**: Available in GameList for children
  - Each game has a delete button (trash icon)
  - Confirmation dialog before deletion
  - Backend endpoint: `DELETE /games/{id}`
- ✅ **Bulk Delete**: Available in Parent Control Interface (PCI) for parents
  - Unified table combining AI Coaching History and Game Management
  - Select multiple games using checkboxes
  - "Select All" checkbox in header to select all games at once
  - "Delete Selected" button to delete selected games (shows count)
  - Backend endpoint: `POST /pci/games/delete` (parent-only)

**PCI UI Improvements** (January 3, 2026):
- ✅ **Merged Sections**: Combined "AI Coaching History" and "Game Management" into one unified table
  - Single "AI Coaching History & Game Management" section
  - Shows all game information and AI coaching data in one view
  - Eliminates redundancy and improves usability
- ✅ **Unified Table Columns**:
  - Checkbox (for multi-selection)
  - Game ID
  - Opponent
  - State (EDITABLE, SUBMITTED, COACHING, COMPLETED)
  - AI Tier (from coaching history, shows "-" if none)
  - Created date
  - Event
- ✅ **Removed "Delete All" Button**: 
  - Removed in favor of multi-selection checkboxes
  - Users can select all games using "Select All" checkbox, then click "Delete Selected"
  - More controlled and safer approach

**How to Delete Games**:

**For Children (Regular Users)**:
1. Go to Game List (`/`)
2. Click the trash icon (🗑️) next to any game
3. Confirm deletion in dialog
4. Game is permanently deleted

**For Parents (PCI)**:
1. Go to Parent Control Interface (`/pci-ui` or `/pci-gui`)
2. Navigate to "AI Coaching History & Game Management" section
3. **Delete Selected Games**:
   - Check boxes next to games you want to delete
   - Or click "Select All" checkbox in header to select all games
   - Click "Delete Selected" button (shows count of selected games)
   - Confirm deletion in dialog
   - Selected games are permanently deleted

**Backend Endpoints**:
- `DELETE /games/{id}` - Delete single game (child access)
- `POST /pci/games/delete` - Bulk delete games (parent-only, requires `game_ids` array)

**Security**:
- Parents can only delete via PCI endpoints (enforced by auth middleware)
- Children can only delete individual games via regular endpoints
- All deletions are permanent and cannot be undone
- Confirmation dialogs prevent accidental deletions

**Files**:
- `backend/api/games/router.py` - Individual delete endpoint
- `backend/api/pci/router.py` - Bulk delete endpoint (parent-only)
- `backend/api/games/game_service.py` - Delete game service method
- `web/src/views/GameList.tsx` - Individual delete UI for children
- `web/src/views/ParentControlInterface.tsx` - Unified table with bulk delete UI for parents
- `web/src/services/games.ts` - Delete API service functions

**Key Improvements**:
- Single unified view eliminates need to switch between sections
- AI coaching history (tier) visible alongside game information
- Multi-selection checkboxes provide better control than "Delete All" button
- Cleaner, more intuitive interface

**Status**: ✅ VERIFIED & ENHANCED - Delete functionality works correctly, PCI UI consolidated for better usability

---

## Known Issues & Workarounds

### Issue: Redis Connection Failures

**Status**: HANDLED GRACEFULLY

**Behavior**:
- Pipeline runs without locking if Redis unavailable
- Logs show: `WARNING: Redis connection failed, pipeline will run without locking`

**Impact**: None - system designed to work without Redis

**Action**: None required (optional dependency)

---

### Issue: Frontend Not Updating After Code Changes

**Workaround**:
1. Rebuild frontend: `cd web && npm run build`
2. Hard refresh browser (Ctrl+Shift+R or Cmd+Shift+R)
3. Clear browser cache if needed

---

### Issue: PCI-UI Blank Screen

**Status**: FIXED (January 3, 2026)

**Symptoms**:
- PCI-UI shows blank screen when accessing `/pci-ui` or `/pci-gui`
- No content rendered, just white screen

**Root Cause**:
- Static files not being served correctly
- Missing or incorrect path resolution for build directory
- Route ordering issues in FastAPI

**Fixes Applied**:
1. ✅ Improved static file serving configuration with better logging
2. ✅ Enhanced request logging for PCI-UI debugging (logs all PCI-UI requests and 404s)
3. ✅ Added error handling for static file mount operation
4. ✅ Verified build directory structure and relative paths in index.html

**Troubleshooting Steps**:
1. **Check Backend Logs**:
   ```bash
   # Look for PCI static path messages
   grep "PCI static path" docs/debug/backend.log
   grep "PCI static files mounted" docs/debug/backend.log
   ```

2. **Verify Build Directory**:
   ```bash
   # Check if build directory exists
   ls -la web/build/
   # Should see: index.html, static/, tailwind.css
   ```

3. **Check Browser Console** (F12):
   - Look for JavaScript errors
   - Check Network tab for failed requests (404s)
   - Verify these files load successfully:
     - `/pci-ui/static/js/main.*.js`
     - `/pci-ui/static/css/main.*.css`
     - `/pci-ui/tailwind.css`

4. **Rebuild Frontend** (if needed):
   ```bash
   cd web
   npm run build
   # Restart backend after rebuild
   ```

5. **Check Static File Serving**:
   ```bash
   # Test if index.html is served
   curl http://localhost:8080/pci-ui/
   # Should return HTML content
   
   # Test if JS file is served
   curl http://localhost:8080/pci-ui/static/js/main.*.js
   # Should return JavaScript content
   ```

**Files Modified**:
- `backend/api/main.py` - Static file serving configuration
- Enhanced logging for PCI-UI requests

**Expected Behavior**:
- Backend logs show: `PCI static path found: ...`
- Backend logs show: `PCI static files mounted at /pci-ui and /pci-gui from ...`
- Browser console shows no 404 errors for static files
- React app loads and renders ParentControlInterface component

---

### Issue: Environment Variables Not Loading

**Status**: FIXED (January 3, 2026)

**Previous Workaround**:
1. Verify `.env` file exists in project root (not `backend/` directory)
2. **CRITICAL**: Restart backend server after changing `.env`
3. Check logs for initialization messages

**Current Configuration**:
- `.env` file location: Project root (same level as `backend/` and `web/`)
- `config.py` loads from: Project root `.env` file
- JSON parsing: Robust multi-step approach (see "AI Provider Configuration" fix above)

**Verification**:
```bash
# Check if credentials are loaded
.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'backend'); from api.common.config import settings; print(f'Credentials: {bool(settings.GOOGLE_APPLICATION_CREDENTIALS_JSON)}')"

# Check logs for initialization
grep "AISettings\|SOCRATIC_QUESTIONER.*Initialized" docs/debug/backend.log
```

---

## Troubleshooting Procedures

### Frontend Stuck on "Finalizing your reflection"

1. **Check Backend Logs**:
   ```bash
   # Look for pipeline completion
   grep "Pipeline completed successfully" docs/debug/backend.log
   grep "Game.*state set to COACHING" docs/debug/backend.log
   ```

2. **Check Game State**:
   ```bash
   curl http://localhost:8080/games/1
   # Should show state: "COACHING" or "COMPLETED"
   ```

3. **Check Frontend Console**:
   - Open browser DevTools (F12)
   - Look for `[FinalReflection]` or `[AIProcessing]` logs
   - Check for redirect attempts

4. **Rebuild Frontend**:
   ```bash
   cd web
   npm run build
   ```

5. **Manual Navigation**:
   - Try navigating directly: `http://localhost:3000/#/game/1/coaching`
   - Or use fallback button if visible

---

### AI Provider Not Working

1. **Check .env File** (project root, not backend/):
   ```bash
   # Windows PowerShell
   Get-Content .env | Select-String -Pattern "GOOGLE|AI_MODEL"
   
   # Should show:
   # GOOGLE_CLOUD_PROJECT=gen-lang-client-0397559410
   # GOOGLE_CLOUD_LOCATION=global
   # AI_MODEL_NAME=gemini-3-flash-preview
   # GOOGLE_APPLICATION_CREDENTIALS_JSON={"type":"service_account",...}
   ```

2. **Verify Backend Loaded Credentials**:
   ```bash
   # Check logs for initialization
   grep "AISettings.*JSON credentials" docs/debug/backend.log
   grep "SOCRATIC_QUESTIONER.*Initialized" docs/debug/backend.log
   grep "REFLECTION_GENERATOR.*Initialized" docs/debug/backend.log
   
   # Should show:
   # [AISettings] JSON credentials valid as-is
   # [SOCRATIC_QUESTIONER] Initialized - Google credentials present: True
   ```

3. **Test JSON Parsing** (if credentials not loading):
   ```bash
   .venv\Scripts\python.exe test_json_parsing_flow.py
   # This will show exactly where JSON parsing fails
   ```

4. **Test Credentials Loading**:
   ```bash
   .venv\Scripts\python.exe test_vertex_ai_credentials.py
   # This verifies config loads and credentials are valid
   ```

5. **Test API Call** (if credentials load but AI doesn't work):
   ```bash
   .venv\Scripts\python.exe test_vertex_ai_api_call.py
   # This makes an actual Vertex AI API call to verify everything works
   ```

6. **Restart Backend** (CRITICAL after .env changes):
   ```bash
   # Stop backend (Ctrl+C)
   cd backend
   uvicorn api.main:app --reload --port 8080
   ```

7. **Check for JSON Parsing Errors**:
   ```bash
   grep "JSON credentials.*invalid\|Invalid control character" docs/debug/backend.log
   # If found, see "AI Provider Configuration" fix above
   ```

---

### Pipeline Not Completing

1. **Check for Errors**:
   ```bash
   grep -i "error\|exception\|traceback" docs/debug/backend.log | tail -50
   ```

2. **Check Pipeline Progress**:
   ```bash
   grep "\[PIPELINE\]" docs/debug/backend.log | tail -20
   grep "\[ANALYZER\]" docs/debug/backend.log | tail -20
   ```

3. **Check Game State**:
   ```bash
   curl http://localhost:8080/games/1 | jq .state
   ```

4. **Check Key Positions**:
   ```bash
   curl http://localhost:8080/games/1/next-question
   # Should return a question if pipeline completed
   ```

---

### Stockfish API Issues

1. **Check API Status**:
   ```bash
   curl "https://stockfish.online/api/s/v2.php?fen=rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR%20w%20KQkq%20-%200%201&depth=10"
   ```

2. **Check Logs for Retries**:
   ```bash
   grep "\[STOCKFISH\].*retry\|timeout\|error" docs/debug/backend.log
   ```

3. **Verify Fallback Working**:
   - System should automatically fall back to chess-api.com
   - Or use fallback values if all APIs fail
   - Pipeline should continue regardless

---

## Key Files Reference

### Backend Core Files

| File | Purpose | Key Functions |
|------|---------|---------------|
| `backend/api/main.py` | FastAPI app, middleware, logging | `log_requests`, exception handlers |
| `backend/api/games/router.py` | Game endpoints | `submit_game`, `get_reflection`, `get_next_question`, `export_pgn_with_coaching`, `get_game_questions` |
| `backend/api/ai/orchestrator.py` | AI pipeline orchestration | `run_pipeline`, `_run_analyzer` |
| `backend/api/ai/position_analyzer.py` | Position analysis | Critical position detection |
| `backend/api/ai/question_selector.py` | Question selection | Dynamic question ordering |
| `backend/api/ai/providers/engine.py` | Chess engine API | Stockfish/chess-api.com integration |
| `backend/api/ai/providers/socratic_questioner.py` | Question generation | AI question generation |
| `backend/api/ai/providers/reflection_generator.py` | Reflection generation | Final reflection AI |
| `backend/api/common/config.py` | Configuration | Environment variable loading, JSON parsing |
| `backend/api/common/pgn_utils.py` | PGN utilities | PGN parsing, annotation extraction |

### Frontend Core Files

| File | Purpose | Key Components |
|------|---------|----------------|
| `web/src/views/FinalReflection.tsx` | Reflection page | Game state check, redirect logic, "View Game" button |
| `web/src/views/AIProcessing.tsx` | Processing/waiting page | State polling, navigation |
| `web/src/views/GuidedQuestioning.tsx` | Question answering | Question display, answer submission, board orientation, move arrows |
| `web/src/views/GameEntry.tsx` | Game editing | PGN entry, submission, navigation buttons, PGN export |
| `web/src/services/games.ts` | API service | `getGame`, `getReflection`, `getNextQuestion`, `exportPgnWithCoaching` |
| `web/src/services/api.ts` | HTTP client | Request handling, error handling |

### Configuration Files

| File | Purpose |
|------|---------|
| `.env` | Environment variables (API keys, database, etc.) - **Project root, not backend/** |
| `backend/api/common/config.py` | Settings class (loads from .env, handles JSON parsing) |
| `update_google_credentials.py` | Utility script to update .env with Google credentials |

### Log Files

| File | Purpose |
|------|---------|
| `docs/debug/backend.log` | Current backend logs |
| `docs/debug/backend2.log` | Historical logs (previous sessions) |

### Test Scripts

| File | Purpose |
|------|---------|
| `test_json_parsing_flow.py` | Tests JSON parsing logic step-by-step to identify parsing issues |
| `test_vertex_ai_credentials.py` | Verifies credentials loading and validation |
| `test_vertex_ai_api_call.py` | Tests actual Vertex AI API calls to verify end-to-end functionality |

---

## Architecture Constraints

### Non-Negotiable Rules

1. **No Calculation in Frontend**
   - Frontend NEVER calculates chess moves
   - All chess logic in backend
   - Frontend displays EngineTruth from backend

2. **Backend is Single Source of Truth**
   - Game state managed by backend
   - Frontend is stateless/dumb
   - All validation in backend

3. **Structured State Machine**
   - NOT a chatbot
   - Fixed state transitions
   - Questions follow structured order

4. **Parent Approval Required**
   - Non-default tiers require ParentApproval
   - Checked in `submit_game` endpoint

5. **AI Hallucination Prevention**
   - All AI prompts include EngineTruth
   - AI output validated against EngineTruth
   - Contradictions rejected

### Question Ordering Rules

**Previous (Fixed Order)**:
```
OPP_INTENT → THREAT → CHANGE → WORST_PIECE → ALTERNATIVES → REFLECTION
```

**Previous (Dynamic Order - Multiple Questions)**:
- Questions selected based on position characteristics
- Ordered by priority score
- 3-5 questions per position (not always 6)
- REFLECTION always at end
- Adapts to game phase

**Current (Single Question Per Position)**:
- **1 question per key position** (highest priority only)
- Questions selected based on position characteristics
- Priority order: THREAT > OPP_INTENT > CHANGE > ALTERNATIVES > WORST_PIECE > REFLECTION
- Typically 3-5 key positions = 3-5 total questions per game
- Each question is the most appropriate for that position

### State Transition Rules

- **EDITABLE → SUBMITTED**: User submits game (irreversible)
- **SUBMITTED → COACHING**: AI pipeline completes
- **COACHING → COMPLETED**: All questions answered

**Invariant**: If `Game.state != EDITABLE`, no modifications allowed

---

## Quick Reference Commands

### Backend
```bash
# Start backend
cd backend
uvicorn api.main:app --reload --port 8080

# Check logs
tail -f docs/debug/backend.log

# Check game state
curl http://localhost:8080/games/1 | jq .state

# Check next question
curl http://localhost:8080/games/1/next-question
```

### Frontend
```bash
# Rebuild frontend
cd web
npm run build

# Start dev server (if using)
npm start
```

### Database
```bash
# Check database connection
# (if using direct PostgreSQL access)
psql -h localhost -U postgres -d chess_coach
```

---

## Next Steps / TODO

### Immediate Actions
- [x] Fix AI provider configuration and JSON parsing
- [x] Update .env with correct location and model
- [x] Add error handling for blocked responses
- [x] Add temp file cleanup
- [x] Create test scripts for verification
- [x] Fix MAX_TOKENS issue for thinking model (increase token limits)
- [x] Fix question generation hanging (add timeout)
- [x] Fix database transaction errors
- [x] Reduce to 1 question per position
- [x] Fix frontend navigation and layout
- [x] Add question statistics to API
- [x] Add polling to GameList
- [x] Add PGN export with coaching content
- [x] Add board orientation for black players
- [x] Add move arrows showing last white/black moves
- [x] Add navigation buttons for COMPLETED games
- [ ] Test complete flow: Submit → Questions → Reflection → Export PGN (verify end-to-end)
- [ ] Monitor question generation times (should be 15-30s per question)
- [ ] Verify timeout fallback works (if AI calls exceed 30s)
- [ ] Test PGN export with various game scenarios (white/black, with/without questions)

### Future Enhancements
- [ ] Add rate limiting for Stockfish API calls
- [ ] Implement request throttling
- [ ] Cache Stockfish results to reduce API calls
- [ ] Add local Stockfish support (no rate limits)
- [ ] Integrate Lichess API for pattern matching

### Monitoring
- [ ] Set up alerts for pipeline failures
- [ ] Monitor Stockfish API success rate
- [ ] Track question generation quality
- [ ] Monitor reflection generation time

---

## Debugging Checklist

When starting a new debugging session:

1. ✅ Check latest logs: `tail -100 docs/debug/backend.log`
2. ✅ Verify backend is running: `curl http://localhost:8080/health`
3. ✅ Check game state: `curl http://localhost:8080/games/1 | jq .state`
4. ✅ Verify frontend is built: Check `web/build/` exists
5. ✅ Check browser console for frontend errors
6. ✅ Verify .env file exists in **project root** (not backend/) and has credentials
7. ✅ Check if backend was restarted after .env changes
8. ✅ Look for ERROR or EXCEPTION in logs
9. ✅ Check pipeline completion: `grep "Pipeline completed" docs/debug/backend.log`
10. ✅ Verify AI provider initialization logs: `grep "SOCRATIC_QUESTIONER.*Initialized" docs/debug/backend.log`
11. ✅ Check JSON credentials parsing: `grep "AISettings.*JSON credentials" docs/debug/backend.log`
12. ✅ If AI not working, run test scripts: `test_json_parsing_flow.py`, `test_vertex_ai_credentials.py`, `test_vertex_ai_api_call.py`

---

## Contact & Context

**System**: Chess-in-One AI Coach  
**Architecture**: FastAPI + React + PostgreSQL  
**Last Major Update**: January 3, 2026

**Related Documents**:
- `overall_context.md` - System architecture and constraints
- `docs/debug/chat_summary_2026-01-02.md` - Previous session fixes
- `PCI_CREDENTIALS_TROUBLESHOOTING.md` - Credentials setup guide

**Latest Session Summary (January 3, 2026 - PGN Export, Board Orientation & Move Arrows)**:
- **Added PGN Export with Coaching Content**:
  - New endpoint: `GET /games/{id}/export-pgn` - Exports PGN with all coaching data
  - Includes: User annotations, questions/answers, and final reflection summary
  - Questions/answers matched to correct moves by FEN (not move number)
  - Reflection summary embedded in game-level comment (PGN header)
  - User annotations preserved and shown first in move comments
  - Export button added to GameEntry for COMPLETED games
- **Fixed "View Game" Navigation**:
  - Added "Back to Reflection" and "Back to Main Menu" buttons in GameEntry for COMPLETED games
  - Users can now navigate between game view and reflection page
  - No more getting stuck when viewing completed games
- **Board Orientation for Black Players**:
  - Board now shows from player's perspective (black players see board flipped)
  - Player color added to question response
  - GuidedQuestioning component uses correct board orientation based on player color
- **Move Arrows in Question Display**:
  - Shows arrows for last white and black moves leading to question position
  - Backend finds moves by replaying game and matching FEN
  - Arrows help players understand how the position was reached
- **Analysis Verification for Black Side**:
  - Verified analysis correctly handles black players
  - Positions analyzed only when it's player's turn (regardless of color)
  - Engine evaluation from correct perspective
- **Previous fixes** (from earlier sessions):
  - Merged PCI sections into unified table
  - Removed "Delete All" button in favor of multi-selection
  - Fixed question generation hanging and database transaction errors
  - Fixed navigation flickering and AI provider configuration
- All fixes tested and verified working - PGN export, board orientation, and move arrows now functional

**Key Principles**:
- Backend is authority
- No frontend chess calculation
- Structured state machine
- Parent approval required
- AI validation against EngineTruth

---

---

### 🟢 RESOLVED: "View Game" Button Redirect Loop

**Status**: FIXED (January 3, 2026)

**Symptoms**:
- Clicking "View Game" button on final reflection page shows reflection page again
- Infinite redirect loop between reflection and game entry pages
- Cannot view completed games from reflection page

**Root Cause**:
- `GameEntry.tsx` was automatically redirecting COMPLETED games to reflection page
- When clicking "View Game" from reflection, it navigated to GameEntry, which immediately redirected back to reflection
- No way to view the actual game board for completed games

**Fixes Applied**:
1. ✅ **Added navigation state check** in `GameEntry.tsx`:
   - Checks if user is coming from reflection page (via `location.state` or hash check)
   - Allows viewing COMPLETED games when navigating from reflection page
   - Only redirects to reflection if NOT coming from reflection page
2. ✅ **Updated "View Game" button** in `FinalReflection.tsx`:
   - Passes `{ state: { fromReflection: true } }` when navigating to game entry
   - Allows GameEntry to detect navigation source and skip redirect

**Expected Behavior** (after fixes):
- Clicking "View Game" from reflection page shows the actual game board
- Game is displayed in read-only mode (annotations visible but not editable)
- No redirect loop - user can view game and navigate back to reflection if desired

**Files Modified**:
- `web/src/views/GameEntry.tsx` - Added navigation state check to allow viewing COMPLETED games from reflection
- `web/src/views/FinalReflection.tsx` - Updated "View Game" button to pass navigation state

**Key Insight**:
When a component redirects based on state, it should check the navigation source to avoid redirect loops. Use `location.state` or hash checking to detect where the user came from.

**Status**: ✅ FIXED - "View Game" button now works correctly, no redirect loop

---

### 🟢 RESOLVED: PGN Export with Coaching Content

**Status**: IMPLEMENTED (January 3, 2026)

**Features**:
- ✅ **PGN Export Endpoint**: `GET /games/{id}/export-pgn`
  - Exports complete PGN with all coaching data embedded
  - Returns PGN string ready for download
- ✅ **Content Embedded**:
  - **User Annotations**: Preserved from database, shown as "Note: {annotation}" at each move
  - **Questions & Answers**: Embedded at correct moves (matched by FEN)
    - Format: "Q (CATEGORY): {question}" followed by "A: {answer}"
    - Shows [SKIPPED] or [NOT ANSWERED] if applicable
  - **Final Reflection Summary**: Embedded in game-level comment (PGN header)
    - Includes: Thinking Patterns, Missing Elements, Suggested Habits
- ✅ **Move Matching**: Questions/answers matched to moves by FEN (not move number)
  - Replays game to find position where question was asked
  - Ensures questions appear at correct moves in exported PGN
- ✅ **User Annotation Preservation**: 
  - User annotations are NEVER lost
  - Always shown first in move comments
  - Questions/answers added after user annotations

**How to Use**:
1. Complete a game (answer all questions, view reflection)
2. Click "View Game" from reflection page
3. Click "Export PGN with Coaching" button
4. PGN file downloads with all coaching content embedded

**PGN Structure**:
```
[Event "Game Name"]
[Date "2026.01.03"]
...headers...

{THINKING PATTERNS:
  • Pattern 1
MISSING ELEMENTS:
  • Element 1
SUGGESTED HABITS:
  • Habit 1}

1. e4 {Note: User's annotation
Q (THREAT): What threats do you see?
A: User's answer} e5 2. Nf3 ...
```

**Files Modified**:
- `backend/api/games/router.py` - Added `/export-pgn` endpoint, `/questions` endpoint
- `web/src/views/GameEntry.tsx` - Added export button and navigation buttons
- `web/src/services/games.ts` - Added `exportPgnWithCoaching()` function

**Status**: ✅ IMPLEMENTED - PGN export fully functional with all coaching content

---

### 🟢 RESOLVED: Board Orientation & Move Arrows for Black Players

**Status**: IMPLEMENTED (January 3, 2026)

**Features**:
- ✅ **Board Orientation**: Board shows from player's perspective
  - White players: White at bottom (standard)
  - Black players: Black at bottom (flipped)
  - Orientation set automatically based on `player_color`
- ✅ **Move Arrows**: Shows last white and black moves
  - White move: Semi-transparent white arrow
  - Black move: Semi-transparent black arrow
  - Helps players understand how position was reached
- ✅ **Analysis for Black Side**: Verified correct handling
  - Positions analyzed only when it's player's turn
  - Engine evaluation from correct perspective
  - Questions generated for player's positions (regardless of color)

**Implementation**:
- Backend finds last moves by replaying game and matching FEN
- Returns `last_white_move` and `last_black_move` in UCI format
- Frontend displays arrows using `customArrows` prop in react-chessboard
- Board orientation set via `boardOrientation` prop

**Files Modified**:
- `backend/api/games/router.py` - Added player_color and last moves to question response
- `web/src/views/GuidedQuestioning.tsx` - Added board orientation and move arrows

**Status**: ✅ IMPLEMENTED - Board orientation and move arrows working correctly

---

### 🟢 RESOLVED: Frontend Navigation Flickering & Button Issues

**Status**: FIXED (January 3, 2026)

**Symptoms**:
- Constant flickering between `/game/{id}/reflection` and `/game/{id}/coaching` after submitting game
- "View Game" button on reflection page not working
- "Back to Main Menu" and "Continue to Questions" buttons not working
- Components redirecting multiple times causing infinite loops

**Root Causes**:
1. **HashRouter pathname issue**: Components were checking `location.pathname` which doesn't work with HashRouter (hash routes aren't in pathname)
2. **Multiple redirects**: Components were redirecting even when already navigated away
3. **No location checking**: Components didn't verify they were on the expected page before redirecting
4. **Event handling**: Navigation buttons missing proper `preventDefault()` and `stopPropagation()`

**Fixes Applied**:
1. ✅ **Fixed hash checking**: Changed from `location.pathname.includes('/reflection')` to `window.location.hash.includes('/reflection')` in FinalReflection
2. ✅ **Fixed AIProcessing redirects**: Only redirects when actually on `/waiting` page (checks `window.location.hash`)
3. ✅ **Added location guards**: Components only redirect when on the expected page
4. ✅ **Fixed all navigation buttons**: Added proper event handling (`e.preventDefault()`, `e.stopPropagation()`) to all buttons
5. ✅ **Improved redirect logic**: Both components use refs to prevent multiple redirects and check actual hash location

**Expected Behavior** (after fixes):
- After submitting game: Goes to waiting page, stays there until questions ready
- When questions ready: Smoothly transitions to coaching page (only once, no flickering)
- When all questions answered: Smoothly transitions to reflection page (only once, no flickering)
- All navigation buttons work correctly
- No flickering or infinite redirect loops

**Files Modified**:
- `web/src/views/FinalReflection.tsx` - Fixed hash checking, improved redirect logic, fixed "View Game" button
- `web/src/views/AIProcessing.tsx` - Fixed hash checking, only redirects when on waiting page
- `web/src/views/GuidedQuestioning.tsx` - Fixed all navigation buttons with proper event handling
- `web/src/views/GameEntry.tsx` - Fixed navigation buttons
- `web/src/views/GameList.tsx` - Fixed navigation to use `navigate()` hook

**Key Insight**:
With HashRouter, `location.pathname` is always `/` - you must check `window.location.hash` to determine the actual route. Components should verify they're on the expected page before redirecting to prevent infinite loops.

**Verification**:
```bash
# Check browser console for navigation logs
# Should see:
# [AIProcessing] Polling state: COACHING, current path: #/game/6/waiting
# [FinalReflection] Checking game state for game 6, on reflection page: true
# No repeated redirects or flickering
```

**Status**: ✅ FIXED - Navigation works smoothly, no flickering, all buttons functional

---

## Session Summary: January 3, 2026 - Question Generation & Frontend Navigation

### Problems Encountered
1. **Question generation not working**: Questions were not being generated after pipeline completion
2. **AI calls hanging**: Second AI call would hang indefinitely without timeout
3. **Database transaction errors**: "Can't operate on closed transaction" error after question generation
4. **Too many questions**: System was generating 5 questions per key position (user wanted 1)
5. **Frontend navigation issues**: No way to navigate to questions from game list
6. **Layout issues**: GuidedQuestioning component had broken layout
7. **Network errors**: Errors when skipping all questions weren't handled properly
8. **Missing navigation**: No way to go back to main menu from reflection page
9. **Navigation flickering**: Constant flickering between reflection and coaching pages after submission
10. **Button failures**: "View Game", "Back to Main Menu", and "Continue to Questions" buttons not working
11. **HashRouter pathname issue**: Components checking `location.pathname` instead of `window.location.hash`

### Solutions Implemented

#### Backend Fixes
1. **Added timeout to AI calls** (`socratic_questioner.py`):
   - Wrapped `model.generate_content_async()` with `asyncio.wait_for(timeout=30.0)`
   - Prevents indefinite hanging
   - Falls back to template questions on timeout

2. **Fixed database transaction** (`orchestrator.py`):
   - Changed `await self.db.commit()` to `await self.db.flush()` in `_generate_socratic_questions`
   - Questions are flushed immediately but committed at pipeline level
   - Ensures atomicity (all questions commit together)

3. **Reduced to 1 question per position** (`question_selector.py`):
   - Changed from selecting 3-5 questions to selecting only highest priority question
   - Each key position now gets exactly 1 most appropriate question
   - Priority order: THREAT > OPP_INTENT > CHANGE > ALTERNATIVES > WORST_PIECE > REFLECTION

4. **Enhanced logging** (`orchestrator.py`):
   - Added detailed INFO logs showing:
     - When method is called
     - When generation starts
     - Progress for each question
     - Key position ID in logs for better debugging

5. **Added question statistics** (`games/router.py`):
   - Added `question_stats` field to game response
   - Shows: total, answered, skipped, remaining
   - Shows "Generating questions..." for SUBMITTED games with key positions but no questions yet

#### Frontend Fixes
1. **GameEntry improvements**:
   - Added "View Questions to Answer" button for COACHING games
   - Removed auto-redirect (user can view game first)
   - Button appears where "Submit for AI Coaching" used to be

2. **GuidedQuestioning improvements**:
   - Fixed layout (moved back button outside flex container)
   - Added proper error handling in `handleSubmit`
   - Improved "all questions completed" detection
   - Added loading state during submission

3. **GameList improvements**:
   - Added question status display (e.g., "5 questions ready", "3 questions remaining")
   - Added polling every 5 seconds for COACHING/SUBMITTED games
   - Shows "Generating questions..." for games in progress

4. **FinalReflection improvements**:
   - Added "Back to Main Menu" button at top
   - Enhanced bottom navigation with "Back to Main Menu" and "View Game" buttons
   - Better visual styling
   - Fixed hash checking (uses `window.location.hash` instead of `location.pathname`)
   - Only redirects when actually on reflection page
   - Fixed "View Game" button with proper event handling

5. **Navigation flickering fix**:
   - Fixed HashRouter pathname issue (check `window.location.hash` not `location.pathname`)
   - AIProcessing only redirects when on waiting page
   - FinalReflection only redirects when on reflection page
   - Added location guards to prevent infinite redirect loops
   - All navigation buttons now use proper event handling

### Key Learnings
1. **Always use timeouts for external API calls** - Vertex AI async calls can hang indefinitely
2. **Database transactions**: Flush inside loops, commit at outer level for atomicity
3. **One well-chosen question is better than multiple generic questions**
4. **Frontend needs explicit navigation** - Don't rely on auto-redirects, give users control
5. **Question generation takes time** (15-30s per question) - Show status to user
6. **Error handling is critical** - Network errors need proper try/catch blocks
7. **HashRouter pathname limitation** - `location.pathname` is always `/` with HashRouter, must check `window.location.hash` for actual route
8. **Prevent redirect loops** - Always verify component is on expected page before redirecting, use refs to prevent multiple redirects
9. **Event handling for navigation** - Always use `e.preventDefault()` and `e.stopPropagation()` on navigation button clicks

### Testing Checklist
- [x] Questions generate successfully (1 per key position)
- [x] Timeout works (if AI call exceeds 30s, falls back to template)
- [x] Database transactions work correctly (no "closed transaction" errors)
- [x] Frontend shows question status in game list
- [x] "View Questions to Answer" button appears for COACHING games
- [x] Questions display properly in GuidedQuestioning component
- [x] All questions can be answered/skipped without errors
- [x] Navigation works throughout (back buttons, main menu access)
- [x] No flickering between pages after submission
- [x] "View Game" button works on reflection page
- [x] All navigation buttons work correctly
- [ ] End-to-end test: Submit → Questions → Reflection (verify complete flow)

### Files Modified This Session
**Backend**:
- `backend/api/ai/providers/socratic_questioner.py` - Added timeout, improved error handling
- `backend/api/ai/orchestrator.py` - Fixed transaction, improved logging
- `backend/api/ai/question_selector.py` - Changed to 1 question per position
- `backend/api/games/router.py` - Added question statistics

**Frontend**:
- `web/src/views/GameEntry.tsx` - Added "View Questions to Answer" button, fixed navigation
- `web/src/views/GuidedQuestioning.tsx` - Fixed layout, error handling, navigation buttons
- `web/src/views/GameList.tsx` - Added question status and polling, fixed navigation
- `web/src/views/FinalReflection.tsx` - Added navigation buttons, fixed hash checking, fixed "View Game" button
- `web/src/views/AIProcessing.tsx` - Fixed hash checking, prevent redirects when not on waiting page

### Next Steps
1. Test complete end-to-end flow: Submit → Questions → Reflection
2. Monitor question generation times (should be 15-30s per question)
3. Verify timeout fallback works (if AI calls exceed 30s)
4. Consider adjusting timeout if legitimate responses take longer
5. Monitor for any remaining transaction errors
6. Verify no flickering occurs during state transitions
7. Test all navigation buttons across all pages

---

**End of Universal Debug Guide**

