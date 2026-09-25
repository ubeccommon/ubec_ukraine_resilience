#!/usr/bin/env python3
"""
11_composite.py — resilience v1.1: three separate indices, non-occupied hromadas only

  python 11_composite.py

Indices (higher = better; percentile ranks among non-occupied hromadas):
  capacity    pre-conditions: own revenue per capita (+, log), transfer dependency (−),
              capex share 2023-25 (+), relative civilian PIT growth 2021-25 (+, log);
              mean of ranks, >= 3 of 4 indicators required            -> bivariate axis vs exposure
  recovery    outcome: night-light recovery 2021->24 and winter ratio 2020/21->2024/25,
              lit pixels only (from 04_nightlights.py v1.1); >= 1 of 2   -> outcome variable
  engagement  DREAM valid projects per 10k (log1p); reported separately because it
              responds to damage as much as to capacity
Diagnostics: indicator correlations, PCA, sensitivity of capacity (z-score, geometric,
  leave-one-out, pillar weights, PIT instead of own revenue), correlations with exposure
  (strikes, alert hours from ../viina/qgis/unit_stats.gpkg), and a descriptive moderation
  test: recovery ~ exposure * capacity (OLS on standardised ranks; cross-sectional, not causal).
Output: tidy/resilience_index_v11_k3.csv, resilience_v1.gpkg layer hromada_index_v11,
        tidy/data_dictionary.csv rows, logs/11_composite.log
Caveat: capacity = institutional/economic capacity of the hromada, not citizen wellbeing;
        per-capita terms use the pre-war GHS-POP 2020 denominator.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import pyogrio

BASE = Path(__file__).resolve().parent
QGIS = BASE.parent / "viina" / "qgis"
TIDY, LOGS = BASE / "tidy", BASE / "logs"
_logf = open(LOGS / "11_composite.log", "w", encoding="utf-8")
pd.set_option("display.width", 220)

CAP = {  # indicator: (direction, transform, pillar)
    "own_rev_gf_pc_2025":       (+1, "log", "fiscal"),
    "transfer_dep_2025":        (-1, None, "fiscal"),
    "capex_share_2325":         (+1, None, "fiscal"),
    "pdfo_civ_growth_rel_2125": (+1, "log", "economy"),
}
REC = {
    "ntl_recovery_2124":     (+1, "log", "recovery"),
    "ntl_winter_ratio_2125": (+1, "log", "recovery"),
}
ENG = {"dream_per10k": (+1, "log1p", "engagement")}
CAP_MIN, REC_MIN = 3, 1
ALT = ("own_rev_gf_pc_2025", "pdfo_civ_pc_2025")


def log(*a):
    m = " ".join(str(x) for x in a)
    print(m, flush=True)
    _logf.write(m + "\n")
    _logf.flush()


def transform(s, how):
    s = pd.to_numeric(s, errors="coerce")
    if how == "log":
        return np.log(s.where(s > 0))
    if how == "log1p":
        return np.log1p(s.clip(lower=0))
    return s


def prep(df, spec):
    out = pd.DataFrame(index=df.index)
    for c, (d, how, _) in spec.items():
        if c not in df:
            log(f"  indicator {c} missing — skipped")
            continue
        v = transform(df[c], how) * d
        out[c] = v.clip(v.quantile(0.02), v.quantile(0.98))
    return out


def rk(x):
    return x.rank(pct=True)


def z(x):
    return (x - x.mean()) / x.std(ddof=0)


def mean_idx(norm, need):
    return norm.mean(axis=1).where(norm.notna().sum(axis=1) >= need)


def quint(s):
    """Quintile 1..5; tied values (e.g. many zero DREAM counts) share a class, so fewer
    than 5 classes can occur."""
    q = pd.qcut(s, 5, labels=False, duplicates="drop")
    return (q + 1).astype("Int64")


def compare(base, var, name):
    both = base.notna() & var.notna()
    rho = base[both].corr(var[both], method="spearman")
    shift = (var.rank(ascending=False) - base.rank(ascending=False))[both].abs().median()
    qc = (quint(var)[both] != quint(base)[both]).mean()
    log(f"  {name:26s} rho={rho:.3f}  median rank shift={shift:6.1f}  quintile change={qc:.1%}")


def ols(y, X, names):
    ok = y.notna() & X.notna().all(axis=1)
    yv, Xv = y[ok].values, np.column_stack([np.ones(ok.sum()), X[ok].values])
    beta, *_ = np.linalg.lstsq(Xv, yv, rcond=None)
    res = yv - Xv @ beta
    n, k = Xv.shape
    s2 = res @ res / (n - k)
    se = np.sqrt(np.diag(s2 * np.linalg.inv(Xv.T @ Xv)))
    r2 = 1 - (res @ res) / ((yv - yv.mean()) @ (yv - yv.mean()))
    log(f"  n={n}  R2={r2:.3f}")
    for nm, b, e in zip(["const"] + names, beta, se):
        log(f"    {nm:28s} b={b:+.3f}  se={e:.3f}  t={b / e:+.2f}")


def main():
    df = pd.read_csv(TIDY / "resilience_v1_k3.csv", dtype={"k1": str, "k2": str, "k3": str})
    df["k3"] = df["k3"].str.zfill(7)
    if "dream_per10k" not in df and {"dream_n", "pop_ghs_2020"} <= set(df):
        df["dream_per10k"] = df["dream_n"] / df["pop_ghs_2020"].where(df["pop_ghs_2020"] >= 100) * 1e4
    occ = df["occupied"].astype(str).str.lower().isin(["true", "1"])
    d = df[~occ].copy().reset_index(drop=True)
    log(f"non-occupied units: {len(d)}")

    Xc, Xr, Xe = prep(d, CAP), prep(d, REC), prep(d, ENG)
    allx = pd.concat([Xc, Xr, Xe], axis=1)
    log("\nindicator coverage (non-occupied):")
    for c in allx:
        log(f"  {c:26s} n={allx[c].notna().sum():5d}")
    log("\nSpearman between oriented indicators:\n" + allx.corr(method="spearman").round(2).to_string())
    Zc = Xc.apply(z).dropna()
    if len(Zc) > 20:
        sv = np.linalg.svd(Zc.values - Zc.values.mean(0), compute_uv=False)
        log(f"\nPCA capacity indicators (n={len(Zc)}): variance shares "
            f"{np.round(sv ** 2 / (sv ** 2).sum(), 2).tolist()}")

    # indices ------------------------------------------------------------------
    Rc, Rr, Re = Xc.apply(rk), Xr.apply(rk), Xe.apply(rk)
    d["capacity_index"] = mean_idx(Rc, CAP_MIN)
    d["n_cap"] = Rc.notna().sum(axis=1)
    d["recovery_index"] = mean_idx(Rr, REC_MIN)
    d["n_rec"] = Rr.notna().sum(axis=1)
    d["engagement_index"] = Re.iloc[:, 0] if Re.shape[1] else np.nan
    for c in ("capacity", "recovery", "engagement"):
        d[f"{c}_quintile"] = quint(d[f"{c}_index"])
    d["capacity_rank"] = d["capacity_index"].rank(ascending=False, method="min")
    log(f"\ncoverage: capacity {d['capacity_index'].notna().sum()}  recovery {d['recovery_index'].notna().sum()} "
        f"(both components {(d['n_rec'] == 2).sum()})  engagement {d['engagement_index'].notna().sum()}  "
        f"of {len(d)}")

    # capacity sensitivity -------------------------------------------------------
    log("\ncapacity sensitivity vs baseline:")
    base = d["capacity_index"]
    var = {"zscore": mean_idx(Xc.apply(z), CAP_MIN),
           "geometric": np.exp(np.log(Rc.clip(lower=0.01)).mean(axis=1)).where(Rc.notna().sum(axis=1) >= CAP_MIN)}
    fis = [c for c, v in CAP.items() if v[2] == "fiscal" and c in Rc]
    eco = [c for c, v in CAP.items() if v[2] == "economy" and c in Rc]
    var["pillars_50_50"] = pd.concat([Rc[fis].mean(axis=1), Rc[eco].mean(axis=1)], axis=1).mean(axis=1).where(
        Rc.notna().sum(axis=1) >= CAP_MIN)
    for c in Rc:
        var[f"without_{c}"] = mean_idx(Rc.drop(columns=c), CAP_MIN - 1)
    if ALT[1] in d:
        cap2 = {(ALT[1] if k == ALT[0] else k): v for k, v in CAP.items()}
        var["pit_pc_instead_own_rev"] = mean_idx(prep(d, cap2).apply(rk), CAP_MIN)
    for nm, v in var.items():
        compare(base, v, nm)
        d[f"sens_cap_{nm}"] = v
    if Rr.shape[1] == 2:
        log("\nrecovery: components vs combined:")
        for c in Rr:
            compare(d["recovery_index"], Rr[c], c)

    # exposure diagnostics -----------------------------------------------------------
    us = QGIS / "unit_stats.gpkg"
    expo_cols = []
    if us.exists():
        e = pyogrio.read_dataframe(us, layer="hromada_poly", read_geometry=False)
        e["k3"] = e["k3"].astype(str).str.zfill(7)
        keep = [c for c in ("n_all", "n_12m", "civcas_all", "alert_h_12m") if c in e]
        d = d.merge(e[["k3"] + keep].drop_duplicates("k3"), on="k3", how="left")
        pop = d["pop_ghs_2020"].where(d["pop_ghs_2020"] >= 100)
        if "n_all" in d:
            d["exp_strikes_log"] = np.log1p(d["n_all"])
            d["exp_strikes_p10k"] = d["n_all"] / pop * 1e4
            expo_cols += ["exp_strikes_log", "exp_strikes_p10k"]
        if "alert_h_12m" in d:
            expo_cols.append("alert_h_12m")
        if "civcas_all" in d:
            expo_cols.append("civcas_all")
        idx_cols = ["capacity_index", "recovery_index", "engagement_index"]
        log("\nSpearman: indices vs exposure (non-occupied):\n" +
            d[idx_cols + expo_cols].corr(method="spearman").loc[idx_cols, idx_cols + expo_cols].round(2).to_string())

        if "exp_strikes_log" in d and d["recovery_index"].notna().sum() > 50:
            log("\nmoderation (descriptive): z(recovery) ~ z(exposure) + z(capacity) + interaction")
            ez, cz = z(d["exp_strikes_log"]), z(d["capacity_index"])
            X = pd.DataFrame({"z_exposure_log_strikes": ez, "z_capacity": cz, "exposure_x_capacity": ez * cz})
            ols(z(d["recovery_index"]), X, list(X.columns))
            t = pd.qcut(d["exp_strikes_log"].rank(method="first"), 3, labels=["low", "mid", "high"])
            ct = pd.qcut(d["capacity_index"].rank(method="first"), 3, labels=["low", "mid", "high"])
            tab = d.assign(exposure=t, capacity=ct).pivot_table(
                index="exposure", columns="capacity", values="recovery_index", aggfunc="median", observed=False)
            log("\nmedian recovery index by exposure tercile (rows) x capacity tercile (cols):\n"
                + tab.round(3).to_string())
    else:
        log(f"\n{us} not found — exposure diagnostics skipped")

    # report --------------------------------------------------------------------------
    cols = ["k3", "name", "capacity_index", "recovery_index", "engagement_index"] + list(Rc.columns)
    ok = d.dropna(subset=["capacity_index"]).copy()
    ok[list(Rc.columns)] = Rc.loc[ok.index]
    log("\ntop 10 capacity (indicator columns = percentile ranks):\n"
        + ok.nlargest(10, "capacity_index")[cols].round(2).to_string(index=False))
    log("\nbottom 10 capacity:\n" + ok.nsmallest(10, "capacity_index")[cols].round(2).to_string(index=False))
    ob = d.groupby("k1")[["capacity_index", "recovery_index", "engagement_index"]].median()
    ob["n"] = d.groupby("k1").size()
    log("\nby oblast (median), sorted by capacity:\n" + ob.sort_values("capacity_index").round(3).to_string())
    if "garrison_flag" in d:
        g = d[d["garrison_flag"] == 1]
        log(f"\ngarrison-flagged: {len(g)}  median capacity {g['capacity_index'].median():.3f} "
            f"vs all {d['capacity_index'].median():.3f}")
    vk = d[d["k3"] == "2602003"]
    if len(vk):
        show = ["name", "capacity_index", "capacity_quintile", "recovery_index", "n_rec",
                "engagement_index"] + list(CAP) + list(REC) + list(ENG)
        log("\nVerkhovyna (raw indicator values):\n" + vk[[c for c in show if c in vk]].T.to_string(header=False))

    out_cols = (["k1", "k2", "k3", "name", "capacity_index", "capacity_rank", "capacity_quintile", "n_cap",
                 "recovery_index", "recovery_quintile", "n_rec", "engagement_index", "engagement_quintile",
                 "dream_per10k", "dream_active_share", "garrison_flag"] + expo_cols
                + [c for c in d if c.startswith("sens_cap_")])
    out_cols = [c for c in out_cols if c in d]
    d[out_cols].to_csv(TIDY / "resilience_index_v11_k3.csv", index=False)
    log(f"\nwrote tidy/resilience_index_v11_k3.csv rows={len(d)}")

    gp = BASE / "resilience_v1.gpkg"
    units = BASE / "units_hromada.gpkg"
    if units.exists():
        import geopandas as gpd
        g = gpd.read_file(units, layer="hromada")[["k3", "geometry"]]
        g["k3"] = g["k3"].astype(str).str.zfill(7)
        g = g.merge(d[out_cols], on="k3", how="inner")
        g.to_file(gp, layer="hromada_index_v11", driver="GPKG", engine="pyogrio")
        log(f"wrote {gp.name}:hromada_index_v11 ({len(g)} polygons)")

    dd_new = pd.DataFrame([
        ["capacity_index", "openbudget.gov.ua + JRC GHS-POP", "UA open data (CMU 835) + EC reuse — attribute both",
         "0-1 (mean percentile rank)", "2021-2025", "hromada",
         "Mean of percentile ranks of own revenue per capita (+, log), transfer dependency (−), capex share "
         f"2023-25 (+), relative civilian PIT growth 2021-25 (+, log); p2/p98 winsorised; >= {CAP_MIN} of 4; "
         "non-occupied only. Bivariate axis against exposure."],
        ["recovery_index", "NASA Black Marble VNP46A3 C2", "public domain — cite NASA Black Marble",
         "0-1 (mean percentile rank)", "2021-2025", "hromada",
         "Mean of percentile ranks of lit-pixel night-light recovery 2021->24 and winter ratio; outcome "
         "variable (responds to strikes and outages), not part of capacity"],
        ["engagement_index", "DREAM public API + JRC GHS-POP", "public open data — attribute DREAM",
         "0-1 (percentile rank)", "2023-2026", "hromada",
         "Percentile rank of valid DREAM projects per 10k (log1p); responds to damage and to planning "
         "capacity — reported separately"],
    ], columns=["indicator", "source", "licence", "unit", "year", "level", "method"])
    ddp = TIDY / "data_dictionary.csv"
    dd = pd.read_csv(ddp, dtype=str) if ddp.exists() else pd.DataFrame(columns=dd_new.columns)
    old = ["res_index", "sub_fiscal", "sub_economy", "sub_infra", "sub_community"]
    dd = pd.concat([dd[~dd["indicator"].isin(list(dd_new["indicator"]) + old)], dd_new], ignore_index=True)
    dd.to_csv(ddp, index=False)
    log(f"data dictionary updated: {len(dd)} indicators (v1 composite rows removed)")


if __name__ == "__main__":
    main()
