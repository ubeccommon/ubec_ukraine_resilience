#!/usr/bin/env python3
"""
32_sphere_indices.py — three-sphere indices per hromada (k3): economic, rights and cultural life,
2021 baseline and 2025, plus the two budget sub-indices. Step 5 of the three-sphere analysis
(resilience/docs/threefolding_framework.md, section 6).

  python 32_sphere_indices.py            # build, diagnostics, outputs
  python 32_sphere_indices.py --check    # inputs and coverage only, no outputs

Method (as the capacity index, 11_composite.py): each indicator is transformed (log for amounts per
resident, log1p for counts), signed by its direction, winsorised at the 2nd/98th percentile and
turned into a percentile rank among non-occupied hromadas. A sphere index is the mean of its ranks,
computed where at least MIN_IND indicators are present. Higher = stronger. Night-time light is in no
index (it is the outcome in the association step). Per-resident terms use pop_ghs_2020.

Indicators (direction):
  economic 2021  three separate tax bases per resident (+): civilian PIT (work and earnings), single
                 tax (codes 1805xxxx: sole proprietors, small firms, group-4 farmers), property and
                 land payments (codes 1801xxxx). Total own revenue is not used here: PIT is its
                 largest part (rank correlation 0.93 with PIT per resident), so it would count PIT
                 twice; it stays in budget_econ_2025.
  economic 2025  the same three for 2025 (+), civilian PIT growth 2021–25 (+)
  rights   2021  transfer dependency (−), capital-expenditure share (+), social protection share
                 of civilian spending (+), candidates per council seat 2020, relative to the
                 electoral system (+)
  rights   2025  transfer dependency (−), capital-expenditure share 2023–25 (+), social protection
                 share (+), DREAM projects per 10,000 (+)
  cultural 2021  culture and arts, education, extracurricular education shares of civilian
                 spending (+)
  cultural 2025  the same three (+), general secondary schools in operation per 10,000 (+)
Budget sub-indices 2025 (the fiscal capacity index split, framework decision of 26 Sep 2026):
  budget_econ_2025   own revenue per resident, civilian PIT growth
  budget_rights_2025 transfer dependency (−), capital-expenditure share
Balance: w_econ, w_rights, w_cult = each sphere index / sum of the three (2025 and 2021) — the input
of the ternary balance map; dominant = sphere with the largest weight.

Inputs (all R4-free): public/budget_long_k3_year.csv (civilian revenue; capex 2021 after
  03_openbudget.py pull --items EXPENSES_ECONOMIC --years 2021, 03 indicators, 25_public_tables.py),
  public/resilience_v1_k3.csv (PIT growth, capex share 2023–25, DREAM), openbudget INCOMES cache (single
  tax, codes 1805xxxx), tidy/functional_spending_k3_year.csv (31_), tidy/elections_2020_k3.csv (33_),
  tidy/schools_k3.csv (34_), tidy/population_k3.csv, tidy/frontline_zone_k3.csv.
Outputs:
  tidy/sphere_indices_k3.csv        hromada values (indices, weights, n of indicators) — tracked
  tidy/sphere_inputs_k3.csv         the indicator values used (for audit) — tracked
  tidy/sphere_indices_r3_raion.csv  population-weighted raion values for every raion touched by the
                                    front-line and border zone (rule R3: maps show these, not the
                                    zone hromadas) — tracked
  tidy/data_dictionary.csv rows, logs/32_sphere_indices.log
Rules: R2 — no night light; R3 — zone hromadas are replaced by raion values on maps and in the data
package (30_data_package.py aggregates whole raions); R4 — only civilian revenue fields are read.
"""
import argparse
import importlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
TIDY, PUB, LOGS = BASE / "tidy", BASE / "public", BASE / "logs"
OUT = TIDY / "sphere_indices_k3.csv"
OUT_IN = TIDY / "sphere_inputs_k3.csv"
OUT_R3 = TIDY / "sphere_indices_r3_raion.csv"
MIN_IND = 3
CARP = {"21": "Закарпатська", "26": "Івано-Франківська", "46": "Львівська", "73": "Чернівецька"}
KEYS = {"k1": str, "k2": str, "k3": str}

