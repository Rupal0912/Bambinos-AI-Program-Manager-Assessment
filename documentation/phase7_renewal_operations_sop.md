# Phase 7: Renewal Operations SOP and Escalation Framework

**Status:** Proposed operating procedure for the assessment prototype. This is not an approved live-company policy. Service targets below are Phase 3 proposals and require business validation before use.

## 1. Purpose and scope

This SOP describes how Operations can track a renewal from recorded payment through teacher form, payment/eligibility review, booking request, batch choice and class schedule. Its aim is to give each handoff an owner and evidence trail while protecting existing live classes.

It covers the renewal queue and its exceptions. It does not verify payments with a live gateway, authorize refunds, change source records, approve uncertain cases, select a batch for a parent, or create or edit live schedules. The Phase 4 prototype is a local, read-only assessment tool: `config/policy.json` keeps automatic approval disabled and disallows booking, schedule and notification writes. The Phase 6 dashboard is also read-only.

| Team / role | Responsibility in this SOP |
|---|---|
| Operations queue owner | Monitors dashboard and queues, assigns cases, checks source evidence, records handoffs and closure. |
| Assigned educator / teacher | Submits or corrects renewal form information through the authorized source process; does not determine payment settlement. |
| Finance | Verifies authoritative payment and settled amount; decides payment-related exceptions under approved policy. |
| Batch owner | Checks current capacity and seat hold using an authoritative source. |
| Scheduling Operations | Creates or verifies booking requests and schedules only under authorized procedures; preserves valid class occurrences. |
| Parent | Makes an explicit batch selection when required and confirms any requested choice. |
| Operations lead | Resolves queue priority/capacity conflicts, approves controlled repairs and coordinates incident escalation. |
| Data / systems owner | Maintains source access, ingestion, event records, auditability, and technical incident response. |

## 2. End-to-end renewal processing SOP

Exact identifiers are used at every join: invoice `id` to form `invoice_id`; form `id` to request `faculty_form_id`; request `id` to schedule `bookingrequest_id`. A student ID may help a person investigate, but must not repair a disagreement between invoice IDs.

