# Phase 9: Three-Stage Decision Architecture

## Purpose

The original evaluator mixed three questions into one outcome: whether a renewal is eligible, whether a booking request is ready, and whether class scheduling can safely proceed. This caused two problems: an approved form without a request could lower renewal eligibility, while any existing request or schedule could fail the eligibility gate. The revised design evaluates these stages separately.

This remains an assessment prototype. The default policy leaves automatic approval disabled. The program only reads input files and writes local analysis outputs. It does not write payment, booking, schedule, or messaging systems.

## Stage model

| Stage | Status values | What the status means |
|---|---|---|
| Renewal eligibility | `AUTO_APPROVED`, `NEEDS_HUMAN_REVIEW`, `BLOCKED` | `AUTO_APPROVED` means the renewal passed the configured payment, exact-link, amount, identity, active-student and form-approval gates. It is not a booking or scheduling action. |
| Booking-request readiness | `READY_TO_CREATE_REQUEST`, `REQUEST_EXISTS_VALID`, `NEEDS_HUMAN_REVIEW`, `BLOCKED`, `NOT_READY` | Determines whether a request could be created under an authorized procedure, or whether one valid request already exists. The prototype does not create it. |
| Scheduling readiness | `READY_FOR_CLASS_SCHEDULE_BOOKINGS`, `ALREADY_FULFILLED`, `WAITING_ON_PARENT`, `WAITING_ON_CAPACITY`, `WAITING_ON_REQUEST`, `NEEDS_HUMAN_REVIEW`, `BLOCKED`, `NOT_READY` | A schedule-stage handoff is ready only when all listed evidence is present, authoritative and conflict-free. It is not a live schedule write. |

### Renewal eligibility rules

The evaluator requires the policy to explicitly enable auto-approval and all of the following:

- An invoice marked as a renewal with an approved paid status.
- Exactly one form linked by exact `invoice.id = form.invoice_id` and an exact `Approved` status.
- No material eligibility findings, including payment failure/partial/unsupported status, missing or mismatched identity fields, duplicate forms, amount conflicts or missing/unrecognized form approval.
- An authoritative gateway verification field.
- An approved payment amount rule, a provider-backed settled amount and currency, form amount within the configured tolerance, and currency agreement.
- Exactly one active-student reference row with explicit `student_active` evidence.

The default policy has `auto_approval_enabled: false` and marks the amount rule provisional. A missing request is no longer an eligibility failure. Existing valid requests and schedules do not automatically fail eligibility. Their own findings are still retained and handled at their stage.

### Booking-request readiness rules

- If eligibility is blocked, booking readiness is blocked. If eligibility is not auto-approved, it is `NOT_READY`.
- If eligibility is auto-approved but no exact-linked request exists, readiness is `READY_TO_CREATE_REQUEST`; this is a no-write result only. For an approved form the exception report retains `APPROVED_FORM_NO_REQUEST` as a booking-stage finding.
- Exactly one request with exact form and invoice IDs, consistent student/account/class/educator IDs, and a present request status is `REQUEST_EXISTS_VALID`.
- Duplicate request rows or incorrect/mismatched links require human review.

`APPROVED_FORM_NO_REQUEST` therefore describes a missing next-stage artifact. It does not by itself claim that payment failed or that the renewal is ineligible. A case without the request cannot enter the scheduling-ready output.

### Scheduling-readiness rules

A record appears in `scheduling_ready.csv` only when:

1. Renewal eligibility is `AUTO_APPROVED`.
2. Exactly one valid exact-linked booking request exists.
3. `request_status` is included in the policy's explicitly approved `schedule_ready_request_statuses` list.
4. Parent choice is explicitly confirmed with a recorded evidence ID where required.
5. A current authoritative capacity check is recorded and the selected batch is available.
6. A valid seat-hold identifier exists.
7. Provider-backed payment amount and currency are verified under an approved Finance rule.
8. A separate `payment_evidence_id` is present and does not equal the invoice ID, and `payment_evidence_source` is included in the policy's explicitly configured trusted-source allowlist. An invoice ID, paid status or amount comparison by itself is not gateway evidence. A blank default allowlist fails closed.
9. Student and linked identity evidence are valid.
10. Schedule parameters include all required identifiers, date, start/end times and a valid IANA timezone. The end time must be strictly later than the start time. Invalid/missing timezone, invalid date/time, missing fields, and invalid duration fail closed.
11. Local start and end times are checked against the timezone's daylight-saving transitions. Ambiguous times (two possible instants) and nonexistent times (no possible instant) fail closed; no fold or offset is guessed.
12. Existing schedule rows have no conflicting or duplicate class occurrence; only schedule occurrences not already fulfilled are emitted.
13. The output has an idempotent stable ID and audit provenance.

