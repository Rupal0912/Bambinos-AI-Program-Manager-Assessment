# PHASE 4 — BUILD THE RENEWAL RECONCILIATION PROTOTYPE

You are continuing the Bambinos.live AI Program Manager (Operations) hiring assessment.

This phase is IMPLEMENTATION.

## STEP 1 — READ THE EXISTING WORK

Before coding, read:
- AGENTS.md
- The official assessment PDF in problem_statement/
- All Phase 1 outputs
- All Phase 2 outputs
- All Phase 3 outputs

Pay particular attention to:
- phase2_leakage_audit.md
- phase2_exception_analysis.csv
- phase3_decision_framework.md
- phase3_architecture.md
- phase3_exception_matrix.csv

Use the actual five input CSV files. Do not fabricate records or silently modify the source data.

## STEP 2 — OBJECTIVE

Build a working Python/Pandas reconciliation engine that processes:

1. 1_invoices.csv
2. 2_faculty_form_unapproved.csv
3. 3_booking_requests.csv
4. 4_class_schedule_bookings.csv
5. reference_active_batches_and_students.csv

The prototype must identify relationships, compare records, detect exceptions and generate an explainable decision for each relevant renewal case.

## STEP 3 — IMPLEMENTATION REQUIREMENTS

Use:
- Python
- Pandas
- Standard Python libraries where appropriate
- pytest for testing

Build modular, readable code.

Implement:

A. Data ingestion
- Load all five CSVs.
- Validate required columns.
- Handle missing values safely.
- Report missing or invalid input files.
- Preserve original input files.

B. Record reconciliation
- Join invoices to forms using exact invoice IDs.
- Join forms to booking requests using exact form IDs.
- Join booking requests to schedule records using exact request IDs.
- Use reference data for supporting identity and batch checks.
- Never silently match records using student ID when invoice IDs disagree.

C. Payment validation
- Detect Paid, Partially_Paid and Failed statuses.
- Identify amount conflicts.
- Do not assume amount, net_amount and amount_paid mean the same thing.
- Do not approve partially paid invoices without an explicitly configurable policy.
- Do not treat a teacher form as payment proof.

D. Exception detection
At minimum, identify:
- Paid renewal invoice without matching form.
- Form referencing nonexistent invoice.
- Multiple forms referencing one invoice.
- Partially paid invoice.
- Failed payment.
- Amount mismatch.
- Approved form without booking request.
- Full batch or unconfirmed capacity.
- Parent batch selection pending.
- Booking request without schedule rows.
- Multiple schedule rows for one request.

IMPORTANT:
Multiple schedule rows are not automatically duplicates. Check schedule IDs and dates before identifying conflicts.

E. Three decision outcomes

Generate:
- AUTO_APPROVED
- NEEDS_HUMAN_REVIEW
- BLOCKED

Every decision must include:
- Relevant invoice ID.
- Form ID, if available.
- Booking request ID, if available.
- Decision outcome.
- Reason code.
- Human-readable explanation.
- Recommended next action.
- Responsible owner.

SAFETY REQUIREMENT:
The business has not approved the proposed payment, amount, capacity or lifecycle rules.

Therefore:
- Implement provisional policy rules in a separate configurable policy file.
- Clearly label all decisions as prototype decisions, not production approvals.
- Make automatic approval configurable and disabled by default until policy sign-off.
- Do not let uncertain cases become AUTO_APPROVED.
- A hard failure such as an authoritative failed payment or invalid invoice reference must prevent downstream booking progression.
- Do not create actual booking or schedule records.

F. Audit logging
For every evaluated case, record:
- Decision ID.
- Source record IDs.
- Decision outcome.
- Reason code.
- Evidence used.
- Rule/policy version.
- Timestamp.
- Whether the decision was automatic or requires human action.

G. Idempotency
- Re-running the engine must not create duplicate output records.
- Use stable decision identifiers based on source record IDs and case type.
- Do not mutate original datasets.

## STEP 4 — OUTPUTS

Create a clean implementation structure. You may adapt it to the existing repository, but use sensible separation of concerns.

Required outputs:

1. `src/reconciliation.py`
2. `src/validators.py`
3. `src/decision_engine.py`
4. `config/policy.yaml` or an equivalent clearly documented configuration
5. `outputs/reconciliation_results.csv`
6. `outputs/exception_report.csv`
7. `outputs/audit_log.csv`
8. `outputs/reconciliation_summary.md`
9. `tests/` containing meaningful automated tests
10. `requirements.txt`
11. `README.md` with execution instructions

Do not overwrite previous Phase 1–3 deliverables.

## STEP 5 — TESTING

Write tests for:
- Exact invoice-to-form match.
- Missing form.
- Nonexistent invoice reference.
- Duplicate invoice references.
- Partially paid invoice.
- Failed payment.
- Amount mismatch.
- Approved form without request.
- Full batch with stale capacity evidence.
- Parent batch selection pending.
- Request without schedule.
- Multiple valid schedule rows.
- Repeated execution without duplicate outputs.

Use actual dataset examples where possible and synthetic test fixtures for edge cases that the five CSVs do not contain.

## STEP 6 — RUN AND VALIDATE

Run the prototype against the five actual CSV files.

Run all tests.

Verify:
- All expected output files are created.
- Output columns are present.
- Reason codes are populated.
- Original CSV files remain unchanged.
- No live API, payment gateway, messaging or booking action is triggered.

Report any failed tests and fix them before completion.

## STEP 7 — STUDENT EXPLANATION

Create:

`documentation/phase4_explanation_for_student.md`

Explain in beginner-friendly language:
- What each Python file does.
- How Pandas reads and joins the CSVs.
- How the reconciliation engine works step by step.
- What each decision outcome means.
- How exceptions are identified.
- How audit logging works.
- How to run the project.
- Examples using actual records from the dataset.

Include interview questions and answers.

## FINAL RESPONSE

At the end, report:
1. Files created.
2. How to execute the prototype.
3. Number of cases processed.
4. Number of cases in each decision category.
5. Exceptions identified.
6. Test results.
7. Known limitations.
8. Any business assumptions still requiring confirmation.

Do not start Phase 5.
Do not build n8n yet.
Do not claim production readiness.