#!/usr/bin/env python3
"""
23_carpathian.py — Carpathian deep dive: hromada profiles and regional summary for
Zakarpattia (21), Ivano-Frankivsk (26), Lviv (46), Chernivtsi (73).

  python 23_carpathian.py

Inputs (tidy/): resilience_v1_k3.csv, resilience_index_v11_k3.csv, trajectories_k3.csv,
  nightlights_panel_k3.csv, budget_quarterly_k3.csv, oblast_context_k1.csv, dtm_oblast_latest_k1.csv
Outputs: tidy/carpathian_profiles_k3.csv, tidy/carpathian_ntl_monthly.csv,
  tidy/carpathian_budget_quarterly.csv, docs/carpathian_profiles.xlsx
Light metrics flagged reliable if >= 30 lit pixels and pre-war noise_sd <= 0.35.
Typology: regional terciles (within the 4 oblasts) of capacity x summer-2024 outage loss —
  descriptive only. No new data; aggregated open data only.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
TIDY, DOCS = BASE / "tidy", BASE / "docs"
DOCS.mkdir(exist_ok=True)
OBL = {"21": "Zakarpattia", "26": "Ivano-Frankivsk", "46": "Lviv", "73": "Chernivtsi"}
REL_NLIT, REL_NOISE = 30, 0.35
pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 30)


def rd(name, **kw):
    d = pd.read_csv(TIDY / name, dtype={"k1": str, "k2": str, "k3": str}, **kw)
    if "k3" in d:
        d["k3"] = d["k3"].str.zfill(7)
    return d


def pick(d, cols):
    return d[[c for c in cols if c in d.columns]]


def main():
    res = rd("resilience_v1_k3.csv")
    idx = rd("resilience_index_v11_k3.csv")
    tr = rd("trajectories_k3.csv")
    d = pick(res, ["k3", "name", "occupied", "pop_ghs_2020", "own_rev_gf_pc_2025", "transfer_dep_2025",
                   "capex_share_2325", "pdfo_civ_growth_rel_2125", "pdfo_mil_share_2021", "garrison_flag",
                   "ntl_n_lit_px", "le_per1k_reg", "le_change_reg", "fop_per1k_reg", "fop_change_reg"])
    d = d.merge(pick(idx, ["k3", "capacity_index", "recovery_index", "engagement_index", "dream_per10k",
                           "exp_strikes_log", "alert_h_12m", "civcas_all"]), on="k3", how="left")
    d = d.merge(pick(tr, ["k3", "capacity_prewar", "tr_h2_23", "tr_s24", "tr_s24_rel", "tr_recent",
                          "tr_trough", "tr_trough_q", "tr_slope_2426", "tr_change_class", "tr_noise_sd",
                          "bt_pit_2022", "bt_pit_recent", "bt_own_recent"]), on="k3", how="left")
    d["k1"] = d["k3"].str[:2]
    d["occupied"] = pd.to_numeric(d["occupied"], errors="coerce").fillna(0).astype(int)
    d["strikes_n"] = np.expm1(d["exp_strikes_log"]).round()
    d["light_reliable"] = ((d["ntl_n_lit_px"] >= REL_NLIT) & (d["tr_noise_sd"] <= REL_NOISE)).astype(int)
    nat = d[d["occupied"] == 0].copy()
    c = nat[nat["k1"].isin(OBL)].copy()
    c["oblast"] = c["k1"].map(OBL)
    c["cap_rank_carp"] = c["capacity_index"].rank(pct=True).round(3)
    print(f"Carpathian non-occupied hromadas: {len(c)}  "
          f"{c['oblast'].value_counts().to_dict()}; light metrics: {c['tr_recent'].notna().sum()}, "
          f"reliable: {int(c['light_reliable'].sum())}")

    # ---------------- summary: medians national / Carpathian / oblast
    M = [("capacity_index", "capacity (national pct)"), ("own_rev_gf_pc_2025", "own revenue per capita 2025, UAH"),
         ("transfer_dep_2025", "transfer dependency 2025"), ("capex_share_2325", "capex share 2023-25"),
         ("pdfo_civ_growth_rel_2125", "civ PIT growth 21-25 (rel.)"), ("alert_h_12m", "alert hours 12 m"),
         ("strikes_n", "strike events since 2022"), ("tr_h2_23", "light H2 2023 (vs pre-war)"),
         ("tr_s24_rel", "summer-24 light / H2 2023"), ("tr_recent", "light last 12 m (vs pre-war)"),
         ("tr_trough", "worst quarter light"), ("bt_pit_2022", "civ PIT rel. 2022 Q2-Q4"),
         ("bt_pit_recent", "civ PIT rel. last 4 q"), ("dream_per10k", "DREAM projects / 10k"),
         ("pop_ghs_2020", "population 2020 (GHS)")]
    cols = {"national": nat, "Carpathian": c} | {v: c[c["k1"] == k] for k, v in OBL.items()}
    S = pd.DataFrame({g: [x[m].median() for m, _ in M] for g, x in cols.items()},
                     index=[lab for _, lab in M])
    S.loc["hromadas (n)"] = [len(x) for x in cols.values()]
    S.loc["share with >= 1 strike"] = [(x["strikes_n"] > 0).mean() for x in cols.values()]
    S.loc["share light declined since H2-23"] = [
        (x["tr_change_class"] == "declined").sum() / max(1, x["tr_change_class"].isin(["declined", "stable", "improved"]).sum())
        for x in cols.values()]
    S.loc["garrison hromadas (n)"] = [int(x["garrison_flag"].fillna(0).sum()) for x in cols.values()]
    print("\nmedians:\n" + S.to_string(float_format=lambda v: f"{v:,.3f}" if abs(v) < 10 else f"{v:,.0f}"))

    # ---------------- oblast context (reSCORE, DTM)
    ctx = rd("oblast_context_k1.csv")
    ctx["k1"] = ctx["k1"].str.zfill(2)
    cc = [x for x in ctx.columns if x.endswith("_2024") or x.endswith("_2024_vs_nat") or "idp" in x.lower()]
    C = ctx[ctx["k1"].isin(OBL)].set_index("k1")[cc].rename(index=OBL).T
    dt = rd("dtm_oblast_latest_k1.csv")
    dt["k1"] = dt["k1"].astype(str).str.zfill(2)
    dc = [x for x in ("dtm_reg_per1000", "dtm_svy_per1000", "dtm_reg_change", "dtm_reg_front_share") if x in dt]
    C = pd.concat([C, dt[dt["k1"].isin(OBL)].set_index("k1")[dc].rename(index=OBL).T])
    print("\noblast context (reSCORE 2024, DTM):\n" + C.to_string(float_format=lambda v: f"{v:.2f}"))

    # ---------------- within-region correlations
    pairs = [("capacity_index", "tr_s24_rel"), ("capacity_prewar", "tr_s24_rel"), ("capacity_index", "tr_recent"),
             ("pop_ghs_2020", "tr_s24_rel"), ("pop_ghs_2020", "capacity_index"), ("alert_h_12m", "tr_recent"),
             ("capacity_index", "bt_pit_2022"), ("tr_s24_rel", "tr_recent"), ("capacity_index", "dream_per10k")]
    rel = c[c["light_reliable"] == 1]
    R = pd.DataFrame([{"x": a, "y": b, "rho_all": c[[a, b]].corr(method="spearman").iloc[0, 1],
                       "n_all": int(c[[a, b]].dropna().shape[0]),
                       "rho_reliable": rel[[a, b]].corr(method="spearman").iloc[0, 1],
                       "n_rel": int(rel[[a, b]].dropna().shape[0])} for a, b in pairs])
    print("\nSpearman within the 4 oblasts:\n" + R.to_string(index=False, float_format=lambda v: f"{v:.2f}"))

    # ---------------- typology: regional terciles capacity x outage loss
    def t3(s):
        out = pd.Series(pd.NA, index=s.index, dtype="object")
        ok = s.notna()
        out[ok] = pd.qcut(s[ok].rank(method="first"), 3, labels=["low", "mid", "high"]).astype(str)
        return out
    c["cap_t_carp"] = t3(c["capacity_index"])
    c["s24_t_carp"] = t3(c["tr_s24_rel"])          # high = kept most light (smallest loss)
    typ = {("high", "high"): "strong & steady", ("high", "low"): "strong but hit",
           ("low", "high"): "weak but steady", ("low", "low"): "weak & hit"}
    c["type_carp"] = [typ.get((a, b), "") if pd.notna(a) and pd.notna(b) else ""
                      for a, b in zip(c["cap_t_carp"], c["s24_t_carp"])]
    X = pd.crosstab(c["cap_t_carp"], c["s24_t_carp"]).reindex(index=["low", "mid", "high"],
                                                              columns=["low", "mid", "high"])
    print("\ncapacity tercile (rows) x outage-loss tercile (cols, high = kept most light), regional:\n" + X.to_string())
    print("\ncorner types by oblast:\n" + pd.crosstab(c["oblast"], c["type_carp"].replace("", np.nan)).to_string())
    show = ["oblast", "name", "pop_ghs_2020", "capacity_index", "tr_s24_rel", "tr_recent", "tr_change_class",
            "light_reliable"]
    for t in typ.values():
        g = c[c["type_carp"] == t].sort_values("pop_ghs_2020", ascending=False)
        print(f"\n{t} (n={len(g)}, largest 6):\n" +
              g[show].head(6).to_string(index=False, float_format=lambda v: f"{v:.2f}" if v < 100 else f"{v:,.0f}"))

    # ---------------- series for charts
    p = rd("nightlights_panel_k3.csv", usecols=["k3", "date", "ntl_idx"])
    lit = nat.set_index("k3")["ntl_n_lit_px"]
    p = p[p["k3"].isin(lit[lit >= 10].index)]
    p["k1"] = p["k3"].str[:2]
    nm = p.groupby("date")["ntl_idx"].median().rename("national")
    om = p[p["k1"].isin(OBL)].groupby(["date", "k1"])["ntl_idx"].median().unstack().rename(columns=OBL)
    ntl = pd.concat([nm, om], axis=1)
    ntl.loc[ntl.index == "2025-06", :] = np.nan            # artefact month, as in 22
    ntl.to_csv(TIDY / "carpathian_ntl_monthly.csv")
    bq = rd("budget_quarterly_k3.csv")
    bq = bq[bq["k3"].isin(nat["k3"])]
    bq["k1"] = bq["k3"].str[:2]
    bq["yq"] = bq["year"].astype(str) + "Q" + bq["q"].astype(str)
    B = []
    for v in ("pdfo_civ_rel", "own_gf_rel"):
        b = bq[bq["k1"].isin(OBL)].groupby(["yq", "k1"])[v].median().unstack().rename(columns=OBL)
        b.columns = [f"{v}_{x}" for x in b.columns]
        B.append(b)
    B = pd.concat(B, axis=1).dropna(how="all")
    B.to_csv(TIDY / "carpathian_budget_quarterly.csv")
    print("\nlight index, oblast medians (selected months):\n" +
          ntl.loc[[m for m in ("2022-03", "2022-11", "2023-10", "2024-07", "2025-01", "2025-10", "2026-02",
                               "2026-08") if m in ntl.index]].to_string(float_format=lambda v: f"{v:.2f}"))
    print("\ncivil PIT rel., oblast medians (selected quarters):\n" +
          B.loc[[q for q in ("2022Q1", "2022Q3", "2023Q3", "2024Q3", "2025Q3", "2026Q2") if q in B.index],
                [x for x in B.columns if x.startswith("pdfo")]].to_string(float_format=lambda v: f"{v:.2f}"))

    # ---------------- outputs
    pcols = ["oblast", "k3", "name", "pop_ghs_2020", "capacity_index", "cap_rank_carp", "capacity_prewar",
             "own_rev_gf_pc_2025", "transfer_dep_2025", "capex_share_2325", "pdfo_civ_growth_rel_2125",
             "garrison_flag", "strikes_n", "alert_h_12m", "tr_h2_23", "tr_s24_rel", "tr_recent", "tr_trough",
             "tr_trough_q", "tr_slope_2426", "tr_change_class", "ntl_n_lit_px", "tr_noise_sd", "light_reliable",
             "bt_pit_2022", "bt_pit_recent", "bt_own_recent", "dream_per10k", "le_per1k_reg", "fop_per1k_reg",
             "cap_t_carp", "s24_t_carp", "type_carp"]
    P = pick(c, pcols).sort_values(["oblast", "capacity_index"], ascending=[True, False])
    P.to_csv(TIDY / "carpathian_profiles_k3.csv", index=False)
    notes = pd.DataFrame({"item": [
        "capacity_index", "cap_rank_carp", "capacity_prewar", "tr_h2_23 / tr_recent", "tr_s24_rel",
        "tr_change_class", "light_reliable", "bt_pit_2022 / bt_pit_recent", "type_carp", "le/fop_per1k_reg",
        "caveats"],
        "meaning": [
        "national percentile of v1.1 capacity (own revenue pc, transfer dependency inv., capex share, civ PIT growth)",
        "percentile of capacity within the 4 oblasts",
        "2021 own revenue pc and transfer dependency, percentile mean",
        "night-light index = radiance / same month 2020-21 (1 = pre-war); H2 2023 = Jul-Dec 2023; recent = last 12 m",
        "light Jun-Jul 2024 as share of own H2 2023 level (outage loss; higher = kept more light)",
        "last 12 m vs H2 2023 beyond +-2 x own pre-war noise",
        f">= {REL_NLIT} lit pixels and noise_sd <= {REL_NOISE}; small towns otherwise noisy — do not quote single values",
        "civilian PIT ratio to same quarter 2021 / national median (1 = national median position)",
        "regional terciles of capacity x outage loss (descriptive corner cases)",
        "statistics-office ЄДРПОУ tables, partial coverage (~40 % / 33 % of hromadas)",
        "light reflects lighting policy and grid conditions; PIT booked at employer address; population GHS-POP 2020 "
        "(pre-war); associations are cross-sectional"]})
    xl = DOCS / "carpathian_profiles.xlsx"
    with pd.ExcelWriter(xl, engine="openpyxl") as w:
        S.to_excel(w, sheet_name="summary")
        C.to_excel(w, sheet_name="oblast_context")
        R.to_excel(w, sheet_name="correlations", index=False)
        X.to_excel(w, sheet_name="typology")
        P.to_excel(w, sheet_name="profiles", index=False)
        ntl.to_excel(w, sheet_name="light_monthly")
        B.to_excel(w, sheet_name="budget_quarterly")
        notes.to_excel(w, sheet_name="notes", index=False)
    print(f"\nwrote tidy/carpathian_profiles_k3.csv ({len(P)}), carpathian_ntl_monthly.csv, "
          f"carpathian_budget_quarterly.csv, docs/{xl.name}")
    vk = P[P["k3"] == "2602003"]
    if len(vk):
        print("\nVerkhovyna:\n" + vk.T.to_string(header=False))


if __name__ == "__main__":
    main()
