# Phase 1: Understanding the Renewal Data (Student Guide)

## What problem are we studying?

When a parent pays to renew a child’s classes, the information passes through several people and tables before the next classes appear on the schedule. The assessment asks us to understand where that handoff can stall, then design a reliable way to process routine cases and route uncertain cases to a person. In this phase we only inspect and explain the data.

## What each CSV represents

- **`1_invoices.csv` — payment/invoice record.** It has invoice identifiers (`id`, `invoice_number`), who and what the invoice concerns (`user_id`, `student_id`, `class_id`, `educator_id`), money and payment details (`amount`, `discount_amount`, `net_amount`, `payment_type`, `payment_mode`, `payment_gateway`, gateway IDs, `payment_status`), renewal flag, and timestamps.
- **`2_faculty_form_unapproved.csv` — teacher-submitted renewal form.** It records the teacher and student, invoice reference, claimed amount paid, sessions bought, whether to continue in the same batch, preferred days/time, remarks, and approval fields. Despite its filename, this extract contains multiple `approval_status` values, including `Approved` and `Pending`.
- **`3_booking_requests.csv` — Operations booking request.** It links to a form and invoice, repeats student/class/educator identifiers, stores session and batch preferences, and tracks request/allocation status and timestamps.
- **`4_class_schedule_bookings.csv` — scheduled class instances.** It links a schedule row to a booking request, invoice, student, class, educator, batch, class date, and start/end time. One booking request can have multiple scheduled class rows in this sample.
- **`reference_active_batches_and_students.csv` — reference snapshot.** It lists student/user IDs and masked contact details alongside current batch, class, teacher, standard fee, batch days/time and capacity counts. It can help check whether a student or batch exists in this extract. Its date/freshness and authority are not stated.

## Important columns in plain [CATEGORY-NAME]

| Column | Plain meaning / what is known |
|---|---|
| `id` | Row identifier in the source file. It is unique within each of the four operational CSV samples. Confirm whether it is the database primary key. |
| `invoice_id` | A form or booking request’s stated link to an invoice row ID. One form reference is repeated, and one does not match this invoice extract. |
| `faculty_form_id` | Booking request’s stated link to a renewal form row. All four booking request values match form IDs in this sample. |
| `bookingrequest_id` | Schedule row’s stated link to a booking request. Two schedule rows reference one request. |
| `student_id`, `user_id` | Student and account/user identifiers. Both are present in multiple files and in the reference extract. The system’s precise definitions are not supplied. |
| `class_id`, `educator_id` | Class/course and teacher identifiers. Repeated across students; may represent current or intended assignment depending on table. |
| `current_classbatch_id`, `classbatch_id` | Batch identifiers. The word “current” appears in the form and reference file; `classbatch_id` appears in booking and schedule files. Confirm whether these mean current, requested, or assigned batch. |
| `amount`, `discount_amount`, `net_amount`, `amount_paid` | Invoice amount components and amount reported on the teacher form. The authoritative amount and acceptable matching rule are not defined. |
| `payment_status`, `approval_status`, `request_status`, `batch_allocated` | State fields at different steps. Similar status-like fields are not interchangeable; each needs a documented transition meaning. |
| `created_at`, `updated_at`, `paid_at`, `approved_at`, `allocated_at`, `class_date` | Event or record timestamps/dates. They can help reconstruct elapsed time after confirming timezone and event semantics. |
| `standard_fee_24_sessions_inr`, `active_students_count`, `max_batch_size` | Reference fee and reported capacity values. The snapshot timing and seat-allocation rules are not specified. |

## How the files relate

A plausible data path, supported by explicit ID-named columns, is:

`invoices.id → faculty_form_unapproved.invoice_id → booking_requests.faculty_form_id → class_schedule_bookings.bookingrequest_id`

The reference CSV can be looked up by `student_id`; batch IDs and class/teacher IDs are additional validation clues. A primary key is an identifier intended to identify one row. A foreign key is a field that points from one table to a row in another. For example, `faculty_form_unapproved.invoice_id` appears intended to point to `invoices.id`. We call these “candidate” keys until the data owner confirms the schema and rules.

## A concrete sample path

Student ID `STU-A` has a paid renewal invoice for INR [AMOUNT-A], a form saying 24 sessions and continue in batch `BATCH-A`, a completed booking request, and two scheduled class rows. The values `INV-A`, `FORM-A`, and `REQ-A` make the handoffs traceable in this example. Contact and name values are intentionally omitted here.

## What we will investigate next

The next phase should confirm join and business rules with an owner, then define exception categories and measures using the actual records. Questions include payment matching (including partial payments), handling unmatched/duplicate form invoice references, meaning of status fields, same-batch versus batch-change behavior, freshness of the reference snapshot, and capacity/seat-hold rules. Do not let an uncertain record auto-approve just because some IDs look similar.
