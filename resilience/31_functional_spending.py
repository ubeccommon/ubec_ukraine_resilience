#!/usr/bin/env python3
"""
31_functional_spending.py — local-budget expenditure by functional classification per hromada (k3),
2021–2026, from openbudget.gov.ua. Inputs for the three-sphere indices
(resilience/docs/threefolding_framework.md, section 6).

  python 31_functional_spending.py probe [--k3 2602003] [--year 2025]
  python 31_functional_spending.py pull  [--years 2021-2026] [--workers 4] [--test N]
  python 31_functional_spending.py shares

Source: localBudgetData EXPENSES with classificationType=PROGRAM. Each row carries the programme code
(COD_CONS_MB_PK, ТПКВКМБ), the functional code (COD_CONS_MB_FK) and the economic code (COD_CONS_EK),
with actual spending in FAKT_AMT (cumulative year to date, period=MONTH). The FUNCTIONAL
classification is not used: its response carries planned amounts only (header ZAT, PLANS, PLANS; no
FAKT_AMT; probe of 27 Sep 2026).

probe   one hromada, one year: columns, the effect of removing hierarchical economic sub-rows (total vs
        the economic-classification FAKT_AMT total from 03's cache, target ratio 1.0000), every
        functional code with its amount, sub-codes served, shares. Run this first.
pull    all non-occupied hromadas; cache and resume as 03_openbudget.py
        (raw/openbudget/EXPENSES_PROGRAM/<year>/<budgetCode>.csv.gz). Rerun to retry failures.
        Responses that are not CSV are not cached.
shares  annual (December, or latest month for 2026), FUND_TYP T ->
        tidy/functional_spending_k3_year.csv       tracked: shares only
        tidy/functional_spending_full_k3_year.csv  ignored: UAH amounts by functional code

De-duplication: within each programme × functional code, an economic code is dropped when a more
detailed code under it is present (2000 > 2100 > 2110 > 2111); rows without an economic code are
dropped when coded rows exist. Functional codes are then summed; parent functional codes (0800 when
0820 exists) are dropped the same way.

Budget codes: 03's jobs table (year-specific code, else the latest); 2026 uses the 2025 code, as
20_budget_quarterly.py does.

Functional classification (Функціональна класифікація видатків):
  01 general public services (administration)   06 housing and communal economy
  08 spiritual and physical development          0810 sport, 082x culture and arts, 0830 media
  09 education                                   0960 extracurricular education (art/music schools)
  10 social protection and social security

Rule R4 (military finance). Excluded from the denominator and from every published share:
  02    defence;
  0180  transfers from the local budget, incl. subventions to the state budget — the channel used
        to fund military units;
  0380  other public order and security, incl. local mobilisation preparation.
Denominator of every share: all other leaf functional codes of divisions 01 and 03–10 ("civilian
service expenditure"). The tracked table has no UAH amounts: with exp_total in
public/budget_long_k3_year.csv, a civilian total would reveal the excluded spending by subtraction.

Licence: openbudget.gov.ua (MinFin / Treasury), open data per CMU Resolution 835 — attribution.
"""
import argparse
import gzip
import importlib
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent
if "__name__" not in (BASE / "03_openbudget.py").read_text(encoding="utf-8"):
    sys.exit("03_openbudget.py has no __main__ guard")
sys.path.insert(0, str(BASE))
ob = importlib.import_module("03_openbudget")

ITEM = "EXPENSES_PROGRAM"
ob.ITEMS[ITEM] = {"budgetItem": "EXPENSES", "classificationType": "PROGRAM"}
PK, FK, EK, AMT = "COD_CONS_MB_PK", "COD_CONS_MB_FK", "COD_CONS_EK", "FAKT_AMT"
FK_NAME = "COD_CONS_MB_FK_NAME"

