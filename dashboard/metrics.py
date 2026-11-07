"""Read-only data loading and exact-ID metrics for the Operations dashboard."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs"

INPUT_COLUMNS = {
    "invoices": ("1_invoices.csv", ["id", "student_id", "payment_status", "is_renewal", "paid_at"]),
    "forms": ("2_faculty_form_unapproved.csv", [
        "id", "invoice_id", "student_id", "approval_status", "amount_paid",
        "current_classbatch_id", "continue_same_batch", "created_at", "approved_at",
    ]),
    "requests": ("3_booking_requests.csv", [
        "id", "faculty_form_id", "invoice_id", "student_id", "request_status",
        "batch_allocated", "classbatch_id", "created_at", "allocated_at",
    ]),
    "schedules": ("4_class_schedule_bookings.csv", [
        "id", "bookingrequest_id", "class_date", "classbatch_id", "is_cancelled", "created_at",
    ]),
    "reference": ("reference_active_batches_and_students.csv", [
        "student_id", "current_classbatch_id", "active_students_count", "max_batch_size",
    ]),
}

OUTPUT_COLUMNS = {
    "results": [
        "case_id", "decision_id", "invoice_id", "form_ids", "booking_request_ids",
        "student_id", "decision_outcome", "reason_code", "policy_version",
    ],
    "exceptions": [
        "exception_id", "source_record_type", "source_record_id", "invoice_id", "form_ids",
        "booking_request_ids", "student_id", "decision_outcome", "reason_code", "severity",
        "recommended_owner", "recommended_action",
    ],
    "audit": ["input_file_sha256"],
}

ID_COLUMNS = {
    "invoices": ["id", "student_id"],
    "forms": ["id", "invoice_id", "student_id", "current_classbatch_id"],
    "requests": ["id", "faculty_form_id", "invoice_id", "student_id", "classbatch_id"],
    "schedules": ["id", "bookingrequest_id", "classbatch_id"],
    "reference": ["student_id", "current_classbatch_id"],
}


PROPOSED_SLAS = [
    {
        "service_measure": "Ingestion and deterministic validation",
        "proposed_target": "95% of valid gateway events staged and checked within 5 minutes",
        "owner": "Systems owner",
    },
    {
        "service_measure": "Paid renewal with no form",
        "proposed_target": "Alert within 15 minutes; first review within 2 business hours; escalate at 12 elapsed hours",
        "owner": "Operations + assigned educator",
    },
    {
        "service_measure": "Payment/amount exception",
        "proposed_target": "Finance first review within 2 business hours; resolution target 1 business day, excluding external investigation",
        "owner": "Finance",
    },
    {
        "service_measure": "Duplicate form reference",
        "proposed_target": "Triage within 4 business hours; no downstream write until disposition",
        "owner": "Operations",
    },
    {
        "service_measure": "Complete form approval",
        "proposed_target": "95% of fully evidenced, eligible cases resolved within 2 business hours",
        "owner": "Operations",
    },
    {
        "service_measure": "Same-batch booking after verified approval",
        "proposed_target": "Booking request and seat hold within 15 minutes; schedule remains a separate step",
        "owner": "Scheduling Operations",
    },
    {
        "service_measure": "Parent batch selection",
        "proposed_target": "Send options within 15 minutes; reminder after 24 hours; escalate after 2 business days",
        "owner": "Operations; parent owns selection",
    },
    {
        "service_measure": "Exception resolution",
        "proposed_target": "90% of Ops-controlled cases closed within 1 business day; report external waits separately",
        "owner": "Named queue owner",
    },
]


def normalize_id(value: Any) -> str:
    """Normalize numeric CSV identifiers without fuzzy or student-only matching."""
    if value is None or pd.isna(value):
        return ""
    text = str(value).strip()
    if text.endswith(".0") and text[:-2].isdigit():
        return text[:-2]
    return text


def _read_csv(path: Path, columns: list[str], id_columns: list[str] | None = None) -> pd.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(f"Required dashboard input is missing: {path}")
    dtypes = {column: "string" for column in (id_columns or [])}
    return pd.read_csv(path, usecols=columns, dtype=dtypes)


def load_dashboard_data(
    data_dir: str | Path = DEFAULT_DATA_DIR,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
    """Load only required operational fields; names and contact details are never read."""
    data_dir, output_dir = Path(data_dir), Path(output_dir)
    data: dict[str, Any] = {}
    for key, (filename, columns) in INPUT_COLUMNS.items():
        data[key] = _read_csv(data_dir / filename, columns, ID_COLUMNS[key])

    for key, filename in (
        ("results", "reconciliation_results.csv"),
        ("exceptions", "exception_report.csv"),
        ("audit", "audit_log.csv"),
    ):
        path = output_dir / filename
        data[key] = _read_csv(path, OUTPUT_COLUMNS[key], ID_COLUMNS.get(key, [])) if path.is_file() else pd.DataFrame(columns=OUTPUT_COLUMNS[key])
    return data


def compute_kpis(data: dict[str, Any]) -> dict[str, int | str]:
    """Compute observed/derived snapshot counts using exact identifier equality."""
    invoices = data["invoices"]
    forms = data["forms"]
    requests = data["requests"]
    schedules = data["schedules"]

    paid_renewal = invoices[
        invoices.payment_status.fillna("").astype(str).str.strip().str.casefold().eq("paid")
        & invoices.is_renewal.fillna("").astype(str).str.strip().str.casefold().eq("yes")
    ]
    paid_invoice_ids = {normalize_id(value) for value in paid_renewal.id if normalize_id(value)}
    form_invoice_ids = {normalize_id(value) for value in forms.invoice_id if normalize_id(value)}

    request_form_ids = {normalize_id(value) for value in requests.faculty_form_id if normalize_id(value)}
    request_ids = {normalize_id(value) for value in requests.id if normalize_id(value)}
    scheduled_request_ids = {normalize_id(value) for value in schedules.bookingrequest_id if normalize_id(value)}

    pending_forms = forms.approval_status.fillna("").astype(str).str.strip().str.casefold().eq("pending")
    approved_forms = forms.approval_status.fillna("").astype(str).str.strip().str.casefold().eq("approved")
    approved_without_request = 0
    for row in forms.loc[approved_forms].itertuples(index=False):
        form_id = normalize_id(row.id)
        if form_id and form_id not in request_form_ids:
            approved_without_request += 1

    request_status = requests.request_status.fillna("").astype(str).str.strip()
    return {
        "paid_renewal_invoices": len(paid_invoice_ids),
        "paid_renewals_without_exact_form": len(paid_invoice_ids - form_invoice_ids),
        "pending_teacher_forms": int(pending_forms.sum()),
        "approved_forms_without_booking_request": approved_without_request,
        "requests_awaiting_batch_allocation": int(request_status.eq("Pending_Batch_Allocation").sum()),
        "failed_batch_allocation_requests": int(request_status.eq("Failed_Batch_Full").sum()),
        "requests_without_schedule": len(request_ids - scheduled_request_ids),
        "hours_saved": "Not yet measurable",
    }


def build_funnel(data: dict[str, Any]) -> pd.DataFrame:
    """Return raw table row counts with relationship context for the four stages."""
    invoices, forms = data["invoices"], data["forms"]
    requests, schedules = data["requests"], data["schedules"]
    paid = compute_kpis(data)["paid_renewal_invoices"]
    exact_paid_forms = len({
        normalize_id(value)
        for value in invoices.loc[
            invoices.payment_status.fillna("").astype(str).str.strip().str.casefold().eq("paid")
            & invoices.is_renewal.fillna("").astype(str).str.strip().str.casefold().eq("yes"), "id"
        ]
        if normalize_id(value) in {normalize_id(x) for x in forms.invoice_id}
    })
    linked_requests = sum(
        normalize_id(value) in {normalize_id(x) for x in forms.id}
        for value in requests.faculty_form_id
        if normalize_id(value)
    )
    requests_with_schedule = len({normalize_id(value) for value in schedules.bookingrequest_id if normalize_id(value)})
    return pd.DataFrame([
        {"stage": "Invoices", "records": len(invoices), "context": f"{paid} paid renewal invoices in this snapshot"},
        {"stage": "Teacher forms", "records": len(forms), "context": f"{exact_paid_forms} of {paid} paid renewals have an exact invoice link"},
        {"stage": "Booking requests", "records": len(requests), "context": f"{linked_requests} request rows link to a form by exact form ID"},
        {"stage": "Class schedule rows", "records": len(schedules), "context": f"Rows link to {requests_with_schedule} booking request(s); a row is a class occurrence"},
    ])


def group_exceptions(exceptions: pd.DataFrame) -> pd.DataFrame:
    """Group by the original reason code only; keep all owners/actions visible."""
    columns = ["reason_code", "count", "severity", "responsible_team", "recommended_next_action"]
    if exceptions.empty:
        return pd.DataFrame(columns=columns)

    def unique_text(series: pd.Series) -> str:
        values = list(dict.fromkeys(str(value).strip() for value in series.dropna() if str(value).strip()))
        return "\n".join(values)

    grouped = (
        exceptions.groupby("reason_code", dropna=False, sort=False)
        .agg(
            count=("exception_id", "count"),
            severity=("severity", unique_text),
            responsible_team=("recommended_owner", unique_text),
            recommended_next_action=("recommended_action", unique_text),
        )
        .reset_index()
    )
    return grouped.sort_values(["count", "reason_code"], ascending=[False, True]).reset_index(drop=True)


def build_action_queue(data: dict[str, Any]) -> pd.DataFrame:
    """Enrich existing exception rows with current status/stage from exact linked IDs."""
    exceptions = data["exceptions"]
    columns = [
        "invoice_id", "teacher_form_id", "booking_request_id", "student_id", "current_stage",
        "status", "exception_reason", "severity", "suggested_owner", "recommended_next_action",
    ]
    if exceptions.empty:
        return pd.DataFrame(columns=columns)

    invoices = {normalize_id(row.id): row for row in data["invoices"].itertuples(index=False) if normalize_id(row.id)}
    forms: dict[str, Any] = {}
    for row in data["forms"].itertuples(index=False):
        key = normalize_id(row.id)
        if key:
            forms[key] = row
    requests: dict[str, Any] = {}
    for row in data["requests"].itertuples(index=False):
        key = normalize_id(row.id)
        if key:
            requests[key] = row
    schedules_by_request: dict[str, list[Any]] = {}
    for row in data["schedules"].itertuples(index=False):
        schedules_by_request.setdefault(normalize_id(row.bookingrequest_id), []).append(row)

    output: list[dict[str, Any]] = []
    for item in exceptions.itertuples(index=False):
        invoice_id = normalize_id(item.invoice_id)
        raw_form_ids = "" if item.form_ids is None or pd.isna(item.form_ids) else str(item.form_ids)
        raw_request_ids = "" if item.booking_request_ids is None or pd.isna(item.booking_request_ids) else str(item.booking_request_ids)
        form_ids = [value for value in (normalize_id(x) for x in raw_form_ids.split(";")) if value]
        if not form_ids and str(item.source_record_type) == "form":
            source_form_id = normalize_id(item.source_record_id)
            if source_form_id:
                form_ids = [source_form_id]
        request_ids = [value for value in (normalize_id(x) for x in raw_request_ids.split(";")) if value]

        invoice = invoices.get(invoice_id)
        linked_forms = [forms[value] for value in form_ids if value in forms]
        linked_requests = [requests[value] for value in request_ids if value in requests]
        linked_schedules = [
            schedule
            for request_id in request_ids
            for schedule in schedules_by_request.get(request_id, [])
        ]

        status_parts: list[str] = []
        if invoice is not None:
            status_parts.append(f"Invoice: {invoice.payment_status}")
        elif invoice_id:
            status_parts.append("Invoice ID not found in extract")
        status_parts.extend(f"Form {normalize_id(row.id)}: {row.approval_status}" for row in linked_forms)
        status_parts.extend(f"Request {normalize_id(row.id)}: {row.request_status}" for row in linked_requests)
        if linked_schedules:
            status_parts.append(f"{len(linked_schedules)} schedule row(s)")
        elif linked_requests:
            status_parts.append("No schedule row in extract")

        if linked_schedules:
            stage = "Class schedule"
        elif linked_requests:
            stage = "Booking request"
        elif linked_forms:
            stage = "Teacher form"
        elif invoice is not None:
            stage = "Invoice"
        else:
            stage = "Unresolved reference"

        output.append({
            "invoice_id": invoice_id,
            "teacher_form_id": "; ".join(form_ids),
            "booking_request_id": "; ".join(request_ids),
            "student_id": normalize_id(item.student_id),
            "current_stage": stage,
            "status": " | ".join(status_parts) or "Status unavailable",
            "exception_reason": str(item.reason_code),
            "severity": str(item.severity),
            "suggested_owner": str(item.recommended_owner),
            "recommended_next_action": str(item.recommended_action),
        })
    return pd.DataFrame(output, columns=columns)


def input_hashes(data_dir: str | Path = DEFAULT_DATA_DIR) -> dict[str, str]:
    data_dir = Path(data_dir)
    return {
        filename: hashlib.sha256((data_dir / filename).read_bytes()).hexdigest()
        for filename, _ in INPUT_COLUMNS.values()
    }


def reconciliation_snapshot_matches(data: dict[str, Any], data_dir: str | Path = DEFAULT_DATA_DIR) -> bool:
    """Check whether existing reconciliation outputs were generated from these CSVs."""
    audit = data["audit"]
    if audit.empty or not str(audit.iloc[0].get("input_file_sha256", "")).strip():
        return False
    if audit.input_file_sha256.dropna().astype(str).nunique() != 1:
        return False
    try:
        stored = json.loads(str(audit.iloc[0]["input_file_sha256"]))
    except (json.JSONDecodeError, TypeError):
        return False
    return stored == input_hashes(data_dir)

