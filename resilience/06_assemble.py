#!/usr/bin/env python3
"""
06_assemble.py — merge tidy indicator tables into resilience v1 (one row per k3)

Inputs (optional ones are merged when present):
  tidy/keys_hromada.csv, tidy/budget_indicators_k3.csv, tidy/budget_long_k3_year.csv,
  tidy/population_k3.csv, [tidy/nightlights_indicators_k3.csv], [tidy/dream_k3.csv],
  [tidy/stat_edrpou_k3.csv  -> regional supplement, suffix _reg, not used in the composite]
Outputs:
  tidy/resilience_v1_k3.csv, resilience_v1.gpkg (layer hromada_resilience, UA_LAEA),
  tidy/data_dictionary.csv (updated), logs/06_assemble.log
"""
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pyogrio

BASE = Path(__file__).resolve().parent
QGIS = BASE.parent / "viina" / "qgis"
UNITS = BASE / "units_hromada.gpkg"
TIDY, LOGS = BASE / "tidy", BASE / "logs"
GARRISON_THRESHOLD = 0.25
REG_MIN_DATE = "2025-01-01"
_logf = open(LOGS / "06_assemble.log", "w", encoding="utf-8")


def log(*a):
    m = " ".join(str(x) for x in a)
    print(m, flush=True)
    _logf.write(m + "\n")
    _logf.flush()


def read(name, required=True):
    p = TIDY / name
    if not p.exists():
        if required:
            raise SystemExit(f"missing {p}")
        log(f"(optional) {name} not found — skipped")
        return None
    df = pd.read_csv(p, dtype={"k3": str, "k2": str, "k1": str})
    df["k3"] = df["k3"].str.zfill(7)
    return df


keys = read("keys_hromada.csv")[["k1", "k2", "k3", "name"]]
ctrl = pyogrio.read_dataframe(QGIS / "hromada_control.gpkg", layer="hromada_control",
                              read_geometry=False)[["k3", "occupied", "occ_share"]]
ctrl["k3"] = ctrl["k3"].astype("string").str.zfill(7).astype(str)
out = keys.merge(ctrl, on="k3", how="left")

# ---- budget
bud = read("budget_indicators_k3.csv")
drop = ["k1", "k2", "name", "occupied", "pop", "own_rev_gf_pc_2025", "pdfo_civ_pc_2025",
        "pdfo_mil_share_2025"]
bud = bud.drop(columns=[c for c in drop if c in bud.columns])
out = out.merge(bud, on="k3", how="left")

long = read("budget_long_k3_year.csv")
l21 = long[long["year"] == 2021][["k3", "pdfo", "pdfo_mil"]].drop_duplicates("k3")
l21["pdfo_mil_share_2021"] = l21["pdfo_mil"] / l21["pdfo"].where(l21["pdfo"] > 0)
out = out.merge(l21[["k3", "pdfo_mil_share_2021"]], on="k3", how="left")
out["garrison_flag"] = (out["pdfo_mil_share_2021"] >= GARRISON_THRESHOLD).astype("Int64")
out.loc[out["pdfo_mil_share_2021"].isna(), "garrison_flag"] = pd.NA

# ---- population + per capita
pop = read("population_k3.csv")[["k3", "pop_ghs_2020", "pop_ghs_2025"]]
out = out.merge(pop, on="k3", how="left")
den = out["pop_ghs_2020"].where(out["pop_ghs_2020"] >= 100)
out["own_rev_gf_pc_2025"] = out["own_rev_gf_2025"] / den
out["pdfo_civ_pc_2025"] = out["pdfo_civ_2025"] / den

# ---- nightlights (optional)
ntl = read("nightlights_indicators_k3.csv", required=False)
if ntl is not None:
    keep = [c for c in ntl.columns if c.startswith("ntl_")]
    out = out.merge(ntl[["k3"] + keep], on="k3", how="left")

# ---- DREAM (optional)
dr = read("dream_k3.csv", required=False)
if dr is not None:
    out = out.merge(dr[["k3", "dream_n", "dream_n_active"]], on="k3", how="left")
    den = out["pop_ghs_2020"].where(out["pop_ghs_2020"] >= 100)
    out["dream_per10k"] = out["dream_n"] / den * 1e4
    out["dream_active_share"] = out["dream_n_active"] / out["dream_n"].where(out["dream_n"] > 0)

# ---- ЄДРПОУ regional supplement (optional, not national — suffix _reg)
st = read("stat_edrpou_k3.csv", required=False)
if st is not None:
    den = out["pop_ghs_2020"].where(out["pop_ghs_2020"] >= 100)
    s = out[["k3"]].merge(st, on="k3", how="left")
    for kind in ("le", "fop"):
        if f"{kind}_count" not in s:
            continue
        cur = s[f"{kind}_date"].fillna("") >= REG_MIN_DATE
        out[f"{kind}_per1k_reg"] = (s[f"{kind}_count"] / den * 1e3).where(cur)
        out[f"{kind}_date_reg"] = s[f"{kind}_date"].where(cur)
        if f"{kind}_count_base" in s:
            out[f"{kind}_change_reg"] = (s[f"{kind}_count"] /
                                         s[f"{kind}_count_base"].where(s[f"{kind}_count_base"] > 0)).where(cur)

out.to_csv(TIDY / "resilience_v1_k3.csv", index=False)
log(f"wrote tidy/resilience_v1_k3.csv rows={len(out)} cols={len(out.columns)}")

