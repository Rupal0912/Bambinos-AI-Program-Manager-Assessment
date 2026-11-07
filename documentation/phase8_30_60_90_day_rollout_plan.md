# Phase 8: 30-60-90-Day Renewal Operations Rollout Plan

**Status:** Proposed roadmap for discussion. It is not a company-approved implementation plan, commitment, staffing allocation, or statement of achieved results. Calendar days are planning windows; progression depends on evidence and named owner approval.

## 1. Executive rollout strategy

Roll out gradually because Phase 2 found direct-link gaps, duplicate form references, payment/amount ambiguity, pending forms, and requests at different scheduling states. Those observations are from a small assessment extract; they do not establish company-wide rates or customer harm. A live workflow needs confirmed source-of-truth rules and complete event data before it can safely make decisions.

Begin in **read-only shadow mode**: collect the same permitted inputs as the current process, generate candidate decisions and exceptions, and compare them with authorized human decisions without writing to payment, booking, or schedule systems. The existing process stays available as the operational fallback. Existing live schedules remain protected; no change to an active schedule is in scope without explicit authorization through the normal scheduling change process.

The plan is designed around the stated operating context of a 10-person Operations team and 200+ teachers. In the first month, all ten team members receive role-based training and feedback is collected from a deliberately selected teacher sample. A controlled pilot would then use a small, named teacher cohort chosen by readiness and support criteria, not simply a percentage of the teacher population. Expansion would proceed in supportable cohorts only after quality, workload, and safety evidence is reviewed. No assumption is made here about current staffing availability or actual teacher volume per cohort.

The existing prototype remains read-only: `config/policy.json` has `auto_approval_enabled: false`, `mode: PROTOTYPE_ONLY`, and disables booking, schedule, and notification writes. Reaching Day 60 or Day 90 does not authorize automatic approval or live writes.

## 2. Days 1–30: Foundation and shadow mode

| Workstream | Proposed actions | Accountable owner(s) | Evidence / output |
|---|---|---|---|
| Policy clarification | Confirm authoritative payment provider/status/amount and currency rules; partial, failed, reversed/refunded payment handling; approval status meanings; duplicate form and renewal-cycle policy; parent choice evidence; capacity freshness/seat holds; expected schedule generation; deletion semantics; timezone and SLA clocks. | Operations Head; Finance; Scheduling/batch owner; Data/system owner | Signed rule register with decision, owner, effective date, version and unresolved items. Unresolved items remain manual review gates. |
| Taxonomy and decision mapping | Compare Phase 3 exception taxonomy with Phase 4.1 emitted codes, severities, owners and actions. Resolve naming/severity differences, including `APPROVED_FORM_NO_REQUEST`; retain legacy mappings for report continuity. | Operations Head; Queue lead; Data/system owner | Approved versioned reason-code dictionary and mapping tests; no silent merge or relabeling. |
| Data quality and provenance | Validate exact IDs, duplicates, missing fields, status domains, source completeness and extract boundaries. Add source snapshot/as-of timestamp, timezone and watermark. Preserve exact-ID-only matching. | Data/system owner; Operations generalists | Data-quality report, source owners, refresh cadence, documented known gaps. |
| Baseline and instrumentation | Define stable KPI units and denominators. Record case open, first action, owner, awaiting-party start/resume, resolution, decision, human override and event timestamps. Measure manual handling time using an agreed sampling method; distinguish active work from waiting. | Queue lead; Data/system owner; Operations generalists | Baseline specification and captured baseline dataset. Do not claim hours saved until reliable manual and automated handling measurements exist. |
| Prototype shadow run | Run the existing reconciliation prototype and dashboard against approved read-only snapshots. Compare candidate decisions to human dispositions; inspect false matches, missed findings, reason-code consistency and idempotency. | Data/system owner; Queue lead; Finance reviewer | Dated shadow-run log, comparison results, discrepancies and corrective actions. No source or live operational writes. |
| Operations and teacher readiness | Train all ten Operations team members on exact-ID evidence, exception handling, escalation, dashboard freshness, audit records, safe communication and fallback. Prepare plain-language teacher form guidance and a support channel. Test materials with a small teacher advisory sample before broad distribution. | Queue lead; Operations Head; educator/teacher liaison | Training completion and competency check; reviewed teacher materials and support routing. |
| Safety preparation | Document access roles, data minimization, incident contact tree, stop/kill-switch path, output restore procedure, and live schedule protection. Practice a tabletop incident. | Operations Head; Data/system owner; Scheduling owner | Approved runbook, access review and drill record; open remediation items assigned. |

