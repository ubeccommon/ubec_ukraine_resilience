#!/usr/bin/env python3
"""
38_sphere_tables.py — paper tables S2–S9 and quoted numbers for the three-sphere analysis (paper v0.5, Part II).

  python 38_sphere_tables.py

Reads only tracked, published tables (no local data needed):
  tidy/sphere_indices_k3.csv, tidy/sphere_inputs_k3.csv (32), tidy/sphere_associations.csv,
  tidy/sphere_lisa_summary.csv (36), tidy/why_there_models.csv, tidy/why_there_profiles.csv (37).
Writes:
  publication/figures/tableS2_spheres_oblast.{csv,md}   sphere indices by oblast, medians 2021 and 2025
  publication/figures/tableS3_spheres_exposure.md       spheres and balance against exposure (36 A, 37 Q2)
  publication/figures/tableS4_zone_gap.md               zone gap and exposure by indicator (37 Q1)
  publication/figures/tableS5_functional.md             pre-war spheres and light outcomes (36 B)
  publication/figures/tableS6_rights_outage.md          rights indicators and summer-2024 light (37 Q3)
  publication/figures/tableS7_between.md                the spheres against each other (36 C)
  publication/figures/tableS8_lisa.md                   global Moran's I and cluster counts (36 D)
  publication/figures/tableS9_carpathian_econ.md        Carpathian economic change (37 Q5)
Table S1 (indicators) is written in the paper. Tables are pasted into paper.md between begin/end markers.
  publication/numbers_spheres.yaml                      generated keys for {{…}} in the paper (build.py
                                                        reads it beside numbers.yaml; do not edit by hand)
Coefficients: standardised (SD); p = restricted wild-cluster bootstrap by oblast (24 clusters, 9,999 draws);
intervals by inverting that test. All values are national, oblast or group aggregates (rules R1–R7).
"""
import importlib
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
TIDY = BASE / "tidy"
ROOT = BASE.parent
FIG = ROOT / "publication" / "figures"
NUM = ROOT / "publication" / "numbers_spheres.yaml"
SPH = ("econ", "rights", "cult")
LABEL = {"econ": "Economic", "rights": "Rights", "cult": "Cultural"}
OBL = {"05": "Vinnytsia", "07": "Volyn", "12": "Dnipropetrovsk", "14": "Donetsk", "18": "Zhytomyr",
       "21": "Zakarpattia", "23": "Zaporizhzhia", "26": "Ivano-Frankivsk", "32": "Kyiv", "35": "Kirovohrad",
       "44": "Luhansk", "46": "Lviv", "48": "Mykolaiv", "51": "Odesa", "53": "Poltava", "56": "Rivne",
       "59": "Sumy", "61": "Ternopil", "63": "Kharkiv", "65": "Kherson", "68": "Khmelnytskyi", "71": "Cherkasy",
       "73": "Chernivtsi", "74": "Chernihiv", "80": "Kyiv City"}
CARP = ("21", "26", "46", "73")
MINUS = "−"
KEYS = {}


# ---- formatting -----------------------------------------------------------------------------------------
def sgn(x, d=2):
    if x is None or not np.isfinite(x):
        return "—"
    s = f"{x:+.{d}f}"
    if float(s) == 0:
        s = f"{0:.{d}f}"
    return s.replace("-", MINUS)


def num(x, d=2):
    if x is None or not np.isfinite(x):
        return "—"
    s = f"{x:.{d}f}"
    if float(s) == 0:
        s = f"{0:.{d}f}"
    return s.replace("-", MINUS)


def pv(p):
    if p is None or not np.isfinite(p):
        return "—"
    return "< 0.001" if p < 0.001 else f"{p:.3f}"


def ci(lo, hi):
    if not (np.isfinite(lo) and np.isfinite(hi)):
        return "—"
    return f"{sgn(lo)} to {sgn(hi)}"


def cell(r, with_ci=False):
    """b (p) [interval]"""
    if r is None:
        return "—"
    s = f"{sgn(r['b'])} ({pv(r['p_wcb'])})"
    if with_ci and np.isfinite(r["ci_lo"]):
        s += f" [{ci(r['ci_lo'], r['ci_hi'])}]"
    return s


def put(key, value, comment=""):
    if key in KEYS:
        raise SystemExit(f"duplicate key {key}")
    KEYS[key] = (value, comment)


