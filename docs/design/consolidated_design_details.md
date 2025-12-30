# Chess-in-One — Consolidated Authoritative Specification

## Backend Architecture
┌──────────────────────────────┐
│        Android Client         │
│        (Child User)           │
│------------------------------│
│ • Game Entry / PGN Import     │
│ • Voice/Text Annotations     │
│ • Guided Question UI         │
│ • Zero AI Visibility Pre-Submit
│------------------------------│
│  Zero-Trust Client            │
└──────────────┬───────────────┘
               │  Authenticated API (JWT + Device Binding)
               │  (Tailscale Private Mesh)
               ▼
┌──────────────────────────────┐
│          Web Client           │
│   (Child + Parent Views)     │
│------------------------------│
│ Child:
│ • Long Review Sessions
│ • Keyboard PGN Workflows
│
│ Parent:
│ • AI Tier Approval
│ • Usage Visibility
│ • Cost Governance
│------------------------------│
│  Zero-Trust Client            │
└──────────────┬───────────────┘
               │
               ▼
══════════════ TRUST BOUNDARY ══════════════
               │
               ▼
┌──────────────────────────────────────────┐
│        Private Backend Service            │
│        (Mac Mini, Private IP)             │
│------------------------------------------│
│ • Authentication & Device Binding         │
│ • Game Lifecycle Enforcement              │
│ • Annotation Freezing                     │
│ • Question Flow State Machine             │
│ • Parent Approval Enforcement             │
│ • AI Cost & Invocation Limits             │
│------------------------------------------│
│ AI Role Orchestration (Internal Only):    │
│   1. Chess Situation Analyzer             │
│   2. Socratic Questioner                  │
│   3. Reflection & Guidance Generator      │
│------------------------------------------│
│ Secure AI Provider Registry               │
│ (Tier → Provider → Model → SecretRef)     │
└──────────────┬───────────────────────────┘
               │  Outbound-Only HTTPS
               │  (No inbound public access)
               ▼
┌──────────────────────────────────────────┐
│       External AI APIs (Pay-Per-Use)      │
│------------------------------------------│
│ • OpenAI / Gemini / Equivalent            │
│ • No client visibility                    │
│ • No PII transmitted                     │
│ • No provider choice by child             │
└──────────────────────────────────────────┘

## Parent Control Interface (PCI) — Functional Specification
2.1 Purpose

The Parent Control Interface is the only surface where:

AI cost

AI capability

AI frequency

AI escalation
are managed.

Children never see providers, models, or costs.

2.2 Access & Identity

Access rules

Web-only

Parent-authenticated account

Strong authentication (password + optional biometric)

Bound to child account(s)

2.3 Core Capabilities
A. AI Tier Management

Parents SHALL be able to:

Enable / disable AI tiers

Assign default tier

Define escalation-allowed tiers

Example (abstracted):

Standard Coach

Advanced Coach

(Tier → provider mapping is backend-only)

B. Approval Controls

Parents SHALL be able to approve:

Non-default tier usage

Second or subsequent AI runs on same game

Approval modes:

One-time approval

Time-window approval (e.g., next 24 hours)

Approval methods:

PIN

Platform biometrics (if available)

C. Usage Visibility

Parents SHALL be able to view:

AI usage count per game

Tier requested vs approved

Estimated session duration

Parents SHALL NOT see:

Child answers

Detailed chess analysis

AI reasoning chains

D. Failure Notifications

Parents SHALL be notified if:

AI invocation fails

Cost limit is hit

Session is partially completed

Failures are never surfaced directly to the child.

2.4 Explicit Prohibitions

PCI SHALL NOT:

Show raw prompts or responses

Allow free-form AI chatting

Allow parent to rewrite child answers

## Security Threat Model (STRIDE-Aligned)
3.1 Threat Actors
Actor	Description
Curious Child	Attempts to bypass AI limits
Malicious Client	Tampered app / API replay
External Attacker	Network or credential attack
Misconfigured Parent	Unintended cost exposure
3.2 Threats & Mitigations
🟥 Spoofing

Threat

Impersonating parent or device

Mitigations

JWT + device binding

Parent approval required for escalation

Tailscale identity enforcement

🟥 Tampering

Threat

Modifying game state after AI submission

Mitigations

Immutable lifecycle: Editable → Submitted → Coached

Server-side enforcement only

No client authority over state transitions

🟥 Repudiation

Threat

Disputes over AI usage or approvals

Mitigations

Backend-logged approval events

Usage counters per game

Time-stamped approval records