### Days 1–30 exit criteria

Proceed to pilot design review only when all are true:

1. Payment, approval, duplicate, identity, parent-choice, capacity and schedule rules have named owners and are either approved or explicitly held for human review.
2. Reason-code mappings and severity discrepancies have a signed decision, or affected cases remain excluded from automation and visibly routed to review.
3. Read-only extracts have source ownership, freshness metadata, reproducible snapshot identity and documented quality checks.
4. Baseline KPI definitions, denominators, timestamp events and manual-time measurement method are documented; missing baseline values are labeled unavailable rather than estimated.
5. Shadow results have human-reviewed precision/false-positive and missed-exception analysis on a sample size agreed by leadership. No numeric threshold is assumed in this plan; the threshold must be approved before review begins.
6. All assigned Operations users complete the role-appropriate training; teacher materials and support path are reviewed.
7. Incident, fallback and rollback drills have named owners and recorded outcomes; no unresolved critical safety issue remains.

Failure to meet an exit criterion extends shadow mode; it does not trigger a calendar-based launch.

## 3. Days 31–60: Controlled pilot

The pilot is conditional on the Day 30 gate. It starts with a limited teacher cohort chosen transparently and with educator leadership input. Keep the normal renewal process available as fallback throughout.

### Cohort selection criteria

- A named teacher/operations contact and backup are available for the pilot period.
- The cohort can be supported by the ten-person team without reducing live-class coverage.
- Renewal records have stable invoice/form IDs and can be observed through read-only sources.
- Pilot cases do not require unresolved partial-payment, identity, capacity, or consent decisions to be automated.
- The group includes a manageable range of ordinary cases and controlled exception examples for observation, with no artificial or fabricated business records.
- Teacher participation, communication, data access and any applicable consent requirements are approved.

### Pilot controls and work

| Activity | Control / owner | Required evidence |
|---|---|---|
| Keep current process available | Queue lead documents fallback steps and confirms who takes over when the tool is unavailable. | Test of fallback on a rehearsed case; owner and contact route. |
| Compare decisions | Operations reviewers compare candidate outcome/reason to the authorized human outcome without allowing the candidate to commit changes. Finance reviews all payment-related samples; Scheduling reviews capacity/schedule items. | Case-level comparison with evidence, disagreement reason, reviewer and disposition. |
| Keep sensitive decisions human-controlled | Payment verification, partial/failed/amount disputes, identity conflict, duplicate canonicalization, parent choice, current capacity, seat hold and schedule validation remain with designated people and authoritative systems. | Audit log shows the evidence and human actor for every decision. |
| Test duplicate prevention | Replay approved test snapshots and controlled test cases; verify stable decision IDs and no duplicate booking/schedule side effects. Since live writes remain disabled, test the idempotency behavior in a non-production test harness. | Repeat-run comparison, stable IDs, replace-not-append output evidence. |
| Monitor dashboard daily | Queue lead checks data freshness, exact reason codes, owners, counts, missing event data and current vs prior trends. Counts are findings/cases only according to their defined units. | Daily review record; stale outputs are not actioned. |
| Incident and rollback drills | Simulate unavailable input, incorrect candidate linkage, duplicate detection failure, data exposure concern and potential schedule disruption. No live schedule is modified for a drill. | Drill timeline, stop/rollback demonstration and follow-up actions. |
| Feedback and adoption | Gather structured Ops/teacher feedback on form clarity, routing, support burden and confusing terms. | Feedback log with themes, action owner and status; no unsupported adoption percentage. |

