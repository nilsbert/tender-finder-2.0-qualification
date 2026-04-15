# 🧠 Domain Model: Qualification Context

> **Context Type:** Supporting Domain
> **Sovereignty:** Full (Private Database, Independent Tests)

---

## 1. Bounded Context Purpose

The Qualification context acts as the **decision gate** between raw scoring and actionable distribution. It evaluates whether a scored tender meets the business criteria for pursuit, applying sector-specific rules and AI-assisted analysis.

## 2. 🧱 Entities

### QualifiedTender (Aggregate Root)
- **Identity**: `tender_id`.
- **Attributes**: `qualification_status` (PENDING, QUALIFIED, REJECTED), `evaluation_score`, `rule_matches`.
- **Invariant**: Status transitions are one-directional (PENDING → QUALIFIED/REJECTED).

### QualificationFeedback
- **Identity**: `feedback_id`.
- **Attributes**: `tender_id`, `user_comment`, `decision`, `submitted_at`.
- **Purpose**: Captures human override/confirmation of automated qualification.

## 3. 💎 Value Objects

### QualificationRule
- **Attributes**: `sector`, `threshold`, `criteria_type`.
- **Purpose**: Defines the minimum requirements for a tender to be considered qualified.

### EvaluationResult
- **Attributes**: `passed_rules`, `failed_rules`, `confidence`.
- **Constraint**: Immutable after creation.

## 4. 📝 Business Rules (Invariants)

- **Threshold Compliance**: A tender must exceed all active qualification rules for its sector to be marked as QUALIFIED.
- **Human Override**: Feedback from qualified reviewers can override automated decisions.
- **One-Way Gate**: Once a tender is QUALIFIED, it cannot be reverted to PENDING.
- **Isolation**: Qualification does not modify tender data in Enriching or Rating — it only assigns status.

---
*Maintained by the Tender Finder Architectural Board*
