import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from decision_engine import _auto_gates_pass, evaluate_case
from reconciliation import build_cases, evaluate_cases, run_reconciliation
from validators import InputValidationError, load_datasets


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def demo_data():
    return load_datasets(ROOT / "examples" / "synthetic_data")


@pytest.fixture(scope="module")
def demo_cases(demo_data):
    policy = json.loads((ROOT / "config" / "policy.json").read_text(encoding="utf-8"))
    return build_cases(demo_data, policy)


def find_invoice_case(cases, invoice_id):
    return next(c for c in cases if c["case_type"] == "invoice_renewal" and c["invoice_id"] == str(invoice_id))


def test_exact_invoice_form_match(demo_cases):
    case = find_invoice_case(demo_cases, "SYN-INV-001")
    assert [str(x["id"]) for x in case["forms"]] == ["SYN-FORM-001"]
    assert [str(x["id"]) for x in case["requests"]] == ["SYN-REQ-001"]
    assert {str(x["id"]) for x in case["schedules"]} == {"SYN-SCHEDULE-001", "SYN-SCHEDULE-002"}


def test_paid_invoice_without_form(demo_cases):
    case = find_invoice_case(demo_cases, "SYN-INV-004")
    decision = evaluate_case(case, json.loads((ROOT / "config/policy.json").read_text()))
    assert decision["decision_outcome"] == "NEEDS_HUMAN_REVIEW"
    assert any(x["reason_code"] == "PAID_RENEWAL_NO_EXACT_FORM" for x in decision["findings"])


def test_nonexistent_invoice_reference_is_blocked(demo_cases):
    case = next(c for c in demo_cases if c["case_type"] == "unmatched_form")
    decision = evaluate_case(case, json.loads((ROOT / "config/policy.json").read_text()))
    assert case["source_record_id"] == "SYN-FORM-ORPHAN"
    assert decision["invoice_id"] == "SYN-INV-404"
    assert decision["decision_outcome"] == "BLOCKED"
    assert decision["reason_code"] == "FORM_INVOICE_ID_NOT_FOUND"


def test_duplicate_invoice_references(demo_cases):
    case = find_invoice_case(demo_cases, "SYN-INV-008")
    decision = evaluate_case(case, json.loads((ROOT / "config/policy.json").read_text()))
    assert {str(f["id"]) for f in case["forms"]} == {"SYN-FORM-008-A", "SYN-FORM-008-B"}
    assert any(x["reason_code"] == "DUPLICATE_FORM_INVOICE_REFERENCE" for x in decision["findings"])
    assert decision["decision_outcome"] == "NEEDS_HUMAN_REVIEW"


def test_partially_paid_invoice_is_never_auto_approved(demo_cases):
    case = find_invoice_case(demo_cases, "SYN-INV-009")
    enabled_policy = json.loads((ROOT / "config/policy.json").read_text())
    enabled_policy["auto_approval_enabled"] = True
    decision = evaluate_case(case, enabled_policy)
    assert decision["decision_outcome"] == "NEEDS_HUMAN_REVIEW"
    assert {x["reason_code"] for x in decision["findings"]} >= {
        "PAYMENT_PARTIAL_POLICY_REVIEW", "PAYMENT_AMOUNT_CONFLICT"
    }


def test_failed_payment_is_blocked(demo_cases):
    case = find_invoice_case(demo_cases, "SYN-INV-013")
    decision = evaluate_case(case, json.loads((ROOT / "config/policy.json").read_text()))
    assert decision["decision_outcome"] == "BLOCKED"
    assert decision["reason_code"] == "PAYMENT_FAILED"


def test_amount_mismatch_detected(demo_cases):
    case = find_invoice_case(demo_cases, "SYN-INV-009")
    decision = evaluate_case(case, json.loads((ROOT / "config/policy.json").read_text()))
    assert any(x["reason_code"] == "PAYMENT_AMOUNT_CONFLICT" for x in decision["findings"])


