#!/usr/bin/env python3
"""
12_moderation.py — robustness of "capacity buffers the effect of exposure on recovery"

  python 12_moderation.py                         main run -> tidy/moderation_results.csv
  python 12_moderation.py --cap COL --tag NAME    variant  -> tidy/moderation_results_NAME.csv
  options: --cap COL            capacity column from resilience_index_v11_k3.csv (default capacity_index)
           --outcome annual|winter  outcome from one light ratio only (log, p2/p98 winsorised,
                                percentile rank among non-occupied, as in 11); default index
           --drop-garrison      exclude hromadas with garrison_flag == 1
           --drop-k1 14,23,...  exclude oblasts (k1 codes)
           --tag NAME           required with any option; names the output and log files

Outcome  z(recovery_index)                      (lit-pixel night-light recovery, 04 v1.1)
Exposure z(log1p strikes since 2022)  |  alt: z(alert hours, 12 m)
Capacity z(capacity_index) (2025)     |  alt: pre-war capacity 2021 (own revenue pc, transfer
                                          dependency) — avoids reverse influence of the war
Models (all standardised, HC1 robust SE):
  M1 baseline                      M2 + oblast fixed effects
  M3 M2 + controls (log pop 2020, log lit pixels, log 2021 lit radiance)
  M4 M3 with alert hours as exposure
  M5 M3 with pre-war (2021) capacity (unchanged by --cap)
  M6 M3 without frontline oblasts (Donetsk 14, Zaporizhzhia 23, Kherson 65)
  M7 spatial lag (S2SLS, instruments WX, W2X) on the M3 specification
Robust inference for capacity and interaction in M1-M6 (robust_inference.py): restricted wild-cluster
  bootstrap p-values by oblast (Webb weights, B = 9,999; t with CR1 SE) and Conley spatial-HAC t-values
  (Bartlett kernel, 50 and 100 km, representative points in UA_LAEA metres). Main run only: 95 % interval
  for the interaction by inverting the wild-cluster test (ci_lo/ci_hi_interaction).
Within-R2 for fixed-effects models: 1 - SSR / sum of squares of y around its oblast mean.
Spatial weights: KNN k=6 on polygon centroids, row-standardised; Moran's I of residuals
  (999 permutations) for M1-M6.
Output: tidy/moderation_results[_TAG].csv (incl. se/t of the capacity main effect and the robust inference),
  logs/12_moderation[_TAG].log
Caveat: cross-sectional and descriptive; the interaction is an association, not a causal effect.
"""
import argparse
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

from robust_inference import conley_t, wild_cluster_ci, wild_cluster_p

BASE = Path(__file__).resolve().parent
TIDY, LOGS = BASE / "tidy", BASE / "logs"
UNITS = BASE / "units_hromada.gpkg"
FRONTLINE = {"14", "23", "65"}
K = 6
B_BOOT = 9999
CUTOFFS = (50_000, 100_000)
OUTCOME_SRC = {"annual": "ntl_recovery_2124", "winter": "ntl_winter_ratio_2125"}
_logf = None
pd.set_option("display.width", 200)


def log(*a):
    m = " ".join(str(x) for x in a)
    print(m, flush=True)
    _logf.write(m + "\n")
    _logf.flush()


def z(x):
    x = pd.to_numeric(x, errors="coerce")
    return (x - x.mean()) / x.std(ddof=0)


def rk(x):
    return pd.to_numeric(x, errors="coerce").rank(pct=True)


def ols_hc1(y, X):
    Xv, yv = X.values.astype(float), y.values.astype(float)
    XtX_inv = np.linalg.pinv(Xv.T @ Xv)
    b = XtX_inv @ Xv.T @ yv
    e = yv - Xv @ b
    n, k = Xv.shape
    meat = (Xv * e[:, None] ** 2).T @ Xv
    V = XtX_inv @ meat @ XtX_inv * n / (n - k)
    r2 = 1 - (e @ e) / ((yv - yv.mean()) @ (yv - yv.mean()))
    return pd.Series(b, X.columns), pd.Series(np.sqrt(np.diag(V)), X.columns), e, r2


def knn_w(gdf, k=K):
    from libpysal.weights import KNN
    pts = gdf.geometry.representative_point()
    w = KNN.from_array(np.column_stack([pts.x, pts.y]), k=k)
    w.transform = "r"
    return w


def moran(e, w):
    try:
        from esda.moran import Moran
        m = Moran(e, w, permutations=999)
        return m.I, m.p_sim
    except Exception as ex:
        log(f"  Moran failed: {ex}")
        return np.nan, np.nan