### Pilot stop conditions

Pause the affected pilot path and revert to the current process if any of these occur:

- A candidate links a payment to the wrong invoice/student or uses a non-exact fallback.
- A material payment, amount, approval-status, parent-choice or capacity rule is unresolved but a path attempts to proceed.
- Duplicate-request or schedule-prevention controls fail in testing, or any unauthorized live write is detected.
- A source snapshot is stale, incomplete, untraceable, or materially inconsistent with the authoritative source.
- Data is exposed to an unauthorized role or a privacy/security incident is suspected.
- Existing live class schedules or class delivery are disrupted, or a credible risk of disruption is identified.
- Human review workload, response coverage or fallback capacity is insufficient to safely handle the pilot cohort.
- The dashboard/reconciliation output cannot be tied to its source snapshot and rule version.

The Operations Head may stop the pilot at any time. Finance, Scheduling, or the Data/system owner may stop their respective unsafe path and escalate immediately. Restart requires documented root-cause review, corrective validation, rollback readiness and owner approval.

### Days 31–60 exit criteria

Recommend an expansion decision only if:

1. Pilot cohort and case boundaries are documented, and the existing process remained available as fallback.
2. Every reviewed case can be traced to source snapshot, rule version, reason, owner and human disposition.
3. Human-vs-candidate comparison results meet the thresholds approved before the pilot; results include missed exceptions and false-positive reviews, not only agreement rate.
4. No unresolved critical identity/payment mismatch, unauthorized write, duplicate side effect, privacy incident or live-class disruption remains.
5. Idempotency and rollback drills pass documented acceptance checks.
6. Queue workload, support demand and coverage are reviewed with measured data; proposed SLA attainment is not inferred from state counts.
7. Operations, Finance, Scheduling and Data/system owners sign the gate decision and risk disposition.

If these criteria are not met, continue or narrow shadow/pilot scope and close the remediation actions before expansion.

## 4. Days 61–90: Conditional gradual scale-up

This phase begins only after the pilot expansion gate. Add teacher cohorts or operational segments in steps sized to actual support capacity. Each step has a named owner, a review date, a feedback route and a rollback path. Do not assume the 200+ teacher population can be moved at once.

| Focus | Proposed approach |
|---|---|
| Cohort expansion | Add one cohort at a time after readiness checks: teacher contact/support, trained Ops coverage, clean source path, approved rules, current capacity evidence, and prior cohort gate approval. Choose cohort size based on observed case volume and queue handling capacity, not an invented fixed percentage. |
| Capacity and support | Review daily exception volume, case mix, response coverage, teacher questions and handover load. Rebalance trained Ops roles only with Operations Head approval and protection for live-class support. |
| Quality assurance | Audit a leadership-approved sample of candidate decisions and all high-severity/payment/identity/duplicate/capacity exceptions. Review missed exceptions, human overrides, reopened cases, and source-data changes. |
| Ownership and monitoring | Establish named business owner for each rule, reason code, source, KPI, support queue, integration and incident response. Maintain a change log and dashboard data-freshness check. |
| Benefits review | Recalculate turnaround, exception rates and handling time from instrumented event data. Compare with a documented baseline and cohort mix; report uncertainty and sample size. Hours saved are calculated only when manual and automated handling measurements are comparable. |
| Governance | Version policy, deterministic rules, mappings, prompts/templates and dashboard definitions separately. Require review, test evidence, approval and rollback plan for each change. LLM output remains advisory and human-reviewed. |
| Automated writes | Any proposal to enable a limited write path requires its own approval gate, least-privilege access, feature flag/kill switch, idempotency, audit trail, reconciliation, tested compensation/rollback and operational owner. Day 90 is not authorization. |

### Day 90 review and exit criteria

