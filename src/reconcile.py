"""
Audit Reconciliation & Financial Data Analysis
----------------------------------------------
1) Generise dvije sinteticke tabele: General Ledger i Bank Statement
2) Provjerava duplikate Transaction_ID-eva
3) Radi outer merge i klasifikuje: Matched / Only in GL / Only in Bank / Amount Mismatch
4) Racuna statistike i exportuje sve u jedan Excel workbook
"""

import numpy as np
import pandas as pd
from datetime import date, timedelta

RNG = np.random.default_rng(42)

# ----------------------------------------------------------------------
# 1. SINTETICKI PODACI
# ----------------------------------------------------------------------

N_BASE = 950          # transakcije koje postoje u obje tabele
N_ONLY_GL = 25        # cekovi / neproknjizeno u banci
N_ONLY_BANK = 20      # bankarske naknade, kamate
N_MISMATCH = 18       # greske u unosu iznosa
N_DUP_GL = 6          # duplirani ID-evi unutar GL
N_DUP_BANK = 4        # duplirani ID-evi unutar Bank

CATEGORIES = [
    "Sales Revenue", "Vendor Payment", "Payroll", "Utilities",
    "Office Supplies", "Travel & Entertainment", "Rent",
    "Marketing", "Bank Fees", "Interest Income",
]

ACCOUNTS = {
    "Sales Revenue": "4000", "Vendor Payment": "5100", "Payroll": "6000",
    "Utilities": "6200", "Office Supplies": "6300", "Travel & Entertainment": "6400",
    "Rent": "6100", "Marketing": "6500", "Bank Fees": "6900", "Interest Income": "4900",
}

DESCRIPTIONS = {
    "Sales Revenue": ["Invoice payment received", "Customer deposit", "Product sale"],
    "Vendor Payment": ["Supplier invoice", "Vendor payment - materials", "Contractor fee"],
    "Payroll": ["Monthly salary run", "Payroll transfer", "Employee wages"],
    "Utilities": ["Electricity bill", "Water utility", "Internet & telecom"],
    "Office Supplies": ["Stationery purchase", "Printer consumables", "Office equipment"],
    "Travel & Entertainment": ["Business trip - airfare", "Client dinner", "Hotel accommodation"],
    "Rent": ["Monthly office rent", "Warehouse lease", "Rent payment"],
    "Marketing": ["Online ad campaign", "Trade fair booth", "Print advertising"],
    "Bank Fees": ["Account maintenance fee", "Wire transfer fee", "Card processing fee"],
    "Interest Income": ["Deposit interest credit", "Savings interest", "Interest accrual"],
}

START = date(2024, 1, 1)
DAYS = 365


def rand_dates(n):
    return [START + timedelta(days=int(d)) for d in RNG.integers(0, DAYS, n)]


def rand_amount(cat):
    """Prihodi pozitivni, troskovi negativni; razliciti rasponi po kategoriji."""
    ranges = {
        "Sales Revenue": (500, 25000, 1), "Interest Income": (5, 400, 1),
        "Payroll": (1500, 12000, -1), "Rent": (800, 6000, -1),
        "Vendor Payment": (200, 15000, -1), "Utilities": (50, 1200, -1),
        "Office Supplies": (20, 900, -1), "Travel & Entertainment": (80, 3500, -1),
        "Marketing": (150, 8000, -1), "Bank Fees": (5, 150, -1),
    }
    lo, hi, sign = ranges[cat]
    return round(sign * float(RNG.uniform(lo, hi)), 2)


def make_rows(ids, cats=None):
    cats = cats if cats is not None else RNG.choice(CATEGORIES, len(ids))
    dates = rand_dates(len(ids))
    rows = []
    for tid, c, d in zip(ids, cats, dates):
        rows.append({
            "Transaction_ID": tid,
            "Date": d,
            "Description": str(RNG.choice(DESCRIPTIONS[c])),
            "Category": c,
            "Amount": rand_amount(c),
            "Account": ACCOUNTS[c],
        })
    return pd.DataFrame(rows)


# --- osnovni skup (postoji u obje tabele) -----------------------------
base_ids = [f"TXN-{i:05d}" for i in range(1, N_BASE + 1)]
base = make_rows(base_ids)

