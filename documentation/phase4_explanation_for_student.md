# Phase 4: Understanding the Renewal Reconciliation Prototype

## What this prototype does

The program reads the five assessment CSV files, connects rows using exact IDs, checks for inconsistencies, and writes a decision and audit trail. It is **read-only**: it does not change the input files, create booking/schedule records, contact a payment gateway, send a message, or approve a real student.

The policy has automatic approval turned off. Because the business has not confirmed payment, amount, lifecycle, parent-choice, or capacity rules, the actual sample is routed to review or blocked from downstream processing. An `AUTO_APPROVED` result is tested only with an explicitly synthetic case and an enabled test policy, and only when exactly one invoice-linked form is explicitly `Approved`.

## What each Python file does

- **`src/validators.py`** lists the required columns for each CSV, loads the five files with Pandas, and gives a clear error if a file or required column is missing. It also normalizes IDs such as `BATCH-A` and `BATCH-A.0` into the same text form without fuzzy matching, and compares numeric amounts safely.
- **`src/reconciliation.py`** is the runner. It reads the policy, builds cases from exact ID links, calls the decision engine, and writes the results, exception report, audit log, and summary. It hashes the input files before and after the run to check they were not changed.
- **`src/decision_engine.py`** applies deterministic rules. It checks payment status, amount fields, duplicate forms, identity IDs, reference students/batches, workflow states, and linked schedule rows. It returns one of the three outcomes and includes evidence, a reason code, an owner, and a next action.
- **`config/policy.json`** separates provisional business rules from code. `auto_approval_enabled` is `false`. The actual CSVs also lack configured evidence fields for verified gateway payment, explicit parent choice, active-student confirmation, and current capacity/seat hold. Business owners must approve the rules and provide authoritative evidence before considering automation.
- **`tests/test_reconciliation.py`** checks the known dataset examples and uses a synthetic test fixture for a complete auto-approval path and for an Approved form without a request (that second scenario is not present in the actual Phase 2 sample).

## How Pandas reads and joins the data

Pandas loads each CSV into a **DataFrame**, a table of rows and columns. The runner creates dictionaries indexed by the join columns, which is equivalent to exact-key joins:

```text
invoices.id
  = faculty_form_unapproved.invoice_id
faculty_form_unapproved.id
  = booking_requests.faculty_form_id
booking_requests.id
  = class_schedule_bookings.bookingrequest_id
reference_active_batches_and_students.student_id
  = operational student_id
```

The reference student and batch values provide supporting checks. Student ID is not used to repair a conflicting invoice ID. The reference capacity extract is treated as non-authoritative because it has no snapshot time.

## How one run works

1. Check for all five source files and the required columns.
2. Build a case for each invoice marked as a renewal; create a separate case for a form whose invoice ID is absent from the invoice extract. Orphan requests and schedules are also included if found.
3. Join the next stage only with exact IDs.
4. Add findings for evidence such as a failed or partial payment, amount conflict, duplicate form reference, missing request/schedule, parent selection, batch capacity uncertainty, or ID mismatch.
5. Choose an outcome. A confirmed hard gate such as a failed payment blocks downstream progress. Ambiguity goes to human review. Automatic approval is possible only when the policy enables it, exactly one form is linked, its status is `Approved`, and all configured evidence gates pass. `Pending`, blank, missing, rejected or unknown form statuses cannot pass this gate.
6. Write one result and audit row per case plus one exception row per finding. Stable IDs are based on the case/reason/source IDs. Output files are overwritten on each run, not appended.

## What the outcomes mean

- **`AUTO_APPROVED`**: all configured gates pass, including the required Operations approval status on exactly one linked teacher form. This means only that the renewal eligibility decision passed. It does not create a booking request, allocate a batch, or create a schedule.
- **`NEEDS_HUMAN_REVIEW`**: evidence is incomplete, ambiguous, or requires an owner/parent decision. The actual dataset mostly lands here because auto approval is disabled and some workflow/payment states need review.
- **`BLOCKED`**: continuing now would be unsafe based on the source evidence. For example, the data marks invoice INV-K as `Failed`, and form FORM-L references invoice INV-N, which is absent from the invoice extract. A person can still investigate and correct the underlying source evidence.

### Decision versus booking request versus schedule

Think of these as three different steps. A **decision** records whether the renewal passed eligibility checks. A **booking request** is a separate operational record asking for classes or batch allocation. A **schedule row** represents a specific class occurrence with a date and time. `AUTO_APPROVED` in this prototype records only the first step; it never creates the other two. The required Operations approval of a teacher form must happen before a booking request may proceed under the assessment workflow.

A teacher form marked `Pending` needs an Operations decision. The program does not change it to `Approved`, create a booking request, or guess a business transition. `Rejected`, blank, missing, or unfamiliar statuses also go to review because they are not evidence of approval. The actual sample contains Pending forms, so even a test policy with other evidence gates enabled cannot automatically approve those cases.

The synthetic test checks the auto-approval evidence gate directly: an `Approved` form can satisfy that gate when all the other evidence is supplied. The full workflow evaluator separately flags an Approved form with no booking request for review. This preserves the existing check for the next stage; passing an eligibility gate does not itself create or imply a booking request.

“Blocked” does not mean a permanent rejection, and a status in this extract is not live gateway verification.