def test_approved_form_without_request_is_flagged():
    invoice = {"id": 70001, "student_id": 7001, "user_id": 701, "class_id": 70,
               "educator_id": 71, "net_amount": 100.0, "payment_status": "Paid",
               "is_renewal": "Yes"}
    form = {"id": 80001, "invoice_id": 70001, "student_id": 7001, "user_id": 701,
            "class_id": 70, "educator_id": 71, "amount_paid": 100.0,
            "approval_status": "Approved", "continue_same_batch": "Yes",
            "current_classbatch_id": 9001}
    case = {"case_type": "invoice_renewal", "invoice_id": "70001", "invoice": invoice,
            "forms": [form], "requests": [], "schedules": [], "reference_rows": []}
    policy = json.loads((ROOT / "config/policy.json").read_text())
    outputs = evaluate_cases([case], policy, {"synthetic_test_fixture": "test-only"})
    assert any(x["reason_code"] == "APPROVED_FORM_NO_REQUEST" for x in outputs["exceptions"].to_dict("records"))
    assert outputs["stage_readiness"].iloc[0].booking_request_readiness_status == "NOT_READY"
    assert outputs["stage_readiness"].iloc[0].scheduling_readiness_status == "NOT_READY"


def test_full_batch_with_stale_reference_is_review_not_block(demo_cases):
    case = find_invoice_case(demo_cases, "SYN-INV-005")
    decision = evaluate_case(case, json.loads((ROOT / "config/policy.json").read_text()))
    assert any(x["reason_code"] == "BATCH_CAPACITY_UNCONFIRMED" for x in decision["findings"])
    assert decision["decision_outcome"] == "NEEDS_HUMAN_REVIEW"


def test_parent_batch_selection_pending(demo_cases):
    case = find_invoice_case(demo_cases, "SYN-INV-007")
    decision = evaluate_case(case, json.loads((ROOT / "config/policy.json").read_text()))
    assert any(x["reason_code"] == "PARENT_BATCH_SELECTION_PENDING" for x in decision["findings"])


def test_request_without_schedule_is_not_called_failure(demo_cases):
    case = find_invoice_case(demo_cases, "SYN-INV-002")
    decision = evaluate_case(case, json.loads((ROOT / "config/policy.json").read_text()))
    codes = {x["reason_code"] for x in decision["findings"]}
    assert "REQUEST_WITHOUT_SCHEDULE" in codes
    assert "REQUEST_PENDING_BATCH_ALLOCATION" in codes
    assert decision["decision_outcome"] == "NEEDS_HUMAN_REVIEW"


def test_multiple_valid_schedule_rows_are_not_duplicates(demo_cases):
    case = find_invoice_case(demo_cases, "SYN-INV-001")
    decision = evaluate_case(case, json.loads((ROOT / "config/policy.json").read_text()))
    codes = {x["reason_code"] for x in decision["findings"]}
    assert "MULTIPLE_VALID_SCHEDULE_ROWS" in codes
    assert "SCHEDULE_OCCURRENCE_CONFLICT" not in codes


def synthetic_auto_approval_case(approval_status="Approved", include_status=True):
    invoice = {"id": 10, "student_id": 20, "user_id": 30, "class_id": 40,
               "educator_id": 50, "net_amount": 100.0, "payment_status": "Paid",
               "is_renewal": "Yes", "gateway_verified": True, "currency": "INR",
               "gateway_settled_amount": 100.0, "gateway_settled_currency": "INR",
               "payment_evidence_id": "PAY-TEST-001",
               "payment_evidence_source": "synthetic_gateway_fixture"}
    form = {"id": 11, "invoice_id": 10, "student_id": 20, "user_id": 30,
            "class_id": 40, "educator_id": 50, "amount_paid": 100.0,
            "continue_same_batch": "Yes",
            "current_classbatch_id": 60, "parent_batch_choice_confirmed": True,
            "parent_choice_evidence_id": "CHOICE-TEST-001", "preferred_days": "Mon,Wed",
            "preferred_time_slot": "16:00:00", "sessions_purchased": 1}
    if include_status:
        form["approval_status"] = approval_status
    ref = {"student_id": 20, "user_id": 30, "class_id": 40, "educator_id": 50,
           "current_classbatch_id": 60, "student_active": True}
    case = {"case_type": "invoice_renewal", "invoice_id": "10", "invoice": invoice,
            "forms": [form], "requests": [], "schedules": [], "reference_rows": [ref],
            "capacity_confirmed": True, "capacity_available": True}
    policy = json.loads((ROOT / "config/policy.json").read_text())
    policy.update({"auto_approval_enabled": True, "reference_capacity_authoritative": True,
                   "payment": {**policy["payment"], "amount_rule_status": "APPROVED",
                               "allowed_evidence_sources": ["synthetic_gateway_fixture"]},
                   "stage_readiness": {
                       "booking_request": {"parent_choice_evidence_id_field": "parent_choice_evidence_id"},
                       "scheduling": {"schedule_ready_request_statuses": ["READY_FOR_SCHEDULING"],
                                      "required_schedule_fields": ["class_id", "educator_id", "classbatch_id",
                                                                    "class_date", "start_time", "end_time", "timezone"]},
                   }})
    return case, policy


