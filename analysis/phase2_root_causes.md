# Phase 2 Root-Cause Analysis

## How to read this analysis

Findings are limited to the supplied extract. “Confirmed” means the values or statuses appear directly in the rows; it does not prove customer harm, cause, or an SLA breach. Interventions are proposals, not confirmed policy.

## 1. Payment-to-form linkage is not reliably explicit

**What happened:** Three of 11 invoices with literal `Paid` and `is_renewal=Yes` have no exact form link: INV-F, INV-J and INV-M. Form FORM-L instead references nonexistent invoice INV-N. Its student/user/class/educator and amount context resembles INV-M, but the direct IDs differ.

**Why it matters:** Payment may be hard to trace through teacher follow-up and scheduling. Guessing based on identity could associate a renewal with the wrong payment.

**Classification:** Missing exact links are confirmed in the extract; the operational cause could be source scope, omission or a typo. Customer outcome is unknown.

**Proposed intervention:** Require a structured invoice ID from the payment/order record; use gateway IDs as corroboration; route unresolved references to human review. Confirm whether one invoice may have multiple forms.

## 2. A repeated form reference creates duplicate-processing risk

**What happened:** Forms FORM-G and FORM-H both reference invoice INV-H, are Pending, and carry the same student and renewal details. They were created 5 minutes 12 seconds apart. They are not identical CSV rows.

**Why it matters:** Independent approval could create duplicate requests or confusing communication.

**Classification:** Repeated reference confirmed; whether one submission is erroneous is unconfirmed.

**Proposed intervention:** Stop automated processing on repeated invoice IDs and show both records to Ops. After policy approval, use an idempotency key tied to invoice and renewal cycle.

## 3. Payment status and form amount can conflict

**What happened:** Form FORM-I says [AMOUNT-B] paid for invoice INV-I. The invoice says `amount=[AMOUNT-B]`, `net_amount=[AMOUNT-K]`, `payment_status=Partially_Paid`. Form FORM-J references invoice INV-K, marked Failed with no `paid_at`.

**Why it matters:** Comparing the form to package price alone could mistake an unpaid or partly settled renewal for a completed payment.

**Classification:** Source values are confirmed; the meaning of `amount_paid` and settlement rules are unknown. This is not evidence of fraud.

**Proposed intervention:** Finance/Ops should define gateway-backed settled amount, accepted payment states, partial-payment policy and amount tolerance. Conflicts should be held for review.

## 4. Form approval and class scheduling are separate states

**What happened:** There are 4 Approved and 8 Pending forms. Four forms have booking requests. The requests have four different states: Completed (REQ-A), Pending_Batch_Allocation (REQ-B), Failed_Batch_Full (REQ-C), and Awaiting_Parent_Batch_Selection (REQ-D). Only request REQ-A has schedule rows.

**Why it matters:** Counting approved forms as completed renewals would overstate readiness; a child may still lack a selected batch or class dates.

**Classification:** Links and statuses are confirmed. Pending age, service delay, and extract completeness are unknown.

**Proposed intervention:** Track separate event times and owners for form review, allocation, parent selection and first schedule creation. Agree SLA calendars before labeling items overdue.

## 5. Capacity evidence is provisional

**What happened:** Reference batch BATCH-D shows 6 active students and maximum size 6. Request REQ-C for that batch is `Failed_Batch_Full`.

**Why it matters:** A full batch may need an alternate offer, while stale counts can wrongly block or overbook a class.

**Classification:** Values agree directionally, but the reference file has no timestamp, reservation count or seat-hold rules. The snapshot does not independently prove the failure cause.

**Proposed intervention:** Define the capacity owner, refresh cadence, whether active count includes pending reservations, and a seat-hold/confirmation step.

## 6. Traceability is promising, but schedule completeness is unknown

**What happened:** Operational student IDs resolve to the reference extract and checked user/class/educator IDs align. All requests link to forms; both schedule rows link to request REQ-A. Those two rows have distinct class dates, not duplicate class instances.

**Why it matters:** Exact IDs support deterministic reconciliation, but two scheduled rows cannot be compared with a 24-session purchase without schedule-generation rules and a complete extract.

**Classification:** Confirmed within the sample. Expected schedule coverage and system constraints are unknown.

**Proposed intervention:** Obtain schedule-generation rules and extract boundaries. Compare expected sessions only after defining a session, cancellation, reschedule and future booking.

## Severity ranking

| Priority | Root-cause signal | Frequency in sample | Potential business risk | Resolution effort |
|---|---|---:|---|---|
| 1 | Missing or incorrect exact payment-to-form reference | 3 paid invoice IDs without direct form link; one form points to absent ID | High continuity/reconciliation risk | Medium |
| 2 | Duplicate renewal-form reference | 2 forms / one repeated invoice ID | Medium-high duplicate processing risk | Low |
| 3 | Payment state/amount ambiguity | One partial amount mismatch and one failed invoice linked to a form | High payment/enrollment integrity risk | Medium |
| 4 | Pending forms and handoff visibility | 8/12 Pending; 8/12 lack a request | Potential delays; SLA unknown | Low |
| 5 | Allocation or parent selection leaves requests unscheduled | 3 of 4 requests lack schedule rows | Paid learners may not resume promptly | Medium |
| 6 | Undated capacity snapshot | One full batch associated with failed allocation | Stale data may block or overbook | Medium |

Ranks combine potential impact and ease of mitigation. Frequencies describe only this small assessment sample and must not be projected to live operations.

## Rules to confirm before Phase 3

- Payment eligibility and source of truth, including partial payments, refunds, reversals and amount tolerance.
- Whether forms can repeat per invoice and how renewal cycles are identified.
- Status meanings and whether Approved authorizes a booking request.
- Expected schedule coverage for a 24-session renewal; treatment of cancelled/rescheduled classes.
- Same-batch capacity checks, parent-selected batch recording, and seat holds.
- Reference snapshot freshness, timezone, SLA calendars, and `deleted_at` semantics.

Phase 3 should encode only confirmed deterministic rules and route unresolved records to a person. No record in this analysis was approved automatically.
