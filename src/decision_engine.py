"""Explainable, policy-driven decisions; this module never writes to source tables."""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, time, timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import pandas as pd

from validators import is_present, normalize_identifier, numbers_match


OUTCOMES = {"AUTO_APPROVED", "NEEDS_HUMAN_REVIEW", "BLOCKED"}

REASON_ORDER = [
    "PAYMENT_FAILED", "FORM_INVOICE_ID_NOT_FOUND", "PAYMENT_PARTIAL_POLICY_REVIEW",
    "PAYMENT_AMOUNT_CONFLICT", "DUPLICATE_FORM_INVOICE_REFERENCE",
    "PARENT_BATCH_SELECTION_PENDING",
    "IDENTITY_FIELD_MISMATCH", "STUDENT_NOT_IN_REFERENCE", "APPROVED_FORM_NO_REQUEST",
    "PARENT_BATCH_SELECTION_REQUIRED", "REQUEST_FAILED_BATCH_FULL",
    "BATCH_CAPACITY_UNCONFIRMED", "REQUEST_PENDING_BATCH_ALLOCATION",
    "REQUEST_WITHOUT_SCHEDULE", "FORM_PENDING", "FORM_REJECTED",
    "FORM_APPROVAL_STATUS_MISSING", "FORM_APPROVAL_STATUS_UNKNOWN", "FORM_HAS_NO_BOOKING_REQUEST",
    "MULTIPLE_VALID_SCHEDULE_ROWS", "SCHEDULE_OCCURRENCE_CONFLICT",
]


def _text(row: dict[str, Any] | None, key: str, default: str = "") -> str:
    if not row:
        return default
    value = row.get(key)
    return "" if not is_present(value) else str(value).strip()


def _same_id(left: Any, right: Any) -> bool:
    return normalize_identifier(left) == normalize_identifier(right)


def _stable_id(prefix: str, *parts: Any) -> str:
    raw = "|".join(str(x) for x in parts)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}-{digest}"


def _finding(code: str, severity: str, evidence: str, action: str, owner: str,
             source_type: str = "case", source_id: Any = "") -> dict[str, str]:
    return {
        "reason_code": code,
        "severity": severity,
        "evidence": evidence,
        "recommended_action": action,
        "owner": owner,
        "source_type": source_type,
        "source_record_id": normalize_identifier(source_id),
    }


def _add_id_mismatches(findings: list[dict[str, str]], left: dict[str, Any], right: dict[str, Any],
                       fields: tuple[str, ...], left_label: str, right_label: str,
                       left_id: Any, right_id: Any) -> None:
    for field in fields:
        if not _same_id(left.get(field), right.get(field)):
            findings.append(_finding(
                "IDENTITY_FIELD_MISMATCH", "HIGH",
                f"{left_label}.{field}={left.get(field)!r} differs from {right_label}.{field}={right.get(field)!r}.",
                "Hold downstream progression and verify the authoritative student/enrollment record.",
                "Operations + data owner", left_label, left_id or right_id,
            ))


def _auto_gates_pass(case: dict[str, Any], findings: list[dict[str, str]], policy: dict[str, Any]) -> bool:
    gates = policy.get("auto_approval_gates", {})
    invoice = case.get("invoice") or {}
    forms = case.get("forms", [])
    material_findings = [x for x in findings if x.get("severity") != "INFO"]
    if (not policy.get("auto_approval_enabled", False) or len(forms) != 1
            or material_findings):
        return False
    form = forms[0]
    approval_status = _text(form, "approval_status").casefold()
    if approval_status != "approved":
        return False
    if not _same_id(invoice.get("id"), form.get("invoice_id")):
        return False
    eligible = policy.get("eligibility", {})
    paid_statuses = {str(x).casefold() for x in eligible.get("paid_statuses", ["Paid"])}
    if _text(invoice, "payment_status").casefold() not in paid_statuses:
        return False
    if _text(invoice, "is_renewal").casefold() != str(eligible.get("renewal_value", "Yes")).casefold():
        return False

    # The configured amount comparison is provisional until Finance signs off.
    # Auto-approval also requires a provider-backed settled amount and currency.
    payment_cfg = policy.get("payment", {})
    if payment_cfg.get("amount_rule_status") != "APPROVED":
        return False
    settled_amount_field = payment_cfg.get("settled_amount_field", "gateway_settled_amount")
    settled_currency_field = payment_cfg.get("settled_currency_field", "gateway_settled_currency")
    settled_amount = invoice.get(settled_amount_field)
    settled_currency = invoice.get(settled_currency_field)
    form_amount = form.get(payment_cfg.get("form_amount_field", "amount_paid"))
    tolerance = payment_cfg.get("amount_tolerance", 0)
    if not is_present(settled_amount) or not is_present(settled_currency):
        return False
    if not numbers_match(form_amount, settled_amount, tolerance):
        return False
    if _text(invoice, "currency").casefold() != str(settled_currency).strip().casefold():
        return False

    payment_verified_field = gates.get("payment_verified_field", "gateway_verified")
    if not payment_verified_field or str(invoice.get(payment_verified_field, "")).strip().casefold() not in {"true", "yes", "1"}:
        return False

    # Active-student and identity evidence are eligibility gates. Parent choice,
    # capacity, seat hold, and schedule parameters belong to scheduling readiness.
    ref_rows = case.get("reference_rows", [])
    active_field = gates.get("student_active_field", "student_active")
    if len(ref_rows) != 1 or active_field not in ref_rows[0]:
        return False
    if str(ref_rows[0].get(active_field)).strip().casefold() not in {"true", "yes", "1"}:
        return False
    return True


ELIGIBILITY_REASON_CODES = {
    "PAYMENT_FAILED", "PAYMENT_PARTIAL_POLICY_REVIEW", "PAYMENT_STATUS_UNSUPPORTED",
    "INVOICE_NOT_MARKED_RENEWAL", "PAID_RENEWAL_NO_EXACT_FORM",
    "DUPLICATE_FORM_INVOICE_REFERENCE", "IDENTITY_FIELD_MISSING", "IDENTITY_FIELD_MISMATCH",
    "PAYMENT_AMOUNT_MISSING", "PAYMENT_AMOUNT_INVALID", "PAYMENT_AMOUNT_CONFLICT",
    "FORM_PENDING", "FORM_REJECTED", "FORM_APPROVAL_STATUS_MISSING",
    "FORM_APPROVAL_STATUS_UNKNOWN", "STUDENT_NOT_IN_REFERENCE",
    "REFERENCE_STUDENT_DUPLICATE", "REFERENCE_ID_MISMATCH",
}

BOOKING_REQUEST_REASON_CODES = {
    "APPROVED_FORM_NO_REQUEST", "FORM_HAS_NO_BOOKING_REQUEST",
    "FORM_REQUEST_FIELD_MISMATCH", "FORM_REQUEST_BATCH_MISMATCH",
    "DUPLICATE_BOOKING_REQUEST_FOR_FORM", "BOOKING_REQUEST_FORM_NOT_FOUND",
    "REQUEST_INVOICE_ID_NOT_FOUND",
}

SCHEDULING_REASON_CODES = {
    "REQUEST_PENDING_BATCH_ALLOCATION", "REQUEST_FAILED_BATCH_FULL",
    "PARENT_BATCH_SELECTION_PENDING", "PARENT_BATCH_SELECTION_REQUIRED",
    "REQUEST_WITHOUT_SCHEDULE", "SCHEDULE_WITHOUT_REQUEST",
    "MULTIPLE_VALID_SCHEDULE_ROWS", "SCHEDULE_OCCURRENCE_CONFLICT",
    "SCHEDULE_FIELDS_MISSING", "REQUEST_SCHEDULE_FIELD_MISMATCH",
    "BATCH_NOT_IN_REFERENCE", "BATCH_CAPACITY_DATA_MISSING",
    "BATCH_CAPACITY_DATA_INVALID", "BATCH_CONFIRMED_FULL",
    "BATCH_CAPACITY_UNCONFIRMED", "FORM_BATCH_NOT_IN_REFERENCE",
    "FORM_REFERENCE_BATCH_MISMATCH", "FORM_REFERENCE_PREFERENCE_MISMATCH",
    "PAYMENT_EVIDENCE_REFERENCE_MISSING", "PAYMENT_EVIDENCE_SOURCE_MISSING",
    "PAYMENT_EVIDENCE_SOURCE_UNTRUSTED", "PAYMENT_EVIDENCE_REFERENCE_CONFLICT",
    "SCHEDULE_PARAMETERS_MISSING", "SCHEDULE_FIELD_MISSING", "SCHEDULE_DATE_INVALID",
    "SCHEDULE_TIME_INVALID", "SCHEDULE_TIMEZONE_MISSING", "SCHEDULE_TIMEZONE_INVALID",
    "SCHEDULE_END_NOT_AFTER_START", "SCHEDULE_LOCAL_TIME_AMBIGUOUS",
    "SCHEDULE_LOCAL_TIME_NONEXISTENT", "SCHEDULE_PARAMETERS_UNVERIFIED",
    "SCHEDULE_PARAMETERS_EVIDENCE_MISSING",
}