| Stage | Trigger and required evidence | Responsible owner | System action | Human action | Output and exception conditions |
|---|---|---|---|---|---|
| 1. Payment received | A payment event or invoice row is received. Evidence: source invoice ID and authoritative payment-provider event/status when available. | Finance owns settlement evidence; systems owner owns ingestion. | Ingest/validate the event and preserve its source ID and timestamp. In the prototype, read the invoice extract only; `Paid` is a literal CSV value, not gateway verification. | Finance checks conflicts or missing provider evidence. | Invoice/payment event available for matching. Failed, partial, reversed, or unverified states remain held for their specific reason; do not infer eligibility from amount or reference fee. |
| 2. Teacher renewal form submitted | A teacher submits a renewal form. Evidence: form ID, invoice ID, student/class/educator identifiers, requested renewal details, and submitted status. | Assigned educator submits; Operations monitors. | Capture the form row and submitted values without rewriting the source. | Teacher corrects source information through the authorized process if requested. | Form is available for exact-ID reconciliation. Missing forms, blank/unknown status, or inconsistent details go to review; no student-only matching. |
| 3. Invoice and form reconciled | A new/changed invoice or form enters the reconciliation snapshot. Evidence: exact invoice and form IDs and source extracts. | Operations; systems owner supports processing. | Join only on exact `invoices.id = form.invoice_id`; detect missing invoice links and repeated form references. | Operations investigates the indicated source records and records a disposition; never silently fixes an ID. | Unique exact link or reason-coded exception. No match, nonexistent invoice, duplicate reference, or linked identity disagreement holds downstream progression. |
| 4. Payment and eligibility verification | An exact link exists, or a payment-related exception is raised. Evidence: authoritative gateway settlement, approved eligibility/status rule, and signed-off amount/currency rule. | Finance decides payment evidence; Operations applies approved workflow rule. | Compare deterministic fields against the approved policy version and record evidence. Prototype policy is conservative and auto-approval is disabled. | Finance resolves partial, failed, amount, refund/reversal, or source conflicts. | Verified eligible payment evidence or a payment exception. `Partially_Paid` does not qualify by assumption; package/list price is not proof of settled funds. |
| 5. Form approval or exception routing | Payment and form evidence are ready for decision. Evidence: approval status meaning, exact link, identity checks, and any human dispositions. | Operations approver; Finance for payment decisions; Operations lead for escalations. | Apply configured deterministic gates and write decision/audit evidence in the future approved workflow. Current prototype only produces outcomes/reports. | Authorized person approves, rejects, or routes the form under confirmed policy. | Approved form decision or open exception. Pending, missing, blank, rejected, or unknown statuses cannot auto-approve. Do not equate form approval with a schedule. |
| 6. Booking request creation | An authorized form approval is recorded and the request is not already present. Evidence: approved form ID, invoice link, eligibility disposition, idempotency check, and repair authorization if applicable. | Operations / Scheduling Operations. | In a future controlled workflow, create at most one request and record its request ID. Prototype configuration does not create booking records. | Confirm source completeness and use approved repair steps for approved forms without requests. | Booking request with its own status and audit link. A booking request is not a class schedule. Existing request, conflicting ID, or uncertain approval is routed for review. |
| 7. Batch allocation or parent batch selection | Booking request is approved for allocation. Evidence: explicit parent intent/choice, current authoritative capacity, and seat-hold result. | Batch owner verifies capacity; Operations coordinates; parent selects where required. | Read current capacity and record the result; do not rely on the undated reference snapshot as live availability. | Parent chooses from confirmed options when a choice is required. Batch owner confirms a seat/hold. | Confirmed allocation, pending parent selection, or capacity exception. Never override a full batch or infer consent from current batch. |
| 8. Class schedule creation | A valid booking request and confirmed allocation/choice satisfy the approved scheduling procedure. Evidence: request ID, selected batch, calendar/teacher availability, schedule rules and authorization. | Scheduling Operations; batch owner/teacher consulted as defined by policy. | Validate required IDs, slot constraints, conflicts, and idempotency before any authorized write. The prototype does not create schedules. | Human scheduler confirms calendar rules and any exception before a live schedule action. | One or more valid schedule occurrence rows linked to the request. Missing rows require freshness/status checks; multiple rows are not duplicates merely because they share a request. |
| 9. Closure and audit logging | A stage is completed or a human disposition is made. Evidence: source IDs, decision/reason, evidence references, actor, timestamp/timezone, rule version, and any side-effect ID. | Case owner; Operations lead reviews exceptions; systems owner maintains the log. | Record immutable decision history and case status; repeated processing must preserve stable IDs and avoid duplicate side effects. | Case owner confirms resolution evidence and notifies stakeholders only when required and authorized. | Closed case with evidence, or an explicitly waiting case with owner/dependency and next review. Do not delete/overwrite source data or erase prior outcomes. |

**Booking request versus schedule:** the request records an approved renewal's operational request and its allocation state. A schedule row records a specific class occurrence (date/time/batch) linked to a request. A request can await batch allocation or parent choice before any schedule exists. Multiple schedule rows can represent distinct class occurrences; count alone is not a duplication test or proof of session coverage.

## 3. Exception handling SOP

The meanings and owners below follow the Phase 3 taxonomy. Severity is the default proposed severity, not an incident classification for every live case. `outputs/exception_report.csv` uses prototype reason codes and may contain multiple findings for one case; finding counts are not failed-case counts.

