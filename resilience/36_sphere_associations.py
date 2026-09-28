#!/usr/bin/env python3
"""
36_sphere_associations.py — step 7: how the three spheres go with war exposure, with functional
resilience, with each other, and where they cluster.

  python 36_sphere_associations.py            full run (about 10–20 minutes; wild-cluster intervals included)
  python 36_sphere_associations.py --no-ci    skip the wild-cluster confidence intervals (quicker)
  python 36_sphere_associations.py --B 1999   fewer bootstrap draws (test runs only)

Inputs (tidy/): sphere_indices_k3.csv (32), resilience_index_v11_k3.csv (11: exp_strikes_log, alert_h_12m,
  recovery_index), resilience_v1_k3.csv (pop_ghs_2020, ntl_n_lit_px, ntl_2021), trajectories_k3.csv (22:
  tr_s24_rel, tr_recent, tr_noise_sd; optional), frontline_zone_k3.csv (zone flag); units_hromada.gpkg.
Sample: non-occupied hromadas with the variables of each model. Zone hromadas are in the models (the tables
  are national aggregates, rule R3 concerns published hromada values); a sensitivity drops them.

Standardisation and inference (as 12_moderation.py and 22_trajectories.py): y and the focus variables are
  z-scored within each model sample, so b is in standard deviations. HC1 standard errors; oblast fixed effects
  where stated (within-R2 = 1 - SSR / sum of squares of y around its oblast mean). For every focus coefficient:
  restricted wild-cluster bootstrap p by oblast (robust_inference.py: Webb weights, B = 9,999, seed 20260926)
  and Conley spatial-HAC t (Bartlett kernel, 50 and 100 km, representative points in UA_LAEA). Key rows add a
  95 % interval by inverting the wild-cluster test (ci_lo / ci_hi). Moran's I of the residuals: KNN k = 6.

Part A — exposure. y = sphere index (2021 or 2025), x = z(log1p strikes since 2022) (alt: alert hours, 12 m),
  control z(log population 2020).
  A1 2021 level (no FE / FE): where the strikes fell relative to pre-war sphere strength. The strikes come
     after 2021, so this row describes geography and targeting, not an effect on the sphere.
  A2 2025 level (no FE / FE).
  A3 2025 given 2021 (FE, + z(sphere 2021)): did more-exposed hromadas move up or down relative to their
     neighbours in the same oblast. Variants: alert hours; without the frontline oblasts (Donetsk 14,
     Zaporizhzhia 23, Kherson 65); without zone hromadas.
  The same A2/A3 FE rows for the balance measures (see Part D).
Part B — functional resilience. y = recovery_index (11), log summer-2024 light relative to H2 2023
  (tr_s24_rel, 22: higher = smaller outage loss), log recent light level (tr_recent). The spheres are the
  2021 values (before the war; the 2025 values are contemporaneous with the outcomes).
  B1 all three spheres together + exposure + controls (log population, log lit pixels, log 2021 radiance) + FE.
  B1r the same on hromadas with reliable light data (>= 30 lit pixels, pre-war noise_sd <= 0.35), light outcomes.
  B2 one sphere at a time with the sphere x exposure interaction (does the sphere buffer exposure?), as 12.
Part C — spheres against each other. z(a) ~ z(b) + z(log population) + FE, for 2021, 2025 and the change
  2021 -> 2025 (difference of the percentile-rank indices = change of relative position). Also the plain
  Spearman rho and the within-oblast rho (ranks demeaned by oblast). Per-resident indicators share the
  population denominator, hence the population control.
Part D — local clusters (LISA, esda Moran_Local, KNN k = 6 on UA_LAEA representative points, row-standardised,
  9,999 permutations, fixed seed). Variables: the three spheres 2021 and 2025, their change, and the balance
  (as 35_sphere_layers.py: weights w_* / national centre -> isometric log-ratio coordinates):
    imbalance_Y         distance from the national centre (size of the departure on map 24)
    lean_cult_Y         cultural weight against the geometric mean of economic and rights (+ = cultural-leaning)
    lean_econ_rights_Y  economic against rights (+ = economic-leaning)
  Scopes: national (all non-occupied) and Carpathian (Zakarpattia 21, Ivano-Frankivsk 26, Lviv 46,
  Chernivtsi 73; weights built within the four oblasts). Classes HH, LL, HL, LH at p < 0.05 and after a
  false-discovery-rate cut (esda.fdr, 0.05).

Outputs
  tidy/sphere_associations.csv   one row per model and focus coefficient (national aggregates; published)
  tidy/sphere_lisa_summary.csv   global Moran's I and LISA class counts by scope, variable and oblast (published)
  tidy/sphere_lisa_k3.csv        hromada LISA classes for step 8 (local only, .gitignore: zone hromadas, R3)
  logs/36_sphere_associations.log
Caveat: cross-sectional and associational; no coefficient here is a causal effect.
"""
import argparse
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from robust_inference import conley_t, wild_cluster_ci, wild_cluster_p