def synthetic_stage_frames(requests=True, schedules=None, invoice_changes=None, form_changes=None,
                           request_changes=None, reference_changes=None, schedule_parameters=None):
    case, _ = synthetic_auto_approval_case()
    case["invoice"].update(invoice_changes or {})
    case["forms"][0].update(form_changes or {})
    parameter = {"class_id": 40, "educator_id": 50, "classbatch_id": 60,
                 "class_date": "2026-12-01", "start_time": "16:00:00",
                 "end_time": "16:30:00", "timezone": "Asia/Kolkata"}
    request = {"id": 12, "faculty_form_id": 11, "invoice_id": 10, "student_id": 20,
               "user_id": 30, "class_id": 40, "educator_id": 50, "classbatch_id": 60,
               "sessions_count": 1, "continue_same_batch": "Yes", "preferred_days": "Mon,Wed",
               "preferred_time": "16:00:00", "request_status": "READY_FOR_SCHEDULING",
               "batch_allocated": "Yes", "capacity_confirmed": True, "capacity_available": True,
               "capacity_evidence_id": "CAP-TEST-001", "seat_hold_id": "HOLD-TEST-001",
               "schedule_parameters_verified": True,
               "schedule_parameters_evidence_id": "CAL-TEST-001",
               "schedule_parameters_json": json.dumps(schedule_parameters if schedule_parameters is not None else [parameter])}
    request.update(request_changes or {})
    ref = {"student_id": 20, "user_id": 30, "class_id": 40, "educator_id": 50,
           "current_classbatch_id": 60, "student_active": True,
           "active_students_count": 2, "max_batch_size": 5,
           "batch_days": "Mon,Wed", "batch_start_time": "16:00:00"}
    ref.update(reference_changes or {})
    schedule_rows = schedules or []
    frames = {
        "invoices": pd.DataFrame([case["invoice"]]),
        "forms": pd.DataFrame(case["forms"]),
        "requests": pd.DataFrame([request] if requests else [], columns=list(request)),
        "schedules": pd.DataFrame(schedule_rows, columns=[
            "id", "bookingrequest_id", "invoice_id", "classschedule_id", "classbatch_id",
            "class_id", "student_id", "user_id", "educator_id", "class_date", "start_time",
            "end_time", "timezone", "is_cancelled",
        ]),
        "reference": pd.DataFrame([ref]),
    }
    policy = json.loads((ROOT / "config/policy.json").read_text())
    policy.update({"auto_approval_enabled": True, "reference_capacity_authoritative": True,
                   "payment": {**policy["payment"], "amount_rule_status": "APPROVED",
                               "allowed_evidence_sources": ["synthetic_gateway_fixture"]},
                   "stage_readiness": {
                       "booking_request": {"parent_choice_evidence_id_field": "parent_choice_evidence_id"},
                       "scheduling": {"schedule_ready_request_statuses": ["READY_FOR_SCHEDULING"],
                                      "required_schedule_fields": ["class_id", "educator_id", "classbatch_id",
                                                                    "class_date", "start_time", "end_time", "timezone"]},
                   }})
    return frames, policy


def evaluate_synthetic(requests=True, schedules=None, invoice_changes=None, form_changes=None,
                       request_changes=None, reference_changes=None, schedule_parameters=None):
    frames, policy = synthetic_stage_frames(requests, schedules, invoice_changes, form_changes,
                                            request_changes, reference_changes, schedule_parameters)
    cases = build_cases(frames, policy)
    outputs = evaluate_cases(cases, policy, {"synthetic_test_fixture": "test-only"})
    return outputs, cases, policy


