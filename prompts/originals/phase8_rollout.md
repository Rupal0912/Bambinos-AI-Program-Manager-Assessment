# Phase 8 — Create the 30-60-90-Day Implementation and Change Management Roadmap

Project:
`<PROJECT_ROOT>`

## Objective

Create a realistic 90-day implementation roadmap for the proposed AI-assisted renewal operations workflow at Bambinos.live.

The company has:
- 200+ teachers
- A 10-person Operations team
- Existing live class schedules that must not be disrupted.

This roadmap is part of Deliverable D of the AI Program Manager (Operations) assessment.

## Inspect existing documentation

Read:
- `analysis/phase2_leakage_audit.md`
- `analysis/phase3_architecture.md`
- `analysis/phase3_kpi_sla_design.md`
- `documentation/phase6_dashboard_explanation.md`
- `documentation/phase7_renewal_operations_sop.md`
- `config/policy.json`
- `README.md`

## Create

`documentation/phase8_30_60_90_day_rollout_plan.md`

## Required structure

### 1. Executive rollout strategy

Explain:
- Why rollout must be gradual.
- Why read-only shadow mode comes first.
- Why existing live schedules must remain protected.
- How the 10-person team and 200+ teachers are included.

### 2. Days 1–30: Foundation and shadow mode

Include:
- Business policy clarification.
- Confirm payment and approval rules.
- Resolve reason-code mapping.
- Establish baseline KPIs.
- Instrument event timestamps and manual handling time.
- Validate source data quality.
- Train the 10-person Operations team.
- Prepare teacher communication and support materials.
- Run the prototype in read-only shadow mode.

Define measurable exit criteria. Do not invent actual achieved results.

### 3. Days 31–60: Controlled pilot

Include:
- Select a limited teacher cohort using explicit selection criteria.
- Keep the existing renewal process available as fallback.
- Compare automated decisions with human decisions.
- Keep payment, approval, parent choice, capacity and schedule exceptions under appropriate human control.
- Test duplicate prevention and idempotency.
- Monitor dashboard KPIs daily.
- Run incident and rollback drills.
- Collect teacher and Ops feedback.

Define measurable exit criteria and conditions that stop the pilot.

### 4. Days 61–90: Gradual scale-up

Include:
- Expansion by teacher cohort or operational segment.
- Capacity and support planning.
- Formal ownership and monitoring.
- Ongoing quality audits.
- Review of hours saved, turnaround and exception rates.
- Governance for model/prompt/policy changes.

Do not assume full automation is approved at Day 90. Make expansion conditional on evidence and leadership authorization.

### 5. KPI scorecard

For each KPI include:
- Definition
- Calculation
- Baseline status
- Target or proposed threshold
- Data source
- Review frequency
- Owner

Include:
- Paid renewal exact-form match rate
- Paid renewal missing-form rate
- Payment-to-form turnaround
- Form approval turnaround
- Booking-request creation turnaround
- Request-to-schedule turnaround
- Exception rate by reason code
- Reconciliation precision / false-positive review rate
- Human override rate
- Duplicate booking prevention
- SLA attainment
- Hours saved
- Live class disruption incidents

Clearly distinguish measurable sample observations, future instrumentation requirements and proposed targets.

### 6. Change management and communication

Explain:
- Training for the 10-person Ops team.
- Teacher onboarding across 200+ teachers.
- Simple communication of new form requirements and invoice ID accuracy.
- Support and escalation channels.
- Feedback collection.
- Adoption monitoring.
- How to prevent parallel processes and inconsistent data entry.

### 7. Risk register

Include:
- Risk
- Likelihood
- Impact
- Mitigation
- Owner
- Trigger
- Contingency

Cover payment mismatch, incorrect identity linkage, duplicate requests, stale capacity, parent delays, system downtime, incorrect AI output, data exposure and disruption to live schedules.

### 8. Go/no-go gates

Define what must be true before:
- Leaving shadow mode.
- Starting the controlled pilot.
- Expanding the pilot.
- Enabling any automated write.

Every gate must require evidence, documented owner approval and rollback readiness.

### 9. Governance and ownership

Define responsibilities for:
- Operations Head
- Queue lead
- Operations generalists
- Finance
- Scheduling/batch owner
- Teachers
- Data/system owner

## Important constraints

- This is a proposed roadmap, not an actual company-approved implementation.
- Do not invent actual baseline metrics, pilot outcomes, staffing availability or approved targets.
- Use the Phase 3 proposed SLA targets only with explicit labels.
- Do not claim hours saved without handling-time evidence.
- Do not enable automatic approval or live writes merely because the calendar reaches Day 60 or Day 90.
- Keep the current prototype read-only.
- Do not modify source code, CSVs, dashboard files, policy files or existing SOP.

## Final report

Report:
1. File created.
2. Sections completed.
3. KPIs and exit criteria defined.
4. Risks and go/no-go gates included.
5. Unresolved business decisions.
6. Confirmation that existing files were not modified.