BASE = Path(__file__).resolve().parent
TIDY, LOGS = BASE / "tidy", BASE / "logs"
UNITS = BASE / "units_hromada.gpkg"
LAEA = "+proj=laea +lat_0=48.5 +lon_0=31 +ellps=GRS80 +units=m"
SPH = ("econ", "rights", "cult")
LABEL = {"econ": "economic", "rights": "rights", "cult": "cultural"}
YEARS = (2021, 2025)
FRONTLINE = {"14", "23", "65"}
CARP = {"21", "26", "46", "73"}
REL_NLIT, REL_NOISE = 30, 0.35
K = 6
CUTOFFS = (50_000, 100_000)
SEED = 20260926
PERM = 9999
OUT = TIDY / "sphere_associations.csv"
OUT_LS = TIDY / "sphere_lisa_summary.csv"
OUT_LK = TIDY / "sphere_lisa_k3.csv"
warnings.filterwarnings("ignore", message="The weights matrix is not fully connected")
pd.set_option("display.width", 220)
pd.set_option("display.max_columns", 40)
_logf = None
_seen = set()


def log(*a):
    m = " ".join(str(x) for x in a)
    print(m, flush=True)
    _logf.write(m + "\n")
    _logf.flush()


def zf(df):
    for c, n in (("k1", 2), ("k2", 4), ("k3", 7)):
        if c in df:
            df[c] = df[c].astype(str).str.split(".").str[0].str.zfill(n)
    return df


def rd(name, required=True):
    p = TIDY / name
    if not p.exists():
        if required:
            raise SystemExit(f"missing input tidy/{name} — run the earlier pipeline steps first")
        log(f"note: tidy/{name} not found; the parts that need it are skipped")
        return None
    return zf(pd.read_csv(p, dtype={"k1": str, "k2": str, "k3": str}, low_memory=False))


def z(x):
    x = pd.to_numeric(pd.Series(x), errors="coerce").astype(float)
    sd = x.std(ddof=0)
    return (x - x.mean()) / sd if sd > 0 else x * np.nan


# ---- balance (as 35_sphere_layers.py) -------------------------------------------------------------------
def closure(p):
    return p / p.sum(axis=-1, keepdims=True)


def centre_of(W):
    g = np.exp(np.nanmean(np.log(W), axis=0))
    return g / g.sum()


def ilr(p):
    l = np.log(p)
    return np.stack([np.sqrt(0.5) * (l[..., 0] - l[..., 1]),
                     np.sqrt(2 / 3) * (0.5 * (l[..., 0] + l[..., 1]) - l[..., 2])], axis=-1)


# ---- models ---------------------------------------------------------------------------------------------
def ols_hc1(y, X):
    A = np.linalg.pinv(X.T @ X)
    b = A @ X.T @ y
    e = y - X @ b
    n, k = X.shape
    V = A @ ((X * e[:, None] ** 2).T @ X) @ A * n / (n - k)
    return b, np.sqrt(np.diag(V)), e


