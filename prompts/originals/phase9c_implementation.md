# Phase 9C — Implement Three-Stage Decision Architecture

Project:
`<PROJECT_ROOT>`

Use the approved Phase 9B design as the implementation specification.

## Objective

Correct the Phase 4 evaluator by separating:

1. Renewal eligibility
2. Booking-request readiness
3. Scheduling readiness

The official assessment requires auto-approved entries ready for `class_schedule_bookings`, flagged exceptions and follow-up drafts.

The prototype must remain read-only.

## Before editing

Inspect the current files and create a clear implementation plan.

Use the existing Phase 9A and Phase 9B reports as design references.

Do not rewrite the entire project. Make the smallest maintainable changes.

## 1. Decision engine

Modify `src/decision_engine.py`.

- Preserve the meaning of existing `decision_outcome` as renewal eligibility.
- Keep `AUTO_APPROVED`, `NEEDS_HUMAN_REVIEW`, and `BLOCKED`.
- Move `APPROVED_FORM_NO_REQUEST` to booking-request readiness.
- A missing booking request must not independently invalidate otherwise verified renewal eligibility.
- A valid existing booking request must not automatically fail eligibility.
- Existing schedule rows must be checked for conflicts, duplication and fulfillment, not blanket-rejected.
- Preserve exact-ID matching.
- Do not weaken payment, amount, identity, approval or capacity checks.
- Keep missing or unverified evidence explicit.

Implement separate stage evaluation functions or equivalent clearly separated logic.

## 2. Stage readiness output

Add:

`outputs/stage_readiness_report.csv`

One row per evaluated case.

Include:
- case_id
- decision_id
- invoice_id
- teacher_form_id
- booking_request_id
- renewal_eligibility_status
- booking_request_readiness_status
- scheduling_readiness_status
- exclusion_reason_codes
- evidence_status_json
- policy_version
- evaluated_at_utc
- input_snapshot_sha256

Evidence statuses must distinguish:
`VERIFIED`, `MISSING`, `UNVERIFIED`, `CONFLICT`, and `NOT_APPLICABLE`.

Do not infer positive evidence from missing fields.

## 3. Scheduling-ready output

Add:

`outputs/scheduling_ready.csv`

Only include records with `READY_FOR_CLASS_SCHEDULE_BOOKINGS`.

Require:
- AUTO_APPROVED renewal eligibility.
- Exactly one valid, exact-linked booking request.
- Approved schedule-ready request state.
- Explicit parent choice when required.
- Current authoritative capacity.
- Valid seat hold.
- Verified payment and approved amount/currency rules.
- Valid student/identity evidence.
- Complete schedule parameters.
- No unresolved duplicate, conflict or fulfillment issue.
- Idempotency and audit provenance.

Do not include records merely because their form status is Approved.

Write headers even if there are zero rows.

Do not create live schedules.

## 4. Default policy and safety

Keep:
- `auto_approval_enabled=false`
- `mode=PROTOTYPE_ONLY`
- All booking writes disabled.
- All schedule writes disabled.
- All messaging writes disabled.

Do not turn on real automatic approval.

Use a separate in-memory synthetic test policy only for tests.

Never modify the actual five input CSVs.

## 5. Synthetic test scenarios

Add full end-to-end tests, not just isolated helper tests.

Required scenarios:

1. Fully evidenced synthetic case passes all three stages and produces one scheduling-ready row.
2. Approved form without request passes eligibility when all eligibility evidence is sufficient, but is excluded from scheduling readiness.
3. Missing gateway verification prevents eligibility approval.
4. Missing parent choice prevents scheduling readiness.
5. Missing capacity or seat hold prevents scheduling readiness.
6. Existing valid request is accepted.
7. Existing valid schedule rows are preserved without duplicate scheduling output.
8. Duplicate requests are rejected or reviewed.
9. Invoice/form mismatch remains excluded.
10. Failed and partial payments remain excluded.
11. Unknown approval status remains under review.
12. Existing valid schedule fulfillment is not recreated.
13. Default policy keeps automatic approval disabled.
14. Repeated runs preserve stable IDs and replace outputs rather than append.
15. Existing CSV outputs remain backward compatible.

Synthetic fixtures must remain test-only and must never be inserted into real outputs.

## 6. Reconciliation output

Modify `src/reconciliation.py` only as needed.

- Preserve existing output columns and meanings.
- Add the two new outputs.
- Retain source hashes and audit provenance.
- Preserve deterministic, stable IDs.
- Ensure empty outputs have valid headers.
- Do not modify input CSVs.
- Do not perform external side effects.

## 7. README and documentation

Update README to explain:
- Three independent stages.
- Meaning of AUTO_APPROVED.
- Difference between booking-request readiness and scheduling readiness.
- New output files.
- Why real scheduling-ready output may be empty.
- Synthetic tests versus actual dataset results.
- Read-only limitations.

Create:

`documentation/phase9_three_stage_architecture.md`

Explain the architecture, evidence requirements, outputs, tests and limitations.

## 8. Validation

Run:
- Full existing Phase 4 tests.
- All new Phase 9 tests.
- Dashboard metric tests.
- Python compilation checks.
- Reconciliation twice.

Verify:
- Original five input CSV hashes are unchanged.
- Existing output formats remain compatible.
- Actual data is not contaminated by synthetic fixtures.
- Default policy still disables automatic approval and all writes.
- No payment, booking, schedule or message actions occur.

## Final report

Provide:
1. Files modified and created.
2. Exact decision-state behavior.
3. Synthetic end-to-end test results.
4. Actual dataset outcomes for all three stages.
5. New output schemas and row counts.
6. Original input hash verification.
7. Full test-suite results.
8. Confirmation that all external writes remain disabled.
9. Any unresolved issues.

Do not claim production readiness.