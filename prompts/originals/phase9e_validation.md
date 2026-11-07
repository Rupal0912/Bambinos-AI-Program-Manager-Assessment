# Phase 9E — Close Readiness Gaps and Validate Safely

Act as a senior Python engineer, QA architect, and operations automation reviewer.

Project:
`<PROJECT_ROOT>`

Phase 9D identified specific readiness and test-coverage gaps. Resolve them without weakening any safety gates or inventing evidence.

## Non-negotiable safeguards

- Never modify the five original source CSVs.
- Keep `auto_approval_enabled` false in the default policy.
- Keep all payment, booking, schedule, and messaging writes disabled.
- Do not fabricate real payment evidence, parent choices, active-student status, capacity, or seat holds.
- Synthetic records must remain isolated in tests.
- Do not change real-data outputs to make results look better.
- Preserve exact-ID matching and existing output compatibility wherever possible.

## 1. Payment evidence reference

Inspect how `payment_evidence_id` is currently populated and validated.

Implement a strict scheduling-readiness requirement:
- The payment evidence reference must be present and non-empty.
- It must point to an explicitly identified evidence record or trusted verification reference.
- An invoice ID alone must not be treated as gateway verification.
- A payment status or amount comparison alone must not satisfy the evidence-reference requirement.
- Missing, unverified, or conflicting evidence must prevent scheduling readiness and produce a precise reason code.
- Preserve the distinction between payment evidence and the invoice record.

Do not make real cases pass using invented references.

## 2. Schedule parameter validation

Review all required scheduling parameters.

Add validation for:
- Valid timezone identifier.
- Valid date and time values.
- End time strictly after start time.
- Invalid or missing timezone.
- Ambiguous or nonexistent local times where daylight-saving transitions apply.
- Missing class, educator, batch, date, time, or other required schedule inputs.

Fail closed: ambiguous or invalid scheduling information must not enter `scheduling_ready.csv`.

Use a clear, documented reason code for each material validation failure.

## 3. Add dedicated synthetic end-to-end tests

Add explicit tests for:
- Missing active-student evidence.
- Non-authoritative capacity.
- Missing seat hold.
- Missing payment evidence ID.
- Invalid or missing timezone.
- End time equal to or earlier than start time.
- Ambiguous/nonexistent local time where applicable.
- Duplicate schedule records.
- Conflicting schedule records.
- Distinct legitimate schedule occurrences.
- Missing required schedule parameters.

Each test must assert all three stage outcomes:
1. Renewal eligibility.
2. Booking-request readiness.
3. Scheduling readiness.

Also assert that no ineligible or incomplete case enters the scheduling-ready output.

Keep a positive fully evidenced synthetic end-to-end case. It must prove that the three-stage architecture can produce a scheduling-ready result under an isolated test-only policy, without changing the default production policy.

## 4. Safe full-suite validation

The existing repeated-run test writes to `outputs/`.

Do not run it against the working project directory.

Instead:
- Create an isolated temporary copy of the project for validation.
- Exclude `.git`, `venv`, `.venv`, caches, and unnecessary large files.
- Run the complete test suite in that copy, including the repeated-run test and dashboard tests.
- Run Python compilation checks.
- Run reconciliation twice in the isolated copy.
- Compare stable decision, exception, readiness, and audit identifiers between runs.
- Verify the original project's source CSV hashes and output file hashes before and after validation.

Do not claim full-suite validation if any test is skipped or excluded.

## 5. Documentation

Update:
- `README.md`
- `documentation/phase9_three_stage_architecture.md`
- `documentation/phase9` student explanation if one exists

Document:
- What counts as payment evidence.
- Why invoice ID is not gateway verification.
- Scheduling timezone and time validation.
- New reason codes.
- Remaining limitations and policy decisions.
- Which synthetic tests demonstrate the positive path.
- Exact full-suite test command and result.

Do not claim production readiness.

## 6. Final report

Return:
1. Files changed.
2. Exact behavior changes.
3. New reason codes.
4. A scenario table showing expected and actual results at all three stages.
5. Positive synthetic end-to-end result.
6. Full test command and exact passed/failed/skipped counts.
7. Proof that validation ran in an isolated copy.
8. Before/after hashes for all five source CSVs and original project outputs.
9. Confirmation that default auto-approval remains disabled and no live writes or messages occurred.
10. Remaining limitations.

Do not silently waive a failed test or unresolved gate. If a requirement cannot be implemented safely with the available data, report it explicitly.