# indicator: (direction, transform)
SPHERES = {
    ("econ", 2021): {"pdfo_civ_pc_2021": (+1, "log"), "single_tax_pc_2021": (+1, "log"),
                     "property_tax_pc_2021": (+1, "log")},
    ("econ", 2025): {"pdfo_civ_pc_2025": (+1, "log"), "single_tax_pc_2025": (+1, "log"),
                     "property_tax_pc_2025": (+1, "log"), "pdfo_civ_growth_rel_2125": (+1, "log")},
    ("rights", 2021): {"transfer_dep_civ_2021": (-1, None), "capex_share_2021": (+1, None),
                       "sh_10_social_2021": (+1, None), "cand_per_seat_rel_2020": (+1, "log")},
    ("rights", 2025): {"transfer_dep_civ_2025": (-1, None), "capex_share_2325": (+1, None),
                       "sh_10_social_2025": (+1, None), "dream_per10k": (+1, "log1p")},
    ("cult", 2021): {"sh_082_culture_arts_2021": (+1, None), "sh_09_education_2021": (+1, None),
                     "sh_0960_extracurricular_2021": (+1, None)},
    ("cult", 2025): {"sh_082_culture_arts_2025": (+1, None), "sh_09_education_2025": (+1, None),
                     "sh_0960_extracurricular_2025": (+1, None), "schools_per10k_2026": (+1, "log")},
}
SUB = {"budget_econ_2025": {"own_gf_civ_pc_2025": (+1, "log"), "pdfo_civ_growth_rel_2125": (+1, "log")},
       "budget_rights_2025": {"transfer_dep_civ_2025": (-1, None), "capex_share_2325": (+1, None)}}
FUNC = ["sh_082_culture_arts", "sh_09_education", "sh_0960_extracurricular", "sh_10_social"]
_logf = None


def log(*a):
    m = " ".join(str(x) for x in a)
    print(m, flush=True)
    if _logf:
        _logf.write(m + "\n")
        _logf.flush()


def zk(df):
    for k in ("k1", "k2", "k3"):
        if k in df:
            df[k] = df[k].astype(str).str.replace(r"\.0$", "", regex=True)
    if "k3" in df:
        df["k3"] = df["k3"].str.zfill(7)
    return df


# ---------------------------------------------------------------- inputs
LOCAL_TAX = {"single_tax": "1805", "property_tax": "1801"}


def local_taxes():
    """Single tax (1805xxxx) and property/land payments (1801xxxx), FUND_TYP T, December YTD,
    leaf codes, 2021 and 2025, from the openbudget INCOMES cache."""
    sys.path.insert(0, str(BASE))
    ob = importlib.import_module("03_openbudget")
    jobs = pd.read_csv(ob.JOBS, dtype=str) if Path(ob.JOBS).exists() else ob.build_jobs(pd.read_csv(ob.XW, dtype=str))
    jobs["k3"] = jobs["k3"].str.zfill(7)
    rows = []
    for r in jobs[jobs["year"].isin(["2021", "2025"])].itertuples():
        d, last = ob.annual(ob.read_cached("INCOMES", int(r.year), r.budgetCode), "COD_INCO")
        if d is None:
            continue
        t = d[(d["FUND_TYP"] == "T")].copy()
        t["c"] = t["COD_INCO"].astype(str).str.strip().str.zfill(8)
        rec = {"k3": r.k3, "year": int(r.year), "inc_last_month": last}
        for name, pre in LOCAL_TAX.items():
            u = t[t["c"].str.startswith(pre)]
            codes = list(u["c"].unique())
            par = {c for c in codes for o in codes if o != c and o.startswith(c.rstrip("0") or c)}
            rec[name] = u.loc[~u["c"].isin(par), "amt"].sum()
        rows.append(rec)
    st = pd.DataFrame(rows)
    log(f"  local taxes: {len(st)} k3-years from the INCOMES cache "
        f"({st.groupby('year').size().to_dict() if len(st) else {}})")
    return st


