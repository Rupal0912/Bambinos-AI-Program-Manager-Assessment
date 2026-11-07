# Phase 2 Leakage Audit

## Executive summary

The supplied extract contains 13 invoices, 12 teacher forms, 4 booking requests, 2 schedule rows, and 13 student/reference rows. Using the literal eligibility rule `payment_status=Paid` AND `is_renewal=Yes`, there are **11 eligible paid renewal invoices**. Of these, **3 (27.3%)** have no exact `invoice_id` form link; **8 (72.7%)** have at least one. This is an extract-level linkage signal, not a company-wide leakage estimate or proof of lost service.

Other key findings: one form (FORM-L) references invoice INV-N, which is absent; invoice INV-H is referenced by two forms; one form amount differs from net amount on a partially paid invoice; eight forms are Pending; and three booking requests have no schedule row. The schedule gaps have distinct states: batch allocation pending, batch full, and awaiting parent selection. No student, user, class, or educator mismatches were found in linked form/request pairs or in the reference lookups checked.

## Scope and interpretation

- **Paid-renewal eligibility:** exact observed values `payment_status=Paid` and `is_renewal=Yes`. The 13 invoice rows comprise 11 Paid, 1 Partially_Paid, and 1 Failed; all are marked renewal. Partial and failed rows are investigated separately.
- All `deleted_at` values are null, but null is not assumed to mean active. Counts cover supplied rows because deletion semantics and extract scope are unconfirmed.
- Joins use exact IDs only: `invoices.id = form.invoice_id`; `form.id = booking.faculty_form_id`; `booking.id = schedule.bookingrequest_id`; reference lookup by `student_id`. Similar student details or amounts do not substitute for an absent direct ID.
- Timestamp strings have no timezone offsets or timezone declaration. Durations use the values as supplied. Event meanings of `paid_at`, `created_at`, `approved_at` and schedule `created_at` need confirmation. `class_date` is not schedule creation time.
- No official extract/as-of timestamp or SLA target was supplied. The latest row update shown is 2026-11-03 18:00:00. Pending does not by itself prove overdue.
- This is a small assessment sample, not a representative company-wide cohort. P90 is omitted because usable samples are too small for a stable tail estimate.

## Investigation A: invoice to teacher form

- **Paid renewal invoices without an exact form link:** `INV-F`, `INV-J`, `INV-M` (3 of 11). Form FORM-L may be related to INV-M by student/user/class/educator and amount context, but it says `invoice_id=INV-N`; do not silently repair this link.
- **Form without invoice row:** form FORM-L references INV-N, not present in the invoice file.
- **Duplicate invoice reference:** forms FORM-G and FORM-H both reference invoice INV-H. Both are Pending with matching student and renewal details; creation times are 5 minutes 12 seconds apart. They are not exact duplicate rows.
- **Amount comparison:** 10 of 11 directly matched form rows equal invoice `net_amount`. Form FORM-I reports [AMOUNT-B] while invoice INV-I has `net_amount=[AMOUNT-K]`, `amount=[AMOUNT-B]`, and `payment_status=Partially_Paid`. The meaning of `amount_paid` is unclear.
- **Identity/assignment checks:** directly matched invoice/form pairs agree on `student_id`, `user_id`, `class_id`, and `educator_id`. All invoice and form student IDs resolve in the reference file; checked user/class/educator values agree.
- **Payment vs approval:** invoice INV-K is Failed while form FORM-J is Pending and has no `paid_at`; invoice INV-I is Partially_Paid while form FORM-I is Pending. Of the 11 exact-matched form rows, 4 are Approved and 7 Pending; unmatched form FORM-L is Pending (12 forms overall: 4 Approved, 8 Pending). Form approval does not establish successful payment.

## Investigation B: teacher form to booking request

- Four forms have requests: `FORM-A→REQ-A`, `FORM-B→REQ-B`, `FORM-E→REQ-C`, `FORM-K→REQ-D`. Eight do not: `FORM-C`, `FORM-D`, `FORM-F`, `FORM-G`, `FORM-H`, `FORM-I`, `FORM-J`, `FORM-L`.
- Every request links to an existing form. Request IDs and `faculty_form_id` values are unique in this sample.
- Across all four linked pairs, student, invoice, class, educator, session count, same-batch flag, preferred days, and preferred time agree.
- The four Approved forms lead to request statuses Completed, Pending_Batch_Allocation, Failed_Batch_Full, and Awaiting_Parent_Batch_Selection. Only request REQ-A has schedule rows.
- Eight forms are Pending and have null `approved_at`. Without an as-of time and SLA, their overdue status cannot be determined.

