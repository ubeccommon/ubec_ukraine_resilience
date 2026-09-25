#!/usr/bin/env python3
"""
25_public_tables.py: public copies of hromada tables without military-finance fields (rule R4).

Security rule R4 (companion paper, section 12): no garrison flag and no military income-tax
fields at hromada level. The pipeline keeps these fields internally (garrison sensitivity checks,
captions); this script writes the copies that may be published and committed.

  tidy/resilience_v1_k3.csv          -> public/resilience_v1_k3.csv
      drop pdfo_mil_share_2021, garrison_flag
  tidy/resilience_index_v11_k3.csv   -> public/resilience_index_v11_k3.csv
      drop garrison_flag
  tidy/budget_indicators_k3.csv      -> public/budget_indicators_k3.csv
      drop pdfo_mil_share_2025
  tidy/budget_long_k3_year.csv       -> public/budget_long_k3_year.csv
      civilian-only revenue: military PIT is removed from the totals that contain it, so that
      garrison hromadas cannot be read off 2021-2023 revenue.
        pdfo       -> pdfo_civ      = pdfo      - pdfo_mil
        own_gf     -> own_gf_civ    = own_gf    - pdfo_mil   (PIT is general-fund revenue)
        rev_total  -> rev_total_civ = rev_total - pdfo_mil
        pdfo_mil   dropped
      pdfo_mil missing while pdfo is present is treated as 0 (no military PIT lines).

Also writes public/README.md (what was removed or converted, row counts) and fails if any
output column matches the R4 pattern.

Run from resilience/:  python 25_public_tables.py
"""
import re
import sys
from datetime import date
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent
TIDY = BASE / "tidy"
PUB = BASE / "public"
LOGF = BASE / "logs" / "25_public_tables.log"
KEYS = {"k1": str, "k2": str, "k3": str}
R4_PATTERN = re.compile(r"garrison|pdfo_mil|_mil_|_mil$|milit", re.IGNORECASE)

_lines = []


def log(msg=""):
    print(msg)
    _lines.append(msg)


def read(name):
    return pd.read_csv(TIDY / name, dtype=KEYS, encoding="utf-8")


def drop_cols(df, cols, name):
    missing = [c for c in cols if c not in df.columns]
    if missing:
        sys.exit(f"{name}: expected columns not found: {missing}")
    return df.drop(columns=cols)


def civilian_long(bl):
    need = ["k3", "year", "code_source", "rev_total", "transfers", "own_gf", "pdfo", "pdfo_mil",
            "inc_last_month", "exp_total", "capex", "exp_last_month"]
    missing = [c for c in need if c not in bl.columns]
    if missing:
        sys.exit(f"budget_long_k3_year.csv: expected columns not found: {missing}")
    d = bl.copy()
    mil = d["pdfo_mil"].where(d["pdfo_mil"].notna() | d["pdfo"].isna(), 0.0)
    d["pdfo_civ"] = d["pdfo"] - mil
    d["own_gf_civ"] = d["own_gf"] - mil
    d["rev_total_civ"] = d["rev_total"] - mil
    out = d[["k3", "year", "code_source", "rev_total_civ", "transfers", "own_gf_civ", "pdfo_civ",
             "inc_last_month", "exp_total", "capex", "exp_last_month"]]
    # checks: 2025 has ~no military PIT, so civilian and original totals must agree there
    y25 = d[d["year"] == 2025]
    if len(y25):
        rel = (y25["own_gf_civ"] - y25["own_gf"]).abs().sum() / y25["own_gf"].abs().sum()
        log(f"  check 2025: |own_gf_civ - own_gf| / |own_gf| = {rel:.2e} (expect ~0)")
    for y, g in d.groupby("year"):
        share = g["pdfo_mil"].sum() / g["pdfo"].sum() if g["pdfo"].sum() else float("nan")
        log(f"  {y}: military PIT removed = {share:.3f} of PIT")
    return out


def main():
    PUB.mkdir(exist_ok=True)
    LOGF.parent.mkdir(exist_ok=True)
    log(f"25_public_tables.py  {date.today().isoformat()}")

    jobs = [
        ("resilience_v1_k3.csv", ["pdfo_mil_share_2021", "garrison_flag"], None),
        ("resilience_index_v11_k3.csv", ["garrison_flag"], None),
        ("budget_indicators_k3.csv", ["pdfo_mil_share_2025"], None),
        ("budget_long_k3_year.csv", None, civilian_long),
    ]
    notes = {
        "resilience_v1_k3.csv": "dropped `pdfo_mil_share_2021`, `garrison_flag`",
        "resilience_index_v11_k3.csv": "dropped `garrison_flag`",
        "budget_indicators_k3.csv": "dropped `pdfo_mil_share_2025`",
        "budget_long_k3_year.csv": "`pdfo`, `own_gf`, `rev_total` replaced by civilian-only "
                                   "`pdfo_civ`, `own_gf_civ`, `rev_total_civ` (military PIT "
                                   "subtracted); `pdfo_mil` dropped",
    }
    rows = []
    for name, cols, func in jobs:
        src = read(name)
        log(f"{name}: {len(src)} rows, {src.shape[1]} columns")
        out = func(src) if func else drop_cols(src, cols, name)
        bad = [c for c in out.columns if R4_PATTERN.search(c)]
        if bad:
            sys.exit(f"{name}: R4 columns still present: {bad}")
        if len(out) != len(src):
            sys.exit(f"{name}: row count changed ({len(src)} -> {len(out)})")
        out.to_csv(PUB / name, index=False, encoding="utf-8")
        log(f"  -> public/{name}: {len(out)} rows, {out.shape[1]} columns")
        rows.append((name, len(out), out.shape[1], notes[name]))

    readme = [
        "# Public copies of hromada tables",
        "",
        "Generated by `resilience/25_public_tables.py`; do not edit by hand.",
        f"Built {date.today().isoformat()} from `resilience/tidy/`.",
        "",
        "These copies apply security rule R4 of the companion paper: no garrison flag and no",
        "military income-tax fields at hromada level. All other columns are unchanged; variable",
        "definitions are in `../tidy/data_dictionary.csv` (civilian-only budget totals follow the",
        "definitions of `pdfo_civ` there: total minus PIT lines naming військовослужбовців).",
        "",
        "| File | Rows | Columns | Change |",
        "|---|---|---|---|",
    ] + [f"| `{n}` | {r} | {c} | {t} |" for n, r, c, t in rows] + [
        "",
        "Military PIT was 6 % of local PIT in 2021, 26–30 % in 2022–2023 and about 0 from Q4 2023,",
        "when it moved to the state budget. From 2024 the civilian and original totals coincide.",
        "",
        "Licence: ODbL 1.0 (see `../../LICENSES.md`).",
        "",
    ]
    (PUB / "README.md").write_text("\n".join(readme), encoding="utf-8")
    log("public/README.md written")
    LOGF.write_text("\n".join(_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
