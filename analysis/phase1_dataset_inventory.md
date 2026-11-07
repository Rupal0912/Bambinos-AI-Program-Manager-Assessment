# Phase 1 Dataset Inventory

> Source files are read-only. The requested `Bambinos_Hiring_Assessment.pdf` is not present; the assessment source used was `problem_statement/Bambinos_AI_PM_Ops_Take_Home_Case.pdf`. Counts and examples below are computed from the supplied CSVs. Samples mask personal fields in display.

## Assessment requirements extracted from the PDF

- **Business context:** Bambinos.live runs live small-group online classes for children aged 4–16 across India, GCC, and US/UK. Renewals drive revenue and retention. Parents pay to continue to the next term/level, often after a teacher pitch. The manual handoffs can interrupt classes, delay scheduling, frustrate parents, and consume Ops time.
- **Current four-step flow:** (1) parent/payment gateway pays; an invoice row is created. (2) teacher manually submits renewal details into `faculty_form_unapproved`. (3) Operations checks form against invoice/payment, approves, and creates a booking request. (4) parent or Operations selects batch/days/time; schedule booking rows are created.
- **Deliverables:** A. Root-cause problem definition and leakage audit, including failure modes and operational metrics/SLAs. B. AI/no-code redesigned workflow, zero-touch happy path and exception triage. C. Working reconciliation/auto-approval prototype outputting eligible records, coded exceptions, and drafted stakeholder messages. D. Daily Ops dashboard, SOP/change management, and 30-60-90 day plan.
- **Submission requirements:** compulsory PDF case report/deck covering A, B, D; compulsory public/shared GitHub repository with prompts, README, datasets or simulated data, reconciliation results, scripts or workflow exports; optional 2–3 minute Loom walkthrough. Official asset repository and Google Form are listed in the PDF.
- **Evaluation:** four equally weighted dimensions (25% each): problem discovery/edge cases; process re-engineering; AI/no-code execution; data, SLAs, ownership.
- **Constraints/expectations:** 48–72 hour timebox; coding listed as none (AI/no-code/Sheets/SQL logic); live case review with Head of Operations. The prototype brief asks for the five provided CSVs. The PDF mentions four-table data colloquially but explicitly lists five CSVs including the reference file.

## Summary

### `1_invoices.csv`

- **Rows:** 13
- **Columns:** 25
- **Exact columns and pandas-inferred dtypes:**

| Column | dtype | missing values |
|---|---:|---:|
| `id` | `int64` | 0 |
| `invoice_number` | `object` | 0 |
| `user_id` | `int64` | 0 |
| `student_id` | `int64` | 0 |
| `class_id` | `int64` | 0 |
| `educator_id` | `int64` | 0 |
| `parent_name` | `object` | 0 |
| `mobile` | `object` | 0 |
| `email` | `object` | 0 |
| `currency` | `object` | 0 |
| `amount` | `float64` | 0 |
| `discount_amount` | `float64` | 0 |
| `net_amount` | `float64` | 0 |
| `payment_type` | `object` | 0 |
| `payment_mode` | `object` | 0 |
| `payment_gateway` | `object` | 0 |
| `gateway_order_id` | `object` | 0 |
| `gateway_payment_id` | `object` | 1 |
| `invoice_link` | `object` | 0 |
| `payment_status` | `object` | 0 |
| `is_renewal` | `object` | 0 |
| `paid_at` | `object` | 1 |
| `created_at` | `object` | 0 |
| `updated_at` | `object` | 0 |
| `deleted_at` | `float64` | 13 |

- **Exact duplicate rows:** 0
- **Potential primary keys (uniqueness only; semantic confirmation needed):** `id` (13/13 non-null unique), `invoice_number` (13/13 non-null unique), `user_id` (13/13 non-null unique), `student_id` (13/13 non-null unique), `gateway_order_id` (13/13 non-null unique), `gateway_payment_id` (12/12 non-null unique)
- **Date/time fields (column-name based):** `paid_at`, `created_at`, `updated_at`, `deleted_at`
- **Payment-related fields (name-based):** `invoice_number`, `currency`, `amount`, `discount_amount`, `net_amount`, `payment_type`, `payment_mode`, `payment_gateway`, `gateway_order_id`, `gateway_payment_id`, `invoice_link`, `payment_status`, `paid_at`
- **Student/parent-related fields (name-based):** `user_id`, `student_id`, `parent_name`, `mobile`, `email`
- **Batch/teacher/class-related fields (name-based):** `class_id`, `educator_id`

