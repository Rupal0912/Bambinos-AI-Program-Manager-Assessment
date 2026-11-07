# Phase 6: Operations Dashboard Explanation

## Purpose

The dashboard gives the Head of Operations a read-only view of renewal stages, operational exceptions, owners, and proposed service targets. It reads the supplied CSV snapshot and existing reconciliation outputs. It does not approve records, modify CSVs, create booking or schedule rows, verify payment with a provider, or send messages.

## Dashboard sections

### Executive KPI overview

The dashboard displays eight requested measures. Each card identifies an observed source count or an exact-ID-derived count. Hours saved remains **Not yet measurable**.

| KPI | Definition and calculation | Current snapshot |
|---|---|---:|
| Paid renewal invoices | Distinct invoice IDs with `payment_status=Paid` and `is_renewal=Yes` | 11 |
| Paid renewals without exact form | Distinct paid renewal invoice IDs not present in `faculty_form_unapproved.invoice_id` | 3 |
| Pending teacher forms | Form rows whose `approval_status` is exactly `Pending` | 8 |
| Approved forms without booking requests | Approved form IDs absent from `booking_requests.faculty_form_id` | 0 |
| Awaiting batch allocation | Request rows with `request_status=Pending_Batch_Allocation` | 1 |
| Failed batch allocation | Request rows with `request_status=Failed_Batch_Full` | 1 |
| Requests without schedule records | Distinct request IDs absent from `class_schedule_bookings.bookingrequest_id` | 3 |
| Hours saved through automation | Not calculable from these files; no measured automation time or manual baseline | Not yet measurable |

The paid-renewal cohort uses literal source values. It is an assessment snapshot, not a production eligibility rule or company-wide performance rate. Matching uses exact normalized identifiers only.

The dashboard displays the proposed calculation:

`Hours saved = ((manual handling minutes - automated handling minutes) × eligible cases) / 60`

This requires measured manual handling minutes, automated processing minutes, and a defined eligible-case count. Those inputs are not present.

### Renewal workflow funnel

The chart shows raw table row counts for the four stages: **13 invoices → 12 teacher forms → 4 booking requests → 2 schedule rows**. Its accompanying table adds relationship context, including that 8 of 11 paid renewal invoice IDs have an exact form link and that the 2 schedule rows belong to 1 request.

These are not same-unit conversion counts. A schedule row is a class occurrence, and a request can have multiple schedule rows. A smaller count later in the pipeline does not by itself mean a renewal failed.

### Exception monitoring

The exception table groups existing reconciliation findings by their exact `reason_code`. It shows the finding count, severity, responsible owner, and recommended action. Different reason codes are not combined. Counts refer to findings, not failed renewal cases.

### Actionable work queue

The queue starts with rows from `outputs/exception_report.csv` and enriches them using exact IDs from the source CSVs. It shows invoice, form, request and student IDs; current stage; current source statuses; exception reason; owner; and next action. Search and filters cover reason code, severity, and owner. Student IDs are included as operational lookup identifiers; names, mobile numbers, emails, and free-text remarks are not loaded or displayed.

The current stage is the furthest linked record found in the snapshot. Its status text can show statuses from multiple linked records. This is a triage aid, not proof that an earlier stage failed.

### SLA and aging

The dashboard shows the proposed Phase 3 SLA targets for ingestion, missing forms, payment exceptions, duplicate forms, approvals, booking, parent selection, and exception resolution. Every target is labeled proposed and pending business validation. No SLA attainment or overdue status is calculated.

Although some source rows contain event timestamps, the files do not provide a reliable extract/as-of timestamp or an agreed timezone and business calendar. Safe aging also needs defined start/stop events and pause rules. Those fields and definitions must be added before an item can be marked overdue or “stuck.”

### Operational insights

The section reports decision counts from `outputs/reconciliation_results.csv`, finding counts from the exception output, and the most frequent recorded reason code. It also calls out exact form-link gaps and Pending forms without implying an SLA breach.

## Data sources and freshness check

The dashboard reads selected columns from:

- `data/1_invoices.csv`
- `data/2_faculty_form_unapproved.csv`
- `data/3_booking_requests.csv`
- `data/4_class_schedule_bookings.csv`
- `data/reference_active_batches_and_students.csv`
- `outputs/reconciliation_results.csv`
- `outputs/exception_report.csv`
- `outputs/audit_log.csv` for the recorded input-file hashes

Names, contact fields, and remarks are excluded from the dashboard loader. The app compares the current five-file SHA-256 map with the hash map in the audit output. If they differ or the audit is unavailable, it warns that reconciliation outcomes and exception rows may be stale. Raw source counts remain visible; output-derived items should not be actioned until reconciliation is refreshed.

## Snapshot limitations and assumptions

- The sample is small and does not represent live company-wide operations.
- `payment_status` is read from the CSV and is not verified with a payment gateway.
- `amount_paid` and invoice `net_amount` semantics, partial-payment rules, deletion behavior, and workflow statuses need business confirmation.
- Reference batch capacity has no timestamp and is not live availability evidence.
- Missing schedule rows do not prove failure; expected schedule count per renewal is undefined.
- The dashboard has no database, API, booking, payment, messaging, or notification integration.
- It is an assessment prototype, not production-ready software.

## How to run

From the project root, install requirements and launch Streamlit:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run dashboard/app.py
```

Streamlit prints a local URL, usually `http://localhost:8501`. The dashboard reads project-local CSVs and only displays data; it has no write controls.

The dashboard metric tests can be run with:

```powershell
python -m pytest tests/test_dashboard_metrics.py -q -p no:cacheprovider -p no:tmpdir
```