# --- samo u GL --------------------------------------------------------
gl_only_ids = [f"TXN-{i:05d}" for i in range(9001, 9001 + N_ONLY_GL)]
gl_only = make_rows(gl_only_ids,
                    RNG.choice(["Vendor Payment", "Payroll", "Rent"], N_ONLY_GL))

# --- samo u Bank ------------------------------------------------------
bank_only_ids = [f"TXN-{i:05d}" for i in range(9501, 9501 + N_ONLY_BANK)]
bank_only = make_rows(bank_only_ids,
                      RNG.choice(["Bank Fees", "Interest Income"], N_ONLY_BANK))

# --- GL tabela --------------------------------------------------------
gl = pd.concat([base, gl_only], ignore_index=True)

# --- Bank tabela (kopija basea + bank_only) ---------------------------
bank = pd.concat([base.copy(), bank_only], ignore_index=True)

# Banka biljezi datum 0-3 dana kasnije (clearing delay) i ima kraci opis
bank["Date"] = [d + timedelta(days=int(x))
                for d, x in zip(bank["Date"], RNG.integers(0, 4, len(bank)))]
bank["Description"] = bank["Description"].str.upper().str[:22]

# --- Amount Mismatch: mijenjamo iznos u banci za dio transakcija ------
mismatch_ids = list(RNG.choice(base_ids, N_MISMATCH, replace=False))
for tid in mismatch_ids:
    m = bank["Transaction_ID"] == tid
    old = bank.loc[m, "Amount"].iloc[0]
    # tipicne greske: transponovane cifre / faktor 10 / mala razlika
    kind = RNG.integers(0, 3)
    if kind == 0:
        new = round(old * 10, 2)
    elif kind == 1:
        new = round(old + RNG.choice([-1, 1]) * float(RNG.uniform(10, 500)), 2)
    else:
        new = round(float(str(abs(old)).replace(".", "")[:4]) / 100 * np.sign(old), 2)
    bank.loc[m, "Amount"] = new

# --- Duplirani Transaction_ID-evi unutar iste tabele -------------------
dup_gl_ids = list(RNG.choice(base_ids, N_DUP_GL, replace=False))
gl = pd.concat([gl, gl[gl["Transaction_ID"].isin(dup_gl_ids)]], ignore_index=True)

dup_bank_ids = list(RNG.choice(base_ids, N_DUP_BANK, replace=False))
bank = pd.concat([bank, bank[bank["Transaction_ID"].isin(dup_bank_ids)]],
                 ignore_index=True)

# Bank Statement nema Category/Account (banka ne zna internu klasifikaciju)
bank = bank[["Transaction_ID", "Date", "Description", "Amount"]]

# promijesaj redoslijed
gl = gl.sample(frac=1, random_state=1).reset_index(drop=True)
bank = bank.sample(frac=1, random_state=2).reset_index(drop=True)

gl.to_csv("../data/sample/general_ledger.csv", index=False)
bank.to_csv("../data/sample/bank_statement.csv", index=False)
print(f"GL: {len(gl)} redova | Bank: {len(bank)} redova")

# ----------------------------------------------------------------------
# 2. OBRADA / RECONCILIATION
# ----------------------------------------------------------------------

gl = pd.read_csv("../data/sample/general_ledger.csv", parse_dates=["Date"])
bank = pd.read_csv("../data/sample/bank_statement.csv", parse_dates=["Date"])

# --- 2a. duplikati ----------------------------------------------------
gl["Is_Duplicate"] = gl.duplicated(subset="Transaction_ID", keep=False)
bank["Is_Duplicate"] = bank.duplicated(subset="Transaction_ID", keep=False)

gl_dup_ids = sorted(gl.loc[gl["Is_Duplicate"], "Transaction_ID"].unique())
bank_dup_ids = sorted(bank.loc[bank["Is_Duplicate"], "Transaction_ID"].unique())
dup_all_ids = sorted(set(gl_dup_ids) | set(bank_dup_ids))

print(f"Duplikati -> GL: {len(gl_dup_ids)} ID | Bank: {len(bank_dup_ids)} ID")

# Za merge koristimo de-duplicirane verzije (prva pojava), da 1 ID = 1 red
gl_u = gl.drop_duplicates(subset="Transaction_ID", keep="first")
bank_u = bank.drop_duplicates(subset="Transaction_ID", keep="first")

# --- 2b. merge --------------------------------------------------------
rec = pd.merge(
    gl_u, bank_u, on="Transaction_ID", how="outer",
    suffixes=("_GL", "_Bank"), indicator=True,
)