def load_inputs():
    keys = zk(pd.read_csv(TIDY / "keys_hromada.csv", dtype=str))[["k1", "k2", "k3", "name"]]
    pop = zk(pd.read_csv(TIDY / "population_k3.csv", dtype={"k3": str}))
    pop = pop[["k3", "pop_ghs_2020", "occupied"]]
    pop["occupied"] = pop["occupied"].astype(str).str.lower().eq("true")
    pop.loc[pop["pop_ghs_2020"] < 100, "pop_ghs_2020"] = np.nan
    df = keys.merge(pop, on="k3", how="left")
    P = df.set_index("k3")["pop_ghs_2020"]

    bl = zk(pd.read_csv(PUB / "budget_long_k3_year.csv", dtype={"k3": str}))
    for y in (2021, 2025):
        b = bl[bl["year"] == y].set_index("k3")
        df[f"own_gf_civ_pc_{y}"] = df["k3"].map(b["own_gf_civ"]) / df["k3"].map(P)
        df[f"pdfo_civ_pc_{y}"] = df["k3"].map(b["pdfo_civ"]) / df["k3"].map(P)
        rt = b["rev_total_civ"].where(b["rev_total_civ"] > 0)
        df[f"transfer_dep_civ_{y}"] = df["k3"].map(b["transfers"] / rt)
        if y == 2021:
            et = b["exp_total"].where(b["exp_total"] > 0)
            df["capex_share_2021"] = df["k3"].map(b["capex"] / et)
    rv = zk(pd.read_csv(PUB / "resilience_v1_k3.csv", dtype=KEYS)).set_index("k3")
    for c in ("pdfo_civ_growth_rel_2125", "capex_share_2325", "dream_per10k"):
        df[c] = df["k3"].map(rv[c])

    st = local_taxes()
    for y in (2021, 2025):
        for name in LOCAL_TAX:
            s = st[st["year"] == y].set_index("k3")[name] if len(st) else pd.Series(dtype=float)
            df[f"{name}_pc_{y}"] = df["k3"].map(s) / df["k3"].map(P)

    fp = TIDY / "functional_spending_k3_year.csv"
    if fp.exists():
        fs = zk(pd.read_csv(fp, dtype={"k3": str}))
        for y in (2021, 2025):
            f = fs[(fs["year"] == y) & (fs["last_month"] == 12)].set_index("k3")
            for c in FUNC:
                df[f"{c}_{y}"] = df["k3"].map(f[c]) if c in f else np.nan
    else:
        log("  functional_spending_k3_year.csv not found — run 31_functional_spending.py shares")
        for y in (2021, 2025):
            for c in FUNC:
                df[f"{c}_{y}"] = np.nan

    el = zk(pd.read_csv(TIDY / "elections_2020_k3.csv", dtype={"k3": str})).set_index("k3")
    df["cand_per_seat_rel_2020"] = df["k3"].map(el["cand_per_seat_rel"])
    sc = zk(pd.read_csv(TIDY / "schools_k3.csv", dtype={"k3": str})).set_index("k3")
    df["schools_per10k_2026"] = df["k3"].map(sc["schools_per10k_2026"])
    return df


# ---------------------------------------------------------------- index
def transform(s, how):
    s = pd.to_numeric(s, errors="coerce")
    if how == "log":
        return np.log(s.where(s > 0))
    if how == "log1p":
        return np.log1p(s.clip(lower=0))
    return s


def ranks(df, spec, free):
    out = pd.DataFrame(index=df.index)
    for c, (d, how) in spec.items():
        v = transform(df[c], how) * d
        v = v.where(free)
        v = v.clip(v.quantile(0.02), v.quantile(0.98))
        out[c] = v.rank(pct=True)
    return out


def index(R, need):
    return R.mean(axis=1).where(R.notna().sum(axis=1) >= need)


def wmean(v, w):
    ok = v.notna() & w.notna() & (w > 0)
    return float((v[ok] * w[ok]).sum() / w[ok].sum()) if ok.any() else np.nan