TIDY, LOGS = BASE / "tidy", BASE / "logs"
OUT = TIDY / "functional_spending_k3_year.csv"
OUT_FULL = TIDY / "functional_spending_full_k3_year.csv"
FAILS = LOGS / "31_pull_failures.csv"
YEARS_ALL = [2021, 2022, 2023, 2024, 2025, 2026]
TEST_K3 = "2602003"                       # Verkhovyna
CIVIL_DIV = ["01", "03", "04", "05", "06", "07", "08", "09", "10"]
EXCLUDED = ("02", "0180", "0380")         # rule R4, see docstring
SHARES = {                                # column: functional-code prefix
    "sh_01_admin": "01",
    "sh_06_housing": "06",
    "sh_08_culture_sport": "08",
    "sh_0810_sport": "081",
    "sh_082_culture_arts": "082",
    "sh_0830_media": "083",
    "sh_09_education": "09",
    "sh_0960_extracurricular": "096",
    "sh_10_social": "10",
}
SUBCODES = ["081", "082", "083", "096"]
_logf = None


def log(*a):
    m = " ".join(str(x) for x in a)
    print(m, flush=True)
    if _logf:
        _logf.write(m + "\n")
        _logf.flush()


def open_log(name, mode="w"):
    global _logf
    LOGS.mkdir(exist_ok=True)
    _logf = open(LOGS / name, mode, encoding="utf-8")


def parse_years(s):
    return [y for y in ob.parse_years(s) if y in YEARS_ALL] if s else YEARS_ALL


# ------------------------------------------------------------------ jobs
def load_jobs():
    if Path(ob.JOBS).exists():
        j = pd.read_csv(ob.JOBS, dtype=str)
    else:
        j = ob.build_jobs(pd.read_csv(ob.XW, dtype=str))
    j["k3"] = j["k3"].astype(str).str.zfill(7)
    j["year"] = j["year"].astype(int)
    j26 = j[j["year"] == 2025].copy()
    j26["year"], j26["code_source"] = 2026, "2025"
    return pd.concat([j[j["year"] != 2026], j26], ignore_index=True)


def non_occupied():
    keys = ob.load_keys()
    keys["k3"] = keys["k3"].astype(str).str.zfill(7)
    return keys, set(keys.loc[keys["occupied"] == False, "k3"])  # noqa: E712


# ------------------------------------------------------------ fetch/read
def looks_like_csv(body):
    head = ob.decode(body[:600])
    return ";" in head and "REP_PERIOD" in head.upper()


def fetch(year, code):
    """ob.fetch_one caches any HTTP 200; keep the file only if it is a data CSV."""
    status, _ = ob.fetch_one(ITEM, year, code)
    p = Path(ob.cache_path(ITEM, year, code))
    if status.startswith("fail") or not p.exists():
        return status
    body = gzip.open(p).read()
    if not body.strip():
        return "empty"                      # served, no rows: an answer, kept
    if not looks_like_csv(body):
        p.rename(p.with_suffix(".bad"))
        return "fail:not csv " + repr(ob.decode(body[:120]))
    return status


# ------------------------------------------------------------ aggregation
def stem(c):
    t = c.rstrip("0")
    return t if t else c


def drop_parents(codes):
    """Codes with a more detailed code under them (same prefix after stripping trailing zeros)."""
    codes = [c for c in codes if c]
    return {c for c in codes for o in codes if o != c and o.startswith(stem(c))}


def norm_code(sr):
    return (sr.astype("string").str.strip().str.replace(r"\.0$", "", regex=True)
            .fillna("").map(lambda v: v.zfill(4) if v else v))


def last_month_rows(df):
    """Rows of the latest month, FUND_TYP T, with normalised codes and numeric amount."""
    for c in (PK, FK, EK, AMT, "REP_PERIOD", "FUND_TYP"):
        if c not in df.columns:
            raise SystemExit(f"column {c} missing; columns: {list(df.columns)}")
    d = df.copy()
    d["m"] = d["REP_PERIOD"].str.extract(r"^(\d{1,2})\.")[0].astype(int)
    last = int(d["m"].max())
    d = d[(d["m"] == last) & (d["FUND_TYP"] == "T")].copy()
    for c in (PK, FK, EK):
        d[c] = norm_code(d[c])
    d["amt"] = pd.to_numeric(d[AMT].astype("string").str.replace(",", ".", regex=False),
                             errors="coerce").fillna(0)
    return d, last