The source files do not establish the required live evidence or approved schedule-ready request state. `schedule_ready_request_statuses` is deliberately empty in the real policy until the business defines valid request states. This prevents a source status from being guessed into an approval rule.

## Evidence status values

The stage report uses these explicit values for each evidence gate:

- `VERIFIED`: present and passed under a configured approved rule.
- `MISSING`: required value or evidence reference is absent.
- `UNVERIFIED`: a value exists but its source/rule is not authoritative or approved.
- `CONFLICT`: present evidence is false, contradictory or inconsistent.
- `NOT_APPLICABLE`: a gate does not apply to that case.

Missing values never imply a positive result. Current-data examples include unavailable gateway verification, no explicit parent-choice evidence, no `student_active` field, an undated/non-authoritative capacity reference, no seat-hold ID, provisional amount semantics, and no complete timezone/calendar-validated schedule parameters.

The payment evidence reference is recorded separately from the invoice record. Policy fields `payment.evidence_id_field`, `payment.evidence_source_field` and `payment.allowed_evidence_sources` identify how a trusted gateway reference is supplied. The default allowed-source list is empty because the business has not approved a source contract. Tests use a clearly labelled synthetic-only source string and an in-memory test policy. They do not modify default policy or real input data.

### Phase 9E reason codes

- Payment evidence: `PAYMENT_EVIDENCE_REFERENCE_MISSING`, `PAYMENT_EVIDENCE_REFERENCE_CONFLICT`, `PAYMENT_EVIDENCE_SOURCE_MISSING`, `PAYMENT_EVIDENCE_SOURCE_UNTRUSTED`.
- Schedule evidence and parameters: `SCHEDULE_PARAMETERS_MISSING`, `SCHEDULE_FIELD_MISSING`, `SCHEDULE_DATE_INVALID`, `SCHEDULE_TIME_INVALID`, `SCHEDULE_TIMEZONE_MISSING`, `SCHEDULE_TIMEZONE_INVALID`, `SCHEDULE_END_NOT_AFTER_START`, `SCHEDULE_LOCAL_TIME_AMBIGUOUS`, `SCHEDULE_LOCAL_TIME_NONEXISTENT`, `SCHEDULE_PARAMETERS_UNVERIFIED`, `SCHEDULE_PARAMETERS_EVIDENCE_MISSING`.

Each code is added to the stage exclusion list and exception report. A failure in these gates cannot enter `scheduling_ready.csv`.

## Outputs

### `outputs/reconciliation_results.csv`

The existing columns and meanings remain unchanged. In particular, `decision_outcome` is the **renewal eligibility** status. It is not the scheduling-readiness state.

### `outputs/stage_readiness_report.csv`

One row per evaluated case, with:

`case_id`, `decision_id`, `invoice_id`, `teacher_form_id`, `booking_request_id`, `renewal_eligibility_status`, `booking_request_readiness_status`, `scheduling_readiness_status`, `exclusion_reason_codes`, `evidence_status_json`, `policy_version`, `evaluated_at_utc`, and `input_snapshot_sha256`.

It includes cases that are not ready and names the missing or conflicting evidence. New stage-specific exclusion labels describe evidence gaps; they do not change existing exception-code meanings.

### `outputs/scheduling_ready.csv`

This file includes only `READY_FOR_CLASS_SCHEDULE_BOOKINGS` schedule occurrences. It includes stable readiness/case/decision IDs, exact invoice/form/request IDs, student/class/educator/batch IDs, occurrence parameters, payment/parent/capacity/seat-hold evidence references, policy version, evaluation time, and input snapshot hash. Contact details are not included.

When there are no qualifying cases, the file is written with its column headers and zero data rows. That is an acceptable and expected result when evidence is unavailable. It is safer than creating a synthetic success from real records.

