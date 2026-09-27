#!/usr/bin/env python3
"""
31_functional_spending.py — local-budget expenditure by functional classification per hromada (k3),
2021–2026, from openbudget.gov.ua. Inputs for the three-sphere indices
(resilience/docs/threefolding_framework.md, section 6).

  python 31_functional_spending.py probe [--k3 2602003] [--year 2025] [--program]
  python 31_functional_spending.py pull  [--years 2021-2026] [--workers 4] [--test N]
  python 31_functional_spending.py shares

probe   one hromada, one year: fetches EXPENSES with classificationType=FUNCTIONAL (and PROGRAM with
        --program), prints the columns, fund types, months and every code with its name and annual
        amount, and says whether the sub-codes 0810/0820/0830/0960 are served. Run this first.
pull    all non-occupied hromadas; cache and resume as 03_openbudget.py
        (raw/openbudget/EXPENSES_FUNCTIONAL/<year>/<budgetCode>.csv.gz). Rerun the same command to
        retry failures. Responses that are not CSV are not cached (logged as failures).
shares  annual (December, or latest month for 2026) totals, FUND_TYP T, leaf codes only, ->
        tidy/functional_spending_k3_year.csv       tracked: shares only
        tidy/functional_spending_full_k3_year.csv  ignored: all divisions and UAH amounts

Budget codes: 03's jobs table (year-specific code, else the latest); 2026 uses the 2025 code, as
20_budget_quarterly.py does. Values: FAKT_AMT, cumulative year to date (period=MONTH).

Functional classification (Функціональна класифікація видатків, MinFin order 11/2011):
  01 general public services (administration)   06 housing and communal economy
  08 spiritual and physical development          0810 sport, 0820 culture and arts, 0830 media
  09 education                                   0960 extracurricular education (art/music schools)
  10 social protection and social security
Leaf codes only: a code is dropped when a more detailed code under it is present (e.g. 0800 when
0820 exists), so totals are not double-counted.

Rule R4 (military finance): division 02 (defence) is excluded from the denominator and never written
to the tracked table. The tracked table has no UAH amounts: with exp_total in
public/budget_long_k3_year.csv, a civilian total would reveal defence spending by subtraction.
Denominator of every share: civilian expenditure = all leaf codes of divisions 01 and 03–10.

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

ITEM = "EXPENSES_FUNCTIONAL"
ITEM_PROG = "EXPENSES_PROGRAM"
ob.ITEMS[ITEM] = {"budgetItem": "EXPENSES", "classificationType": "FUNCTIONAL"}
ob.ITEMS[ITEM_PROG] = {"budgetItem": "EXPENSES", "classificationType": "PROGRAM"}

TIDY, LOGS = BASE / "tidy", BASE / "logs"
OUT = TIDY / "functional_spending_k3_year.csv"
OUT_FULL = TIDY / "functional_spending_full_k3_year.csv"
FAILS = LOGS / "31_pull_failures.csv"
YEARS_ALL = [2021, 2022, 2023, 2024, 2025, 2026]
TEST_K3 = "2602003"                       # Verkhovyna
CIVIL_DIV = ["01", "03", "04", "05", "06", "07", "08", "09", "10"]
SHARES = {                                # column: code prefix (leaf codes starting with it)
    "sh_01_admin": "01",
    "sh_06_housing": "06",
    "sh_08_culture_sport": "08",
    "sh_0810_sport": "081",
    "sh_0820_culture_arts": "082",
    "sh_0830_media": "083",
    "sh_09_education": "09",
    "sh_0960_extracurricular": "096",
    "sh_10_social": "10",
}
SUBCODES = ["0810", "0820", "0830", "0960"]
# Amount column for actual spending. The FUNCTIONAL response has no FAKT_AMT (the ECONOMIC one has);
# its header repeats PLANS_AMT. Set from the probe: the column whose annual total matches the
# economic-classification FAKT_AMT total. None = FAKT_AMT only.
AMT_COL = None
_logf = None


def log(*a):
    m = " ".join(str(x) for x in a)
    print(m, flush=True)
    if _logf:
        _logf.write(m + "\n")
        _logf.flush()


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


def fetch(item, year, code):
    """ob.fetch_one caches any HTTP 200; keep the file only if it is a data CSV."""
    status, n = ob.fetch_one(item, year, code)
    p = Path(ob.cache_path(item, year, code))
    if status.startswith("fail") or not p.exists():
        return status
    body = gzip.open(p).read()
    if not body.strip():
        return "empty"                      # served, no rows (kept: an answer, not an error)
    if not looks_like_csv(body):
        p.rename(p.with_suffix(".bad"))
        return "fail:not csv " + repr(ob.decode(body[:120]))
    return status


def code_column(df):
    cols = [c for c in df.columns if c.upper().startswith("COD_")]
    pref = [c for c in cols if any(t in c.upper() for t in ("FK", "FUNC", "FKV"))]
    if pref:
        return pref[0]
    for c in cols:                          # 4-digit codes, divisions 01–10
        v = df[c].dropna().astype(str).str.strip()
        if len(v) and v.str.fullmatch(r"\d{3,4}").mean() > 0.9:
            return c
    return None


def name_column(df):
    names = [c for c in df.columns if "NAME" in c.upper()]
    return names[0] if names else None


def amount_column(df):
    if "FAKT_AMT" in df.columns:
        return "FAKT_AMT"
    if AMT_COL and AMT_COL in df.columns:
        return AMT_COL
    raise SystemExit(f"no actual-spending column: FAKT_AMT absent and AMT_COL={AMT_COL!r}; "
                     f"run 'probe' and set AMT_COL. Columns: {list(df.columns)}")


def num(sr):
    return pd.to_numeric(sr.astype("string").str.replace(",", ".", regex=False), errors="coerce").fillna(0)


def annual_leaves(df, amt=None):
    """December (or latest) cumulative amounts, FUND_TYP T, leaf codes -> (Series code->UAH, month)."""
    if df is None or df.empty or "REP_PERIOD" not in df.columns:
        return None, None
    cc = code_column(df)
    if cc is None:
        raise SystemExit(f"no functional code column found; columns: {list(df.columns)}")
    d = df.copy()
    d["m"] = d["REP_PERIOD"].str.extract(r"^(\d{1,2})\.")[0].astype(int)
    last = int(d["m"].max())
    d = d[(d["m"] == last) & (d["FUND_TYP"] == "T")].copy()
    d["code"] = d[cc].astype(str).str.strip().str.replace(r"\.0$", "", regex=True).str.zfill(4)
    d["amt"] = num(d[amt or amount_column(df)])
    s = d.groupby("code")["amt"].sum()
    codes = list(s.index)

    def stem(c):
        t = c.rstrip("0")
        return t if len(t) >= 2 else c[:2]
    parents = {c for c in codes for o in codes if o != c and o.startswith(stem(c))}
    return s[[c for c in codes if c not in parents]], last


# ----------------------------------------------------------------- probe
def cmd_probe(a):
    global _logf
    LOGS.mkdir(exist_ok=True)
    _logf = open(LOGS / "31_probe.log", "w", encoding="utf-8")
    jobs = load_jobs()
    sel = jobs[(jobs["k3"] == a.k3) & (jobs["year"] == a.year)]
    if sel.empty:
        sys.exit(f"no budget code for k3={a.k3} year={a.year} in the jobs table")
    code = sel.iloc[0]["budgetCode"]
    items = [ITEM] + ([ITEM_PROG] if a.program else [])
    for item in items:
        st = fetch(item, a.year, code)
        log(f"\n=== {item} k3={a.k3} year={a.year} budgetCode={code}: {st}")
        df = ob.read_cached(item, a.year, code)
        if df is None or df.empty:
            bad = Path(ob.cache_path(item, a.year, code)).with_suffix(".bad")
            if bad.exists():
                log("response (not CSV): " + ob.decode(gzip.open(bad).read()[:600]))
            else:
                log("no rows")
            continue
        log(f"rows={len(df)} columns={list(df.columns)}")
        log("FUND_TYP: " + str(df["FUND_TYP"].value_counts().to_dict()) if "FUND_TYP" in df else "no FUND_TYP")
        if "REP_PERIOD" in df:
            per = sorted(df["REP_PERIOD"].unique(), key=lambda s: s.split(".")[::-1])
            log(f"REP_PERIOD: {per[0]} … {per[-1]} ({len(per)} periods)")
        cc, nc = code_column(df), name_column(df)
        log(f"code column: {cc}   name column: {nc}")
        raw = ob.decode(gzip.open(ob.cache_path(item, a.year, code)).read()[:400]).splitlines()
        log("raw header: " + (raw[0] if raw else ""))
        log("raw row 1:  " + (raw[1] if len(raw) > 1 else ""))
        if cc is None:
            log("first rows:\n" + df.head(8).to_string())
            continue
        econ = ob.read_cached("EXPENSES_ECONOMIC", a.year, code)
        em = ob.expense_metrics(econ) if econ is not None and "FAKT_AMT" in econ.columns else None
        ref = em["exp_total"] if em and em.get("exp_total") else None
        if econ is not None:
            log(f"economic cache columns: {list(econ.columns)}")
        amt_cols = [c for c in df.columns if "AMT" in c.upper()]
        mon = int(df["REP_PERIOD"].str.extract(r"^(\d{1,2})\.")[0].astype(int).max())
        refs = "n/a" if ref is None else f"{ref:,.0f}"
        log(f"\namount columns, annual total over leaf codes (month {mon}, FUND_TYP T) "
            f"vs economic FAKT_AMT total {refs}:")
        best, best_err = None, None
        for c in amt_cols:
            lv, _ = annual_leaves(df, amt=c)
            tot = lv.sum()
            r = tot / ref if ref else float("nan")
            log(f"  {c:20s} {tot:>18,.0f}   ratio {r:8.4f}")
            if ref and tot > 0 and (best_err is None or abs(r - 1) < best_err):
                best, best_err = c, abs(r - 1)
        use = "FAKT_AMT" if "FAKT_AMT" in df.columns else (AMT_COL if AMT_COL in df.columns else best)
        log(f"best match: {best} (|ratio-1|={best_err if best_err is None else round(best_err, 4)});  "
            f"used below: {use}")
        if use is None:
            continue
        d = df.copy()
        d["m"] = d["REP_PERIOD"].str.extract(r"^(\d{1,2})\.")[0].astype(int)
        d = d[(d["m"] == d["m"].max()) & (d["FUND_TYP"] == "T")].copy()
        d["code"] = d[cc].astype(str).str.strip().str.zfill(4)
        d["amt"] = num(d[use])
        g = d.groupby("code").agg(amt=("amt", "sum"),
                                  name=(nc, "first") if nc else ("amt", "size")).reset_index()
        pd.set_option("display.max_colwidth", 70)
        pd.set_option("display.width", 160)
        log(f"\ncodes, month {int(d['m'].max())}, FUND_TYP T, {use} ({len(g)}):\n"
            + g.to_string(index=False, formatters={"amt": "{:,.0f}".format}))
        if item == ITEM:
            leaves, last = annual_leaves(df, amt=use)
            civ = leaves[leaves.index.str[:2].isin(CIVIL_DIV)].sum()
            log(f"\nleaf codes: {len(leaves)}   civilian total (excl. 02): {civ:,.0f}   "
                f"division 02 present: {bool((leaves.index.str[:2] == '02').any())}   "
                f"codes outside 01–10: {sorted(c for c in leaves.index if c[:2] not in CIVIL_DIV + ['02'])}")
            served = {sc: any(c.startswith(sc[:3]) for c in g["code"]) for sc in SUBCODES}
            log("sub-codes served: " + ", ".join(f"{sc}={'yes' if v else 'no'}" for sc, v in served.items()))
            for col, pre in SHARES.items():
                v = leaves[leaves.index.str.startswith(pre)].sum()
                log(f"  {col:26s} {v / civ if civ else float('nan'):7.3f}")


# ------------------------------------------------------------------ pull
def cmd_pull(a):
    global _logf
    LOGS.mkdir(exist_ok=True)
    _logf = open(LOGS / "31_pull.log", "a", encoding="utf-8")
    jobs = load_jobs()
    jobs = jobs[jobs["year"].isin(a.years)]
    _, free = non_occupied()
    jobs = jobs[jobs["k3"].isin(free)]
    if a.test:
        pool = [k for k in sorted(set(jobs["k3"])) if k != TEST_K3]
        jobs = jobs[jobs["k3"].isin([TEST_K3] + pool[: a.test - 1])]
    req = list(dict.fromkeys((int(r.year), r.budgetCode) for r in jobs.itertuples()))
    cached = lambda y, c: Path(ob.cache_path(ITEM, y, c)).exists()  # noqa: E731
    todo = [j for j in req if not cached(*j)]
    log(f"{time.strftime('%F %T')} pull {ITEM} years={a.years} units={jobs['k3'].nunique()} "
        f"requests={len(req)} cached={len(req) - len(todo)} to_fetch={len(todo)} workers={a.workers}")
    if not todo:
        return
    fails, t0, done = [], time.time(), 0
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = {ex.submit(fetch, ITEM, y, c): (y, c) for y, c in todo}
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


# ---------------------------------------------------------------- shares
def cmd_shares(a):
    global _logf
    LOGS.mkdir(exist_ok=True)
    _logf = open(LOGS / "31_shares.log", "w", encoding="utf-8")
    jobs = load_jobs()
    keys, free = non_occupied()
    jobs = jobs[jobs["k3"].isin(free)]
    recs, full = [], []
    for r in jobs.itertuples():
        df = ob.read_cached(ITEM, r.year, r.budgetCode)
        if df is None:
            continue
        leaves, last = annual_leaves(df)
        if leaves is None or leaves.empty:
            continue
        div = leaves.index.str[:2]
        civ = leaves[div.isin(CIVIL_DIV)].sum()
        rec = {"k3": r.k3, "year": r.year, "code_source": r.code_source, "last_month": last,
               "subcodes_08": bool(leaves.index.str.match(r"08[1-4]").any()),
               "subcodes_09": bool(leaves.index.str.match(r"09[1-9]").any())}
        for col, pre in SHARES.items():
            rec[col] = leaves[leaves.index.str.startswith(pre)].sum() / civ if civ > 0 else float("nan")
        recs.append(rec)
        f = {"k3": r.k3, "year": r.year, "budgetCode": r.budgetCode, "last_month": last,
             "exp_leaf_total": leaves.sum(), "exp_civil": civ}
        f.update({f"d{d}": leaves[div == d].sum() for d in sorted(set(div))})
        f.update({f"c{c}": v for c, v in leaves.items()
                  if c[:3] in ("081", "082", "083", "084", "096")})
        full.append(f)
    if not recs:
        sys.exit("no cached functional data — run 'pull' first")

    out = pd.DataFrame(recs)
    # sub-code shares only where the sub-codes are served; else NaN, never 0
    for col in ("sh_0810_sport", "sh_0820_culture_arts", "sh_0830_media"):
        out.loc[~out["subcodes_08"], col] = float("nan")
    out.loc[~out["subcodes_09"], "sh_0960_extracurricular"] = float("nan")
    out = keys[["k1", "k2", "k3", "name"]].merge(out, on="k3", how="inner")
    out = out.sort_values(["k3", "year"])
    num = [c for c in out.columns if c.startswith("sh_")]
    out[num] = out[num].round(5)
    out.to_csv(OUT, index=False)
    pd.DataFrame(full).sort_values(["k3", "year"]).to_csv(OUT_FULL, index=False)
    log(f"wrote {OUT.name} rows={len(out)}  and {OUT_FULL.name} (internal, not tracked)")

    log("\ncoverage and medians by year (non-occupied):")
    for y, g in out.groupby("year"):
        part = int((g["last_month"] < 12).sum())
        log(f"  {y}: hromadas={len(g)}  months<12={part}  subcodes_08={g['subcodes_08'].mean():.2f}  "
            f"subcodes_09={g['subcodes_09'].mean():.2f}")
        log("      " + "  ".join(f"{c[3:]}={g[c].median():.3f}" for c in num if g[c].notna().any()))
    lo = out[out["sh_09_education"] < 0.05]
    if len(lo):
        log(f"\nWARNING {len(lo)} k3-years with education share < 0.05 (check codes): "
            + ", ".join(f"{r.k3}/{r.year}" for r in lo.head(10).itertuples()))
    vk = out[out["k3"] == TEST_K3]
    if len(vk):
        log("\nVerkhovyna 2602003:\n" + vk[["year", "last_month"] + num].to_string(index=False))

    ff = pd.DataFrame(full)
    econ = pd.read_csv(TIDY / "budget_long_k3_year.csv", dtype={"k3": str}) \
        if (TIDY / "budget_long_k3_year.csv").exists() else None
    if econ is not None and "exp_total" in econ:
        econ["k3"] = econ["k3"].str.zfill(7)
        m = ff.merge(econ[["k3", "year", "exp_total"]], on=["k3", "year"])
        m = m[m["exp_total"] > 0]
        if len(m):
            r = m["exp_leaf_total"] / m["exp_total"]
            log(f"\ncheck vs economic classification (03): n={len(m)}  ratio median={r.median():.4f}  "
                f"share within ±1 %={((r - 1).abs() <= 0.01).mean():.3f}")

    src = "openbudget.gov.ua (MinFin/Treasury), localBudgetData EXPENSES classificationType=FUNCTIONAL"
    lic = "Ukrainian open data, CMU Resolution 835 — attribution required"
    meth = ("share of civilian expenditure (leaf functional codes of divisions 01, 03–10; division 02 "
            "defence excluded, rule R4), FUND_TYP T, December YTD (2026: latest month)")
    rows = [[c, src, lic, "ratio", "2021-2026", "hromada", f"functional {p}…; " + meth]
            for c, p in SHARES.items()]
    rows += [["subcodes_08", src, lic, "flag", "2021-2026", "hromada",
              "sub-codes 081x–084x served; if false the 0810/0820/0830 shares are empty"],
             ["subcodes_09", src, lic, "flag", "2021-2026", "hromada",
              "sub-codes 091x–099x served; if false the 0960 share is empty"]]
    dd_new = pd.DataFrame(rows, columns=["indicator", "source", "licence", "unit", "year", "level", "method"])
    ddp = TIDY / "data_dictionary.csv"
    dd = pd.read_csv(ddp, dtype=str) if ddp.exists() else pd.DataFrame(columns=dd_new.columns)
    dd = pd.concat([dd[~dd["indicator"].isin(dd_new["indicator"])], dd_new], ignore_index=True)
    dd.to_csv(ddp, index=False)
    log(f"data dictionary updated: {len(dd)} indicators")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("mode", choices=["probe", "pull", "shares"])
    ap.add_argument("--k3", default=TEST_K3)
    ap.add_argument("--year", type=int, default=2025)
    ap.add_argument("--program", action="store_true", help="probe: also fetch PROGRAM classification")
    ap.add_argument("--years", default="2021-2026")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--test", type=int, default=0)
    a = ap.parse_args()
    a.years = parse_years(a.years)
    {"probe": cmd_probe, "pull": cmd_pull, "shares": cmd_shares}[a.mode](a)


if __name__ == "__main__":
    main()
