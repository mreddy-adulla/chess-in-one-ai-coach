# Frontend Compliance & Release Specification

## Chess‑in‑One AI Coach

**Status:** RELEASE‑BLOCKING FRONTEND COMPLIANCE AUTHORITY  
**Derived From:** Production Implementation & Compliance Package  
**Audience:** QA, Security, Audit, Release Engineering

---

## 1. Compliance Objective

This document defines **mandatory frontend compliance rules**.

Any violation is a **release blocker**.

---

## 2. Compliance Domains

### 2.1 AI Safety & Visibility

Frontend is NON‑COMPLIANT if:
- AI output appears before submission
- Partial AI output is shown
- AI identity or model is visible

---

### 2.2 Lifecycle Integrity

Frontend is NON‑COMPLIANT if:
- Game edits allowed after submission
- Back navigation bypasses states
- Client assumes state transitions

---

### 2.3 Question Flow Integrity

Frontend is NON‑COMPLIANT if:
- Questions reordered
- Multiple questions shown
- Entire position skipped in one action

---

### 2.4 Parent Governance

Frontend is NON‑COMPLIANT if:
- Child can access PCI
- Approval cached client‑side
- AI proceeds without explicit approval

---

### 2.5 Security & Privacy

Frontend is NON‑COMPLIANT if:
- AI secrets stored or logged
- Engine data displayed
- Child answers logged externally

---

## 3. Required Frontend Tests

### 3.1 State Enforcement Tests

- Attempt edit after submission → FAIL
- Attempt answer without active question → FAIL

### 3.2 AI Gating Tests

- Force AI call pre‑submission → FAIL
- Refresh mid‑session → Resume correctly

### 3.3 Parent Approval Tests

- Expired approval → Block AI
- Wrong role token → HTTP 403

---

## 4. Release Gate Checklist (Mandatory)

- [ ] No AI before submission
- [ ] Fixed question order enforced
- [ ] Parent approval enforced
- [ ] No evaluative language in UI
- [ ] No provider or model exposure
- [ ] Backend state always authoritative

---

## 5. Audit Evidence Required

Before release, archive:
- Screen recordings (key flows)
- Network logs (no AI secrets)
- Test results for all above cases

---

## 6. Compliance Status Declaration

Release is permitted ONLY if:
- All checklist items pass
- No waivers are granted

---

## END OF FRONTEND COMPLIANCE SPEC

