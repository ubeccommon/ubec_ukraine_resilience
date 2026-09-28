#!/usr/bin/env python3
"""
37_why_there.py — step 8: "why there?" Profiles and models behind the five questions left by step 7
(docs/threefolding_framework.md, section 9).

  python 37_why_there.py            full run (about 10 minutes)
  python 37_why_there.py --no-ci    skip the wild-cluster confidence intervals
  python 37_why_there.py --B 1999   fewer bootstrap draws (test runs only)

Shared data assembly and models: sphere_common.py (as 36). Indicator ranks: the transform, direction, p2/p98
winsorising and percentile rank of 32_sphere_indices.py (SPHERES, ranks), among the non-occupied hromadas here.
Like-for-like indices: mean rank of the indicators measured in both years (>= 2 of 3), because the 2025 indices
add indicators the 2021 ones lack (economic: PIT growth; rights: DREAM instead of candidates per seat; cultural:
schools per 10,000):
  economic  civilian PIT, single tax, property tax per resident
  rights    transfer dependency (−), capital-expenditure share (2021 | 2023–25), social spending per resident
  cultural  culture and arts, education, extracurricular spending per resident
  ll_<s>_2021, ll_<s>_2025, d_ll_<s> = change. r_<indicator> = rank, dr_<indicator> = change of rank.
Further inputs (tidy/): sphere_inputs_k3.csv (32), schools_k3.csv (34), stat_edrpou_k3.csv (09: sole proprietors
and legal entities, base 2022-01), population_k3.csv (GHS-POP 2020 and 2025 — the 2025 epoch is modelled, a weak
signal of population change), sphere_lisa_k3.csv (36, local, optional).
Hromada type from the council name: міська = city, селищна = settlement, сільська = village.

Q1 The zone as carrier of the economic and cultural fall. Profiles (median rank 2021, 2025, change) for zone
   hromadas, the rest of the same oblasts, and the other oblasts. Models per indicator and like-for-like index:
   zone gap (rank 2025 ~ zone + rank 2021 + log population + oblast FE; b = gap in SD of the 2025 rank), and
   exposure with and without the zone (as 36 A3). 2025-only indicators: zone gap on the 2025 level.
Q2 The balance shift without the zone: 36 A3 for imbalance, lean_cult, lean_econ_rights — without zone
   hromadas, without frontline oblasts, alert hours without the zone, the zone gap, and exposure inside the zone.
Q3 Which rights indicators carry the summer-2024 link: y_s24 ~ the four rights ranks 2021 (joint and one at a
   time) + economic and cultural 2021 + exposure + controls (log population, lit pixels, 2021 radiance) + FE;
   reliable light data and without the zone as checks; the same joint model for the recent light level.
Q4 The negative cultural–light link: y_recent ~ the three cultural ranks 2021 (joint) + economic and rights 2021 +
   exposure + controls + FE; cultural 2021 by hromada type; with school network (log class size, rural school share;
   log pupils per 1,000 in a separate row, about 60 % coverage) and with population change added. Profile by cultural-2021 quintile.
Q5 The Carpathian economic rise: profiles of rank changes per economic indicator, registrations and population
   change by Carpathian oblast; Carpathian gap in the like-for-like economic change, per indicator, and with modelled
   population change (no FE — the gap is an oblast contrast; WCB by oblast); the same gap given the 2021 level
   (the Carpathian oblasts started low: regression to the mean), also without Lviv and without the zone. Registration growth (09) exists only
   for 5 oblasts, none Carpathian: used only to check that single-tax revenue tracks registrations; profile of the national LISA clusters of economic change (36). IOM DTM figures, if present
   locally, are printed to the log only (DTM terms: no redistribution or derivative works).

Outputs
  tidy/why_there_models.csv    one row per model and focus coefficient (as sphere_associations.csv + question)
  tidy/why_there_profiles.csv  group medians and shares (question, table, group, n, variable, stat, value);
                               groups with n < 5 suppressed; no night-light values (rule R2: light medians go to
                               the log only)
  logs/37_why_there.log
Caveat: descriptive and associational; the profiles show where things differ, not why they differ.
"""
import argparse
import importlib
import sys
import time
import warnings

import numpy as np
import pandas as pd

from sphere_common import (BASE, CARP, FRONTLINE, LABEL, TIDY, Models, load_base, log, open_log, rd,
                           reliable_light)

