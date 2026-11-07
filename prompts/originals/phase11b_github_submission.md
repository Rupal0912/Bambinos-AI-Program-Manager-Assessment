# Phase 11B — Prepare Bambinos GitHub Submission

Project: `<PROJECT_ROOT>`

Prepare a GitHub-ready submission following the official Bambinos assessment repository instructions.

This is a LOCAL PREPARATION task only.

Do not initialize Git, create a GitHub repository, commit, push, publish, or delete original files.

## 1. Required submission structure

Prepare:

- `prompts/` — exact AI prompts used, where available; distinguish reconstructed prompts from original prompts.
- `results/` — aggregate results and sanitized demonstration outputs.
- `workflows_or_scripts/` — documented entry points to the existing Python implementation.
- `submission/` — final case report PDF.
- `README.md` — clear project navigation and execution instructions.

Preserve existing `src/`, `dashboard/`, `config/`, `tests/`, `analysis/`, and `documentation/` directories.

## 2. Data protection

Do not publish or modify the five original CSVs.

Keep `data/*.csv` and current `outputs/*` excluded through `.gitignore`.

Create a small synthetic demonstration dataset only if necessary to let reviewers execute the prototype without the original files.

Do not reproduce original names, contact information, payment references, or linked record IDs in public demonstration files.

Aggregate assessment findings may be included with their denominators and limitations.

## 3. Final report

Inspect the existing 13-page report.

Correct the character-encoding error in the page 9 hours-saved formula.

Preserve the report's analysis, findings, caveats and layout.

Do not publish the DOCX unless explicitly needed.

Check the PDF for sensitive record-level identifiers. If necessary, prepare a separate public-safe PDF while retaining the original for direct submission.

## 4. README

Document:

- Business problem
- Three-stage decision architecture
- Prototype and dashboard
- How to run the project
- How to run tests
- Assessment findings and limitations
- Required submission artifacts
- Dataset provenance and privacy
- No live integrations or automatic approval

## 5. Validation

Verify:

- Original five CSV hashes unchanged.
- Original reconciliation outputs unchanged.
- Default auto-approval disabled.
- No credentials or personal contact information in staged public files.
- PDF opens correctly and formula displays correctly.
- All required submission directories contain useful artifacts.

## 6. Final report

Return:

- Files created or modified.
- Proposed public repository tree.
- Any remaining sensitive material.
- Whether a clean clone can run the tests.
- Exact next steps before Git initialization.

Do not publish anything.