def dedupe_ek(d):
    """Keep leaf economic codes within each programme × functional code."""
    keep = []
    for _, g in d.groupby([PK, FK], sort=False):
        coded = g[g[EK] != ""]
        if len(coded):
            par = drop_parents(list(coded[EK].unique()))
            keep.append(coded[~coded[EK].isin(par)])
        else:
            keep.append(g)
    return pd.concat(keep) if keep else d.iloc[0:0]


def functional_leaves(df):
    """-> (Series functional code -> UAH, leaf codes only; last month) or (None, None)."""
    if df is None or df.empty or "REP_PERIOD" not in df.columns:
        return None, None
    d, last = last_month_rows(df)
    d = dedupe_ek(d)
    s = d.groupby(FK)["amt"].sum()
    s = s[s.index != ""]
    par = drop_parents(list(s.index))
    return s[[c for c in s.index if c not in par]], last


def is_excluded(code):
    return any(code.startswith(e) for e in EXCLUDED)


def civilian(leaves):
    return leaves[[c[:2] in CIVIL_DIV and not is_excluded(c) for c in leaves.index]]


def economic_total(year, code):
    econ = ob.read_cached("EXPENSES_ECONOMIC", year, code)
    if econ is None or econ.empty or "FAKT_AMT" not in econ.columns:
        return None
    em = ob.expense_metrics(econ)
    return em["exp_total"] if em and em.get("exp_total") else None


# ----------------------------------------------------------------- probe
def cmd_probe(a):
    open_log("31_probe.log")
    jobs = load_jobs()
    sel = jobs[(jobs["k3"] == a.k3) & (jobs["year"] == a.year)]
    if sel.empty:
        sys.exit(f"no budget code for k3={a.k3} year={a.year} in the jobs table")
    code = sel.iloc[0]["budgetCode"]
    st = fetch(a.year, code)
    log(f"=== {ITEM} k3={a.k3} year={a.year} budgetCode={code}: {st}")
    df = ob.read_cached(ITEM, a.year, code)
    if df is None or df.empty:
        bad = Path(ob.cache_path(ITEM, a.year, code)).with_suffix(".bad")
        log("response (not CSV): " + ob.decode(gzip.open(bad).read()[:600]) if bad.exists() else "no rows")
        return
    log(f"rows={len(df)} columns={list(df.columns)}")
    d, last = last_month_rows(df)
    ref = economic_total(a.year, code)
    refs = "n/a (no economic cache for this year)" if ref is None else f"{ref:,.0f}"
    log(f"month {last}, FUND_TYP T: rows={len(d)}  economic FAKT_AMT total {refs}")

    def ratio(x):
        return f"{x:,.0f}" + ("" if ref is None else f"   ratio {x / ref:.4f}")
    log(f"  all rows                      {ratio(d['amt'].sum())}")
    log(f"  rows without economic code    {(d[EK] == '').sum()}  sum {d.loc[d[EK] == '', 'amt'].sum():,.0f}")
    log(f"  economic codes present: {sorted(d[EK].unique())[:40]}")
    dd = dedupe_ek(d)
    log(f"  leaf economic codes           {ratio(dd['amt'].sum())}")
    leaves, _ = functional_leaves(df)
    log(f"  leaf functional codes         {ratio(leaves.sum())}")

    names = d.groupby(FK)[FK_NAME].first() if FK_NAME in d.columns else pd.Series(dtype=str)
    t = pd.DataFrame({"amt": leaves, "name": names.reindex(leaves.index)})
    t["R4_excluded"] = [is_excluded(c) for c in t.index]
    pd.set_option("display.max_colwidth", 70)
    pd.set_option("display.width", 170)
    log(f"\nfunctional codes (leaf, {len(t)}):\n"
        + t.to_string(formatters={"amt": "{:,.0f}".format}))
    civ = civilian(leaves).sum()
    log(f"\ncivilian service expenditure (excl. {', '.join(EXCLUDED)}): {civ:,.0f}  "
        f"= {civ / leaves.sum():.3f} of the leaf total")
    log("sub-codes served: " + ", ".join(
        f"{s}x={'yes' if any(c.startswith(s) for c in leaves.index) else 'no'}" for s in SUBCODES))
    cl = civilian(leaves)
    for col, pre in SHARES.items():
        log(f"  {col:26s} {cl[cl.index.str.startswith(pre)].sum() / civ if civ else float('nan'):7.3f}")
    pk = d.groupby(PK)["amt"].sum()
    log(f"\nprogramme codes: {len(pk)} distinct (kept in the raw cache for later use)")