🟥 Information Disclosure

Threat

Leaking AI keys or personal data

Mitigations

AI keys encrypted at rest

Keys never sent to clients

No PII included in AI prompts

🟥 Denial of Service

Threat

Repeated AI submissions

Mitigations

Per-game invocation caps

Explicit parent approval gates

No automatic retries

🟥 Elevation of Privilege

Threat

Child accessing parent controls

Mitigations

Separate auth roles

Web-only PCI

No parent features exposed in child UI

## Implementation Checklist (Authoritative)
Phase 1 — Backend Foundations

 Private backend on Mac Mini

 Tailscale mesh networking

 JWT + device binding

 Zero-trust client model

Phase 2 — Game Lifecycle Enforcement

 Immutable state transitions

 Annotation freezing on submission

 Server-side move ownership validation

Phase 3 — AI Role Pipeline

 Chess Situation Analyzer (internal only)

 Key position selector (3–5 max)

 Socratic Questioner with locked order

 Reflection generator (1–2 habits only)

Phase 4 — Parent Control Interface

 Web-only PCI

 Tier enable/disable

 Approval workflows

 Usage visibility dashboard

Phase 5 — AI Provider Security

 Encrypted key storage

 Tier → provider registry

 Outbound-only AI calls

 No client provider knowledge

Phase 6 — Failure & Recovery

 Partial progress persistence

 Resume from last unanswered question

 Parent-only failure notifications

Phase 7 — Compliance Validation

 No AI before submission

 No reordered questions

 No scoring or evaluation language

 No public backend exposure

## 1️⃣ Sequence Diagrams (Per Phase)

Notation: → synchronous call, ⇒ async job, ⛔ forbidden action

Phase 1–2: Game Creation & Annotation (No AI)
Child Client → Backend: POST /games
Backend → Backend: create Game(state=EDITABLE)

loop per move
  Child Client → Backend: POST /moves
  Child Client → Backend: POST /annotations (voice/text)
end

⛔ Child Client → AI (forbidden)


Invariant

AI services unreachable

Backend enforces state == EDITABLE

Phase 3: Submit to AI (Freeze Boundary)
Child Client → Backend: POST /games/{id}/submit
Backend → Backend:
  validate completeness
  freeze annotations
  transition state: EDITABLE → SUBMITTED


Security

Immutable transition

No rollback path 

security-threat-model

Phase 4: Key Position Identification (Internal AI)
Backend ⇒ Analyzer Agent:
  input: PGN + annotations
  output: key_positions[3–5]

Backend → Backend:
  persist key_positions
  transition state: SUBMITTED → COACHING


Notes

No child-visible output

Analyzer has no language output 

ai_chess_positional_coach_desig…

Phase 5: Socratic Question Loop (Per Position)
loop position in key_positions
  loop question in fixed_sequence
    Backend → Child Client: question
    Child Client → Backend: answer | skip
    Backend → Backend: persist response
  end
end


Hard Guarantees

No reordering

No batch skipping

Resume from last unanswered question on failure 

Implementation-checklist

Phase 6: Reflection Generation
Backend ⇒ Reflection Agent:
  input: all answers
  output:
    - thinking pattern
    - missing elements
    - 1–2 habits

Backend → Child Client: final reflection
Backend → Backend: state = COMPLETED

Phase 7: Parent Approval / Escalation (PCI)
Child Client → Backend: request advanced tier
Backend → Parent PCI: approval request
Parent → Backend: approve | deny
Backend → Child Client: proceed | blocked

## 2️⃣ Database Schema (State-Machine Driven)
Core Tables (Authoritative)
Game (
  id UUID PK,
  child_id UUID,
  state ENUM(
    'EDITABLE',
    'SUBMITTED',
    'COACHING',
    'COMPLETED'
  ),
  created_at,
  submitted_at
)

Move (
  id UUID PK,
  game_id FK,
  move_number,
  san,
  is_player_move BOOLEAN
)

Annotation (
  id UUID PK,
  move_id FK,
  input_type ENUM('VOICE','TEXT'),
  content TEXT,
  frozen BOOLEAN
)

KeyPosition (
  id UUID PK,
  game_id FK,
  fen,
  reason_code ENUM(
    'OPP_INTENT',
    'THREAT',
    'TRANSITION'
  )
)

Question (
  id UUID PK,
  key_position_id FK,
  category ENUM(
    'OPP_INTENT',
    'THREAT',
    'CHANGE',
    'WORST_PIECE',
    'ALTERNATIVES',
    'REFLECTION'
  ),
  order_index INT
)