| Reason code | Meaning | Default severity | Responsible team | First action | Escalation condition (proposed) | Closure evidence |
|---|---|---|---|---|---|---|
| `PAID_RENEWAL_NO_EXACT_FORM` (EX-01) | Paid renewal invoice has no exact linked form. | High | Operations + educator | Locate/submit the correct form using its authoritative invoice reference; no student-ID fallback. | Ops lead if unresolved in proposed 12-hour review window or before a scheduled class is at risk. | Exact form-to-invoice source link or documented verified disposition. |
| `FORM_INVOICE_ID_NOT_FOUND` (EX-02) | Form refers to an invoice absent from authoritative invoice source. | High | Operations + Finance; educator supplies correction | Verify invoice/gateway source; hold downstream processing. | Finance/Ops lead if source verification misses proposed 2-business-hour first response. | Authoritative invoice evidence and auditable corrected source reference or documented non-match. |
| `DUPLICATE_FORM_INVOICE_REFERENCE` (EX-03) | Multiple forms reference the same invoice ID. | High | Operations | Hold request creation; compare both forms and determine canonical disposition under approved duplicate policy. | Ops lead if unresolved by proposed 4-business-hour duplicate review target. | All form IDs retained, authorized disposition, and duplicate group marked resolved. |
| `PAYMENT_PARTIAL_POLICY_REVIEW` (EX-04) | Payment is partial or settlement evidence is incomplete. | High | Finance + Operations | Finance checks settled funds and applies approved partial-payment rule. | Finance lead if open past proposed 1-business-day resolution target; external investigation is separately tracked. | Provider/source evidence, decision under named policy version, and recorded amount/status. |
| `PAYMENT_FAILED` (EX-05) | Authoritative payment status is failed. | High | Finance | Stop booking/schedule progression and check for a later successful attempt. | Immediate Finance lead escalation if class start is near or systems conflict. | Authoritative payment attempt history and final disposition; any later success must be separately identified. |
| `PAYMENT_AMOUNT_CONFLICT` (EX-06) | Form amount differs from approved settled amount/tolerance. | High | Finance + Operations | Compare gross, discount, net and settled evidence; do not select a field by guess. | Finance lead after proposed 2-business-hour first response target. | Finance-approved comparison and amount rule, evidence references, and recorded resolution. |
| `APPROVED_FORM_NO_REQUEST` (EX-07) | Approved form has no exact request after source refresh. | Phase 3 taxonomy: Medium; Phase 4.1 decision engine: High. Severity is discrepant and pending business confirmation; do not silently choose one. | Operations | Refresh sources and check idempotency ledger before a controlled repair. | Phase 3 EX-07 matrix proposes escalation after a 4-business-hour triage target; the target requires business approval before operational use. | Source refresh evidence, existing request ID or authorized repair request ID, audit record. |
| `BATCH_CONFIRMED_FULL` / `REQUEST_FAILED_BATCH_FULL` (EX-08) | Requested batch is full according to current authoritative capacity. Prototype output currently uses `REQUEST_FAILED_BATCH_FULL`; confirm code mapping before production. | High | Operations + batch owner; parent chooses | Verify current capacity/seat hold and present confirmed approved alternatives. | Batch owner/Ops lead if no alternative or seat decision within proposed 1 business day. | Timestamped capacity/hold evidence and parent choice or documented no-availability outcome. |
| `PARENT_BATCH_SELECTION_REQUIRED` / `PARENT_BATCH_SELECTION_PENDING` (EX-09) | Explicit parent batch choice is required or absent. Phase 3 design and prototype currently use these different labels. | Medium | Parent + Operations | Send approved options and wait for explicit recorded selection. | Proposed reminder after 24 hours and Ops escalation after 2 business days; business to approve timing and calendar. | Message/delivery reference as authorized, explicit parent choice, and selected option ID. |
| `REQUEST_WITHOUT_SCHEDULE_REVIEW` / `REQUEST_WITHOUT_SCHEDULE` (EX-10) | Request exists without linked schedule row in the current extract. The implementation output uses `REQUEST_WITHOUT_SCHEDULE`; Phase 3 uses the suffixed label. | Medium | Operations / Scheduling | Check request state, extract freshness and schedule-generation rule; absence alone is not failure. | Only after approved schedule SLA expires or source evidence conflicts. | Refreshed source result, valid schedule ID(s), or documented current request state and next owner/action. |
| `MULTIPLE_VALID_SCHEDULE_INSTANCES_NOOP` / `SCHEDULE_CONFLICT_REVIEW` (EX-11) | Multiple schedule rows link to one request; review only if conflicting IDs/occurrences exist. Phase 3 and prototype labels differ. | Low by default; proposed High for conflict | Scheduling service; Operations for conflict | Validate schedule IDs, dates, slots and cancellations; preserve valid distinct occurrences. | Escalate for duplicate occurrence or conflicting student/batch/time, not row count alone. | Per-row validation and evidence of distinct valid instances or authorized conflict correction. |
| `BATCH_CAPACITY_UNCONFIRMED` (EX-12) | Capacity snapshot is stale, missing freshness or conflicts with live evidence. | Medium | Operations + batch owner | Refresh the authoritative source; do not approve/block based on stale reference data. | Escalate if authoritative source unavailable at allocation time or before class risk threshold. | Timestamped authoritative capacity and seat-hold result, or documented dependency/next review. |
| `IDENTITY_MISMATCH` (EX-13; implementation code mapping to confirm) | Student/user/class/educator identifiers disagree across exact-linked records. | High | Operations + data owner; Finance if payment identity is affected | Hold progression and compare authoritative enrollment/student records. | Immediate escalation if funds could be assigned to another learner or wrong learner could be enrolled. | Source-of-truth identifiers and controlled correction/disposition with actor and audit record. |

