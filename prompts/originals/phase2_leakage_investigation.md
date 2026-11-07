
PHASE 2: BAMBINOS.LIVE — DATA-BACKED LEAKAGE INVESTIGATION

You are now acting as a Senior Data Analyst and AI Program Manager.

Phase 1 is complete. You have already inspected the official assessment PDF and five CSV datasets.

Your task is to investigate the actual operational problems in the renewal-to-class-scheduling pipeline.

IMPORTANT:
Do not start building the automation or Python reconciliation engine yet.
This phase is ONLY for data investigation, root-cause analysis and KPI calculation.

==================================================
1. READ EXISTING PROJECT DOCUMENTATION
==================================================

First read:

- AGENTS.md
- analysis/phase1_dataset_inventory.md
- analysis/phase1_business_process.md
- analysis/phase1_relationship_mapping.md
- documentation/phase1_explanation_for_student.md

Then inspect the original five CSVs again.

Use the exact column names discovered in Phase 1.

==================================================
2. INVESTIGATION A: INVOICE TO TEACHER FORM
==================================================

Compare:

invoices.id
with
faculty_form_unapproved.invoice_id

Investigate:

A. Paid invoices with no corresponding teacher form.

B. Teacher forms with no corresponding invoice.

C. Teacher forms referencing duplicate invoice IDs.

D. Invoice amount versus teacher-reported amount:
   invoices.net_amount
   versus
   faculty_form_unapproved.amount_paid

E. Student ID mismatches.

F. User ID mismatches.

G. Class ID mismatches.

H. Educator ID mismatches.

I. Payment status and renewal flag.

Pay special attention to:
- Invoice ID `<INVOICE_ID>`, which Phase 1 identified as unmatched.
- Repeated invoice references in teacher forms.
- Differences between payment status and teacher form approval status.

Do not automatically classify every mismatch as fraud or a confirmed failure.

==================================================
3. INVESTIGATION B: TEACHER FORM TO BOOKING REQUEST
==================================================

Compare:

faculty_form_unapproved.id
with
booking_requests.faculty_form_id

Investigate:

- Forms without booking requests.
- Booking requests without matching forms.
- Duplicate booking requests.
- Student ID mismatches.
- Invoice ID mismatches.
- Class and educator mismatches.
- Session count discrepancies.
- Differences in batch and scheduling preferences.
- Approval status versus booking request status.

Identify forms marked Pending, Approved or any other status.

Do not assume that a form marked Approved means that a class has been scheduled.

==================================================
4. INVESTIGATION C: BOOKING REQUEST TO SCHEDULE
==================================================

Compare:

booking_requests.id
with
class_schedule_bookings.bookingrequest_id

Investigate:

- Booking requests without schedule entries.
- Schedule entries without valid booking requests.
- Multiple schedule entries per booking request.
- Duplicate class schedules.
- Student ID mismatches.
- Invoice ID mismatches.
- Batch and educator mismatches.
- Cancelled schedule entries.
- Requests marked Completed but lacking schedule records.
- Requests marked Failed_Batch_Full.
- Requests awaiting parent batch selection.
- Requests pending batch allocation.

IMPORTANT:

Multiple schedule rows for one booking request are not automatically duplicates.

Check the meaning of:
- class_date
- start_time
- end_time
- classschedule_id
- is_cancelled

Do not classify a request as unscheduled simply because it has more than one or fewer than a fixed number of schedule rows. The expected number of sessions must first be established.

==================================================
5. INVESTIGATION D: REFERENCE DATA VALIDATION
==================================================

Use:

reference_active_batches_and_students.csv

Validate:

- Student IDs.
- User IDs.
- Current batch IDs.
- Class IDs.
- Educator IDs.
- Standard fee for 24 sessions.
- Batch days and time.
- Active student count.
- Maximum batch size.

Calculate remaining seats as:

max_batch_size - active_students_count

Only where the capacity snapshot is valid and the values are reliable.

Investigate:
- Students missing from reference data.
- Batch mismatches.
- Class and teacher mismatches.
- Batches that appear full.
- Whether the requested batch matches the student's current batch.

IMPORTANT:

The reference file has no stated snapshot timestamp.

Clearly state that capacity and availability findings are provisional until snapshot freshness and seat-hold rules are confirmed.

Do not assume that a full batch in the reference file proves that a booking request failed because of capacity.

==================================================
6. INVESTIGATION E: TIME AND PROCESSING DELAYS
==================================================

Use available timestamp columns.

Calculate where possible:

1. Payment to teacher form creation:
   invoices.paid_at
   to faculty_form_unapproved.created_at

2. Form creation to approval:
   faculty_form_unapproved.created_at
   to faculty_form_unapproved.approved_at

3. Form creation to booking request:
   faculty_form_unapproved.created_at
   to booking_requests.created_at

4. Booking request to schedule creation:
   booking_requests.created_at
   to class_schedule_bookings.created_at

5. Payment to first schedule creation:
   invoices.paid_at
   to earliest valid class_schedule_bookings.created_at

Report:
- Time in hours.
- Median.
- Minimum.
- Maximum.
- P90 only where sample size makes it meaningful.

Separate missing timestamps from zero-hour delays.

Do not confuse class_date with schedule creation time.

Use timestamps only after documenting their timezone and event meaning limitations.

==================================================
7. INVESTIGATION F: OPERATIONAL KPIs
==================================================

Calculate the following metrics wherever supported:

1. Orphaned Invoice Rate.

Formula:
Eligible paid renewal invoices without matching forms
divided by total eligible paid renewal invoices
multiplied by 100.

2. Invoice-to-Form Match Rate.

3. Duplicate Invoice Reference Rate.

4. Payment Amount Mismatch Rate.

5. Form-to-Booking Conversion Rate.

6. Pending Teacher Form Rate.

7. Approved but Unscheduled Request Rate.

8. Failed Batch Allocation Rate.

9. Payment-to-Schedule Turnaround Time.

10. Overall Exception Rate.

For every KPI show:

- Definition.
- Formula.
- Numerator.
- Denominator.
- Actual value.
- Dataset used.
- Data limitations.

Use the exact payment eligibility criteria supported by the data.

Do not silently assume all invoice rows represent successful payments.

Where a denominator is zero or a metric is not measurable, report N/A.

==================================================
8. INVESTIGATION G: ROOT CAUSE ANALYSIS
==================================================

Group actual findings into:

- Data quality problems.
- Human dependency problems.
- Payment reconciliation problems.
- Approval delays.
- Scheduling problems.
- Batch capacity problems.
- Process visibility problems.

For each finding provide:

1. What happened?
2. Which record IDs demonstrate it?
3. Why does it matter?
4. Is it a confirmed issue, possible issue or unknown?
5. What business rule needs confirmation?
6. What intervention would solve it?

Rank findings by:
- Business impact.
- Risk.
- Frequency in this sample.
- Ease of resolution.

Do not confuse frequency in this small sample with company-wide frequency.

==================================================
9. CREATE THE FOLLOWING OUTPUT FILES
==================================================

Create:

analysis/phase2_leakage_audit.md

Include:
- Executive summary.
- Actual findings.
- Stage-wise leakage analysis.
- Evidence using record IDs.
- Root-cause analysis.
- Severity ranking.
- Data limitations.

Create:

analysis/phase2_kpi_results.csv

Include all measurable KPIs, formulas, numerators, denominators and results.

Create:

analysis/phase2_exception_analysis.csv

Include:
- Source record ID.
- Related invoice ID.
- Student ID.
- Exception category.
- Reason code.
- Evidence.
- Severity.
- Recommended owner.
- Recommended action.

Create:

analysis/phase2_root_causes.md

Explain the underlying operational problems and proposed interventions.

Create:

documentation/phase2_explanation_for_student.md

Explain everything in simple English.

Include:
- What we investigated.
- How records were compared.
- What each KPI means.
- Actual problems discovered.
- Examples from the datasets.
- What we learned.
- What remains uncertain.

==================================================
10. IMPORTANT QUALITY RULES
==================================================

- Never fabricate results.
- Never invent missing records.
- Never assume null deleted_at means active without documenting the assumption.
- Never treat every unmatched record as an orphaned invoice.
- Never count multiple class schedule entries for one request as duplicate bookings automatically.
- Never approve an unpaid or ambiguous record.
- Never assume standard fee is the actual paid amount without confirmation.
- Do not modify original CSV files.
- Do not modify Phase 1 documents.
- Keep all analysis reproducible.
- Use actual record IDs as evidence.
- Clearly distinguish actual findings from proposed business rules.
- Do not build automation in this phase.

==================================================
11. FINAL RESPONSE
==================================================

When finished, report:

1. Five most important findings.
2. Actual leakage numbers.
3. Which students or records need investigation.
4. Which business rules remain unclear.
5. Which files were created.
6. Whether the data is sufficient to design Phase 3.

STOP AFTER PHASE 2.

Wait for the user to review the results before continuing.