def _truthy(value: Any) -> bool:
    return str(value).strip().casefold() in {"true", "yes", "1"}


def _schedule_parameters(request: dict[str, Any]) -> list[dict[str, Any]]:
    raw = request.get("schedule_parameters", request.get("schedule_parameters_json", []))
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (TypeError, json.JSONDecodeError):
            return []
    if isinstance(raw, dict):
        raw = [raw]
    return [x for x in raw if isinstance(x, dict)] if isinstance(raw, list) else []


def _occurrence_key(row: dict[str, Any]) -> tuple[str, ...]:
    return tuple(normalize_identifier(row.get(field)) if field in {"student_id", "class_id", "classbatch_id"}
                 else str(row.get(field, "")).strip()
                 for field in ("student_id", "class_id", "class_date", "start_time", "classbatch_id"))


def _validate_schedule_parameters(params: dict[str, Any], required_fields: list[str]) -> list[str]:
    """Return precise fail-closed errors for a local schedule occurrence."""
    errors: list[str] = []
    missing = [field for field in required_fields if not is_present(params.get(field))]
    if missing:
        errors.append("SCHEDULE_FIELD_MISSING")
    if not all(is_present(params.get(field)) for field in ("class_date", "start_time", "end_time", "timezone")):
        if not is_present(params.get("timezone")):
            errors.append("SCHEDULE_TIMEZONE_MISSING")
        if not is_present(params.get("class_date")):
            errors.append("SCHEDULE_DATE_INVALID")
        if not is_present(params.get("start_time")) or not is_present(params.get("end_time")):
            errors.append("SCHEDULE_TIME_INVALID")
        return sorted(set(errors))

    try:
        local_date = date.fromisoformat(str(params["class_date"]))
    except (TypeError, ValueError):
        errors.append("SCHEDULE_DATE_INVALID")
        return sorted(set(errors))
    try:
        start = time.fromisoformat(str(params["start_time"]))
        end = time.fromisoformat(str(params["end_time"]))
        if start.tzinfo is not None or end.tzinfo is not None:
            errors.append("SCHEDULE_TIME_INVALID")
            return sorted(set(errors))
        if end <= start:
            errors.append("SCHEDULE_END_NOT_AFTER_START")
    except (TypeError, ValueError):
        errors.append("SCHEDULE_TIME_INVALID")
        return sorted(set(errors))

    try:
        zone = ZoneInfo(str(params["timezone"]).strip())
    except (TypeError, ValueError, ZoneInfoNotFoundError):
        errors.append("SCHEDULE_TIMEZONE_INVALID")
        return sorted(set(errors))

    # A round trip through UTC distinguishes ordinary, ambiguous, and nonexistent
    # local wall times without guessing which DST fold the business intended.
    for wall_time in (start, end):
        naive = datetime.combine(local_date, wall_time)
        roundtrips: list[datetime] = []
        offsets = set()
        for fold in (0, 1):
            aware = naive.replace(tzinfo=zone, fold=fold)
            returned = aware.astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None)
            if returned == naive:
                roundtrips.append(returned)
                offsets.add(aware.utcoffset())
        if not roundtrips:
            errors.append("SCHEDULE_LOCAL_TIME_NONEXISTENT")
        elif len(offsets) > 1:
            errors.append("SCHEDULE_LOCAL_TIME_AMBIGUOUS")
    return sorted(set(errors))


