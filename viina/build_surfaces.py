"""Step 3: weather-map style surfaces from hromada centres.
 - control mask: qgis/hromada_control.gpkg (occ_share, occupied)  [cached in qgis/control_latest.pkl]
 - rasters     : qgis/surfaces/<var>_<method>.tif   (float32, UA_LAEA, 5 km, nodata -9999, clipped to outline, occupied masked)
                 <var>_krige_se.tif = kriging standard error (in transformed units)
 - isolines    : qgis/surfaces/isolines.gpkg  layer <var>_<method>  (level, label)
 - variograms  : qgis/surfaces/variograms.csv (empirical + fitted parameters)
Variables (last 12 months): strike_n12 (unweighted count), strike_rep12 (sum n_reports), strike_score (recency-weighted, all years),
                             strike_rate12 (per 100k GeoNames pop, units with pop>=1000 only), alert_h12 (hours under alert).
Counts/rates are interpolated as log1p and back-transformed; alert hours linear.
Kriging: ordinary kriging, global system solved directly (LU), exponential variogram fitted on pairs <= 400 km
         (range capped at 300 km, nugget >= 5% of sill); predictions clipped to the input range."""
import glob, time, zipfile
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.transform import from_origin
from rasterio.features import geometry_mask
from scipy.spatial import cKDTree
from scipy.spatial.distance import cdist
from scipy.optimize import curve_fit
from scipy.linalg import lu_factor, lu_solve
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from shapely.geometry import LineString

OUT = Path("qgis"); SURF = OUT / "surfaces"; SURF.mkdir(exist_ok=True)
RES = 5000            # m
IDW_K, IDW_P = 16, 2.0
VG_MAXLAG, VG_NBINS, VG_MAXRANGE = 400e3, 20, 300e3
NODATA = -9999.0
t0 = time.time()

hp = gpd.read_file(OUT / "unit_stats.gpkg", layer="hromada_pt", engine="pyogrio")
hpoly = gpd.read_file(OUT / "unit_stats.gpkg", layer="hromada_poly", engine="pyogrio")
CRS = hp.crs
outline = gpd.read_file(OUT / "ukraine_outline.gpkg", engine="pyogrio").to_crs(CRS)

# --- 1. occupation mask from latest control status -----------------------------------------------
cache = OUT / "control_latest.pkl"
if cache.exists():
    ctrl = pd.read_pickle(cache)
else:
    z = sorted(glob.glob("control_latest_*.zip"))[-1]
    parts = []
    with zipfile.ZipFile(z) as zf:
        name = [n for n in zf.namelist() if n.endswith(".csv")][0]
        for chunk in pd.read_csv(zf.open(name), usecols=["geonameid", "date", "status"], chunksize=2_000_000):
            parts.append(chunk.sort_values("date").drop_duplicates("geonameid", keep="last"))
    ctrl = pd.concat(parts).sort_values("date").drop_duplicates("geonameid", keep="last").dropna(subset=["geonameid"])
    ctrl["geonameid"] = ctrl["geonameid"].astype("int64")
    ctrl.to_pickle(cache)
print(f"control: latest date {ctrl['date'].max()}, {len(ctrl):,} places")
gn = gpd.read_file("gn_UA_tess.geojson", engine="pyogrio")[["geonameid", "population", "longitude", "latitude"]]
gn["geonameid"] = gn["geonameid"].astype("int64")
gn = gn.merge(ctrl[["geonameid", "status"]], on="geonameid", how="left")
gn = gpd.GeoDataFrame(gn, geometry=gpd.points_from_xy(gn["longitude"], gn["latitude"]), crs="EPSG:4326").to_crs(CRS)
gj = gpd.sjoin(gn, hpoly[["k3", "geometry"]], how="inner", predicate="within")
gj = gj[~gj.index.duplicated(keep="first")]
gj["ru"] = gj["status"].isin(["RU", "CONTESTED"]).astype(int)
gj["w"] = gj["population"].clip(lower=1)
occ = gj.groupby("k3").apply(lambda d: pd.Series({"occ_share": (d["ru"] * d["w"]).sum() / d["w"].sum(),
                                                   "n_ctrl": d["status"].notna().sum()}), include_groups=False)
hpoly = hpoly.merge(occ, left_on="k3", right_index=True, how="left")
hpoly["occ_share"] = hpoly["occ_share"].fillna(0).round(3)
hpoly["occupied"] = hpoly["occ_share"] >= 0.5
hpoly.loc[hpoly["k1"].isin(["01", "85"]), "occupied"] = True
hpoly[["unit_id", "k1", "k2", "k3", "label", "oblast_en", "occ_share", "n_ctrl", "occupied", "geometry"]].to_file(
    OUT / "hromada_control.gpkg", driver="GPKG")
