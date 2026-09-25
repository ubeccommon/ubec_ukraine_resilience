#!/usr/bin/env python3
"""
12_moderation.py — robustness of "capacity buffers the effect of exposure on recovery"

  python 12_moderation.py

Outcome  z(recovery_index)                      (lit-pixel night-light recovery, 04 v1.1)
Exposure z(log1p strikes since 2022)  |  alt: z(alert hours, 12 m)
Capacity z(capacity_index) (2025)     |  alt: pre-war capacity 2021 (own revenue pc, transfer
                                          dependency) — avoids reverse influence of the war
Models (all standardised, HC1 robust SE):
  M1 baseline                      M2 + oblast fixed effects
  M3 M2 + controls (log pop 2020, log lit pixels, log 2021 lit radiance)
  M4 M3 with alert hours as exposure
  M5 M3 with pre-war (2021) capacity
  M6 M3 without frontline oblasts (Donetsk 14, Zaporizhzhia 23, Kherson 65)
  M7 spatial lag (S2SLS, instruments WX, W2X) on the M3 specification
Spatial weights: KNN k=6 on polygon centroids, row-standardised; Moran's I of residuals
  (999 permutations) for M1-M6.
Output: tidy/moderation_results.csv, logs/12_moderation.log
Caveat: cross-sectional and descriptive; the interaction is an association, not a causal effect.
"""
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
TIDY, LOGS = BASE / "tidy", BASE / "logs"
UNITS = BASE / "units_hromada.gpkg"
FRONTLINE = {"14", "23", "65"}
K = 6
_logf = open(LOGS / "12_moderation.log", "w", encoding="utf-8")
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


def main():
    idx = pd.read_csv(TIDY / "resilience_index_v11_k3.csv", dtype={"k1": str, "k2": str, "k3": str})
    base = pd.read_csv(TIDY / "resilience_v1_k3.csv", dtype={"k1": str, "k2": str, "k3": str})
    for t in (idx, base):
        t["k3"] = t["k3"].str.zfill(7)
    extra = [c for c in ("pop_ghs_2020", "ntl_n_lit_px", "ntl_2021") if c in base]
    d = idx.merge(base[["k3"] + extra], on="k3", how="left")

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

    g = gpd.read_file(UNITS, layer="hromada")[["k3", "geometry"]]
    g["k3"] = g["k3"].astype(str).str.zfill(7)
    d = g.merge(d, on="k3", how="inner")

    need = ["recovery_index", "capacity_index", "exp_strikes_log"]
    s = d.dropna(subset=need).copy().reset_index(drop=True)
    log(f"analysis sample: {len(s)} non-occupied hromadas with recovery, capacity and exposure")

    s["y"] = z(s["recovery_index"])
    s["exp"] = z(s["exp_strikes_log"])
    s["cap"] = z(s["capacity_index"])
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
        log(f"\n{name}  n={ok.sum()}  R2={r2:.3f}  Moran's I(resid)={I:.3f} (p={p:.3f})  {note}")
        for c in focus:
            log(f"    {c:10s} b={b[c]:+.3f}  se={se[c]:.3f}  t={b[c] / se[c]:+.2f}")
        ic = [c for c in focus if c.startswith("int")][0]
        results.append({"model": name, "n": int(ok.sum()), "r2": r2, "moran_I": I, "moran_p": p,
                        "b_exposure": b[focus[0]], "b_capacity": b[focus[1]], "b_interaction": b[ic],
                        "se_interaction": se[ic], "t_interaction": b[ic] / se[ic], "note": note})

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
                    "note": f"rho={b['rho_Wy']:.3f}"})

    # tercile tables -------------------------------------------------------------
    def terciles(col, label):
        t = pd.qcut(s["exp_strikes_log"].rank(method="first"), 3, labels=["low", "mid", "high"])
        c = pd.qcut(s[col].rank(method="first"), 3, labels=["low", "mid", "high"])
        tab = s.assign(exposure=t, capacity=c).pivot_table(index="exposure", columns="capacity",
                                                           values="recovery_index", aggfunc="median", observed=False)
        cnt = s.assign(exposure=t, capacity=c).pivot_table(index="exposure", columns="capacity",
                                                           values="recovery_index", aggfunc="count", observed=False)
        log(f"\nmedian recovery by exposure (rows) x {label} (cols)  [n per cell]\n"
            + tab.round(3).astype(str).add(" [").add(cnt.astype(int).astype(str)).add("]").to_string())

    terciles("capacity_index", "capacity 2025")
    if "cap_pre" in s:
        terciles("capacity_prewar", "pre-war capacity 2021")

    r = pd.DataFrame(results)
    r.to_csv(TIDY / "moderation_results.csv", index=False)
    log("\nsummary (interaction term):\n" + r[["model", "n", "b_exposure", "b_capacity", "b_interaction",
                                              "t_interaction", "moran_I", "note"]].round(3).to_string(index=False))
    log("\nwrote tidy/moderation_results.csv")


if __name__ == "__main__":
    main()