# ---------------------------------------------------------------- main
def main():
    global _logf
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    LOGS.mkdir(exist_ok=True)
    _logf = open(LOGS / "32_sphere_indices.log", "w", encoding="utf-8")

    df = load_inputs()
    free = ~df["occupied"].fillna(True)
    log(f"hromadas: {len(df)}, non-occupied: {int(free.sum())}")
    log("\ncoverage of indicators among non-occupied hromadas:")
    allind = sorted({c for s in SPHERES.values() for c in s})
    for c in allind:
        v = pd.to_numeric(df.loc[free, c], errors="coerce")
        log(f"  {c:32s} n={v.notna().sum():5d}  median={v.median():12.4f}" if v.notna().any()
            else f"  {c:32s} n=    0  (missing input)")
    if a.check:
        return

    res = df[["k1", "k2", "k3", "name"]].copy()
    inp = df[["k1", "k2", "k3"] + allind].copy()
    log("\nsphere indices (non-occupied):")
    for (sph, y), spec in SPHERES.items():
        avail = {c: v for c, v in spec.items() if df.loc[free, c].notna().any()}
        col = f"{sph}_{y}"
        if len(avail) < MIN_IND:
            res[col], res[f"n_{col}"] = np.nan, 0
            log(f"  {col:12s} not computed: {len(avail)} of {len(spec)} indicators available (< {MIN_IND})")
            continue
        R = ranks(df, avail, free)
        res[col] = index(R, MIN_IND).round(4)
        res[f"n_{col}"] = R.notna().sum(axis=1)
        v = res.loc[free, col]
        log(f"  {col:12s} indicators={len(avail)}/{len(spec)}  n={v.notna().sum()}  "
            f"median={v.median():.3f}  p10={v.quantile(.1):.3f}  p90={v.quantile(.9):.3f}")
        cm = R[free].corr(method="spearman").round(2)
        log("    rank correlations within the sphere:\n" + "\n".join("      " + l for l in cm.to_string().splitlines()))
        for c in avail:                                           # leave-one-out
            loo = index(R.drop(columns=c), min(MIN_IND, len(avail) - 1))
            rho = res.loc[free, col].corr(loo[free], method="spearman")
            log(f"    without {c:32s} rho={rho:.3f}")
    for name, spec in SUB.items():
        R = ranks(df, spec, free)
        res[name] = index(R, 2).round(4)
        log(f"  {name:20s} n={res.loc[free, name].notna().sum()}")

    for y in (2021, 2025):
        S = res[[f"econ_{y}", f"rights_{y}", f"cult_{y}"]]
        tot = S.sum(axis=1, min_count=3)
        for s, c in zip(("econ", "rights", "cult"), S.columns):
            res[f"w_{s}_{y}"] = (res[c] / tot).round(4)
        W = res[[f"w_econ_{y}", f"w_rights_{y}", f"w_cult_{y}"]]
        full = W.notna().all(axis=1)
        dom = pd.Series(np.nan, index=res.index, dtype=object)
        if full.any():
            dom[full] = W[full].idxmax(axis=1).str.replace(f"w_|_{y}", "", regex=True)
        res[f"dominant_{y}"] = dom
        log(f"\nbalance {y}: dominant sphere counts " + str(res.loc[free, f"dominant_{y}"].value_counts().to_dict()))
        log(f"  between-sphere rank correlations {y}:\n" + "\n".join(
            "    " + l for l in res.loc[free, S.columns].corr(method="spearman").round(3).to_string().splitlines()))
    both = res.loc[free, ["econ_2021", "econ_2025", "rights_2021", "rights_2025", "cult_2021", "cult_2025"]]
    for s in ("econ", "rights", "cult"):
        ok = both[f"{s}_2021"].notna() & both[f"{s}_2025"].notna()
        if ok.any():
            log(f"  {s}: 2021 vs 2025 rank correlation {both.loc[ok, f'{s}_2021'].corr(both.loc[ok, f'{s}_2025'], method='spearman'):.3f} (n={ok.sum()})")
    fx = res.loc[free, ["budget_econ_2025", "budget_rights_2025"]].dropna()
    if len(fx):
        log(f"  budget sub-indices 2025: rank correlation {fx.corr(method='spearman').iloc[0, 1]:.3f} (n={len(fx)})")

    carp = res[free & res["k1"].isin(CARP)]
    if len(carp):
        cols = [c for c in ("econ_2025", "rights_2025", "cult_2025", "econ_2021", "rights_2021", "cult_2021") if res[c].notna().any()]
        g = carp.groupby("k1")[cols].median().round(3)
        g.index = [CARP[k] for k in g.index]
        nat = res.loc[free, cols].median().round(3).rename("Україна (медіана)")
        log("\nCarpathian oblasts, median index:\n" + pd.concat([g, nat.to_frame().T]).to_string())

    res["occupied"] = df["occupied"]
    res.loc[~free, [c for c in res.columns if c not in ("k1", "k2", "k3", "name", "occupied")]] = np.nan
    res.to_csv(OUT, index=False)
    inp[free].round(6).to_csv(OUT_IN, index=False)
    log(f"\nwrote {OUT.name} ({len(res)} rows) and {OUT_IN.name} ({int(free.sum())} rows)")

    zone = zk(pd.read_csv(TIDY / "frontline_zone_k3.csv", dtype=str))
    touched = sorted(set(zone.loc[zone["zone"] == "1", "k2"]))
    idx_cols = [c for c in res.columns if c.split("_")[0] in ("econ", "rights", "cult", "budget")]
    rows = []
    w = df["pop_ghs_2020"]
    for k2 in touched:
        m = free & (res["k2"] == k2)
        if not m.any():
            continue
        r = {"k1": res.loc[m, "k1"].iloc[0], "k2": k2, "n_hromadas": int(m.sum()),
             "n_zone": int(res.loc[m, "k3"].isin(set(zone.loc[zone["zone"] == "1", "k3"])).sum())}
        r.update({c: round(wmean(res.loc[m, c], w[m]), 4) for c in idx_cols})
        rows.append(r)
    r3 = pd.DataFrame(rows)
    for y in (2021, 2025):
        if len(r3) and all(f"{s}_{y}" in r3 for s in ("econ", "rights", "cult")):
            t = r3[[f"econ_{y}", f"rights_{y}", f"cult_{y}"]].sum(axis=1, min_count=3)
            for s in ("econ", "rights", "cult"):
                r3[f"w_{s}_{y}"] = (r3[f"{s}_{y}"] / t).round(4)
    r3.to_csv(OUT_R3, index=False)
    log(f"wrote {OUT_R3.name}: {len(r3)} raions touched by the zone (population-weighted, whole raion)")

    src = "32_sphere_indices.py; inputs see resilience/docs/threefolding_framework.md section 6"
    lic = "CC BY 4.0 (derived); input licences as in the data dictionary"
    rows = []
    for (sph, y), spec in SPHERES.items():
        rows.append([f"{sph}_{y}", src, lic, "index 0–1", str(y), "hromada",
                     f"mean percentile rank (non-occupied) of {len(spec)} indicators, >= {MIN_IND} required: "
                     + ", ".join(f"{c} ({'+' if d > 0 else '−'})" for c, (d, _) in spec.items())])
    for n, spec in SUB.items():
        rows.append([n, src, lic, "index 0–1", "2025", "hromada",
                     "fiscal capacity split: " + ", ".join(f"{c} ({'+' if d > 0 else '−'})" for c, (d, _) in spec.items())])
    for y in (2021, 2025):
        rows.append([f"w_econ_{y} / w_rights_{y} / w_cult_{y}", src, lic, "share", str(y), "hromada",
                     "sphere index / sum of the three sphere indices (ternary balance)"])
        rows.append([f"dominant_{y}", src, lic, "category", str(y), "hromada", "sphere with the largest weight"])
    rows += [["single_tax_pc_2021 / single_tax_pc_2025", "openbudget.gov.ua INCOMES (codes 1805xxxx) + GHS-POP",
              "UA open data (CMU Res. 835) + EC reuse notice", "UAH/person", "2021, 2025", "hromada",
              "single tax, FUND_TYP T, December YTD, leaf codes / pop_ghs_2020"],
             ["property_tax_pc_2021 / property_tax_pc_2025", "openbudget.gov.ua INCOMES (codes 1801xxxx) + GHS-POP",
              "UA open data (CMU Res. 835) + EC reuse notice", "UAH/person", "2021, 2025", "hromada",
              "property tax incl. land payments, FUND_TYP T, December YTD, leaf codes / pop_ghs_2020"],
             ["transfer_dep_civ_2021 / transfer_dep_civ_2025", "public/budget_long_k3_year.csv",
              "UA open data (CMU Res. 835)", "ratio", "2021, 2025", "hromada",
              "transfers / civilian total revenue (military PIT removed, rule R4)"]]
    dd_new = pd.DataFrame(rows, columns=["indicator", "source", "licence", "unit", "year", "level", "method"])
    ddp = TIDY / "data_dictionary.csv"
    dd = pd.read_csv(ddp, dtype=str) if ddp.exists() else pd.DataFrame(columns=dd_new.columns)
    dd = pd.concat([dd[~dd["indicator"].isin(dd_new["indicator"])], dd_new], ignore_index=True)
    dd.to_csv(ddp, index=False)
    log(f"data dictionary updated: {len(dd)} indicators")


if __name__ == "__main__":
    main()