**Five representative records (personal fields masked):**
```json
[
  {
    "id": "INV-A",
    "invoice_number": "BMB-INV-2026-INV-A",
    "user_id": "USER-A",
    "student_id": "STU-A",
    "class_id": "CLASS-A",
    "educator_id": "EDU-A",
    "parent_name": "[masked name]",
    "mobile": "[masked phone]",
    "email": "[masked email]",
    "currency": "INR",
    "amount": "12000.0",
    "discount_amount": "0.0",
    "net_amount": "12000.0",
    "payment_type": "Full",
    "payment_mode": "UPI",
    "payment_gateway": "Razorpay",
    "gateway_order_id": "[GATEWAY-ORDER-ID]",
    "gateway_payment_id": "[GATEWAY-PAYMENT-ID]",
    "invoice_link": "https://bambinos.live/invoice/BMB-INV-2026-INV-A",
    "payment_status": "Paid",
    "is_renewal": "Yes",
    "paid_at": "2026-11-01 10:15:22",
    "created_at": "2026-11-01 10:12:00",
    "updated_at": "2026-11-01 10:15:22",
    "deleted_at": "BATCH-J"
  },
  {
    "id": "INV-B",
    "invoice_number": "BMB-INV-2026-INV-B",
    "user_id": "USER-B",
    "student_id": "STU-B",
    "class_id": "CLASS-B",
    "educator_id": "EDU-B",
    "parent_name": "[masked name]",
    "mobile": "[masked phone]",
    "email": "[masked email]",
    "currency": "INR",
    "amount": "10500.0",
    "discount_amount": "0.0",
    "net_amount": "10500.0",
    "payment_type": "Full",
    "payment_mode": "Card",
    "payment_gateway": "Razorpay",
    "gateway_order_id": "[GATEWAY-ORDER-ID]",
    "gateway_payment_id": "[GATEWAY-PAYMENT-ID]",
    "invoice_link": "https://bambinos.live/invoice/BMB-INV-2026-INV-B",
    "payment_status": "Paid",
    "is_renewal": "Yes",
    "paid_at": "2026-11-01 14:20:10",
    "created_at": "2026-11-01 14:15:00",
    "updated_at": "2026-11-01 14:20:10",
    "deleted_at": "BATCH-J"
  },
  {
    "id": "INV-C",
    "invoice_number": "BMB-INV-2026-INV-C",
    "user_id": "USER-C",
    "student_id": "STU-C",
    "class_id": "CLASS-C",
    "educator_id": "EDU-C",
    "parent_name": "[masked name]",
    "mobile": "[masked phone]",
    "email": "[masked email]",
    "currency": "INR",
    "amount": "9000.0",
    "discount_amount": "0.0",
    "net_amount": "9000.0",
    "payment_type": "Full",
    "payment_mode": "UPI",
    "payment_gateway": "Razorpay",
    "gateway_order_id": "[GATEWAY-ORDER-ID]",
    "gateway_payment_id": "[GATEWAY-PAYMENT-ID]",
    "invoice_link": "https://bambinos.live/invoice/BMB-INV-2026-INV-C",
    "payment_status": "Paid",
    "is_renewal": "Yes",
    "paid_at": "2026-11-02 09:05:44",
    "created_at": "2026-11-02 09:00:12",
    "updated_at": "2026-11-02 09:05:44",
    "deleted_at": "BATCH-J"
  },
  {
    "id": "INV-D",
    "invoice_number": "BMB-INV-2026-INV-D",
    "user_id": "USER-D",
    "student_id": "STU-D",
    "class_id": "CLASS-A",
    "educator_id": "EDU-A",
    "parent_name": "[masked name]",
    "mobile": "[masked phone]",
    "email": "[masked email]",
    "currency": "INR",
    "amount": "12000.0",
    "discount_amount": "0.0",
    "net_amount": "12000.0",
    "payment_type": "Full",
    "payment_mode": "Netbanking",
    "payment_gateway": "Razorpay",
    "gateway_order_id": "[GATEWAY-ORDER-ID]",
    "gateway_payment_id": "[GATEWAY-PAYMENT-ID]",
    "invoice_link": "https://bambinos.live/invoice/BMB-INV-2026-INV-D",
    "payment_status": "Paid",
    "is_renewal": "Yes",
    "paid_at": "2026-11-02 11:30:05",
    "created_at": "2026-11-02 11:25:00",
    "updated_at": "2026-11-02 11:30:05",
    "deleted_at": "BATCH-J"
  },
  {
    "id": "INV-E",
    "invoice_number": "BMB-INV-2026-INV-E",
    "user_id": "USER-E",
    "student_id": "STU-E",
    "class_id": "CLASS-D",
    "educator_id": "EDU-D",
    "parent_name": "[masked name]",
    "mobile": "[masked phone]",
    "email": "[masked email]",
    "currency": "INR",
    "amount": "11000.0",
    "discount_amount": "0.0",
    "net_amount": "11000.0",
    "payment_type": "Full",
    "payment_mode": "UPI",
    "payment_gateway": "Razorpay",
    "gateway_order_id": "[GATEWAY-ORDER-ID]",
    "gateway_payment_id": "[GATEWAY-PAYMENT-ID]",
    "invoice_link": "https://bambinos.live/invoice/BMB-INV-2026-INV-E",
    "payment_status": "Paid",
    "is_renewal": "Yes",
    "paid_at": "2026-11-02 13:10:19",
    "created_at": "2026-11-02 13:05:00",
    "updated_at": "2026-11-02 13:10:19",
    "deleted_at": "BATCH-J"
  }
]
```