The reason strings separated by `/` above are **not** merged. They identify known naming differences between the Phase 3 design taxonomy and current Phase 4 output. Confirm a canonical code dictionary and migration mapping before operational reporting or trend comparisons. The Phase 3 codes `EX-01`–`EX-13` are taxonomy references; they are not fields currently emitted in the exception report.

## 4. AI versus human responsibility matrix

| Activity | Deterministic automation | AI assistance | Human decision / prohibited action |
|---|---|---|---|
| Exact-ID reconciliation and duplicate detection | Match specified IDs, detect repeats, validate required fields, attach reason codes. | May summarize the matched evidence in plain language. | A person investigates source errors. No ambiguous invoice relinking by student ID alone. |
| Payment and amount validation | Compare authoritative provider status and approved settled amount against signed-off rules. | May draft an explanation of an already-established exception. | Finance confirms payment. AI must not confirm payment without authoritative evidence or decide disputed/partial eligibility. |
| Approval and eligibility | Apply only versioned, approved deterministic gates; in this assessment, auto-approval is disabled. | No authorization role. | Authorized Operations/Finance approver handles exceptions. AI must not approve disputed or partial payments. |
| Capacity and parent choice | Validate current capacity response, seat-hold and recorded choice fields. | May draft parent options message from approved alternatives. | Batch owner confirms capacity; parent selects. AI must not override capacity or choose for a parent without authorization. |
| Booking and scheduling | Validate IDs, idempotency and configured calendar constraints before an authorized action. | May summarize conflicts for a scheduler. | Human/authorized scheduling process validates live calendar and writes. AI must not create live schedules without required booking and calendar validation. |
| Communications and audit | Store approved templates, delivery status, evidence links and decision history. | Draft/summarize only; a person reviews before sending where required. | No message is sent by this prototype. Human action and all system side effects require audit evidence. |

## 5. Daily Operations checklist

Use the Phase 6 dashboard and its searchable actionable queue as the prototype's morning view. Refresh/reconcile the underlying extracts first; if the dashboard says output hashes are stale, do not action stale decision or exception rows.

### Morning dashboard review

- Confirm the displayed input snapshot matches the reconciliation audit hash.
- Review paid renewal invoices, exact form-link gaps, pending teacher forms, approved forms without requests, allocation states, requests without schedule rows, and hours-saved availability.
- Review exception findings by exact reason code, severity, owner and next action. A finding count is not a count of failed renewals.
- Do not label a record overdue from the snapshot: the dashboard has no trusted as-of time and approved SLA clock configuration.

### Queue assignment and prioritization

- Assign one named queue owner and backup to each open case in the operational case log (not currently supplied by the prototype).
- Triage payment failure, invoice-link failure, identity risk and payment amount conflicts first; then duplicates, capacity, parent choice, missing forms, and schedule visibility, while considering imminent class continuity.
- Keep each exact reason code separate and retain evidence/IDs. Do not expose unnecessary parent contact details in broad-access notes.

### Midday backlog check

