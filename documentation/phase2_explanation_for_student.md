# Phase 2: What the Data Says About Renewal Delays

## What we investigated

We traced the renewal path with exact ID comparisons:

1. Invoice `id` to form `invoice_id`.
2. Form `id` to booking request `faculty_form_id`.
3. Booking request `id` to schedule `bookingrequest_id`.
4. Student, class, teacher and batch information against the reference file.
5. Time between available events.

An exact ID is stronger evidence than a similar name or amount. We did not decide two records were the same renewal just because their student details looked alike.

## Which invoices count as paid renewals?

For paid-renewal rates, we used the exact values in the invoice file: `payment_status=Paid` and `is_renewal=Yes`. That gives 11 invoices. The other two renewal invoices are one `Partially_Paid` and one `Failed`; we discuss them separately. We did not assume that a blank `deleted_at` means active because that meaning is not documented.

## Main findings

- **Three paid renewal invoices have no exact form link:** INV-F, INV-J and INV-M. This means the stated invoice IDs cannot trace those invoices to forms. It does not prove that a child received no classes.
- **Form FORM-L has an unmatched invoice reference:** it says INV-N, which is not in the invoice file. It has similar student/class context to INV-M, but we did not silently connect them.
- **Invoice INV-H appears on two forms:** FORM-G and FORM-H. Both are Pending and have the same renewal details. This could be a duplicate submission, but an owner must confirm.
- **One amount comparison differs:** form FORM-I says [AMOUNT-B] paid, while invoice INV-I has net amount [AMOUNT-K] and status `Partially_Paid`. The invoice's gross `amount` is [AMOUNT-B]. We need a clear definition of `amount_paid`.
- **A form points to a failed payment:** form FORM-J references invoice INV-K, marked `Failed` with no `paid_at`. A form does not prove the payment settled.
- **Eight forms are Pending and have no booking request.** Four forms are Approved and have a request. Approved does not mean scheduled.
- **Three booking requests have no schedule rows:** REQ-B is pending batch allocation, REQ-C is marked batch full, and REQ-D awaits parent batch selection. Request REQ-A has two schedule rows on different dates; these are different class instances on the available fields.
- **Student, user, class and teacher IDs align** in the reference lookups and linked form/request pairs.
- **Batch BATCH-D is shown as full:** 6 active students for a maximum of 6. Request REQ-C names this batch and is marked `Failed_Batch_Full`. The reference file has no timestamp, so it cannot prove the batch was full when that request was processed.

## What the KPIs mean

The numerator is the number at the top of a fraction; the denominator is the total being compared. For example, 3/11 means three of eleven eligible paid-renewal invoice IDs lack an exact form link.

| KPI | Result | Simple meaning |
|---|---:|---|
| Orphaned Invoice Rate | 3/11 = 27.3% | Paid renewal invoices without an exact form reference. |
| Invoice-to-Form Match Rate | 8/11 = 72.7% | Distinct invoices with at least one exact matching form. |
| Duplicate Invoice Reference Rate | 2/12 = 16.7% | Form rows involved in a repeated invoice reference. |
| Payment Amount Mismatch Rate | 1/11 = 9.1% | Matched form rows whose amount differs from invoice net amount. |
| Form-to-Booking Conversion Rate | 4/12 = 33.3% | Forms with a booking request in this extract. |
| Pending Teacher Form Rate | 8/12 = 66.7% | Forms whose status is Pending; overdue is not established. |
| Approved but Unscheduled Request Rate | 3/4 = 75.0% | Requests linked to Approved forms with no schedule row. |
| Failed Batch Allocation Rate | 1/4 = 25.0% | Requests explicitly marked `Failed_Batch_Full`. |
| Payment-to-Schedule Time | 1.7453 hours (n=1) | One eligible invoice's payment-to-first-schedule time; too few examples for a typical estimate. |
| Overall Exception / Review Signal Rate | 10/11 = 90.9% | Proposed measure of paid renewals with any review signal; not a confirmed failure rate. |

Definitions, formulas, data sources and caveats are in `analysis/phase2_kpi_results.csv`.

## How we calculated elapsed time

For each event pair, we subtracted the first timestamp from the second and converted seconds into hours. A missing endpoint was counted as missing, not as zero. For example, Pending forms have no `approved_at`, so they do not count as 0-hour approvals.

The timestamps have no timezone offsets. The values use the supplied clock as-is, and we cannot confirm the timezone or the exact business meaning of each event. `class_date` is when the class should occur; schedule `created_at` is when the row was recorded. They answer different questions. The sample is small, so P90 is omitted.

## Why a person needs to review some records

- Invoice INV-M and form FORM-L look related by student details, but their invoice IDs differ. Verify the payment source before correcting the link.
- Forms FORM-G and FORM-H may be two submissions for one payment. Operations should decide the canonical record and keep an audit trail.
- Invoice INV-I is partially paid. Finance/Ops should say whether the form amount is package value or money received.
- Invoice INV-K is Failed. The form cannot authorize scheduling by itself.
- Request REQ-C is marked full, but its capacity snapshot may be stale. Confirm availability before proposing another batch.

These records are not allegations of fraud. They are data and process questions that the CSVs cannot answer alone.

## What remains uncertain

Confirm payment eligibility, partial-payment rules, amount tolerance, invoice/form uniqueness, status meanings, expected schedule rows for 24 sessions, timezone, SLA timing, capacity freshness, seat holds, and null `deleted_at` meaning.

Phase 3 should start after these rules are agreed. Automated checks should use exact IDs and payment evidence, and uncertain records should go to a human queue. This phase built no automation and approved no records.