print(f"occupied hromadas: {hpoly['occupied'].sum()} of {len(hpoly)}  (by oblast: "
      f"{hpoly[hpoly['occupied']].groupby('oblast_en').size().to_dict()})")
hp = hp.merge(hpoly[["unit_id", "occupied"]], on="unit_id")
fit = hp[~hp["occupied"]].copy()
print(f"fit points: {len(fit)} hromada centres")

# --- 2. grid --------------------------------------------------------------------------------------
xmin, ymin, xmax, ymax = outline.total_bounds
xmin, ymin = np.floor((xmin - 20000) / RES) * RES, np.floor((ymin - 20000) / RES) * RES
xmax, ymax = np.ceil((xmax + 20000) / RES) * RES, np.ceil((ymax + 20000) / RES) * RES
gx = np.arange(xmin + RES / 2, xmax, RES); gy = np.arange(ymax - RES / 2, ymin, -RES)
GX, GY = np.meshgrid(gx, gy)
transform = from_origin(xmin, ymax, RES, RES)
shape = GY.shape
inside = ~geometry_mask(outline.geometry, out_shape=shape, transform=transform, invert=False)
occ_mask = geometry_mask(hpoly.loc[hpoly["occupied"], "geometry"], out_shape=shape, transform=transform, invert=True)
valid = inside & ~occ_mask
print(f"grid {shape[1]}x{shape[0]} cells at {RES/1000:.0f} km; valid cells {valid.sum():,}")
grid = np.c_[GX.ravel(), GY.ravel()]
vflat = valid.ravel()

# --- 3. interpolators -----------------------------------------------------------------------------
def idw(xy, z):
    tree = cKDTree(xy)
    d, i = tree.query(grid, k=IDW_K)
    w = 1.0 / np.maximum(d, RES / 2) ** IDW_P
    return (w * z[i]).sum(1) / w.sum(1)

def exp_model(h, psill, rng, nug):          # exponential: nugget + psill*(1-exp(-3h/range))
    return nug + psill * (1 - np.exp(-3 * h / rng))

def fit_variogram(xy, z):
    tree = cKDTree(xy)
    pairs = tree.query_pairs(VG_MAXLAG, output_type="ndarray")
    d = np.linalg.norm(xy[pairs[:, 0]] - xy[pairs[:, 1]], axis=1)
    g = 0.5 * (z[pairs[:, 0]] - z[pairs[:, 1]]) ** 2
    edges = np.linspace(0, VG_MAXLAG, VG_NBINS + 1)
    idx = np.clip(np.digitize(d, edges) - 1, 0, VG_NBINS - 1)
    lag = np.array([d[idx == i].mean() if (idx == i).any() else np.nan for i in range(VG_NBINS)])
    sv = np.array([g[idx == i].mean() if (idx == i).any() else np.nan for i in range(VG_NBINS)])
    n = np.array([(idx == i).sum() for i in range(VG_NBINS)])
    ok = (n > 30) & np.isfinite(sv)
    var = z.var()
    popt, _ = curve_fit(exp_model, lag[ok], sv[ok], p0=[0.5 * var, 100e3, 0.3 * var],
                        bounds=([0, 10e3, 0], [10 * var, VG_MAXRANGE, var]), sigma=1 / np.sqrt(n[ok]), maxfev=20000)
    psill, rng, nug = popt
    nug = max(nug, 0.05 * (psill + nug))
    return (psill, rng, nug), pd.DataFrame({"lag_km": lag / 1000, "semivar": sv, "n_pairs": n})

def ok_predict(xy, z, params, chunk=4000):
    """Ordinary kriging on the grid (valid cells only). Global system, LU-factored once."""
    psill, rng, nug = params
    n = len(xy)
    A = np.zeros((n + 1, n + 1))
    A[:n, :n] = exp_model(cdist(xy, xy), psill, rng, nug)
    np.fill_diagonal(A[:n, :n], 0.0)
    A[n, :n] = 1.0; A[:n, n] = 1.0
    lu = lu_factor(A)
    pred = np.full(len(grid), np.nan); var = np.full(len(grid), np.nan)
    tgt = np.flatnonzero(vflat)
    for s in range(0, len(tgt), chunk):
        ii = tgt[s:s + chunk]
        b = np.empty((n + 1, len(ii)))
        b[:n] = exp_model(cdist(xy, grid[ii]), psill, rng, nug)
        b[n] = 1.0
        w = lu_solve(lu, b)
        pred[ii] = w[:n].T @ z
        var[ii] = (w * b).sum(0)
    return pred, np.sqrt(np.clip(var, 0, None))