- Recheck case owner, last action, waiting dependency, next review time, and whether a proposed target is approaching. The target is not an approved SLA unless signed off.
- Separate Ops-controlled time from time awaiting parent, teacher, gateway or batch owner. Do not silently count waiting time as resolved.
- Refresh source snapshots before concluding that an item remains unresolved.

### End-of-day reconciliation

- Refresh the authorized extracts and run the approved reconciliation process; prototype command is `python src/reconciliation.py` and writes assessment outputs, not live records.
- Compare new findings to prior case IDs and record new, changed, resolved and waiting states in the case log. Preserve source records and prior decisions.
- Confirm every human disposition has actor, timestamp/timezone, evidence, reason code and rule/policy version.
- Escalate any unowned high-severity case or imminent class-continuity risk before handover.

### Shift handover

- Transfer case ID and source IDs, current outcome/reason, evidence checked, owner, last action, dependency, next review, escalation status, and parent/teacher communication status where authorized.
- Receiving owner acknowledges high-severity and time-sensitive items. Never pass a case as “done” without closure evidence.

## 6. Escalation matrix

These are the Phase 3 **proposed** targets. They require business approval of timezone, business calendar, holidays, start/stop events, pause rules, local contact hours, and external-wait treatment. Business-hour targets stay in business hours; the Phase 3 12-hour missing-form window is explicitly elapsed time only pending confirmation.

| Case / measure | First response target (proposed) | Resolution / next milestone target (proposed) | Escalation trigger | Escalation owner | External dependency handling |
|---|---|---|---|---|---|
| Ingestion and deterministic validation | 95% of valid gateway events staged and checked within 5 minutes. | Validation outcome recorded. | Source watermark/retry misses target or events conflict. | Systems owner, then Operations lead. | Track provider delay separately; preserve event ID and retry history. |
| Paid renewal without form | Alert educator/Ops within 15 minutes; first human review within 2 business hours. | Reconcile within 12 elapsed hours (whether this means elapsed clock is to be confirmed). | Unresolved at proposed 12-hour window or next class at risk. | Operations lead. | Record teacher/educator wait start and follow-up; do not silently pause an unapproved clock. |
| Payment or amount exception | Finance first review within 2 business hours. | Proposed 1 business day excluding external gateway investigation. | First response missed, or investigation remains open beyond internal target. | Finance lead. | Record provider case/reference and awaiting-provider interval separately; retain next check time. |
| Duplicate form reference | Triage within 4 business hours. | Canonical disposition before any downstream request creation. | Still unresolved at proposed 4-business-hour target. | Operations lead. | Teacher clarification is a dependency; preserve every submitted form. |
| Complete form approval | Resolve 95% of fully evidenced, policy-eligible cases within 2 business hours. | Approval/review decision recorded. | Evidence complete but target missed, or policy ambiguity is discovered. | Operations lead; Finance for payment rules. | Incomplete evidence is not treated as a complete-case clock without an approved definition. |
| Same-batch booking after verified approval | Create/confirm request and seat hold within 15 minutes. | Schedule only after separate calendar checks pass. | No authoritative capacity or seat-hold result, or imminent class risk. | Scheduling Operations / batch owner; Ops lead. | Awaiting capacity endpoint is a tracked dependency; never bypass it. |
| Parent batch selection | Send approved options within 15 minutes after verified request. | Reminder after 24 hours; Ops escalation after 2 business days without response. | No selection after proposed escalation interval. | Operations lead; parent owns the choice. | Record send/delivery/reply IDs and local time rules; timing needs approval. |
| Ops-controlled exception resolution | Queue owner assigned promptly (target not specified in Phase 3). | 90% closed within 1 business day; report external-wait cases separately. | Internal target missed, high-severity case unowned, or class continuity risk. | Named queue owner, then Operations lead; Finance lead for payment. | Capture opened/first-action/awaiting-party/resumed/resolved timestamps and pause reason. |
| Approved form with no request | No approved target. Phase 3 EX-07 matrix proposes 4-business-hour triage; this requires business approval before use. | Repair only under approved procedure after source refresh and idempotency check. | Escalate after a business-approved triage target is missed; until then, prioritize by operational impact and class risk without labeling the case overdue. | Operations lead. | Check for upstream/source delay and existing request before repair. |
| Full batch / capacity uncertainty | No separate first response beyond capacity workflow target is specified. | Proposed 1 business day for alternative or confirmed seat decision. | No alternative or seat decision by target, or batch source unavailable. | Batch owner / Operations lead. | Wait for authoritative capacity; reference snapshot has no timestamp and is not authoritative. |
| Request without schedule / schedule conflict | No independent numeric target defined; check request state and approved scheduling SLA. | Resolve only after schedule-generation rules and clock are defined. | Approved schedule SLA expires or records conflict. | Scheduling Operations / Operations lead. | Refresh extract and track calendar/batch dependency; missing row alone is not failure. |