At Day 90, leadership receives an evidence pack rather than an automatic “go” recommendation. It contains cohort coverage, data-quality/freshness, KPI definitions and observed values with denominators, candidate-vs-human quality, overrides, unresolved risks, incidents, handling-time evidence, training/support feedback, cost/capacity needs, and the rollback test record.

Any further scale-up requires approval from the Operations Head and relevant control owners. Any automated write additionally requires explicit approval by the affected system owner and business owner. If evidence is weak or incomplete, continue the current safe mode and define the additional observation period.

## 5. KPI scorecard

All observations below are from the supplied assessment snapshot and are **not** company-wide baselines. Proposed thresholds are design suggestions, not approved targets. KPI owners should approve units, cohort eligibility, clock rules and reporting cadence before trend reporting. `n/a` means the current inputs cannot establish the measure as defined.

| KPI | Definition and calculation | Baseline status in supplied work | Target / proposed threshold | Required source / future instrumentation | Review frequency | Owner |
|---|---|---|---|---|---|---|
| Paid renewal exact-form match rate | Distinct explicitly eligible paid-renewal invoice IDs with ≥1 exact form link ÷ eligible paid-renewal invoice IDs. | Snapshot: 8/11 = 72.7% using literal `payment_status=Paid` and `is_renewal=Yes`; proposed eligibility only, not a live baseline. | Phase 3 proposes 95% of valid gateway events staged and checked within 5 minutes; it does not set a match-rate target. Set a match-rate target after policy approval and baseline. | Invoice/form exact IDs, authoritative eligibility, snapshot watermark. | Daily operational trend; weekly quality review. | Operations; Finance approves eligibility. |
| Paid renewal missing-form rate | Eligible paid-renewal invoice IDs without exact form link ÷ eligible paid-renewal invoice IDs. | Snapshot: 3/11 = 27.3%; extract-level linkage signal, not proven leakage. | Phase 3 proposes alert within 15 minutes, first review within 2 business hours, unresolved escalation at 12 elapsed hours (clock meaning requires confirmation); no rate threshold set. | Verified payment event, exact form link, alert/review/resolution timestamps, timezone/calendar. | Daily queue; weekly trend. | Operations + assigned educator; Finance for payment eligibility. |
| Payment-to-form turnaround | Median of form-created timestamp minus verified-payment timestamp for valid exact-ID pairs; report valid sample count and missing endpoints. | Phase 2 descriptive median 0.4511 hours across 10 pairs, with caveats; not a reliable SLA baseline and one pair lacked `paid_at`. | No turnaround target in Phase 3. Establish after event semantics/calendar and shadow baseline. | Provider event timestamp, form created timestamp, timezone, snapshot boundary. | Weekly after sufficient valid volume. | Operations; Data/system owner for event quality. |
| Form approval turnaround | Median `approved_at - created_at` for valid approved forms; report pending cases separately. | Phase 2: 4 valid rows, median 1.5417 hours; small sample, no timezone/calendar approval. Eight forms pending in snapshot; age not established. | Phase 3 proposes 95% of fully evidenced, policy-eligible cases resolved within 2 business hours. Approval required. | Form-created and authorized decision timestamps; complete-evidence definition; business calendar. | Daily queue / weekly KPI. | Operations. |
| Booking-request creation turnaround | Time from verified approval/complete evidence to request creation; report eligible cases and missing endpoints. | No distinct event-based baseline established. Phase 2 has four form-to-request pairs (median 1.5417 hours) but lacks a separately approved verified-approval start definition. | Phase 3 proposes same-batch request confirmation and seat hold within 15 minutes after verified approval plus explicit same-batch intent. Proposal only; schedule is a separate step. | Approval event, explicit intent, request creation, seat-hold event, idempotency result. | Daily pilot monitoring. | Scheduling Operations / Operations. |
| Request-to-schedule turnaround | Time from request reaching schedule-ready state to first valid schedule creation; report request status and valid schedule count. | No reliable cohort baseline. Phase 2 has one request-to-first-schedule observation (0.5014 hours, n=1) and three unscheduled requests in distinct states. | No numeric Phase 3 turnaround target; define only after schedule-ready event and schedule-generation policy are approved. | Request state history, batch/seat confirmation, schedule creation event, cancellations and expected-session policy. | Daily queue; weekly trend. | Scheduling Operations. |
| Exception rate by reason code | Distinct case IDs with a given open reason ÷ defined eligible case cohort; also show raw finding rows separately. Never merge codes without approved mapping. | The output contains findings, sometimes several per case; a case-rate baseline requires a case ledger and stable taxonomy. Phase 2 overall review-signal rate 10/11 = 90.9% is a proposed union, not a failure rate. | No universal target set. Set reason-specific thresholds after taxonomy and baseline approval. | Case ID, exact reason code, opened/closed state, cohort denominator and code-map version. | Daily counts; weekly case-rate review. | Queue lead; functional owner for each reason. |
| Reconciliation precision / false-positive review rate | Precision = human-confirmed correct candidate decisions ÷ all candidate decisions reviewed. False-positive review rate = candidates routed to human review but confirmed valid under signed-off rules ÷ reviewed candidates. Define missed-exception sampling separately. | Not measured in source CSVs; establish in shadow mode with human dispositions. | Threshold must be approved before controlled pilot; no value invented here. | Candidate result, independent human disposition, review sample method, adjudicator and rule version. | Daily pilot; weekly gate review. | Operations Head; Finance/Scheduling review relevant cases. |
| Human override rate | Candidate decisions changed by authorized human disposition ÷ candidate decisions with a final human disposition; report change direction/reason. | Not measurable without candidate-to-human comparison ledger. | Monitor and investigate by reason; no Phase 3 numerical threshold. Any payment/identity/capacity overrides require control review. | Candidate and final decisions, actor, reason, timestamps and rule version. | Weekly. | Operations Head / Queue lead. |
| Duplicate booking prevention | Duplicate booking/request side effects prevented ÷ duplicate attempts detected; also report count of actual duplicate side effects (target zero after the control is approved). | Not measurable from supplied snapshot; request uniqueness in sample is not a prevention-rate baseline. | Acceptance criterion for testing: repeated processing produces no duplicate side effect. Production target/monitoring approved by system owner before writes. | Idempotency key, attempted/created side-effect IDs, replay tests, booking ledger. | Every run; daily review during pilot. | Data/system owner + Scheduling Operations. |
| SLA attainment | Cases meeting approved target ÷ eligible cases with complete start/stop timestamps; separate paused/external-wait time. | Not measurable as attainment from five CSVs; no reliable as-of timestamp, approved SLA calendars or case event ledger. | Phase 3 targets are proposals only; approve target, clock and pause rules first. | Case event ledger, timezone/calendar, event completeness, dependency pauses. | Daily queue; weekly owner review. | Queue lead; each service owner. |
| Hours saved | `((manual handling minutes − automated handling minutes) × eligible cases) / 60`; compare like-for-like cases and include exception handling. | Not measurable; no manual baseline or measured automated handling duration. | Set after time study and shadow baseline. Do not present savings until measurements exist. | Sampled manual task time, automated elapsed/active time, case eligibility and volume. | Monthly after valid instrumentation. | Operations Head; Data/system owner measures. |
| Live class disruption incidents | Count renewal-workflow incidents causing an unauthorized schedule change, missed/incorrect live class, or confirmed interruption; publish severity and affected scope. | No incident baseline supplied. | Proposed control objective: zero unauthorized live schedule changes. Any incident triggers immediate stop and review; formal threshold/definition requires approval. | Incident log, schedule audit history, class impact evidence and severity definition. | Immediate incident reporting; weekly safety review. | Operations Head + Scheduling owner. |