class Models:
    def __init__(self, d, B, do_ci):
        self.d, self.B, self.do_ci = d, B, do_ci
        self.rows = []
        try:
            import esda  # noqa: F401
            from libpysal.weights import KNN  # noqa: F401
            self.spatial = True
        except Exception as ex:
            log(f"note: esda/libpysal not available ({ex}); residual Moran's I left empty")
            self.spatial = False

    def fit(self, part, model, ycol, focus, extra=(), fe=True, data=None, ci=(), note="", inter=None):
        """z(y) ~ z(focus) + z(extra) [+ oblast FE]; inter=(a, b) adds the product of the z-scored focus
        variables a and b (as 12_moderation.py) as a further focus term 'a x b'."""
        d = self.d if data is None else data
        yv = pd.to_numeric(d[ycol], errors="coerce")
        ok = yv.notna() & np.isfinite(yv)
        for c in list(focus) + list(extra):
            v = pd.to_numeric(d[c], errors="coerce")
            ok &= v.notna() & np.isfinite(v)
        s = d[ok]
        if len(s) < 50:
            log(f"  {model}: n={len(s)} too small, skipped")
            return
        Xd = pd.DataFrame(index=s.index)
        for f in focus:
            Xd[f] = z(s[f])
        focus = list(focus)
        if inter:
            nm = f"{inter[0]} x {inter[1]}"
            Xd[nm] = Xd[inter[0]] * Xd[inter[1]]
            focus.append(nm)
        for c in extra:
            Xd[c] = z(s[c])
        if fe:
            D = pd.get_dummies(s["k1"], prefix="ob", drop_first=True, dtype=float)
            D = D.loc[:, D.std() > 0]
            Xd = pd.concat([Xd, D], axis=1)
        Xd = Xd.loc[:, Xd.std() > 0]
        Xd.insert(0, "const", 1.0)
        yz = z(yv[ok]).values
        X = Xd.values.astype(float)
        b, se, e = ols_hc1(yz, X)
        r2 = 1 - (e @ e) / (yz @ yz)
        grp = s["k1"].astype(str).values
        r2w = np.nan
        if fe:
            yd = yz - pd.Series(yz).groupby(grp).transform("mean").values
            r2w = 1 - (e @ e) / (yd @ yd)
        js = [Xd.columns.get_loc(f) for f in focus if f in Xd.columns]
        wb = wild_cluster_p(yz, X, js, grp, B=self.B)
        xy = np.column_stack([s["x"].values, s["y"].values])
        ct = conley_t(yz, X, js, xy, CUTOFFS)
        mi = np.nan
        if self.spatial:
            from esda.moran import Moran
            from libpysal.weights import KNN
            w = KNN.from_array(xy, k=K)
            w.transform = "r"
            mi = Moran(e, w, permutations=0).I
        head = (f"{part} | {model} | y={ycol}  n={len(s)}  R2={r2:.3f}"
                + (f"  within-R2={r2w:.3f}" if fe else "") + f"  Moran I(resid)={mi:.3f}" + (f"  {note}" if note else ""))
        log(head)
        for f, j in zip([f for f in focus if f in Xd.columns], js):
            lo = hi = np.nan
            if self.do_ci and f in ci:
                lo, hi = wild_cluster_ci(yz, X, j, grp, B=self.B)
            p = wb[j][1]
            star = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "." if p < 0.1 else ""
            log(f"    {f:28s} b={b[j]:+.3f}  HC1 t={b[j] / se[j]:+6.2f}  CR1 t={wb[j][0]:+6.2f}  WCB p={p:.3f}{star:3s}"
                f"  Conley t50={ct[CUTOFFS[0]][j]:+6.2f} t100={ct[CUTOFFS[1]][j]:+6.2f}"
                + (f"  95% [{lo:+.3f}, {hi:+.3f}]" if np.isfinite(lo) else ""))
            self.rows.append({"part": part, "model": model, "y": ycol, "x": f, "fe": int(fe),
                              "controls": ";".join(extra), "n": len(s), "r2": r2, "r2_within": r2w,
                              "b": b[j], "se_hc1": se[j], "t_hc1": b[j] / se[j], "t_cr1": wb[j][0], "p_wcb": p,
                              "t_conley50": ct[CUTOFFS[0]][j], "t_conley100": ct[CUTOFFS[1]][j],
                              "ci_lo": lo, "ci_hi": hi, "moran_I_resid": mi, "note": note})


# ---- LISA -----------------------------------------------------------------------------------------------
def lisa(d, var, scope):
    from esda.moran import Moran, Moran_Local
    from esda import fdr
    from libpysal.weights import KNN
    s = d[pd.to_numeric(d[var], errors="coerce").notna()]
    xy = np.column_stack([s["x"].values, s["y"].values])
    w = KNN.from_array(xy, k=K)
    w.transform = "r"
    if scope not in _seen and w.n_components > 1:
        log(f"   note: KNN {K} weights in scope {scope} have {w.n_components} disconnected components")
    _seen.add(scope)
    v = s[var].astype(float).values
    np.random.seed(SEED)
    g = Moran(v, w, permutations=999)
    try:
        lm = Moran_Local(v, w, permutations=PERM, seed=SEED)
    except TypeError:
        np.random.seed(SEED)
        lm = Moran_Local(v, w, permutations=PERM)
    q = pd.Series(lm.q, index=s.index).map({1: "HH", 2: "LH", 3: "LL", 4: "HL"})
    p = pd.Series(lm.p_sim, index=s.index)
    try:
        cut = fdr(lm.p_sim, 0.05)
    except Exception:
        cut = 0.05 / len(v)
    cls = q.where(p < 0.05, "ns")
    cls_f = q.where(p <= cut, "ns")
    return s, g, cls, cls_f, cut