Do not convert a business-hour target to elapsed hours. Do not mark any current dashboard item overdue: Phase 6 states that reliable snapshot age and SLA attainment are unavailable.

## 7. Team operating model for 10 people

This is a proposed role allocation, not a statement about current staffing or authority. People may cross-cover after training, but each case has one accountable owner at a time.

| Suggested coverage | Seats | Primary focus | Backup |
|---|---:|---|---|
| Queue lead / escalation coordinator | 1 | Daily queue review, assignment, aging instrumentation, handover and escalation. | Trained senior Operations generalist. |
| Renewal reconciliation generalists | 4 | Exact-ID linkage, form completeness, standard approvals where authorized, case updates. | Cross-cover among the four; queue lead for urgent cases. |
| Scheduling and batch coordination | 2 | Capacity confirmation, parent choices, booking/schedule state coordination. | Each other; trained renewal generalist for intake triage. |
| Finance liaison / payment exception specialists | 2 | Payment-provider evidence, partial/failed/amount exceptions, finance case follow-up. | Each other; Finance remains decision authority for settlement. |
| Data and systems operations | 1 | Extract freshness, access, reconciliation run, audit and incident coordination. | Designated trained backup from queue lead/generalists for continuity; systems owner retains technical authority. |

The proposed 10-seat arrangement divides queue ownership by work type, not by teacher count. To support 200+ teachers, use structured form fields for invoice ID, stable reason codes, a shared case queue, clear team routing, published response channels, and a rotating educator contact point per teacher cohort if the business adopts one. Keep one intake path and common rules so teachers do not need to understand internal routing. During peak volume, the queue lead can rebalance trained generalists by reason-code volume. Validate workload and coverage with a shadow-mode baseline before setting staffing ratios or asserting capacity.

Live classes are protected by separating renewal triage from class operations: no active schedule is edited as part of a renewal repair without authorized change control; any confirmed imminent class impact is escalated to Scheduling Operations and the Ops lead.

## 8. Safety and change control

- Initial rollout is read-only/shadow mode. Do not change existing live schedules without explicit authorization and the normal scheduling change process.
- Do not silently correct IDs, amounts, statuses, batch selections or student assignments. Corrections must be source-backed, authorized, attributable and recorded.
- Never delete or overwrite source records. Keep original records and append an auditable disposition/correction event.
- Human review is required for exceptions and for every unresolved business rule. No payment, enrollment, batch or schedule side effect is authorized by this SOP alone.
- Maintain an audit trail of source IDs, exact match keys, evidence, decision, reason code, policy/rule version, actor, timestamp/timezone, previous decision and any side-effect ID.
- Idempotency checks must prevent a repeated run from creating duplicate booking requests or schedules. Existing distinct schedule occurrences must be preserved.
- For an incident (wrong learner/payment linkage, unauthorized write, possible duplicate enrollment/schedule, data exposure, or disruption to a live class): stop the affected automation path, preserve logs and source evidence, notify the Operations lead and relevant Finance/Scheduling/Data owner immediately, assess affected records, and resume only after authorized incident disposition and documented validation.
- A rollback means disable/stop the affected automation and restore its prior configuration/output view under controlled versioning. It does not mean deleting source records or erasing audit history. Any live-system correction follows the separately authorized system procedure.