def test_pending_form_never_auto_approves_with_other_gates_satisfied():
    case, policy = synthetic_auto_approval_case("Pending")
    assert _auto_gates_pass(case, [], policy) is False
    decision = evaluate_case(case, policy)
    assert decision["decision_outcome"] == "NEEDS_HUMAN_REVIEW"
    assert decision["automatic_decision"] is False
    finding = next(x for x in decision["findings"] if x["reason_code"] == "FORM_PENDING")
    assert finding["severity"] != "INFO"
    assert finding["owner"] == "Operations"


@pytest.mark.parametrize(("status", "include_status", "expected_code"), [
    (None, False, "FORM_APPROVAL_STATUS_MISSING"),
    ("   ", True, "FORM_APPROVAL_STATUS_MISSING"),
    ("Rejected", True, "FORM_REJECTED"),
    ("NeedsOpsReview", True, "FORM_APPROVAL_STATUS_UNKNOWN"),
])
def test_non_approved_or_unrecognized_form_status_never_auto_approves(status, include_status, expected_code):
    case, policy = synthetic_auto_approval_case(status, include_status=include_status)
    assert _auto_gates_pass(case, [], policy) is False
    decision = evaluate_case(case, policy)
    assert decision["decision_outcome"] == "NEEDS_HUMAN_REVIEW"
    assert decision["automatic_decision"] is False
    assert expected_code in {x["reason_code"] for x in decision["findings"]}


def test_approved_form_without_request_passes_eligibility_but_not_scheduling():
    outputs, _, _ = evaluate_synthetic(requests=False)
    assert outputs["results"].iloc[0].decision_outcome == "AUTO_APPROVED"
    row = outputs["stage_readiness"].iloc[0]
    assert row.renewal_eligibility_status == "AUTO_APPROVED"
    assert row.booking_request_readiness_status == "READY_TO_CREATE_REQUEST"
    assert row.scheduling_readiness_status == "WAITING_ON_REQUEST"
    assert "APPROVED_FORM_NO_REQUEST" in row.exclusion_reason_codes
    assert outputs["scheduling_ready"].empty
    assert "APPROVED_FORM_NO_REQUEST" in set(outputs["exceptions"].reason_code)


def test_fully_evidenced_synthetic_case_passes_all_stages_and_produces_ready_row():
    outputs, _, _ = evaluate_synthetic()
    stage = outputs["stage_readiness"].iloc[0]
    assert outputs["results"].iloc[0].decision_outcome == "AUTO_APPROVED"
    assert stage.booking_request_readiness_status == "REQUEST_EXISTS_VALID"
    assert stage.scheduling_readiness_status == "READY_FOR_CLASS_SCHEDULE_BOOKINGS"
    assert len(outputs["scheduling_ready"]) == 1
    assert outputs["scheduling_ready"].iloc[0].booking_request_id == "12"


def assert_stages(outputs, eligibility, booking, scheduling, ready=False):
    row = outputs["stage_readiness"].iloc[0]
    assert (row.renewal_eligibility_status, row.booking_request_readiness_status,
            row.scheduling_readiness_status) == (eligibility, booking, scheduling)
    assert bool(len(outputs["scheduling_ready"])) is ready


def test_missing_active_student_evidence_fails_all_later_stages():
    outputs, _, _ = evaluate_synthetic(reference_changes={"student_active": None})
    assert_stages(outputs, "NEEDS_HUMAN_REVIEW", "NOT_READY", "NOT_READY")
    assert "STUDENT_ACTIVE_STATUS_CONFLICT" in outputs["stage_readiness"].iloc[0].exclusion_reason_codes


def test_non_authoritative_capacity_fails_scheduling_only():
    frames, policy = synthetic_stage_frames()
    policy["reference_capacity_authoritative"] = False
    outputs = evaluate_cases(build_cases(frames, policy), policy, {"synthetic_test_fixture": "test-only"})
    assert_stages(outputs, "AUTO_APPROVED", "REQUEST_EXISTS_VALID", "WAITING_ON_CAPACITY")
    assert "CAPACITY_NOT_AUTHORITATIVE" in outputs["stage_readiness"].iloc[0].exclusion_reason_codes


def test_missing_seat_hold_fails_scheduling_only():
    outputs, _, _ = evaluate_synthetic(request_changes={"seat_hold_id": None})
    assert_stages(outputs, "AUTO_APPROVED", "REQUEST_EXISTS_VALID", "WAITING_ON_CAPACITY")
    assert "SEAT_HOLD_MISSING" in outputs["stage_readiness"].iloc[0].exclusion_reason_codes


