# Workflow and script entry points

The implementation remains in `src/` and `dashboard/`; this directory documents how to invoke it.

## Reconciliation CLI

Run from the repository root:

```powershell
python src/reconciliation.py --input-dir examples/synthetic_data --output-dir results/synthetic_demo --policy config/policy.json
```

The input is synthetic and contains no parent/student contact fields or assessment record IDs. Outputs are replaced in the selected output directory. The default policy keeps automatic approval disabled, and the program performs no payment, booking, schedule, or messaging writes.

If you have separately authorized local access to the official assessment CSVs, keep them untracked under `data/` and select a separate local output path, for example `--input-dir data --output-dir outputs`. Do not commit those files or outputs.

## Dashboard

```powershell
python -m streamlit run dashboard/app.py
```

The dashboard reads local assessment inputs if all five are present. In a public clone without them, it uses `examples/synthetic_data/` and `results/synthetic_demo/` and labels the view as synthetic.

## Tests

```powershell
python -m pytest -q
```

Tests use only synthetic fixture records and temporary output directories. They do not need the excluded assessment data or modify `outputs/`.