def evaluate_stage_readiness(case: dict[str, Any], decision: dict[str, Any], policy: dict[str, Any],
                             input_snapshot_sha256: str) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, str]]]:
    """Evaluate request and schedule readiness separately; never performs writes."""
    invoice = case.get("invoice") or {}
    forms = case.get("forms", [])
    requests = case.get("requests", [])
    schedules = case.get("schedules", [])
    refs = case.get("reference_rows", [])
    findings = decision.get("findings", [])
    eligibility = decision["decision_outcome"]
    reason_codes = {x["reason_code"] for x in findings}
    stage_findings: list[dict[str, str]] = []
    form_id = normalize_identifier(forms[0].get("id")) if len(forms) == 1 else ""
    request_id = normalize_identifier(requests[0].get("id")) if len(requests) == 1 else ""
    form = forms[0] if len(forms) == 1 else {}
    request = requests[0] if len(requests) == 1 else {}

    status = _text(form, "approval_status").casefold()
    if len(forms) == 1 and not requests and status == "approved":
        stage_findings.append(_finding(
            "APPROVED_FORM_NO_REQUEST", "HIGH",
            f"Approved form {form_id} has no booking request with an exact faculty_form_id match.",
            "Create or repair the request only under an approved procedure; no request is created by this prototype.",
            "Operations", "form", form_id,
        ))
    elif len(forms) == 1 and not requests and status not in {"", "pending"}:
        stage_findings.append(_finding(
            "FORM_HAS_NO_BOOKING_REQUEST", "MEDIUM",
            f"Form {form_id} has no booking request with an exact faculty_form_id match.",
            "Confirm form approval/payment status and queue the next step under business policy.",
            "Operations", "form", form_id,
        ))

    if eligibility == "BLOCKED":
        booking_status = "BLOCKED"
    elif eligibility != "AUTO_APPROVED":
        booking_status = "NOT_READY"
    elif len(forms) != 1:
        booking_status = "NEEDS_HUMAN_REVIEW"
    elif not requests:
        booking_status = "READY_TO_CREATE_REQUEST"
    elif len(requests) > 1:
        booking_status = "NEEDS_HUMAN_REVIEW"
    else:
        request = requests[0]
        valid_link = (
            _same_id(request.get("faculty_form_id"), form_id)
            and _same_id(request.get("invoice_id"), invoice.get("id"))
            and all(_same_id(request.get(field), invoice.get(field))
                    for field in ("student_id", "user_id", "class_id", "educator_id"))
            and is_present(request.get("request_status"))
        )
        booking_status = "REQUEST_EXISTS_VALID" if valid_link else "NEEDS_HUMAN_REVIEW"

    # Evidence status values are deliberately explicit. Missing fields never imply a pass.
    gates = policy.get("auto_approval_gates", {})
    payment_cfg = policy.get("payment", {})
    stage_cfg = policy.get("stage_readiness", {})
    request_cfg = stage_cfg.get("booking_request", {})
    schedule_cfg = stage_cfg.get("scheduling", {})
    payment_verified_field = gates.get("payment_verified_field", "gateway_verified")
    ref = refs[0] if len(refs) == 1 else {}
    parent_field = gates.get("parent_choice_confirmed_field", "parent_batch_choice_confirmed")
    parent_evidence_field = request_cfg.get("parent_choice_evidence_id_field", "parent_choice_evidence_id")
    parent_confirmed = any(_truthy(row.get(parent_field)) for row in (form, requests[0] if len(requests) == 1 else {}))
    parent_evidence_id = next((normalize_identifier(row.get(parent_evidence_field)) for row in
                               (form, requests[0] if len(requests) == 1 else {})
                               if is_present(row.get(parent_evidence_field))), "")
    capacity_authoritative = bool(policy.get("reference_capacity_authoritative", False))
    capacity_confirmed = _truthy(request.get("capacity_confirmed", False)) if len(requests) == 1 else _truthy(case.get("capacity_confirmed", False))
    capacity_available = _truthy(request.get("capacity_available", False)) if len(requests) == 1 else _truthy(case.get("capacity_available", False))
    capacity_evidence_id = normalize_identifier(request.get("capacity_evidence_id")) if len(requests) == 1 else normalize_identifier(case.get("capacity_evidence_id"))
    seat_hold_id = normalize_identifier(request.get("seat_hold_id")) if len(requests) == 1 else normalize_identifier(case.get("seat_hold_id"))
    amount_field = payment_cfg.get("settled_amount_field", "gateway_settled_amount")
    currency_field = payment_cfg.get("settled_currency_field", "gateway_settled_currency")
    schedule_params = _schedule_parameters(request) if len(requests) == 1 else []
    required_schedule_fields = schedule_cfg.get("required_schedule_fields", [
        "class_id", "educator_id", "classbatch_id", "class_date", "start_time", "end_time", "timezone",
    ])
    schedule_parameter_errors: set[str] = set()
    if not schedule_params:
        schedule_parameter_errors.add("SCHEDULE_PARAMETERS_MISSING")
    for params in schedule_params:
        schedule_parameter_errors.update(_validate_schedule_parameters(params, required_schedule_fields))
    parameters_verified = _truthy(request.get(schedule_cfg.get("parameters_verified_field", "schedule_parameters_verified")))
    parameters_evidence_id = request.get(schedule_cfg.get("parameters_evidence_id_field", "schedule_parameters_evidence_id"))
    if not parameters_verified:
        schedule_parameter_errors.add("SCHEDULE_PARAMETERS_UNVERIFIED")
    if not is_present(parameters_evidence_id):
        schedule_parameter_errors.add("SCHEDULE_PARAMETERS_EVIDENCE_MISSING")
    params_complete = bool(schedule_params) and not schedule_parameter_errors

    payment_evidence_id_field = payment_cfg.get("evidence_id_field", "payment_evidence_id")
    payment_evidence_source_field = payment_cfg.get("evidence_source_field", "payment_evidence_source")
    payment_evidence_id = normalize_identifier(invoice.get(payment_evidence_id_field))
    payment_evidence_source = _text(invoice, payment_evidence_source_field).casefold()
    allowed_payment_evidence_sources = {
        str(x).strip().casefold() for x in payment_cfg.get("allowed_evidence_sources", []) if is_present(x)
    }
    if not payment_evidence_id:
        payment_evidence_status = "MISSING"
        payment_evidence_reason = "PAYMENT_EVIDENCE_REFERENCE_MISSING"
    elif _same_id(payment_evidence_id, invoice.get("id")):
        payment_evidence_status = "CONFLICT"
        payment_evidence_reason = "PAYMENT_EVIDENCE_REFERENCE_CONFLICT"
    elif not payment_evidence_source:
        payment_evidence_status = "MISSING"
        payment_evidence_reason = "PAYMENT_EVIDENCE_SOURCE_MISSING"
    elif payment_evidence_source not in allowed_payment_evidence_sources:
        payment_evidence_status = "UNVERIFIED"
        payment_evidence_reason = "PAYMENT_EVIDENCE_SOURCE_UNTRUSTED"
    else:
        payment_evidence_status = "VERIFIED"
        payment_evidence_reason = ""
    scheduling_context = eligibility == "AUTO_APPROVED" and booking_status == "REQUEST_EXISTS_VALID"

    gateway_status = "VERIFIED" if _truthy(invoice.get(payment_verified_field)) else (
        "MISSING" if not is_present(invoice.get(payment_verified_field)) else "CONFLICT")
    parent_status = "VERIFIED" if parent_confirmed and parent_evidence_id else (
        "MISSING" if not parent_confirmed else "UNVERIFIED")
    active_field = gates.get("student_active_field", "student_active")
    active_value = ref.get(active_field)
    active_status = "VERIFIED" if _truthy(active_value) else (
        "MISSING" if active_field not in ref else "CONFLICT")
    capacity_status = "VERIFIED" if capacity_authoritative and capacity_confirmed and capacity_evidence_id else (
        "UNVERIFIED" if not capacity_authoritative else "MISSING")
    seat_status = "VERIFIED" if capacity_available and seat_hold_id else (
        "MISSING" if not seat_hold_id else "CONFLICT")
    amount_verified = (
        payment_cfg.get("amount_rule_status") == "APPROVED"
        and is_present(invoice.get(amount_field)) and is_present(invoice.get(currency_field))
        and numbers_match(form.get(payment_cfg.get("form_amount_field", "amount_paid")), invoice.get(amount_field), payment_cfg.get("amount_tolerance", 0))
        and _text(invoice, "currency").casefold() == _text(invoice, currency_field).casefold()
    )
    if amount_verified:
        amount_status = "VERIFIED"
    elif not is_present(invoice.get(amount_field)) or not is_present(invoice.get(currency_field)):
        amount_status = "MISSING"
    elif is_present(form.get(payment_cfg.get("form_amount_field", "amount_paid"))) and not numbers_match(
            form.get(payment_cfg.get("form_amount_field", "amount_paid")), invoice.get(amount_field), payment_cfg.get("amount_tolerance", 0)):
        amount_status = "CONFLICT"
    else:
        amount_status = "UNVERIFIED"
    evidence_status = {
        "gateway_verification": gateway_status,
        "explicit_parent_choice": parent_status,
        "active_student": active_status,
        "authoritative_capacity": capacity_status,
        "seat_hold": seat_status,
        "payment_amount_currency": amount_status,
        "payment_evidence_reference": payment_evidence_status,
        "schedule_parameters": "VERIFIED" if params_complete else ("MISSING" if not schedule_params else "CONFLICT"),
        "exact_booking_request": "VERIFIED" if booking_status == "REQUEST_EXISTS_VALID" else ("MISSING" if not requests else "CONFLICT"),
    }
    if case.get("case_type") != "invoice_renewal":
        evidence_status = {field: "NOT_APPLICABLE" for field in evidence_status}

    scheduling_status = "NOT_READY"
    ready_rows: list[dict[str, Any]] = []
    exclusion_codes: set[str] = set()
    if gateway_status != "VERIFIED":
        exclusion_codes.add("GATEWAY_VERIFICATION_MISSING" if gateway_status == "MISSING" else "GATEWAY_VERIFICATION_CONFLICT")
    if amount_status != "VERIFIED":
        exclusion_codes.add("PAYMENT_AMOUNT_CURRENCY_UNVERIFIED" if amount_status in {"MISSING", "UNVERIFIED"} else "PAYMENT_AMOUNT_CURRENCY_CONFLICT")
    if scheduling_context and payment_evidence_reason:
        exclusion_codes.add(payment_evidence_reason)
    if active_status != "VERIFIED":
        exclusion_codes.add("STUDENT_ACTIVE_STATUS_UNAVAILABLE" if active_status == "MISSING" else "STUDENT_ACTIVE_STATUS_CONFLICT")
    if parent_status != "VERIFIED":
        exclusion_codes.add("PARENT_CHOICE_EVIDENCE_MISSING" if parent_status == "MISSING" else "PARENT_CHOICE_NOT_CONFIRMED")
    if capacity_status != "VERIFIED":
        exclusion_codes.add("CAPACITY_NOT_AUTHORITATIVE" if capacity_status == "UNVERIFIED" else "CAPACITY_EVIDENCE_MISSING")
    if seat_status != "VERIFIED":
        exclusion_codes.add("SEAT_HOLD_MISSING" if seat_status == "MISSING" else "SEAT_HOLD_CONFLICT")
    if scheduling_context:
        exclusion_codes.update(schedule_parameter_errors)
    if eligibility == "BLOCKED":
        scheduling_status = "BLOCKED"
    elif eligibility != "AUTO_APPROVED":
        scheduling_status = "NOT_READY"
        exclusion_codes.update(reason_codes)
    elif not requests:
        scheduling_status = "WAITING_ON_REQUEST"
        exclusion_codes.add("APPROVED_FORM_NO_REQUEST")
    elif len(requests) != 1 or booking_status != "REQUEST_EXISTS_VALID":
        scheduling_status = "NEEDS_HUMAN_REVIEW"
        exclusion_codes.add("DUPLICATE_BOOKING_REQUEST_FOR_FORM" if len(requests) > 1 else "BOOKING_REQUEST_LINK_INVALID")
    else:
        request = requests[0]
        request_status = _text(request, "request_status")
        approved_request_states = {str(x).casefold() for x in schedule_cfg.get("schedule_ready_request_statuses", [])}
        if not approved_request_states or request_status.casefold() not in approved_request_states:
            scheduling_status = "NEEDS_HUMAN_REVIEW"
            exclusion_codes.add("SCHEDULE_READY_REQUEST_STATUS_UNAPPROVED")
        elif not parent_confirmed or not parent_evidence_id:
            scheduling_status = "WAITING_ON_PARENT"
            exclusion_codes.add("PARENT_CHOICE_EVIDENCE_MISSING" if not parent_evidence_id else "PARENT_CHOICE_NOT_CONFIRMED")
        elif not capacity_authoritative or not capacity_confirmed or not capacity_evidence_id:
            scheduling_status = "WAITING_ON_CAPACITY"
            exclusion_codes.add("CAPACITY_NOT_AUTHORITATIVE" if not capacity_authoritative else "CAPACITY_EVIDENCE_MISSING")
        elif not capacity_available:
            scheduling_status = "WAITING_ON_CAPACITY"
            exclusion_codes.add("BATCH_CAPACITY_UNAVAILABLE")
        elif not seat_hold_id:
            scheduling_status = "WAITING_ON_CAPACITY"
            exclusion_codes.add("SEAT_HOLD_MISSING")
        elif payment_evidence_status != "VERIFIED":
            scheduling_status = "NEEDS_HUMAN_REVIEW"
            exclusion_codes.add(payment_evidence_reason)
        elif not params_complete:
            scheduling_status = "NEEDS_HUMAN_REVIEW"
            exclusion_codes.update(schedule_parameter_errors)
        else:
            scheduling_findings = [x for x in findings if x["reason_code"] in SCHEDULING_REASON_CODES]
            blocking_schedule_findings = [x for x in scheduling_findings
                                          if x.get("severity") != "INFO"
                                          and x["reason_code"] != "REQUEST_WITHOUT_SCHEDULE"]
            if blocking_schedule_findings:
                scheduling_status = "NEEDS_HUMAN_REVIEW"
                exclusion_codes.update(x["reason_code"] for x in blocking_schedule_findings)
            else:
                active_rows = [x for x in schedules if str(x.get("is_cancelled", "")).strip().casefold() != "yes"]
                ids = [normalize_identifier(x.get("classschedule_id")) for x in active_rows]
                keys = [_occurrence_key(x) for x in active_rows]
                request_id_value = normalize_identifier(request.get("id"))
                expected_by_key = {_occurrence_key({**params, "student_id": request.get("student_id")}) : params
                                   for params in schedule_params}
                row_conflict = (
                    any(not x for x in ids) or len(ids) != len(set(ids))
                    or len(keys) != len(set(keys))
                    or any(not _same_id(x.get("bookingrequest_id"), request_id_value) for x in active_rows)
                )
                for row, key in zip(active_rows, keys):
                    expected = expected_by_key.get(key)
                    if expected is None:
                        continue
                    for field in ("class_id", "educator_id", "classbatch_id", "class_date", "start_time", "end_time", "timezone"):
                        left, right = row.get(field), expected.get(field)
                        same = _same_id(left, right) if field in {"class_id", "educator_id", "classbatch_id"} else str(left).strip().casefold() == str(right).strip().casefold()
                        if not same:
                            row_conflict = True
                            break
                if row_conflict:
                    scheduling_status = "NEEDS_HUMAN_REVIEW"
                    exclusion_codes.add("SCHEDULE_OCCURRENCE_CONFLICT")
                else:
                    existing_keys = set(keys)
                    unexpected = existing_keys - set(expected_by_key)
                    if unexpected:
                        scheduling_status = "NEEDS_HUMAN_REVIEW"
                        exclusion_codes.add("SCHEDULE_FULFILLMENT_UNDETERMINED")
                    else:
                        missing = [(key, params) for key, params in expected_by_key.items() if key not in existing_keys]
                        if not missing:
                            scheduling_status = "ALREADY_FULFILLED"
                        else:
                            scheduling_status = "READY_FOR_CLASS_SCHEDULE_BOOKINGS"
                            for key, params in missing:
                                instance_key = "|".join(key)
                                ready_rows.append({
                                    "readiness_id": _stable_id("READY", request_id_value, instance_key),
                                    "case_id": decision["case_id"],
                                    "decision_id": decision["decision_id"],
                                    "invoice_id": normalize_identifier(invoice.get("id")),
                                    "teacher_form_id": form_id,
                                    "booking_request_id": request_id_value,
                                    "student_id": normalize_identifier(request.get("student_id")),
                                    "user_id": normalize_identifier(request.get("user_id")),
                                    "class_id": normalize_identifier(params.get("class_id")),
                                    "educator_id": normalize_identifier(params.get("educator_id")),
                                    "classbatch_id": normalize_identifier(params.get("classbatch_id")),
                                    "schedule_instance_key": instance_key,
                                    "class_date": params.get("class_date"),
                                    "start_time": params.get("start_time"),
                                    "end_time": params.get("end_time"),
                                    "timezone": params.get("timezone"),
                                    "payment_evidence_id": normalize_identifier(invoice.get("payment_evidence_id")),
                                    "parent_choice_evidence_id": parent_evidence_id,
                                    "capacity_evidence_id": capacity_evidence_id,
                                    "seat_hold_id": seat_hold_id,
                                    "verified_settled_amount": invoice.get(amount_field),
                                    "currency": invoice.get(currency_field),
                                    "policy_version": policy.get("policy_version", "unspecified"),
                                    "evaluated_at_utc": decision["evaluated_at_utc"],
                                    "input_snapshot_sha256": input_snapshot_sha256,
                                })

    exclusion_codes.update(
        x["reason_code"] for x in findings
        if x["reason_code"] not in ELIGIBILITY_REASON_CODES | BOOKING_REQUEST_REASON_CODES
        and x["reason_code"] != "REQUEST_WITHOUT_SCHEDULE"
        and x.get("severity") != "INFO"
    )
    exclusion_codes.update(x["reason_code"] for x in stage_findings)
    reason_descriptions = {
        "PAYMENT_EVIDENCE_REFERENCE_MISSING": "A payment evidence ID is required; invoice ID is not payment evidence.",
        "PAYMENT_EVIDENCE_REFERENCE_CONFLICT": "Payment evidence reference must identify a separate evidence record, not the invoice.",
        "PAYMENT_EVIDENCE_SOURCE_MISSING": "Payment evidence source is missing.",
        "PAYMENT_EVIDENCE_SOURCE_UNTRUSTED": "Payment evidence source is not on the explicitly configured trusted-source allowlist.",
        "SCHEDULE_PARAMETERS_MISSING": "No schedule occurrence parameters were supplied.",
        "SCHEDULE_FIELD_MISSING": "One or more required schedule fields are missing.",
        "SCHEDULE_DATE_INVALID": "Schedule date is missing or invalid.",
        "SCHEDULE_TIME_INVALID": "Schedule start/end time is missing or invalid.",
        "SCHEDULE_TIMEZONE_MISSING": "A timezone identifier is required.",
        "SCHEDULE_TIMEZONE_INVALID": "Timezone must be a valid IANA timezone identifier.",
        "SCHEDULE_END_NOT_AFTER_START": "Schedule end time must be strictly after its start time.",
        "SCHEDULE_LOCAL_TIME_AMBIGUOUS": "Local time occurs twice at a daylight-saving transition; an explicit disambiguation rule is required.",
        "SCHEDULE_LOCAL_TIME_NONEXISTENT": "Local time does not exist at a daylight-saving transition.",
        "SCHEDULE_PARAMETERS_UNVERIFIED": "Schedule parameters lack an explicit verified status.",
        "SCHEDULE_PARAMETERS_EVIDENCE_MISSING": "Schedule parameter verification evidence ID is missing.",
    }
    for code in sorted(exclusion_codes):
        if code in reason_descriptions and not any(f["reason_code"] == code for f in stage_findings):
            stage_findings.append(_finding(code, "HIGH", reason_descriptions[code],
                                           "Verify authoritative evidence and correct the source before scheduling.",
                                           "Operations + data owner", "case", decision.get("case_id", "")))
    # The above findings also belong in the stage report exclusions and exception output.
    exclusion_codes.update(x["reason_code"] for x in stage_findings)
    if scheduling_status != "READY_FOR_CLASS_SCHEDULE_BOOKINGS":
        ready_rows = []
    row = {
        "case_id": decision["case_id"],
        "decision_id": decision["decision_id"],
        "invoice_id": decision["invoice_id"],
        "teacher_form_id": form_id,
        "booking_request_id": request_id,
        "renewal_eligibility_status": eligibility,
        "booking_request_readiness_status": booking_status,
        "scheduling_readiness_status": scheduling_status,
        "exclusion_reason_codes": ";".join(sorted(exclusion_codes)),
        "evidence_status_json": json.dumps(evidence_status, sort_keys=True),
        "policy_version": decision["policy_version"],
        "evaluated_at_utc": decision["evaluated_at_utc"],
        "input_snapshot_sha256": input_snapshot_sha256,
    }
    return row, ready_rows, stage_findings


