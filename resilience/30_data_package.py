#!/usr/bin/env python3
"""
30_data_package.py — export the data package for Zenodo (publication request 32), applying security rules R2–R6.

  python 30_data_package.py        (after run_all.sh; writes publication/data_package/out/, never committed)

R2  Hromada monthly night lights end at PUB_END (>= 6 months before release); only reliable hromadas (>= 30 lit pixels
    and pre-war noise_sd <= 0.35). Trajectory metrics are recomputed from the panel cut at PUB_END. The latest months
    appear at oblast level only (oblast_nightlight_monthly.csv, full period).
R3  Every raion touched by the front-line and border zone (28_frontline_zone.py) is aggregated as a whole: one row per
    raion (unit_type raion_r3, k3 empty) over all its non-occupied hromadas, none of which appear individually —
    aggregating only the zone part would let users recover zone hromadas by subtraction. Sums for counts and budget
    flows; population-weighted means for alert hours and capacity; lit-pixel-weighted means for night lights.
R4  Civilian income tax only: military PIT removed from revenue and own funds; no garrison flag.
R5  Strike counts per unit only; no event points, no dates of last strike.
R6  No personal names or free text (official hromada and raion names only).
Occupied units and Crimea appear in the exposure table only (missing_reason "occupied" elsewhere).
Oblast context (IOM DTM, reSCORE) is not included (upstream terms); see the fetch scripts in the repository.
"""
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
TIDY, PUB = BASE / "tidy", BASE / "public"
OUT = ROOT / "publication/data_package/out"
TAB, GEO = OUT / "data/tables", OUT / "data/geo"
PUB_END = "2026-03"
EXCL = {"2025-06"}
REL_NLIT, REL_NOISE, MIN_LIT = 30, 0.35, 10
ID = ["unit_type", "k1", "k2", "k3", "name"]
R4_BAD = ("garrison", "pdfo_mil", "_mil", "military")


def zf(df):
    for c, n in (("k1", 2), ("k2", 4), ("k3", 7)):
        if c in df:
            df[c] = df[c].astype(str).str.zfill(n)
    return df


def num(df, cols):
    for c in cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def wmean(v, w):
    v, w = pd.to_numeric(v, errors="coerce"), pd.to_numeric(w, errors="coerce")
    ok = v.notna() & w.notna() & (w > 0)
    return float(np.average(v[ok], weights=w[ok])) if ok.any() else np.nan


def aggregate(df, keys, sums=(), wmeans=None, mins=()):
    wmeans = wmeans or {}
    rows = []
    for kv, d in df.groupby(keys, sort=True):
        kv = kv if isinstance(kv, tuple) else (kv,)
        r = dict(zip(keys, kv))
        r["n_hromadas"] = d["k3"].nunique()
        for c in sums:
            r[c] = pd.to_numeric(d[c], errors="coerce").sum(min_count=1)
        for c in mins:
            r[c] = pd.to_numeric(d[c], errors="coerce").min()
        for c, w in wmeans.items():
            r[c] = wmean(d[c], d[w])
        rows.append(r)
    return pd.DataFrame(rows)


