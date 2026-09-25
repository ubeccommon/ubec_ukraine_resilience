#!/usr/bin/env python3
"""
20_budget_quarterly.py — quarterly local-budget flows per hromada, 2021 … latest.

  python 20_budget_quarterly.py pull2026 [--workers 4]   # 2026 YTD with 2025 budget codes
  python 20_budget_quarterly.py [build]                  # quarterly table + summary

Source: openbudget INCOMES cache (raw/openbudget/INCOMES/<year>/<code>.csv.gz, pulled by
03_openbudget.py; period=MONTH, FAKT_AMT cumulative YTD). Year-specific budget codes from
03's jobs table (tidy/budget_jobs.csv; same crosswalk as v1.1). 2026 is not in 03's YEARS:
it is pulled here with the 2025 codes via 03's fetch_one (03's crosswalk untouched).

Definitions (as 03 income_metrics, applied to every month):
  rev_total  FUND_TYP T, all codes          transfers  T, 40000000–49999999
  own_gf     FUND_TYP C, codes < 40000000   pdfo       T, 11010000–11019999
  pdfo_mil   PIT lines naming 'військовослуж'; pdfo_civ = pdfo − pdfo_mil
Quarterly flow = cumulative(quarter-end month) − cumulative(previous quarter end); Q1 = month 3.
Missing quarter-end month -> NaN (no imputation; incomplete 2026 quarters stay empty).
Indices: <v>_r21 = v / same quarter 2021 (nominal); <v>_rel = _r21 / national median of
  _r21 in that quarter (non-occupied; inflation-neutral relative position).
Military PIT went to the state budget from Q4 2023: pdfo_mil ~0 afterwards; pdfo_civ is
  comparable across the break only insofar as military lines are named as such.
Output: tidy/budget_quarterly_k3.csv
Biases: PIT booked at employer address; military PIT identified by line name; budget-code
  changes across years handled by 03's crosswalk; population denominator GHS-POP 2020.
Licence: openbudget.gov.ua, CMU resolution 835 (open data).
"""
import sys, importlib, time, argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
if "__name__" not in (BASE / "03_openbudget.py").read_text():
    sys.exit("03_openbudget.py has no __main__ guard")
sys.path.insert(0, str(BASE))
ob = importlib.import_module("03_openbudget")
TIDY = BASE / "tidy"
CTRL = BASE.parent / "viina" / "qgis" / "hromada_control.gpkg"
RES = TIDY / "resilience_v1_k3.csv"
OUT = TIDY / "budget_quarterly_k3.csv"
CARP = {"21", "26", "46", "73"}
QEND = [3, 6, 9, 12]
Y_EXTRA = 2026


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def load_jobs():
    if Path(ob.JOBS).exists():
        j = pd.read_csv(ob.JOBS, dtype=str)
    else:
        j = ob.build_jobs(pd.read_csv(ob.XW, dtype=str))
    j["k3"] = j["k3"].astype(str).str.zfill(7)
    j["year"] = j["year"].astype(int)
    j["budgetCode"] = j["budgetCode"].astype(str).str.zfill(10)
    return j


def occupied_k3():
    try:
        import pyogrio
        c = pyogrio.read_dataframe(CTRL, read_geometry=False)
        c["k3"] = c["k3"].astype(str).str.zfill(7)
        return set(c.loc[c["occupied"].fillna(0).astype(int) == 1, "k3"])
    except Exception as e:
        log(f"occupied flag not read ({e})")
        return set()


# ------------------------------------------------------------ pull 2026
def cmd_pull2026(workers):
    jobs = load_jobs()
    occ = occupied_k3()
    j = jobs[(jobs["year"] == 2025) & ~jobs["k3"].isin(occ)]
    codes = sorted(set(j["budgetCode"]))
    path = lambda c: Path(ob.cache_path("INCOMES", Y_EXTRA, c))  # noqa: E731
    todo = [c for c in codes if not path(c).exists()]
    log(f"{Y_EXTRA}: {len(codes)} budget codes (2025 codes, non-occupied), "
        f"cached {len(codes) - len(todo)}, to fetch {len(todo)}")
    if not todo:
        return
    try:
        ob.warm_up()
    except Exception as e:
        log(f"warm-up failed ({e}) — continuing")
    fails = []
    t0 = time.time()
    with ThreadPoolExecutor(workers) as ex:
        futs = {ex.submit(ob.fetch_one, "INCOMES", Y_EXTRA, c): c for c in todo}
        for i, f in enumerate(as_completed(futs), 1):
            c = futs[f]
            try:
                f.result()
                if not path(c).exists():
                    fails.append((c, "no file written"))
            except Exception as e:
                fails.append((c, repr(e)[:120]))
            if i % 100 == 0 or i == len(todo):
                log(f"  {i}/{len(todo)} fails={len(fails)} {i / (time.time() - t0):.2f}/s")
    if fails:
        pd.DataFrame(fails, columns=["code", "error"]).to_csv(
            TIDY / f"budget_fails_{Y_EXTRA}.csv", index=False)
        log(f"{len(fails)} failures -> tidy/budget_fails_{Y_EXTRA}.csv (rerun to retry)")
    sample = [c for c in codes if path(c).exists()][:50]
    lm = []
    for c in sample:
        cum = monthly_cum(path(c))
        if cum is not None and len(cum):
            lm.append(int(cum.index.max()))
    if lm:
        log(f"{Y_EXTRA} last reported month in sample of {len(lm)}: "
            f"{pd.Series(lm).value_counts().sort_index().to_dict()}")


