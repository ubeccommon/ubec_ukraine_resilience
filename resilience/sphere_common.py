"""sphere_common.py — shared data assembly, models and LISA for 36_sphere_associations.py (step 7) and
37_why_there.py (step 8).

open_log(name)      logs/<name>.log; log() prints and writes
load_base()         non-occupied hromadas with the sphere indices (32), exposure and recovery (11), population and
                    light controls (resilience_v1), light trajectories (22, optional), zone flag (28) and UA_LAEA
                    representative points; derived: c_logpop, c_loglit, c_rad21, d_<sphere>, balance
                    (imbalance_Y, lean_cult_Y, lean_econ_rights_Y, as 35_sphere_layers.py), y_s24, y_recent,
                    exp, exp_alert
Models.fit()        z(y) ~ z(focus) [+ raw focus] + z(extra) [+ oblast FE]; HC1, wild-cluster bootstrap by oblast,
                    Conley t 50/100 km, optional wild-cluster interval, Moran's I of residuals (KNN 6)
lisa()              global Moran's I and local Moran classes (HH/LL/HL/LH at p < 0.05 and after FDR)
"""
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
warnings.filterwarnings("ignore", message="The weights matrix is not fully connected")
pd.set_option("display.width", 220)
pd.set_option("display.max_columns", 40)
_logf = None
_seen = set()


def open_log(name):
    global _logf
    LOGS.mkdir(exist_ok=True)
    _logf = open(LOGS / f"{name}.log", "w", encoding="utf-8")


def log(*a):
    m = " ".join(str(x) for x in a)
    print(m, flush=True)
    if _logf:
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


# ---- data -----------------------------------------------------------------------------------------------
def load_base():
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
    return d


def reliable_light(d):
    if "tr_noise_sd" not in d:
        return pd.Series(False, index=d.index)
    return (pd.to_numeric(d["ntl_n_lit_px"], errors="coerce") >= REL_NLIT) & \
           (pd.to_numeric(d["tr_noise_sd"], errors="coerce") <= REL_NOISE)


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

    def fit(self, part, model, ycol, focus, extra=(), fe=True, data=None, ci=(), note="", inter=None, raw=()):
        """z(y) ~ z(focus) + z(extra) [+ oblast FE]; inter=(a, b) adds the product of the z-scored focus
        variables a and b (as 12_moderation.py) as a further focus term 'a x b'. Focus variables named in raw
        (e.g. 0/1 group dummies) enter unstandardised: b = difference in standard deviations of y."""
        d = self.d if data is None else data
        yv = pd.to_numeric(d[ycol], errors="coerce")
        ok = yv.notna() & np.isfinite(yv)
        for c in list(focus) + list(extra):
            v = pd.to_numeric(d[c], errors="coerce")
            ok &= v.notna() & np.isfinite(v)
        s = d[ok]
        if len(s) < 50:
            log(f"  {model}: n={len(s)} too small, skipped")
            return None
        Xd = pd.DataFrame(index=s.index)
        for f in focus:
            Xd[f] = pd.to_numeric(s[f], errors="coerce").astype(float) if f in raw else z(s[f])
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
        out = {}
        for f, j in zip([f for f in focus if f in Xd.columns], js):
            lo = hi = np.nan
            if self.do_ci and f in ci:
                lo, hi = wild_cluster_ci(yz, X, j, grp, B=self.B)
            p = wb[j][1]
            star = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "." if p < 0.1 else ""
            log(f"    {f:28s} b={b[j]:+.3f}  HC1 t={b[j] / se[j]:+6.2f}  CR1 t={wb[j][0]:+6.2f}  WCB p={p:.3f}{star:3s}"
                f"  Conley t50={ct[CUTOFFS[0]][j]:+6.2f} t100={ct[CUTOFFS[1]][j]:+6.2f}"
                + (f"  95% [{lo:+.3f}, {hi:+.3f}]" if np.isfinite(lo) else ""))
            row = {"part": part, "model": model, "y": ycol, "x": f, "fe": int(fe),
                   "controls": ";".join(extra), "n": len(s), "r2": r2, "r2_within": r2w,
                   "b": b[j], "se_hc1": se[j], "t_hc1": b[j] / se[j], "t_cr1": wb[j][0], "p_wcb": p,
                   "t_conley50": ct[CUTOFFS[0]][j], "t_conley100": ct[CUTOFFS[1]][j],
                   "ci_lo": lo, "ci_hi": hi, "moran_I_resid": mi, "note": note}
            self.rows.append(row)
            out[f] = row
        return out


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
