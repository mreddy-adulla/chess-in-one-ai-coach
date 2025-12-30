# Chess‑in‑One AI Coach — Implementation Specification (v2.0)

> **Status:** AUTHORITATIVE IMPLEMENTATION BASELINE  
> **Supersedes:** Implementation Spec v1.0  
> **Derived from:** Consolidated Requirements, Design v2.1, Detailed AI Contracts

---

## 0. Purpose & Scope

This document is the **fully merged, execution‑complete implementation specification** for the Chess‑in‑One AI Coach system.

It translates **all requirements, design constraints, AI role contracts, security guarantees, and governance rules** into concrete, enforceable implementation behavior.

This spec is **sufficient to build, test, audit, and deploy** the system without referring to any other document.

---

## 1. Deployment & Network Architecture (Final)

### 1.1 Topology

```
Android / Web Clients
        │ HTTPS
        ▼
Tailscale Funnel (Public TLS Edge)
        ▼
Tailscale Node (Mac Mini)
        ▼  localhost
Docker Compose Stack
```

### 1.2 Invariants

- No backend service is directly exposed to the public internet
- TLS termination occurs at Tailscale Funnel
- All backend traffic is treated as untrusted and authenticated
- Clients never join the tailnet

---

## 2. Backend Runtime Stack

| Layer | Technology |
|-----|-----------|
| Host | macOS (Mac Mini) |
| Container Runtime | Docker Desktop |
| API | FastAPI (Python) |
| Database | PostgreSQL 16 |
| Cache / Locks | Redis 7 |
| Auth | JWT + Device Binding |
| AI | External APIs only |

---

## 3. Repository & Container Layout (Authoritative)

```
backend/
├── docker-compose.yml
├── .env
├── api/
│   ├── main.py
│   ├── auth/
│   ├── games/
│   ├── ai/
│   │   ├── orchestrator.py
│   │   ├── providers/
│   │   └── validators/
│   ├── pci/
│   └── common/
├── db/
│   └── migrations/
└── secrets/
```

---

## 4. Docker Compose (Locked)

- API binds to `127.0.0.1` only
- Database and Redis are internal‑only
- No service exposes a public port

Funnel forwards `443 → localhost:8080`

---

## 5. Authentication & Identity Enforcement

### 5.1 JWT Claims

```json
{
  "sub": "user_id",
  "role": "CHILD | PARENT",
  "device_id": "uuid",
  "exp": 123456
}
```

### 5.2 Rules

- Tokens are valid only for the issuing device
- Parent tokens are rejected on child APIs
- Child tokens are rejected on PCI APIs
- Replay or parallel usage from another device invalidates the token

---

## 6. Game Lifecycle State Machine (Hard Enforcement)

### 6.1 States

```
EDITABLE → SUBMITTED → COACHING → COMPLETED
```

### 6.2 Enforcement Rules

- Only backend may change state
- Transitions are single‑direction and irreversible
- Any invalid transition returns HTTP 409
- Submit endpoint is idempotent

---

## 7. Persistence & Consistency Rules

### 7.1 Annotations

- Writable only when game state = EDITABLE
- Frozen automatically on SUBMITTED
- DB constraint enforces `frozen = true` for non‑editable games

### 7.2 Answers

- Insert allowed only when state = COACHING
- Each question accepts exactly one answer or skip
- Duplicate answers rejected

### 7.3 Transactions

- State transition + side effects occur in a single transaction
- Partial writes are forbidden

---

## 8. AI Orchestration Pipeline (Deterministic)

### 8.1 Execution Order

1. Chess Situation Analyzer (internal)
2. Persist 3–5 key positions
3. Socratic Question Loop (child‑facing)
4. Reflection & Guidance Generator

No retries. No fallback models. No re‑entry.

---

## 9. AI Contract Enforcement (Mandatory)

### 9.1 Validator Gate

- Every AI response MUST pass its role‑specific validator
- Validation occurs **before persistence or exposure**
- Any violation immediately aborts the pipeline

### 9.2 Failure Policy

- No auto‑repair
- No partial output
- No retry with alternate model
- Failure is recoverable only by parent approval (if applicable)

Violation of a contract is a **system defect**.

---

## 10. Socratic Question State Machine

### 10.1 Structure

For each key position:

```
Q1 → Q2 → Q3 → Q4 → Q5 → Q6
```

Categories are immutable and ordered.

### 10.2 Rules

- Only one question active at a time
- Skip advances cursor but is recorded
- Resume continues from last unanswered question
- No batch skipping
- No reordering

---

## 11. Parent Approval Enforcement

### 11.1 Approval Triggers

Approval is REQUIRED for:
- Any non‑default AI tier
- Second or later AI run on same game

### 11.2 Approval Semantics

- Approvals are single‑use OR time‑bound
- Expired approvals are invalid
- Approval is checked **before AI invocation**
- Mid‑session expiry blocks further progress

All approval decisions are logged.

---

## 12. AI Provider Registry

```python
MODEL_REGISTRY = {
  "STANDARD": { "provider": "…", "model": "…", "secret": "…" },
  "ADVANCED": { "provider": "…", "model": "…", "secret": "…" }
}
```

- Resolved backend‑only
- Secrets encrypted at rest
- Never logged or returned

---

## 13. API Contracts (Authoritative)

### Child APIs

- `POST /games`
- `POST /games/{id}/submit`
- `GET /games/{id}/next-question`
- `POST /questions/{id}/answer`

### PCI APIs

- `POST /pci/approvals`
- `POST /pci/approvals/{id}/decision`
- `GET /pci/usage`

All endpoints enforce state, role, and approval rules.

---

## 14. Failure Handling & Resume

- AI failure halts immediately
- Completed answers persist
- Resume continues from last unanswered question
- Child sees neutral interruption message
- Parent is notified with failure reason

---

## 15. Logging & Audit (Strict)

Logged:
- State transitions
- AI invocation metadata
- Approval grants / denials
- Failure events

Never logged:
- AI prompts
- AI responses
- Child answers content

---

## 16. Concurrency & Abuse Protection

- One active AI session per game
- Concurrent submit attempts rejected
- Redis lock protects AI pipeline

---

## 17. Compliance Checklist (Release Gate)

- [ ] AI invisible before submission
- [ ] Validators enforced
- [ ] Question order immutable
- [ ] Parent approval enforced
- [ ] No public backend exposure
- [ ] No AI secrets outside backend

---

## END OF IMPLEMENTATION SPEC v2.0

