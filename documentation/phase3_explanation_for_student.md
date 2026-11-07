# Phase 3: Designing a Safer Renewal Workflow

## What are we designing?

We are designing how payment information can travel from an invoice to a class booking with fewer repeated manual checks. This is a **design**, not software that has been connected to Bambinos.live. No records were approved, changed or messaged.

Phase 2 showed that exact records can be joined, but the extract also contains missing and repeated links, partial/failed payment states, and booking requests in different scheduling states. So the design automates clear checks and keeps uncertain cases with a person.

## The three decision outcomes

- **`AUTO_APPROVED`** means every required fact passes a deterministic rule that the business has approved. The system may advance a renewal request once, with a record of the evidence. It does **not** mean classes are already on the schedule.
- **`NEEDS_HUMAN_REVIEW`** means a person needs to resolve an uncertainty, such as two forms using one invoice ID or a parent choosing a batch. The system pauses the action and creates a task for the right owner.
- **`BLOCKED`** means there is evidence that makes it unsafe to proceed right now, such as an authoritative failed payment or a form pointing to an invoice that cannot be found. A person can still investigate and unblock it after correcting or confirming the source.

These are proposed labels and rules. Until the business approves its payment, amount, capacity and status rules, candidate cases should stay in review.

## How the future process works

1. **Record what the parent wants.** Before or during payment, capture the student, package, renewal cycle and an explicit choice to stay in the current batch or choose another. The current batch in a reference file is not proof that the parent wants to continue there.
2. **Receive the payment event.** Save the invoice ID and payment-provider transaction IDs. A form or a message is not payment proof.
3. **Join records by exact IDs.** Invoice ID links the invoice to the form; form ID links to the request; request ID links to schedule rows. Compare student, class and teacher IDs as additional checks. Do not connect different invoice IDs just because student details look similar.
4. **Run safe rules.** Confirm the payment status, amount rule, unique form, student details, renewal intent and (when needed) live batch capacity. These are ordinary data checks, not AI decisions.
5. **Route the result.** A clean, uniquely linked case can be auto-approved only after its rule is approved. Missing or conflicting evidence goes to a human queue. A hard failed gate blocks booking until someone verifies it.
6. **Choose and reserve a batch.** Use a current capacity source and reserve a seat. If the parent wants to change batches, wait for their explicit choice. The Phase 2 reference file has no snapshot time, so its counts cannot safely reserve a live seat.
7. **Create schedule rows.** Generate class instances only after batch and calendar rules are confirmed. Multiple schedule rows can be normal because one request may have multiple class dates. Check each row; do not remove rows just because they share a request ID.
8. **Log and notify.** Save the decision, reason, rule version, actor, time and any created request/schedule IDs. Send only approved messages; drafts in the workflow document were not sent.

## Example 1: an exact, clean link

Student `STU-A` has Paid renewal invoice `INV-A`, form `FORM-A` references invoice `INV-A`, booking request `REQ-A` references form `FORM-A`, and schedule rows `SCHED-A` and `SCHED-B` reference request `REQ-A` on different dates. A future system can verify the exact links and avoid creating those schedule rows a second time. The two rows do not prove that all 24 sessions are covered; the business has not supplied the rule for that.

## Example 2: similar student details, different invoice IDs

Invoice `INV-M` is a Paid renewal. Form `FORM-L` says `invoice_id=INV-N`, which is not in the invoice file. Even though the student context looks similar, the system should not assume the form belongs to invoice INV-M. Operations/Finance should verify the payment source and record any correction with an audit trail.

## Example 3: duplicate and payment uncertainty

Forms `FORM-G` and `FORM-H` both reference invoice `INV-H`. They are both Pending and contain the same renewal details, but they are separate rows. The system should hold them for an Operations decision. Separately, form `FORM-I` reports [AMOUNT-B] for invoice `INV-I`, whose `net_amount` is [AMOUNT-K] and status is Partially_Paid. Finance must define what “amount paid” means before the system can decide whether that renewal qualifies.

## Example 4: approved does not mean scheduled

Booking request `REQ-C` comes from an Approved form but is marked `Failed_Batch_Full`. The reference snapshot shows batch `BATCH-D` at 6 of 6, but there is no timestamp for that snapshot. Operations must check current capacity and help the parent choose an available option. The system should not tell the parent the class is scheduled until a seat and schedule are actually confirmed.

## What the architecture tools do

- **SQL or Python** compare exact IDs, payment states, amounts, duplicates and capacity values using clear rules.
- **n8n** can start a workflow when a payment event arrives, route results to the right queue and send an approved template. It coordinates steps; it does not decide if a payment is valid.
- **A restricted Ops queue** shows the record IDs, evidence, reason and owner so a person can resolve it. A spreadsheet should not become the authoritative payment or enrollment database.
- **An audit log** records why the workflow made a decision and what it changed. This makes it possible to explain and review the result later.
- **AI is optional** for summarizing a case or drafting wording from an approved template. It must not decide payment eligibility, repair invoice IDs, approve a student or create classes.

## KPIs and SLAs in simple terms

A KPI measures a result, such as the share of paid renewal invoices with a matching form. An SLA is an agreed time expectation, such as how quickly Operations reviews a payment exception. Phase 2 has some timestamps, so it supports a small snapshot measure of form approval time. It does not contain `resolved_at` for exception cases, so exception resolution time cannot yet be calculated.

The Phase 3 KPI document separates what can be counted from the current CSVs, what needs new event data, and suggested SLA targets. The suggested targets are proposals only. They are not actual performance and need approval from Operations/Finance, including decisions about weekends, holidays and timezones.

## Terms you may hear

- **Exact ID join:** match rows only when their designated identifier values are equal.
- **Exception queue:** a list of cases that need a person to investigate or decide.
- **Idempotency:** running the same event again does not create another copy of the same booking.
- **Audit trail:** the saved explanation of what was checked, who/what decided, and when.
- **Seat hold:** temporarily reserve a place so another request cannot take it while booking finishes.
- **Shadow mode:** compare proposed system decisions with Operations decisions without making live changes.
- **Human-in-the-loop:** a person makes the decision when the evidence is unclear or a customer choice is needed.

## What is still unknown?

Before implementation, the business should confirm payment eligibility and partial-payment rules, what amount field is authoritative, duplicate-form policy, status transitions, expected schedule rows for a package, parent consent and batch-choice rules, live capacity/seat-hold behavior, `deleted_at` meaning, timezone and SLA calendar.

## Questions an interviewer may ask

1. Why not match form FORM-L to invoice INV-M using `student_id`? Because the explicit invoice IDs conflict; a wrong payment-to-student association is risky, so a human verifies it.
2. Why use AI at all? It may save time drafting explanations, but deterministic rules are safer for payments and enrollment.
3. Does `AUTO_APPROVED` guarantee classes are scheduled? No. Approval, seat allocation and schedule creation are separate steps with separate checks.
4. Are two schedule rows duplicates? Not automatically. In the sample, request REQ-A has two different class dates and schedule IDs.
5. What is the biggest implementation dependency? Business-approved rules for payment state, amounts, capacity, schedule completeness and SLAs. Until they exist, the safe result is human review.