@pytest.mark.parametrize(("invoice_changes", "expected_reason"), [
    ({"payment_evidence_id": None}, "PAYMENT_EVIDENCE_REFERENCE_MISSING"),
    ({"payment_evidence_id": "10"}, "PAYMENT_EVIDENCE_REFERENCE_CONFLICT"),
    ({"payment_evidence_source": None}, "PAYMENT_EVIDENCE_SOURCE_MISSING"),
    ({"payment_evidence_source": "unconfigured_source"}, "PAYMENT_EVIDENCE_SOURCE_UNTRUSTED"),
])
def test_payment_evidence_reference_is_required_and_trusted(invoice_changes, expected_reason):
    outputs, _, _ = evaluate_synthetic(invoice_changes=invoice_changes)
    assert_stages(outputs, "AUTO_APPROVED", "REQUEST_EXISTS_VALID", "NEEDS_HUMAN_REVIEW")
    assert expected_reason in outputs["stage_readiness"].iloc[0].exclusion_reason_codes


@pytest.mark.parametrize(("parameter_change", "expected_reason"), [
    ({"timezone": "Not/A_Real_Zone"}, "SCHEDULE_TIMEZONE_INVALID"),
    ({"timezone": None}, "SCHEDULE_TIMEZONE_MISSING"),
    ({"end_time": "16:00:00"}, "SCHEDULE_END_NOT_AFTER_START"),
    ({"start_time": "16:45:00", "end_time": "16:30:00"}, "SCHEDULE_END_NOT_AFTER_START"),
    ({"classbatch_id": None}, "SCHEDULE_FIELD_MISSING"),
    ({"class_date": "2026-02-30"}, "SCHEDULE_DATE_INVALID"),
])
def test_invalid_schedule_parameters_fail_scheduling_only(parameter_change, expected_reason):
    parameter = {"class_id": 40, "educator_id": 50, "classbatch_id": 60,
                 "class_date": "2026-12-01", "start_time": "16:00:00",
                 "end_time": "16:30:00", "timezone": "Asia/Kolkata"}
    parameter.update(parameter_change)
    outputs, _, _ = evaluate_synthetic(schedule_parameters=[parameter])
    assert_stages(outputs, "AUTO_APPROVED", "REQUEST_EXISTS_VALID", "NEEDS_HUMAN_REVIEW")
    assert expected_reason in outputs["stage_readiness"].iloc[0].exclusion_reason_codes


@pytest.mark.parametrize(("parameter", "expected_reason"), [
    ({"class_id": 40, "educator_id": 50, "classbatch_id": 60, "class_date": "2026-11-01",
      "start_time": "01:30:00", "end_time": "02:30:00", "timezone": "America/New_York"},
     "SCHEDULE_LOCAL_TIME_AMBIGUOUS"),
    ({"class_id": 40, "educator_id": 50, "classbatch_id": 60, "class_date": "2026-03-08",
      "start_time": "02:30:00", "end_time": "03:30:00", "timezone": "America/New_York"},
     "SCHEDULE_LOCAL_TIME_NONEXISTENT"),
])
def test_dst_ambiguous_or_nonexistent_local_times_fail_closed(parameter, expected_reason):
    outputs, _, _ = evaluate_synthetic(schedule_parameters=[parameter])
    assert_stages(outputs, "AUTO_APPROVED", "REQUEST_EXISTS_VALID", "NEEDS_HUMAN_REVIEW")
    assert expected_reason in outputs["stage_readiness"].iloc[0].exclusion_reason_codes


def test_missing_schedule_parameter_list_fails_scheduling_only():
    outputs, _, _ = evaluate_synthetic(schedule_parameters=[])
    assert_stages(outputs, "AUTO_APPROVED", "REQUEST_EXISTS_VALID", "NEEDS_HUMAN_REVIEW")
    assert "SCHEDULE_PARAMETERS_MISSING" in outputs["stage_readiness"].iloc[0].exclusion_reason_codes


