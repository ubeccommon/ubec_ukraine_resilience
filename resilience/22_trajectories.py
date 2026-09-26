#!/usr/bin/env python3
"""
22_trajectories.py — recovery trajectories per hromada (night lights monthly/quarterly,
budgets quarterly) and their relation to capacity and exposure.

  python 22_trajectories.py

Inputs: tidy/nightlights_panel_k3.csv, nightlights_noise_k3.csv (19); budget_quarterly_k3.csv
(20); resilience_index_v11_k3.csv (11); resilience_v1_k3.csv; budget_long_k3_year.csv (2021).
Night lights: ntl_idx = lit radiance / mean same month 2020–21. June 2025 excluded (artifact).
  Windows need >= half their months valid; quarters >= 2 valid months.
  Sample: non-occupied, >= 10 lit pixels, noise_sd available. Change class: recent vs H2 2023,
  z = dlog / (noise_sd * sqrt(1/n1 + 1/n2)), |z| > 2.
Budgets: _rel = ratio to same quarter 2021 / national median (inflation-neutral).
Models as 12: z(y) ~ exposure + capacity + interaction [+ oblast FE] [+ controls, NaN -> 0];
  HC1 SEs; M3w weights 1/noise_sd^2; budget outcomes use pre-war (2021) capacity only
  (2025 capacity contains 2025 own revenue and PIT growth — circular).
  Robust inference (robust_inference.py) for exposure, capacity and interaction in every model:
  restricted wild-cluster bootstrap p-values by oblast (p_wcb_*, Webb weights, B = 9,999) and Conley
  spatial-HAC t-values (t_c50_*, t_c100_*: Bartlett kernel, 50 / 100 km, centroids in UA_LAEA).
Publication rule R2 (maps 19–20): hromada light values shown only for a window ending at PUB_END (at least six
  months before release) and only where the light data are reliable: >= 30 lit pixels and pre-war noise_sd
  <= 0.35 (tr_light_reliable, as 23_carpathian.py). Fields *_pub hold the publication classes; the models and
  the current-window classes are unchanged.
Map classes (maps 19–20, build_qgis_project.py):
  bv_rec_cap  light-deficit tercile (1 = brightest third, 3 = darkest third of tr_recent, sample)
              x capacity tercile (non-occupied, as 13_bivariate); "na" no light metric, "occ" occupied
  s24_q       quintiles of tr_s24_rel (1 = largest loss); chg_cls improved/stable/declined/na/occ
  *_pub       the same on the publication window and the reliable hromadas only (terciles / quintiles among
              those); used by the map pages
Outputs: tidy/trajectories_k3.csv, tidy/ntl_quarterly_k3.csv, tidy/trajectory_models.csv,
  tidy/trajectory_classes.json (cut points, change shares, publication window for captions),
  resilience_maps.gpkg layer hromada_trajectories.
"""
import json
import time
from pathlib import Path
import numpy as np
import pandas as pd

from robust_inference import conley_t, wild_cluster_p

BASE = Path(__file__).resolve().parent
TIDY = BASE / "tidy"
UNITS = BASE / "units_hromada.gpkg"
MAPS = BASE / "resilience_maps.gpkg"
LAEA = "+proj=laea +lat_0=48.5 +lon_0=31 +ellps=GRS80 +units=m"
CARP = {"21", "26", "46", "73"}
EXCL = {"2025-06"}
MIN_LIT = 10
B_BOOT = 9999
CUTOFFS = (50_000, 100_000)
PUB_END = "2026-03"            # last month shown on published hromada light maps (R2: >= 6 months before release)
REL_NLIT, REL_NOISE = 30, 0.35  # reliability rule for single-hromada light values (R2, as 23_carpathian.py)


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def z(s):
    s = pd.Series(s, dtype=float)
    return (s - s.mean()) / s.std()


def k(df, col="k3", n=7):
    df[col] = df[col].astype(str).str.zfill(n)
    return df


