# Phase 3: KPI and SLA Design

**Design proposal only.** Phase 2 results describe this small extract; they are not live performance or approved service levels. The suggested targets below require Operations, Finance and business-owner approval, including timezone, business hours, holidays and parent/teacher response-time rules.

## KPI definitions and what the five CSVs can support

| KPI | Proposed formula | Current five-CSV support | Phase 2 observation | Primary owner |
|---|---|---|---|---|
| Invoice-to-form match rate | Distinct eligible paid renewal invoice IDs with >=1 exact `invoices.id = form.invoice_id` / all eligible paid renewal invoice IDs | **Measurable as a snapshot** if eligibility is confirmed; exact ID is present. | 8/11 = 72.7% using literal `Paid` + `is_renewal=Yes`. Not a company-wide rate. | Operations; Finance owns eligibility definition |
| Unresolved payment exceptions | Count of distinct payment/renewal cases with an open payment exception and no `resolved_at`; optionally rate = open payment exceptions / eligible renewal payments | **Not measurable as open/resolved queue status.** CSVs show status/amount signals but no exception case, owner, or resolution timestamp. A snapshot proxy can count Partially_Paid, Failed and amount conflicts. | Proxy signals include invoice INV-I (Partially_Paid/amount conflict) and INV-K (Failed). Do not label them open without live case state. | Finance |
| Duplicate form rate | Affected teacher form rows with an invoice ID repeated / total teacher form rows (keep definition stable for trend) | **Measurable as a snapshot** by repeated `invoice_id`; cycle/soft-delete policy unknown. | 2/12 = 16.7% affected forms (forms FORM-G/FORM-H). One repeated invoice group. | Operations |
| Form approval turnaround | Median `approved_at - created_at` for forms with both timestamps; also report valid count and pending age separately | **Partially measurable.** Timestamps exist for approved rows, but timezone and SLA calendar are unknown; pending forms have no `approved_at`. | 4 valid rows; median 1.5417 hours. This is sample descriptive data, not an SLA result. | Operations |
| Booking request-to-schedule conversion | Requests with >=1 valid, non-cancelled schedule row / requests eligible to be scheduled in that cohort | **Only presence proxy measurable.** Need eligibility/cohort and expected schedule-generation policy to define true conversion/completion. | 1/4 requests has schedule rows (25% presence proxy); not proof 24 sessions were completed/scheduled. | Scheduling Operations |
| Approved but unscheduled requests | Requests linked to Approved forms with no valid schedule row / requests linked to Approved forms | **Measurable as point-in-time presence** using form/request/schedule IDs; not overdue without age/SLA. | 3/4 = 75%; requests REQ-B, REQ-C, REQ-D have different current states. | Operations |
| Batch allocation failure rate | Requests explicitly `Failed_Batch_Full` / requests with a batch-allocation decision (after allocation-state definition) | **Status proxy measurable.** Need a denominator that distinguishes pending, parent selection and attempted allocations. | 1/4 of all requests; preferred future denominator is allocation attempts, not all requests. | Batch owner / Operations |
| Exception resolution time | Median/P90 of `resolved_at - opened_at` by reason/severity; report unresolved age separately | **Not measurable**: no exception open/resolution events exist in CSVs. | N/A. Do not substitute payment-to-form or form-to-approval time. | Queue owner; Finance for payment issues |

### Measurement guardrails

- For payment-based rates, a proposed initial cohort is `payment_status=Paid` and `is_renewal=Yes`, exactly as recorded. This needs approval as the production eligibility definition. Do not include Partially_Paid as paid by default.
- Use exact IDs. Do not fix missing links by matching on student ID or amount. Deduplicate to renewal/invoice key where the KPI is invoice-level; say whether the unit is a row, invoice, form, request or case.
- Do not treat null `deleted_at` as active until lifecycle semantics are confirmed. Capture an explicit snapshot timestamp and source extract boundary.
- Distinguish “has at least one schedule row” from “all purchased sessions are scheduled.” Phase 2 has two distinct rows for request REQ-A, and no rule describing expected schedule-row count.
- A status count is a queue snapshot, not an SLA breach. An SLA needs a start event, stop event, timezone/calendar and paused-time rules.

## Proposed SLA targets for discussion (not approved)

The numbers are starting points for a pilot discussion, not observed performance. A clock should start only after the relevant event is complete and authoritative. Use elapsed-time targets only if weekends/holidays and region-specific class timezones are agreed.

| Service measure | Proposed target | Clock start/stop | Owner | Data required / approval note |
|---|---|---|---|---|
| Ingestion and deterministic validation | 95% of valid gateway events staged and checked within 5 minutes | Signed payment event received → validation outcome recorded | Systems owner | Webhook/source timestamps, retries and source watermark; confirm realistic system capability. |
| Paid renewal with no form | Alert educator/Ops within 15 minutes; first human review within 2 business hours; escalate if unresolved at 12 elapsed hours | `paid_at`/verified event → alert, first review, and resolution separately | Operations + assigned educator | Assessment calls out stuck invoices over 12h for monitoring; confirm whether 12 hours is elapsed or business time and how weekends work. |
| Payment/amount exception | Finance first review within 2 business hours; update parent only after verified need; resolution target 1 business day excluding external gateway investigation | Exception `opened_at` → first review and `resolved_at` | Finance | Requires exception case timestamps and pause reason for provider/parent wait. |
| Duplicate form reference | Triage within 4 business hours; no downstream write until canonical form disposition | Duplicate detected → Ops disposition | Operations | Requires duplicate group key and disposition timestamp. |
| Complete form approval | 95% of fully evidenced, policy-eligible cases resolved within 2 business hours | Complete evidence received → approval/review decision | Operations | Define “complete”, timezone, business calendar and sample handling. |
| Same-batch booking after verified approval | Create/confirm booking request and seat hold within 15 minutes; schedule only after calendar rules pass | Verified approval + explicit same-batch intent → booking/hold; schedule event separate | Scheduling Operations | Requires parent intent, current capacity endpoint, seat-hold outcome and expected schedule rules. |
| Parent batch selection | Send approved options within 15 minutes after a verified request; reminder after 24 hours; Ops escalation after 2 business days without response | Awaiting selection state → message, reminder, selection | Operations; parent owns selection | Consent, contact channel, local time, pause/cancel rules and reminders require approval. |
| Exception resolution | 90% of Ops-controlled cases closed within 1 business day; report external-wait cases separately | `opened_at` → `resolved_at`, with paused/awaiting-parent/provider time reported separately | Named queue owner | Requires case ledger, severity and explicit pause/resume events. |

Targets should be revised after a shadow-mode baseline and operational capacity review. Do not claim these targets are met based on the sample durations.

## Instrumentation needed

Add a case/event ledger with `case_id`, source IDs, `reason_code`, `opened_at`, owner, `first_action_at`, `awaiting_party_since`, `resumed_at`, `resolved_at`, resolution code, rule version, and audit actor. Keep event timezone/UTC offset and source event IDs. Add explicit parent choice, renewal-cycle key, live seat-hold result, schedule-generation status, notification delivery/reply ID and a snapshot watermark. These are design requirements, not fields currently present in the five CSVs.
