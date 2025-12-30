# chess-in-one-ai-coach
## Consolidated Requirements Specification (Complete)

---

## 0. Purpose

This document defines the **complete and authoritative requirements** for the *chess-in-one-ai-coach* application.

It consolidates **all requirements** from prior specifications into a **single, comprehensive baseline**, without reference to any external or prior documents.

This specification:
- Preserves **all functional, system, AI, governance, and platform requirements**
- Avoids design, UI, and implementation details
- Is written as a freshly authored, standalone requirements document

This document is suitable for:
- Product definition
- System architecture
- Design handoff
- Verification and acceptance testing

---

## 1. Product Intent (Non‑Negotiable)

The system is a **post‑game chess coaching application** focused on improving **thinking habits**, not move accuracy.

Target user profile:
- Junior competitive chess player
- Fast, intuitive decision‑maker
- Tactically strong
- Frequently misses opponent intentions and positional shifts
- Responds poorly to lectures, scores, or engine‑centric feedback

### Core Objective

The system SHALL:
- Capture the player’s own thinking first
- Identify missing thinking dimensions
- Use structured Socratic questioning
- Provide minimal, calm, reflective guidance

The system SHALL NOT:
- Judge performance
- Assign scores or evaluations
- Teach by lecturing or authoritative explanation

---

## 2. System Scope & Mode

### 2.1 Supported Mode

- The system SHALL operate **strictly in post‑game mode**

### 2.2 Explicit Exclusions

The system SHALL NOT support:
- Live boards
- Clock‑aware behavior
- In‑game move suggestions
- Real‑time coaching
- Chat‑style interaction
- Engine‑first analysis

---

## 3. High‑Level System Overview

The system consists of:
- Android client
- Web client
- Private backend service
- AI subsystems for analysis, questioning, and reflection

The system is not a public cloud service and is not a general chess platform.

---

## 4. Game Creation & Lifecycle

### 4.1 Game Creation

The system SHALL allow creation of a game with:
- Player color
- Opponent name
- Event
- Date
- Time control

### 4.2 Game Input

The system SHALL support:
- Manual move‑by‑move entry
- PGN import

### 4.3 Game Export

The system SHALL support export of:
- Game moves
- Player annotations
- AI guidance
in PGN format.

### 4.4 Game Lifecycle Control

The lifecycle SHALL be strictly:

`Editable Game → Submitted Game → AI‑Coached Game`

This transition SHALL be:
- Single‑direction
- Irreversible

Once AI questioning begins, the system SHALL NOT allow:
- Game edits
- Annotation edits
- AI re‑submission without parent approval

---

## 5. Annotation Phase (Pre‑AI)

### 5.1 Annotation Rules

- Annotations SHALL be allowed **only on player moves**
- Annotations SHALL be optional per move
- Empty, skipped, or “Don’t remember” annotations SHALL be permitted

### 5.2 Input Methods

Each annotation SHALL support:
- Voice input
- Text input (mandatory fallback)

### 5.3 AI Isolation

During this phase:
- No AI feedback SHALL be visible
- No hints or suggestions SHALL appear
- No corrections SHALL be provided

---

## 6. AI Invocation

### 6.1 Submission Control

- The system SHALL provide a single explicit action to submit a game to the AI Coach
- Submission SHALL freeze all annotations
- AI processing SHALL occur asynchronously

### 6.2 AI Visibility Rules

The AI SHALL remain completely invisible until:
- All annotations are complete or skipped
- The game is explicitly submitted

The AI SHALL NOT generate:
- Partial feedback
- Board highlights
- Hints
prior to submission.

---

## 7. Key Position Identification

### 7.1 Selection Rules

The AI SHALL identify **3–5 key positions per game**.

Key positions SHALL be selected based on:
- Missed opponent intent
- Threat awareness gaps
- Positional transitions
- Thinking relevance

Blunder severity SHALL NOT be the primary criterion.

### 7.2 Analysis Limitation