def evaluate_case(case: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    """Evaluate one renewal case and return a decision plus zero or more findings."""
    invoice = case.get("invoice")
    forms = case.get("forms", [])
    requests = case.get("requests", [])
    schedules = case.get("schedules", [])
    refs = case.get("reference_rows", [])
    findings: list[dict[str, str]] = []
    payment_cfg = policy.get("payment", {})
    eligibility_cfg = policy.get("eligibility", {})
    reason = ""
    explanation = ""
    action = ""
    owner = "Operations"

    if case.get("case_type") == "unmatched_form":
        form = forms[0]
        missing_invoice_id = normalize_identifier(form.get("invoice_id"))
        findings.append(_finding(
            "FORM_INVOICE_ID_NOT_FOUND", "HIGH",
            f"Form {form.get('id')} references invoice_id {missing_invoice_id}, which is absent from the invoice extract.",
            "Verify the gateway/source invoice ID; do not match using student_id alone.",
            "Operations + Finance", "form", form.get("id"),
        ))
        _add_form_status_finding(findings, form)
        return _decision(case, "BLOCKED", findings, policy,
                         "FORM_INVOICE_ID_NOT_FOUND",
                         "The form cannot progress because its invoice reference is not present in the supplied invoice data.",
                         "Verify the source invoice and correct only through an auditable review.", "Operations + Finance")

    if case.get("case_type") == "orphan_request":
        request = (requests or [{}])[0]
        findings.append(_finding("BOOKING_REQUEST_FORM_NOT_FOUND", "HIGH",
                                 f"Booking request {request.get('id')} has no form with an exact faculty_form_id match.",
                                 "Verify the source request and its invoice/form history; do not create a replacement automatically.",
                                 "Operations", "request", request.get("id")))
        if invoice is None:
            findings.append(_finding("REQUEST_INVOICE_ID_NOT_FOUND", "HIGH",
                                     f"Booking request {request.get('id')} references invoice {case.get('invoice_id')}, absent from the invoice extract.",
                                     "Verify source transaction and hold all downstream action.",
                                     "Operations + Finance", "request", request.get("id")))
            return _decision(case, "BLOCKED", findings, policy, "REQUEST_INVOICE_ID_NOT_FOUND",
                             "The request cannot progress without its referenced invoice.",
                             "Verify the invoice source and correct only with auditable evidence.", "Operations + Finance")
        return _decision(case, "NEEDS_HUMAN_REVIEW", findings, policy, "BOOKING_REQUEST_FORM_NOT_FOUND",
                         "The booking request is not linked to a form by exact ID.",
                         "Verify the source records and preserve existing booking state.", "Operations")

    if case.get("case_type") == "orphan_schedule":
        schedule = (schedules or [{}])[0]
        findings.append(_finding("SCHEDULE_WITHOUT_REQUEST", "HIGH",
                                 f"Schedule row {schedule.get('id')} references request {schedule.get('bookingrequest_id')}, absent from the request extract.",
                                 "Verify source-system request history; do not delete or recreate the schedule automatically.",
                                 "Scheduling + Operations", "schedule", schedule.get("id")))
        return _decision(case, "NEEDS_HUMAN_REVIEW", findings, policy, "SCHEDULE_WITHOUT_REQUEST",
                         "The schedule row has no exact-linked booking request in the input snapshot.",
                         "Refresh source data and investigate the relationship before any write.", "Scheduling + Operations")

    if case.get("case_type") != "invoice_renewal" or invoice is None:
        return _decision(case, "NEEDS_HUMAN_REVIEW", findings, policy, "CASE_SOURCE_UNRESOLVED",
                         "The case does not have an invoice row to evaluate.",
                         "Inspect the source records and restore the exact ID relationship.", "Operations")

    invoice_id = invoice.get("id")
    payment_status = _text(invoice, "payment_status")
    paid_statuses = {str(x).casefold() for x in eligibility_cfg.get("paid_statuses", ["Paid"])}
    partial_statuses = {str(x).casefold() for x in payment_cfg.get("partial_statuses", ["Partially_Paid"])}
    failed_statuses = {str(x).casefold() for x in payment_cfg.get("failed_statuses", ["Failed"])}
    if payment_status.casefold() in failed_statuses:
        findings.append(_finding("PAYMENT_FAILED", "HIGH",
                                 f"Invoice {invoice_id} has payment_status={payment_status}.",
                                 "Stop booking progression and verify whether another successful payment attempt exists.",
                                 "Finance", "invoice", invoice_id))
    elif payment_status.casefold() in partial_statuses:
        findings.append(_finding("PAYMENT_PARTIAL_POLICY_REVIEW", "HIGH",
                                 f"Invoice {invoice_id} has payment_status={payment_status}; eligibility policy is not approved.",
                                 "Finance must verify settled funds and the partial-payment rule.",
                                 "Finance + Operations", "invoice", invoice_id))
    elif payment_status.casefold() not in paid_statuses:
        findings.append(_finding("PAYMENT_STATUS_UNSUPPORTED", "HIGH",
                                 f"Invoice {invoice_id} has unsupported payment_status={payment_status!r}.",
                                 "Verify payment state with the authoritative provider.",
                                 "Finance", "invoice", invoice_id))

    if str(invoice.get("is_renewal", "")).strip().casefold() != str(eligibility_cfg.get("renewal_value", "Yes")).casefold():
        findings.append(_finding("INVOICE_NOT_MARKED_RENEWAL", "HIGH",
                                 f"Invoice {invoice_id} is_renewal={invoice.get('is_renewal')!r}.",
                                 "Confirm whether this invoice belongs in the renewal workflow.",
                                 "Operations + Finance", "invoice", invoice_id))

    if not forms:
        if payment_status.casefold() in paid_statuses and str(invoice.get("is_renewal", "")).casefold() == "yes":
            findings.append(_finding("PAID_RENEWAL_NO_EXACT_FORM", "HIGH",
                                     f"Paid renewal invoice {invoice_id} has no form with an exact invoice_id match.",
                                     "Ask the assigned educator/Operations to locate or submit the correct form; do not use student_id as a fallback.",
                                     "Operations + educator", "invoice", invoice_id))
    elif len(forms) > 1:
        form_ids = [normalize_identifier(x.get("id")) for x in forms]
        findings.append(_finding("DUPLICATE_FORM_INVOICE_REFERENCE", "HIGH",
                                 f"Invoice {invoice_id} is referenced by multiple forms: {', '.join(form_ids)}.",
                                 "Hold downstream progression until Operations records a canonical disposition.",
                                 "Operations", "invoice", invoice_id))

    for form in forms:
        form_id = form.get("id")
        for field in policy.get("identity_fields", ["student_id", "user_id", "class_id", "educator_id"]):
            if not normalize_identifier(invoice.get(field)) or not normalize_identifier(form.get(field)):
                findings.append(_finding("IDENTITY_FIELD_MISSING", "HIGH",
                                         f"Required identity field {field} is missing on invoice {invoice_id} or form {form_id}.",
                                         "Verify the authoritative student/enrollment record before any downstream action.",
                                         "Operations + data owner", "form", form_id))
            elif not _same_id(invoice.get(field), form.get(field)):
                _add_id_mismatches(findings, invoice, form, (field,), "invoice", "form", invoice_id, form_id)
        comparison_field = payment_cfg.get("invoice_comparison_field", "net_amount")
        form_amount_field = payment_cfg.get("form_amount_field", "amount_paid")
        if not is_present(form.get(form_amount_field)) or not is_present(invoice.get(comparison_field)):
            findings.append(_finding("PAYMENT_AMOUNT_MISSING", "HIGH",
                                     f"Cannot compare invoice {invoice_id} {comparison_field} and form {form_id} {form_amount_field} because at least one is missing.",
                                     "Verify the package price and settled amount from the source system.",
                                     "Finance + Operations", "form", form_id))
        else:
            comparison_value = invoice.get(comparison_field)
            amount_match = numbers_match(form.get(form_amount_field), comparison_value,
                                         payment_cfg.get("amount_tolerance", 0))
            if amount_match is None:
                findings.append(_finding("PAYMENT_AMOUNT_INVALID", "HIGH",
                                     f"Invoice {invoice_id} and form {form_id} amount values are present but not safely numeric.",
                                     "Finance must verify the source amounts and currency before approval.",
                                     "Finance + Operations", "form", form_id))
            elif amount_match is False:
                findings.append(_finding("PAYMENT_AMOUNT_CONFLICT", "HIGH",
                                     f"Form {form_id} {form_amount_field}={form.get(form_amount_field)} differs from invoice {invoice_id} {comparison_field}={comparison_value}; amount semantics are unconfirmed.",
                                     "Finance must confirm the settled amount, discounts and comparison rule.",
                                     "Finance + Operations", "form", form_id))
        _add_form_status_finding(findings, form)

    # Cross-check each exact-linked row; no fuzzy fallback is allowed.
    for form in forms:
        for request in [x for x in requests if _same_id(x.get("faculty_form_id"), form.get("id"))]:
            for left_field, right_field in [
                ("student_id", "student_id"), ("invoice_id", "invoice_id"),
                ("user_id", "user_id"), ("class_id", "class_id"), ("educator_id", "educator_id"),
                ("sessions_purchased", "sessions_count"),
                ("continue_same_batch", "continue_same_batch"),
                ("preferred_days", "preferred_days"), ("preferred_time_slot", "preferred_time"),
            ]:
                left, right = form.get(left_field), request.get(right_field)
                if left_field in {"student_id", "invoice_id", "user_id", "class_id", "educator_id", "sessions_purchased"} and (not is_present(left) or not is_present(right)):
                    same = False
                else:
                    same = _same_id(left, right) if left_field.endswith("_id") or left_field in {"sessions_purchased"} else str(left).strip().casefold() == str(right).strip().casefold()
                if not same:
                    findings.append(_finding("FORM_REQUEST_FIELD_MISMATCH", "HIGH",
                                             f"Form {form.get('id')} {left_field}={left!r} differs from request {request.get('id')} {right_field}={right!r}.",
                                             "Verify the canonical student/request values before scheduling.",
                                             "Operations", "request", request.get("id")))
            if str(form.get("continue_same_batch", "")).strip().casefold() == "yes" and is_present(request.get("classbatch_id")):
                if not _same_id(form.get("current_classbatch_id"), request.get("classbatch_id")):
                    findings.append(_finding("FORM_REQUEST_BATCH_MISMATCH", "HIGH",
                                             f"Same-batch form {form.get('id')} current_classbatch_id differs from request {request.get('id')} classbatch_id.",
                                             "Verify requested versus current batch semantics and the parent's recorded choice.",
                                             "Operations / batch owner", "request", request.get("id")))

    request_ids = {normalize_identifier(x.get("id")) for x in requests}
    schedule_groups: dict[str, list[dict[str, Any]]] = {}
    for schedule in schedules:
        request_id = normalize_identifier(schedule.get("bookingrequest_id"))
        if request_id not in request_ids:
            findings.append(_finding("SCHEDULE_WITHOUT_REQUEST", "HIGH",
                                     f"Schedule {schedule.get('id')} references missing request {request_id}.",
                                     "Verify schedule/request source IDs; do not delete or recreate records automatically.",
                                     "Scheduling + Operations", "schedule", schedule.get("id")))
        schedule_groups.setdefault(request_id, []).append(schedule)

    for request in requests:
        request_id = request.get("id")
        linked_schedules = schedule_groups.get(normalize_identifier(request_id), [])
        linked_form_ids = {normalize_identifier(x.get("id")) for x in forms}
        if normalize_identifier(request.get("faculty_form_id")) in linked_form_ids:
            request_for_form = [x for x in requests if _same_id(x.get("faculty_form_id"), request.get("faculty_form_id"))]
            if len(request_for_form) > 1:
                findings.append(_finding("DUPLICATE_BOOKING_REQUEST_FOR_FORM", "HIGH",
                                         f"Form {request.get('faculty_form_id')} has multiple booking requests: {', '.join(normalize_identifier(x.get('id')) for x in request_for_form)}.",
                                         "Hold downstream writes and have Operations verify the canonical request.",
                                         "Operations", "form", request.get("faculty_form_id")))
        request_status = _text(request, "request_status")
        if request_status == "Pending_Batch_Allocation":
            findings.append(_finding("REQUEST_PENDING_BATCH_ALLOCATION", "MEDIUM",
                                     f"Request {request_id} is Pending_Batch_Allocation and has no confirmed batch allocation.",
                                     "Check the current allocation queue and authoritative capacity source.",
                                     "Operations / batch owner", "request", request_id))
        if request_status == "Failed_Batch_Full":
            findings.append(_finding("REQUEST_FAILED_BATCH_FULL", "HIGH",
                                     f"Request {request_id} is marked Failed_Batch_Full; this status is not independently verified against live capacity.",
                                     "Verify current capacity and offer an approved alternative for parent choice.",
                                     "Operations / batch owner", "request", request_id))
        if request_status == "Awaiting_Parent_Batch_Selection":
            findings.append(_finding("PARENT_BATCH_SELECTION_PENDING", "MEDIUM",
                                     f"Request {request_id} awaits parent batch choice; classbatch_id={request.get('classbatch_id')!r}.",
                                     "Send an approved choice request and wait for an explicit parent selection.",
                                     "Parent + Operations", "request", request_id))
        if not linked_schedules:
            findings.append(_finding("REQUEST_WITHOUT_SCHEDULE", "MEDIUM",
                                     f"Request {request_id} has no linked schedule row in this input snapshot; absence alone is not a failure.",
                                     "Check request state, extract freshness and scheduling SLA before taking action.",
                                     "Operations / scheduling", "request", request_id))
        elif len(linked_schedules) > 1:
            ids = [normalize_identifier(x.get("classschedule_id")) for x in linked_schedules]
            duplicate_schedule_ids = len(ids) != len(set(ids))
            active_schedules = [x for x in linked_schedules if str(x.get("is_cancelled", "")).strip().casefold() != "yes"]
            schedule_fields_missing = any(not is_present(x.get("classschedule_id")) or not is_present(x.get("class_date")) or not is_present(x.get("start_time")) for x in active_schedules)
            occurrence_keys = [(
                normalize_identifier(x.get("student_id")), normalize_identifier(x.get("class_id")),
                str(x.get("class_date", "")).strip(), str(x.get("start_time", "")).strip(),
                normalize_identifier(x.get("classbatch_id")),
            ) for x in active_schedules if is_present(x.get("class_date")) and is_present(x.get("start_time"))]
            conflict = duplicate_schedule_ids or len(occurrence_keys) != len(set(occurrence_keys))
            code = "SCHEDULE_OCCURRENCE_CONFLICT" if conflict else ("SCHEDULE_FIELDS_MISSING" if schedule_fields_missing else "MULTIPLE_VALID_SCHEDULE_ROWS")
            severity = "HIGH" if conflict else ("MEDIUM" if schedule_fields_missing else "INFO")
            detail = "Repeated schedule ID or same student/class/date/time/batch occurrence found." if conflict else ("One or more active rows lacks an ID, class date, or start time." if schedule_fields_missing else "Rows have distinct schedule IDs and class occurrences; multiple rows are not treated as duplicates.")
            findings.append(_finding(code, severity,
                                     f"Request {request_id} has {len(linked_schedules)} schedule rows ({', '.join(ids)}). {detail}",
                                     "Preserve valid instances; investigate only a repeated ID or conflicting class occurrence. Do not infer package completion from row count.",
                                     "Scheduling" if not conflict else "Scheduling + Operations", "request", request_id))

        # Compare schedule row values to its exact booking request.
        for schedule in linked_schedules:
            for field in ["invoice_id", "student_id", "user_id", "class_id", "educator_id"]:
                if not _same_id(schedule.get(field), request.get(field)):
                    findings.append(_finding("REQUEST_SCHEDULE_FIELD_MISMATCH", "HIGH",
                                             f"Schedule {schedule.get('id')} {field} differs from request {request_id}.",
                                             "Hold schedule progression and verify source records.",
                                             "Scheduling + Operations", "schedule", schedule.get("id")))
            if is_present(request.get("classbatch_id")) and not _same_id(schedule.get("classbatch_id"), request.get("classbatch_id")):
                findings.append(_finding("REQUEST_SCHEDULE_FIELD_MISMATCH", "HIGH",
                                         f"Schedule {schedule.get('id')} classbatch_id differs from request {request_id}.",
                                         "Verify selected batch and schedule assignment before proceeding.",
                                         "Scheduling + Operations", "schedule", schedule.get("id")))

    # Support reference identity, batch and provisional capacity checks.
    for row in [invoice, *forms]:
        if row is None:
            continue
        student_id = normalize_identifier(row.get("student_id"))
        matches = [r for r in refs if normalize_identifier(r.get("student_id")) == student_id]
        if not matches:
            findings.append(_finding("STUDENT_NOT_IN_REFERENCE", "MEDIUM",
                                     f"Student {student_id} is absent from the supplied reference snapshot.",
                                     "Confirm current student enrollment with the authoritative student source.",
                                     "Operations / data owner", "form" if row in forms else "invoice", row.get("id")))
        elif len(matches) > 1:
            findings.append(_finding("REFERENCE_STUDENT_DUPLICATE", "HIGH",
                                     f"Student {student_id} has multiple rows in the reference snapshot.",
                                     "Confirm the canonical current student row before any automatic action.",
                                     "Operations / data owner", "form" if row in forms else "invoice", row.get("id")))
        elif len(matches) == 1:
            ref = matches[0]
            for field in ["user_id", "class_id", "educator_id"]:
                if field in row and field in ref and not _same_id(row.get(field), ref.get(field)):
                    findings.append(_finding("REFERENCE_ID_MISMATCH", "HIGH",
                                             f"Student {student_id} {field} differs from the reference row.",
                                             "Verify against the authoritative student/enrollment system.",
                                             "Operations + data owner", "form" if row in forms else "invoice", row.get("id")))

    # Validate same-batch preferences against the reference as supporting evidence only.
    for form in forms:
        if str(form.get("continue_same_batch", "")).strip().casefold() != "yes":
            continue
        batch_id = normalize_identifier(form.get("current_classbatch_id"))
        batch_rows = [r for r in refs if normalize_identifier(r.get("current_classbatch_id")) == batch_id]
        if not batch_rows:
            findings.append(_finding("FORM_BATCH_NOT_IN_REFERENCE", "MEDIUM",
                                     f"Form {form.get('id')} current batch {batch_id} is absent from the reference snapshot.",
                                     "Verify current batch and teacher/time details from the authoritative batch source.",
                                     "Operations / batch owner", "form", form.get("id")))
            continue
        ref = batch_rows[0]
        for form_field, ref_field in [("class_id", "class_id"), ("educator_id", "educator_id")]:
            if not _same_id(form.get(form_field), ref.get(ref_field)):
                findings.append(_finding("FORM_REFERENCE_BATCH_MISMATCH", "HIGH",
                                         f"Form {form.get('id')} {form_field} differs from the reference details for current batch {batch_id}.",
                                         "Confirm current versus requested batch assignment with the batch owner.",
                                         "Operations / batch owner", "form", form.get("id")))
        for form_field, ref_field in [("preferred_days", "batch_days"), ("preferred_time_slot", "batch_start_time")]:
            if str(form.get(form_field, "")).strip().casefold() != str(ref.get(ref_field, "")).strip().casefold():
                findings.append(_finding("FORM_REFERENCE_PREFERENCE_MISMATCH", "MEDIUM",
                                         f"Form {form.get('id')} {form_field} differs from the reference schedule for batch {batch_id}.",
                                         "Confirm whether this is a batch change or preference update; do not overwrite parent intent.",
                                         "Operations + parent", "form", form.get("id")))

    for request in requests:
        batch_id = normalize_identifier(request.get("classbatch_id"))
        if not batch_id:
            continue
        batch_rows = [r for r in refs if normalize_identifier(r.get("current_classbatch_id")) == batch_id]
        if not batch_rows:
            findings.append(_finding("BATCH_NOT_IN_REFERENCE", "MEDIUM",
                                     f"Request {request.get('id')} batch {batch_id} is absent from the reference snapshot.",
                                     "Verify the requested batch in the authoritative batch system.",
                                     "Operations / batch owner", "request", request.get("id")))
            continue
        first = batch_rows[0]
        if not is_present(first.get("max_batch_size")) or not is_present(first.get("active_students_count")):
            findings.append(_finding("BATCH_CAPACITY_DATA_MISSING", "MEDIUM",
                                     f"Batch {batch_id} has missing active count or maximum capacity in the reference snapshot.",
                                     "Refresh capacity from an authoritative batch source; do not infer seats.",
                                     "Operations / batch owner", "request", request.get("id")))
            continue
        try:
            remaining = int(first.get("max_batch_size")) - int(first.get("active_students_count"))
        except (TypeError, ValueError):
            findings.append(_finding("BATCH_CAPACITY_DATA_INVALID", "MEDIUM",
                                     f"Batch {batch_id} capacity counts are not valid integers.",
                                     "Verify the capacity values with the batch owner.",
                                     "Operations / batch owner", "request", request.get("id")))
            continue
        if remaining <= 0:
            if policy.get("reference_capacity_authoritative", False):
                findings.append(_finding("BATCH_CONFIRMED_FULL", "HIGH",
                                         f"Batch {batch_id} has {remaining} calculated seats in a policy-authoritative snapshot.",
                                         "Do not assign this batch; get parent choice for an alternative.",
                                         "Operations / batch owner", "request", request.get("id")))
            else:
                findings.append(_finding("BATCH_CAPACITY_UNCONFIRMED", "MEDIUM",
                                         f"Reference batch {batch_id} calculates to {remaining} remaining seats, but policy marks the snapshot non-authoritative.",
                                         "Refresh live capacity and obtain a seat hold; do not call this a confirmed allocation failure.",
                                         "Operations / batch owner", "request", request.get("id")))

    # Deduplicate identical findings created by overlapping checks while retaining distinct record IDs.
    unique: dict[tuple[str, str, str], dict[str, str]] = {}
    for item in findings:
        key = (item["reason_code"], item["source_type"], item["source_record_id"])
        unique.setdefault(key, item)
    findings = list(unique.values())

    eligibility_findings = [x for x in findings if x["reason_code"] in ELIGIBILITY_REASON_CODES]
    hard_codes = set(policy.get("hard_block_reason_codes", ["PAYMENT_FAILED", "FORM_INVOICE_ID_NOT_FOUND"]))
    blocking = [x for x in eligibility_findings if x["reason_code"] in hard_codes]
    if blocking:
        outcome = "BLOCKED"
        chosen = blocking[0]
    elif _auto_gates_pass(case, eligibility_findings, policy):
        outcome = "AUTO_APPROVED"
        chosen = None
    else:
        outcome = "NEEDS_HUMAN_REVIEW"
        material_findings = [x for x in eligibility_findings if x.get("severity") != "INFO"]
        ordered = sorted(material_findings, key=lambda x: REASON_ORDER.index(x["reason_code"]) if x["reason_code"] in REASON_ORDER else len(REASON_ORDER))
        chosen = ordered[0] if ordered else None

    if chosen:
        reason, explanation, action, owner = chosen["reason_code"], chosen["evidence"], chosen["recommended_action"], chosen["owner"]
    elif outcome == "AUTO_APPROVED":
        reason, explanation = "AUTO_EXACT_MATCH_VERIFIED_SETTLEMENT", "All configured prototype auto-approval gates passed."
        action, owner = "Record the decision only; this prototype does not create booking or schedule records.", "Workflow service"
    elif requests or schedules:
        reason, explanation = "EXISTING_BOOKING_NO_WRITE", "An exact-linked booking or schedule already exists; no new record should be created by this read-only run."
        action, owner = "Preserve source records; compare full authoritative schedule state before any repair.", "Operations"
    elif not policy.get("auto_approval_enabled", False):
        reason, explanation = "AUTO_APPROVAL_DISABLED", "No material data exception was found, but auto approval is disabled pending business policy sign-off."
        action, owner = "Review the candidate and obtain policy sign-off; no booking or schedule write is made.", "Operations + Finance"
    else:
        reason, explanation = "AUTO_APPROVAL_GATES_NOT_MET", "No configured exception was found, but one or more evidence gates required for automatic approval are unavailable or false."
        action, owner = "Supply verified payment, explicit parent choice, active-student and authoritative capacity evidence before enabling automation.", "Operations + Finance"

    return _decision(case, outcome, findings, policy, reason, explanation, action, owner)


def _decision(case: dict[str, Any], outcome: str, findings: list[dict[str, str]], policy: dict[str, Any],
              reason: str, explanation: str, action: str, owner: str) -> dict[str, Any]:
    invoice = case.get("invoice") or {}
    forms = case.get("forms", [])
    requests = case.get("requests", [])
    schedules = case.get("schedules", [])
    refs = case.get("reference_rows", [])
    invoice_id = normalize_identifier(invoice.get("id")) or normalize_identifier(case.get("invoice_id"))
    form_ids = sorted({normalize_identifier(x.get("id")) for x in forms if normalize_identifier(x.get("id"))})
    request_ids = sorted({normalize_identifier(x.get("id")) for x in requests if normalize_identifier(x.get("id"))})
    schedule_ids = sorted({normalize_identifier(x.get("id")) for x in schedules if normalize_identifier(x.get("id"))})
    student_id = normalize_identifier(invoice.get("student_id")) or (normalize_identifier(forms[0].get("student_id")) if forms else "")
    case_id = case.get("case_id") or _stable_id("CASE", case.get("case_type"), invoice_id, ",".join(form_ids), case.get("source_record_id", ""))
    decision_id = _stable_id("DEC", case_id)
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    payment_cfg = policy.get("payment", {})
    gates = policy.get("auto_approval_gates", {})
    evidence_fields = {
        "invoice": ["id", "student_id", "user_id", "class_id", "educator_id",
                    "payment_status", "is_renewal", gates.get("payment_verified_field", "gateway_verified"),
                    payment_cfg.get("settled_amount_field", "gateway_settled_amount"),
                    payment_cfg.get("settled_currency_field", "gateway_settled_currency"),
                    payment_cfg.get("evidence_id_field", "payment_evidence_id"),
                    payment_cfg.get("evidence_source_field", "payment_evidence_source"),
                    payment_cfg.get("invoice_comparison_field", "net_amount")],
        "forms": ["id", "invoice_id", "student_id", "user_id", "class_id", "educator_id",
                  "approval_status",
                  payment_cfg.get("form_amount_field", "amount_paid"),
                  gates.get("parent_choice_confirmed_field", "parent_batch_choice_confirmed"),
                  policy.get("stage_readiness", {}).get("booking_request", {}).get("parent_choice_evidence_id_field", "parent_choice_evidence_id"),
                  "sessions_purchased", "continue_same_batch", "preferred_days", "preferred_time_slot",
                  "current_classbatch_id", "classbatch_id"],
        "requests": ["id", "faculty_form_id", "invoice_id", "student_id", "user_id", "class_id",
                     "educator_id", "request_status", "batch_allocated", "sessions_count",
                     "continue_same_batch", "preferred_days", "preferred_time", "classbatch_id",
                      "parent_batch_choice_confirmed", "parent_choice_evidence_id", "capacity_confirmed",
                      "capacity_available", "capacity_evidence_id", "seat_hold_id",
                      "schedule_parameters_verified", "schedule_parameters_evidence_id", "schedule_parameters_json"],
        "schedules": ["id", "bookingrequest_id", "student_id", "user_id", "class_id",
                      "educator_id", "classbatch_id",
                      "classschedule_id", "class_date", "start_time", "end_time", "is_cancelled"],
        "reference": ["student_id", "user_id", "class_id", "educator_id", "current_classbatch_id",
                      "classbatch_id", gates.get("student_active_field", "student_active"),
                      "active_students_count", "max_batch_size", "batch_days", "batch_start_time"],
    }

    def selected(row: dict[str, Any], keys: list[str]) -> dict[str, Any]:
        # Keep only operational identifiers and decision evidence; omit names, contact
        # details, free-text notes, and any other unnecessary personal data.
        return {key: row.get(key) for key in dict.fromkeys(keys) if key in row}

    audit_evidence = {
        "source_values": {
            "invoice": selected(invoice, evidence_fields["invoice"]),
            "forms": [selected(row, evidence_fields["forms"]) for row in forms],
            "booking_requests": [selected(row, evidence_fields["requests"]) for row in requests],
            "schedule_rows": [selected(row, evidence_fields["schedules"]) for row in schedules],
            "student_batch_reference": [selected(row, evidence_fields["reference"]) for row in refs],
        },
        "finding_codes": [x["reason_code"] for x in findings],
    }
    return {
        "case_id": case_id,
        "decision_id": decision_id,
        "case_type": case.get("case_type", "invoice_renewal"),
        "invoice_id": invoice_id,
        "form_ids": ";".join(form_ids),
        "booking_request_ids": ";".join(request_ids),
        "schedule_row_ids": ";".join(schedule_ids),
        "student_id": student_id,
        "decision_outcome": outcome,
        "reason_code": reason,
        "explanation": explanation,
        "recommended_next_action": action,
        "responsible_owner": owner,
        "evidence": json.dumps(audit_evidence, sort_keys=True),
        "policy_version": policy.get("policy_version", "unspecified"),
        "evaluated_at_utc": timestamp,
        "automatic_decision": outcome == "AUTO_APPROVED",
        "requires_human_action": outcome != "AUTO_APPROVED",
        "prototype_only": True,
        "findings": findings,
    }


def _add_form_status_finding(findings: list[dict[str, str]], form: dict[str, Any]) -> None:
    """Record non-approved form states for Operations without inventing transitions."""
    status = _text(form, "approval_status")
    normalized = status.casefold()
    form_id = form.get("id")
    if normalized == "approved":
        return
    if normalized == "pending":
        code, severity, detail = "FORM_PENDING", "MEDIUM", "is Pending and requires an Operations approval decision."
    elif normalized == "rejected":
        code, severity, detail = "FORM_REJECTED", "HIGH", "is Rejected; confirm the authorized disposition before progression."
    elif not normalized:
        code, severity, detail = "FORM_APPROVAL_STATUS_MISSING", "HIGH", "has no approval_status value; verify it with Operations."
    else:
        code, severity, detail = "FORM_APPROVAL_STATUS_UNKNOWN", "HIGH", f"has unrecognized approval_status={status!r}; verify it with Operations."
    findings.append(_finding(
        code, severity, f"Form {form_id} {detail}",
        "Operations must verify or record the authorized form decision; do not change the status or create a booking request automatically.",
        "Operations", "form", form_id,
    ))
