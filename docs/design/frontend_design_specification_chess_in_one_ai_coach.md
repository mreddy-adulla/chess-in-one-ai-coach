# Frontend Design Specification

## Chess‑in‑One AI Coach

**Status:** Authoritative Frontend Design Spec  
**Derived From:** Consolidated Requirements Specification (authoritative)  
**Audience:** UI/UX Designers, Frontend Engineers, QA, Product Owners

---

## 1. Design Philosophy (Non‑Negotiable)

The frontend SHALL embody **calm, disciplined, low‑stimulus design**.

Core principles:
- No gamification
- No scores, badges, ratings, or leaderboards
- No chat metaphors
- No AI “personality”
- No celebratory or corrective tone

The UI exists to **slow the player down**, not excite them.

---

## 2. Platform Targets

| Platform | Primary Use | Design Bias |
|--------|------------|------------|
| Android | Short sessions (5–7 min) | Voice‑first, large touch targets |
| Web | Long review (15–20 min) | Keyboard‑centric, dense views |

Behavioral flow MUST be identical across platforms.

---

## 3. Global Navigation Model

### 3.1 Navigation Rules

- Single‑column linear navigation
- No tabbed workflows inside a game
- Back navigation SHALL NEVER skip lifecycle states

### 3.2 Top‑Level Screens

1. Game List
2. Create Game
3. Game Entry
4. Annotation Session
5. AI Processing (Waiting)
6. Guided Questioning
7. Final Reflection

---

## 4. Game List Screen

### Purpose
Entry point for all games.

### Elements
- List of games (chronological)
- Status badge:
  - Editable
  - Submitted
  - Coached

### Explicit Exclusions
- No sorting by performance
- No analytics
- No filters beyond date

---

## 5. Game Creation Screen

### Fields
- Player color (required)
- Opponent name
- Event
- Date
- Time control

### Behavior
- Save creates an **Editable Game**
- No AI presence

---

## 6. Game Entry Screen

### Purpose
Move‑by‑move input before annotation.

### Supported Inputs
- Manual move entry
- PGN import

### UI Requirements
- Board + move list
- Undo allowed
- No evaluation bar
- No engine suggestions

---

## 7. Annotation Session Screen (Pre‑AI)

### Scope
Player annotations ONLY.

### Per‑Move UI
- Board position
- Move number
- Annotation input area

### Input Methods
- 🎤 Voice input (primary)
- ⌨️ Text input (mandatory fallback)

### Controls
- Skip annotation
- Save & continue

### Hard Rules
- AI MUST NOT appear
- No hints, highlights, or warnings

---

## 8. Submission Confirmation Screen

### Purpose
Irreversible transition into AI phase.

### UI Requirements
- Clear warning: annotations will be locked
- Single confirm action

Once confirmed:
- Game becomes read‑only

---

## 9. AI Processing Screen

### Behavior
- Passive waiting screen
- Minimal animation
- No progress percentage

### Copy
“Preparing your reflection session…”

---

## 10. Guided Questioning Screen

### Structure
One key position at a time.

#### Components
- Static board
- Player’s original annotation (read‑only)
- One question at a time
- Answer input

### Question Flow
Fixed sequence (non‑reorderable):
1. Opponent intent
2. Threat awareness
3. Change detection
4. Worst piece
5. Plan alternatives
6. Reflection

### Controls
- Answer
- Skip (logged internally)

### Prohibitions
- No explanation until all questions done
- No jumping between positions

---

## 11. Final Reflection Screen

### Content Sections
1. How you were thinking
2. What was missing
3. One or two habits

### Presentation
- Plain text blocks
- No bullets longer than 2 lines
- No diagrams

---

## 12. Parent Approval UI

### When Triggered
- Non‑default AI tier
- Re‑analysis request

### Design
- Modal overlay
- PIN or biometric

Child UI MUST block until approval.

---

## 13. Error & Recovery States

### Rules
- Preserve completed answers
- Resume from last unanswered question

### Messaging
Shown to parent, not child.

---

## 14. Accessibility Requirements

- Large tap targets (Android)
- High contrast text
- Voice optional, never mandatory
- Keyboard‑only navigation (Web)

---

## 15. Explicit UI Anti‑Patterns (Forbidden)

- Chat bubbles
- Emoji reactions
- “Correct / Incorrect” labels
- Engine bars
- Move arrows or highlights
- Confetti / celebration

---

## 16. Design Handoff Checklist

Frontend is NON‑COMPLIANT if:
- AI appears before submission
- Question order can be changed
- Scores or evaluations appear
- Parent approval can be bypassed
- Game can be edited after submission

---

## END OF FRONTEND DESIGN SPEC