### `2_faculty_form_unapproved.csv`

- **Rows:** 12
- **Columns:** 23
- **Exact columns and pandas-inferred dtypes:**

| Column | dtype | missing values |
|---|---:|---:|
| `id` | `int64` | 0 |
| `educator_id` | `int64` | 0 |
| `educator_name` | `object` | 0 |
| `user_id` | `int64` | 0 |
| `student_id` | `int64` | 0 |
| `student_name` | `object` | 0 |
| `parent_mobile` | `object` | 0 |
| `class_id` | `int64` | 0 |
| `current_classbatch_id` | `int64` | 0 |
| `invoice_id` | `int64` | 0 |
| `invoice_link` | `object` | 0 |
| `amount_paid` | `float64` | 0 |
| `sessions_purchased` | `int64` | 0 |
| `continue_same_batch` | `object` | 0 |
| `preferred_days` | `object` | 0 |
| `preferred_time_slot` | `object` | 0 |
| `remarks` | `object` | 0 |
| `approval_status` | `object` | 0 |
| `approved_by` | `object` | 8 |
| `approved_at` | `object` | 8 |
| `created_at` | `object` | 0 |
| `updated_at` | `object` | 0 |
| `deleted_at` | `float64` | 12 |

- **Exact duplicate rows:** 0
- **Potential primary keys (uniqueness only; semantic confirmation needed):** `id` (12/12 non-null unique)
- **Date/time fields (column-name based):** `preferred_time_slot`, `approved_at`, `created_at`, `updated_at`, `deleted_at`
- **Payment-related fields (name-based):** `invoice_id`, `invoice_link`, `amount_paid`
- **Student/parent-related fields (name-based):** `user_id`, `student_id`, `student_name`, `parent_mobile`
- **Batch/teacher/class-related fields (name-based):** `educator_id`, `educator_name`, `class_id`, `current_classbatch_id`, `continue_same_batch`, `preferred_days`, `preferred_time_slot`