def put_row(key, r, comment=""):
    if r is None:
        return
    put(f"{key}_b", sgn(r["b"]), comment)
    put(f"{key}_p", pv(r["p_wcb"]))
    if np.isfinite(r["ci_lo"]):
        put(f"{key}_ci", ci(r["ci_lo"], r["ci_hi"]))


def get(df, model, y, x):
    m = df[(df["model"] == model) & (df["y"] == y) & (df["x"] == x)]
    if len(m) != 1:
        print(f"  missing or ambiguous: {model} | {y} | {x} ({len(m)})")
        return None
    return m.iloc[0]


def md(path, title, header, rows, note):
    lines = [f"**{title}**", "", "| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    lines += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    lines += ["", note, ""]
    txt = "\n".join(lines)
    path.write_text(txt, encoding="utf-8")
    print(f"\n{txt}")


def zf(df):
    for c, n in (("k1", 2), ("k2", 4), ("k3", 7)):
        if c in df:
            df[c] = df[c].astype(str).str.split(".").str[0].str.zfill(n)
    return df


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    si = zf(pd.read_csv(TIDY / "sphere_indices_k3.csv", dtype={"k1": str, "k2": str, "k3": str}))
    si = si[~si["occupied"].astype(str).str.lower().isin(["true", "1"])].copy()
    A = pd.read_csv(TIDY / "sphere_associations.csv")
    W = pd.read_csv(TIDY / "why_there_models.csv")
    P = pd.read_csv(TIDY / "why_there_profiles.csv", dtype={"group": str})
    L = pd.read_csv(TIDY / "sphere_lisa_summary.csv", dtype={"k1": str})

    # ---- sphere indices: coverage, stability, leave-one-out, oblast medians --------------------------
    cols = [f"{s}_{y}" for y in (2021, 2025) for s in SPH]
    put("n_spheres", f"{int(si[cols].notna().all(axis=1).sum()):,}", "non-occupied hromadas with all six indices")
    for s in SPH:
        put(f"sph_stab_{s}", num(si[f"{s}_2021"].corr(si[f"{s}_2025"], method="spearman")),
            "rank correlation 2021 vs 2025")
    for a_, b_ in (("econ", "rights"), ("econ", "cult"), ("rights", "cult")):
        for y in (2021, 2025):
            put(f"sph_rho_{a_}_{b_}_{y}", num(si[f"{a_}_{y}"].corr(si[f"{b_}_{y}"], method="spearman")))
    # leave-one-out: recompute ranks as 32 does
    sys.path.insert(0, str(BASE))
    s32 = importlib.import_module("32_sphere_indices")
    inp = zf(pd.read_csv(TIDY / "sphere_inputs_k3.csv", dtype={"k1": str, "k2": str, "k3": str}))
    inp = inp[inp["k3"].isin(si["k3"])].reset_index(drop=True)
    free = pd.Series(True, index=inp.index)
    for s in SPH:
        loo = []
        for y in (2021, 2025):
            spec = s32.SPHERES[(s, y)]
            R = s32.ranks(inp, spec, free)
            full = s32.index(R, s32.MIN_IND)
            for c in spec:
                part = s32.index(R.drop(columns=c), min(s32.MIN_IND, len(spec) - 1))
                loo.append(full.corr(part, method="spearman"))
        put(f"sph_loo_{s}", num(min(loo)), "lowest leave-one-out rank correlation, both years")
    # within-sphere rank correlations between indicators, and like-for-like change vs index change
    COMMON = {"econ": [("pdfo_civ_pc_2021", "pdfo_civ_pc_2025"), ("single_tax_pc_2021", "single_tax_pc_2025"),
                       ("property_tax_pc_2021", "property_tax_pc_2025")],
              "rights": [("transfer_dep_civ_2021", "transfer_dep_civ_2025"), ("capex_share_2021", "capex_share_2325"),
                         ("social_pc_2021", "social_pc_2025")],
              "cult": [("culture_arts_pc_2021", "culture_arts_pc_2025"), ("education_pc_2021", "education_pc_2025"),
                       ("extracurricular_pc_2021", "extracurricular_pc_2025")]}
    spec_all = {}
    for spec in s32.SPHERES.values():
        spec_all.update(spec)
    RA = s32.ranks(inp, spec_all, free)
    RA["k3"] = inp["k3"]
    RA = RA.merge(si[["k3"] + cols], on="k3", how="left")
    for s in SPH:
        cors = []
        for y in (2021, 2025):
            c = RA[list(s32.SPHERES[(s, y)])].corr(method="spearman").values
            cors += list(c[np.triu_indices_from(c, 1)])
        put(f"sph_within_{s}_min", num(min(cors)))
        put(f"sph_within_{s}_max", num(max(cors)))
        ll21 = RA[[a for a, _ in COMMON[s]]].mean(axis=1).where(RA[[a for a, _ in COMMON[s]]].notna().sum(axis=1) >= 2)
        ll25 = RA[[b for _, b in COMMON[s]]].mean(axis=1).where(RA[[b for _, b in COMMON[s]]].notna().sum(axis=1) >= 2)
        put(f"ll_corr_{s}", num((ll25 - ll21).corr(RA[f"{s}_2025"] - RA[f"{s}_2021"], method="spearman")),
            "rank correlation, like-for-like change vs index change")
    put("sph_rho_budget_sub", num(si["budget_econ_2025"].corr(si["budget_rights_2025"], method="spearman")),
        "economic vs rights budget sub-index 2025")
    zone = zf(pd.read_csv(TIDY / "frontline_zone_k3.csv", dtype=str))
    put("n_zone", f"{int(si['k3'].isin(set(zone.loc[zone['zone'] == '1', 'k3'])).sum()):,}",
        "non-occupied hromadas within 30 km of the front line or border")
    # balance: national centre and median imbalance (as 35_sphere_layers.py)
    for y in (2021, 2025):
        Wm = si[[f"w_{s}_{y}" for s in SPH]].to_numpy(float)
        Wm = Wm[np.isfinite(Wm).all(axis=1) & (Wm > 0).all(axis=1)]
        g = np.exp(np.log(Wm).mean(axis=0))
        c = g / g.sum()
        q = Wm / c
        q = q / q.sum(axis=1, keepdims=True)
        lq = np.log(q)
        z1 = np.sqrt(0.5) * (lq[:, 0] - lq[:, 1])
        z2 = np.sqrt(2 / 3) * (0.5 * (lq[:, 0] + lq[:, 1]) - lq[:, 2])
        put(f"bal_centre_{y}", " : ".join(f"{v:.2f}" for v in c), "national centre, economic : rights : cultural")
        put(f"bal_imb_med_{y}", num(np.median(np.hypot(z1, z2))))
    med = si.groupby("k1")[cols].median() * 100
    n = si.groupby("k1")[cols].count().min(axis=1)
    rows, csvrows = [], []
    for k1 in sorted(med.index, key=lambda k: OBL.get(k, k)):
        if k1 not in OBL:
            continue
        r = [OBL[k1], f"{int(n[k1])}"] + [num(med.loc[k1, c], 0) for c in cols]
        rows.append(r)
        csvrows.append([k1] + r)
        for c in cols:
            put(f"sph_med_{c}_{k1}", num(med.loc[k1, c], 0))
    carp = si[si["k1"].isin(CARP)]
    for lab, g in (("Carpathian (4 oblasts)", carp), ("Ukraine (non-occupied)", si)):
        r = [lab, f"{int(g[cols].count().min()):,}"] + [num(g[c].median() * 100, 0) for c in cols]
        rows.append(r)
        csvrows.append([lab] + r)
        tag = "carp" if lab.startswith("Carp") else "nat"
        for c in cols:
            put(f"sph_med_{c}_{tag}", num(g[c].median() * 100, 0))
    hdr = ["Oblast", "Hromadas", "Economic 2021", "Rights 2021", "Cultural 2021",
           "Economic 2025", "Rights 2025", "Cultural 2025"]
    pd.DataFrame(csvrows, columns=["k1"] + hdr).to_csv(FIG / "tableS2_spheres_oblast.csv", index=False)
    md(FIG / "tableS2_spheres_oblast.md", "Table S2. Sphere indices by oblast, medians (0–100)", hdr, rows,
       "Mean percentile rank of the sphere's indicators among non-occupied hromadas (0–100; national median "
       "about 50). Zone hromadas are included in the oblast medians. Indicators: Table S1.")

    # ---- Table 14: exposure ----------------------------------------------------------------------------
    rows = []
    for s in SPH:
        r1 = get(A, "A1 2021, FE", f"{s}_2021", "exp")
        r3 = get(A, "A3 2025 given 2021, FE", f"{s}_2025", "exp")
        rz = get(A, "A3 without zone hromadas", f"{s}_2025", "exp")
        ra = get(A, "A3 alert hours", f"{s}_2025", "exp_alert")
        rows.append([f"{LABEL[s]} sphere", cell(r1), cell(r3, True), cell(rz), cell(ra)])
        for k, r in (("a1", r1), ("a3", r3), ("a3nz", rz), ("a3alert", ra),
                     ("a3nf", get(A, "A3 without frontline oblasts", f"{s}_2025", "exp")),
                     ("a1nofe", get(A, "A1 2021, no FE", f"{s}_2021", "exp")),
                     ("a2", get(A, "A2 2025, FE", f"{s}_2025", "exp"))):
            put_row(f"{k}_{s}", r)
    BAL = {"imbalance": "Imbalance (distance from the national centre)",
           "lean_cult": "Lean to cultural", "lean_econ_rights": "Lean to economic (vs rights)"}
    for bv, lab in BAL.items():
        r3 = get(A, "A3 2025 given 2021, FE", f"{bv}_2025", "exp")
        rz = get(W, "exposure without zone", f"{bv}_2025", "exp")
        ra = get(W, "alert hours without zone", f"{bv}_2025", "exp_alert")
        rows.append([lab, "—", cell(r3), cell(rz), f"{cell(ra)} (without zone)"])
        put_row(f"a3_{bv}", r3)
        put_row(f"q2nz_{bv}", rz)
        put_row(f"q2zone_{bv}", get(W, "zone gap", f"{bv}_2025", "zone"))
        put_row(f"q2in_{bv}", get(W, "exposure inside the zone", f"{bv}_2025", "exp"))
        put_row(f"q2nf_{bv}", get(W, "exposure without frontline oblasts", f"{bv}_2025", "exp"))
    md(FIG / "tableS3_spheres_exposure.md", "Table S3. The spheres and war exposure",
       ["Outcome", "2021 level (pre-war)", "2025 given 2021 [95 % interval]", "2025 given 2021, without zone",
        "2025 given 2021, alert hours"], rows,
       "Standardised coefficient of exposure (log strikes since 24 Feb 2022; last column: alert hours, 12 months), "
       "with p from a restricted wild-cluster bootstrap by oblast (24 clusters, 9,999 draws) in brackets and the "
       "95 % interval from inverting that test. All models with oblast fixed effects and log population 2020; "
       "\"given 2021\" adds the 2021 value of the same outcome. Zone: the " + KEYS["n_zone"][0] + " hromadas within "
       "30 km of the front line or the Russian or Belarusian border. The 2021 row describes where strikes later fell; strikes "
       "cannot affect the 2021 values.")

    # ---- Table 15: zone gap by indicator ---------------------------------------------------------------
    IND = {"econ": ["pdfo_civ_pc", "single_tax_pc", "property_tax_pc"],
           "rights": ["transfer_dep_civ", "capex_share", "social_pc"],
           "cult": ["culture_arts_pc", "education_pc", "extracurricular_pc"]}
    INDLAB = {"pdfo_civ_pc": "Civilian income tax per resident", "single_tax_pc": "Single tax per resident",
              "property_tax_pc": "Property and land payments per resident",
              "transfer_dep_civ": "Transfer dependency (−)", "capex_share": "Capital-expenditure share",
              "social_pc": "Social protection spending per resident",
              "culture_arts_pc": "Culture and arts spending per resident",
              "education_pc": "Education spending per resident",
              "extracurricular_pc": "Extracurricular education spending per resident"}
    LL = {"econ": "like-for-like economic", "rights": "like-for-like rights", "cult": "like-for-like cultural"}
    def pval(table, group, var):
        m = P[(P["table"] == table) & (P["group"] == group) & (P["variable"] == var)]
        return float(m["value"].iloc[0]) if len(m) == 1 else np.nan

    rows = []
    for s in SPH:
        items = [(LL[s], f"{LABEL[s]} sphere, like-for-like", f"d_ll_{s}")] + \
                [(i, INDLAB[i], f"dr_{i}") for i in IND[s]]
        for nm, lab, dv in items:
            rz = W[(W["model"] == f"zone gap: {nm}") & (W["x"] == "zone")]
            rz = rz.iloc[0] if len(rz) == 1 else None
            re_ = W[(W["model"] == f"exposure without zone: {nm}") & (W["x"] == "exp")]
            re_ = re_.iloc[0] if len(re_) == 1 else None
            dz = pval("Q1 ranks by zone", "zone", dv)
            dr = pval("Q1 ranks by zone", "same oblasts, outside zone", dv)
            bold = "**" if nm.startswith("like") else ""
            rows.append([f"{bold}{lab}{bold}", sgn(dz), sgn(dr), cell(rz, nm.startswith("like")), cell(re_)])
            slug = nm.replace("like-for-like ", "ll_").replace("economic", "econ").replace("cultural", "cult")
            put_row(f"q1zone_{slug}", rz)
            put_row(f"q1expnz_{slug}", re_)
            re2 = W[(W["model"] == f"exposure: {nm}") & (W["x"] == "exp")]
            put_row(f"q1exp_{slug}", re2.iloc[0] if len(re2) == 1 else None)
            put(f"q1d_zone_{slug}", sgn(dz, 3))
            put(f"q1d_rest_{slug}", sgn(dr, 3))
    for c in ("pdfo_civ_growth_rel_2125", "dream_per10k", "schools_per10k_2026"):
        r = W[(W["model"] == f"zone gap 2025 level: {c}") & (W["x"] == "zone")]
        r = r.iloc[0] if len(r) == 1 else None
        lab = {"pdfo_civ_growth_rel_2125": "Civilian income-tax growth 2021–25 (2025 only)",
               "dream_per10k": "DREAM projects per 10,000 (2025 only)",
               "schools_per10k_2026": "Schools per 10,000 (2025 only)"}[c]
        rows.append([lab, "—", "—", f"{cell(r)} (2025 level)", "—"])
        put_row(f"q1zone25_{c}", r)
        put(f"q1r25_zone_{c}", num(pval("Q1 ranks by zone", "zone", f"r_{c}")))
        put(f"q1r25_rest_{c}", num(pval("Q1 ranks by zone", "other oblasts", f"r_{c}")))
    md(FIG / "tableS4_zone_gap.md", "Table S4. The zone: change 2021–2025 by indicator",
       ["Indicator", "Median rank change, zone", "Median rank change, rest of the same oblasts",
        "Zone gap, 2025 given 2021 (p) [95 % interval]", "Exposure outside the zone (p)"], rows,
       "Rank change: percentile rank 2025 minus 2021 (0–1 scale) among non-occupied hromadas. Zone gap: "
       "difference between zone hromadas and other hromadas of the same oblast in the 2025 rank, given the 2021 "
       "rank and log population, in standard deviations. Exposure outside the zone: coefficient of log strikes "
       "in the same model without zone hromadas. Like-for-like: mean rank of the indicators measured in both "
       "years. Per-resident values use the 2020 population.")

    # ---- Table 16: functional resilience -------------------------------------------------------------
    OUT = {"recovery_index": "Recovery index (2024 / 2021)", "y_s24": "Summer-2024 light vs H2 2023",
           "y_recent": "Recent light level"}
    SHORT = {"recovery_index": "rec", "y_s24": "s24", "y_recent": "recent"}
    rows = []
    for o, lab in OUT.items():
        rr = [get(A, "B1 three spheres, FE", o, f"{s}_2021") for s in SPH]
        rows.append([lab] + [cell(r, True) for r in rr])
        for s, r in zip(SPH, rr):
            put_row(f"b1_{SHORT[o]}_{s}", r)
            put_row(f"b1r_{SHORT[o]}_{s}", get(A, "B1r reliable light data", o, f"{s}_2021"))
            put_row(f"b2int_{SHORT[o]}_{s}",
                    get(A, f"B2 {LABEL[s].lower()} x exposure, FE", o, f"{s}_2021 x exp"))
    md(FIG / "tableS5_functional.md", "Table S5. Pre-war spheres (2021) and functional resilience",
       ["Outcome", "Economic 2021", "Rights 2021", "Cultural 2021"], rows,
       "One model per outcome with all three 2021 sphere indices, log strikes, log population 2020, log lit "
       "pixels, log 2021 radiance and oblast fixed effects. Standardised coefficients, wild-cluster p in "
       "brackets, 95 % interval. Outcomes as in Part I (sections 5.2, 8.4); higher = more light kept.")
    RI = {"r_transfer_dep_civ_2021": "Transfer dependency (−)", "r_capex_share_2021": "Capital-expenditure share",
          "r_social_pc_2021": "Social spending per resident", "r_cand_per_seat_rel_2020": "Candidates per seat 2020"}
    rows = []
    for c, lab in RI.items():
        rj = get(W, "joint, summer 2024", "y_s24", c)
        rr = get(W, "joint, summer 2024, reliable light", "y_s24", c)
        rz = get(W, "joint, summer 2024, without zone", "y_s24", c)
        rows.append([lab, cell(rj, True), cell(rr), cell(rz)])
        slug = c.replace("r_", "", 1).replace("_2021", "").replace("_2020", "")
        put_row(f"q3_{slug}", rj)
        put_row(f"q3r_{slug}", rr)
        put_row(f"q3nz_{slug}", rz)
        put_row(f"q3recent_{slug}", get(W, "joint, recent level", "y_recent", c))
    md(FIG / "tableS6_rights_outage.md", "Table S6. Which rights indicators go with the summer-2024 light loss",
       ["Rights indicator, 2021 rank", "All (p) [95 % interval]", "Reliable light data", "Without zone"], rows,
       "Outcome: log summer-2024 light relative to July–December 2023 (higher = smaller loss). The four rights "
       "indicators enter together, with economic and cultural 2021, log strikes, the light controls and oblast "
       "fixed effects. Reliable light: at least 30 lit pixels and pre-war noise at most 0.35.")
    # Q4
    for c in ("r_culture_arts_pc_2021", "r_education_pc_2021", "r_extracurricular_pc_2021"):
        slug = c.replace("r_", "", 1).replace("_2021", "")
        put_row(f"q4_{slug}", get(W, "joint cultural indicators, recent level", "y_recent", c))
        put_row(f"q4r_{slug}", get(W, "joint cultural indicators, reliable light", "y_recent", c))
    put_row("q4_school", get(W, "cultural 2021 + school network", "y_recent", "cult_2021"))
    put_row("q4_school_same", get(W, "cultural 2021, same sample as school network", "y_recent", "cult_2021"))
    put_row("q4_pop", get(W, "cultural 2021 + population change (GHS, modelled)", "y_recent", "cult_2021"))
    for t in ("city", "settlement", "village"):
        put_row(f"q4_{t}", get(W, f"cultural 2021, {t} hromadas", "y_recent", "cult_2021"))
    for q in range(1, 6):
        g = f"cultural 2021 Q{q}"
        put(f"q4_pop_q{q}", f"{pval('Q4 profile by cultural-2021 quintile', g, 'pop_ghs_2020'):,.0f}")
        put(f"q4_econ_q{q}", num(pval("Q4 profile by cultural-2021 quintile", g, "econ_2021")))

    # ---- Table 17: between spheres ----------------------------------------------------------------------
    rows = []
    PAIRS = [("econ", "rights"), ("econ", "cult"), ("rights", "cult")]
    for a_, b_ in PAIRS:
        r = [f"{LABEL[a_]}–{LABEL[b_].lower()}"]
        for yr, ya, yb in ((2021, f"{a_}_2021", f"{b_}_2021"), (2025, f"{a_}_2025", f"{b_}_2025"),
                           ("change", f"d_{a_}", f"d_{b_}")):
            row = get(A, f"C {yr}, FE", ya, yb)
            m = re.search(r"rho=([-0-9.]+); rho_within=([-0-9.]+)", str(row["note"])) if row is not None else None
            rho, rhow = (float(m.group(1)), float(m.group(2))) if m else (np.nan, np.nan)
            r.append(f"{num(rho)} \\| {num(rhow)}")
            r.append(cell(row, True))
            key = f"c_{a_}_{b_}_{yr}"
            put(f"{key}_rho", num(rho))
            put(f"{key}_rhow", num(rhow))
            put_row(key, row)
        rows.append(r)
    cm = A[A["model"].str.startswith("C ")]["moran_I_resid"]
    put("c_moran_min", num(cm.min()))
    put("c_moran_max", num(cm.max()))
    md(FIG / "tableS7_between.md", "Table S7. The spheres against each other",
       ["Pair", "2021: ρ \\| within", "2021: b (p) [95 %]", "2025: ρ \\| within", "2025: b (p) [95 %]",
        "Change: ρ \\| within", "Change: b (p) [95 %]"], rows,
       "ρ: Spearman rank correlation, plain and within oblasts (ranks demeaned by oblast). b: standardised "
       "coefficient of the second sphere in a model of the first with log population and oblast fixed effects, "
       "wild-cluster p and 95 % interval. Change: 2025 minus 2021 index (change of relative position).")

    # ---- Table 18: LISA ---------------------------------------------------------------------------------
    VARS = [("econ_2021", "Economic 2021"), ("econ_2025", "Economic 2025"), ("d_econ", "Economic change"),
            ("rights_2021", "Rights 2021"), ("rights_2025", "Rights 2025"), ("d_rights", "Rights change"),
            ("cult_2021", "Cultural 2021"), ("cult_2025", "Cultural 2025"), ("d_cult", "Cultural change"),
            ("imbalance_2021", "Imbalance 2021"), ("imbalance_2025", "Imbalance 2025"),
            ("lean_cult_2021", "Lean to cultural 2021"), ("lean_cult_2025", "Lean to cultural 2025"),
            ("lean_econ_rights_2021", "Lean to economic vs rights 2021"),
            ("lean_econ_rights_2025", "Lean to economic vs rights 2025")]
    rows = []
    for v, lab in VARS:
        r = [lab]
        for scope in ("national", "carpathian"):
            g = L[(L["scope"] == scope) & (L["variable"] == v) & (L["k1"] == "all")]
            if len(g) != 1:
                r += ["—", "—"]
                continue
            g = g.iloc[0]
            r += [f"{num(g['moran_I'])}", f"{int(g['HH'])} / {int(g['LL'])} ({int(g['HH_fdr'])} / {int(g['LL_fdr'])})"]
            sc = "nat" if scope == "national" else "carp"
            put(f"lisa_{sc}_{v}_I", num(g["moran_I"]))
            for c in ("HH", "LL", "HL", "LH", "HH_fdr", "LL_fdr"):
                put(f"lisa_{sc}_{v}_{c.replace('_', '')}", f"{int(g[c])}")
        rows.append(r)
        nat = L[(L["scope"] == "national") & (L["variable"] == v)]
        for k1 in CARP:
            g = nat[nat["k1"] == k1]
            if len(g) == 1:
                put(f"lisa_nat_{v}_{k1}_HH", f"{int(g['HH'].iloc[0])}")
                put(f"lisa_nat_{v}_{k1}_LL", f"{int(g['LL'].iloc[0])}")
    md(FIG / "tableS8_lisa.md", "Table S8. Spatial clustering of the spheres and the balance",
       ["Variable", "National: Moran's I", "National: HH / LL clusters (after FDR)",
        "Carpathian: Moran's I", "Carpathian: HH / LL clusters (after FDR)"], rows,
       "Global Moran's I and local Moran (LISA) with six nearest neighbours (UA_LAEA representative points, "
       "row-standardised), 9,999 permutations; HH = high values among high neighbours, LL = low among low, at "
       "p < 0.05 and, in brackets, after a false-discovery-rate cut (Benjamini–Hochberg, 0.05). Carpathian: "
       "weights built within the four oblasts only. Counts of hromadas; no hromada is named or mapped (rule R3).")

    # ---- Table 19: Carpathian economic change --------------------------------------------------------
    T5 = "Q5 economic change, Carpathian oblasts"
    groups = ["Zakarpattia", "Ivano-Frankivsk", "Lviv", "Chernivtsi", "Carpathian", "rest, outside zone"]
    VAR5 = [("econ_2021", "Economic index 2021"), ("econ_2025", "Economic index 2025"),
            ("d_econ", "Change, index"), ("d_ll_econ", "Change, like-for-like"),
            ("dr_pdfo_civ_pc", "… civilian income tax"), ("dr_single_tax_pc", "… single tax"),
            ("dr_property_tax_pc", "… property and land"),
            ("r_pdfo_civ_growth_rel_2125", "Income-tax growth, rank 2025"),
            ("pdfo_civ_growth_rel_2125", "Income-tax growth 2021–25 / national median")]
    rows = []
    for v, lab in VAR5:
        r = [lab]
        for g in groups:
            x = pval(T5, g, v)
            r.append(sgn(x) if v.startswith("d") else num(x))
            slug = {"Zakarpattia": "zk", "Ivano-Frankivsk": "if", "Lviv": "lv", "Chernivtsi": "cv",
                    "Carpathian": "carp", "rest, outside zone": "restnz"}[g]
            put(f"q5_{v}_{slug}", sgn(x) if v.startswith("d") else num(x))
        rows.append(r)
    md(FIG / "tableS9_carpathian_econ.md", "Table S9. The Carpathian economic change, medians",
       ["Measure", "Zakarpattia", "Ivano-Frankivsk", "Lviv", "Chernivtsi", "Carpathian", "Rest, outside zone"],
       rows,
       "Index values 0–1 (percentile-rank means); changes 2025 minus 2021. Like-for-like: the three tax bases "
       "measured in both years; the 2025 index adds civilian income-tax growth. Income-tax growth: civilian PIT "
       "2025 / 2021 relative to the national median (1 = national median).")
    for key, model, y, x in (
            ("q5gap_ll", "Carpathian gap, like-for-like economic change", "d_ll_econ", "carp"),
            ("q5gap_idx", "Carpathian gap, economic index change", "d_econ", "carp"),
            ("q5gap_pop", "Carpathian gap + population change (GHS, modelled)", "d_ll_econ", "carp"),
            ("q5gap_nz", "Carpathian gap without zone", "d_ll_econ", "carp"),
            ("q5lvl_ll", "Carpathian gap given 2021 level, like-for-like", "ll_econ_2025", "carp"),
            ("q5lvl_idx", "Carpathian gap given 2021 level, economic index", "econ_2025", "carp"),
            ("q5lvl_nolviv", "Carpathian gap given 2021 level, like-for-like, without Lviv", "ll_econ_2025", "carp"),
            ("q5lvl_nz", "Carpathian gap given 2021 level, like-for-like, without zone", "ll_econ_2025", "carp"),
            ("q5gap_pit", "Carpathian gap: pdfo_civ_pc", "dr_pdfo_civ_pc", "carp"),
            ("q5gap_single", "Carpathian gap: single_tax_pc", "dr_single_tax_pc", "carp"),
            ("q5gap_prop", "Carpathian gap: property_tax_pc", "dr_property_tax_pc", "carp"),
            ("q5gap_growth", "Carpathian gap: PIT growth rank 2025", "r_pdfo_civ_growth_rel_2125", "carp"),
            ("q5reg_fop", "registrations within oblasts (oblasts with data)", "d_ll_econ", "fop_growth"),
            ("q5reg_single", "registrations vs single-tax rank change (oblasts with data)", "dr_single_tax_pc",
             "fop_growth")):
        put_row(key, get(W, model, y, x))
    TL = "Q5 profile of LISA clusters: d_econ_national"
    for g, slug in (("HH", "hh"), ("LL", "ll")):
        put(f"q5lisa_{slug}_n", f"{int(P[(P['table'] == TL) & (P['group'] == g)]['n'].iloc[0])}")
        put(f"q5lisa_{slug}_carp", f"{pval(TL, g, 'is_carp') * 100:.0f} %")
        put(f"q5lisa_{slug}_zone", f"{pval(TL, g, 'in_zone') * 100:.0f} %")
        put(f"q5lisa_{slug}_econ21", num(pval(TL, g, "econ_2021")))
    # Q1 / Q2 profile values used in the text
    for g, slug in (("zone", "zone"), ("same oblasts, outside zone", "same"), ("other oblasts", "other")):
        for v in ("imbalance_2021", "imbalance_2025"):
            put(f"q2_{v}_{slug}", num(pval("Q2 balance by zone", g, v)))
        for s in SPH:
            for v in (f"{s}_2021", f"{s}_2025", f"d_{s}", f"ll_{s}_2025", f"d_ll_{s}"):
                x = pval("Q1 ranks by zone", g, v)
                put(f"q1m_{v}_{slug}", sgn(x) if v.startswith("d") else num(x))
        put(f"q1m_capex_{slug}", num(pval("Q1 ranks by zone", g, "r_capex_share_2325")))

    # ---- numbers file ----------------------------------------------------------------------------------
    lines = ["# GENERATED by resilience/38_sphere_tables.py from tracked tidy tables — do not edit by hand.",
             "# Three-sphere analysis (paper v0.5, Part II). Read by publication/build/build.py beside numbers.yaml.",
             "# Coefficients standardised; _p = wild-cluster bootstrap p by oblast; _ci = 95 % interval.", ""]
    for k, (v, c) in KEYS.items():
        lines.append(f'{k}: "{v}"' + (f"  # {c}" if c else ""))
    NUM.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwrote {NUM.relative_to(ROOT)} ({len(KEYS)} keys) and tables 13–19 in {FIG.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