def main():
    global _logf
    ap = argparse.ArgumentParser(description="step 7: sphere associations")
    ap.add_argument("--no-ci", action="store_true", help="skip wild-cluster confidence intervals")
    ap.add_argument("--B", type=int, default=9999, help="bootstrap draws (default 9,999)")
    a = ap.parse_args()
    LOGS.mkdir(exist_ok=True)
    _logf = open(LOGS / "36_sphere_associations.log", "w", encoding="utf-8")
    t0 = time.time()
    log(f"36_sphere_associations.py  {time.strftime('%Y-%m-%d %H:%M')}  B={a.B}  ci={'no' if a.no_ci else 'yes'}")

    # ---- data
    si = rd("sphere_indices_k3.csv")
    si["occupied"] = si["occupied"].astype(str).str.lower().isin(["true", "1"])
    d = si[~si["occupied"]].copy()
    idx = rd("resilience_index_v11_k3.csv")
    d = d.merge(idx[["k3"] + [c for c in ("exp_strikes_log", "alert_h_12m", "recovery_index") if c in idx]],
                on="k3", how="left")
    base = rd("resilience_v1_k3.csv")
    d = d.merge(base[["k3"] + [c for c in ("pop_ghs_2020", "ntl_n_lit_px", "ntl_2021") if c in base]],
                on="k3", how="left")
    tr = rd("trajectories_k3.csv", required=False)
    if tr is not None:
        d = d.merge(tr[["k3"] + [c for c in ("tr_s24_rel", "tr_recent", "tr_noise_sd") if c in tr]],
                    on="k3", how="left")
    zone = rd("frontline_zone_k3.csv")
    d["in_zone"] = d["k3"].isin(set(zone.loc[zone["zone"].astype(str) == "1", "k3"]))

    import geopandas as gpd
    g = zf(gpd.read_file(UNITS, layer="hromada")[["k3", "geometry"]]).to_crs(LAEA)
    pts = g.set_index("k3").geometry.representative_point()
    d["x"] = d["k3"].map(pts.x)
    d["y"] = d["k3"].map(pts.y)
    miss = d["x"].isna().sum()
    if miss:
        log(f"note: {miss} hromadas without geometry dropped")
    d = d[d["x"].notna()].reset_index(drop=True)
    log(f"non-occupied hromadas: {len(d)}  (zone {int(d['in_zone'].sum())}, Carpathian {int(d['k1'].isin(CARP).sum())})")

    # derived variables
    d["c_logpop"] = np.log(pd.to_numeric(d["pop_ghs_2020"], errors="coerce").clip(lower=1))
    d["c_loglit"] = np.log1p(pd.to_numeric(d.get("ntl_n_lit_px"), errors="coerce"))
    d["c_rad21"] = np.log(pd.to_numeric(d.get("ntl_2021"), errors="coerce").clip(lower=0.01))
    for c in ("c_loglit", "c_rad21"):
        d[c] = d[c].fillna(d[c].median())            # as 12/22 (NaN -> mean after z-scoring)
    for s in SPH:
        d[f"d_{s}"] = d[f"{s}_2025"] - d[f"{s}_2021"]
    for yr in YEARS:
        W = d[[f"w_{s}_{yr}" for s in SPH]].to_numpy(float)
        ok = np.isfinite(W).all(axis=1) & (W > 0).all(axis=1)
        c = centre_of(W[ok])
        zc = np.full((len(d), 2), np.nan)
        zc[ok] = ilr(closure(W[ok] / c))
        d[f"imbalance_{yr}"] = np.hypot(zc[:, 0], zc[:, 1])
        d[f"lean_econ_rights_{yr}"] = zc[:, 0]
        d[f"lean_cult_{yr}"] = -zc[:, 1]
        log(f"balance {yr}: national centre (econ, rights, cult) = {np.round(c, 3).tolist()}  "
            f"median imbalance {np.nanmedian(d[f'imbalance_{yr}']):.3f}")
    if "tr_s24_rel" in d:
        d["y_s24"] = np.log(pd.to_numeric(d["tr_s24_rel"], errors="coerce").where(lambda v: v > 0))
        d["y_recent"] = np.log(pd.to_numeric(d["tr_recent"], errors="coerce").clip(lower=0.01))
    if "alert_h_12m" in d:
        d["exp_alert"] = pd.to_numeric(d["alert_h_12m"], errors="coerce")
    d["exp"] = pd.to_numeric(d["exp_strikes_log"], errors="coerce")

    log("\ncorrelations (Spearman, non-occupied) of the spheres with exposure and outcomes:")
    xs = [c for c in ("exp", "exp_alert", "recovery_index", "y_s24", "y_recent") if c in d]
    ys = [f"{s}_{yr}" for yr in YEARS for s in SPH] + [f"d_{s}" for s in SPH]
    log(d[ys + xs].corr(method="spearman").loc[ys, xs].round(2).to_string())

    M = Models(d, a.B, not a.no_ci)

    # ---- Part A: exposure
    log("\n==== Part A — spheres and war exposure ====")
    for s in SPH:
        log(f"\n-- {LABEL[s]}")
        M.fit("A", "A1 2021, no FE", f"{s}_2021", ["exp"], ["c_logpop"], fe=False)
        M.fit("A", "A1 2021, FE", f"{s}_2021", ["exp"], ["c_logpop"])
        M.fit("A", "A2 2025, no FE", f"{s}_2025", ["exp"], ["c_logpop"], fe=False)
        M.fit("A", "A2 2025, FE", f"{s}_2025", ["exp"], ["c_logpop"])
        M.fit("A", "A3 2025 given 2021, FE", f"{s}_2025", ["exp"], [f"{s}_2021", "c_logpop"], ci=("exp",))
        if "exp_alert" in d:
            M.fit("A", "A3 alert hours", f"{s}_2025", ["exp_alert"], [f"{s}_2021", "c_logpop"])
        M.fit("A", "A3 without frontline oblasts", f"{s}_2025", ["exp"], [f"{s}_2021", "c_logpop"],
              data=d[~d["k1"].isin(FRONTLINE)], note="dropped k1 14, 23, 65")
        M.fit("A", "A3 without zone hromadas", f"{s}_2025", ["exp"], [f"{s}_2021", "c_logpop"],
              data=d[~d["in_zone"]], note="dropped zone hromadas")
    for bv in ("imbalance", "lean_cult", "lean_econ_rights"):
        log(f"\n-- balance: {bv}")
        M.fit("A", "A2 2025, FE", f"{bv}_2025", ["exp"], ["c_logpop"])
        M.fit("A", "A3 2025 given 2021, FE", f"{bv}_2025", ["exp"], [f"{bv}_2021", "c_logpop"])

    # ---- Part B: functional resilience
    log("\n==== Part B — pre-war spheres (2021) and functional resilience ====")
    ctrl = ["c_logpop", "c_loglit", "c_rad21"]
    sph21 = [f"{s}_2021" for s in SPH]
    outcomes = [c for c in ("recovery_index", "y_s24", "y_recent") if c in d]
    rel = pd.Series(False, index=d.index)
    if "tr_noise_sd" in d:
        rel = (pd.to_numeric(d["ntl_n_lit_px"], errors="coerce") >= REL_NLIT) & \
              (pd.to_numeric(d["tr_noise_sd"], errors="coerce") <= REL_NOISE)
    for yc in outcomes:
        log(f"\n-- outcome {yc}")
        M.fit("B", "B1 three spheres, FE", yc, sph21, ["exp"] + ctrl, ci=tuple(sph21))
        if yc != "recovery_index" and rel.any():
            M.fit("B", "B1r reliable light data", yc, sph21, ["exp"] + ctrl, data=d[rel],
                  note=f">= {REL_NLIT} lit pixels, noise_sd <= {REL_NOISE}")
        for s in SPH:
            M.fit("B", f"B2 {LABEL[s]} x exposure, FE", yc, [f"{s}_2021", "exp"], ctrl,
                  inter=(f"{s}_2021", "exp"))

    # ---- Part C: spheres against each other
    log("\n==== Part C — the spheres against each other ====")
    rho = []
    for a_, b_ in (("econ", "rights"), ("econ", "cult"), ("rights", "cult")):
        for tag, ca, cb in ((2021, f"{a_}_2021", f"{b_}_2021"), (2025, f"{a_}_2025", f"{b_}_2025"),
                            ("change", f"d_{a_}", f"d_{b_}")):
            ok = d[[ca, cb]].notna().all(axis=1)
            s = d[ok]
            r_raw = s[ca].corr(s[cb], method="spearman")
            ra, rb = s[ca].rank(), s[cb].rank()
            ra_w = ra - ra.groupby(s["k1"]).transform("mean")
            rb_w = rb - rb.groupby(s["k1"]).transform("mean")
            r_w = ra_w.corr(rb_w)
            rho.append((f"{LABEL[a_]}–{LABEL[b_]}", tag, len(s), r_raw, r_w))
            log(f"\n-- {LABEL[a_]} ~ {LABEL[b_]} ({tag}): Spearman {r_raw:+.2f}, within oblasts {r_w:+.2f}")
            M.fit("C", f"C {tag}, FE", ca, [cb], ["c_logpop"], ci=(cb,), note=f"rho={r_raw:.3f}; rho_within={r_w:.3f}")
    log("\nrank correlations between the spheres (plain | within oblasts):")
    log(pd.DataFrame(rho, columns=["pair", "year", "n", "rho", "rho_within"]).round(3).to_string(index=False))

    res = pd.DataFrame(M.rows)
    res.to_csv(OUT, index=False, float_format="%.6g")
    log(f"\nwrote {OUT.relative_to(BASE)} ({len(res)} rows)   [{(time.time() - t0) / 60:.1f} min]")

    # ---- Part D: LISA
    log("\n==== Part D — local clusters (LISA) ====")
    try:
        import esda  # noqa: F401
    except Exception as ex:
        log(f"esda not available ({ex}); Part D skipped")
        return
    lvars = ([f"{s}_{yr}" for yr in YEARS for s in SPH] + [f"d_{s}" for s in SPH]
             + [f"{bv}_{yr}" for yr in YEARS for bv in ("imbalance", "lean_cult", "lean_econ_rights")])
    summ, hk = [], d[["k1", "k2", "k3", "name", "in_zone"]].copy()
    for scope, sub in (("national", d), ("carpathian", d[d["k1"].isin(CARP)])):
        log(f"\n-- scope {scope} (n={len(sub)})")
        for v in lvars:
            s, gm, cls, cls_f, cut = lisa(sub, v, scope)
            hk.loc[s.index, f"{v}_{scope}"] = cls
            hk.loc[s.index, f"{v}_{scope}_fdr"] = cls_f
            cnt, cntf = cls.value_counts(), cls_f.value_counts()
            log(f"   {v:26s} Moran I={gm.I:+.3f} (p={gm.p_sim:.3f})  "
                + "  ".join(f"{c} {int(cnt.get(c, 0)):3d}/{int(cntf.get(c, 0)):3d}" for c in ("HH", "LL", "HL", "LH"))
                + f"   [p<0.05 / FDR, cut {cut:.4f}]")
            groups = [("all", s.index)] + [(k1, s.index[s["k1"] == k1]) for k1 in sorted(s["k1"].unique())]
            for k1, ix in groups:
                row = {"scope": scope, "variable": v, "k1": k1, "n": len(ix),
                       "moran_I": gm.I if k1 == "all" else np.nan, "moran_p": gm.p_sim if k1 == "all" else np.nan,
                       "fdr_cut": cut if k1 == "all" else np.nan}
                for c in ("HH", "LL", "HL", "LH", "ns"):
                    row[c] = int((cls[ix] == c).sum())
                for c in ("HH", "LL", "HL", "LH"):
                    row[f"{c}_fdr"] = int((cls_f[ix] == c).sum())
                summ.append(row)
    S = pd.DataFrame(summ)
    S.to_csv(OUT_LS, index=False, float_format="%.6g")
    hk.to_csv(OUT_LK, index=False)
    log(f"\nwrote {OUT_LS.relative_to(BASE)} ({len(S)} rows) and {OUT_LK.relative_to(BASE)} (local only)")

    # Carpathian profile of the national clusters
    log("\nnational LISA classes inside the Carpathian oblasts (p < 0.05; counts HH/LL/HL/LH):")
    cp = S[(S["scope"] == "national") & S["k1"].isin(CARP)]
    log(cp.pivot_table(index="variable", columns="k1", values=["HH", "LL"], aggfunc="sum")
        .reindex(lvars).fillna(0).astype(int).to_string())
    log(f"\ndone in {(time.time() - t0) / 60:.1f} min")


if __name__ == "__main__":
    main()