Answer (
  id UUID PK,
  question_id FK,
  content TEXT,
  skipped BOOLEAN
)

ParentApproval (
  id UUID PK,
  game_id FK,
  tier ENUM('STANDARD','ADVANCED'),
  expires_at,
  used BOOLEAN
)


State Integrity Rules

Annotation.frozen = true iff Game.state != EDITABLE

Answer inserts forbidden unless Game.state == COACHING

All transitions server-validated only 

security-threat-model

## API Contract Definitions (Zero-Trust)
Child-Facing APIs
Create Game
POST /games
→ 201 { game_id }

Submit Game
POST /games/{id}/submit
→ 202 Accepted
⛔ if state != EDITABLE

Get Next Question
GET /games/{id}/next-question
→ 200 { question, board_fen }
→ 204 No Content (position complete)

Answer Question
POST /questions/{id}/answer
{
  content?: string,
  skipped: boolean
}

Parent Control Interface APIs
Request Approval
POST /pci/approvals
{
  game_id,
  tier,
  duration_hours
}

Approve / Deny
POST /pci/approvals/{id}/decision
{
  decision: APPROVE | DENY
}

Usage Visibility
GET /pci/usage?child_id=
→ AI runs, tiers, timestamps


Explicitly Absent

No AI prompts

No AI responses

No provider info 


## PCI UI Wireframe (Logic-Only)
+--------------------------------------------------+
| Parent Control Interface (Web Only)               |
+--------------------------------------------------+

[ Child Selector ▼ ]

--------------------------------------------
AI Tier Control
--------------------------------------------
( ) Standard Coach   [DEFAULT]
( ) Advanced Coach   [Requires Approval]

--------------------------------------------
Approval Rules
--------------------------------------------
[✓] Require approval for non-default tier
[✓] Require approval for repeat AI runs

Approval Mode:
( ) One-time
( ) Time window: [ 24 ] hours

--------------------------------------------
Usage Visibility
--------------------------------------------
Game ID | Tier | Runs | Last Used
--------------------------------------------
G-1024  | Std  | 1    | Today
G-1029  | Adv  | 1    | Approved

--------------------------------------------
Failure Alerts
--------------------------------------------
⚠ Cost limit reached (Game G-1031)
⚠ AI session incomplete


Deliberate Omissions

No child answers

No chess content

No AI reasoning

No free text input 

## AI Prompts contracts
Folder Structure (Authoritative)
ai/
├── contracts/
│   ├── analyzer.contract.md
│   ├── socratic_questioner.contract.md
│   └── reflection_generator.contract.md
│
├── validators/
│   ├── analyzer.validator.ts
│   ├── socratic_questioner.validator.ts
│   └── reflection_generator.validator.ts
│
└── README.md

1️⃣ contracts/analyzer.contract.md
# AI Prompt Contract — Chess Situation Analyzer

## Contract Version
v1.0

## Role Name
Chess Situation Analyzer

## Visibility
INTERNAL ONLY — NEVER CHILD FACING

## Purpose
Identify thinking-relevant positions in a completed chess game.
This role exists solely to detect *where thinking mattered*, not *what move was best*.

## Inputs (Read-Only)
- Full PGN (complete game)
- Player color
- Player annotations (optional, may be empty)

## Allowed Output (STRICT)
The output MUST be valid JSON and MUST match this schema exactly:

```json
{
  "key_positions": [
    {
      "fen": "string",
      "reason_code": "OPP_INTENT | THREAT | TRANSITION"
    }
  ]
}

Output Constraints

key_positions count MUST be between 3 and 5

fen MUST be a valid chess FEN

reason_code MUST be one of the enumerated values

Output MUST contain NO additional fields

Explicit Prohibitions (Hard Rules)

The Analyzer MUST NOT:

Produce natural language explanations

Evaluate moves (e.g., “good”, “bad”, “mistake”)

Suggest moves or plans

Address the user directly

Mention engines, scores, or evaluations

Output prose, markdown, or commentary

Failure Policy

If constraints cannot be satisfied:

The role MUST fail explicitly

The system MUST NOT attempt self-repair or retries

Compliance Status

Violation of this contract is a SYSTEM DEFECT.


---

# 2️⃣ `contracts/socratic_questioner.contract.md`

```md
# AI Prompt Contract — Socratic Questioner

## Contract Version
v1.0

## Role Name
Socratic Questioner

## Visibility
CHILD-FACING (QUESTIONS ONLY)

## Purpose
Expose missing thinking dimensions through structured questioning.
This role asks questions. It never teaches.