def test_duplicate_schedule_occurrence_is_reviewed_and_never_emitted():
    schedule = {"id": 90, "bookingrequest_id": 12, "invoice_id": 10,
                "classschedule_id": 91, "classbatch_id": 60, "class_id": 40,
                "student_id": 20, "user_id": 30, "educator_id": 50,
                "class_date": "2026-12-01", "start_time": "16:00:00",
                "end_time": "16:30:00", "timezone": "Asia/Kolkata", "is_cancelled": "No"}
    duplicate = {**schedule, "id": 92, "classschedule_id": 93}
    outputs, _, _ = evaluate_synthetic(schedules=[schedule, duplicate])
    assert_stages(outputs, "AUTO_APPROVED", "REQUEST_EXISTS_VALID", "NEEDS_HUMAN_REVIEW")
    assert "SCHEDULE_OCCURRENCE_CONFLICT" in outputs["stage_readiness"].iloc[0].exclusion_reason_codes


def test_conflicting_schedule_occurrence_is_reviewed_and_never_emitted():
    schedule = {"id": 90, "bookingrequest_id": 12, "invoice_id": 10,
                "classschedule_id": 91, "classbatch_id": 60, "class_id": 40,
                "student_id": 20, "user_id": 30, "educator_id": 50,
                "class_date": "2026-12-01", "start_time": "16:00:00",
                "end_time": "16:45:00", "timezone": "Asia/Kolkata", "is_cancelled": "No"}
    outputs, _, _ = evaluate_synthetic(schedules=[schedule])
    assert_stages(outputs, "AUTO_APPROVED", "REQUEST_EXISTS_VALID", "NEEDS_HUMAN_REVIEW")
    assert "SCHEDULE_OCCURRENCE_CONFLICT" in outputs["stage_readiness"].iloc[0].exclusion_reason_codes


def test_distinct_schedule_occurrences_are_preserved_and_only_missing_one_is_emitted():
    parameters = [
        {"class_id": 40, "educator_id": 50, "classbatch_id": 60, "class_date": "2026-12-01",
         "start_time": "16:00:00", "end_time": "16:30:00", "timezone": "Asia/Kolkata"},
        {"class_id": 40, "educator_id": 50, "classbatch_id": 60, "class_date": "2026-12-08",
         "start_time": "16:00:00", "end_time": "16:30:00", "timezone": "Asia/Kolkata"},
    ]
    existing = {"id": 90, "bookingrequest_id": 12, "invoice_id": 10,
                "classschedule_id": 91, "classbatch_id": 60, "class_id": 40,
                "student_id": 20, "user_id": 30, "educator_id": 50,
                "class_date": "2026-12-01", "start_time": "16:00:00",
                "end_time": "16:30:00", "timezone": "Asia/Kolkata", "is_cancelled": "No"}
    outputs, _, _ = evaluate_synthetic(schedules=[existing], schedule_parameters=parameters)
    assert_stages(outputs, "AUTO_APPROVED", "REQUEST_EXISTS_VALID", "READY_FOR_CLASS_SCHEDULE_BOOKINGS", True)
    assert len(outputs["scheduling_ready"]) == 1
    assert outputs["scheduling_ready"].iloc[0].class_date == "2026-12-08"


def test_missing_gateway_evidence_has_precise_exclusion():
    outputs, _, _ = evaluate_synthetic(invoice_changes={"gateway_verified": None})
    row = outputs["stage_readiness"].iloc[0]
    statuses = json.loads(row.evidence_status_json)
    assert row.renewal_eligibility_status == "NEEDS_HUMAN_REVIEW"
    assert statuses["gateway_verification"] == "MISSING"
    assert "GATEWAY_VERIFICATION_MISSING" in row.exclusion_reason_codes
    assert outputs["scheduling_ready"].empty


def test_missing_parent_choice_prevents_scheduling_readiness():
    outputs, _, _ = evaluate_synthetic(form_changes={"parent_batch_choice_confirmed": None,
                                                    "parent_choice_evidence_id": None})
    row = outputs["stage_readiness"].iloc[0]
    assert row.renewal_eligibility_status == "AUTO_APPROVED"
    assert row.scheduling_readiness_status == "WAITING_ON_PARENT"
    assert "PARENT_CHOICE_EVIDENCE_MISSING" in row.exclusion_reason_codes
    assert outputs["scheduling_ready"].empty