### Existing exception and audit outputs

`exception_report.csv` retains the existing columns, reason codes, severities, and draft-only message behavior. Stage findings such as `APPROVED_FORM_NO_REQUEST` appear in this file without changing the renewal `decision_outcome`. `audit_log.csv` retains its existing columns and five-file input hash provenance. New readiness artifacts carry the same combined snapshot hash.

All outputs are replaced rather than appended on each run. Decision and exception IDs remain stable from the same case/source identifiers. Synthetic fixtures are used only by tests and are never included in real output generation.

## Test design

The suite includes a synthetic end-to-end success path assembled in memory with all trusted gates and an explicitly configured test-only schedule-ready request state. It exercises case building, renewal eligibility, booking readiness, schedule readiness and the readiness DataFrame. The fixture is not saved as assessment input or real output data.

Other synthetic cases verify:

- Approved form without request: eligibility can pass; request is separately marked ready-to-create; scheduling waits for the request.
- Missing gateway verification: eligibility does not auto-approve and the report names the missing evidence.
- Missing parent choice, capacity evidence or seat hold: no scheduling-ready row is emitted.
- One valid existing request: accepted rather than blanket-rejected.
- Existing schedule fulfillment: recognized and not emitted again.
- Duplicate requests and invoice/form mismatch: excluded from scheduling readiness.
- Failed and partial payments, unknown approval statuses, and default disabled policy remain safe.
- Repeated runs preserve stable IDs and replace outputs; output columns and original CSV hashes remain compatible/unchanged.
- Missing active-student evidence, non-authoritative capacity, missing seat hold and each missing/untrusted/conflicting payment evidence reference, asserting all three stage statuses.
- Invalid/missing timezone, equal/earlier end time, invalid date, missing required fields, missing schedule parameters, and ambiguous/nonexistent New York daylight-saving local times, asserting all three stage statuses.
- Duplicate and conflicting schedule rows are excluded; two distinct legitimate occurrences are preserved, and a previously fulfilled occurrence is not emitted a second time.
- A fully evidenced positive synthetic path reaches `READY_FOR_CLASS_SCHEDULE_BOOKINGS` and emits a row only under an in-memory test policy and test-only evidence source.

## Current dataset and limitations

The supplied real CSVs do not provide gateway verification or a separate trusted payment evidence ID/source, explicit parent-choice evidence, an active-student flag, authoritative current capacity, a seat hold, or schedule-ready request-state approval. They also lack scheduling parameters with a verified IANA timezone contract and an approved authoritative settlement rule. Therefore no real record should be declared scheduling-ready under the default policy. The output may be empty without indicating that the workflow has failed.

The prototype validates the payment evidence reference field, its separation from the invoice ID, and its source against a configured allowlist. It cannot resolve that reference against a gateway evidence store or confirm that the record belongs to the payment. A production integration must perform those checks before treating the reference as verified. The current duration rule assumes same-day classes; overnight sessions are rejected and need explicit business treatment if they are valid.

No live service integrations exist. Payment source-of-truth, partial-payment eligibility, amount/currency tolerance, status meanings, parent-consent evidence, capacity freshness and reservation rules, schedule coverage and timezone, and allowed request states still require business-owner confirmation.

## How to run

From the project root:

```powershell
python src/reconciliation.py
```

This replaces local output files, records input hashes in the audit log, and does not modify the five input CSVs or perform external writes. Tests can be run with:

```powershell
python -m pytest tests -q -p no:cacheprovider -p no:tmpdir
```

For Phase 9E, the complete suite (including the repeated-run output-writing test and dashboard tests) was run in an isolated temporary project copy using the command above: **57 passed, 0 failed, 0 skipped**. Python compilation was checked in memory for the three source files and reconciliation test module. Reconciliation ran twice in the copy; decision, exception, readiness, and audit identifiers were identical between runs. Original project source and output hashes were unchanged. Do not run the repeated-run test against the working project outputs when preserving those outputs is required.

The positive scheduling-ready case uses only in-memory synthetic records and an isolated test policy. It demonstrates the stage flow, not real eligibility, business approval, or a production integration. The default auto-approval setting and all external-write controls remain disabled.

