# Aggregate assessment findings

**Scope:** supplied assessment extract only. These figures are not company-wide performance, confirmed financial leakage, or proof of a missed service.

## Extract size

| Source | Rows |
|---|---:|
| Invoices | 13 |
| Teacher forms | 12 |
| Booking requests | 4 |
| Class schedule rows | 2 |
| Student/batch reference rows | 13 |

## Observed metrics

| Measure | Result | Interpretation and limitation |
|---|---:|---|
| Paid renewal invoices with exact-linked form | 8/11 = 72.7% | Uses exact invoice ID; a record-linkage measure. |
| Paid renewal invoices without exact-linked form | 3/11 = 27.3% | Extract-level signal, not confirmed loss or company-wide leakage. |
| Forms affected by repeated invoice reference | 2/12 = 16.7% | Repeated reference requires disposition; rows are not assumed duplicates. |
| Form/invoice amount mismatch | 1/11 = 9.1% | Amount-field semantics and partial-payment policy need Finance confirmation. |
| Pending teacher forms | 8/12 = 66.7% | Status count; no reliable SLA age conclusion. |
| Approved-form requests without a schedule row | 3/4 = 75.0% | Missing schedule rows have distinct request states and are not automatically failures. |
| Request explicitly marked batch-full | 1/4 = 25.0% | Reference capacity is undated and non-authoritative. |
| Proposed union of exception/review signals | 10/11 = 90.9% | Distinct paid renewal invoice IDs with any defined signal; not a failure rate. |

Limited timestamp pairs produced medians of 0.4511 hours from payment to form creation (n=10), 1.5417 hours from form creation to approval (n=4), and 1.7453 hours from payment to first schedule creation (n=1). These small samples do not establish SLA performance.

## Prototype snapshot

The documented real-data run evaluated 14 cases: 0 `AUTO_APPROVED`, 12 `NEEDS_HUMAN_REVIEW`, 2 `BLOCKED`, 24 exception findings, and 0 scheduling-ready occurrences. Automatic approval is disabled by default. The empty scheduling-ready output is expected because authoritative gateway evidence, explicit parent-choice evidence, an active-student field, authoritative capacity, seat holds, and approved schedule-state/parameter contracts are unavailable.

Hours saved are **not yet measurable**. The proposed calculation is `((manual handling minutes - automated handling minutes) × eligible cases) / 60`; manual baseline and actual automation handling-time data are not supplied.

## Data limitations

- The extract is small and has no confirmed representative sampling frame.
- Timestamp timezone and event semantics are not fully established; no overdue cases are inferred.
- Capacity reference data has no snapshot timestamp or reservation/seat-hold semantics.
- A schedule row represents a class occurrence; the expected total number of occurrences is not provided.
- Payment status and amount fields do not replace authoritative gateway settlement evidence.

Assessment metrics above are distinct from the synthetic demonstration outputs in `synthetic_demo/`.
