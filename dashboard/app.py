"""Streamlit read-only Operations dashboard for renewal reconciliation."""

from __future__ import annotations

import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dashboard.metrics import (  # noqa: E402
    PROPOSED_SLAS,
    build_action_queue,
    build_funnel,
    compute_kpis,
    group_exceptions,
    load_dashboard_data,
    reconciliation_snapshot_matches,
)


st.set_page_config(page_title="Renewal Operations Dashboard", page_icon="📚", layout="wide")
st.markdown(
    """
    <style>
      .block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
      [data-testid="stMetric"] {
        background: #111827;
        border: 1px solid #475569;
        padding: 0.8rem 1rem;
        border-radius: 0.6rem;
      }
      [data-testid="stMetric"] [data-testid="stMetricLabel"],
      [data-testid="stMetric"] [data-testid="stMetricLabel"] *,
      [data-testid="stMetric"] [data-testid="stMetricValue"],
      [data-testid="stMetric"] [data-testid="stMetricValue"] *,
      [data-testid="stMetric"] [data-testid="stMetricDelta"],
      [data-testid="stMetric"] [data-testid="stMetricDelta"] * {
        color: #f8fafc !important;
        opacity: 1 !important;
      }
      .section-note {color: #cbd5e1; font-size: 0.92rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Renewal Operations Dashboard")
st.caption("Bambinos.live | Assessment prototype | Read-only CSV snapshot")

data_dir = PROJECT_ROOT / "data"
output_dir = PROJECT_ROOT / "outputs"
required_inputs = (
    "1_invoices.csv",
    "2_faculty_form_unapproved.csv",
    "3_booking_requests.csv",
    "4_class_schedule_bookings.csv",
    "reference_active_batches_and_students.csv",
)
using_demo_data = not all((data_dir / filename).is_file() for filename in required_inputs)
if using_demo_data:
    data_dir = PROJECT_ROOT / "examples" / "synthetic_data"
    output_dir = PROJECT_ROOT / "results" / "synthetic_demo"
    st.info("Showing the synthetic demonstration dataset. These invented rows are not assessment records.")

try:
    data = load_dashboard_data(data_dir, output_dir)
except (FileNotFoundError, ValueError, KeyError) as exc:
    st.error(f"Dashboard data could not be loaded: {exc}")
    st.stop()

snapshot_current = reconciliation_snapshot_matches(data, data_dir)
if snapshot_current:
    st.success("Reconciliation outputs match the current five-file input snapshot.")
else:
    st.warning(
        "The reconciliation outputs are missing or do not match the current input CSV hashes. "
        "Raw-file counts remain available, but decision and exception views may be stale. "
        "Refresh them with `python src/reconciliation.py` before acting on output-derived items."
    )

kpis = compute_kpis(data)
results = data["results"]
exceptions = data["exceptions"]

st.header("Executive KPI overview")
st.caption("Observed = directly counted source statuses/rows. Derived = exact-ID relationship calculation. No overdue label is inferred.")

cards = [
    ("Paid renewal invoices", kpis["paid_renewal_invoices"], "Observed source values: payment_status=Paid and is_renewal=Yes."),
    ("Paid renewals without exact form", kpis["paid_renewals_without_exact_form"], "Derived by exact invoices.id = form.invoice_id."),
    ("Pending teacher forms", kpis["pending_teacher_forms"], "Observed approval_status=Pending; age/SLA breach is not established."),
    ("Approved forms without request", kpis["approved_forms_without_booking_request"], "Derived by exact form.id = booking_requests.faculty_form_id."),
    ("Awaiting batch allocation", kpis["requests_awaiting_batch_allocation"], "Observed request_status=Pending_Batch_Allocation."),
    ("Failed batch allocation", kpis["failed_batch_allocation_requests"], "Observed request_status=Failed_Batch_Full; the reference capacity is not live proof."),
    ("Requests without schedule rows", kpis["requests_without_schedule"], "Derived by exact booking_requests.id = schedule.bookingrequest_id."),
    ("Hours saved through automation", kpis["hours_saved"], "Not yet measurable; manual and automated handling-time baselines are absent."),
]
for offset in range(0, len(cards), 4):
    columns = st.columns(4)
    for column, (label, value, help_text) in zip(columns, cards[offset:offset + 4]):
        column.metric(label, value, help=help_text)

st.markdown(
    "**Proposed calculation, not a measured value:**  \n"
    "`Hours saved = ((manual handling minutes - automated handling minutes) × eligible cases) / 60`"
)
st.caption("The supplied files contain no manual-handling baseline, automated handling duration, or production automation event count.")

st.header("Renewal workflow funnel")
funnel = build_funnel(data)
left, right = st.columns([1, 1.2])
with left:
    st.bar_chart(funnel.set_index("stage")[["records"]], horizontal=True)
with right:
    st.dataframe(funnel, hide_index=True, width="stretch")
st.info(
    "These are raw rows from one extract, not a single-cohort conversion funnel: entities differ by stage, "
    "and schedule rows represent class occurrences. Fewer rows at a later stage do not by themselves prove failure."
)

st.header("Exception monitoring")
if exceptions.empty:
    st.info("No reconciliation exception output is available.")
else:
    exception_summary = group_exceptions(exceptions)
    reason_order = exception_summary.reason_code.astype(str).tolist()
    reason_chart = (
        alt.Chart(exception_summary)
        .mark_bar(color="#38bdf8", cornerRadiusEnd=3)
        .encode(
            x=alt.X(
                "count:Q",
                title="Finding rows",
                axis=alt.Axis(labelColor="#cbd5e1", titleColor="#cbd5e1", gridColor="#334155", tickMinStep=1),
            ),
            y=alt.Y(
                "reason_code:N",
                title=None,
                sort=reason_order,
                axis=alt.Axis(labelColor="#f8fafc", labelFontSize=11, labelLimit=480, labelOverlap=False),
            ),
            tooltip=[
                alt.Tooltip("reason_code:N", title="Reason code"),
                alt.Tooltip("count:Q", title="Finding rows"),
                alt.Tooltip("severity:N", title="Severity"),
                alt.Tooltip("responsible_team:N", title="Responsible team"),
            ],
        )
        .properties(height=max(320, 28 * len(exception_summary)))
        .configure_view(stroke=None)
        .configure_axis(domain=False, ticks=False)
    )
    st.altair_chart(reason_chart, width="stretch")
    st.dataframe(exception_summary, hide_index=True, width="stretch")
    st.caption("Counts are finding rows, not failed renewal cases. Reason codes are kept separate as recorded in the reconciliation output.")

st.header("Actionable work queue")
queue = build_action_queue(data)
if queue.empty:
    st.info("No exception rows are available for the action queue.")
else:
    st.caption("Student IDs are included only as internal lookup identifiers. Names, parent contact details, and free-text remarks are not loaded or displayed.")
    filter_cols = st.columns([2, 1, 1, 1])
    search = filter_cols[0].text_input("Search IDs, status, reason, owner or action", key="queue_search")
    reasons = sorted(queue.exception_reason.dropna().astype(str).unique())
    selected_reasons = filter_cols[1].multiselect("Reason code", reasons, default=reasons)
    severities = sorted(exceptions.severity.dropna().astype(str).unique())
    selected_severities = filter_cols[2].multiselect("Severity", severities, default=severities)
    owners = sorted(queue.suggested_owner.dropna().astype(str).unique())
    selected_owners = filter_cols[3].multiselect("Owner", owners, default=owners)

    filtered = queue[
        queue.exception_reason.isin(selected_reasons)
        & queue.severity.isin(selected_severities)
        & queue.suggested_owner.isin(selected_owners)
    ].copy()
    if search.strip():
        searchable = filtered.astype(str).agg(" ".join, axis=1).str.casefold()
        filtered = filtered[searchable.str.contains(search.strip().casefold(), regex=False)]
    queue_column_config = {
        "invoice_id": st.column_config.TextColumn("Invoice", width="small"),
        "teacher_form_id": st.column_config.TextColumn("Form ID", width="small"),
        "booking_request_id": st.column_config.TextColumn("Request ID", width="small"),
        "student_id": st.column_config.TextColumn("Student ID", width="small"),
        "current_stage": st.column_config.TextColumn("Stage", width="small"),
        "status": st.column_config.TextColumn("Source status", width="medium"),
        "exception_reason": st.column_config.TextColumn("Reason code", width="medium"),
        "severity": st.column_config.TextColumn("Severity", width="small"),
        "suggested_owner": st.column_config.TextColumn("Owner", width="medium"),
        "recommended_next_action": st.column_config.TextColumn("Next action", width="large"),
    }
    st.dataframe(filtered, hide_index=True, width="stretch", height=460, column_config=queue_column_config)
    st.caption("Scroll horizontally in the table to review source status and the full next action.")
    st.caption(f"Showing {len(filtered)} of {len(queue)} exception finding rows. Filters do not change source records.")

if not snapshot_current:
    st.caption("Decision outcomes and exception findings below are retained for context but should not be actioned until the output snapshot is refreshed.")

st.header("SLA and aging")
st.warning(
    "Targets below are proposals from Phase 3 and require business validation. This dashboard does not calculate age, "
    "overdue status, or SLA attainment from the supplied snapshot."
)
st.dataframe(pd.DataFrame(PROPOSED_SLAS), hide_index=True, width="stretch")
st.markdown(
    "To calculate age safely, capture a trusted extract/as-of timestamp and timezone, then define each clock's "
    "start event, stop event, business calendar, pause rules, and approved SLA. Existing event timestamps alone "
    "do not establish how old a record was when this snapshot was taken."
)

st.header("Operational insights")
review_count = int(results.decision_outcome.eq("NEEDS_HUMAN_REVIEW").sum()) if not results.empty else None
blocked_count = int(results.decision_outcome.eq("BLOCKED").sum()) if not results.empty else None
if review_count is None:
    st.info("Reconciliation decision outcomes are unavailable.")
else:
    one, two, three = st.columns(3)
    one.metric("Cases needing human review", review_count)
    two.metric("Blocked cases", blocked_count)
    three.metric("Exception finding rows", len(exceptions))

if not exceptions.empty and not exception_summary.empty:
    top = exception_summary.iloc[0]
    st.markdown(
        f"- Most frequent recorded reason: **{top.reason_code}** ({int(top['count'])} finding rows).\n"
        f"- Exact form-link gaps: **{kpis['paid_renewals_without_exact_form']}** paid renewal invoice IDs.\n"
        f"- Pending teacher forms: **{kpis['pending_teacher_forms']}**; current age and overdue status are unavailable."
    )

with st.expander("Data limitations and assumptions"):
    st.markdown(
        "- The extract is a small point-in-time sample, not company-wide performance.\n"
        "- `Paid` and `is_renewal=Yes` are literal source-value filters; payment is not verified with a gateway.\n"
        "- Links use exact IDs only; student identity is not a fallback join key.\n"
        "- `amount_paid` versus invoice `net_amount`, partial-payment eligibility, status transitions, and deletion semantics need business confirmation.\n"
        "- The reference capacity file has no snapshot timestamp and cannot prove live availability.\n"
        "- Schedule rows are class occurrences; expected sessions per renewal are undefined.\n"
        "- No payments, bookings, schedules, source data, or messages are changed by this dashboard."
    )

st.caption("Assessment prototype · local CSV files only · read-only · not production-ready")

