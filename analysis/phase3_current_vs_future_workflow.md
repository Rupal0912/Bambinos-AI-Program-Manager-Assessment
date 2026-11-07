# Phase 3: Current vs Future Renewal Workflow

**Status: design proposal only.** The workflow below is not implemented, business-approved, or connected to live records. Statements about the sample are Phase 2 findings; new controls are proposed and require owner sign-off.

## Existing workflow and observed weaknesses

| Stage | Current process (assessment) | Observed weakness or uncertainty |
|---|---|---|
| 1. Invoice | Parent pays via payment link; invoice row is created. | Phase 2 found 3 of 11 literal Paid renewal invoices without an exact form link. Payment status and `net_amount` need definition for partial payments. |
| 2. Teacher form | Teacher manually enters/pastes invoice link, student and payment details. | Form FORM-L references absent invoice INV-N; invoice INV-H is referenced by forms FORM-G and FORM-H. Eight forms are Pending, but their age against an SLA is unknown. |
| 3. Ops verification and request | Operations compares form to invoice, approves, then creates a booking request. | Manual repeated checking; a form may be Approved without a schedule. Form FORM-I amount differs from invoice net amount for a partially paid invoice; form FORM-J points to a failed invoice. |
| 4. Batch and schedule | Parent or Ops selects batch/days/time; schedule rows are created. | Phase 2 found 3 requests without schedule rows, each with a different status. The reference capacity snapshot has no timestamp. Two schedule rows for request REQ-A are on distinct dates and are not presumed duplicates. |

Risks above describe the supplied extract and assessment narrative, not company-wide rates or proven parent harm. No SLA breach is concluded because no authoritative extract time or agreed thresholds were supplied.

## Proposed future workflow

The main redesign is to capture renewal intent once, carry stable IDs forward, reconcile payment using deterministic evidence, and let people handle exceptions. A missing form is a queue item, never a reason to guess a match.

| Step / trigger | Owner | Checks and decision | Pass path | Fail or uncertain path |
|---|---|---|---|---|
| 0. Renewal intent recorded before or with payment | Parent; teacher may initiate the request | Proposed structured intent: student ID, renewal cycle, package, explicit same-batch choice or selected alternative, preferred schedule, consent/contact channel. Do not infer future intent from `current_classbatch_id`. | Store intent ID and link it to payment metadata/order where supported. Pre-fill student/payment fields from the source so teachers confirm the learning/batch details instead of retyping IDs and amounts. | Missing/unclear intent: ask parent/teacher to confirm; no batch-change assumption. |
| 1. Invoice/payment event arrives | Payment gateway and Finance/system owner | Deterministic ingestion of invoice ID, gateway order/payment ID, `is_renewal`, currency, amount fields and status. Check event signature/source, idempotency key, and duplicate delivery. | Store read-only event and create a prefilled renewal-form draft linked to the exact invoice ID; run reconciliation once per invoice/renewal cycle. | Unknown status, missing gateway evidence, partial/failed payment: hold downstream booking; route to Finance/Ops. |
| 2. Candidate records joined | Workflow service; Operations owns exception queue | Exact `invoices.id = form.invoice_id`; exact form/request and request/schedule IDs. Compare student/user/class/educator IDs. No student-only fallback. Check form duplicates and amount under a signed-off rule. | One unambiguous candidate, consistent identifiers and payment evidence proceeds to policy checks. | Missing form, unmatched invoice ID, duplicate form or field mismatch: `NEEDS_HUMAN_REVIEW` or `BLOCKED` per decision framework. |
| 3. Eligibility decision | Deterministic rules; Operations accountable for policy | Apply only business-approved payment, identity, package, renewal, and deletion rules. Validate current student/reference data. | If all gates pass, record `AUTO_APPROVED` for the renewal booking request with evidence and reason code. | Any unresolved or contradictory evidence is held; AI cannot overrule the deterministic result. |
| 4. Batch choice and capacity | Parent chooses; Operations/batch owner maintains capacity | Require explicit parent choice for same/different batch. Query a current capacity source and obtain an atomic seat hold; reference CSV alone is not a live capacity source. Check class, teacher, days/time and restrictions. | Same-batch eligible request can proceed once the seat/slot is confirmed. A batch-change request proceeds after parent choice and capacity confirmation. | Full/unavailable batch: do not allocate; offer alternatives through an approved message and wait for parent choice. A stale snapshot or missing capacity evidence goes to human review. |
| 5. Schedule creation | Scheduling service; Operations owns exceptions | Generate schedule instances from the confirmed package and calendar rules; verify request ID, batch, dates, time, cancellation state and idempotency. | Create only missing valid instances; audit each schedule ID and source request. Distinct dates/classes for one request are allowed. | Missing selection, calendar conflict, ambiguous expected session count, or existing conflicting booking: hold for human review. Missing schedule alone is not failure until state/SLA is checked. |
| 6. Notifications and monitoring | Workflow sends approved templates; Operations handles replies | Send only when trigger and recipient are verified. Record message ID, template version, recipient, delivery status and reply/next action. | Parent receives confirmation only after a batch/schedule is actually secured. Teacher/Ops receive actionable exception tasks. | Delivery failure or no response past an approved reminder/escalation threshold returns to the owner queue. |

### Where manual work changes

- **Could be removed on the happy path after approval:** copying invoice links, manually re-keying identifiers, routine comparison of consistent IDs/amounts, and creating a duplicate request by hand.
- **Remains a human decision:** confirming ambiguous payment evidence, correcting ID conflicts, deciding on duplicate submissions, selecting a different batch for a parent, and resolving capacity or schedule conflicts.
- **No automation should infer:** that an invoice is paid from a form, that a parent wants the current batch, that one of two duplicate forms is canonical, or that a missing schedule proves failure.

## Example using actual sample records

For student `STU-A`, invoice `INV-A` is marked Paid and renewal, form `FORM-A` references that exact invoice, request `REQ-A` links to the form, and two schedule rows (`SCHED-A`, `SCHED-B`) have different dates. The future process would verify those exact links and payment evidence, preserve both valid schedule instances, and avoid creating them again. This example does not establish the complete expected 24-session schedule.

For invoice `INV-M` and form `FORM-L`, the form cites invoice `INV-N`. Even though the student context is similar, the proposed process would route the mismatch to Operations/Finance and would not silently substitute invoice INV-M.

## Draft notification text (not sent)

- **Teacher form missing:** “A renewal payment is recorded for invoice {{invoice_id}}, but we could not find a matching renewal form. Please check the renewal record for student {{student_id}} and submit or confirm the correct form reference. Do not resend payment details in chat.”
- **Payment verification required:** “We’re checking the payment linked to invoice {{invoice_id}} because the recorded status or amount needs confirmation. Please allow Operations to verify it with the payment record before class scheduling proceeds. No payment is being requested again.”
- **Possible duplicate form:** “We found two renewal forms ({{form_id_1}} and {{form_id_2}}) linked to invoice {{invoice_id}}. Operations is checking which submission should continue. Please do not submit another form for this invoice yet.”
- **Batch full:** “The requested batch {{batch_name}} is currently reported as unavailable. Please choose from the confirmed alternatives {{approved_options}} or tell us a suitable day/time so Operations can help. We will confirm only after a place is secured.”
- **Parent batch choice pending:** “Please choose the batch for the renewed classes: {{approved_options}}. We have not scheduled the classes yet. Reply with your choice or contact {{support_channel}} for help.”

Templates must be localized, checked against consent/channel rules, and approved by the business before use. They are drafts only; no messages were sent.