@pytest.mark.parametrize(("request_changes", "expected_code"), [
    ({"capacity_confirmed": False}, "CAPACITY_EVIDENCE_MISSING"),
    ({"seat_hold_id": None}, "SEAT_HOLD_MISSING"),
])
def test_missing_capacity_or_seat_hold_prevents_scheduling(request_changes, expected_code):
    outputs, _, _ = evaluate_synthetic(request_changes=request_changes)
    row = outputs["stage_readiness"].iloc[0]
    assert row.renewal_eligibility_status == "AUTO_APPROVED"
    assert row.scheduling_readiness_status == "WAITING_ON_CAPACITY"
    assert expected_code in row.exclusion_reason_codes
    assert outputs["scheduling_ready"].empty


def test_existing_valid_request_is_accepted():
    outputs, _, _ = evaluate_synthetic()
    row = outputs["stage_readiness"].iloc[0]
    assert row.booking_request_readiness_status == "REQUEST_EXISTS_VALID"
    assert row.scheduling_readiness_status == "READY_FOR_CLASS_SCHEDULE_BOOKINGS"


def test_existing_valid_schedule_fulfillment_is_not_recreated():
    schedule = {"id": 90, "bookingrequest_id": 12, "invoice_id": 10,
                "classschedule_id": 91, "classbatch_id": 60, "class_id": 40,
                "student_id": 20, "user_id": 30, "educator_id": 50,
                "class_date": "2026-12-01", "start_time": "16:00:00",
                "end_time": "16:30:00", "timezone": "Asia/Kolkata", "is_cancelled": "No"}
    outputs, _, _ = evaluate_synthetic(schedules=[schedule])
    row = outputs["stage_readiness"].iloc[0]
    assert row.scheduling_readiness_status == "ALREADY_FULFILLED"
    assert outputs["scheduling_ready"].empty


def test_duplicate_requests_are_reviewed_and_excluded():
    frames, policy = synthetic_stage_frames()
    duplicate = frames["requests"].iloc[0].to_dict()
    duplicate["id"] = 13
    frames["requests"] = pd.concat([frames["requests"], pd.DataFrame([duplicate])], ignore_index=True)
    outputs = evaluate_cases(build_cases(frames, policy), policy, {"synthetic_test_fixture": "test-only"})
    assert outputs["stage_readiness"].iloc[0].booking_request_readiness_status == "NEEDS_HUMAN_REVIEW"
    assert outputs["scheduling_ready"].empty


def test_invoice_form_mismatch_remains_excluded():
    frames, policy = synthetic_stage_frames(form_changes={"invoice_id": 999})
    outputs = evaluate_cases(build_cases(frames, policy), policy, {"synthetic_test_fixture": "test-only"})
    assert not outputs["results"].decision_outcome.eq("AUTO_APPROVED").any()
    assert outputs["scheduling_ready"].empty


def test_unknown_approval_status_remains_under_review():
    outputs, _, _ = evaluate_synthetic(form_changes={"approval_status": "NeedsOpsReview"})
    assert outputs["results"].iloc[0].decision_outcome == "NEEDS_HUMAN_REVIEW"
    assert outputs["scheduling_ready"].empty


def test_default_policy_disables_auto_approval_and_excludes_demo_records(demo_cases):
    policy = json.loads((ROOT / "config/policy.json").read_text())
    assert policy["auto_approval_enabled"] is False
    assert policy["mode"] == "PROTOTYPE_ONLY"
    assert policy["output_policy"]["create_booking_records"] is False
    assert policy["output_policy"]["create_schedule_records"] is False
    assert policy["output_policy"]["send_notifications"] is False
    assert all(evaluate_case(case, policy)["decision_outcome"] != "AUTO_APPROVED" for case in demo_cases)


def test_default_policy_disables_auto_approval_and_demo_pending_forms_do_not_auto_approve(demo_cases):
    policy = json.loads((ROOT / "config/policy.json").read_text())
    assert policy["auto_approval_enabled"] is False
    enabled_policy = {**policy, "auto_approval_enabled": True, "reference_capacity_authoritative": True}
    pending_cases = [case for case in demo_cases if any(
        str(form.get("approval_status", "")).strip().casefold() == "pending" for form in case["forms"]
    )]
    assert pending_cases
    for case in pending_cases:
        decision = evaluate_case(case, enabled_policy)
        assert decision["decision_outcome"] != "AUTO_APPROVED"