## What the output files contain

- **`outputs/reconciliation_results.csv`**: one row for each evaluated case, including invoice/form/request/schedule IDs, outcome, primary reason, explanation, owner, next action, policy version, and timestamp.
- **`outputs/exception_report.csv`**: every issue or informational finding with reason code, evidence, severity, owner, recommended action, and optional draft message. Draft messages are not sent.
- **`outputs/audit_log.csv`**: one entry per evaluated case with invoice/form/request/schedule IDs; structured values used in payment, approval, parent-choice, student and batch checks; the policy version; UTC timestamp; outcome and reason; SHA-256 for each input CSV; and a combined hash for the five-file snapshot. It avoids names, contact details and free-text notes. It is stronger prototype traceability, not production-grade audit storage.
- **`outputs/reconciliation_summary.md`**: total cases and outcomes, exception counts, and limitations.

## Results from the actual assessment CSVs

The run processed **14 cases**: 13 renewal invoice rows and one separate form case for the unmatched `invoice_id=INV-N`.

| Outcome | Cases |
|---|---:|
| `AUTO_APPROVED` | 0 |
| `NEEDS_HUMAN_REVIEW` | 12 |
| `BLOCKED` | 2 |

The latest run's findings include:

- Paid renewal invoices `INV-F`, `INV-J`, and `INV-M` with no exact form reference.
- Form `FORM-L` referencing absent invoice `INV-N`; it is not silently matched to invoice `INV-M` by student details.
- Duplicate invoice reference `INV-H` on forms `FORM-G` and `FORM-H`.
- Partially paid invoice `INV-I` and its form amount conflict ([AMOUNT-B] reported vs [AMOUNT-K] net amount).
- Failed invoice `INV-K` linked to form `FORM-J`.
- Three booking requests with no schedule rows; these remain distinct states (pending allocation, failed batch, and parent selection pending).
- Request `REQ-A` has two schedule rows on different dates and unique schedule IDs. They are reported as multiple valid schedule instances, not duplicates. The 24-session schedule-completeness rule remains unknown.

Batch `BATCH-D` has a reference count of 6/6 and request `REQ-C` says `Failed_Batch_Full`; because the snapshot is undated, the prototype reports capacity as unconfirmed rather than treating it as live proof.

## Provisional rules that need business confirmation

The default policy keeps automatic approval disabled. Before considering it, business owners must confirm payment source of truth and settlement rules, amount field semantics/tolerance, partial-payment eligibility, what an Operations approval means for each form status, duplicate-form handling, student-active evidence, parent batch-choice evidence, live capacity/seat holds, expected schedule generation, and timezone/SLA rules. The prototype's rule that only `Approved` passes the form gate preserves the existing four-step workflow; it does not define a new status transition.

## How to run it

Install dependencies once:

```powershell
python -m pip install -r requirements.txt
```

From the repository root, run the prototype:

```powershell
python src/reconciliation.py
```

Run the automated tests:

```powershell
python -m pytest tests -q -p no:cacheprovider -p no:tmpdir
```

The pytest flags avoid user-profile temp/cache locations that are unavailable in some restricted Windows environments. The normal `python -m pytest -q` command is also suitable in a standard local environment.

## Test coverage

The updated suite reports **21 passed test cases**. Coverage includes exact matching, absent forms, nonexistent invoice references, duplicate invoice references, partial and failed payments, amount mismatch, Approved forms without booking requests, stale full-batch evidence, pending parent selection, missing schedules, multiple valid schedule rows, and input-file errors. It also verifies that Pending forms and missing, blank, rejected, or unknown approval statuses cannot auto-approve; an Approved form can pass the synthetic eligibility gates when all other evidence is satisfied; and the full workflow still requires a separate booking request. Additional checks confirm that the default policy keeps automatic approval disabled, audit evidence and input snapshot hashes are present, and repeated runs preserve stable IDs and replace outputs rather than append.

## Interview questions and sample answers

**Why not match form FORM-L to invoice INV-M?**  
The invoice IDs conflict. Matching only by student could attach the wrong payment, so the engine blocks that form from progressing and routes it for source verification.

**Why is the auto-approved count zero?**  
The policy is disabled pending business sign-off. The provided CSVs also lack verified gateway evidence, explicit parent-choice confirmation, an explicit active-student field, and current seat-hold evidence.

**Does a missing schedule row mean a failed renewal?**  
No. The request may be awaiting batch allocation or a parent choice, and the extract may be incomplete. The engine records a review finding and checks the request status.

**Are multiple rows for request REQ-A duplicates?**  
No. They use different class dates and different schedule IDs. We retain both and do not infer whether all 24 purchased sessions are represented.

**Why use AI at all?**  
AI is optional for summarizing evidence or drafting a message. Exact ID matching, amount checks, payment validation and approval decisions use deterministic rules and human judgment.

## Known limitations and business decisions

The data is a small snapshot. `payment_status` is read from the CSV and not verified with a live gateway. The amount comparison against `net_amount` is provisional. Partial-payment eligibility, duplicate-form policy, status transitions, `deleted_at` semantics, parent consent, capacity freshness/seat holds, expected schedule count, timezone and SLA rules need business confirmation. No live action or production approval is performed.