# ------------------------------------------------------------ build
def monthly_cum(path):
    d = pd.read_csv(path, sep=";", dtype=str, compression="gzip")
    if d.empty or "REP_PERIOD" not in d:
        return None
    d["m"] = pd.to_numeric(d["REP_PERIOD"].str.extract(r"^(\d{1,2})\.")[0], errors="coerce")
    d = d.dropna(subset=["m"])
    d["m"] = d["m"].astype(int)
    d["amt"] = pd.to_numeric(d["FAKT_AMT"].astype("string").str.replace(",", ".", regex=False),
                             errors="coerce").fillna(0)
    d["code"] = pd.to_numeric(d["COD_INCO"], errors="coerce")
    T, C = d[d["FUND_TYP"] == "T"], d[d["FUND_TYP"] == "C"]
    pm = (T["code"] >= 11010000) & (T["code"] < 11020000)
    mil = T["NAME_INC"].str.contains("військовослуж", case=False, na=False)
    months = sorted(d["m"].unique())
    return pd.DataFrame({
        "rev_total": T.groupby("m")["amt"].sum(),
        "transfers": T[(T["code"] >= 40000000) & (T["code"] < 50000000)].groupby("m")["amt"].sum(),
        "own_gf": C[C["code"] < 40000000].groupby("m")["amt"].sum(),
        "pdfo": T[pm].groupby("m")["amt"].sum(),
        "pdfo_mil": T[pm & mil].groupby("m")["amt"].sum(),
    }).reindex(months).fillna(0)


def quarterly(cum):
    c = cum.reindex(QEND)
    f = c.diff()
    f.iloc[0] = c.iloc[0]
    f.index = [1, 2, 3, 4]
    return f


def update_dictionary(years):
    dd_fn = TIDY / "data_dictionary.csv"
    src = "openbudget.gov.ua localBudgetData INCOMES, period=MONTH (YTD cumulative)"
    lic = "CMU resolution 835 (open data)"
    yr = f"{min(years)}-{max(years)}"
    new = pd.DataFrame([
        ("bq_own_gf", src, lic, "UAH", yr, "hromada x quarter",
         "Own general-fund revenue (C, codes < 4xxxxxxx), quarterly flow from YTD cumulative"),
        ("bq_pdfo_civ", src, lic, "UAH", yr, "hromada x quarter",
         "Civilian PIT: 1101xxxx minus lines naming військовослужбовці; military PIT to state budget from Q4 2023"),
        ("bq_transfer_dep", src, lic, "share", yr, "hromada x quarter",
         "Transfers (4xxxxxxx) / total revenue, FUND_TYP T"),
        ("bq_own_gf_rel", src, lic, "ratio", yr, "hromada x quarter",
         "own_gf / same quarter 2021, divided by national median of that ratio (inflation-neutral)"),
        ("bq_pdfo_civ_rel", src, lic, "ratio", yr, "hromada x quarter",
         "pdfo_civ / same quarter 2021, divided by national median (inflation-neutral)"),
    ], columns=["indicator", "source", "licence", "unit", "year", "level", "method"])
    if dd_fn.exists():
        dd = pd.read_csv(dd_fn)
        dd = dd[~dd["indicator"].astype(str).str.startswith("bq_")]
        for col in dd.columns:
            if col not in new:
                new[col] = ""
        dd = pd.concat([dd, new[dd.columns]], ignore_index=True)
    else:
        dd = new
    dd.to_csv(dd_fn, index=False)
    log(f"data_dictionary.csv: {len(dd)} rows ({len(new)} bq_*)")