# --- 2c. status logika ------------------------------------------------
TOL = 0.01  # tolerancija na zaokruzivanje

rec["Amount_Diff"] = (rec["Amount_GL"].fillna(0) - rec["Amount_Bank"].fillna(0)).round(2)

conds = [
    rec["_merge"] == "left_only",
    rec["_merge"] == "right_only",
    (rec["_merge"] == "both") & (rec["Amount_Diff"].abs() > TOL),
]
rec["Status"] = np.select(conds,
                          ["Only in GL", "Only in Bank", "Amount Mismatch"],
                          default="Matched")

rec["Is_Exception"] = rec["Status"] != "Matched"
rec["Has_Duplicate_ID"] = rec["Transaction_ID"].isin(dup_all_ids)

# Amount_Diff ima smisla samo kod mismatcha
rec.loc[rec["Status"] != "Amount Mismatch", "Amount_Diff"] = np.nan

# Datum za pivot po mjesecima + popunjavanje kategorije za bank-only redove
rec["Date"] = rec["Date_GL"].fillna(rec["Date_Bank"])
rec["Month"] = rec["Date"].dt.to_period("M").dt.to_timestamp()
rec["Category"] = rec["Category"].fillna("Unclassified (Bank only)")
rec["Account"] = rec["Account"].fillna("N/A")
rec["Amount"] = rec["Amount_GL"].fillna(rec["Amount_Bank"])
rec["Abs_Amount"] = rec["Amount"].abs()

rec = rec[[
    "Transaction_ID", "Date", "Month", "Category", "Account",
    "Description_GL", "Description_Bank",
    "Amount_GL", "Amount_Bank", "Amount", "Abs_Amount", "Amount_Diff",
    "Status", "Is_Exception", "Has_Duplicate_ID",
]].sort_values("Transaction_ID").reset_index(drop=True)

rec.columns = [
    "Transaction_ID", "Date", "Month", "Category", "Account",
    "Description_GL", "Description_Bank",
    "Amount_GL", "Amount_Bank", "Amount", "Abs_Amount", "Amount_Diff",
    "Status", "Is_Exception", "Has_Duplicate_ID",
]

# ----------------------------------------------------------------------
# 3. STATISTIKE
# ----------------------------------------------------------------------

status_stats = (rec.groupby("Status")
                .agg(Transactions=("Transaction_ID", "count"),
                     Total_Amount=("Amount", "sum"),
                     Avg_Amount=("Amount", "mean"))
                .round(2).reset_index())

cat_stats = (rec.groupby("Category")
             .agg(Transactions=("Transaction_ID", "count"),
                  Total_Amount=("Amount", "sum"),
                  Exceptions=("Is_Exception", "sum"))
             .round(2).reset_index()
             .sort_values("Total_Amount", ascending=False))

month_stats = (rec.groupby("Month")
               .agg(Transactions=("Transaction_ID", "count"),
                    Total_Amount=("Amount", "sum"),
                    Exceptions=("Is_Exception", "sum"))
               .round(2).reset_index())

counts = rec["Status"].value_counts()
total = len(rec)
kpi = {
    "Total Transactions": total,
    "Matched": int(counts.get("Matched", 0)),
    "Exceptions": int(total - counts.get("Matched", 0)),
    "Duplicates": len(dup_all_ids),
    "Only in GL": int(counts.get("Only in GL", 0)),
    "Only in Bank": int(counts.get("Only in Bank", 0)),
    "Amount Mismatch": int(counts.get("Amount Mismatch", 0)),
}
kpi["Match Rate %"] = round(kpi["Matched"] / total * 100, 2)

print("\n--- KPI ---")
for k, v in kpi.items():
    print(f"{k:>22}: {v}")
print("\n--- Po statusu ---")
print(status_stats.to_string(index=False))

# sacuvaj medjurezultate za korak 4
rec.to_pickle("./_rec.pkl")
gl.to_pickle("./_gl.pkl")
bank.to_pickle("./_bank.pkl")
pd.to_pickle(
    {"kpi": kpi, "status": status_stats, "cat": cat_stats, "month": month_stats,
     "gl_dup_ids": gl_dup_ids, "bank_dup_ids": bank_dup_ids},
    "./_stats.pkl",
)
print("\nOK - podaci spremni.")