# ------------------------------------------------------------------ pull
def cmd_pull(a):
    open_log("31_pull.log", "a")
    jobs = load_jobs()
    jobs = jobs[jobs["year"].isin(a.years)]
    _, free = non_occupied()
    jobs = jobs[jobs["k3"].isin(free)]
    if a.test:
        pool = [k for k in sorted(set(jobs["k3"])) if k != TEST_K3]
        jobs = jobs[jobs["k3"].isin([TEST_K3] + pool[: a.test - 1])]
    req = list(dict.fromkeys((int(r.year), r.budgetCode) for r in jobs.itertuples()))
    todo = [j for j in req if not Path(ob.cache_path(ITEM, *j)).exists()]
    log(f"{time.strftime('%F %T')} pull {ITEM} years={a.years} units={jobs['k3'].nunique()} "
        f"requests={len(req)} cached={len(req) - len(todo)} to_fetch={len(todo)} workers={a.workers}")
    if todo:
        fails, t0, done = [], time.time(), 0
        with ThreadPoolExecutor(max_workers=a.workers) as ex:
            futs = {ex.submit(fetch, y, c): (y, c) for y, c in todo}
            for f in as_completed(futs):
                y, c = futs[f]
                try:
                    st = f.result()
                except Exception as e:
                    st = "fail:" + repr(e)[:120]
                done += 1
                if st.startswith("fail"):
                    fails.append((y, c, st))
                if done % 100 == 0 or done == len(todo):
                    rate = done / max(time.time() - t0, 1)
                    log(f"  {done}/{len(todo)}  fails={len(fails)}  {rate:.2f}/s  "
                        f"eta {(len(todo) - done) / max(rate, 1e-6) / 60:.0f} min")
        if fails:
            pd.DataFrame(fails, columns=["year", "code", "status"]).to_csv(
                FAILS, mode="a", header=not FAILS.exists(), index=False)
            log(f"{len(fails)} failures -> {FAILS} (first: {fails[0]}); rerun the same command to retry")
    if a.test:
        log("\ncheck per test unit and year (leaf total vs economic FAKT_AMT total):")
        for r in jobs.sort_values(["k3", "year"]).itertuples():
            lv, last = functional_leaves(ob.read_cached(ITEM, r.year, r.budgetCode))
            if lv is None:
                log(f"  {r.k3} {r.year}: no data")
                continue
            ref = economic_total(r.year, r.budgetCode)
            log(f"  {r.k3} {r.year}: month {last:2d}  leaf total {lv.sum():>16,.0f}  "
                + ("no economic cache" if ref is None else f"ratio {lv.sum() / ref:.4f}"))


