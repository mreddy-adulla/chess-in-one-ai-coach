# Frontend Implementation Specification

## Chess‑in‑One AI Coach

**Status:** AUTHORITATIVE FRONTEND IMPLEMENTATION BASELINE  
**Derived From:** Frontend Design Specification, Backend Design v2.1, Implementation Spec v2.0, Production Compliance Package  
**Audience:** Frontend Engineers, QA, Security Review

---

## 1. Purpose

This document defines **exact, enforceable frontend implementation behavior** for the Chess‑in‑One AI Coach.

It translates frontend design intent into:
- Concrete state handling rules
- API interaction contracts
- UI behavior constraints
- Failure and recovery semantics

This document is **binding** for implementation.

---

## 2. Frontend Architecture (Authoritative)

### 2.1 Supported Clients

- Android (primary child device)
- Web (child + parent views)

### 2.2 Non‑Negotiable Rules

- Frontend is **stateless across reloads** except via backend
- Backend is the **single source of truth**
- No client‑side AI logic
- No speculative UI

---

## 3. Global State Model (Frontend)

The frontend SHALL treat game state as:

```
EDITABLE | SUBMITTED | COACHING | COMPLETED
```

Rules:
- State is fetched from backend
- State transitions are never assumed
- Any mismatch triggers a hard refresh

---

## 4. Screen‑to‑API Binding (Locked)

### 4.1 Game List

- `GET /games`
- Render only server‑provided state
- No local sorting beyond date

### 4.2 Game Creation

- `POST /games`
- Client never generates IDs

### 4.3 Game Entry & Annotation

- `POST /moves`
- `POST /annotations`

Rules:
- Allowed only if state == EDITABLE
- Backend rejection MUST block UI

### 4.4 Submit to AI

- `POST /games/{id}/submit`

Rules:
- Disable all inputs immediately
- Await server confirmation
- On failure → restore EDITABLE UI

### 4.5 Guided Questioning

- `GET /games/{id}/next-question`
- `POST /questions/{id}/answer`

Rules:
- Exactly one active question
- Skip sends `{ skipped: true }`
- Never batch requests

### 4.6 Final Reflection

- Reflection is **read‑only**
- No regeneration button

---

## 5. AI Visibility Constraints (Hard)

Frontend MUST NOT:
- Display AI output before submission
- Display partial AI results
- Display AI provider/model info
- Display engine evaluations

Any accidental exposure is a **severity‑1 defect**.

---

## 6. Parent Control Interface (Web‑Only)

### 6.1 Role Enforcement

- Parent JWT required
- Child JWT MUST be rejected

### 6.2 Capabilities

- View AI usage
- Approve or deny escalation

Frontend MUST NOT:
- Cache approvals
- Assume approval persistence

---

## 7. Error & Recovery Handling

### 7.1 AI Failure

- Show neutral interruption to child
- Do not explain failure
- Require refresh to resume

### 7.2 Network Failure

- Retry is user‑initiated only
- No auto‑retry loops

---

## 8. Accessibility & Input

- Voice input optional
- Text fallback mandatory
- Keyboard navigation (Web)
- Large touch targets (Android)

---

## 9. Forbidden Frontend Behaviors

The frontend MUST NEVER:
- Reorder questions
- Skip entire positions
- Retry AI calls automatically
- Store AI outputs locally
- Allow editing after submission

---

## 10. Implementation Checklist (Gate)

Frontend is NON‑COMPLIANT if:
- Any AI appears pre‑submission
- Question order changes
- Parent approval is bypassed
- Backend state is overridden

---

## END OF FRONTEND IMPLEMENTATION SPEC