**Five representative records (personal fields masked):**
```json
[
  {
    "id": "FORM-A",
    "educator_id": "EDU-A",
    "educator_name": "[masked name]",
    "user_id": "USER-A",
    "student_id": "STU-A",
    "student_name": "[masked name]",
    "parent_mobile": "[masked phone]",
    "class_id": "CLASS-A",
    "current_classbatch_id": "BATCH-A",
    "invoice_id": "INV-A",
    "invoice_link": "https://bambinos.live/invoice/BMB-INV-2026-INV-A",
    "amount_paid": "12000.0",
    "sessions_purchased": "24",
    "continue_same_batch": "Yes",
    "preferred_days": "Tue,Thu",
    "preferred_time_slot": "17:00:00",
    "remarks": "Continue in same batch BATCH-A",
    "approval_status": "Approved",
    "approved_by": "ops_exec_02",
    "approved_at": "2026-11-01 11:30:00",
    "created_at": "2026-11-01 10:45:00",
    "updated_at": "2026-11-01 11:30:00",
    "deleted_at": "BATCH-J"
  },
  {
    "id": "FORM-B",
    "educator_id": "EDU-B",
    "educator_name": "[masked name]",
    "user_id": "USER-B",
    "student_id": "STU-B",
    "student_name": "[masked name]",
    "parent_mobile": "[masked phone]",
    "class_id": "CLASS-B",
    "current_classbatch_id": "BATCH-B",
    "invoice_id": "INV-B",
    "invoice_link": "https://bambinos.live/invoice/BMB-INV-2026-INV-B",
    "amount_paid": "10500.0",
    "sessions_purchased": "24",
    "continue_same_batch": "Yes",
    "preferred_days": "Mon,Wed",
    "preferred_time_slot": "18:00:00",
    "remarks": "Same batch BATCH-B",
    "approval_status": "Approved",
    "approved_by": "ops_exec_01",
    "approved_at": "2026-11-01 17:00:00",
    "created_at": "2026-11-01 15:10:00",
    "updated_at": "2026-11-01 17:00:00",
    "deleted_at": "BATCH-J"
  },
  {
    "id": "FORM-C",
    "educator_id": "EDU-C",
    "educator_name": "[masked name]",
    "user_id": "USER-C",
    "student_id": "STU-C",
    "student_name": "[masked name]",
    "parent_mobile": "[masked phone]",
    "class_id": "CLASS-C",
    "current_classbatch_id": "BATCH-C",
    "invoice_id": "INV-C",
    "invoice_link": "https://bambinos.live/invoice/BMB-INV-2026-INV-C",
    "amount_paid": "9000.0",
    "sessions_purchased": "24",
    "continue_same_batch": "Yes",
    "preferred_days": "Wed,Fri",
    "preferred_time_slot": "16:30:00",
    "remarks": "Continue same batch BATCH-C",
    "approval_status": "Pending",
    "approved_by": "BATCH-J",
    "approved_at": "BATCH-J",
    "created_at": "2026-11-02 09:30:00",
    "updated_at": "2026-11-02 09:30:00",
    "deleted_at": "BATCH-J"
  },
  {
    "id": "FORM-D",
    "educator_id": "EDU-A",
    "educator_name": "[masked name]",
    "user_id": "USER-D",
    "student_id": "STU-D",
    "student_name": "[masked name]",
    "parent_mobile": "[masked phone]",
    "class_id": "CLASS-A",
    "current_classbatch_id": "BATCH-A",
    "invoice_id": "INV-D",
    "invoice_link": "https://bambinos.live/invoice/BMB-INV-2026-INV-D",
    "amount_paid": "12000.0",
    "sessions_purchased": "24",
    "continue_same_batch": "Yes",
    "preferred_days": "Tue,Thu",
    "preferred_time_slot": "17:00:00",
    "remarks": "Mother paid from her number",
    "approval_status": "Pending",
    "approved_by": "BATCH-J",
    "approved_at": "BATCH-J",
    "created_at": "2026-11-02 12:00:00",
    "updated_at": "2026-11-02 12:00:00",
    "deleted_at": "BATCH-J"
  },
  {
    "id": "FORM-E",
    "educator_id": "EDU-D",
    "educator_name": "[masked name]",
    "user_id": "USER-E",
    "student_id": "STU-E",
    "student_name": "[masked name]",
    "parent_mobile": "[masked phone]",
    "class_id": "CLASS-D",
    "current_classbatch_id": "BATCH-D",
    "invoice_id": "INV-E",
    "invoice_link": "https://bambinos.live/invoice/BMB-INV-2026-INV-E",
    "amount_paid": "11000.0",
    "sessions_purchased": "24",
    "continue_same_batch": "Yes",
    "preferred_days": "Sat,Sun",
    "preferred_time_slot": "11:00:00",
    "remarks": "Continue batch BATCH-D",
    "approval_status": "Approved",
    "approved_by": "ops_exec_03",
    "approved_at": "2026-11-02 16:30:00",
    "created_at": "2026-11-02 14:00:00",
    "updated_at": "2026-11-02 16:30:00",
    "deleted_at": "BATCH-J"
  }
]
```

