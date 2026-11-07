"""Input and field validators for the read-only renewal prototype."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import pandas as pd


REQUIRED_COLUMNS: dict[str, set[str]] = {
    "invoices": {
        "id", "student_id", "user_id", "class_id", "educator_id", "net_amount",
        "amount", "discount_amount", "currency", "payment_status", "is_renewal",
        "paid_at", "gateway_payment_id", "payment_gateway", "deleted_at",
    },
    "forms": {
        "id", "invoice_id", "student_id", "user_id", "class_id", "educator_id",
        "amount_paid", "sessions_purchased", "current_classbatch_id",
        "continue_same_batch", "preferred_days", "preferred_time_slot",
        "approval_status", "created_at", "approved_at", "deleted_at",
    },
    "requests": {
        "id", "faculty_form_id", "invoice_id", "student_id", "user_id", "class_id",
        "educator_id", "classbatch_id", "sessions_count", "continue_same_batch",
        "preferred_days", "preferred_time", "request_status", "batch_allocated",
        "created_at", "deleted_at",
    },
    "schedules": {
        "id", "bookingrequest_id", "invoice_id", "classschedule_id", "classbatch_id",
        "class_id", "student_id", "user_id", "educator_id", "class_date", "start_time",
        "end_time", "is_cancelled", "created_at", "deleted_at",
    },
    "reference": {
        "student_id", "user_id", "current_classbatch_id", "class_id", "educator_id",
        "standard_fee_24_sessions_inr", "batch_days", "batch_start_time",
        "active_students_count", "max_batch_size", "deleted_at",
    },
}

FILE_NAMES = {
    "invoices": "1_invoices.csv",
    "forms": "2_faculty_form_unapproved.csv",
    "requests": "3_booking_requests.csv",
    "schedules": "4_class_schedule_bookings.csv",
    "reference": "reference_active_batches_and_students.csv",
}


class InputValidationError(ValueError):
    """Raised when a required file or column is missing or unreadable."""


def normalize_identifier(value: Any) -> str:
    """Normalize CSV identifiers without fuzzy matching or losing integer IDs."""
    if value is None or pd.isna(value):
        return ""
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (int,)):
        return str(value)
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    text = str(value).strip()
    if not text:
        return ""
    # pandas may read nullable numeric identifiers as floats; drop a trailing .0.
    try:
        number = Decimal(text)
        if number == number.to_integral_value():
            return str(int(number))
    except InvalidOperation:
        pass
    return text


def is_present(value: Any) -> bool:
    """Return False for nulls and whitespace-only text."""
    if value is None or pd.isna(value):
        return False
    return not (isinstance(value, str) and not value.strip())


def numbers_match(left: Any, right: Any, tolerance: Any = 0) -> bool | None:
    """Compare numeric values; return None when either value is missing/invalid."""
    if not is_present(left) or not is_present(right):
        return None
    try:
        return abs(Decimal(str(left)) - Decimal(str(right))) <= Decimal(str(tolerance))
    except (InvalidOperation, ValueError):
        return None


def load_datasets(input_dir: str | Path) -> dict[str, pd.DataFrame]:
    """Read all required CSVs and fail clearly on missing files/columns."""
    folder = Path(input_dir)
    loaded: dict[str, pd.DataFrame] = {}
    errors: list[str] = []
    for key, filename in FILE_NAMES.items():
        path = folder / filename
        if not path.is_file():
            errors.append(f"Missing input file: {path}")
            continue
        try:
            frame = pd.read_csv(path)
        except Exception as exc:  # includes decoding/parser errors, surfaced with filename
            errors.append(f"Could not read {path}: {exc}")
            continue
        missing = sorted(REQUIRED_COLUMNS[key] - set(frame.columns))
        if missing:
            errors.append(f"{path} is missing required columns: {', '.join(missing)}")
            continue
        loaded[key] = frame
    if errors:
        raise InputValidationError("Input validation failed:\n- " + "\n- ".join(errors))
    return loaded