## Investigation C: booking request to schedule

- Requests `REQ-B`, `REQ-C`, and `REQ-D` have no schedule rows; request `REQ-A` has two. All schedule rows refer to a valid request.
- The two schedule rows for REQ-A have distinct dates (Nov 3 and Nov 5), distinct `classschedule_id` values, and are not duplicate class instances on the fields supplied. Both have `is_cancelled=No`. No exact duplicate schedule rows or checked ID mismatches were observed.
- REQ-B is `Pending_Batch_Allocation`; REQ-C is `Failed_Batch_Full`; REQ-D is `Awaiting_Parent_Batch_Selection`, `continue_same_batch=No`, and has null `classbatch_id`. These are observed states, not proof that a service SLA was missed.
- The expected number of schedule rows for a 24-session purchase is not supplied. Two schedule rows do not prove that 24 sessions are scheduled, and fewer rows do not prove under-scheduling. `class_date` is the class occurrence date; `created_at` is when the schedule row was recorded, subject to timezone/event-definition limits.
- `classschedule_id` is unique in this sample and appears to identify a schedule occurrence; its formal meaning is unconfirmed.

## Investigation D: reference validation and capacity

- All invoice (13/13), form (12/12), booking request (4/4), and schedule (2/2) student IDs resolve to a reference row. Checked user, class and educator IDs agree.
- Every form `current_classbatch_id` resolves to a reference batch. Non-null request and schedule batch IDs also resolve. Same-batch form preferences align with the reference row. Form FORM-K explicitly requests a different batch (`continue_same_batch=No`), so its Sat/Sun 11:00 preference differs from current batch BATCH-C; that is a change request, not inherently an inconsistency.
- Provisional remaining seats (`max_batch_size - active_students_count`) by distinct reference batch: BATCH-A:2; BATCH-B:1; BATCH-C:3; BATCH-D:0; BATCH-K:1; BATCH-E:2; BATCH-F:1; BATCH-G:2; BATCH-L:1; BATCH-H:1; BATCH-I:2. Batch BATCH-D is shown full (6/6), and request REQ-C for it is `Failed_Batch_Full`. This is consistent but does not prove the snapshot caused the failure.
- The reference file has no snapshot time, active-count definition, or seat-hold/concurrency rule. Capacity and availability findings are provisional.
- Reference fee is package/list-price context, not proof of funds settled. Invoice INV-G has amount [AMOUNT-F], discount [AMOUNT-I], net [AMOUNT-J]; its form reports [AMOUNT-J]. Invoice INV-I is Partially_Paid at [AMOUNT-K] net while the form says [AMOUNT-B].

## Investigation E: time and process delays

| Interval | Valid pairs | Missing endpoint/pair | Zero-hour | Min hours | Median hours | Max hours | P90 |
|---|---:|---:|---:|---:|---:|---:|---|
| Payment to teacher form creation | 10 | 1 | 0 | 0.2469 | 0.4511 | 0.8306 | N/A (small sample) |
| Form creation to approval | 4 | 8 | 0 | 0.7500 | 1.5417 | 2.5000 | N/A (small sample) |
| Form creation to booking request | 4 | 0 | 0 | 0.7500 | 1.5417 | 2.5000 | N/A (small sample) |
| Booking request to first schedule creation | 1 | 0 | 0 | 0.5014 | 0.5014 | 0.5014 | N/A (small sample) |
| Payment to first schedule creation | 1 | 10 eligible invoices without valid pair | 0 | 1.7453 | 1.7453 | 1.7453 | N/A (small sample) |

Payment-to-form statistics count exact-matched form events; invoice INV-H contributes two forms. One matched record (failed invoice INV-K) has no `paid_at`. Form-to-approval has eight missing endpoints (Pending); form-to-booking has eight missing pairs (no request). These are missing events, not zero-hour delays. For schedule measures, the earliest linked non-cancelled schedule creation is used. The single payment-to-first-schedule observation is invoice INV-A. No negative or zero durations were observed.

## Investigation F: operational KPIs

See [`phase2_kpi_results.csv`](phase2_kpi_results.csv) for each definition, formula, numerator, denominator, result, sources, and limitations.