### `3_booking_requests.csv`

- **Rows:** 4
- **Columns:** 20
- **Exact columns and pandas-inferred dtypes:**

| Column | dtype | missing values |
|---|---:|---:|
| `id` | `int64` | 0 |
| `faculty_form_id` | `int64` | 0 |
| `invoice_id` | `int64` | 0 |
| `user_id` | `int64` | 0 |
| `student_id` | `int64` | 0 |
| `class_id` | `int64` | 0 |
| `educator_id` | `int64` | 0 |
| `classbatch_id` | `float64` | 1 |
| `sessions_count` | `int64` | 0 |
| `is_renewal` | `object` | 0 |
| `continue_same_batch` | `object` | 0 |
| `preferred_days` | `object` | 0 |
| `preferred_time` | `object` | 0 |
| `request_status` | `object` | 0 |
| `batch_allocated` | `object` | 0 |
| `allocated_by` | `object` | 3 |
| `allocated_at` | `object` | 3 |
| `created_at` | `object` | 0 |
| `updated_at` | `object` | 0 |
| `deleted_at` | `float64` | 4 |

- **Exact duplicate rows:** 0
- **Potential primary keys (uniqueness only; semantic confirmation needed):** `id` (4/4 non-null unique), `faculty_form_id` (4/4 non-null unique), `invoice_id` (4/4 non-null unique), `user_id` (4/4 non-null unique), `student_id` (4/4 non-null unique), `class_id` (4/4 non-null unique), `educator_id` (4/4 non-null unique), `classbatch_id` (3/3 non-null unique)
- **Date/time fields (column-name based):** `preferred_time`, `allocated_at`, `created_at`, `updated_at`, `deleted_at`
- **Payment-related fields (name-based):** `invoice_id`
- **Student/parent-related fields (name-based):** `user_id`, `student_id`
- **Batch/teacher/class-related fields (name-based):** `class_id`, `educator_id`, `classbatch_id`, `continue_same_batch`, `preferred_days`, `preferred_time`, `batch_allocated`