warnings.simplefilter("ignore", pd.errors.PerformanceWarning)
OUT_M = TIDY / "why_there_models.csv"
OUT_P = TIDY / "why_there_profiles.csv"
MIN_N = 5
OBL = {"21": "Zakarpattia", "26": "Ivano-Frankivsk", "46": "Lviv", "73": "Chernivtsi"}
COMMON = {
    "econ": [("pdfo_civ_pc", "pdfo_civ_pc_2021", "pdfo_civ_pc_2025"),
             ("single_tax_pc", "single_tax_pc_2021", "single_tax_pc_2025"),
             ("property_tax_pc", "property_tax_pc_2021", "property_tax_pc_2025")],
    "rights": [("transfer_dep_civ", "transfer_dep_civ_2021", "transfer_dep_civ_2025"),
               ("capex_share", "capex_share_2021", "capex_share_2325"),
               ("social_pc", "social_pc_2021", "social_pc_2025")],
    "cult": [("culture_arts_pc", "culture_arts_pc_2021", "culture_arts_pc_2025"),
             ("education_pc", "education_pc_2021", "education_pc_2025"),
             ("extracurricular_pc", "extracurricular_pc_2021", "extracurricular_pc_2025")],
}
ONLY25 = ["pdfo_civ_growth_rel_2125", "dream_per10k", "schools_per10k_2026"]
RIGHTS21 = ["r_transfer_dep_civ_2021", "r_capex_share_2021", "r_social_pc_2021", "r_cand_per_seat_rel_2020"]
CULT21 = ["r_culture_arts_pc_2021", "r_education_pc_2021", "r_extracurricular_pc_2021"]
PROFILES = []


def htype(name):
    n = str(name).lower()
    if "міськ" in n:
        return "city"
    if "селищ" in n:
        return "settlement"
    if "сільськ" in n:
        return "village"
    return "other"


def profile(question, table, groups, spec):
    """groups: {label: boolean mask}; spec: [(variable, stat)] with stat 'median' or 'share'."""
    rows = []
    for g, m in groups.items():
        sub = PD[m]
        n = len(sub)
        for v, stat in spec:
            x = pd.to_numeric(sub[v], errors="coerce") if stat == "median" else sub[v]
            if stat == "median":
                val, nv = x.median(), int(x.notna().sum())
            else:
                val, nv = float(x.astype(float).mean()), n
            if nv < MIN_N:
                val = np.nan
            rows.append({"question": question, "table": table, "group": g, "n": n, "variable": v,
                         "stat": stat, "value": val, "n_valid": nv})
    df = pd.DataFrame(rows)
    PROFILES.append(df)
    wide = df.pivot_table(index="variable", columns="group", values="value", aggfunc="first", sort=False)
    wide = wide.reindex([v for v, _ in spec])[list(groups)]
    ns = "  ".join(f"{g}: n={int(m.sum())}" for g, m in groups.items())
    log(f"\n[{table}]  {ns}\n" + wide.round(3).to_string())
    return df