| KPI | Result | Numerator / denominator | Interpretation |
|---|---:|---:|---|
| Orphaned Invoice Rate | 27.3% | 3/11 | Paid renewal invoices with no exact form link |
| Invoice-to-Form Match Rate | 72.7% | 8/11 | Distinct paid renewal invoices with exact form link |
| Duplicate Invoice Reference Rate | 16.7% | 2/12 | Form records affected by repeated invoice reference |
| Payment Amount Mismatch Rate | 9.1% | 1/11 | Matched form rows differing from invoice net amount |
| Form-to-Booking Conversion Rate | 33.3% | 4/12 | Forms with a request in this snapshot |
| Pending Teacher Form Rate | 66.7% | 8/12 | Pending status; overdue not established |
| Approved but Unscheduled Request Rate | 75.0% | 3/4 | Approved-form requests with no schedule row |
| Failed Batch Allocation Rate | 25.0% | 1/4 | Requests explicitly marked Failed_Batch_Full |
| Payment-to-Schedule Turnaround | 1.7453 hours (n=1) | 1 valid pair | Not a stable performance estimate |
| Overall Exception / Review Signal Rate | 90.9% | 10/11 | Proposed review-signal union, not confirmed failure rate |

The overall exception/review KPI is explicitly a proposed measure: count distinct eligible paid invoice IDs with any enumerated linkage, duplicate, pending, failed, allocation, or selection signal. Pending states may still be within SLA. It should not be presented as proven leakage.

## Root-cause themes and severity ranking

| Rank | Finding | Sample frequency | Potential impact/risk | Confidence | Ease | Proposed intervention |
|---:|---|---:|---|---|---|---|
| 1 | Missing or incorrect payment-to-form reference | 3 paid invoice IDs lack exact form link; 1 form points to absent ID | High continuity/reconciliation risk | Linkage fact confirmed; cause unknown | Medium | Require structured invoice ID; route unresolved references to Ops for source verification |
| 2 | Duplicate renewal-form reference | 2 forms cite invoice INV-H | Duplicate approval or scheduling risk | Repeated reference confirmed; error status unknown | Easy | Human disposition; define idempotency rule after policy approval |
| 3 | Payment status/amount ambiguity | 1 partial mismatch and 1 failed invoice linked to form | High payment/enrollment integrity risk | Values confirmed; amount semantics unknown | Medium | Define gateway settlement source, partial-payment policy, and amount tolerance; hold conflicts |
| 4 | Pending forms and handoff visibility | 8/12 Pending; 8/12 lack request | Potential delays; SLA breach unknown | Snapshot states confirmed | Easy | Add queue owner, age, and agreed SLA thresholds |
| 5 | Allocation or parent selection leaves requests unscheduled | 3 of 4 requests lack schedule | Paid learners may not resume promptly | Current states confirmed; duration unknown | Medium | Separate owner queues for allocation, failure, parent selection |
| 6 | Undated capacity snapshot | Batch BATCH-D shown 6/6 with failed request | Stale data may block or overbook | Provisional | Medium | Timestamp capacity and define reservation/refresh rules |

Sample frequencies must not be extrapolated to company-wide operations. Record-level triage is in [`phase2_exception_analysis.csv`](phase2_exception_analysis.csv).

## Data limitations and business clarification

1. Confirm production payment eligibility and handling for partial payments, refunds, chargebacks, reversals, and deleted rows.
2. Define whether `amount_paid` means settled funds, package price, or another value; establish currency/rounding/tolerance and payment source of truth.
3. Confirm whether an invoice can have multiple forms and how repeated submissions are handled.
4. Define status meanings/transitions for `approval_status`, `request_status`, `batch_allocated`, and `is_cancelled`.
5. Establish expected schedule generation/coverage for a 24-session renewal and handling of cancelled/rescheduled sessions.
6. Confirm reference snapshot timestamp, active-count definition, seat holds, concurrency and same-batch capacity rules.
7. Provide timezone, event definitions, extract as-of time, SLA calendars, and weekend treatment.
8. Confirm `deleted_at` semantics and whether these extracts include inactive/deleted rows.

## Reproducibility

Results were recomputed directly from the five CSVs with pandas and the exact ID joins described above. KPI denominators use raw extract rows except where the formula specifies distinct invoice IDs. The exception file has one row per source-record/reason pair; the overall review-signal KPI deduplicates to invoice ID. Original CSVs and Phase 1 documents were not edited.
