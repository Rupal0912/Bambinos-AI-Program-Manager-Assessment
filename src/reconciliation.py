"""Read-only CSV reconciliation runner for the Bambinos renewal prototype."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from decision_engine import _stable_id, evaluate_case, evaluate_stage_readiness
from validators import FILE_NAMES, InputValidationError, load_datasets, normalize_identifier


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data"
DEFAULT_OUTPUT = ROOT / "outputs"
DEFAULT_POLICY = ROOT / "config" / "policy.json"

STAGE_REPORT_COLUMNS = [
    "case_id", "decision_id", "invoice_id", "teacher_form_id", "booking_request_id",
    "renewal_eligibility_status", "booking_request_readiness_status",
    "scheduling_readiness_status", "exclusion_reason_codes", "evidence_status_json",
    "policy_version", "evaluated_at_utc", "input_snapshot_sha256",
]

SCHEDULING_READY_COLUMNS = [
    "readiness_id", "case_id", "decision_id", "invoice_id", "teacher_form_id",
    "booking_request_id", "student_id", "user_id", "class_id", "educator_id",
    "classbatch_id", "schedule_instance_key", "class_date", "start_time", "end_time",
    "timezone", "payment_evidence_id", "parent_choice_evidence_id", "capacity_evidence_id",
    "seat_hold_id", "verified_settled_amount", "currency", "policy_version",
    "evaluated_at_utc", "input_snapshot_sha256",
]


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    # Converting nulls to None keeps evidence JSON serializable and comparisons safe.
    return [row.where(pd.notna(row), None).to_dict() for _, row in frame.iterrows()]


def _index(rows: list[dict[str, Any]], field: str) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        key = normalize_identifier(row.get(field))
        if key:
            result.setdefault(key, []).append(row)
    return result


def build_cases(datasets: dict[str, pd.DataFrame], policy: dict[str, Any]) -> list[dict[str, Any]]:
    """Create renewal cases using only the exact ID relationships in the source columns."""
    invoices = _records(datasets["invoices"])
    forms = _records(datasets["forms"])
    requests = _records(datasets["requests"])
    schedules = _records(datasets["schedules"])
    reference = _records(datasets["reference"])
    invoice_by_id = _index(invoices, "id")
    forms_by_invoice = _index(forms, "invoice_id")
    request_by_form = _index(requests, "faculty_form_id")
    request_by_id = _index(requests, "id")
    schedules_by_request = _index(schedules, "bookingrequest_id")
    refs_by_student = _index(reference, "student_id")
    cases: list[dict[str, Any]] = []
    renewal_value = str(policy.get("eligibility", {}).get("renewal_value", "Yes")).casefold()

    for invoice in invoices:
        if str(invoice.get("is_renewal", "")).strip().casefold() != renewal_value:
            continue
        invoice_id = normalize_identifier(invoice.get("id"))
        matched_forms = forms_by_invoice.get(invoice_id, [])
        linked_requests: list[dict[str, Any]] = []
        for form in matched_forms:
            linked_requests.extend(request_by_form.get(normalize_identifier(form.get("id")), []))
        linked_schedules: list[dict[str, Any]] = []
        for request in linked_requests:
            linked_schedules.extend(schedules_by_request.get(normalize_identifier(request.get("id")), []))
        student_id = normalize_identifier(invoice.get("student_id"))
        case = {
            "case_type": "invoice_renewal",
            "invoice_id": invoice_id,
            "source_record_id": invoice_id,
            "invoice": invoice,
            "forms": matched_forms,
            "requests": linked_requests,
            "schedules": linked_schedules,
            "reference_rows": refs_by_student.get(student_id, []),
        }
        case["case_id"] = _stable_id("CASE", "invoice_renewal", invoice_id)
        cases.append(case)

    # Keep dangling forms visible as their own blocked cases. Do not repair via student ID.
    known_invoice_ids = set(invoice_by_id)
    for form in forms:
        invoice_id = normalize_identifier(form.get("invoice_id"))
        if invoice_id in known_invoice_ids:
            continue
        form_id = normalize_identifier(form.get("id"))
        student_id = normalize_identifier(form.get("student_id"))
        case = {
            "case_type": "unmatched_form",
            "invoice_id": invoice_id,
            "source_record_id": form_id,
            "invoice": None,
            "forms": [form],
            "requests": request_by_form.get(form_id, []),
            "schedules": [],
            "reference_rows": refs_by_student.get(student_id, []),
        }
        case["case_id"] = _stable_id("CASE", "unmatched_form", invoice_id, form_id)
        cases.append(case)

    # Orphan requests/schedules are included even if no matching upstream case exists.
    known_form_ids = {normalize_identifier(x.get("id")) for x in forms}
    for request in requests:
        if normalize_identifier(request.get("faculty_form_id")) in known_form_ids:
            continue
        request_id = normalize_identifier(request.get("id"))
        invoice_id = normalize_identifier(request.get("invoice_id"))
        invoice = (invoice_by_id.get(invoice_id) or [None])[0]
        req_schedules = schedules_by_request.get(request_id, [])
        case = {
            "case_type": "orphan_request", "invoice_id": invoice_id,
            "source_record_id": request_id, "invoice": invoice, "forms": [],
            "requests": [request], "schedules": req_schedules,
            "reference_rows": refs_by_student.get(normalize_identifier(request.get("student_id")), []),
        }
        case["case_id"] = _stable_id("CASE", "orphan_request", request_id)
        cases.append(case)

    for schedule in schedules:
        request_id = normalize_identifier(schedule.get("bookingrequest_id"))
        if request_id in request_by_id:
            continue
        schedule_id = normalize_identifier(schedule.get("id"))
        invoice_id = normalize_identifier(schedule.get("invoice_id"))
        invoice = (invoice_by_id.get(invoice_id) or [None])[0]
        case = {
            "case_type": "orphan_schedule", "invoice_id": invoice_id,
            "source_record_id": schedule_id, "invoice": invoice, "forms": [],
            "requests": [], "schedules": [schedule],
            "reference_rows": refs_by_student.get(normalize_identifier(schedule.get("student_id")), []),
        }
        case["case_id"] = _stable_id("CASE", "orphan_schedule", schedule_id)
        cases.append(case)

    return cases


def _draft_message(reason_code: str, row: dict[str, Any]) -> str:
    """Create a draft only; this function never sends communications."""
    inv = row.get("invoice_id") or "{{invoice_id}}"
    form_ids = row.get("form_ids") or "{{form_id}}"
    student = row.get("student_id") or "{{student_id}}"
    drafts = {
        "PAID_RENEWAL_NO_EXACT_FORM": f"Draft to teacher: A renewal payment is recorded for invoice {inv}, but we could not find a matching form. Please check the renewal record for student {student} and confirm the correct form reference. Do not resend payment details in chat.",
        "PAYMENT_PARTIAL_POLICY_REVIEW": f"Draft to parent: We are checking the payment associated with invoice {inv}. Operations will confirm its status before class scheduling continues; this message is not a new payment request.",
        "PAYMENT_AMOUNT_CONFLICT": f"Draft to Finance/Ops: Please verify the settled amount and amount rule for invoice {inv}; the form and invoice values differ.",
        "DUPLICATE_FORM_INVOICE_REFERENCE": f"Draft to teacher: We found multiple renewal forms ({form_ids}) linked to invoice {inv}. Operations is reviewing them; please do not submit another form yet.",
        "REQUEST_FAILED_BATCH_FULL": f"Draft to parent: The requested batch for invoice {inv} is reported as unavailable. Please choose from confirmed alternatives; we will confirm only after a place is secured.",
        "PARENT_BATCH_SELECTION_PENDING": f"Draft to parent: Please choose a batch for the renewal linked to invoice {inv}. Classes are not scheduled until your choice and availability are confirmed.",
    }
    return drafts.get(reason_code, "")


def _flatten_findings(decisions: list[dict[str, Any]]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for decision in decisions:
        for finding in decision.pop("findings", []):
            source_type = finding.get("source_type", "case")
            rows.append({
                "exception_id": _stable_id("EXC", decision["case_id"], finding["reason_code"], source_type,
                                           finding.get("source_record_id", "")),
                "decision_id": decision["decision_id"],
                "source_record_type": source_type,
                "source_record_id": finding.get("source_record_id", ""),
                "invoice_id": decision["invoice_id"],
                "form_ids": decision["form_ids"],
                "booking_request_ids": decision["booking_request_ids"],
                "student_id": decision["student_id"],
                "decision_outcome": decision["decision_outcome"],
                "exception_category": finding["reason_code"],
                "reason_code": finding["reason_code"],
                "evidence": finding["evidence"],
                "severity": finding["severity"],
                "recommended_owner": finding["owner"],
                "recommended_action": finding["recommended_action"],
                "draft_message": _draft_message(finding["reason_code"], decision),
                "policy_version": decision["policy_version"],
                "prototype_only": True,
            })
    return pd.DataFrame(rows)


def _audit_frame(decisions: list[dict[str, Any]], input_hashes: dict[str, str]) -> pd.DataFrame:
    hash_json = json.dumps(input_hashes, sort_keys=True, separators=(",", ":"))
    snapshot_hash = hashlib.sha256(hash_json.encode("utf-8")).hexdigest()
    rows = []
    for d in decisions:
        rows.append({
            "decision_id": d["decision_id"],
            "case_id": d["case_id"],
            "case_type": d["case_type"],
            "invoice_id": d["invoice_id"],
            "form_ids": d["form_ids"],
            "booking_request_ids": d["booking_request_ids"],
            "schedule_row_ids": d["schedule_row_ids"],
            "decision_outcome": d["decision_outcome"],
            "reason_code": d["reason_code"],
            "evidence": d["evidence"],
            "input_file_sha256": hash_json,
            "input_snapshot_sha256": snapshot_hash,
            "policy_version": d["policy_version"],
            "timestamp_utc": d["evaluated_at_utc"],
            "automatic_decision": d["automatic_decision"],
            "requires_human_action": d["requires_human_action"],
            "prototype_only": d["prototype_only"],
        })
    return pd.DataFrame(rows)


def evaluate_cases(cases: list[dict[str, Any]], policy: dict[str, Any],
                   input_hashes: dict[str, str]) -> dict[str, pd.DataFrame]:
    """Evaluate all stages and build output frames without writing or external side effects."""
    hash_json = json.dumps(input_hashes, sort_keys=True, separators=(",", ":"))
    snapshot_hash = hashlib.sha256(hash_json.encode("utf-8")).hexdigest()
    decisions: list[dict[str, Any]] = []
    stage_rows: list[dict[str, Any]] = []
    ready_rows: list[dict[str, Any]] = []
    for case in cases:
        decision = evaluate_case(case, policy)
        stage_row, ready, stage_findings = evaluate_stage_readiness(case, decision, policy, snapshot_hash)
        decision["findings"].extend(stage_findings)
        decisions.append(decision)
        stage_rows.append(stage_row)
        ready_rows.extend(ready)

    results = pd.DataFrame([{k: v for k, v in decision.items() if k != "findings"} for decision in decisions])
    exceptions = _flatten_findings(decisions)
    audit = _audit_frame(decisions, input_hashes)
    stage_report = pd.DataFrame(stage_rows, columns=STAGE_REPORT_COLUMNS)
    scheduling_ready = pd.DataFrame(ready_rows, columns=SCHEDULING_READY_COLUMNS)
    return {
        "results": results,
        "exceptions": exceptions,
        "audit": audit,
        "stage_readiness": stage_report,
        "scheduling_ready": scheduling_ready,
    }


def write_outputs(output_dir: str | Path, outputs: dict[str, pd.DataFrame]) -> None:
    """Replace prototype output artifacts; this function never writes to input data."""
    folder = Path(output_dir)
    folder.mkdir(parents=True, exist_ok=True)
    outputs["results"].to_csv(folder / "reconciliation_results.csv", index=False, encoding="utf-8-sig")
    outputs["exceptions"].to_csv(folder / "exception_report.csv", index=False, encoding="utf-8-sig")
    outputs["audit"].to_csv(folder / "audit_log.csv", index=False, encoding="utf-8-sig")
    outputs["stage_readiness"].to_csv(folder / "stage_readiness_report.csv", index=False, encoding="utf-8-sig")
    outputs["scheduling_ready"].to_csv(folder / "scheduling_ready.csv", index=False, encoding="utf-8-sig")


def _write_summary(path: Path, datasets: dict[str, pd.DataFrame], results: pd.DataFrame,
                   exceptions: pd.DataFrame, stage_readiness: pd.DataFrame,
                   scheduling_ready: pd.DataFrame, policy: dict[str, Any],
                   input_hashes: dict[str, str]) -> None:
    counts = results.decision_outcome.value_counts().to_dict() if len(results) else {}
    hash_json = json.dumps(input_hashes, sort_keys=True, separators=(",", ":"))
    snapshot_hash = hashlib.sha256(hash_json.encode("utf-8")).hexdigest()
    lines = [
        "# Reconciliation Prototype Summary", "",
        "**Prototype only. No live payment, booking, schedule, or messaging action was performed.**",
        "Automatic approval is disabled by default in the policy file.", "",
        "## Run summary", "",
        f"- Evaluated renewal cases: {len(results)}",
        f"- `AUTO_APPROVED`: {counts.get('AUTO_APPROVED', 0)}",
        f"- `NEEDS_HUMAN_REVIEW`: {counts.get('NEEDS_HUMAN_REVIEW', 0)}",
        f"- `BLOCKED`: {counts.get('BLOCKED', 0)}",
        f"- Exception findings: {len(exceptions)}",
        f"- Cases with booking requests ready to create: {(stage_readiness.booking_request_readiness_status == 'READY_TO_CREATE_REQUEST').sum()}",
        f"- Cases ready for `class_schedule_bookings`: {(stage_readiness.scheduling_readiness_status == 'READY_FOR_CLASS_SCHEDULE_BOOKINGS').sum()}",
        f"- Scheduling-ready occurrence rows: {len(scheduling_ready)}",
        f"- Policy version: `{policy.get('policy_version', 'unspecified')}`",
        f"- Input snapshot SHA-256: `{snapshot_hash}`",
        f"- Input rows: invoices={len(datasets['invoices'])}, forms={len(datasets['forms'])}, requests={len(datasets['requests'])}, schedules={len(datasets['schedules'])}, reference={len(datasets['reference'])}",
        "", "## Exception counts by reason code", "",
    ]
    if exceptions.empty:
        lines.append("No exception findings.")
    else:
        lines.extend(["| Reason code | Cases/findings |", "|---|---:|"])
        lines.extend(f"| `{code}` | {count} |" for code, count in exceptions.reason_code.value_counts().sort_index().items())
    lines += [
        "", "## Safety and interpretation", "",
        "- Decisions are deterministic prototype outputs using the configured provisional policy; they are not production approvals.",
        "- Exact IDs are used for joins. No fuzzy/student-only invoice matching is performed.",
        "- `AUTO_APPROVED` means only that configured renewal eligibility checks passed; it does not create a booking request or class schedule. An exactly linked form must have `approval_status=Approved`; Pending and other statuses require Operations review.",
        "- The default policy disables auto approval. The supplied data also lacks payment verification, explicit parent batch-choice confirmation, an explicit student-active field, and authoritative live capacity.",
        "- The reference capacity file is treated as non-authoritative. A full reference count is a review signal, not a confirmed live allocation failure.",
        "- Missing schedule rows and multiple schedule rows are not automatically treated as failure or duplicates. Expected session totals are not inferred.",
        "- Null `deleted_at` is not interpreted as active.",
        "- Draft messages are output text only and are not sent.",
        "- Output CSVs are replaced on each run; stable case/decision/exception IDs prevent duplicate rows on rerun.",
        "- The audit log records source IDs, selected values used by checks, policy version, UTC evaluation time, per-file SHA-256 hashes, and a combined input snapshot hash. This is a stronger prototype audit trail, not production-grade audit storage.",
        "", "## Business rules still requiring confirmation", "",
        "Payment eligibility and source of truth; amount semantics/tolerance; partial payment policy; duplicate-form disposition; status transitions; current student lifecycle; parent choice; live capacity and seat holds; schedule-generation rules; timezone/SLA calendars; and deletion semantics.", "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def run_reconciliation(input_dir: str | Path, output_dir: str | Path,
                       policy_path: str | Path) -> dict[str, pd.DataFrame]:
    """Run validation and reconciliation, overwriting deterministic outputs (never appending)."""
    input_dir, output_dir, policy_path = Path(input_dir), Path(output_dir), Path(policy_path)
    with policy_path.open("r", encoding="utf-8") as stream:
        policy = json.load(stream)
    input_hashes = _hash_inputs(input_dir)
    datasets = load_datasets(input_dir)
    cases = build_cases(datasets, policy)
    outputs = evaluate_cases(cases, policy, input_hashes)
    write_outputs(output_dir, outputs)
    _write_summary(output_dir / "reconciliation_summary.md", datasets, outputs["results"], outputs["exceptions"],
                   outputs["stage_readiness"], outputs["scheduling_ready"], policy, input_hashes)
    return outputs


def _hash_inputs(input_dir: Path) -> dict[str, str]:
    hashes = {}
    for filename in FILE_NAMES.values():
        path = input_dir / filename
        hashes[filename] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the read-only renewal reconciliation prototype.")
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    args = parser.parse_args(argv)
    try:
        before = _hash_inputs(args.input_dir)
        outputs = run_reconciliation(args.input_dir, args.output_dir, args.policy)
        after = _hash_inputs(args.input_dir)
        if before != after:
            raise RuntimeError("Input hash changed during run; original files may have been altered.")
    except (InputValidationError, OSError, json.JSONDecodeError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    results = outputs["results"]
    print(f"Processed {len(results)} cases. Outputs written to {args.output_dir}.")
    print(results.decision_outcome.value_counts().reindex(
        ["AUTO_APPROVED", "NEEDS_HUMAN_REVIEW", "BLOCKED"], fill_value=0).to_string())
    print("Input SHA-256 hashes were unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
