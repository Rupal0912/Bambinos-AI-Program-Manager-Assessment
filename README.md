# Bambinos.live Renewal Operations Assessment

This repository contains an evidence-based operations assessment and a read-only Python prototype for reconciling student renewal records from payment through class scheduling. It is a hiring-assessment prototype, not a production integration.

## Business problem

The assessment describes a four-step handoff: invoice/payment, teacher renewal form, Operations booking request, and parent/Operations batch selection and scheduling. Manual checks, missing or mismatched identifiers, duplicate submissions, unclear payment evidence, and unresolved batch selection can leave cases waiting between stages. The supplied sample is small and does not establish company-wide loss, service failure, or SLA performance.

## Three-stage decision architecture

1. **Renewal eligibility** evaluates the exact-linked invoice and form, payment and amount evidence, identity, and form approval.
2. **Booking-request readiness** determines whether an authorized request could be created or whether one valid exact-linked request already exists.
3. **Scheduling readiness** requires a valid request plus explicit parent choice, authoritative capacity and seat-hold evidence, verified payment evidence, and valid schedule parameters.

These outcomes are separate. `APPROVED_FORM_NO_REQUEST` is a booking-stage finding; it does not itself make payment or renewal ineligible. The default policy keeps automatic approval disabled. No payment, booking, schedule, or message action is performed.

## Prototype and dashboard

- `src/` contains exact-ID reconciliation, deterministic decision rules, and input validation.
- `dashboard/` contains the read-only Streamlit Operations dashboard.
- `config/policy.json` contains provisional, disabled-by-default policy settings.
- `tests/` contains reconciliation and dashboard tests using the synthetic demonstration fixture.
- `examples/synthetic_data/` contains clearly labeled, invented records with no parent/student contacts or assessment record IDs.
- `results/synthetic_demo/` contains generated outputs from that synthetic fixture. `results/assessment_findings.md` separately reports aggregate findings from the assessment extract.

The original assessment CSVs and local reconciliation outputs are excluded from version control. Their absence from a public clone does not change their status as the source for the reported assessment aggregates.

## Quick start

Use Python 3.10 or newer. From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Run the prototype on the synthetic example. This writes only under `results/synthetic_demo/`:

```powershell
python src/reconciliation.py --input-dir examples/synthetic_data --output-dir results/synthetic_demo --policy config/policy.json
```

Run the dashboard:

```powershell
python -m streamlit run dashboard/app.py
```

When original local inputs are present, the dashboard reads `data/` and `outputs/`. In a public clone without those excluded files, it uses the labeled synthetic data and its demo outputs.

Run tests:

```powershell
python -m pytest -q
```

See [`workflows_or_scripts/README.md`](workflows_or_scripts/README.md) for entry points and output descriptions.

## Assessment findings and limitations

The supplied extract contains 13 invoice rows, 12 teacher forms, 4 booking requests, 2 schedule rows, and 13 reference rows. Among 11 paid renewal invoices, 8 have an exact-linked form (8/11 = 72.7%) and 3 do not (3/11 = 27.3%). These are extract-level linkage measures, not company-wide leakage estimates. Other measured counts and denominators are in [`results/assessment_findings.md`](results/assessment_findings.md).

The prototype summary records 14 evaluated cases, 0 `AUTO_APPROVED`, 12 requiring human review, 2 blocked, and 0 real scheduling-ready rows. The empty scheduling-ready output is expected because the supplied extract lacks required authoritative evidence. The dashboard reports hours saved as **Not yet measurable**; a manual handling-time baseline and automated handling-time measurement are unavailable.

Business rules for payment source of truth, partial payment, amount semantics, student-active status, parent choice, capacity freshness, seat holds, schedule coverage, and SLA calendars still require owner approval. Missing schedule rows are not automatically failures; multiple distinct schedule rows are not assumed duplicates.

## Assessment deliverables

- **A — Problem discovery and leakage audit:** `analysis/phase1_*`, aggregate `analysis/phase2_*`, and `results/assessment_findings.md`. The row-level `analysis/phase2_exception_analysis.csv` is intentionally excluded from the public repository.
- **B — Workflow redesign and exception handling:** `analysis/phase3_*`.
- **C — Reconciliation prototype:** `src/`, `config/`, `tests/`, and the run instructions above.
- **D — Dashboard, SOP, and rollout plan:** `dashboard/`, `documentation/phase6_dashboard_explanation.md`, `documentation/phase7_renewal_operations_sop.md`, and `documentation/phase8_30_60_90_day_rollout_plan.md`.
- **Case report:** [`submission/Bambinos_AI_Program_Manager_Assessment_Report_Public.pdf`](submission/Bambinos_AI_Program_Manager_Assessment_Report_Public.pdf).

The assessment brief is available from the [official Bambinos assessment repository](https://github.com/bambinoslive/AI-PM-hiring-take-home-assignments); the brief PDF is not redistributed here.

## Dataset provenance and privacy

The five supplied CSVs were provided for the take-home assessment. They include populated parent/student/educator name or contact columns, student-linked identifiers, payment references, and child schedule details. They are **not included** in this public-preparation tree. Do not copy them into `data/` or commit them without explicit authorization and a privacy review. The committed example records are synthetic and must not be cited as assessment findings.

Local authorized inputs can be placed under `data/` (ignored by Git), then processed with the CLI using an explicitly chosen output directory. Local generated `outputs/` are also ignored. Do not use `git add -f` for these paths.

## Safety and limitations

- Exact identifiers are required; student ID or similarity is never used to repair an invoice mismatch.
- `Partially_Paid` remains in human review under the provisional policy; a source status is not gateway verification.
- The prototype cannot resolve payment evidence against a live gateway, confirm live capacity, or send communications.
- `AUTO_APPROVED` is a renewal-eligibility state, not permission to create a request or schedule.
- Outputs are local assessment artifacts and are not production audit storage.
- The suite passed **57 tests** in a clean-clone check without `data/` or `outputs/`; tests use the included synthetic fixtures and temporary test outputs. Re-run the command above to validate your environment.

For the submission-artifact privacy boundary, see [`submission/README.md`](submission/README.md). Prompt provenance is documented in [`prompts/README.md`](prompts/README.md).