def test_repeated_runs_have_stable_unique_decision_ids():
    input_dir = ROOT / "examples" / "synthetic_data"
    output_dir = ROOT / "results" / "test_runs"
    source_files = sorted(input_dir.glob("*.csv"))
    source_hashes_before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files}
    first = run_reconciliation(input_dir, output_dir, ROOT / "config/policy.json")
    first_ids = first["results"].decision_id.tolist()
    first_exception_ids = first["exceptions"].exception_id.tolist()
    second = run_reconciliation(input_dir, output_dir, ROOT / "config/policy.json")
    second_ids = second["results"].decision_id.tolist()
    second_exception_ids = second["exceptions"].exception_id.tolist()
    assert first_ids == second_ids
    assert first_exception_ids == second_exception_ids
    assert second["results"].decision_id.is_unique
    assert second["exceptions"].exception_id.is_unique
    assert len(pd.read_csv(output_dir / "reconciliation_results.csv")) == len(second["results"])
    assert len(pd.read_csv(output_dir / "audit_log.csv")) == len(second["audit"])
    assert len(pd.read_csv(output_dir / "exception_report.csv")) == len(second["exceptions"])
    assert len(pd.read_csv(output_dir / "stage_readiness_report.csv")) == len(second["stage_readiness"])
    assert len(pd.read_csv(output_dir / "scheduling_ready.csv")) == len(second["scheduling_ready"])
    assert list(pd.read_csv(output_dir / "scheduling_ready.csv").columns) == [
        "readiness_id", "case_id", "decision_id", "invoice_id", "teacher_form_id",
        "booking_request_id", "student_id", "user_id", "class_id", "educator_id",
        "classbatch_id", "schedule_instance_key", "class_date", "start_time", "end_time",
        "timezone", "payment_evidence_id", "parent_choice_evidence_id", "capacity_evidence_id",
        "seat_hold_id", "verified_settled_amount", "currency", "policy_version",
        "evaluated_at_utc", "input_snapshot_sha256",
    ]
    assert "renewal_eligibility_status" in pd.read_csv(output_dir / "stage_readiness_report.csv").columns
    assert list(first["results"].columns) == [
        "case_id", "decision_id", "case_type", "invoice_id", "form_ids", "booking_request_ids",
        "schedule_row_ids", "student_id", "decision_outcome", "reason_code", "explanation",
        "recommended_next_action", "responsible_owner", "evidence", "policy_version",
        "evaluated_at_utc", "automatic_decision", "requires_human_action", "prototype_only",
    ]
    source_hashes_after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files}
    assert source_hashes_after == source_hashes_before
    audit = pd.read_csv(output_dir / "audit_log.csv")
    required = {"invoice_id", "form_ids", "booking_request_ids", "schedule_row_ids",
                "evidence", "policy_version", "timestamp_utc", "decision_outcome",
                "reason_code", "input_file_sha256", "input_snapshot_sha256"}
    assert required <= set(audit.columns)
    assert audit.input_snapshot_sha256.nunique() == 1
    input_hashes = json.loads(audit.input_file_sha256.iloc[0])
    expected_files = {
        "1_invoices.csv", "2_faculty_form_unapproved.csv", "3_booking_requests.csv",
        "4_class_schedule_bookings.csv", "reference_active_batches_and_students.csv",
    }
    assert set(input_hashes) == expected_files
    snapshot = hashlib.sha256(json.dumps(input_hashes, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    assert set(audit.input_snapshot_sha256) == {snapshot}
    evidence = json.loads(audit.loc[audit.invoice_id.astype(str) == "SYN-INV-001", "evidence"].iloc[0])
    assert evidence["source_values"]["invoice"]["payment_status"] == "Paid"
    assert evidence["source_values"]["invoice"]["is_renewal"] == "Yes"
    assert evidence["source_values"]["invoice"]["class_id"] == "SYN-CLASS-001"
    assert evidence["source_values"]["forms"][0]["approval_status"] == "Approved"
    assert "amount_paid" in evidence["source_values"]["forms"][0]
    assert evidence["source_values"]["forms"][0]["continue_same_batch"] == "Yes"
    assert evidence["source_values"]["student_batch_reference"][0]["max_batch_size"] == 6
    assert "parent_name" not in json.dumps(evidence)


def test_missing_input_file_is_reported():
    with pytest.raises(InputValidationError, match="Missing input file"):
        load_datasets(ROOT / "directory-that-does-not-exist-for-test")