vg_rows = []
def krige(xy, z, var):
    params, emp = fit_variogram(xy, z)
    psill, rng, nug = params
    emp.insert(0, "var", var)
    vg_rows.append(emp.assign(fit_psill=psill, fit_range_km=rng / 1000, fit_nugget=nug))
    print(f"     variogram exponential: psill={psill:.3g} range={rng/1000:.0f} km nugget={nug:.3g} "
          f"(nugget share {nug/(psill+nug):.0%}, var={z.var():.3g}); empirical: "
          + " ".join(f"{l:.0f}km:{s:.2g}" for l, s in zip(emp["lag_km"][:6], emp["semivar"][:6])))
    return ok_predict(xy, z, params)

def write_tif(path, arr):
    a = np.where(valid, arr, NODATA).astype("float32")
    with rasterio.open(path, "w", driver="GTiff", height=shape[0], width=shape[1], count=1, dtype="float32",
                       crs=CRS.to_wkt(), transform=transform, nodata=NODATA, compress="deflate") as dst:
        dst.write(a, 1)

def contours(arr, levels, labels):
    a = np.where(valid, arr, np.nan)
    cs = plt.contour(GX, GY, a, levels=levels)
    recs = []
    for lvl, lab, path in zip(cs.levels, labels, cs.get_paths()):
        v, c = path.vertices, path.codes
        starts = np.flatnonzero(c == 1) if c is not None else np.array([0])
        ends = np.r_[starts[1:], len(v)]
        for s, e in zip(starts, ends):
            seg = v[s:e]
            if len(seg) >= 2:
                recs.append({"level": float(lvl), "label": lab, "geometry": LineString(seg)})
    plt.close("all")
    return gpd.GeoDataFrame(recs, geometry="geometry", crs=CRS)

VARS = {
    "strike_n12":    dict(col="n_12m",        log=True,  levels=[1, 2, 5, 10, 20, 50, 100, 200, 500, 1000], minpop=0),
    "strike_rep12":  dict(col="rep_12m",      log=True,  levels=[1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000], minpop=0),
    "strike_score":  dict(col="score",        log=True,  levels=[0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500], minpop=0),
    "strike_rate12": dict(col="rate_12m",     log=True,  levels=[1, 2, 5, 10, 20, 50, 100, 200], minpop=1000),
    "alert_h12":     dict(col="alert_hp_12m", log=False, levels=[100, 250, 500, 1000, 1500, 2000, 3000, 4000, 5000, 6000, 7000, 8000], minpop=0),
}
iso_path = SURF / "isolines.gpkg"
if iso_path.exists():
    iso_path.unlink()
summary = []
for var, spec in VARS.items():
    f = fit if spec["minpop"] == 0 else fit[fit["pop_gn"] >= spec["minpop"]]
    f = f[f[spec["col"]].notna()]
    pxy = np.c_[f.geometry.x, f.geometry.y]
    z = f[spec["col"]].to_numpy(float)
    zt = np.log1p(z) if spec["log"] else z
    for method in ("idw", "krige"):
        t = time.time()
        surf, err = (idw(pxy, zt), None) if method == "idw" else krige(pxy, zt, var)
        surf = np.asarray(surf, float)
        n_clip = int(((surf < zt.min()) | (surf > zt.max())).sum())
        surf = np.clip(surf, zt.min(), zt.max()).reshape(shape)
        back = np.clip(np.expm1(surf) if spec["log"] else surf, 0, None)
        write_tif(SURF / f"{var}_{method}.tif", back)
        if err is not None:
            write_tif(SURF / f"{var}_{method}_se.tif", err.reshape(shape))
        levels = np.log1p(spec["levels"]) if spec["log"] else spec["levels"]
        iso = contours(surf, levels, [f"{l:g}" for l in spec["levels"]])
        iso.to_file(iso_path, layer=f"{var}_{method}", driver="GPKG")
        vmax, vmed = np.nanmax(back[valid]), np.nanmedian(back[valid])
        j = np.argmax(z); r, c = ~transform * (pxy[j, 0], pxy[j, 1]); at_max = back[int(c), int(r)]
        summary.append((var, method, len(f), round(float(z.max()), 1), round(float(at_max), 1), round(float(vmax), 1),
                        round(float(vmed), 2), n_clip, len(iso), round(time.time() - t, 1)))
        print(f"{var:14s} {method:5s} points={len(f):4d} input max={z.max():8.1f} surface at that point={at_max:8.1f} "
              f"surface max={vmax:8.1f} median={vmed:7.2f} clipped={n_clip:5d} isolines={len(iso):4d} ({time.time()-t:.1f}s)")

pd.concat(vg_rows).to_csv(SURF / "variograms.csv", index=False)
print(pd.DataFrame(summary, columns=["var", "method", "points", "in_max", "surf_at_max", "surf_max", "median", "clipped", "n_iso", "sec"]).to_string(index=False))
print(f"\nwritten: {SURF}/<var>_<method>.tif, {iso_path}, {SURF}/variograms.csv, {OUT}/hromada_control.gpkg   ({time.time()-t0:.0f}s)")
