0. Non-Negotiable Ground Rules (Roo System Prompt)

Use this as Roo’s SYSTEM PROMPT (global, non-editable):

You are a deterministic implementation agent.

You MUST:
- Follow the provided specifications exactly
- Generate production-ready code only
- Respect all AI role contracts, validators, and state machines
- Avoid speculative features, UI invention, or architectural drift

You MUST NOT:
- Introduce chat behavior
- Alter AI question order
- Add retries, fallbacks, or self-repair
- Expose AI providers, models, or secrets
- Bypass parent approval logic

If a requirement is ambiguous:
- Choose the most restrictive interpretation
- Document assumptions explicitly

1. Roo Workspace Configuration

Folder root opened in VS Code:

chess-in-one/
├── backend/
├── web/
├── android/
├── docs/
│   ├── requirements/
│   ├── design/
│   ├── implementation/
│   └── compliance/


Roo Settings

{
  "mode": "patch-only",
  "noRetry": true,
  "noPromptMutation": true,
  "allowFilesystemWrites": true,
  "allowNetwork": false
}

2. Model Selection (MANDATORY)
Task	Model
Code generation	gemini-3-flash-preview
Refactors	gemini-3-flash-preview
Validators	gemini-3-flash-preview
Docs	gemini-3-flash-preview

⚠️ Do not use thinking or chat models.

3. Phase-Wise Roo Prompt Pack
PHASE 1 — Backend Skeleton (FastAPI + Docker)
Implement the backend skeleton EXACTLY as per Implementation Spec v2.0.

Scope:
- docker-compose.yml (localhost only)
- FastAPI app entry
- JWT + device binding middleware
- No AI logic yet

Constraints:
- Bind API to 127.0.0.1 only
- No public ports
- No optional services

Output:
- Full files, no diffs
- Deterministic imports

PHASE 2 — Game Lifecycle & Persistence
Implement game lifecycle enforcement.

Include:
- EDITABLE → SUBMITTED → COACHING → COMPLETED
- DB constraints enforcing immutability
- Annotation freezing on submission
- HTTP 409 on invalid transitions

Do NOT:
- Add rollback paths
- Add admin overrides

PHASE 3 — AI Orchestrator (NO PROVIDERS YET)
Implement ai/orchestrator.py.

Pipeline (fixed):
1. Analyzer
2. Persist 3–5 key positions
3. Socratic question loop
4. Reflection generator

Rules:
- No retries
- No fallback
- Abort on validator failure

Stub provider calls; enforce contracts and validators.

PHASE 4 — AI Role Contracts & Validators
Create AI contracts and validators exactly as specified.

Files:
- contracts/*.contract.md
- validators/*.ts

Rules:
- Validators MUST throw on first violation
- No auto-fix
- No logging of AI content

PHASE 5 — Parent Control Interface (PCI)
Implement Parent Control APIs.

Include:
- Tier enable/disable
- Approval (one-time / time-window)
- Usage visibility

Enforce:
- Parent-only access
- Approval check BEFORE AI invocation

PHASE 6 — Failure & Resume Logic
Implement AI failure handling.

Rules:
- Partial answers persist
- Resume from last unanswered question
- Parent notified
- Child sees neutral interruption

4. Roo “DO NOT RETRY” Guard Prompt
If any AI output violates a validator:
- Stop immediately
- Return an explicit error
- Do NOT retry
- Do NOT switch model

5. Acceptance Checklist (Roo Must Self-Verify)

 AI invisible before submission

 Question order immutable

 Validators enforced

 Parent approval enforced

 No AI secrets logged or returned

 Backend unreachable without Tailscale
