# Project: audit-reconciliation-tool

Python tool for GL vs bank statement reconciliation (Excel in, Excel out).

## Current task
Add an explanation layer: for each unmatched item, a local LLM (Ollama,
model qwen2.5:7b) suggests a category and a one-sentence explanation.

## Rules
- Python does ALL matching and arithmetic. The model only describes
  precomputed facts. Never ask the model to calculate.
- Model output must be exactly one category from this list:
  timing difference, bank fee, partial payment, possible duplicate,
  needs manual review
- Prompts and categories are in English.
- Everything runs locally. No external APIs, no real financial data in
  the repo or in tests.
- Do not change the existing matching logic unless asked.
- Keep model calls in a single function so the model name is easy to change.
- One small change at a time. Add a test for every new function.
- Never commit .env, venv/ or real data files.