# ---------------------------------------------------------------- shares
def cmd_shares(a):
    open_log("31_shares.log")
    jobs = load_jobs()
    keys, free = non_occupied()
    jobs = jobs[jobs["k3"].isin(free)]
    recs, full = [], []
    for r in jobs.itertuples():
        leaves, last = functional_leaves(ob.read_cached(ITEM, r.year, r.budgetCode))
        if leaves is None or leaves.empty:
            continue
        cl = civilian(leaves)
        civ = cl.sum()
        rec = {"k3": r.k3, "year": r.year, "code_source": r.code_source, "last_month": last}
        for col, pre in SHARES.items():
            rec[col] = cl[cl.index.str.startswith(pre)].sum() / civ if civ > 0 else float("nan")
        recs.append(rec)
        f = {"k3": r.k3, "year": r.year, "budgetCode": r.budgetCode, "last_month": last,
             "exp_leaf_total": leaves.sum(), "exp_civil": civ,
             "exp_excluded_r4": leaves[[is_excluded(c) for c in leaves.index]].sum()}
        f.update({f"fk_{c}": v for c, v in leaves.items()})
        full.append(f)
    if not recs:
        sys.exit("no cached programme data — run 'pull' first")

    out = keys[["k1", "k2", "k3", "name"]].merge(pd.DataFrame(recs), on="k3", how="inner")
    out = out.sort_values(["k3", "year"])
    num = [c for c in out.columns if c.startswith("sh_")]
    out[num] = out[num].round(5)
    out.to_csv(OUT, index=False)
    ff = pd.DataFrame(full).sort_values(["k3", "year"])
    ff.to_csv(OUT_FULL, index=False)
    log(f"wrote {OUT.name} rows={len(out)}  and {OUT_FULL.name} (internal, not tracked)")

    log("\ncoverage and medians by year (non-occupied):")
    for y, g in out.groupby("year"):
        log(f"  {y}: hromadas={len(g)}  months<12={int((g['last_month'] < 12).sum())}")
        log("      " + "  ".join(f"{c[3:]}={g[c].median():.3f}" for c in num))
    lo = out[out["sh_09_education"] < 0.05]
    if len(lo):
        log(f"\nWARNING {len(lo)} k3-years with education share < 0.05: "
            + ", ".join(f"{r.k3}/{r.year}" for r in lo.head(10).itertuples()))

    tot = []
    for r in ff.itertuples():
        ref = economic_total(r.year, r.budgetCode)
        if ref:
            tot.append(r.exp_leaf_total / ref)
    if tot:
        t = pd.Series(tot)
        log(f"\ncheck vs economic classification (03 cache): n={len(t)}  ratio median={t.median():.4f}  "
            f"within ±1 %={((t - 1).abs() <= 0.01).mean():.3f}  within ±5 %={((t - 1).abs() <= 0.05).mean():.3f}")
    vk = out[out["k3"] == TEST_K3]
    if len(vk):
        log("\nVerkhovyna 2602003:\n" + vk[["year", "last_month"] + num].to_string(index=False))

    src = "openbudget.gov.ua (MinFin/Treasury), localBudgetData EXPENSES classificationType=PROGRAM"
    lic = "Ukrainian open data, CMU Resolution 835 — attribution required"
    meth = ("share of civilian service expenditure: leaf functional codes of divisions 01, 03–10 "
            "excluding 0180 and 0380 (and division 02; rule R4); FAKT_AMT, FUND_TYP T, December YTD "
            "(2026: latest month); economic sub-rows de-duplicated")
    rows = [[c, src, lic, "ratio", "2021-2026", "hromada", f"functional {p}…; " + meth]
            for c, p in SHARES.items()]
    rows.append(["last_month", src, lic, "month", "2021-2026", "hromada",
                 "latest reporting month in the year (12 = full year)"])
    dd_new = pd.DataFrame(rows, columns=["indicator", "source", "licence", "unit", "year", "level", "method"])
    ddp = TIDY / "data_dictionary.csv"
    dd = pd.read_csv(ddp, dtype=str) if ddp.exists() else pd.DataFrame(columns=dd_new.columns)
    old = [c for c in dd["indicator"] if str(c).startswith("sh_") or c in ("subcodes_08", "subcodes_09")]
    dd = pd.concat([dd[~dd["indicator"].isin(set(dd_new["indicator"]) | set(old))], dd_new],
                   ignore_index=True)
    dd.to_csv(ddp, index=False)
    log(f"data dictionary updated: {len(dd)} indicators")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("mode", choices=["probe", "pull", "shares"])
    ap.add_argument("--k3", default=TEST_K3)
    ap.add_argument("--year", type=int, default=2025)
    ap.add_argument("--years", default="2021-2026")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--test", type=int, default=0)
    a = ap.parse_args()
    a.years = parse_years(a.years)
    {"probe": cmd_probe, "pull": cmd_pull, "shares": cmd_shares}[a.mode](a)


if __name__ == "__main__":
    main()