# ---- geopackage with geometry (UA_LAEA)
src = UNITS if UNITS.exists() else QGIS / "admin_units.gpkg"
g = gpd.read_file(src, layer="hromada")[["k3", "geometry"]]
g["k3"] = g["k3"].astype("string").str.zfill(7).astype(str)
gg = g.merge(out, on="k3", how="left")
gpkg = BASE / "resilience_v1.gpkg"
gg.to_file(gpkg, layer="hromada_resilience", driver="GPKG", engine="pyogrio")
log(f"wrote {gpkg.name}:hromada_resilience (geometry from {src.name}) crs={gg.crs.to_string()[:40]}")

# ---- coverage report
free = out[out["occupied"] == False]  # noqa: E712
skip = {"k1", "k2", "k3", "name", "occupied", "occ_share", "le_date_reg", "fop_date_reg"}
log(f"\ncoverage on {len(free)} non-occupied hromadas:")
for c in [c for c in out.columns if c not in skip]:
    v = pd.to_numeric(free[c], errors="coerce")
    log(f"  {c:26s} n={v.notna().sum():5d}  median={v.median():>14,.3f}  "
        f"p05={v.quantile(.05):>14,.3f}  p95={v.quantile(.95):>14,.3f}")
log(f"\ngarrison_flag (share >= {GARRISON_THRESHOLD}) among non-occupied: "
    f"{int(free['garrison_flag'].fillna(0).sum())}")
cols = ["k3", "name", "own_rev_gf_pc_2025", "pdfo_civ_pc_2025", "transfer_dep_2025", "pop_ghs_2020"]
f2 = free.dropna(subset=["own_rev_gf_pc_2025"])
log("\nhighest own_rev_gf_pc_2025:\n" + f2.nlargest(6, "own_rev_gf_pc_2025")[cols].to_string(index=False))
log("\nlowest own_rev_gf_pc_2025:\n" + f2.nsmallest(6, "own_rev_gf_pc_2025")[cols].to_string(index=False))
num = free.select_dtypes("number").drop(columns=["occ_share"], errors="ignore")
core = [c for c in ["own_rev_gf_pc_2025", "pdfo_civ_pc_2025", "transfer_dep_2025",
                    "pdfo_civ_growth_rel_2125", "capex_share_2325",
                    "ntl_recovery_2124", "ntl_winter_ratio_2125", "dream_per10k",
                    "le_per1k_reg", "fop_per1k_reg"] if c in num]
log("\nSpearman correlations (non-occupied):\n" + num[core].corr(method="spearman").round(2).to_string())
log("\nVerkhovyna 2602003:\n" + out[out["k3"] == "2602003"].T.to_string(header=False))

# ---- dictionary
src_b = "openbudget.gov.ua (MinFin/Treasury) + JRC GHS-POP R2023A"
lic_b = "UA open data (CMU Res. 835) + EC reuse notice — attribute both"
rows = [
    ["own_rev_gf_pc_2025", src_b, lic_b, "UAH/person", "2025", "hromada",
     "own_rev_gf_2025 / pop_ghs_2020 (pre-war baseline; inflated where population left, "
     "deflated in IDP-host hromadas); NaN if pop < 100"],
    ["pdfo_civ_pc_2025", src_b, lic_b, "UAH/person", "2025", "hromada",
     "pdfo_civ_2025 / pop_ghs_2020; PIT booked at employer address (commuter and HQ bias)"],
    ["pdfo_mil_share_2021", "openbudget.gov.ua", "UA open data (CMU Res. 835)", "ratio", "2021",
     "hromada", "PIT code 11010200 (military pay) / all PIT, 2021 (military PIT left local "
     "budgets from late 2023)"],
    ["garrison_flag", "openbudget.gov.ua", "UA open data (CMU Res. 835)", "0/1", "2021", "hromada",
     f"pdfo_mil_share_2021 >= {GARRISON_THRESHOLD}; interpret PIT growth with care where 1"],
    ["dream_per10k", "DREAM public API (public-api.dream.gov.ua) + GHS-POP", "public open data — attribute DREAM",
     "projects / 10k persons", "2023-2026", "hromada",
     "Valid (not cancelled/unsuccessful) projects with a KATOTTG location in the hromada / pop_ghs_2020; "
     "25% of valid projects carry no hromada location; reflects planning capacity, donor attention and damage"],
    ["le_per1k_reg", "State Statistics Service regional offices (ЄДРПОУ)", "official statistics — attribution to office",
     "legal entities / 1k persons", ">= 2025", "hromada (subset of oblasts)",
     "REGIONAL SUPPLEMENT, ~40% national coverage — not in composite; registrations by legal address"],
    ["fop_per1k_reg", "State Statistics Service regional offices (ЄДРПОУ)", "official statistics — attribution to office",
     "sole proprietors / 1k persons", ">= 2025", "hromada (subset of oblasts)",
     "REGIONAL SUPPLEMENT, ~30% national coverage — not in composite"],
    ["le_change_reg", "State Statistics Service regional offices (ЄДРПОУ)", "official statistics — attribution to office",
     "ratio latest / base", "2022-2026", "hromada (subset)", "latest (>= 2025) / first snapshot <= 2022-04-01"],
    ["fop_change_reg", "State Statistics Service regional offices (ЄДРПОУ)", "official statistics — attribution to office",
     "ratio latest / base", "2022-2026", "hromada (subset)", "latest (>= 2025) / first snapshot <= 2022-04-01"],
]
dd_new = pd.DataFrame(rows, columns=["indicator", "source", "licence", "unit", "year", "level", "method"])
ddp = TIDY / "data_dictionary.csv"
dd = pd.read_csv(ddp, dtype=str)
dd = dd[~dd["indicator"].isin(list(dd_new["indicator"]) + ["pdfo_mil_share_2025"])]
dd = pd.concat([dd, dd_new], ignore_index=True)
dd.to_csv(ddp, index=False)
log(f"data dictionary updated: {len(dd)} indicators")
_logf.close()