def s2sls_lag(y, X, lag_cols, w):
    """Spatial lag y = rho*Wy + Xb; instruments X, WX, W2X for the continuous lag_cols."""
    W = w.sparse
    yv, Xv = y.values.astype(float), X.values.astype(float)
    Wy = W @ yv
    WX = W @ X[lag_cols].values.astype(float)
    W2X = W @ WX
    H = np.column_stack([Xv, WX, W2X])
    Zs = np.column_stack([Wy, Xv])
    P = H @ np.linalg.pinv(H.T @ H) @ H.T
    A = np.linalg.pinv(Zs.T @ P @ Zs)
    b = A @ Zs.T @ P @ yv
    e = yv - Zs @ b
    s2 = e @ e / len(yv)
    se = np.sqrt(np.diag(s2 * A))
    names = ["rho_Wy"] + list(X.columns)
    return pd.Series(b, names), pd.Series(se, names)


def parse():
    ap = argparse.ArgumentParser(description="capacity x exposure moderation models")
    ap.add_argument("--cap", default="capacity_index")
    ap.add_argument("--outcome", choices=["index", "annual", "winter"], default="index")
    ap.add_argument("--drop-garrison", action="store_true")
    ap.add_argument("--drop-k1", default="")
    ap.add_argument("--tag", default="")
    a = ap.parse_args()
    a.drop_k1 = {k.strip().zfill(2) for k in a.drop_k1.split(",") if k.strip()}
    variant = a.cap != "capacity_index" or a.outcome != "index" or a.drop_garrison or a.drop_k1
    if variant and not a.tag:
        ap.error("--tag is required with --cap, --outcome, --drop-garrison or --drop-k1")
    return a