**Five representative records (personal fields masked):**
```json
[
  {
    "id": "REQ-A",
    "faculty_form_id": "FORM-A",
    "invoice_id": "INV-A",
    "user_id": "USER-A",
    "student_id": "STU-A",
    "class_id": "CLASS-A",
    "educator_id": "EDU-A",
    "classbatch_id": "BATCH-A.0",
    "sessions_count": "24",
    "is_renewal": "Yes",
    "continue_same_batch": "Yes",
    "preferred_days": "Tue,Thu",
    "preferred_time": "17:00:00",
    "request_status": "Completed",
    "batch_allocated": "Yes",
    "allocated_by": "ops_exec_02",
    "allocated_at": "2026-11-01 12:00:00",
    "created_at": "2026-11-01 11:30:00",
    "updated_at": "2026-11-01 12:00:00",
    "deleted_at": "BATCH-J"
  },
  {
    "id": "REQ-B",
    "faculty_form_id": "FORM-B",
    "invoice_id": "INV-B",
    "user_id": "USER-B",
    "student_id": "STU-B",
    "class_id": "CLASS-B",
    "educator_id": "EDU-B",
    "classbatch_id": "BATCH-B.0",
    "sessions_count": "24",
    "is_renewal": "Yes",
    "continue_same_batch": "Yes",
    "preferred_days": "Mon,Wed",
    "preferred_time": "18:00:00",
    "request_status": "Pending_Batch_Allocation",
    "batch_allocated": "No",
    "allocated_by": "BATCH-J",
    "allocated_at": "BATCH-J",
    "created_at": "2026-11-01 17:00:00",
    "updated_at": "2026-11-01 17:00:00",
    "deleted_at": "BATCH-J"
  },
  {
    "id": "REQ-C",
    "faculty_form_id": "FORM-E",
    "invoice_id": "INV-E",
    "user_id": "USER-E",
    "student_id": "STU-E",
    "class_id": "CLASS-D",
    "educator_id": "EDU-D",
    "classbatch_id": "BATCH-D.0",
    "sessions_count": "24",
    "is_renewal": "Yes",
    "continue_same_batch": "Yes",
    "preferred_days": "Sat,Sun",
    "preferred_time": "11:00:00",
    "request_status": "Failed_Batch_Full",
    "batch_allocated": "No",
    "allocated_by": "BATCH-J",
    "allocated_at": "BATCH-J",
    "created_at": "2026-11-02 16:30:00",
    "updated_at": "2026-11-02 16:35:00",
    "deleted_at": "BATCH-J"
  },
  {
    "id": "REQ-D",
    "faculty_form_id": "FORM-K",
    "invoice_id": "INV-L",
    "user_id": "USER-L",
    "student_id": "STU-L",
    "class_id": "CLASS-C",
    "educator_id": "EDU-C",
    "classbatch_id": "BATCH-J",
    "sessions_count": "24",
    "is_renewal": "Yes",
    "continue_same_batch": "No",
    "preferred_days": "Sat,Sun",
    "preferred_time": "11:00:00",
    "request_status": "Awaiting_Parent_Batch_Selection",
    "batch_allocated": "No",
    "allocated_by": "BATCH-J",
    "allocated_at": "BATCH-J",
    "created_at": "2026-11-03 17:15:00",
    "updated_at": "2026-11-03 17:15:00",
    "deleted_at": "BATCH-J"
  }
]
```

### `4_class_schedule_bookings.csv`

- **Rows:** 2
- **Columns:** 18
- **Exact columns and pandas-inferred dtypes:**

| Column | dtype | missing values |
|---|---:|---:|
| `id` | `int64` | 0 |
| `bookingrequest_id` | `int64` | 0 |
| `invoice_id` | `int64` | 0 |
| `classschedule_id` | `int64` | 0 |
| `classbatch_id` | `int64` | 0 |
| `class_id` | `int64` | 0 |
| `user_id` | `int64` | 0 |
| `student_id` | `int64` | 0 |
| `educator_id` | `int64` | 0 |
| `class_date` | `object` | 0 |
| `start_time` | `object` | 0 |
| `end_time` | `object` | 0 |
| `booking_type` | `object` | 0 |
| `is_cancelled` | `object` | 0 |
| `attended_class` | `object` | 0 |
| `created_at` | `object` | 0 |
| `updated_at` | `object` | 0 |
| `deleted_at` | `float64` | 2 |

- **Exact duplicate rows:** 0
- **Potential primary keys (uniqueness only; semantic confirmation needed):** `id` (2/2 non-null unique), `classschedule_id` (2/2 non-null unique)
- **Date/time fields (column-name based):** `class_date`, `start_time`, `end_time`, `created_at`, `updated_at`, `deleted_at`
- **Payment-related fields (name-based):** `invoice_id`
- **Student/parent-related fields (name-based):** `user_id`, `student_id`
- **Batch/teacher/class-related fields (name-based):** `classschedule_id`, `classbatch_id`, `class_id`, `educator_id`