The system SHALL prevent analysis of every move.

---

## 8. Guided Questioning

### 8.1 Session Structure

For each key position, the system SHALL:
- Display the board
- Display the player’s original annotation (if any)

### 8.2 Question Flow Control

- Questions SHALL be asked one at a time
- The sequence SHALL be fixed and non‑reorderable
- Sessions SHALL be sequential and non‑parallel
- The system SHALL prevent skipping the entire questioning phase with one action
- Skipped questions SHALL be recorded internally

### 8.3 Mandatory Question Sequence

Each key position SHALL follow this exact sequence:
1. Opponent intent
2. Threat awareness
3. Change detection
4. Worst‑piece identification
5. Plan alternatives
6. Reflection on move choice

The category order is immutable; phrasing may adapt.

### 8.4 Explanation Timing

The AI SHALL NOT explain or correct until:
- All questions for that position are answered or skipped

---

## 9. AI Reflection & Guidance

After all key positions are completed, the AI SHALL generate exactly:

1. **How the player was thinking**
2. **What thinking elements were missing**
3. **One or two habits to try next game**

The AI SHALL NOT:
- Assign scores
- Label moves as good or bad
- Use evaluative or authoritative language
- Overload with information

---

## 10. AI Role Contracts

### 10.1 Chess Situation Analyzer

Responsibilities:
- Understand positions
- Detect threats and positional shifts
- Flag thinking‑relevant moments

Prohibitions:
- No user interaction
- No explanations
- No evaluations

### 10.2 Socratic Questioner

Responsibilities:
- Select key positions
- Ask only locked‑sequence questions
- Adapt phrasing to age and responses

Prohibitions:
- No correcting answers
- No teaching moves
- No new question categories

### 10.3 Reflection & Guidance Agent

Responsibilities:
- Summarize thinking patterns
- Identify omissions
- Provide minimal guidance

Prohibitions:
- No authoritative tone
- No rewriting player annotations

---

## 11. Parent Control & Governance

### 11.1 Approval Requirements

- Any non‑default AI tier SHALL require parent approval
- Second and subsequent AI runs on the same game SHALL require approval
- Approval methods MAY include PIN or platform biometrics

### 11.2 Parent Visibility

Parents SHALL be able to view:
- AI usage count per game
- Requested AI tier
- Estimated session duration

Parents MAY define:
- One‑time approvals
- Time‑window approvals

---

## 12. Failure & Recovery

- AI failures SHALL preserve completed answers
- Sessions SHALL resume from the last unanswered question
- The system SHALL NOT silently retry AI invocations
- AI failures SHALL be surfaced to parents, not the child

---

## 13. Metrics & Analytics

### 13.1 Internal Metrics

The system MAY track:
- Skipped questions
- Response latency
- Repeated thinking omissions

### 13.2 Usage Restrictions

Metrics SHALL NOT be used for:
- Rankings
- Player comparison
- Performance scoring

---

## 14. Platform Constraints

### 14.1 Android Client

- Voice‑first interaction
- Mandatory text fallback
- Tolerant of interruptions
- Optimized for short sessions (5–7 minutes)

### 14.2 Web Client

- Optimized for long review sessions (15–20 minutes)
- Keyboard‑centric workflows
- Full PGN workflows

### 14.3 Cross‑Platform Rules

- Behavioral flow SHALL be identical
- Differences limited to interaction convenience

---

## 15. Backend & Security Constraints

- Backend SHALL run as a private service
- Access SHALL be restricted to authenticated devices
- No public exposure is permitted
- AI provider mappings SHALL reside exclusively on the backend
- Clients SHALL NEVER store AI provider credentials
- AI requests SHALL exclude identifying personal information

---

## 16. Compliance Guardrails

The system is NON‑COMPLIANT if:
- AI appears before submission
- Question order is altered
- Parent approval is bypassed
- Evaluative language is used
- Client accesses AI secrets

---

## END OF DOCUMENT