def main():
    global _logf
    a = parse()
    sfx = f"_{a.tag}" if a.tag else ""
    _logf = open(LOGS / f"12_moderation{sfx}.log", "w", encoding="utf-8")
    if a.tag:
        log(f"variant '{a.tag}': cap={a.cap}  outcome={a.outcome}  drop_garrison={a.drop_garrison}  "
            f"drop_k1={sorted(a.drop_k1)}")

    idx = pd.read_csv(TIDY / "resilience_index_v11_k3.csv", dtype={"k1": str, "k2": str, "k3": str})
    base = pd.read_csv(TIDY / "resilience_v1_k3.csv", dtype={"k1": str, "k2": str, "k3": str})
    for t in (idx, base):
        t["k3"] = t["k3"].str.zfill(7)
    assert a.cap in idx, f"capacity column {a.cap} not in resilience_index_v11_k3.csv"
    extra = [c for c in ("pop_ghs_2020", "ntl_n_lit_px", "ntl_2021") + tuple(OUTCOME_SRC.values()) if c in base]
    d = idx.merge(base[["k3"] + extra], on="k3", how="left")

    # outcome
    if a.outcome == "index":
        ycol = "recovery_index"
    else:
        v = pd.to_numeric(d[OUTCOME_SRC[a.outcome]], errors="coerce")
        v = np.log(v.where(v > 0))
        v = v.clip(v.quantile(0.02), v.quantile(0.98))
        d["y_single"] = v.rank(pct=True)
        ycol = "y_single"
        log(f"outcome from {OUTCOME_SRC[a.outcome]} only: n={d[ycol].notna().sum()}  "
            f"Spearman with recovery_index = {d[ycol].corr(d['recovery_index'], method='spearman'):.2f}")

    # pre-war capacity from 2021 budgets
    lp = TIDY / "budget_long_k3_year.csv"
    if lp.exists():
        L = pd.read_csv(lp, dtype={"k3": str})
        L["k3"] = L["k3"].str.zfill(7)
        b21 = L[L["year"] == 2021].drop_duplicates("k3").set_index("k3")
        pop = d.set_index("k3")["pop_ghs_2020"].where(lambda s: s >= 100)
        own21 = np.log((b21["own_gf"] / pop.reindex(b21.index)).where(lambda s: s > 0))
        tdep21 = -(b21["transfers"] / b21["rev_total"].where(b21["rev_total"] > 0))
        pre = pd.concat([rk(own21), rk(tdep21)], axis=1).mean(axis=1)
        d["capacity_prewar"] = d["k3"].map(pre)
        log(f"pre-war capacity (2021 own revenue pc, transfer dependency): n={d['capacity_prewar'].notna().sum()}  "
            f"Spearman with capacity_index 2025 = "
            f"{d['capacity_prewar'].corr(d['capacity_index'], method='spearman'):.2f}")
    if a.cap != "capacity_index":
        log(f"capacity column {a.cap}: n={d[a.cap].notna().sum()}  Spearman with capacity_index = "
            f"{d[a.cap].corr(d['capacity_index'], method='spearman'):.2f}")

    g = gpd.read_file(UNITS, layer="hromada")[["k3", "geometry"]]
    g["k3"] = g["k3"].astype(str).str.zfill(7)
    d = g.merge(d, on="k3", how="inner")

    if a.drop_garrison:
        gf = pd.to_numeric(d["garrison_flag"], errors="coerce") == 1
        log(f"dropping {int(gf.sum())} garrison hromadas")
        d = d[~gf]
    if a.drop_k1:
        dk = d["k1"].str.zfill(2).isin(a.drop_k1)
        log(f"dropping {int(dk.sum())} hromadas in oblasts {sorted(a.drop_k1)}")
        d = d[~dk]

    need = [ycol, a.cap, "exp_strikes_log"]
    s = d.dropna(subset=need).copy().reset_index(drop=True)
    log(f"analysis sample: {len(s)} non-occupied hromadas with recovery, capacity and exposure")

    s["y"] = z(s[ycol])
    s["exp"] = z(s["exp_strikes_log"])
    s["cap"] = z(s[a.cap])
    s["int"] = s["exp"] * s["cap"]
    ctrl = []
    if "pop_ghs_2020" in s:
        s["c_logpop"] = z(np.log(s["pop_ghs_2020"].clip(lower=1)))
        ctrl.append("c_logpop")
    if "ntl_n_lit_px" in s:
        s["c_loglit"] = z(np.log1p(s["ntl_n_lit_px"]))
        ctrl.append("c_loglit")
    if "ntl_2021" in s:
        s["c_rad21"] = z(np.log(s["ntl_2021"].clip(lower=0.01)))
        ctrl.append("c_rad21")
    s[ctrl] = s[ctrl].fillna(0)
    fe = pd.get_dummies(s["k1"], prefix="ob", drop_first=True, dtype=float)
    s = pd.concat([s, fe], axis=1)
    fe_cols = list(fe.columns)
    w = knn_w(s)

    results = []

    def run(name, data, cols, note=""):
        X = data[cols].copy()
        X.insert(0, "const", 1.0)
        ok = X.notna().all(axis=1) & data["y"].notna()
        b, se, e, r2 = ols_hc1(data.loc[ok, "y"], X[ok])
        wi = knn_w(data[ok]) if ok.sum() < len(data) or data is not s else w
        I, p = moran(e, wi)
        focus = [c for c in cols if c in ("exp", "cap", "int", "exp_alert", "cap_pre", "int_alert", "int_pre")]
        yo = data.loc[ok, "y"].astype(float).values
        grp = data.loc[ok, "k1"].astype(str).values
        r2w = np.nan
        if any(c.startswith("ob_") for c in cols):
            yd = yo - pd.Series(yo).groupby(grp).transform("mean").values
            r2w = 1 - (e @ e) / (yd @ yd)
        log(f"\n{name}  n={ok.sum()}  R2={r2:.3f}  within-R2={r2w:.3f}  Moran's I(resid)={I:.3f} (p={p:.3f})  {note}")
        for c in focus:
            log(f"    {c:10s} b={b[c]:+.3f}  se={se[c]:.3f}  t={b[c] / se[c]:+.2f}")
        ic = [c for c in focus if c.startswith("int")][0]
        cc = focus[1]
        # robust inference for capacity and interaction
        Xo = X[ok].astype(float)
        jc, ji = Xo.columns.get_loc(cc), Xo.columns.get_loc(ic)
        wb = wild_cluster_p(yo, Xo.values, [jc, ji], grp, B=B_BOOT)
        pts = data.loc[ok].geometry.representative_point()
        ct = conley_t(yo, Xo.values, [jc, ji], np.column_stack([pts.x.values, pts.y.values]), CUTOFFS)
        c50, c100 = ct[CUTOFFS[0]], ct[CUTOFFS[1]]
        lo = hi = np.nan
        if not a.tag:
            lo, hi = wild_cluster_ci(yo, Xo.values, ji, grp, B=B_BOOT)
        log(f"    robust     {cc}: CR1 t={wb[jc][0]:+.2f}  WCB p={wb[jc][1]:.3f}  Conley t50={c50[jc]:+.2f} "
            f"t100={c100[jc]:+.2f} | {ic}: CR1 t={wb[ji][0]:+.2f}  WCB p={wb[ji][1]:.3f}  "
            f"Conley t50={c50[ji]:+.2f} t100={c100[ji]:+.2f}  WCB 95% [{lo:+.3f}, {hi:+.3f}]")
        results.append({"model": name, "n": int(ok.sum()), "r2": r2, "moran_I": I, "moran_p": p,
                        "b_exposure": b[focus[0]], "b_capacity": b[cc], "b_interaction": b[ic],
                        "se_interaction": se[ic], "t_interaction": b[ic] / se[ic], "note": note,
                        "se_capacity": se[cc], "t_capacity": b[cc] / se[cc],
                        "t_cr1_capacity": wb[jc][0], "p_wcb_capacity": wb[jc][1],
                        "t_conley50_capacity": c50[jc], "t_conley100_capacity": c100[jc],
                        "t_cr1_interaction": wb[ji][0], "p_wcb_interaction": wb[ji][1],
                        "t_conley50_interaction": c50[ji], "t_conley100_interaction": c100[ji],
                        "r2_within": r2w, "ci_lo_interaction": lo, "ci_hi_interaction": hi})

    run("M1 baseline", s, ["exp", "cap", "int"])
    run("M2 + oblast FE", s, ["exp", "cap", "int"] + fe_cols)
    run("M3 + FE + controls", s, ["exp", "cap", "int"] + ctrl + fe_cols, "controls: " + ", ".join(ctrl))

    if "alert_h_12m" in s and s["alert_h_12m"].notna().sum() > 50:
        s["exp_alert"] = z(s["alert_h_12m"])
        s["int_alert"] = s["exp_alert"] * s["cap"]
        sub = s.dropna(subset=["exp_alert"])
        run("M4 alert hours", sub, ["exp_alert", "cap", "int_alert"] + ctrl + fe_cols, "exposure = alert hours 12 m")

    if "capacity_prewar" in s and s["capacity_prewar"].notna().sum() > 50:
        s["cap_pre"] = z(s["capacity_prewar"])
        s["int_pre"] = s["exp"] * s["cap_pre"]
        sub = s.dropna(subset=["cap_pre"])
        run("M5 pre-war capacity", sub, ["exp", "cap_pre", "int_pre"] + ctrl + fe_cols, "capacity from 2021 budgets")

    sub = s[~s["k1"].isin(FRONTLINE)]
    fe_sub = [c for c in fe_cols if sub[c].sum() > 0]
    run("M6 without frontline oblasts", sub, ["exp", "cap", "int"] + ctrl + fe_sub,
        f"dropped k1 {sorted(FRONTLINE)}")

    X = s[["exp", "cap", "int"] + ctrl + fe_cols].copy()
    X.insert(0, "const", 1.0)
    b, se = s2sls_lag(s["y"], X, ["exp", "cap", "int"] + ctrl, w)
    log(f"\nM7 spatial lag (S2SLS, KNN {K})  n={len(s)}")
    for c in ("rho_Wy", "exp", "cap", "int"):
        log(f"    {c:10s} b={b[c]:+.3f}  se={se[c]:.3f}  t={b[c] / se[c]:+.2f}")
    results.append({"model": "M7 spatial lag", "n": len(s), "r2": np.nan, "moran_I": np.nan, "moran_p": np.nan,
                    "b_exposure": b["exp"], "b_capacity": b["cap"], "b_interaction": b["int"],
                    "se_interaction": se["int"], "t_interaction": b["int"] / se["int"],
                    "note": f"rho={b['rho_Wy']:.3f}", "se_capacity": se["cap"], "t_capacity": b["cap"] / se["cap"]})

    # tercile tables -------------------------------------------------------------
    def terciles(col, label):
        t = pd.qcut(s["exp_strikes_log"].rank(method="first"), 3, labels=["low", "mid", "high"])
        c = pd.qcut(s[col].rank(method="first"), 3, labels=["low", "mid", "high"])
        tab = s.assign(exposure=t, capacity=c).pivot_table(index="exposure", columns="capacity",
                                                           values=ycol, aggfunc="median", observed=False)
        cnt = s.assign(exposure=t, capacity=c).pivot_table(index="exposure", columns="capacity",
                                                           values=ycol, aggfunc="count", observed=False)
        log(f"\nmedian recovery by exposure (rows) x {label} (cols)  [n per cell]\n"
            + tab.round(3).astype(str).add(" [").add(cnt.astype(int).astype(str)).add("]").to_string())

    terciles(a.cap, "capacity 2025" if a.cap == "capacity_index" else a.cap)
    if "cap_pre" in s:
        terciles("capacity_prewar", "pre-war capacity 2021")

    r = pd.DataFrame(results)
    if a.tag:
        r["variant"] = a.tag
        r["cap_col"] = a.cap
        r["outcome"] = a.outcome
        r["dropped"] = ";".join(filter(None, ["garrison" if a.drop_garrison else "",
                                              ",".join(sorted(a.drop_k1))]))
    out = TIDY / f"moderation_results{sfx}.csv"
    r.to_csv(out, index=False)
    log("\nsummary (interaction term):\n" + r[["model", "n", "b_exposure", "b_capacity", "b_interaction",
                                              "t_interaction", "moran_I", "note"]].round(3).to_string(index=False))
    log(f"\nwrote {out.relative_to(BASE)}")


if __name__ == "__main__":
    main()