**Five representative records (personal fields masked):**
```json
[
  {
    "id": "SCHED-A",
    "bookingrequest_id": "REQ-A",
    "invoice_id": "INV-A",
    "classschedule_id": "OCC-A",
    "classbatch_id": "BATCH-A",
    "class_id": "CLASS-A",
    "user_id": "USER-A",
    "student_id": "STU-A",
    "educator_id": "EDU-A",
    "class_date": "2026-11-03",
    "start_time": "17:00:00",
    "end_time": "17:50:00",
    "booking_type": "Regular_Renewal",
    "is_cancelled": "No",
    "attended_class": "Yes",
    "created_at": "2026-11-01 12:00:05",
    "updated_at": "2026-11-03 18:00:00",
    "deleted_at": "BATCH-J"
  },
  {
    "id": "SCHED-B",
    "bookingrequest_id": "REQ-A",
    "invoice_id": "INV-A",
    "classschedule_id": "OCC-B",
    "classbatch_id": "BATCH-A",
    "class_id": "CLASS-A",
    "user_id": "USER-A",
    "student_id": "STU-A",
    "educator_id": "EDU-A",
    "class_date": "2026-11-05",
    "start_time": "17:00:00",
    "end_time": "17:50:00",
    "booking_type": "Regular_Renewal",
    "is_cancelled": "No",
    "attended_class": "No",
    "created_at": "2026-11-01 12:00:05",
    "updated_at": "2026-11-01 12:00:05",
    "deleted_at": "BATCH-J"
  }
]
```

### `reference_active_batches_and_students.csv`

- **Rows:** 13
- **Columns:** 20
- **Exact columns and pandas-inferred dtypes:**

| Column | dtype | missing values |
|---|---:|---:|
| `student_id` | `int64` | 0 |
| `user_id` | `int64` | 0 |
| `student_name_masked` | `object` | 0 |
| `parent_name_masked` | `object` | 0 |
| `registered_mobile_masked` | `object` | 0 |
| `registered_email_masked` | `object` | 0 |
| `current_classbatch_id` | `int64` | 0 |
| `classbatch_name` | `object` | 0 |
| `class_id` | `int64` | 0 |
| `class_name` | `object` | 0 |
| `category_id` | `int64` | 0 |
| `category_name` | `object` | 0 |
| `educator_id` | `int64` | 0 |
| `educator_name` | `object` | 0 |
| `standard_fee_24_sessions_inr` | `float64` | 0 |
| `batch_days` | `object` | 0 |
| `batch_start_time` | `object` | 0 |
| `active_students_count` | `int64` | 0 |
| `max_batch_size` | `int64` | 0 |
| `deleted_at` | `float64` | 13 |

- **Exact duplicate rows:** 0
- **Potential primary keys (uniqueness only; semantic confirmation needed):** `student_id` (13/13 non-null unique), `user_id` (13/13 non-null unique)
- **Date/time fields (column-name based):** `batch_start_time`, `deleted_at`
- **Payment-related fields (name-based):** None detected.
- **Student/parent-related fields (name-based):** `student_id`, `user_id`, `student_name_masked`, `parent_name_masked`, `registered_mobile_masked`, `registered_email_masked`, `active_students_count`
- **Batch/teacher/class-related fields (name-based):** `current_classbatch_id`, `classbatch_name`, `class_id`, `educator_id`, `educator_name`, `batch_days`, `batch_start_time`, `max_batch_size`