def slope_by(df, key, t, v, min_n):
    out = {}
    for kk, g in df.dropna(subset=[v]).groupby(key):
        if len(g) >= min_n:
            out[kk] = np.polyfit(g[t].values, g[v].values, 1)[0]
    return pd.Series(out, dtype=float)


def nq(s, n):
    """n-quantile classes '1'..'n' by rank (ties broken by order, as 13_bivariate)."""
    s = pd.to_numeric(s, errors="coerce")
    out = pd.Series(pd.NA, index=s.index, dtype="object")
    ok = s.notna()
    if ok.sum() >= n:
        out[ok] = pd.qcut(s[ok].rank(method="first"), n,
                          labels=[str(i) for i in range(1, n + 1)]).astype(str)
    return out


def ols(y, X, w=None):
    X = np.column_stack([np.ones(len(y)), np.asarray(X, float)])
    y = np.asarray(y, float)
    w = np.ones(len(y)) if w is None else np.asarray(w, float) / np.mean(w)
    sw = np.sqrt(w)
    Xw, yw = X * sw[:, None], y * sw
    b = np.linalg.lstsq(Xw, yw, rcond=None)[0]
    e = yw - Xw @ b
    n, kk = Xw.shape
    bread = np.linalg.pinv(Xw.T @ Xw)
    V = bread @ ((Xw * (e ** 2)[:, None]).T @ Xw) @ bread * n / (n - kk)
    ybar = np.sum(w * y) / np.sum(w)
    r2 = 1 - np.sum(e ** 2) / np.sum(w * (y - ybar) ** 2)
    return b[1:], np.sqrt(np.diag(V))[1:], r2, n, e / sw