## 9. Open policy decisions before live use

These questions remain unresolved in the supplied Phase 2–6 artifacts and should be answered by the named business owners before enabling writes or automatic approval:

1. Which payment source and amount field are authoritative (gross, discount, net, `amount_paid`, settled amount, currency, rounding and tolerance)? **Owner:** Finance.
2. Are partial payments ever eligible, and what evidence/status qualifies? What about refunds, chargebacks, reversals and later successful attempts? **Owner:** Finance / business owner.
3. Can an invoice have multiple forms? What identifies the renewal cycle, canonical form and duplicate disposition? **Owner:** Operations / educator lead.
4. What do every approval/request/batch status mean, and what transitions are permitted? Are missing, blank, rejected and unknown approval values always held? **Owner:** Operations / product owner.
5. When is parent choice required, how is explicit consent stored, and what reminder channel/local-time/contact rules apply? **Owner:** Operations / customer communications owner.
6. Which capacity source is authoritative and how fresh must it be? How are active counts, seat holds, concurrent allocation and release handled? **Owner:** Batch owner / scheduling.
7. How many schedule rows or class sessions should a renewal create, and how are cancellations, reschedules and future-dated sessions represented? **Owner:** Scheduling / academic operations.
8. What do `deleted_at` and other soft-delete fields mean, and are inactive/deleted records in the extracts? **Owner:** Data/system owner.
9. What timezone, business calendar, holiday/weekend rules, clock start/stop events, pause rules and extract-as-of timestamp define each SLA? **Owner:** Operations leadership.
10. Which taxonomy is canonical where Phase 3 and Phase 4 code labels differ, including full batch, parent selection, no-schedule, multiple schedules and identity mismatch? **Owner:** Operations + data/system owner.
11. Who can authorize booking-request repair, live schedule creation/change, outbound notification, and rollback? **Owner:** Operations leadership / system owners.

## Consistency notes for adoption

- The Phase 3 decision framework and matrix are design proposals; Phase 4 `config/policy.json` explicitly sets `auto_approval_enabled` to `false`, `PROTOTYPE_ONLY`, and disables booking/schedule/message writes. Treat current outputs as review evidence, not live workflow actions.
- Phase 3 reason labels and Phase 4 output labels are not fully aligned. Examples in the current exception report include `REQUEST_FAILED_BATCH_FULL`, `PARENT_BATCH_SELECTION_PENDING`, and `REQUEST_WITHOUT_SCHEDULE`; Phase 3 also uses `BATCH_CONFIRMED_FULL`, `PARENT_BATCH_SELECTION_REQUIRED`, and `REQUEST_WITHOUT_SCHEDULE_REVIEW`. Do not merge or relabel these in reports without an approved mapping.
- `APPROVED_FORM_NO_REQUEST` has a severity discrepancy: Phase 3 EX-07 labels it Medium, while `src/decision_engine.py` assigns High. The supplied `outputs/exception_report.csv` has no row with this reason code, so there is no emitted finding in that output to resolve the discrepancy. Keep both source values visible and obtain business confirmation before standardizing severity.
- Phase 3 EX-07 in `analysis/phase3_exception_matrix.csv` proposes a 4-business-hour triage target for an approved form without a request. `analysis/phase3_kpi_sla_design.md` does not define a separate SLA row for this case; its 4-business-hour target is for duplicate form references. Therefore the EX-07 triage timing is marked as requiring business approval in this SOP. It is separate from the 15-minute same-batch booking-request and seat-hold milestone, which Phase 3 does explicitly list.
- Phase 3 taxonomy includes an identity mismatch code, while the observed Phase 4 exception report supplied here does not show that code. Confirm the implemented validator/code mapping before treating it as an emitted prototype reason.
- Phase 2 records 8 Pending forms, three requests with no schedule rows and two distinct schedule occurrences for request REQ-A. These are snapshot observations, not overdue cases, failed renewals, or schedule duplicates.
- Phase 3 SLA targets are proposals; Phase 6 measures no aging/SLA attainment. Establish event timestamps and an approved calendar before measuring performance.
