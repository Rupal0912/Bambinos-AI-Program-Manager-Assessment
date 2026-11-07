# Phase 7 — Create Renewal Operations SOP and Escalation Framework

Project:
`<PROJECT_ROOT>`

## Objective

Create a practical Standard Operating Procedure (SOP) for Bambinos.live's renewal operations workflow.

This is part of Deliverable D of the AI Program Manager (Operations) assessment.

The SOP must explain how a 10-person Operations team can manage renewal processing and exceptions across 200+ teachers without disrupting existing live classes.

## First: inspect existing project documentation

Read:
- `analysis/phase2_leakage_audit.md`
- `analysis/phase2_root_causes.md`
- `analysis/phase3_current_vs_future_workflow.md`
- `analysis/phase3_decision_framework.md`
- `analysis/phase3_exception_matrix.csv`
- `analysis/phase3_kpi_sla_design.md`
- `documentation/phase4_explanation_for_student.md`
- `documentation/phase6_dashboard_explanation.md`
- `config/policy.json`
- `outputs/exception_report.csv`

Use the existing reason codes, owners, decision rules and proposed SLA targets.

Do not invent company policies or claim that proposed targets are already approved.

## Create

`documentation/phase7_renewal_operations_sop.md`

### Section 1 — Purpose and scope
- Explain the renewal workflow.
- Define the teams and responsibilities.
- Identify what the SOP covers and what it does not cover.

### Section 2 — End-to-end renewal processing SOP

Document each stage:

1. Payment received.
2. Teacher renewal form submitted.
3. Invoice and form reconciled using exact IDs.
4. Payment and eligibility verification.
5. Form approval or exception routing.
6. Booking request creation.
7. Batch allocation or parent batch selection.
8. Class schedule creation.
9. Closure and audit logging.

For every stage specify:
- Trigger
- Required evidence
- Responsible owner
- System action
- Human action
- Output
- Exception conditions

Clearly distinguish booking-request creation from class-schedule creation.

### Section 3 — Exception handling SOP

Use the existing exception taxonomy.

For each reason code document:
- Meaning
- Severity
- Responsible team
- First action
- Escalation condition
- Required closure evidence

Do not merge reason codes merely because they look similar.

### Section 4 — AI versus human responsibility matrix

Explicitly distinguish:
- Deterministic automated validation
- AI-assisted drafting or summarization
- Human approval and judgment
- Actions prohibited without verified authorization

AI must not independently:
- Confirm a payment without authoritative payment evidence.
- Resolve ambiguous invoice references through student ID alone.
- Approve disputed or partial payments.
- Override capacity constraints.
- Select a batch on behalf of a parent without authorization.
- Create live schedules without required booking and calendar validation.

### Section 5 — Daily Operations checklist

Create:
- Morning dashboard review
- Queue assignment
- Exception prioritization
- Midday backlog check
- End-of-day reconciliation
- Shift handover

Use the dashboard KPIs and actionable queue as the operational source of truth for the prototype.

### Section 6 — Escalation matrix

Use Phase 3 proposed SLA targets.

Clearly label all targets as proposals requiring business validation.

Include:
- First response target
- Resolution target
- Escalation trigger
- Escalation owner
- External dependency handling

Do not convert business-hour targets into elapsed-hour targets without justification.

### Section 7 — Team operating model

Explain how a 10-person Operations team could divide responsibilities.

Propose roles and backup coverage rather than inventing actual employee names.

Explain how the model scales across 200+ teachers.

### Section 8 — Safety and change control

Include:
- No changes to existing live schedules during initial rollout without authorization.
- No silent data correction.
- No deletion or overwriting of source records.
- Complete audit trail for decisions.
- Human review for exceptions.
- Rollback and incident escalation.

### Section 9 — Open policy decisions

Explicitly list unresolved business questions:
- Authoritative payment amount field.
- Partial payment eligibility.
- Duplicate form policy.
- Meaning of approval statuses.
- Parent choice requirements.
- Capacity freshness and seat-hold policy.
- Expected schedule rows per renewal.
- Deleted record semantics.
- Timezone and SLA clock definitions.

## Quality requirements

- Operational, concise and specific.
- Use tables where they improve clarity.
- Avoid generic textbook explanations.
- Do not invent policies, people, metrics or actual SLA performance.
- Preserve consistency with existing Phase 2, 3, 4 and 6 artifacts.
- Do not modify source code, CSV files, policy files or existing dashboard files.

## Final report

Report:
1. File created.
2. Sections completed.
3. Existing reason codes covered.
4. SLA targets reused.
5. Any inconsistencies or missing information found.
6. Confirmation that no existing project files were changed.