def main():
    # ---------------- units
    base = k(pd.read_csv(TIDY / "resilience_v1_k3.csv", dtype={"k1": str, "k3": str}))
    base["k1"] = base["k3"].str[:2]
    idx = k(pd.read_csv(TIDY / "resilience_index_v11_k3.csv", dtype={"k3": str}))
    u = base[["k1", "k3", "name", "occupied", "pop_ghs_2020", "ntl_n_lit_px", "ntl_2021"]].merge(
        idx[["k3", "capacity_index", "recovery_index", "exp_strikes_log", "alert_h_12m",
             "garrison_flag"]], on="k3", how="left")
    u["occupied"] = pd.to_numeric(u["occupied"], errors="coerce").fillna(0).astype(int)
    L = k(pd.read_csv(TIDY / "budget_long_k3_year.csv", dtype={"k3": str}))
    b21 = L[L["year"] == 2021].drop_duplicates("k3").set_index("k3")
    pop = u.set_index("k3")["pop_ghs_2020"].where(lambda s: s >= 100)
    own21 = np.log((b21["own_gf"] / pop.reindex(b21.index)).where(lambda s: s > 0))
    tdep21 = -(b21["transfers"] / b21["rev_total"].where(b21["rev_total"] > 0))
    u["capacity_prewar"] = u["k3"].map(pd.concat([own21.rank(pct=True), tdep21.rank(pct=True)],
                                                  axis=1).mean(axis=1))

    # ---------------- night lights
    p = k(pd.read_csv(TIDY / "nightlights_panel_k3.csv", dtype={"k3": str},
                      usecols=["k3", "year", "month", "date", "ntl_idx"]))
    p = p[~p["date"].isin(EXCL) & p["ntl_idx"].notna()]
    last = pd.Period(p["date"].max(), freq="M")
    pub = pd.Period(PUB_END, freq="M")
    assert pub <= last, f"PUB_END {PUB_END} lies after the last panel month {last}"
    W = {"w2223": ("2022-11", "2023-02"), "h2_23": ("2023-07", "2023-12"),
         "s24": ("2024-06", "2024-07"), "w2425": ("2024-12", "2025-02"),
         "recent": (str(last - 11), str(last)),
         "recent_pub": (str(pub - 11), str(pub))}
    T = u.copy()
    nwin = {}
    for name, (a, b) in W.items():
        ms = [str(x) for x in pd.period_range(a, b, freq="M") if str(x) not in EXCL]
        g = p[p["date"].isin(ms)].groupby("k3")["ntl_idx"].agg(["mean", "count"])
        need = max(1, int(np.ceil(len(ms) / 2)))
        T[f"tr_{name}"] = T["k3"].map(g["mean"].where(g["count"] >= need))
        nwin[name] = T["k3"].map(g["count"])
    log(f"windows: {W}")

    p["q"] = (p["month"] - 1) // 3 + 1
    qn = p.groupby(["k3", "year", "q"])["ntl_idx"].agg(ntl_q="mean", n_m="count").reset_index()
    qn.loc[qn["n_m"] < 2, "ntl_q"] = np.nan
    qn["t"] = qn["year"] + (qn["q"] - 1) / 4
    war = qn[(qn["t"] >= 2022.25) & qn["ntl_q"].notna()]
    tr = war.loc[war.groupby("k3")["ntl_q"].idxmin()].set_index("k3")
    T["tr_trough"] = T["k3"].map(tr["ntl_q"])
    T["tr_trough_q"] = T["k3"].map(tr["year"].astype(int).astype(str) + "Q" + tr["q"].astype(int).astype(str))
    T["tr_slope_2426"] = T["k3"].map(slope_by(qn[qn["t"] >= 2024], "k3", "t", "ntl_q", 8))
    T["tr_below50_share"] = T["k3"].map(war.assign(b=war["ntl_q"] < 0.5).groupby("k3")["b"].mean())
    T["tr_s24_rel"] = T["tr_s24"] / T["tr_h2_23"]
    T["tr_rebound"] = T["tr_recent"] / T["tr_trough"].where(T["tr_trough"] > 0.01)

    nz = k(pd.read_csv(TIDY / "nightlights_noise_k3.csv", dtype={"k3": str})).set_index("k3")
    T["tr_noise_sd"] = T["k3"].map(nz["noise_sd"])
    for sfx, win in (("", "recent"), ("_pub", "recent_pub")):
        dl = np.log(T[f"tr_{win}"].clip(lower=0.01)) - np.log(T["tr_h2_23"].clip(lower=0.01))
        T[f"tr_change_z{sfx}"] = dl / (T["tr_noise_sd"] * np.sqrt(1 / nwin[win] + 1 / nwin["h2_23"]))
        T[f"tr_change_class{sfx}"] = np.select([T[f"tr_change_z{sfx}"] > 2, T[f"tr_change_z{sfx}"] < -2],
                                               ["improved", "declined"], "stable")
        T.loc[T[f"tr_change_z{sfx}"].isna(), f"tr_change_class{sfx}"] = ""
    ntl_ok = (T["occupied"] == 0) & (T["ntl_n_lit_px"] >= MIN_LIT) & T["tr_noise_sd"].notna()
    for c in [c for c in T if c.startswith("tr_")]:
        T.loc[~ntl_ok, c] = np.nan if T[c].dtype.kind == "f" else ""
    T["tr_light_reliable"] = (ntl_ok & (T["ntl_n_lit_px"] >= REL_NLIT) & (T["tr_noise_sd"] <= REL_NOISE)).astype(int)

    # ---------------- budgets
    bq = k(pd.read_csv(TIDY / "budget_quarterly_k3.csv", dtype={"k3": str}))
    bq["t"] = bq["year"] + (bq["q"] - 1) / 4
    cnt = bq.groupby("t")["own_gf"].count()
    full = sorted(cnt[cnt >= 1000].index)
    rq = full[-4:]
    br = bq[bq["t"].isin(rq)].groupby("k3")[["own_gf_rel", "pdfo_civ_rel"]].mean()
    T["bt_own_recent"] = T["k3"].map(br["own_gf_rel"])
    T["bt_pit_recent"] = T["k3"].map(br["pdfo_civ_rel"])
    T["bt_pit_2022"] = T["k3"].map(bq[(bq["t"] >= 2022.25) & (bq["t"] < 2023)]
                                   .groupby("k3")["pdfo_civ_rel"].mean())
    bs = bq[(bq["t"] >= 2022.25) & (bq["t"] <= full[-1])].copy()
    bs["lp"] = np.log(bs["pdfo_civ_rel"].where(bs["pdfo_civ_rel"] > 0))
    T["bt_pit_slope"] = T["k3"].map(slope_by(bs, "k3", "t", "lp", 12))
    log(f"budget recent quarters: {rq}")

    # ---------------- map classes (maps 19–20)
    occ = T["occupied"] == 1
    cap_t = nq(T["capacity_index"].where(~occ), 3)
    dark_t = nq(-T["tr_recent"], 3)                      # 3 = darkest third (largest deficit)
    bv = (dark_t.astype("string") + cap_t.astype("string")).where(dark_t.notna() & cap_t.notna(), "na")
    bv[occ] = "occ"
    T["bv_rec_cap"] = bv.astype(str)
    s24q = nq(T["tr_s24_rel"], 5).fillna("na")
    s24q[occ] = "occ"
    T["s24_q"] = s24q.astype(str)
    chg = T["tr_change_class"].replace("", np.nan).fillna("na").astype(str)
    chg[occ] = "occ"
    T["chg_cls"] = chg
    # publication classes (R2): publication window, reliable hromadas only
    rel = T["tr_light_reliable"] == 1
    dark_tp = nq(-T["tr_recent_pub"].where(rel), 3)
    bvp = (dark_tp.astype("string") + cap_t.astype("string")).where(dark_tp.notna() & cap_t.notna(), "na")
    bvp[occ] = "occ"
    T["bv_rec_cap_pub"] = bvp.astype(str)
    s24qp = nq(T["tr_s24_rel"].where(rel), 5).fillna("na")
    s24qp[occ] = "occ"
    T["s24_q_pub"] = s24qp.astype(str)
    chgp = T["tr_change_class_pub"].where(rel).replace("", np.nan).fillna("na").astype(str)
    chgp[occ] = "occ"
    T["chg_cls_pub"] = chgp
    carp = T["k1"].isin(CARP)
    allu = pd.Series(True, index=T.index)
    classes = {
        "recent_window": f"{W['recent'][0]} – {W['recent'][1]}",
        "recent_terciles": T["tr_recent"].dropna().quantile([1 / 3, 2 / 3]).round(3).tolist(),
        "capacity_terciles": T.loc[~occ, "capacity_index"].dropna().quantile([1 / 3, 2 / 3]).round(3).tolist(),
        "s24_quintiles": T["tr_s24_rel"].dropna().quantile([.2, .4, .6, .8]).round(3).tolist(),
        "change_share": {grp: T.loc[m & ~occ, "tr_change_class"].replace("", np.nan).dropna()
                         .value_counts(normalize=True).round(3).to_dict()
                         for grp, m in (("national", allu), ("carpathian", carp))},
        "n_light": int(ntl_ok.sum()),
        "pub_end": PUB_END,
        "pub_window": f"{W['recent_pub'][0]} – {W['recent_pub'][1]}",
        "pub_rule": f">= {REL_NLIT} lit pixels and pre-war noise_sd <= {REL_NOISE}",
        "n_light_reliable": int(rel.sum()),
        "recent_terciles_pub": T.loc[rel, "tr_recent_pub"].dropna().quantile([1 / 3, 2 / 3]).round(3).tolist(),
        "s24_quintiles_pub": T.loc[rel, "tr_s24_rel"].dropna().quantile([.2, .4, .6, .8]).round(3).tolist(),
        "change_share_pub": {grp: T.loc[m & ~occ & rel, "tr_change_class_pub"].replace("", np.nan).dropna()
                             .value_counts(normalize=True).round(3).to_dict()
                             for grp, m in (("national", allu), ("carpathian", carp))},
    }
    (TIDY / "trajectory_classes.json").write_text(json.dumps(classes, ensure_ascii=False, indent=1))
    log(f"map classes: bv_rec_cap {T.loc[~occ, 'bv_rec_cap'].value_counts().sort_index().to_dict()}")
    log(f"publication classes ({classes['pub_window']}, reliable n={classes['n_light_reliable']}): "
        f"bv_rec_cap_pub {T.loc[~occ, 'bv_rec_cap_pub'].value_counts().sort_index().to_dict()}  "
        f"chg_cls_pub {T.loc[~occ, 'chg_cls_pub'].value_counts().sort_index().to_dict()}")
    log(f"trajectory_classes.json: {classes}")

    qn.merge(bq[["k3", "year", "q", "own_gf_rel", "pdfo_civ_rel"]], on=["k3", "year", "q"],
             how="outer").to_csv(TIDY / "ntl_quarterly_k3.csv", index=False)
    T.to_csv(TIDY / "trajectories_k3.csv", index=False)
    log(f"wrote trajectories_k3.csv ({int(ntl_ok.sum())} units with night-light metrics, "
        f"{int(T['bt_pit_recent'].notna().sum())} with budget metrics), ntl_quarterly_k3.csv")

    # ---------------- descriptives
    no = T[T["occupied"] == 0].copy().reset_index(drop=True)
    no["carp"] = no["k1"].isin(CARP)
    mcols = ["tr_w2223", "tr_h2_23", "tr_s24", "tr_w2425", "tr_recent", "tr_trough", "tr_slope_2426",
             "tr_below50_share", "tr_s24_rel", "bt_own_recent", "bt_pit_recent", "bt_pit_2022", "bt_pit_slope"]
    desc = pd.DataFrame({"all": no[mcols].median(), "carpathian": no[no.carp][mcols].median(),
                         "rest": no[~no.carp][mcols].median()})
    print("\nmedians (non-occupied):\n" + desc.to_string(float_format=lambda v: f"{v:.3f}"))
    print("\ntrough timing (share of units):\n" +
          no["tr_trough_q"].replace("", np.nan).value_counts(normalize=True).head(6).round(3).to_string())
    cc = pd.crosstab(no["carp"].map({True: "carpathian", False: "rest"}),
                     no["tr_change_class"].replace("", np.nan), normalize="index").round(3)
    print("\nchange recent vs H2 2023 (|z|>2 against own noise):\n" + cc.to_string())
    xs = ["capacity_index", "capacity_prewar", "exp_strikes_log", "alert_h_12m", "recovery_index"]
    print("\nSpearman (non-occupied):\n" +
          no[mcols + xs].corr(method="spearman").loc[mcols, xs].round(2).to_string())

    # ---------------- models
    fe = pd.get_dummies(no["k1"], prefix="ob", drop_first=True, dtype=float)
    no = pd.concat([no, fe], axis=1)
    fec = list(fe.columns)
    no["c_logpop"] = z(np.log(no["pop_ghs_2020"].clip(lower=1)))
    no["c_loglit"] = z(np.log1p(no["ntl_n_lit_px"]))
    no["c_rad21"] = z(np.log(no["ntl_2021"].clip(lower=0.01)))
    ctrl = ["c_logpop", "c_loglit", "c_rad21"]
    no[ctrl] = no[ctrl].fillna(0)
    outcomes = {"log recent level": (np.log(no["tr_recent"].clip(lower=0.01)), True),
                "log trough": (np.log(no["tr_trough"].clip(lower=0.01)), True),
                "log summer-24 dip vs H2-23": (np.log(no["tr_s24_rel"].clip(lower=0.01)), True),
                "slope 2024-26": (no["tr_slope_2426"], True),
                "log civ PIT rel recent": (np.log(no["bt_pit_recent"].where(no["bt_pit_recent"] > 0)), False),
                "log civ PIT rel 2022": (np.log(no["bt_pit_2022"].where(no["bt_pit_2022"] > 0)), False)}
    xy = None
    try:
        import geopandas as gpd, libpysal, esda
        g = k(gpd.read_file(UNITS, layer="hromada")[["k3", "geometry"]]).to_crs(LAEA)
        cg = g.set_index("k3").geometry.centroid.reindex(no["k3"])
        xy = np.column_stack([cg.x.values, cg.y.values])
    except Exception as e:
        log(f"spatial check disabled ({e})")
    rows = []
    for oname, (yv, is_ntl) in outcomes.items():
        capv = "capacity_prewar" if not is_ntl else "capacity_index"
        specs = [("M1", "exp_strikes_log", capv, [], None), ("M2 FE", "exp_strikes_log", capv, fec, None),
                 ("M3 FE+ctrl", "exp_strikes_log", capv, ctrl + fec, None),
                 ("M4 alerts", "alert_h_12m", capv, ctrl + fec, None)]
        if is_ntl:
            specs.insert(3, ("M3w weighted", "exp_strikes_log", capv, ctrl + fec, "w"))
            specs.append(("M5 pre-war cap", "exp_strikes_log", "capacity_prewar", ctrl + fec, None))
        for sname, ev, cv, extra, wt in specs:
            ok = np.isfinite(yv) & no[ev].notna() & no[cv].notna()
            if wt:
                ok &= no["tr_noise_sd"].notna()
            s = no[ok]
            X = pd.DataFrame({"exp": z(s[ev]).values, "cap": z(s[cv]).values})
            X["int"] = X["exp"] * X["cap"]
            X = pd.concat([X, s[extra].reset_index(drop=True)], axis=1)
            X = X.loc[:, X.std() > 0]
            w = (1 / s["tr_noise_sd"].clip(lower=0.05) ** 2).values if wt else None
            yz = z(yv[ok]).values
            b, se, r2, n, e = ols(yz, X.values, w)
            r = {"outcome": oname, "spec": sname, "capacity": cv, "exposure": ev, "n": n, "r2": r2}
            for j, c in enumerate(["exp", "cap", "int"]):
                r[f"b_{c}"], r[f"t_{c}"] = b[j], b[j] / se[j]
            if xy is not None and sname == "M3 FE+ctrl":
                pts = xy[ok.values]
                good = np.isfinite(pts).all(axis=1)
                wk = libpysal.weights.KNN.from_array(pts[good], k=8)
                wk.transform = "r"
                r["moran_resid"] = esda.Moran(e[good], wk, permutations=0).I
            # robust inference: columns 1-3 of Xc are exp, cap, int
            Xc = np.column_stack([np.ones(len(X)), X.values.astype(float)])
            wb = wild_cluster_p(yz, Xc, [1, 2, 3], s["k1"].astype(str).values, w=w, B=B_BOOT)
            for j, c in zip([1, 2, 3], ["exp", "cap", "int"]):
                r[f"p_wcb_{c}"] = wb[j][1]
            if xy is not None:
                pts = xy[ok.values]
                if np.isfinite(pts).all():
                    ct = conley_t(yz, Xc, [1, 2, 3], pts, CUTOFFS, w=w)
                    for j, c in zip([1, 2, 3], ["exp", "cap", "int"]):
                        r[f"t_c50_{c}"], r[f"t_c100_{c}"] = ct[CUTOFFS[0]][j], ct[CUTOFFS[1]][j]
            rows.append(r)
    R = pd.DataFrame(rows)
    R.to_csv(TIDY / "trajectory_models.csv", index=False)
    print("\nmodels: z(outcome) ~ exposure + capacity + interaction (HC1 t in brackets; WCB p by oblast)")
    for oname, g2 in R.groupby("outcome", sort=False):
        print(f"\n{oname}  (capacity = {g2['capacity'].iloc[0]})")
        for _, r in g2.iterrows():
            mi = f"  I={r['moran_resid']:.2f}" if pd.notna(r.get("moran_resid")) else ""
            print(f"  {r['spec']:<15} n={r['n']:4d} R2={r['r2']:.2f}  exp {r['b_exp']:+.2f} [{r['t_exp']:+.1f}]"
                  f"  cap {r['b_cap']:+.2f} [{r['t_cap']:+.1f}] p={r['p_wcb_cap']:.3f}"
                  f"  int {r['b_int']:+.2f} [{r['t_int']:+.1f}] p={r['p_wcb_int']:.3f}{mi}")

    # ---------------- map layer + dictionary
    try:
        import geopandas as gpd
        g = k(gpd.read_file(UNITS, layer="hromada")[["k3", "geometry"]])
        keep = (["k1", "k3", "name", "occupied", "bv_rec_cap", "s24_q", "chg_cls",
                 "bv_rec_cap_pub", "s24_q_pub", "chg_cls_pub"]
                + [c for c in T if c.startswith(("tr_", "bt_"))])
        g.merge(T[keep], on="k3", how="left").to_file(MAPS, layer="hromada_trajectories",
                                                     driver="GPKG", engine="pyogrio")
        log("wrote resilience_maps.gpkg:hromada_trajectories")
    except Exception as e:
        log(f"map layer not written ({e})")
    dd_fn = TIDY / "data_dictionary.csv"
    src, lic = "derived: 19 (Black Marble VNP46A3) and 20 (openbudget)", "NASA public domain; CMU 835"
    new = pd.DataFrame(
        [(f"tr_{n}", src, lic, "ratio", f"{a}..{b}", "hromada",
          f"mean ntl_idx (radiance / same month 2020-21) over {a}..{b}, >= half months valid")
         for n, (a, b) in W.items()] +
        [("tr_trough", src, lic, "ratio", "2022Q2-", "hromada", "minimum quarterly ntl_idx since 2022Q2"),
         ("tr_slope_2426", src, lic, "ratio/yr", "2024-", "hromada", "OLS slope of quarterly ntl_idx, >= 8 quarters"),
         ("tr_below50_share", src, lic, "share", "2022Q2-", "hromada", "share of quarters with ntl_idx < 0.5"),
         ("tr_change_class", src, lic, "class", "", "hromada",
          "recent vs H2 2023, |dlog| > 2 x own pre-war noise (noise_sd 2021/2020)"),
         ("tr_change_class_pub", src, lic, "class", W["recent_pub"][0] + ".." + W["recent_pub"][1], "hromada",
          "publication window (ends PUB_END, rule R2) vs H2 2023, |dlog| > 2 x own pre-war noise"),
         ("tr_light_reliable", src, lic, "flag", "", "hromada",
          f"1 if >= {REL_NLIT} lit pixels and pre-war noise_sd <= {REL_NOISE} (single-hromada light values publishable, R2)"),
         ("bt_pit_recent", src, lic, "ratio", "last 4 q", "hromada", "mean pdfo_civ_rel, last 4 complete quarters"),
         ("bt_own_recent", src, lic, "ratio", "last 4 q", "hromada", "mean own_gf_rel, last 4 complete quarters"),
         ("bt_pit_2022", src, lic, "ratio", "2022Q2-Q4", "hromada", "mean pdfo_civ_rel 2022Q2-Q4 (relocation effect)"),
         ("bt_pit_slope", src, lic, "log/yr", "2022Q2-", "hromada", "slope of log pdfo_civ_rel, >= 12 quarters")],
        columns=["indicator", "source", "licence", "unit", "year", "level", "method"])
    dd = pd.read_csv(dd_fn)
    dd = dd[~dd["indicator"].astype(str).str.startswith(("tr_", "bt_"))]
    for col in dd.columns:
        if col not in new:
            new[col] = ""
    pd.concat([dd, new[dd.columns]], ignore_index=True).to_csv(dd_fn, index=False)
    vk = T[T["k3"] == "2602003"]
    if len(vk):
        print("\nVerkhovyna:\n" + vk[["name"] + mcols + ["tr_trough_q", "tr_change_class", "tr_noise_sd",
                                                          "bv_rec_cap", "s24_q"]].T.to_string(header=False))


if __name__ == "__main__":
    main()
