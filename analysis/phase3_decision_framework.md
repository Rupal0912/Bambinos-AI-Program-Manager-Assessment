# Phase 3: Three-Outcome Decision Framework

**Design proposal only.** Nothing here has been implemented or approved by the business. The proposed rules are conservative because Phase 2 exposed ambiguous invoice links, duplicate forms, partial/failed payment statuses and an undated batch-capacity snapshot.

## Outcome definitions

| Outcome | Meaning | Effect |
|---|---|---|
| `AUTO_APPROVED` | Every required fact is present, uniquely linked, and passes a deterministic rule that the business has approved. | System may create or advance the renewal booking request, with an audit record. Scheduling is a separate gate; this outcome does not promise that classes are scheduled. |
| `NEEDS_HUMAN_REVIEW` | Records are incomplete, ambiguous, inconsistent, or require a parent/Operations/Finance decision. | Hold side effects; create a queue item with evidence, owner and next action. A person resolves or records a disposition. |
| `BLOCKED` | Evidence currently contradicts eligibility or a required hard gate fails. | Do not create/advance booking or schedule rows. Keep the item blocked until source data or external state changes and it is reprocessed or reviewed. “Blocked” is not a permanent rejection of the student. |

Until payment, amount, lifecycle, batch and status rules are formally approved, a production pilot should send candidate records to `NEEDS_HUMAN_REVIEW`; the table below describes a possible future path after sign-off.

## Proposed AUTO_APPROVED gate

All conditions must pass; any uncertain check routes to review. This gate is a proposal, not current policy.

1. Payment is verified against the authoritative payment source and meets the signed-off renewal eligibility rule; the invoice is explicitly a renewal.
2. Exactly one renewal form matches `invoices.id = faculty_form_unapproved.invoice_id`; the invoice is not referenced by another unresolved form.
3. Invoice, form and trusted student record agree on required student/account/class/educator IDs. No student-ID-only fallback is allowed.
4. The settled payment amount meets the business-approved amount/currency rule. Reference standard fee is not used as proof of settlement.
5. Explicit renewal intent and batch choice are present. Same-batch continuation is affirmed, not inferred from `current_classbatch_id`.
6. A current authoritative capacity check and seat hold succeed, if capacity is a required gate.
7. Required package/schedule information is complete, no conflicting prior booking exists, and an idempotency check confirms the system has not already created the same request.
8. Rule version, evidence IDs, timestamp and outcome can be written to the audit trail.

If class dates/session instances cannot yet be safely generated, the renewal request may be auto-approved while scheduling remains pending. Business owners must define this boundary.

## Scenario decisions

Reason codes below are proposed codes. They label the evidence; they do not claim fraud or a proven service failure.