**Five representative records (personal fields masked):**
```json
[
  {
    "student_id": "STU-A",
    "user_id": "USER-A",
    "student_name_masked": "[masked name]",
    "parent_name_masked": "[masked name]",
    "registered_mobile_masked": "[masked phone]",
    "registered_email_masked": "[masked email]",
    "current_classbatch_id": "BATCH-A",
    "classbatch_name": "[CLASSBATCH-NAME]",
    "class_id": "CLASS-A",
    "class_name": "[CLASS-NAME]",
    "category_id": "1",
    "category_name": "[CATEGORY-NAME]",
    "educator_id": "EDU-A",
    "educator_name": "[masked name]",
    "standard_fee_24_sessions_inr": "12000.0",
    "batch_days": "Tue,Thu",
    "batch_start_time": "17:00:00",
    "active_students_count": "4",
    "max_batch_size": "6",
    "deleted_at": "BATCH-J"
  },
  {
    "student_id": "STU-B",
    "user_id": "USER-B",
    "student_name_masked": "[masked name]",
    "parent_name_masked": "[masked name]",
    "registered_mobile_masked": "[masked phone]",
    "registered_email_masked": "[masked email]",
    "current_classbatch_id": "BATCH-B",
    "classbatch_name": "[CLASSBATCH-NAME]",
    "class_id": "CLASS-B",
    "class_name": "[CLASS-NAME]",
    "category_id": "2",
    "category_name": "[CATEGORY-NAME]",
    "educator_id": "EDU-B",
    "educator_name": "[masked name]",
    "standard_fee_24_sessions_inr": "10500.0",
    "batch_days": "Mon,Wed",
    "batch_start_time": "18:00:00",
    "active_students_count": "5",
    "max_batch_size": "6",
    "deleted_at": "BATCH-J"
  },
  {
    "student_id": "STU-C",
    "user_id": "USER-C",
    "student_name_masked": "[masked name]",
    "parent_name_masked": "[masked name]",
    "registered_mobile_masked": "[masked phone]",
    "registered_email_masked": "[masked email]",
    "current_classbatch_id": "BATCH-C",
    "classbatch_name": "[CLASSBATCH-NAME]",
    "class_id": "CLASS-C",
    "class_name": "[CLASS-NAME]",
    "category_id": "3",
    "category_name": "[CATEGORY-NAME]",
    "educator_id": "EDU-C",
    "educator_name": "[masked name]",
    "standard_fee_24_sessions_inr": "9000.0",
    "batch_days": "Wed,Fri",
    "batch_start_time": "16:30:00",
    "active_students_count": "3",
    "max_batch_size": "6",
    "deleted_at": "BATCH-J"
  },
  {
    "student_id": "STU-D",
    "user_id": "USER-D",
    "student_name_masked": "[masked name]",
    "parent_name_masked": "[masked name]",
    "registered_mobile_masked": "[masked phone]",
    "registered_email_masked": "[masked email]",
    "current_classbatch_id": "BATCH-A",
    "classbatch_name": "[CLASSBATCH-NAME]",
    "class_id": "CLASS-A",
    "class_name": "[CLASS-NAME]",
    "category_id": "1",
    "category_name": "[CATEGORY-NAME]",
    "educator_id": "EDU-A",
    "educator_name": "[masked name]",
    "standard_fee_24_sessions_inr": "12000.0",
    "batch_days": "Tue,Thu",
    "batch_start_time": "17:00:00",
    "active_students_count": "4",
    "max_batch_size": "6",
    "deleted_at": "BATCH-J"
  },
  {
    "student_id": "STU-E",
    "user_id": "USER-E",
    "student_name_masked": "[masked name]",
    "parent_name_masked": "[masked name]",
    "registered_mobile_masked": "[masked phone]",
    "registered_email_masked": "[masked email]",
    "current_classbatch_id": "BATCH-D",
    "classbatch_name": "[CLASSBATCH-NAME]",
    "class_id": "CLASS-D",
    "class_name": "[CLASS-NAME]",
    "category_id": "4",
    "category_name": "[CATEGORY-NAME]",
    "educator_id": "EDU-D",
    "educator_name": "[masked name]",
    "standard_fee_24_sessions_inr": "11000.0",
    "batch_days": "Sat,Sun",
    "batch_start_time": "11:00:00",
    "active_students_count": "6",
    "max_batch_size": "6",
    "deleted_at": "BATCH-J"
  }
]
```

## Cross-file key and relationship observations

- Candidate PK uniqueness is reported per-file above. An identifier being unique in this sample does not establish a database constraint.
- Candidate FK/relationship columns and observed matches are detailed in `phase1_relationship_mapping.md`. Repeated values in ordinary columns (e.g. class, batch, teacher, status) are expected and are not duplicate rows.
- CSVs contain masked personal data already; displayed examples additionally replace name/contact values with generic masks.
- “Missing” means pandas-recognized null/blank values. Empty-looking tokens that are literal text, if any, are not reclassified. Dtypes are parser inference, not authoritative database schema.