## 6. Change management and communication

### Operations team (10 people)

- Train all ten team members before shadow review. Use role-based scenarios: exact-ID mismatch, duplicate forms, failed/partial payment, amount conflict, pending parent choice, stale capacity, no schedule row, and multiple valid schedule rows.
- Require a short competency check: staff can explain evidence, hold unsafe progression, route to the right owner, avoid unsupported “overdue/failed” labels, and record a complete audit note.
- Designate a queue lead and backup, then rotate shadow-review assignments so workload and decision consistency can be observed. This is a proposed operating pattern, not a statement about current assignments.
- Provide a single internal support/escalation route and a documented fallback procedure. Record questions and update training only through version control.

### Teacher onboarding across 200+ teachers

- Start with a small advisory group and pilot cohort; do not ask all teachers to switch at once.
- Explain the practical requirement in plain language: enter the invoice ID from the authoritative payment/invoice record exactly; do not estimate, copy a student ID into the invoice field, or reuse an old invoice reference.
- Explain which fields are required, how to correct a submission through the authorized source process, what status a teacher can expect, and how to contact support. Do not promise a schedule until a batch and schedule are confirmed.
- Publish one approved form link/process and one support channel per cohort. Keep old and new entry routes from running in parallel for the same cohort after the approved transition date; announce that date and provide a monitored fallback. Do not close the existing route before pilot sign-off.
- Provide short guide, examples with masked/synthetic identifiers, FAQ, and escalation route. Do not distribute real student/payment details in training materials.

