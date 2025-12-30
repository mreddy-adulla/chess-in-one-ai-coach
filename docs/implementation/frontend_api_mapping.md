# Frontend API Mapping Specification

## Overview
This document maps each screen defined in the **Frontend Design Specification** to its corresponding **Backend API Endpoint**.

---

## 1. Game List Screen
- **Purpose**: List all existing games for the child.
- **API Endpoint**: `GET /games`
- **Expected Payload**: 
  ```json
  [
    { "id": 1, "opponent_name": "...", "state": "EDITABLE", "created_at": "..." },
    ...
  ]
  ```

## 2. Create Game Screen
- **Purpose**: Initialize a new game.
- **API Endpoint**: `POST /games`
- **Payload**:
  ```json
  {
    "player_color": "WHITE",
    "opponent_name": "...",
    "event": "...",
    "date": "...",
    "time_control": "..."
  }
  ```

## 3. Game Entry / Annotation Session Screen
- **Purpose**: Record moves and thinking annotations.
- **API Endpoints**:
  - `POST /games/{id}/annotations`: Add/update thinking for a specific move.
- **Payload**:
  ```json
  { "move_number": 10, "content": "I was looking for tactics..." }
  ```
- **Constraint**: Only valid when `state == EDITABLE`.

## 4. Submission Confirmation Screen
- **Purpose**: Irreversibly lock annotations and start AI coaching.
- **API Endpoint**: `POST /games/{id}/submit`
- **Result**: Transitions state to `SUBMITTED`, then asynchronously to `COACHING`.

## 5. AI Processing Screen
- **Purpose**: Passive waiting while AI runs.
- **API Endpoint**: `GET /games/{id}`
- **Behavior**: Poll until `state == COACHING`.

## 6. Guided Questioning Screen
- **Purpose**: Fixed sequence Socratic questioning.
- **API Endpoints**:
  - `GET /games/{id}/next-question`: Retrieve the current active question (supports resume logic).
  - `POST /questions/{question_id}/answer`: Submit response or skip.
- **Question Flow**: Enforced server-side in the order: `OPP_INTENT → THREAT → CHANGE → WORST_PIECE → ALTERNATIVES → REFLECTION`.

## 7. Final Reflection Screen
- **Purpose**: View AI-generated thinking habits.
- **API Endpoint**: `GET /games/{id}/reflection`
- **Result**: Returns thinking patterns, missing elements, and 1-2 habits.

## 8. Parent Control Interface (Web-only)
- **Purpose**: Manage approvals and tiers.
- **API Endpoints**:
  - `GET /pci/usage`: View child AI usage.
  - `POST /pci/approvals`: Create/Update AI tier approvals.
- **Constraint**: Enforces `PARENT` role in JWT.