| Scenario | Outcome | Conditions and required evidence | Reason code | Next action | Owner |
|---|---|---|---|---|---|
| Paid renewal invoice with exact matching teacher form | `AUTO_APPROVED` only if every proposed gate above passes; otherwise `NEEDS_HUMAN_REVIEW` | Exact unique invoice ID link; authoritative settled payment; matching required IDs; amount rule passes; explicit intent and confirmed batch path; no duplicate/previous side effect | `AUTO_EXACT_MATCH_VERIFIED_SETTLEMENT` or `HOLD_GATE_NOT_CONFIRMED` | Create/advance one booking request and log evidence; keep scheduling state separate | Workflow service; Ops owns policy and exceptions |
| Paid invoice with no matching form | `NEEDS_HUMAN_REVIEW` | Invoice is explicitly Paid renewal; no form has exact invoice ID. Phase 2: INV-F, INV-J, INV-M | `PAID_RENEWAL_NO_EXACT_FORM` | Queue to educator/Ops to locate or submit correct form; do not match by student alone | Educator for form; Operations for queue |
| Teacher form refers to nonexistent invoice | `BLOCKED` for downstream processing; create a human review task | Form invoice ID absent from the authoritative invoice source. Phase 2: form FORM-L references INV-N | `FORM_INVOICE_ID_NOT_FOUND` | Verify source/gateway record and correct through controlled, auditable data process; never auto-relink to INV-M | Operations + Finance; educator supplies correction |
| Multiple forms refer to same invoice | `NEEDS_HUMAN_REVIEW` | More than one form shares invoice ID. Phase 2: forms FORM-G/FORM-H both reference INV-H | `DUPLICATE_FORM_INVOICE_REFERENCE` | Hold downstream creation; compare source forms and record canonical disposition | Operations |
| Partially paid invoice | `NEEDS_HUMAN_REVIEW`; `BLOCKED` only if approved policy says full settlement is mandatory and payment source confirms incomplete settlement | Gateway/source status and settled amount. Phase 2: invoice INV-I is Partially_Paid; form FORM-I reports [AMOUNT-B] vs net [AMOUNT-K] | `PAYMENT_PARTIAL_POLICY_REVIEW` | Finance confirms settled funds and business partial-payment rule; no inferred eligibility | Finance + Operations |
| Failed payment | `BLOCKED` | Authoritative payment record says Failed or no settlement after gateway confirmation. Phase 2: invoice INV-K Failed and no `paid_at` | `PAYMENT_FAILED` | Stop booking/schedule progression; verify whether a later successful attempt exists before any retry | Finance; Operations informed |
| Amount mismatch | `NEEDS_HUMAN_REVIEW` | Exact match exists but reported amount differs from approved authoritative settled-amount field/tolerance. Phase 2: form FORM-I vs invoice INV-I | `PAYMENT_AMOUNT_CONFLICT` | Reconcile gross, discount, net and settled amounts with Finance; record resolution | Finance + Operations |
| Approved form has no booking request | `NEEDS_HUMAN_REVIEW` | `approval_status=Approved` but no exact `booking_requests.faculty_form_id` exists after join refresh. Do not assume request was never created outside extract. This is a design control scenario; Phase 2's four Approved forms all had requests. | `APPROVED_FORM_NO_REQUEST` | Check source system and idempotency ledger; create missing request only under signed-off repair procedure | Operations |
| Booking request names a full batch | `NEEDS_HUMAN_REVIEW` on the assessment snapshot; `BLOCKED` for that batch assignment only if live authoritative capacity/seat hold confirms no place | Phase 2: request REQ-C `Failed_Batch_Full`, batch BATCH-D reference count 6/6; snapshot is undated | `BATCH_CAPACITY_UNCONFIRMED` or `BATCH_CONFIRMED_FULL` | Refresh/hold capacity, then offer approved alternatives and wait for parent choice | Batch owner + Operations; parent selects |
| Request awaits parent batch selection | `NEEDS_HUMAN_REVIEW` / pending parent action | `request_status=Awaiting_Parent_Batch_Selection`; Phase 2: request REQ-D, `continue_same_batch=No`, `classbatch_id` null | `PARENT_BATCH_SELECTION_REQUIRED` | Send approved choice request; resume after recorded parent selection | Parent + Operations |
| Booking request has no schedule row | `NEEDS_HUMAN_REVIEW` only when its current state, timing or integrity needs resolution; absence alone is not failure | Exact request exists, no schedule row on refreshed extract. Phase 2 has REQ-B, REQ-C, REQ-D with distinct statuses | `REQUEST_WITHOUT_SCHEDULE_REVIEW` | Check request status, expected schedule process, extract completeness and SLA; never infer failure from row absence alone | Operations / scheduling |
| Multiple schedule rows for one request | `AUTO_APPROVED` as a no-op/reconciliation result only if every row has valid links and distinct valid class occurrences; otherwise `NEEDS_HUMAN_REVIEW` | Exact request link; unique schedule IDs; distinct dates/slots as expected; cancellations considered. Phase 2 request REQ-A has rows SCHED-A/SCHED-B on Nov 3/5 with distinct `classschedule_id` | `MULTIPLE_VALID_SCHEDULE_INSTANCES_NOOP` or `SCHEDULE_CONFLICT_REVIEW` | Preserve valid rows; create no duplicate rows. Do not infer 24-session completion from row count | Scheduling service; Operations for conflicts |

## How to distinguish review from blocked

- **Review** means there may be a valid path, but a person or fresher evidence must settle a question: missing form, duplicate reference, amount ambiguity, parent choice, stale capacity, or unexplained no-schedule state.
- **Blocked** means continuing now would violate an observed hard gate: failed payment or an invalid invoice reference. Block only the action/record, not access to support. After correction or confirmation, re-run the checks and keep the prior outcome in the audit history.
- A pending status or a missing schedule is not automatically blocked. A schedule row count is not compared with purchased sessions until the business defines the expected schedule model.

## Audit record for every decision

Proposed fields: decision ID; source row IDs; invoice/form/request/schedule IDs; matched keys; evidence field/value; reason code; outcome; rule version; actor (system or person); timestamp and timezone; prior outcome; human disposition; and side effect IDs. Store enough to reproduce why a decision was made. Do not log unnecessary parent/student contact details in broad-access logs.
