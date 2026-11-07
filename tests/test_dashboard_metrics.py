from pathlib import Path

from dashboard import metrics as dashboard_metrics
from dashboard.metrics import (
    build_action_queue,
    build_funnel,
    compute_kpis,
    group_exceptions,
    load_dashboard_data,
    reconciliation_snapshot_matches,
)


ROOT = Path(__file__).resolve().parents[1]


def dashboard_data():
    return load_dashboard_data(ROOT / "examples" / "synthetic_data", ROOT / "results" / "synthetic_demo")


def test_dashboard_kpis_match_synthetic_demo_snapshot():
    metrics = compute_kpis(dashboard_data())
    assert metrics == {
        "paid_renewal_invoices": 11,
        "paid_renewals_without_exact_form": 3,
        "pending_teacher_forms": 8,
        "approved_forms_without_booking_request": 0,
        "requests_awaiting_batch_allocation": 1,
        "failed_batch_allocation_requests": 1,
        "requests_without_schedule": 3,
        "hours_saved": "Not yet measurable",
    }


def test_funnel_shows_raw_rows_and_link_context():
    funnel = build_funnel(dashboard_data())
    assert funnel.records.tolist() == [13, 12, 4, 2]
    assert "8 of 11" in funnel.loc[funnel.stage == "Teacher forms", "context"].iloc[0]
    assert "class occurrence" in funnel.loc[funnel.stage == "Class schedule rows", "context"].iloc[0]


def test_exception_summary_preserves_reason_codes_and_counts():
    data = dashboard_data()
    summary = group_exceptions(data["exceptions"])
    counts = summary.set_index("reason_code")["count"].to_dict()
    assert len(data["exceptions"]) > 0
    assert counts["FORM_PENDING"] == 8
    assert counts["REQUEST_WITHOUT_SCHEDULE"] == 3
    assert counts["PAID_RENEWAL_NO_EXACT_FORM"] == 3
    assert "PAYMENT_FAILED" in counts
    assert "FORM_INVOICE_ID_NOT_FOUND" in counts


def test_action_queue_is_enriched_by_exact_ids_and_excludes_contact_fields():
    queue = build_action_queue(dashboard_data())
    assert len(queue) == len(dashboard_data()["exceptions"])
    request_case = queue[queue.booking_request_id.astype(str).str.contains("SYN-REQ-002", regex=False)].iloc[0]
    assert request_case.current_stage == "Booking request"
    assert "Pending_Batch_Allocation" in request_case.status
    assert "No schedule row in extract" in request_case.status
    assert "student_id" in queue.columns
    forbidden = {"parent_name", "student_name", "mobile", "parent_mobile", "email", "remarks"}
    assert forbidden.isdisjoint(queue.columns)


def test_reconciliation_outputs_match_current_source_snapshot():
    assert reconciliation_snapshot_matches(dashboard_data(), ROOT / "examples" / "synthetic_data")


def test_reconciliation_snapshot_mismatch_is_detected(monkeypatch):
    data = dashboard_data()
    monkeypatch.setattr(dashboard_metrics, "input_hashes", lambda _data_dir: {"1_invoices.csv": "stale"})
    assert not reconciliation_snapshot_matches(data, ROOT / "examples" / "synthetic_data")