def main():
    TAB.mkdir(parents=True, exist_ok=True)
    GEO.mkdir(parents=True, exist_ok=True)

    # ---------------- frame, R3 raions
    u = zf(pd.read_csv(TIDY / "resilience_v1_k3.csv", dtype={"k1": str, "k2": str, "k3": str}))[
        ["k1", "k2", "k3", "name", "occupied", "pop_ghs_2020", "ntl_n_lit_px", "dream_n"]]
    u["occupied"] = u["occupied"].astype(str).str.lower().isin(["true", "1", "1.0"]).astype(int)
    u = num(u, ["pop_ghs_2020", "ntl_n_lit_px", "dream_n"])
    zone = zf(pd.read_csv(TIDY / "frontline_zone_k3.csv", dtype=str))
    touched = set(zone.loc[zone["zone"] == "1", "k2"])
    u["r3"] = (u["occupied"] == 0) & u["k2"].isin(touched)
    r3k3 = set(u.loc[u["r3"], "k3"])
    rn = zf(gpd.read_file(ROOT / "viina/qgis/admin_units.gpkg", layer="raion", read_geometry=False))[["k1", "k2", "name"]]
    rn = rn.drop_duplicates("k2")
    print(f"frame {len(u):,} units ({int((u['occupied'] == 0).sum()):,} non-occupied); R3: {len(touched)} raions "
          f"aggregated as a whole ({len(r3k3)} hromadas, of which {int((zone['zone'] == '1').sum())} in the zone)")

    def hrom(df):
        d = df[~df["k3"].isin(r3k3)].copy()
        d["unit_type"] = "hromada"
        return d

    def raion(df):
        d = df.merge(rn, on="k2", how="left")
        d["unit_type"], d["k3"] = "raion_r3", ""
        return d

    def write(name, h, r, cols, sort=("k1", "k2", "k3")):
        t = pd.concat([h, r], ignore_index=True)
        t = t[[c for c in ID + cols if c in t.columns]].sort_values(list(sort)).reset_index(drop=True)
        t.to_csv(TAB / name, index=False, float_format="%.6g")
        print(f"  {name}: {len(t):,} rows ({(t['unit_type'] == 'raion_r3').sum():,} raion_r3)")
        return t

    print("\ntables:")
    # ---------------- 1 exposure (whole frame)
    us = zf(pd.read_csv(ROOT / "viina/qgis/unit_stats_hromada.csv", dtype={"k1": str, "k2": str, "k3": str}))
    E_SUM = ["area_km2", "n_all", "rep_all", "civcas_all", "n_12m", "rep_12m", "civcas_12m"]
    E_W = ["alert_h_12m", "alert_n_12m", "alert_h_all", "alert_n_all"]
    ex = u[["k1", "k2", "k3", "name", "occupied", "pop_ghs_2020", "r3"]].merge(
        num(us[["k3"] + E_SUM + E_W].copy(), E_SUM + E_W), on="k3", how="left", validate="1:1")
    t_ex = write("hromada_exposure.csv", hrom(ex),
                 raion(aggregate(ex[ex["r3"]], ["k2"], E_SUM + ["pop_ghs_2020"], {c: "pop_ghs_2020" for c in E_W})),
                 ["n_hromadas", "occupied", "pop_ghs_2020"] + E_SUM + E_W)

    # ---------------- 2 indices
    ix = zf(pd.read_csv(TIDY / "resilience_index_v11_k3.csv", dtype={"k3": str}))[
        ["k3", "capacity_index", "recovery_index", "engagement_index", "dream_per10k"]]
    pre = zf(pd.read_csv(TIDY / "trajectories_k3.csv", dtype={"k3": str}))[["k3", "capacity_prewar"]]
    ind = u.merge(ix, on="k3", how="left", validate="1:1").merge(pre, on="k3", how="left", validate="1:1")
    ind = num(ind, ["capacity_index", "recovery_index", "engagement_index", "dream_per10k", "capacity_prewar"])
    reasons = []
    for r in ind.itertuples():
        if r.occupied == 1:
            reasons.append("occupied")
            continue
        m = []
        if pd.isna(r.capacity_index):
            m.append("cap_lt3")
        if pd.isna(r.recovery_index):
            m.append("rec_lit_lt10" if (pd.isna(r.ntl_n_lit_px) or r.ntl_n_lit_px < MIN_LIT) else "rec_no_ratio")
        if pd.isna(r.engagement_index):
            m.append("eng_pop_lt100")
        reasons.append(";".join(m))
    ind["missing_reason"] = reasons
    ri = aggregate(ind[ind["r3"]], ["k2"], ["pop_ghs_2020", "dream_n"],
                   {"capacity_index": "pop_ghs_2020", "capacity_prewar": "pop_ghs_2020", "recovery_index": "ntl_n_lit_px"})
    ri["dream_per10k"] = ri["dream_n"] / ri["pop_ghs_2020"] * 1e4
    ri["missing_reason"] = "r3_raion"
    write("hromada_indices.csv", hrom(ind), raion(ri),
          ["n_hromadas", "occupied", "capacity_index", "capacity_prewar", "recovery_index", "engagement_index",
           "dream_per10k", "missing_reason"])

    # ---------------- 3 budget annual (civilian, from public/)
    ba = zf(pd.read_csv(PUB / "budget_long_k3_year.csv", dtype={"k3": str}))
    B_SUM = ["rev_total_civ", "transfers", "own_gf_civ", "pdfo_civ", "exp_total", "capex"]
    B_MIN = ["inc_last_month", "exp_last_month"]
    ba = num(ba, B_SUM + B_MIN).merge(u[["k1", "k2", "k3", "name", "r3"]], on="k3", how="left")
    write("hromada_budget_annual.csv", hrom(ba),
          raion(aggregate(ba[ba["r3"].fillna(False)], ["k2", "year"], B_SUM, mins=B_MIN)),
          ["n_hromadas", "year"] + B_SUM + B_MIN, sort=("k1", "k2", "k3", "year"))

    # ---------------- 4 budget quarterly (military PIT removed)
    bq = zf(pd.read_csv(TIDY / "budget_quarterly_k3.csv", dtype={"k3": str}))
    bq = num(bq, ["rev_total", "transfers", "own_gf", "pdfo_mil", "pdfo_civ", "last_month"])
    bq["rev_total_civ"] = bq["rev_total"] - bq["pdfo_mil"].fillna(0)
    bq["own_gf_civ"] = bq["own_gf"] - bq["pdfo_mil"].fillna(0)
    Q_SUM = ["rev_total_civ", "transfers", "own_gf_civ", "pdfo_civ"]
    bq = bq[["k3", "year", "q", "last_month"] + Q_SUM].merge(u[["k1", "k2", "k3", "name", "r3"]], on="k3", how="left")
    write("hromada_budget_quarterly.csv", hrom(bq),
          raion(aggregate(bq[bq["r3"].fillna(False)], ["k2", "year", "q"], Q_SUM, mins=["last_month"])),
          ["n_hromadas", "year", "q", "last_month"] + Q_SUM, sort=("k1", "k2", "k3", "year", "q"))

    # ---------------- night lights: panel, reliability
    p = zf(pd.read_csv(TIDY / "nightlights_panel_k3.csv", dtype={"k3": str},
                       usecols=["k3", "date", "ntl_idx", "valid_frac_lit"]))
    p = num(p[~p["date"].isin(EXCL)], ["ntl_idx", "valid_frac_lit"])
    tj = zf(pd.read_csv(TIDY / "trajectories_k3.csv", dtype={"k3": str}))[["k3", "tr_light_reliable", "tr_noise_sd"]]
    tj = num(tj, ["tr_light_reliable", "tr_noise_sd"])
    uu = u.merge(tj, on="k3", how="left")
    rel = set(uu.loc[(uu["tr_light_reliable"] == 1) & (uu["occupied"] == 0), "k3"])
    pc = p[p["date"] <= PUB_END].merge(uu[["k1", "k2", "k3", "name", "ntl_n_lit_px", "tr_noise_sd", "r3"]], on="k3")
    hm = pc[pc["k3"].isin(rel) & ~pc["r3"]].copy()
    rm_src = pc[pc["k3"].isin(rel) & pc["r3"]]
    rm = raion(aggregate(rm_src, ["k2", "date"], wmeans={"ntl_idx": "ntl_n_lit_px"}))

    # ---------------- 5 hromada monthly (R2, R3)
    hm["unit_type"] = "hromada"
    write("hromada_nightlight_monthly.csv", hm, rm, ["n_hromadas", "date", "ntl_idx", "valid_frac_lit"],
          sort=("k1", "k2", "k3", "date"))

    # ---------------- 6 oblast monthly (full period)
    po = p.merge(uu[["k1", "k3", "occupied", "ntl_n_lit_px"]], on="k3")
    po = po[(po["occupied"] == 0) & (po["ntl_n_lit_px"] >= MIN_LIT)]
    ob = aggregate(po, ["k1", "date"], wmeans={"ntl_idx": "ntl_n_lit_px"})
    na = aggregate(po.assign(k1="UA"), ["k1", "date"], wmeans={"ntl_idx": "ntl_n_lit_px"})
    obl = pd.concat([ob, na], ignore_index=True).sort_values(["k1", "date"])
    obl.to_csv(TAB / "oblast_nightlight_monthly.csv", index=False, float_format="%.6g")
    print(f"  oblast_nightlight_monthly.csv: {len(obl):,} rows, {obl['date'].min()} – {obl['date'].max()}")

    # ---------------- 7 trajectory metrics (cut at PUB_END)
    S = pd.concat([hm[["k3", "date", "ntl_idx"]].rename(columns={"k3": "uid"}),
                   rm[["k2", "date", "ntl_idx"]].assign(uid=lambda d: "R" + d["k2"])[["uid", "date", "ntl_idx"]]],
                  ignore_index=True)
    pub = pd.Period(PUB_END, freq="M")
    W = {"w2223": ("2022-11", "2023-02"), "h2_23": ("2023-07", "2023-12"), "s24": ("2024-06", "2024-07"),
         "w2425": ("2024-12", "2025-02"), "pub": (str(pub - 11), str(pub))}
    M, cnt = pd.DataFrame(index=sorted(S["uid"].unique())), {}
    for name, (a, b) in W.items():
        ms = [str(x) for x in pd.period_range(a, b, freq="M") if str(x) not in EXCL]
        g = S[S["date"].isin(ms)].groupby("uid")["ntl_idx"].agg(["mean", "count"])
        M[f"tr_{name}"] = g["mean"].where(g["count"] >= max(1, int(np.ceil(len(ms) / 2))))
        cnt[name] = g["count"]
    S["year"], S["q"] = S["date"].str[:4].astype(int), (S["date"].str[5:7].astype(int) - 1) // 3 + 1
    qn = S.groupby(["uid", "year", "q"])["ntl_idx"].agg(ntl_q="mean", n_m="count").reset_index()
    qn.loc[qn["n_m"] < 2, "ntl_q"] = np.nan
    qn["t"] = qn["year"] + (qn["q"] - 1) / 4
    war = qn[(qn["t"] >= 2022.25) & qn["ntl_q"].notna()]
    trq = war.loc[war.groupby("uid")["ntl_q"].idxmin()].set_index("uid")
    M["tr_trough"] = trq["ntl_q"]
    M["tr_trough_q"] = trq["year"].astype(int).astype(str) + "Q" + trq["q"].astype(int).astype(str)
    M["tr_below50_share"] = war.assign(b=war["ntl_q"] < 0.5).groupby("uid")["b"].mean()
    sl = {}
    for uid, g in qn[(qn["t"] >= 2024) & qn["ntl_q"].notna()].groupby("uid"):
        if len(g) >= 8:
            sl[uid] = np.polyfit(g["t"].values, g["ntl_q"].values, 1)[0]
    M["tr_slope_2024_2026q1"] = pd.Series(sl, dtype=float)
    M["tr_s24_rel"] = M["tr_s24"] / M["tr_h2_23"]
    noise = pd.concat([hm.drop_duplicates("k3").set_index("k3")["tr_noise_sd"],
                       pd.Series({"R" + k2: wmean(d["tr_noise_sd"], d["ntl_n_lit_px"])
                                  for k2, d in rm_src.drop_duplicates("k3").groupby("k2")})])
    zc = (np.log(M["tr_pub"].clip(lower=0.01)) - np.log(M["tr_h2_23"].clip(lower=0.01))) / (
        noise.reindex(M.index) * np.sqrt(1 / cnt["pub"].reindex(M.index) + 1 / cnt["h2_23"].reindex(M.index)))
    M["tr_change_class_pub"] = np.select([zc > 2, zc < -2], ["improved", "declined"], "stable")
    M.loc[zc.isna(), "tr_change_class_pub"] = ""
    M = M.reset_index(names="uid")
    hmeta = hm.drop_duplicates("k3")[["k1", "k2", "k3", "name"]].assign(unit_type="hromada", uid=lambda d: d["k3"])
    rmeta = rm.drop_duplicates("k2")[["unit_type", "k1", "k2", "k3", "name", "n_hromadas"]].assign(
        uid=lambda d: "R" + d["k2"])
    tm = M.merge(pd.concat([hmeta, rmeta], ignore_index=True), on="uid", how="left", validate="1:1")
    mcols = [c for c in M.columns if c.startswith("tr_")]
    write("hromada_trajectory_metrics.csv", tm[tm["unit_type"] == "hromada"], tm[tm["unit_type"] == "raion_r3"],
          ["n_hromadas"] + mcols)

    # ---------------- geometry
    gh = zf(gpd.read_file(BASE / "units_hromada.gpkg", layer="hromada"))[["k3", "geometry"]]
    gh = gh.merge(u[["k1", "k2", "k3", "name", "occupied", "r3"]], on="k3", how="inner", validate="1:1")
    g1 = gh[~gh["r3"]].assign(unit_type="hromada", n_hromadas=1)
    g2 = gh[gh["r3"]].dissolve(by="k2", as_index=False, aggfunc={"k3": "count"}).rename(columns={"k3": "n_hromadas"})
    g2 = g2.merge(rn, on="k2", how="left").assign(unit_type="raion_r3", k3="", occupied=0)
    units = gpd.GeoDataFrame(pd.concat([g1, g2], ignore_index=True)[ID + ["n_hromadas", "occupied", "geometry"]],
                             geometry="geometry", crs=gh.crs)
    units.to_file(GEO / "hromadas.gpkg", layer="units", driver="GPKG", engine="pyogrio")
    fz = BASE / "frontline_zone.gpkg"
    if fz.exists():
        gpd.read_file(fz, layer="lines").to_crs(gh.crs).to_file(GEO / "hromadas.gpkg", layer="frontline_border",
                                                                driver="GPKG", engine="pyogrio")
    obg = gpd.read_file(ROOT / "viina/qgis/admin_units.gpkg", layer="oblast")[["k1", "name", "geometry"]].to_crs(gh.crs)
    obg.to_file(GEO / "oblasts.gpkg", layer="oblasts", driver="GPKG", engine="pyogrio")
    print(f"\ngeo: hromadas.gpkg units {len(units):,} ({len(g2)} raion_r3), frontline_border; oblasts.gpkg {len(obg)}")

    # ---------------- checks
    print("\nchecks:")
    bad = []
    for f in sorted(TAB.glob("*.csv")):
        t = pd.read_csv(f, dtype=str)
        r4 = [c for c in t.columns if any(b in c.lower() for b in R4_BAD)]
        leak = t["k3"].isin(r3k3).sum() if "k3" in t else 0
        if r4 or leak:
            bad.append(f"{f.name}: R4 columns {r4}, R3 hromadas {leak}")
    mh = pd.read_csv(TAB / "hromada_nightlight_monthly.csv", dtype=str)
    late = (mh["date"] > PUB_END).sum()
    unrel = (~mh.loc[mh["unit_type"] == "hromada", "k3"].isin(rel)).sum()
    print(f"  R2: hromada light rows after {PUB_END}: {late}; unreliable hromadas: {unrel}")
    print(f"  R3/R4: {'; '.join(bad) if bad else 'no R4 columns, no hromada of a touched raion in any table'}")
    assert not bad and late == 0 and unrel == 0, "security checks failed"
    print(f"\nwrote {OUT.relative_to(ROOT)}/data/")


if __name__ == "__main__":
    main()