### Feedback, adoption, and process control

- Collect teacher and Ops feedback through structured weekly prompts and case-level “confusing field/rework reason” tagging. Assign an owner and disposition to each recurring theme.
- Monitor adoption using teacher submissions through the designated route, form completion quality, use of the old route, support requests and duplicate submissions. Define denominators before publishing rates; do not infer adoption from page views or training attendance alone.
- Reduce parallel processes by using a published cohort start date, one named route, redirects/instructions from the old route where authorized, and a daily check for duplicate/late submissions. Keep a fallback route controlled by the queue lead for incidents.
- Change form fields, templates, rules, prompts or routing only with versioned review and communication. Give teachers a clear effective date and support contact for material changes.

## 7. Risk register

Likelihood ratings are preliminary qualitative planning judgments, not measured frequencies. Reassess them with shadow/pilot evidence.

| Risk | Likelihood (initial) | Impact | Mitigation | Owner | Trigger | Contingency |
|---|---|---|---|---|---|---|
| Payment mismatch or unverified settlement | Medium; source ambiguity is observed in sample | Incorrect renewal progression, payment confusion | Authoritative provider evidence; approved settled-amount rule; Finance review; hold partial/failed/conflicting cases. | Finance | Provider and invoice/form values conflict, status unsupported, or verification unavailable. | Stop payment-dependent progression; open Finance case; use current process only after Finance disposition. |
| Incorrect identity linkage | Low-to-medium; no linked mismatch observed in sample, but impact high | Wrong student/enrollment or funds linked to wrong learner | Exact IDs, cross-field validation, no student-only fallback, restricted corrections and audit. | Operations + Data/system owner | ID disagreement, absent invoice, or suspected wrong learner. | Stop case and related path; preserve evidence; immediate Ops/Finance/data review. |
| Duplicate booking/request | Medium; duplicate form reference found, though no duplicate request observed in sample | Double processing, confusing parent/teacher communication | Renewal-cycle key, idempotency ledger, unique constraint/transaction, replay tests and human disposition for duplicate forms. | Data/system owner + Scheduling | Repeated event, repeated form/request, or idempotency collision. | Disable write path; inspect linked IDs; prevent additional side effects; reconcile under authorized repair process. |
| Stale or conflicting capacity | Medium; reference capacity is undated | Overbooking or unnecessary denial | Current authoritative capacity lookup, atomic seat hold, freshness check; reference CSV is not live truth. | Batch owner | Capacity source stale/unavailable or counts conflict. | Hold allocation; offer no alternatives until confirmed; escalate to Scheduling/Ops lead. |
| Parent response delay / no batch choice | Medium; selection state exists in sample | Renewal remains unscheduled; parent confusion | Approved options, consented contact path, local-time reminder rules, clear case owner and waiting state. | Operations; parent owns choice | No reply by business-approved reminder/escalation threshold. | Keep request pending; follow approved contact cadence; do not choose on behalf of parent. |
| System downtime or stale ingestion | Medium | Missing/duplicate processing or stale decisions | Snapshot watermark, health monitoring, replay-safe ingestion, fallback SOP and visible dashboard freshness warning. | Data/system owner | Missing source, failed job, stale hash/watermark, or service unavailable. | Pause automation; use current process with controlled manual logging; replay after validation. |
| Incorrect AI output or unsupported explanation | Low in deterministic decision path; impact medium/high if trusted | Misleading case summary or message | AI limited to draft/summarization; source evidence and reason code remain deterministic; human review; no decision authority. | Queue lead + AI/system owner | Draft adds unsupported fact, changes meaning, or omits a critical conflict. | Do not send/use; correct template/prompt under change control; log issue and disable AI assistance if recurring. |
| Data exposure | Low-to-medium; actual controls require confirmation | Student/payment privacy harm and compliance impact | Least privilege, data minimization, masking, retention rules, encrypted transport/storage and access logs, all confirmed before pilot. | Data/system owner + Operations Head | Unauthorized access, misdirected message, exposed export or suspected compromise. | Stop affected access/integration; preserve logs; follow incident response and notification policy. |
| Disruption to live schedules | Low if read-only controls hold; impact very high | Missed/incorrect class or disruption to existing learners | Read-only shadow mode; separate schedule gate; no edits without explicit authorization; calendar validation and rollback drill. | Scheduling owner + Operations Head | Any unauthorized write, conflicting slot or confirmed class impact. | Immediately stop workflow path, protect current schedule, notify Scheduling/Ops lead, assess impact and resume only after approved incident closure. |
| Taxonomy/policy drift | Medium; Phase 3 and Phase 4 labels differ | Misrouted cases, unreliable KPI trends, wrong severity response | Versioned code dictionary, mapping tests, named owner and approval/change log. | Operations Head + Data/system owner | New/unmapped code or severity disagreement. | Route to human review under visible unmapped status; do not merge until mapping approved. |
| Ops overload / insufficient coverage | Medium; workload baseline unavailable | Queue aging, missed handoffs, teacher support delays | Measure actual volumes and handling time; cohort limits; backup coverage; queue balancing and stop thresholds. | Operations Head / Queue lead | Queue exceeds staffed capacity or required review cannot be covered. | Pause cohort expansion, return to shadow/current process, rebalance only with approval. |