def cmd_build():
    jobs = load_jobs()
    d26 = Path(ob.cache_path("INCOMES", Y_EXTRA, "0")).parent
    if d26.exists() and any(d26.glob("*.csv.gz")):
        j26 = jobs[jobs["year"] == 2025].copy()
        j26["year"] = Y_EXTRA
        jobs = pd.concat([jobs, j26], ignore_index=True)
    years = sorted(int(y) for y in jobs["year"].unique())
    log(f"jobs: {len(jobs)} ({jobs['k3'].nunique()} units, years {years})")
    shared = jobs.groupby(["year", "budgetCode"])["k3"].nunique()
    if (shared > 1).any():
        log(f"budget codes shared by >1 unit: {int((shared > 1).sum())} (values duplicated)")

    cache, rows, missing = {}, [], {}
    for r in jobs.itertuples():
        key = (r.year, r.budgetCode)
        if key not in cache:
            p = Path(ob.cache_path("INCOMES", r.year, r.budgetCode))
            cache[key] = monthly_cum(p) if p.exists() else None
        cum = cache[key]
        if cum is None:
            missing[int(r.year)] = missing.get(int(r.year), 0) + 1
            continue
        q = quarterly(cum)
        q["q"] = q.index
        q["k3"], q["year"] = r.k3, int(r.year)
        q["last_month"] = int(cum.index.max())
        rows.append(q)
    if missing:
        log(f"no cached file (unit-years; occupied units have none): {dict(sorted(missing.items()))}")
    d = pd.concat(rows, ignore_index=True)
    d["pdfo_civ"] = d["pdfo"] - d["pdfo_mil"]
    d["transfer_dep"] = d["transfers"] / d["rev_total"].where(d["rev_total"] > 0)

    res = pd.read_csv(RES, dtype={"k3": str})
    res["k3"] = res["k3"].str.zfill(7)
    d = d.merge(res[["k3", "pop_ghs_2020"]], on="k3", how="left")
    for v in ("own_gf", "pdfo_civ"):
        d[f"{v}_pc"] = d[v] / d["pop_ghs_2020"].where(d["pop_ghs_2020"] > 0)

    d["occupied"] = d["k3"].isin(occupied_k3()).astype(int)
    for v in ("own_gf", "pdfo_civ", "rev_total"):
        b = d.loc[d["year"] == 2021, ["k3", "q", v]].rename(columns={v: "_b"})
        b["_b"] = b["_b"].where(b["_b"] > 0)
        d = d.merge(b, on=["k3", "q"], how="left")
        d[f"{v}_r21"] = d[v] / d["_b"]
        med = (d[d["occupied"] == 0].groupby(["year", "q"])[f"{v}_r21"].median()
                 .rename("_m").reset_index())
        d = d.merge(med, on=["year", "q"], how="left")
        d[f"{v}_rel"] = d[f"{v}_r21"] / d["_m"]
        d = d.drop(columns=["_b", "_m"])

    d = d.sort_values(["k3", "year", "q"])
    d.to_csv(OUT, index=False)
    log(f"wrote {OUT.relative_to(BASE)} rows={len(d)} units={d['k3'].nunique()}")

    neg = int((d[["own_gf", "pdfo_civ"]] < 0).any(axis=1).sum())
    log(f"unit-quarters with negative own_gf or pdfo_civ flow (refunds/corrections): {neg}")

    if "own_rev_gf_2025" in res:
        a25 = d[d["year"] == 2025].groupby("k3")["own_gf"].sum(min_count=4)
        chk = res.set_index("k3")["own_rev_gf_2025"].reindex(a25.index)
        rr = (a25 / chk.where(chk > 0)).dropna()
        log(f"check 2025 sum(Q1–Q4) own_gf / v1.1 own_rev_gf_2025: n={len(rr)}, "
            f"median {rr.median():.4f}, within 1 %: {(rr.sub(1).abs() < .01).mean():.1%}")

    s = d[d["occupied"] == 0].copy()
    s["carp"] = s["k3"].str[:2].isin(CARP)
    out = []
    for (y, q), g in s.groupby(["year", "q"]):
        c = g[g["carp"]]
        out.append({"year": y, "q": q, "n": int(g["own_gf"].notna().sum()),
                    "own_r21": g["own_gf_r21"].median(),
                    "civPIT_r21": g["pdfo_civ_r21"].median(),
                    "carp_own_rel": c["own_gf_rel"].median(),
                    "carp_pit_rel": c["pdfo_civ_rel"].median(),
                    "transf_dep": g["transfer_dep"].median(),
                    "mil_share": g["pdfo_mil"].sum() / g["pdfo"].sum() if g["pdfo"].sum() else np.nan})
    pd.set_option("display.width", 160)
    print("\nnon-occupied hromadas (medians; _r21 nominal vs same quarter 2021):")
    print(pd.DataFrame(out).to_string(index=False, float_format=lambda v: f"{v:.2f}"))
    update_dictionary(years)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", nargs="?", default="build", choices=["build", "pull2026"])
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    if a.cmd == "pull2026":
        cmd_pull2026(a.workers)
    else:
        cmd_build()
