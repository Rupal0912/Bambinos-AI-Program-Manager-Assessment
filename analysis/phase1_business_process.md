# Phase 1 Business Process

## Assessment context

The assessment describes Bambinos.live as an online small-group learning service for children aged 4–16. Renewals are important for retention and revenue; teachers often pitch the continuation to parents. The assessed journey spans payment through class scheduling and involves the parent/payment gateway, teacher, Operations, and parent or Operations again.

## Existing process: one observed example

The CSVs contain a coherent example for student ID `STU-A` (names and contact details are omitted here). This illustrates how the tables describe the process; it does not prove that every renewal follows the same rules.

1. **Payment / `invoices`:** invoice `BMB-INV-2026-INV-A` (`id=INV-A`) is marked `Paid`, `is_renewal=Yes`, with `net_amount=12000 INR`, `student_id=STU-A`, `class_id=CLASS-A`, and `educator_id=EDU-A`. `paid_at` is 2026-11-01 10:15:22.
2. **Teacher renewal form / `faculty_form_unapproved`:** form `id=FORM-A` references `invoice_id=INV-A`, student `STU-A`, class `CLASS-A`, educator `EDU-A`, says 24 sessions, and requests continuing in batch `BATCH-A` on Tue/Thu at 17:00. In this row, the form status is already `Approved`, with approver and time populated. Thus the file name does not mean every included row is unapproved.
3. **Ops booking request / `booking_requests`:** request `id=REQ-A` references form `FORM-A` and invoice `INV-A`. It shows 24 sessions, same-batch continuation, batch `BATCH-A`, and `request_status=Completed`, `batch_allocated=Yes`.
4. **Schedule / `class_schedule_bookings`:** two schedule rows (`SCHED-A`, `SCHED-B`) reference `bookingrequest_id=REQ-A` and invoice `INV-A`, for class dates 2026-11-03 and 2026-11-05, 17:00–17:50, in batch `BATCH-A`.

## Information passed between stages

- **Payment to renewal form:** invoice/student/user/class/educator identifiers, invoice link, amount paid, and payment confirmation are represented across the invoices and faculty form. The assessment says the teacher pastes the invoice link and student/payment details.
- **Form to booking request:** form ID, invoice/student/user/class/educator IDs, session count, batch preference, preferred days/time, and renewal/same-batch flags are represented in both tables.
- **Booking request to schedule booking:** booking request ID, invoice/student/user/class/educator/batch IDs and the selected schedule/date/time are represented in the schedule table.
- **Reference validation:** the reference file provides student/user IDs and current batch/class/educator details, plus masked contact values, standard fee for 24 sessions and batch capacity counts.

## Process uncertainties

The PDF describes the human handoffs, but does not define authoritative status transitions, what “approved” means, whether every invoice should have a form, payment amount tolerances, treatment of partial payments, or whether `current_classbatch_id`, `classbatch_id`, and a future booking batch have the same lifecycle meaning. Confirm these before implementing policy or automation.