## 8. Go/no-go gates

Every gate requires objective evidence, named owner approvals and a tested rollback/fallback path. A calendar date alone cannot pass a gate.

| Gate | Minimum conditions and evidence | Required approval | No-go / fallback |
|---|---|---|---|
| Leave shadow mode | Approved policy for the specific scope; source ownership/freshness and auditability; human-vs-candidate quality meets a pre-approved threshold; false positives and missed exceptions reviewed; operational workload and support demonstrated; critical risks resolved; incident and rollback drill passes; runbook/training ready. | Operations Head, Finance for payment rules, Scheduling/batch owner for capacity/schedule rules, Data/system owner for source/security/integration. | Continue read-only shadow mode; keep existing process; remediate and repeat comparison. |
| Start controlled pilot | Named limited cohort and support contacts; teacher communication and fallback ready; access approved; all unresolved rules explicitly excluded/held; monitoring and case ledger available; pilot stop conditions and owners signed; no writes required for the pilot unless separately approved. | Operations Head plus relevant control owners and teacher/educator liaison. | Do not enroll cohort; continue shadow run and readiness work. |
| Expand pilot | Prior cohort meets pre-approved quality/safety/workload thresholds; no unresolved critical incident; KPI denominators and data quality validated; teacher/Ops feedback actioned; duplicate prevention, rollback, fallback and handover tested; next cohort has support capacity. | Operations Head, Finance, Scheduling/batch owner, Data/system owner, as applicable. | Keep/narrow current cohort or pause; complete remediation and re-review. |
| Enable any automated write | Separate scope-specific business authorization; approved policy and deterministic tests; authoritative payment/identity/parent/capacity evidence; least-privilege service account; feature flag/kill switch; transactional idempotency; append-only audit; monitoring/alerting; retry and compensation procedure; rollback and restore drill; support coverage and legal/privacy review as required. | Business owner and Operations Head, plus Finance for payment, Scheduling/system owner for booking/schedule, Data/security owner. | No write enablement. Continue read-only or authorized human-controlled process. Automatic approval remains disabled absent explicit approval of each gate. |