## Inputs (Read-Only)
- One key position (FEN)
- Player’s original annotation (optional)
- Question category (provided by backend, immutable)

## Allowed Output (STRICT)
The output MUST be valid JSON:

```json
{
  "question_text": "string"
}

Question Category Order (IMMUTABLE)

OPP_INTENT

THREAT

CHANGE

WORST_PIECE

ALTERNATIVES

REFLECTION

The model MUST NOT alter or skip categories.

Tone Constraints

Neutral

Curious

Non-judgmental

Age-appropriate

Explicit Prohibitions (Hard Rules)

The Socratic Questioner MUST NOT:

Explain the position

Correct the player

Suggest moves

Give hints

Use evaluative language (good/bad/better/worse)

Ask multiple questions at once

Refer to previous or future questions

Failure Policy

If a compliant question cannot be generated:

The role MUST fail

The system MUST surface a recoverable error

Compliance Status

Violation of this contract is a SYSTEM DEFECT.


---

# 3️⃣ `contracts/reflection_generator.contract.md`

```md
# AI Prompt Contract — Reflection & Guidance Generator

## Contract Version
v1.0

## Role Name
Reflection & Guidance Generator

## Visibility
CHILD-FACING (FINAL OUTPUT ONLY)

## Purpose
Summarize how the player was thinking and suggest minimal habit-level guidance.

This role reflects. It does not instruct.

## Inputs (Read-Only)
- All answers
- Skip markers
- Internal thinking-dimension flags
- NO board positions

## Allowed Output (STRICT)
The output MUST be valid JSON:

```json
{
  "thinking_summary": "string",
  "missing_elements": ["string"],
  "habits_to_try": ["string"]
}

Output Constraints

habits_to_try MUST contain 1 or 2 items ONLY

missing_elements MUST be conceptual (not move-specific)

Language MUST be non-evaluative

Explicit Prohibitions (Hard Rules)

The Reflection Generator MUST NOT:

Suggest specific moves

Reference evaluations or engines

Rewrite or reinterpret child answers

Use authority language (“you should”, “correct move”)

Produce more than 2 habits

Failure Policy

If constraints cannot be satisfied:

The role MUST fail

Partial output is NOT allowed

Compliance Status

Violation of this contract is a SYSTEM DEFECT.


---

# 4️⃣ Output Validators (TypeScript, Deterministic)

These run **after every AI call**.

---

## `validators/analyzer.validator.ts`

```ts
export function validateAnalyzerOutput(output: any) {
  if (!output?.key_positions) throw new Error("Missing key_positions")

  if (output.key_positions.length < 3 || output.key_positions.length > 5) {
    throw new Error("Invalid number of key positions")
  }

  for (const kp of output.key_positions) {
    if (!kp.fen || typeof kp.fen !== "string") {
      throw new Error("Invalid FEN")
    }

    if (!["OPP_INTENT", "THREAT", "TRANSITION"].includes(kp.reason_code)) {
      throw new Error("Invalid reason_code")
    }
  }

  const forbiddenText = JSON.stringify(output)
  if (/[a-zA-Z]{4,}/.test(forbiddenText)) {
    throw new Error("Natural language detected in analyzer output")
  }
}

validators/socratic_questioner.validator.ts
export function validateSocraticOutput(output: any) {
  if (!output?.question_text) {
    throw new Error("Missing question_text")
  }

  const forbidden = [
    "best", "better", "worse", "should",
    "move", "engine", "correct", "mistake"
  ]

  for (const word of forbidden) {
    if (output.question_text.toLowerCase().includes(word)) {
      throw new Error(`Forbidden language detected: ${word}`)
    }
  }

  if (output.question_text.split("?").length > 2) {
    throw new Error("Multiple questions detected")
  }
}

validators/reflection_generator.validator.ts
export function validateReflectionOutput(output: any) {
  if (!output.thinking_summary) {
    throw new Error("Missing thinking_summary")
  }

  if (!Array.isArray(output.habits_to_try)) {
    throw new Error("habits_to_try must be an array")
  }

  if (output.habits_to_try.length < 1 || output.habits_to_try.length > 2) {
    throw new Error("Invalid number of habits")
  }

  const forbidden = [
    "best move", "engine", "evaluation",
    "you should", "correct move"
  ]

  const textBlob = JSON.stringify(output).toLowerCase()
  for (const word of forbidden) {
    if (textBlob.includes(word)) {
      throw new Error(`Forbidden evaluative language: ${word}`)
    }
  }
}