def main():
    global PD
    ap = argparse.ArgumentParser(description="step 8: why there?")
    ap.add_argument("--no-ci", action="store_true", help="skip wild-cluster confidence intervals")
    ap.add_argument("--B", type=int, default=9999, help="bootstrap draws (default 9,999)")
    a = ap.parse_args()
    open_log("37_why_there")
    t0 = time.time()
    log(f"37_why_there.py  {time.strftime('%Y-%m-%d %H:%M')}  B={a.B}  ci={'no' if a.no_ci else 'yes'}")

    d = load_base()
    sys.path.insert(0, str(BASE))
    s32 = importlib.import_module("32_sphere_indices")

    # ---- further inputs
    inp = rd("sphere_inputs_k3.csv")
    d = d.merge(inp.drop(columns=[c for c in ("k1", "k2") if c in inp]), on="k3", how="left")
    sc = rd("schools_k3.csv")
    sc["rural_school_share"] = pd.to_numeric(sc["schools_rural_2026"], errors="coerce") / \
        pd.to_numeric(sc["schools_2026"], errors="coerce").where(lambda v: v > 0)
    d = d.merge(sc[["k3", "class_size_2021", "pupils_per1000_2021", "rural_school_share"]], on="k3", how="left")
    ed = rd("stat_edrpou_k3.csv")
    for k in ("fop", "le"):
        num = pd.to_numeric(ed[f"{k}_count"], errors="coerce")
        den = pd.to_numeric(ed[f"{k}_count_base"], errors="coerce")
        ed[f"{k}_growth"] = np.log(num.where(num > 0) / den.where(den > 0))
    d = d.merge(ed[["k3", "fop_growth", "le_growth"]], on="k3", how="left")
    pop = rd("population_k3.csv")
    pop["pop_change"] = np.log(pd.to_numeric(pop["pop_ghs_2025"], errors="coerce") /
                               pd.to_numeric(pop["pop_ghs_2020"], errors="coerce").where(lambda v: v > 0))
    d = d.merge(pop[["k3", "pop_change"]], on="k3", how="left")
    d["htype"] = d["name"].map(htype)
    for t in ("city", "settlement", "village"):
        d[f"is_{t}"] = (d["htype"] == t).astype(float)
    d["log_class_size"] = np.log(pd.to_numeric(d["class_size_2021"], errors="coerce").where(lambda v: v > 0))
    d["log_pupils_pc"] = np.log(pd.to_numeric(d["pupils_per1000_2021"], errors="coerce").where(lambda v: v > 0))
    log(f"hromada types: {d['htype'].value_counts().to_dict()}")
    log(f"coverage: registrations {int(d['fop_growth'].notna().sum())}, population change "
        f"{int(d['pop_change'].notna().sum())}, class size {int(d['class_size_2021'].notna().sum())}")

    # ---- indicator ranks (as 32) and like-for-like indices
    free = pd.Series(True, index=d.index)
    spec_all = {}
    for (s, yr), spec in s32.SPHERES.items():
        spec_all.update(spec)
    R = s32.ranks(d, spec_all, free)
    d = pd.concat([d, R.add_prefix("r_")], axis=1)
    new = {}
    for s, items in COMMON.items():
        for nm, c21, c25 in items:
            new[f"dr_{nm}"] = d[f"r_{c25}"] - d[f"r_{c21}"]
        for yr, pos in ((2021, 1), (2025, 2)):
            M3 = d[[f"r_{it[pos]}" for it in items]]
            new[f"ll_{s}_{yr}"] = M3.mean(axis=1).where(M3.notna().sum(axis=1) >= 2)
        new[f"d_ll_{s}"] = new[f"ll_{s}_2025"] - new[f"ll_{s}_2021"]
        rho = new[f"d_ll_{s}"].corr(d[f"d_{s}"], method="spearman")
        log(f"like-for-like {LABEL[s]}: rank correlation of the change with the index change = {rho:.2f}")
    new["carp"] = d["k1"].isin(CARP).astype(float)
    new["zone"] = d["in_zone"].astype(float)
    d = pd.concat([d, pd.DataFrame(new)], axis=1).copy()
    zone_obl = set(d.loc[d["in_zone"], "k1"])
    PD = d
    M = Models(d, a.B, not a.no_ci)
    ctrl = ["c_logpop", "c_loglit", "c_rad21"]
    rel = reliable_light(d)

    # ================= Q1 zone ==========================================================================
    log("\n==== Q1 — the zone as carrier of the economic and cultural fall ====")
    g1 = {"zone": d["in_zone"], "same oblasts, outside zone": d["k1"].isin(zone_obl) & ~d["in_zone"],
          "other oblasts": ~d["k1"].isin(zone_obl)}
    spec = [("exp_strikes_log", "median")]
    for s, items in COMMON.items():
        spec += [(f"{s}_2021", "median"), (f"{s}_2025", "median"), (f"d_{s}", "median"),
                 (f"ll_{s}_2021", "median"), (f"ll_{s}_2025", "median"), (f"d_ll_{s}", "median")]
        for nm, c21, c25 in items:
            spec += [(f"r_{c21}", "median"), (f"r_{c25}", "median"), (f"dr_{nm}", "median")]
    spec += [(f"r_{c}", "median") for c in ONLY25] + [("fop_growth", "median"), ("le_growth", "median"),
                                                       ("pop_change", "median"), ("is_city", "share")]
    profile("Q1", "Q1 ranks by zone", g1, spec)

    for s, items in COMMON.items():
        log(f"\n-- {LABEL[s]}")
        pairs = [(f"like-for-like {LABEL[s]}", f"ll_{s}_2021", f"ll_{s}_2025")] + \
                [(nm, f"r_{c21}", f"r_{c25}") for nm, c21, c25 in items]
        for nm, y21, y25 in pairs:
            ci = ("zone",) if nm.startswith("like") else ()
            M.fit("Q1", f"zone gap: {nm}", y25, ["zone"], [y21, "c_logpop"], raw=("zone",), ci=ci)
            M.fit("Q1", f"exposure: {nm}", y25, ["exp"], [y21, "c_logpop"])
            M.fit("Q1", f"exposure without zone: {nm}", y25, ["exp"], [y21, "c_logpop"], data=d[~d["in_zone"]])
    log("\n-- indicators measured in 2025 only (zone gap on the 2025 level)")
    for c in ONLY25:
        M.fit("Q1", f"zone gap 2025 level: {c}", f"r_{c}", ["zone"], ["c_logpop"], raw=("zone",))

    # ================= Q2 balance without the zone =======================================================
    log("\n==== Q2 — the balance shift without the zone ====")
    for bv in ("imbalance", "lean_cult", "lean_econ_rights"):
        y25, y21 = f"{bv}_2025", f"{bv}_2021"
        log(f"\n-- {bv}")
        M.fit("Q2", "exposure, all (as 36 A3)", y25, ["exp"], [y21, "c_logpop"])
        M.fit("Q2", "exposure without zone", y25, ["exp"], [y21, "c_logpop"], data=d[~d["in_zone"]])
        M.fit("Q2", "exposure without frontline oblasts", y25, ["exp"], [y21, "c_logpop"],
              data=d[~d["k1"].isin(FRONTLINE)])
        if "exp_alert" in d:
            M.fit("Q2", "alert hours without zone", y25, ["exp_alert"], [y21, "c_logpop"], data=d[~d["in_zone"]])
        M.fit("Q2", "zone gap", y25, ["zone"], [y21, "c_logpop"], raw=("zone",), ci=("zone",))
        M.fit("Q2", "exposure inside the zone", y25, ["exp"], [y21, "c_logpop"], data=d[d["in_zone"]],
              note=f"{len(zone_obl)} oblast clusters only")
    profile("Q2", "Q2 balance by zone", g1,
            [(f"{bv}_{yr}", "median") for bv in ("imbalance", "lean_cult", "lean_econ_rights") for yr in (2021, 2025)])

    # ================= Q3 rights indicators and summer 2024 ==============================================
    log("\n==== Q3 — which rights indicators carry the summer-2024 link ====")
    base3 = ["econ_2021", "cult_2021", "exp"] + ctrl
    if "y_s24" in d:
        M.fit("Q3", "joint, summer 2024", "y_s24", RIGHTS21, base3, ci=tuple(RIGHTS21))
        M.fit("Q3", "joint, summer 2024, reliable light", "y_s24", RIGHTS21, base3, data=d[rel])
        M.fit("Q3", "joint, summer 2024, without zone", "y_s24", RIGHTS21, base3, data=d[~d["in_zone"]])
        for c in RIGHTS21:
            M.fit("Q3", f"alone, summer 2024: {c}", "y_s24", [c], base3)
        M.fit("Q3", "joint, recent level", "y_recent", RIGHTS21, base3)
    else:
        log("no light trajectories (22) — Q3 skipped")

    # ================= Q4 cultural sphere and recent light ===============================================
    log("\n==== Q4 — the negative cultural–light link ====")
    base4 = ["econ_2021", "rights_2021", "exp"] + ctrl
    school = ["log_class_size", "rural_school_share"]       # pupils per 1,000 covers about 60 %: separate row
    if "y_recent" in d:
        M.fit("Q4", "joint cultural indicators, recent level", "y_recent", CULT21, base4, ci=tuple(CULT21))
        M.fit("Q4", "joint cultural indicators, reliable light", "y_recent", CULT21, base4, data=d[rel])
        M.fit("Q4", "joint cultural indicators, summer 2024", "y_s24", CULT21, base4)
        M.fit("Q4", "cultural 2021, same sample as school network", "y_recent", ["cult_2021"], base4,
              data=d[d[school].notna().all(axis=1)])
        M.fit("Q4", "cultural 2021 + school network", "y_recent", ["cult_2021"] + school, base4)
        M.fit("Q4", "cultural 2021, same sample as pupils per 1,000", "y_recent", ["cult_2021"], base4,
              data=d[d[school + ["log_pupils_pc"]].notna().all(axis=1)])
        M.fit("Q4", "cultural 2021 + school network + pupils per 1,000", "y_recent",
              ["cult_2021"] + school + ["log_pupils_pc"], base4)
        M.fit("Q4", "cultural 2021, same sample as population change", "y_recent", ["cult_2021"], base4,
              data=d[d["pop_change"].notna()])
        M.fit("Q4", "cultural 2021 + population change (GHS, modelled)", "y_recent", ["cult_2021", "pop_change"],
              base4)
        for t in ("city", "settlement", "village"):
            M.fit("Q4", f"cultural 2021, {t} hromadas", "y_recent", ["cult_2021"], base4, data=d[d["htype"] == t])
    else:
        log("no light trajectories (22) — Q4 models skipped")
    d["cult21_q"] = pd.qcut(d["cult_2021"].rank(method="first"), 5, labels=[f"Q{i}" for i in range(1, 6)])
    g4 = {f"cultural 2021 {q}": d["cult21_q"] == q for q in [f"Q{i}" for i in range(1, 6)]}
    profile("Q4", "Q4 profile by cultural-2021 quintile", g4,
            [("culture_arts_pc_2021", "median"), ("education_pc_2021", "median"),
             ("extracurricular_pc_2021", "median"), ("class_size_2021", "median"), ("pupils_per1000_2021", "median"),
             ("rural_school_share", "median"), ("pop_ghs_2020", "median"), ("pop_change", "median"),
             ("fop_growth", "median"), ("econ_2021", "median"), ("rights_2021", "median"),
             ("is_city", "share"), ("is_settlement", "share"), ("is_village", "share"), ("in_zone", "share")])
    if "y_recent" in d:
        lm = d.groupby("cult21_q", observed=True)["tr_recent"].median().round(3)
        log("\nrecent light level (tr_recent, median) by cultural-2021 quintile — log only, rule R2:\n"
            + lm.to_string())
        lt = d.groupby("htype")["tr_recent"].median().round(3)
        log("recent light level by hromada type — log only:\n" + lt.to_string())

    # ================= Q5 Carpathian economic rise =======================================================
    log("\n==== Q5 — the Carpathian economic rise ====")
    g5 = {OBL[k]: d["k1"] == k for k in ("21", "26", "46", "73")}
    g5["Carpathian"] = d["k1"].isin(CARP)
    g5["rest, outside zone"] = ~d["k1"].isin(CARP) & ~d["in_zone"]
    g5["rest"] = ~d["k1"].isin(CARP)
    spec5 = [("econ_2021", "median"), ("econ_2025", "median"), ("d_econ", "median"), ("d_ll_econ", "median")]
    spec5 += [(f"dr_{nm}", "median") for nm, _, _ in COMMON["econ"]]
    spec5 += [("r_pdfo_civ_growth_rel_2125", "median"), ("pdfo_civ_growth_rel_2125", "median"),
              ("fop_growth", "median"), ("le_growth", "median"), ("pop_change", "median"),
              ("d_ll_rights", "median"), ("d_ll_cult", "median"), ("is_city", "share")]
    profile("Q5", "Q5 economic change, Carpathian oblasts", g5, spec5)

    M.fit("Q5", "Carpathian gap, like-for-like economic change", "d_ll_econ", ["carp"], ["c_logpop"], fe=False,
          raw=("carp",), ci=("carp",))
    M.fit("Q5", "Carpathian gap, economic index change", "d_econ", ["carp"], ["c_logpop"], fe=False, raw=("carp",))
    M.fit("Q5", "Carpathian gap + population change (GHS, modelled)", "d_ll_econ", ["carp", "pop_change"],
          ["c_logpop"], fe=False, raw=("carp",))
    M.fit("Q5", "Carpathian gap without zone", "d_ll_econ", ["carp"], ["c_logpop"], fe=False, raw=("carp",),
          data=d[~d["in_zone"]])
    # the Carpathian oblasts started low (regression to the mean): the same gap given the 2021 level
    M.fit("Q5", "Carpathian gap given 2021 level, like-for-like", "ll_econ_2025", ["carp"], ["ll_econ_2021", "c_logpop"],
          fe=False, raw=("carp",), ci=("carp",))
    M.fit("Q5", "Carpathian gap given 2021 level, economic index", "econ_2025", ["carp"], ["econ_2021", "c_logpop"],
          fe=False, raw=("carp",))
    M.fit("Q5", "Carpathian gap given 2021 level, like-for-like, without Lviv", "ll_econ_2025", ["carp"],
          ["ll_econ_2021", "c_logpop"], fe=False, raw=("carp",), data=d[d["k1"] != "46"])
    M.fit("Q5", "Carpathian gap given 2021 level, like-for-like, without zone", "ll_econ_2025", ["carp"],
          ["ll_econ_2021", "c_logpop"], fe=False, raw=("carp",), data=d[~d["in_zone"]])
    for nm, _, _ in COMMON["econ"]:
        M.fit("Q5", f"Carpathian gap: {nm}", f"dr_{nm}", ["carp"], ["c_logpop"], fe=False, raw=("carp",))
    M.fit("Q5", "Carpathian gap: PIT growth rank 2025", "r_pdfo_civ_growth_rel_2125", ["carp"], ["c_logpop"],
          fe=False, raw=("carp",))
    # registration growth exists only where the regional statistics office published both snapshots
    reg_obl = sorted(d.loc[d["fop_growth"].notna(), "k1"].unique())
    log(f"\nregistration growth (2022-01 -> latest) available in oblasts {reg_obl} only "
        f"({int(d['fop_growth'].notna().sum())} hromadas) — no Carpathian oblast; single-tax revenue per resident "
        f"(dr_single_tax_pc) is the nationwide small-business signal")
    M.fit("Q5", "registrations within oblasts (oblasts with data)", "d_ll_econ", ["fop_growth", "le_growth"],
          ["c_logpop"], note=f"oblasts {','.join(reg_obl)}")
    M.fit("Q5", "registrations vs single-tax rank change (oblasts with data)", "dr_single_tax_pc", ["fop_growth"],
          ["c_logpop"], note=f"oblasts {','.join(reg_obl)}")

    lk = rd("sphere_lisa_k3.csv", required=False)
    if lk is not None and "d_econ_national" in lk:
        d2 = d.merge(lk[["k3", "d_econ_national", "d_cult_national"]], on="k3", how="left")
        PD = d2
        for v in ("d_econ_national", "d_cult_national"):
            cl = d2[v].fillna("na")
            g6 = {"HH": cl == "HH", "LL": cl == "LL", "HL or LH": cl.isin(["HL", "LH"]), "not significant": cl == "ns"}
            d2["is_carp"] = d2["carp"]
            profile("Q5", f"Q5 profile of LISA clusters: {v}", g6,
                    [("is_carp", "share"), ("in_zone", "share"), ("is_city", "share"), ("exp_strikes_log", "median"),
                     ("econ_2021", "median"), ("d_econ", "median"), ("d_ll_econ", "median"),
                     ("dr_pdfo_civ_pc", "median"), ("dr_single_tax_pc", "median"), ("dr_property_tax_pc", "median"),
                     ("r_pdfo_civ_growth_rel_2125", "median"), ("d_ll_cult", "median"), ("fop_growth", "median"),
                     ("le_growth", "median"), ("pop_change", "median")])
        PD = d
    else:
        log("\nsphere_lisa_k3.csv (36) not found — LISA cluster profiles skipped")

    dtm = TIDY / "dtm_oblast_latest_k1.csv"
    if dtm.exists():
        try:
            t = rd("dtm_oblast_latest_k1.csv")
            num = [c for c in t.columns if c not in ("k1", "k2", "k3") and pd.api.types.is_numeric_dtype(t[c])]
            log("\nIOM DTM, latest oblast figures — LOG ONLY, not for publication (DTM terms):\n"
                + t[t["k1"].isin(CARP)][["k1"] + num[:6]].to_string(index=False))
        except Exception as ex:
            log(f"\nIOM DTM oblast file not readable ({ex})")

    # ---- outputs
    res = pd.DataFrame(M.rows).rename(columns={"part": "question"})
    res.to_csv(OUT_M, index=False, float_format="%.6g")
    P = pd.concat(PROFILES, ignore_index=True)
    P.to_csv(OUT_P, index=False, float_format="%.6g")
    log(f"\nwrote {OUT_M.relative_to(BASE)} ({len(res)} rows), {OUT_P.relative_to(BASE)} ({len(P)} rows)"
        f"   [{(time.time() - t0) / 60:.1f} min]")


if __name__ == "__main__":
    main()