## 9. Governance and ownership

| Role | Accountabilities |
|---|---|
| Operations Head | Executive accountable owner; approves cohort scope, operational readiness, stop/restart and escalation; accepts residual business risks; does not delegate payment or system authority outside policy. |
| Queue lead | Daily queue review, case assignment/backup, KPI quality checks, handover, operational incident coordination and feedback themes. |
| Operations generalists | Verify exact links and evidence, work approved cases, route exceptions, record authorized dispositions and maintain support continuity. They do not override Finance or parent-choice authority. |
| Finance | Owns authoritative payment source, settlement/amount/partial/refund rules, payment exception decisions and payment evidence. |
| Scheduling / batch owner | Owns live capacity source, seat-hold rule, parent choice handoff, scheduling constraints and protection of existing live classes. |
| Teachers | Submit accurate renewal forms and invoice references, correct their source submissions via approved process, respond to Operations clarification and provide workflow feedback. They do not verify settlement. |
| Data / system owner | Owns ingestion/source watermark, access/security, deterministic rule deployment, versioning, idempotency, audit storage, monitoring, incidents and rollback mechanics. |

### Change governance

- Maintain separate versions for business policy, deterministic code/rules, reason-code mapping, dashboard/KPI definitions, AI prompts/templates and operating procedure.
- Every proposed change records the change owner, reason, affected cohorts/cases, evidence, tests, approvers, effective date, rollback plan and post-change review.
- Payment, identity, eligibility, capacity and schedule rules require the corresponding business control owner. AI prompt changes cannot expand AI authority.
- Run changes in test/shadow context first. Compare output against an approved fixture or human-reviewed evidence; promote only after the relevant gate is signed.
- Review incidents, overrides, unmapped reason codes, source quality and KPI shifts on a defined governance cadence. Preserve prior rule versions and decision history for reproducibility.

## Unresolved business decisions

Before any controlled workflow moves beyond read-only observation, obtain named decisions for: authoritative settled amount/payment status and provider; partial/refund/reversal policy; meaning of approval and request statuses; duplicate-form and renewal-cycle rules; parent consent and batch choice; authoritative capacity freshness and seat holds; schedule/session-generation rules; deletion semantics; timezone, business calendar and SLA clocks; canonical reason-code/severity map; data access/retention/notification rules; and authority for booking, schedule and rollback actions. Until decided, affected cases remain human-reviewed or out of scope.

## Source alignment

- Phase 2 findings are sample observations only: 11 literal paid renewal invoices, 8/11 exact form links, three missing exact form links, eight Pending forms, and three requests without schedule rows. They do not establish live company performance or customer harm.
- Phase 3 KPI/SLA values are proposed targets requiring owner approval. Dashboard and supplied CSVs cannot currently calculate reliable SLA attainment or aging; they lack a trustworthy snapshot/as-of timestamp and complete case event ledger.
- Hours saved are unavailable until manual handling baselines, comparable automated handling times and eligible-case volume are measured.
- Phase 4 policy is prototype-only with automatic approval and writes disabled. This plan does not alter that configuration or authorize an implementation.
- Phase 7 SOP is the operational proposal; the reason-code mapping, severity differences, owners and safety controls must be resolved/approved before a live queue uses them as policy.
