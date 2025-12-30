# Chess‑in‑One AI Coach
## Production Implementation & Compliance Package

**Status:** FINAL, RELEASE‑BLOCKING AUTHORITY  
**Scope:** End‑to‑end production implementation, security, governance, and compliance baseline  
**Derived From:** Consolidated Requirements, Design v2.1, Implementation Spec v2.0, Consolidated Authoritative Specification

---

## 1. Purpose of This Package

This document is the **single authoritative production handoff** for the Chess‑in‑One AI Coach system.

It unifies:
- Functional requirements
- System and AI design constraints
- Backend architecture and deployment rules
- AI role contracts and validators
- Parent governance and approval enforcement
- Security, privacy, and compliance guarantees

This file alone is sufficient for:
- Engineering implementation
- Security and compliance audit
- Production deployment
- Ongoing regression verification

No external specification is required or permitted once this package is adopted.

---

## 2. Non‑Negotiable Product Intent

The system is a **post‑game chess coaching tool** focused exclusively on improving **thinking habits**, not move quality.

The system SHALL:
- Capture the player’s thinking first
- Identify missing thinking dimensions
- Use structured Socratic questioning
- Provide minimal reflective guidance

The system SHALL NOT:
- Coach during games
- Provide move suggestions or evaluations
- Display engine scores or rankings
- Operate as a chat system

---

## 3. System Topology & Deployment (Production‑Locked)

### 3.1 Physical & Network Deployment

- Backend runs on a **dedicated Mac Mini**
- No public cloud deployment
- No public inbound ports

**Network Path**
```
Android / Web Clients
        │ HTTPS
        ▼
Tailscale Funnel (TLS Edge)
        ▼
Mac Mini (Private IP)
        ▼
Docker Compose Stack (localhost only)
```

### 3.2 Hard Invariants

- Backend services bind to `127.0.0.1` only
- TLS terminates at Tailscale Funnel
- Clients never join the tailnet
- All outbound AI calls are HTTPS only

---

## 4. Backend Runtime Stack

| Layer | Technology |
|-----|-----------|
| Host | macOS (Mac Mini) |
| Runtime | Docker Desktop |
| API | FastAPI (Python) |
| Database | PostgreSQL 16 |
| Cache / Locks | Redis 7 |
| Auth | JWT + Device Binding |
| AI | External Pay‑Per‑Use APIs |

---

## 5. Repository & Service Layout (Authoritative)

```
backend/
├── docker-compose.yml
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

No additional runtime services are permitted.

---

## 6. Authentication & Identity Enforcement

### 6.1 JWT Claims (Mandatory)

```json
{
  "sub": "user_id",
  "role": "CHILD | PARENT",
  "device_id": "uuid",
  "exp": 123456
}
```

### 6.2 Enforcement Rules

- Tokens are device‑bound
- Parallel use on another device invalidates the token
- Parent tokens are rejected on child APIs
- Child tokens are rejected on PCI APIs

---

## 7. Game Lifecycle State Machine (Hard‑Locked)

### 7.1 States

```
EDITABLE → SUBMITTED → COACHING → COMPLETED
```

### 7.2 Rules

- Transitions are single‑direction and irreversible
- Only backend may transition state
- Invalid transitions return HTTP 409
- Submit is idempotent

---

## 8. Annotation & Persistence Rules

- Annotations allowed **only** in EDITABLE
- Annotations auto‑freeze on SUBMITTED
- Frozen annotations are DB‑enforced
- Answers allowed **only** in COACHING
- Each question accepts exactly one answer or skip

All state changes occur in a single transaction.

---

## 9. AI Orchestration Pipeline (Deterministic)

Execution order is fixed:

1. Chess Situation Analyzer (internal)
2. Persist 3–5 key positions
3. Socratic Question Loop
4. Reflection & Guidance Generator

Rules:
- No retries
- No model fallback
- No mid‑pipeline re‑entry

---

## 10. AI Role Contracts (Mandatory)

### 10.1 Chess Situation Analyzer

- Internal only
- JSON output only
- No language, no evaluation
- Outputs 3–5 key positions with reason codes

### 10.2 Socratic Questioner

- Child‑facing
- Fixed category order
- One question at a time
- No explanations or hints

### 10.3 Reflection & Guidance Generator

- Final output only
- Summarizes thinking patterns
- Identifies missing elements
- Produces **1–2 habits only**

Violation of any contract is a **system defect**.

---

## 11. Validator Gate (Non‑Bypassable)

- Every AI response passes a role‑specific validator
- Validation occurs before persistence or exposure
- Failure aborts the pipeline immediately
- No auto‑repair or retries

---

## 12. Socratic Question State Machine

For each key position:

```
OPP_INTENT → THREAT → CHANGE → WORST_PIECE → ALTERNATIVES → REFLECTION
```

Rules:
- Order is immutable
- Only one active question
- Skip advances cursor and is recorded
- Resume continues from last unanswered question

---

## 13. Parent Control Interface (PCI)

### 13.1 Capabilities

Parents may:
- Enable / disable AI tiers
- Set default tier
- Approve escalation
- View AI usage per game

Children NEVER:
- See providers or models
- See costs
- See approval logic

### 13.2 Approval Triggers

Approval is REQUIRED for:
- Non‑default tier usage
- Second or later AI run on a game

Approvals are:
- Single‑use or time‑bound
- Checked **before** AI invocation
- Logged immutably

---

## 14. AI Provider Registry (Backend‑Only)

```json
{
  "STANDARD": { "provider": "…", "model": "…", "secret": "…" },
  "ADVANCED": { "provider": "…", "model": "…", "secret": "…" }
}
```

- Secrets encrypted at rest
- Never logged
- Never exposed to clients

---

## 15. Failure & Recovery Semantics

- AI failure halts immediately
- Completed answers persist
- Resume from last unanswered question
- Child sees neutral interruption
- Parent receives failure notification

---

## 16. Logging & Audit Rules

Logged:
- State transitions
- AI invocation metadata (no content)
- Approval grants / denials
- Failure events

Never logged:
- AI prompts
- AI responses
- Child answer content

---

## 17. Concurrency & Abuse Protection

- One AI session per game
- Concurrent submits rejected
- Redis lock guards AI pipeline

---

## 18. Compliance Release Checklist (Blocking)

The system is **NON‑COMPLIANT** if ANY are true:

- AI visible before submission
- Question order altered
- Parent approval bypassed
- Evaluative language used
- AI secrets exposed to clients
- Backend publicly reachable

---

## 19. Compliance Status

When implemented exactly as specified, the system is:

- Child‑safe
- Parent‑governed
- Cost‑controlled
- Deterministic
- Auditable
- Production‑ready

---

## AI Hallucination Prevention Compliance

To be production-compliant:

- All AI prompts MUST include EngineTruth
- AI outputs MUST be validated against provided engine facts
- Any deviation constitutes a severity-1 compliance violation

The system MUST log:
- EngineTruth payload
- AI prompt
- AI response

This guarantees auditability and deterministic failure analysis.

---

**END OF PRODUCTION IMPLEMENTATION & COMPLIANCE PACKAGE**

