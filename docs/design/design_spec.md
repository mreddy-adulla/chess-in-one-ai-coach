# AI Chess Positional Coach
## DESIGN DOCUMENT (v2.1 – Backend AI API, Parent Governance, Network Topology Finalized)

---

## 0. PURPOSE OF THIS DOCUMENT

This document is the **authoritative, end‑to‑end design specification** for the *AI Chess Positional Coach* system.

It:
- Fully covers **all functional requirements** from the consolidated requirements specification
- Explicitly incorporates **pay‑per‑use AI APIs**, **parent‑only AI configuration**, **secure credential handling**, and **Mac Mini + Tailscale deployment**
- Is complete enough to proceed directly into architecture, implementation, and audit

This version **supersedes v2.0** and closes all identified gaps.

---

## 1. DESIGN GOALS (UNCHANGED)

### 1.1 Primary Goal
Create a **child‑safe, reflective chess coaching system** that improves *thinking habits* through structured questioning, not instruction.

### 1.2 Non‑Goals
- No real‑time coaching
- No chat UI
- No move evaluation or scoring
- No public cloud or multi‑tenant service

---

## 2. CORE DESIGN PRINCIPLES

1. Player thinking precedes AI feedback
2. AI asks before it explains
3. AI is invisible until submission
4. Parents control escalation, cost, and access
5. Backend is authoritative; clients are untrusted

---

## 3. SYSTEM ARCHITECTURE OVERVIEW

### 3.1 Components

- **Android Client (Child)**
- **Web Client (Child / Parent)**
- **Parent Control Interface (Web‑only)**
- **Private Backend Service (Mac Mini)**
- **External AI APIs (Pay‑Per‑Use)**

### 3.2 Trust Boundary

- Clients are **zero‑trust**
- Backend is the **sole AI authority**
- Parents configure AI; children only consume

---

## 3.3 Hybrid Intelligence Architecture (Explicit)

The system follows a strict Hybrid Intelligence model:

- Chess engines (Stockfish / Chess API providers) are the sole source of chess truth
- The AI Coach is a pedagogical interpreter, not a chess reasoner

The AI Coach:
- MUST trust engine-provided facts as authoritative
- MUST NOT independently evaluate positions
- MUST NOT search for best moves or tactics

This separation is mandatory to prevent hallucination and ensure deterministic chess correctness.

---

## 4. UX PHASE DESIGN (CONFIRMED)

| Phase | Description | AI Visibility |
|-----|------------|---------------|
| 0 | Home / Resume | None |
| 1 | Game Creation | None |
| 2 | Self‑Annotation | None |
| 3 | Submit to AI | Still None |
| 4 | Key Positions | AI Internal |
| 5 | Guided Questions | AI Asks Only |
| 6 | Reflection | AI Explains |

All phase transitions are **single‑direction and irreversible** after AI submission.

---

## 5. AI ROLE DESIGN (LOCKED)

### 5.1 Chess Situation Analyzer
- Internal‑only
- Detects thinking‑relevant moments
- Produces structured, non‑linguistic output

### 5.2 Socratic Questioner
- Child‑facing
- Fixed category order
- Adaptive phrasing only

### 5.3 Reflection & Guidance Generator
- Summarizes thinking patterns
- Identifies missing dimensions
- Produces **1–2 habits only**

---

## 6. AI PROVIDER & COST MODEL (NEW – EXPLICIT)

### 6.1 Pay‑Per‑Use AI APIs

The system SHALL support **external, usage‑billed AI APIs**, including but not limited to:
- OpenAI (ChatGPT / GPT‑x)
- Google Gemini
- Other equivalent providers

There is **no on‑device or on‑prem model requirement**.

### 6.2 Provider Abstraction Rule

Clients SHALL NOT:
- Know which provider is used
- Select providers
- Access API keys

All provider logic resides **only on the backend**.

---

## 7. PARENT‑ONLY AI CONFIGURATION (NEW – STRICT)

### 7.1 Parent Control Interface (PCI)

A dedicated **Parent Control Interface** SHALL exist (web‑only) to manage:

- Enabled AI providers
- Active pricing tier
- Per‑session AI limits
- Approval rules

Children NEVER see provider names.

### 7.2 AI Tier Abstraction

Example tiers:
- **Standard Coach** (low cost)
- **Advanced Coach** (higher cost / better reasoning)

Tier → Provider mapping is **backend‑only**.

### 7.3 Authentication to AI APIs

- API keys are entered **only** in the Parent Control Interface
- Keys are stored encrypted on the backend
- Keys are never logged, cached client‑side, or transmitted to clients

---

## 8. BACKEND AI MODEL REGISTRY

Backend maintains a secure registry:

```json
{
  "STANDARD": {
    "provider": "openai",
    "model": "gpt‑4o‑mini",
    "secretRef": "OPENAI_STD_KEY"
  },
  "ADVANCED": {
    "provider": "openai",
    "model": "gpt‑5.2",
    "secretRef": "OPENAI_ADV_KEY"
  }
}
```

Only the backend resolves this mapping.

---

## 9. PARENT APPROVAL & GOVERNANCE

- Non‑default tier ALWAYS requires approval
- Second AI run on same game ALWAYS requires approval
- Approvals are:
  - Time‑bound
  - Single‑use
  - Revocable

Approval mechanisms:
- PIN
- Platform biometric (where supported)

---

## 10. BACKEND DEPLOYMENT (NEW – EXPLICIT)

### 10.1 Hardware

- Backend runs on a **dedicated Mac Mini**
- Not deployed to public cloud

### 10.2 Network Exposure via Tailscale

- Backend service is **not publicly exposed**
- Access is provided via **Tailscale mesh network**
- Only authenticated devices (child + parent) may connect

### 10.3 Service Characteristics

- Private IP only
- No inbound public ports
- Backend reachable only through Tailscale identity

---

## 11. SECURITY & PRIVACY (FINAL)

### 11.1 Security
- Zero‑trust clients
- JWT + device binding
- Encrypted secrets at rest
- No AI credentials outside backend

### 11.2 Privacy
- No personal data sent to AI
- No analytics visible to child
- Full data deletion supported

---

## 12. FAILURE, COST & SAFETY CONTROLS

- No silent retries
- Partial progress preserved
- AI failures surfaced to parents only
- Hard per‑game AI invocation limits

---

## 13. COMPLIANCE CHECKLIST (MUST HOLD)

System is NON‑COMPLIANT if:
- Client selects AI provider
- Client stores AI keys
- AI appears before submission
- Question order is altered
- Parent approval is bypassed
- Backend is publicly exposed

---

## 14. DESIGN STATUS

This design is now:
- Requirements‑complete
- Security‑complete
- Cost‑governed
- Parent‑controlled
- Network‑isolated
- Ready for architecture & implementation

---

**END OF DESIGN DOCUMENT v2.1**

