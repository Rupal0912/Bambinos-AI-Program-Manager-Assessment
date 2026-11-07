# Reconciliation Prototype Summary

**Prototype only. No live payment, booking, schedule, or messaging action was performed.**
Automatic approval is disabled by default in the policy file.

## Run summary

- Evaluated renewal cases: 14
- `AUTO_APPROVED`: 0
- `NEEDS_HUMAN_REVIEW`: 12
- `BLOCKED`: 2
- Exception findings: 28
- Cases with booking requests ready to create: 0
- Cases ready for `class_schedule_bookings`: 0
- Scheduling-ready occurrence rows: 0
- Policy version: `phase4-prototype-1.0`
- Input snapshot SHA-256: `cef95432ef66a98709db4e39de2e584ca3e38b9e8f9bd39f05a78c09fa20b139`
- Input rows: invoices=13, forms=12, requests=4, schedules=2, reference=13

## Exception counts by reason code

| Reason code | Cases/findings |
|---|---:|
| `BATCH_CAPACITY_UNCONFIRMED` | 1 |
| `DUPLICATE_FORM_INVOICE_REFERENCE` | 2 |
| `FORM_BATCH_NOT_IN_REFERENCE` | 1 |
| `FORM_INVOICE_ID_NOT_FOUND` | 1 |
| `FORM_PENDING` | 8 |
| `FORM_REQUEST_BATCH_MISMATCH` | 1 |
| `FORM_REQUEST_FIELD_MISMATCH` | 1 |
| `MULTIPLE_VALID_SCHEDULE_ROWS` | 1 |
| `PAID_RENEWAL_NO_EXACT_FORM` | 3 |
| `PARENT_BATCH_SELECTION_PENDING` | 1 |
| `PAYMENT_AMOUNT_CONFLICT` | 1 |
| `PAYMENT_FAILED` | 1 |
| `PAYMENT_PARTIAL_POLICY_REVIEW` | 1 |
| `REQUEST_FAILED_BATCH_FULL` | 1 |
| `REQUEST_PENDING_BATCH_ALLOCATION` | 1 |
| `REQUEST_WITHOUT_SCHEDULE` | 3 |

## Safety and interpretation

- Decisions are deterministic prototype outputs using the configured provisional policy; they are not production approvals.
- Exact IDs are used for joins. No fuzzy/student-only invoice matching is performed.
- `AUTO_APPROVED` means only that configured renewal eligibility checks passed; it does not create a booking request or class schedule. An exactly linked form must have `approval_status=Approved`; Pending and other statuses require Operations review.
- The default policy disables auto approval. The supplied data also lacks payment verification, explicit parent batch-choice confirmation, an explicit student-active field, and authoritative live capacity.
- The reference capacity file is treated as non-authoritative. A full reference count is a review signal, not a confirmed live allocation failure.
- Missing schedule rows and multiple schedule rows are not automatically treated as failure or duplicates. Expected session totals are not inferred.
- Null `deleted_at` is not interpreted as active.
- Draft messages are output text only and are not sent.
- Output CSVs are replaced on each run; stable case/decision/exception IDs prevent duplicate rows on rerun.
- The audit log records source IDs, selected values used by checks, policy version, UTC evaluation time, per-file SHA-256 hashes, and a combined input snapshot hash. This is a stronger prototype audit trail, not production-grade audit storage.

## Business rules still requiring confirmation

Payment eligibility and source of truth; amount semantics/tolerance; partial payment policy; duplicate-form disposition; status transitions; current student lifecycle; parent choice; live capacity and seat holds; schedule-generation rules; timezone/SLA calendars; and deletion semantics.
