"""
Prompt building for the LLM explanation layer.

Python (reconcile.py) computes every match and every number. This module
only formats those precomputed facts into a prompt string - it never asks
the model to calculate anything, and it does not call a model itself.
See CLAUDE.md for the full rules.
"""

from pathlib import Path

import ollama
import pandas as pd

# Fixed set the model must choose exactly one from (see CLAUDE.md).
CATEGORIES = [
    "timing difference",
    "bank fee",
    "partial payment",
    "possible duplicate",
    "needs manual review",
]


def _fmt_amount(value):
    if pd.isna(value):
        return "N/A"
    return f"{value:.2f}"


def _fmt_text(value):
    if pd.isna(value) or value == "":
        return "N/A"
    return str(value)


def build_prompt(row):
    """Build an LLM prompt describing one precomputed exception row.

    `row` is a row of the reconciliation DataFrame (e.g. `rec` from
    reconcile.py) for which `Is_Exception` is True. All facts included
    (Status, amounts, duplicate flag, category, descriptions) are already
    computed by Python; the model only describes them and picks a category.
    """
    categories_list = "\n".join(f"- {c}" for c in CATEGORIES)

    return f"""You are assisting with a bank reconciliation review.

Below are precomputed facts about one exception found by a Python
reconciliation script. Do not perform any calculation - only describe
the facts you are given.

Status: {row['Status']}
Category (internal GL category): {_fmt_text(row['Category'])}
Amount in General Ledger: {_fmt_amount(row['Amount_GL'])}
Amount in Bank Statement: {_fmt_amount(row['Amount_Bank'])}
Amount Difference (GL - Bank): {_fmt_amount(row['Amount_Diff'])}
Has a duplicate Transaction_ID elsewhere in the data: {bool(row['Has_Duplicate_ID'])}
GL Description: {_fmt_text(row['Description_GL'])}
Bank Description: {_fmt_text(row['Description_Bank'])}

Task:
1. Pick exactly ONE category from this fixed list that best matches this exception:
{categories_list}
2. Write exactly one sentence in plain English explaining why this
   transaction is an exception, based only on the facts above.

Respond in this exact format:
Category: <one category from the list>
Explanation: <one sentence>
"""


def explain_row(row, model="qwen2.5:7b"):
    """Ask the local Ollama model to categorize and explain one exception row.

    Python has already computed every fact in the prompt (see build_prompt);
    the model only describes them and picks a category. Kept as the single
    function that calls ollama.chat so the model name is easy to change.
    """
    prompt = build_prompt(row)
    response = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    return response["message"]["content"]


if __name__ == "__main__":
    rec_path = Path(__file__).parent / "_rec.pkl"
    rec = pd.read_pickle(rec_path)
    exceptions = rec[rec["Is_Exception"]].head(3)
    for _, row in exceptions.iterrows():
        print(explain_row(row))
        print("-" * 60)
