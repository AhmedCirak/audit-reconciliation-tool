# Audit Reconciliation & Financial Data Analysis Tool

A Python + Excel tool that automates reconciliation between a General Ledger
and a Bank Statement — the kind of task an audit or accounting team does
manually every month. The tool matches transactions, flags exceptions, and
outputs an interactive Excel workbook for review.

## Features

- Generates realistic synthetic GL and Bank Statement datasets (~1,000 rows
  each) with intentionally seeded exceptions: unmatched transactions, amount
  mismatches, and duplicate transaction IDs
- Detects duplicate transaction IDs within each source table
- Reconciles both tables on `Transaction_ID` and classifies every transaction
  as **Matched**, **Only in GL**, **Only in Bank**, or **Amount Mismatch**
- Computes summary statistics (counts, totals, averages per status/category/month)
- Exports everything into a single formatted Excel workbook:
  - `GL_Data`, `Bank_Data`, `Reconciliation` sheets as structured Excel Tables
  - `Summary` sheet with formula-driven KPIs (match rate, exception count,
    materiality threshold) that recalculate automatically
  - PivotTables and PivotCharts (status breakdown, category analysis, monthly trend)
  - Conditional formatting to highlight exceptions and duplicates

  ## LLM Explanation Layer (prototype)

For every exception, a local LLM (Ollama, `qwen2.5:7b`) proposes a
category and a one-sentence explanation. Python does all matching and
arithmetic; the model only describes precomputed facts (status,
amounts, difference, descriptions) and is never asked to calculate.
Everything runs locally, and no data leaves the machine.

- `src/explain.py`: `build_prompt(row)` turns one exception row into a
  prompt with a fixed list of allowed categories, and `explain_row(row)`
  sends it to the model.
- `Seeded_Cause`: a ground-truth column recording how each exception
  was seeded into the synthetic data. It is used only for evaluation,
  is never passed to the model, and is not written to the Excel report.
- `test_explain.py`: unit tests for the prompt builder.

**Status:** accuracy has not been measured yet. Early manual runs
showed the model giving plausible but unsupported explanations (for
example, inferring a timing difference that the data cannot show),
which is why evaluation against the seeded ground truth is the next step.

### Limitations

- All data is synthetic, so results say nothing about real audits.
- The reconciliation matches on `Transaction_ID` and does not compare
  dates, so some causes cannot be derived from the data at all.
- A small local model can produce convincing explanations without
  evidence; outputs should be treated as suggestions for a reviewer.

## Tech Stack

Python · Pandas · NumPy · openpyxl · Excel (PivotTables, Conditional Formatting) · Ollama (local LLM)

## Project Structure

```
audit-reconciliation-tool/
├── src/
│   ├── reconcile.py       # generates synthetic data + runs reconciliation
│   ├── export_excel.py    # builds the formatted Excel workbook
│   └── explain.py         # LLM prompt builder + Ollama call
├── test_explain.py        # tests for the prompt builder
├── test_ollama.py         # smoke test for the local model
├── data/sample/           # sample GL / Bank Statement CSVs
├── output/                # sample finished workbook
└── screenshots/

## How It Works

1. `reconcile.py` generates synthetic `general_ledger.csv` and
   `bank_statement.csv` files, then merges them on `Transaction_ID`
   (outer join) and classifies each row by status.
2. `export_excel.py` reads the reconciliation output and builds a
   multi-sheet Excel workbook with tables, formulas, and formatting.
3. PivotTables, PivotCharts, and slicers on top of the workbook are built
   manually in Excel (see `output/Audit_Reconciliation_sample.xlsx` for the
   finished result).

## Setup

```bash
pip install -r requirements.txt
cd src
python reconcile.py
python export_excel.py
```
### Optional: LLM explanations

Requires [Ollama](https://ollama.com) running locally.

```
ollama pull qwen2.5:7b
cd src
python reconcile.py
python explain.py
```

The workbook is written to `output/Audit_Reconciliation.xlsx`.

## Sample Output

See `output/Audit_Reconciliation_sample.xlsx` for the finished dashboard,
including the Summary KPIs, Exceptions worklist, and PivotTables/PivotCharts.

## Notes

All data in this project is synthetically generated (seeded, not real
transactions) for demonstration purposes.


