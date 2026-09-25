"""Step 4: hot spots.
(a) KDE rasters from settlement-precision event points  -> qgis/hotspots/kde_<var>_<bw>km.tif (events per 1,000 km2)
    vars: n12 (last 12 m, unweighted), rep12 (weighted by n_reports), rec (all years, recency-weighted), nall (all years)
(b) Getis-Ord Gi* and local Moran (LISA) on hromada centres (non-occupied) -> qgis/hotspots/gi_hromada.gpkg
    layers hromada_poly, hromada_pt; columns per <var>_<w>:
      gz   analytical Gi* z-score (binary weights incl. self)
      gp   two-sided conditional-permutation p (9,999 perms, tie-aware: separate hot/cold tails, ties count against significance)
      gcls hot99/hot95/hot90/ns/cold90/cold95/cold99 (from gp and tail direction)
      gfdr +1 hot / -1 cold / 0 : significant after Benjamini-Hochberg FDR (q = 0.05)
      lq   LISA quadrant HH/LH/LL/HL, lp two-sided permutation p, lcls quadrant if lp <= 0.05 else ns
    vars: n12 (log1p n_12m), rep12 (log1p rep_12m), score (log1p score), rate12 (log1p rate_12m, pop >= 1000 only),
          alert (alert_hp_12m)
    weights: knn8 (8 nearest centres) and db60 (60 km distance band, islands joined to nearest neighbour)
    Permutation draws neighbours with replacement from all other units (exact exclusion of i).
(c) global Moran's I (esda, row-standardised, 999 perms) -> qgis/hotspots/moran_summary.csv"""
import time, warnings
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.transform import from_origin
from rasterio.features import geometry_mask
from scipy.ndimage import gaussian_filter
from libpysal.weights import KNN, DistanceBand, W as WCls, w_union
from esda.moran import Moran
from esda import fdr

warnings.filterwarnings("ignore")
OUT = Path("qgis"); HOT = OUT / "hotspots"; HOT.mkdir(exist_ok=True)
RES = 5000
NODATA = -9999.0
PERMS = 9999          # local tests: enough resolution for FDR over ~1,300 units
PERMS_GLOBAL = 999
rng = np.random.default_rng(42)
t0 = time.time()

hpoly = gpd.read_file(OUT / "unit_stats.gpkg", layer="hromada_poly", engine="pyogrio")
hpt = gpd.read_file(OUT / "unit_stats.gpkg", layer="hromada_pt", engine="pyogrio")
ctl = gpd.read_file(OUT / "hromada_control.gpkg", engine="pyogrio")[["unit_id", "occupied", "occ_share"]]
hpoly = hpoly.merge(ctl, on="unit_id"); hpt = hpt.merge(ctl, on="unit_id")
CRS = hpoly.crs
outline = gpd.read_file(OUT / "ukraine_outline.gpkg", engine="pyogrio").to_crs(CRS)

# --- grid identical to build_surfaces.py -------------------------------------------------------
xmin, ymin, xmax, ymax = outline.total_bounds
xmin, ymin = np.floor((xmin - 20000) / RES) * RES, np.floor((ymin - 20000) / RES) * RES
xmax, ymax = np.ceil((xmax + 20000) / RES) * RES, np.ceil((ymax + 20000) / RES) * RES
nx, ny = int((xmax - xmin) / RES), int((ymax - ymin) / RES)
transform = from_origin(xmin, ymax, RES, RES)
shape = (ny, nx)
inside = ~geometry_mask(outline.geometry, out_shape=shape, transform=transform, invert=False)
occ_mask = geometry_mask(hpoly.loc[hpoly["occupied"], "geometry"], out_shape=shape, transform=transform, invert=True)
valid = inside & ~occ_mask

def write_tif(path, arr):
    a = np.where(valid, arr, NODATA).astype("float32")
    with rasterio.open(path, "w", driver="GTiff", height=shape[0], width=shape[1], count=1, dtype="float32",
                       crs=CRS.to_wkt(), transform=transform, nodata=NODATA, compress="deflate") as dst:
        dst.write(a, 1)

# --- (a) KDE ------------------------------------------------------------------------------------
stp = pd.read_pickle(OUT / "strike_events_settlement.pkl")
END = stp["date"].max(); START12 = END - pd.Timedelta(days=365)
pts = gpd.GeoDataFrame(stp, geometry=gpd.points_from_xy(stp["longitude"], stp["latitude"]), crs="EPSG:4326").to_crs(CRS)
pts["w_rec"] = 0.5 ** ((END - pts["date"]).dt.days / 182.5)
pts["n_reports"] = pts["n_reports"].fillna(1)
p12 = pts[pts["date"] >= START12]
KDE = {"n12": (p12, None), "rep12": (p12, "n_reports"), "rec": (pts, "w_rec"), "nall": (pts, None)}
xe = np.arange(xmin, xmax + RES / 2, RES); ye = np.arange(ymin, ymax + RES / 2, RES)
for name, (df, wcol) in KDE.items():
    H, _, _ = np.histogram2d(df.geometry.x, df.geometry.y, bins=[xe, ye], weights=None if wcol is None else df[wcol])
    H = H.T[::-1]
    for bw in (25, 10):
        dens = gaussian_filter(H, sigma=bw * 1000 / RES, mode="constant") / (RES / 1000) ** 2 * 1000
        write_tif(HOT / f"kde_{name}_{bw}km.tif", dens)
        print(f"kde {name:5s} bw={bw:2d} km: total={H.sum():9.1f}  max density={dens[valid].max():8.2f} /1000 km2")

# --- (b) weights ----------------------------------------------------------------------------------
fit = hpt[~hpt["occupied"]].reset_index(drop=True)
coords_all = np.c_[fit.geometry.x, fit.geometry.y]

def make_weights(coords):
    ws = {"knn8": KNN.from_array(coords, k=8)}
    db = DistanceBand(coords, threshold=60000, binary=True, silence_warnings=True)
    if db.islands:
        db = w_union(db, KNN.from_array(coords, k=1), silence_warnings=True)
    ws["db60"] = db
    return ws

# --- local statistics with tie-aware conditional permutation --------------------------------------
def local_stats(y, w):
    n = len(y)
    nb = [np.asarray(w.neighbors[i], dtype=int) for i in range(n)]
    ybar, s = y.mean(), y.std()
    z = (y - ybar) / s if s > 0 else np.zeros(n)
    gz = np.empty(n); gph = np.empty(n); gpc = np.empty(n)
    lph = np.empty(n); lpc = np.empty(n); lag = np.empty(n)
    for i in range(n):
        J = nb[i]; k = len(J)
        # Gi* (binary, self included)
        Wi = k + 1
        obs = y[i] + y[J].sum()
        gz[i] = (obs - ybar * Wi) / (s * np.sqrt((n * Wi - Wi ** 2) / (n - 1))) if s > 0 else 0.0
        idx = rng.integers(0, n - 1, size=(PERMS, k))
        idx += idx >= i                                       # exclude i exactly
        sim = y[i] + y[idx].sum(1)
        gph[i] = ((sim >= obs).sum() + 1) / (PERMS + 1)
        gpc[i] = ((sim <= obs).sum() + 1) / (PERMS + 1)
        # local Moran (row-standardised)
        lag[i] = z[J].mean()
        Iobs = z[i] * lag[i]
        Isim = z[i] * z[idx].mean(1)
        lph[i] = ((Isim >= Iobs).sum() + 1) / (PERMS + 1)
        lpc[i] = ((Isim <= Iobs).sum() + 1) / (PERMS + 1)
    gp = np.minimum(1, 2 * np.minimum(gph, gpc))
    ghot = gph < gpc
    lp = np.minimum(1, 2 * np.minimum(lph, lpc))
    quad = np.where(z >= 0, np.where(lag >= 0, "HH", "HL"), np.where(lag >= 0, "LH", "LL"))
    return gz, gp, ghot, lp, quad

def gi_class(gp, hot):
    lev = np.select([gp <= 0.01, gp <= 0.05, gp <= 0.10], ["99", "95", "90"], default="")
    return np.where(lev == "", "ns", np.where(hot, "hot", "cold") + lev)

VARS = {"n12": ("n_12m", True), "rep12": ("rep_12m", True), "score": ("score", True),
        "rate12": ("rate_12m", True), "alert": ("alert_hp_12m", False)}

res = pd.DataFrame({"unit_id": fit["unit_id"]})
moran_rows = []
for var, (col, logt) in VARS.items():
    mask = fit[col].notna().to_numpy(copy=True)
    if var == "rate12":
        mask = mask & (fit["pop_gn"] >= 1000).to_numpy(copy=True)
    y = fit.loc[mask, col].to_numpy(float, copy=True)
    y = np.log1p(y) if logt else y
    ws = make_weights(coords_all[mask])
    for wk, w in ws.items():
        t = time.time()
        gz, gp, ghot, lp, quad = local_stats(y, w)
        wr = WCls(w.neighbors, silence_warnings=True); wr.transform = "R"
        mi = Moran(y, wr, permutations=PERMS_GLOBAL)
        thr = fdr(gp, 0.05)
        pre = f"{var}_{wk}"
        num = {f"{pre}_gz": np.round(gz, 3), f"{pre}_gp": np.round(gp, 5),
               f"{pre}_gfdr": np.where((gp <= thr) & (thr > 0), np.where(ghot, 1, -1), 0).astype(float),
               f"{pre}_lp": np.round(lp, 5)}
        txt = {f"{pre}_gcls": gi_class(gp, ghot), f"{pre}_lq": quad, f"{pre}_lcls": np.where(lp <= 0.05, quad, "ns")}
        for c, v in num.items():
            full = np.full(len(res), np.nan); full[mask] = v; res[c] = full
        for c, v in txt.items():
            full = np.full(len(res), "na", dtype=object); full[mask] = v; res[c] = full
        gc = pd.Series(txt[f"{pre}_gcls"]).value_counts().to_dict()
        lc = pd.Series(txt[f"{pre}_lcls"]).value_counts().to_dict()
        gf = num[f"{pre}_gfdr"]
        row = dict(var=var, weights=wk, n=int(mask.sum()), mean_nb=round(w.mean_neighbors, 1),
                   moran_I=round(mi.I, 4), moran_p=round(mi.p_sim, 4), moran_z=round(mi.z_sim, 2),
                   fdr_thr=round(float(thr), 5),
                   hot95=int(gc.get("hot95", 0) + gc.get("hot99", 0)), cold95=int(gc.get("cold95", 0) + gc.get("cold99", 0)),
                   hot_fdr=int((gf == 1).sum()), cold_fdr=int((gf == -1).sum()),
                   HH=lc.get("HH", 0), HL=lc.get("HL", 0), LH=lc.get("LH", 0), LL=lc.get("LL", 0))
        moran_rows.append(row)
        print(f"{var:6s} {wk}: n={row['n']} Moran I={mi.I:.3f} (p={mi.p_sim:.3f})  Gi*: hot95={row['hot95']} hot_fdr={row['hot_fdr']} "
              f"cold95={row['cold95']} cold_fdr={row['cold_fdr']}  LISA: HH={row['HH']} HL={row['HL']} LH={row['LH']} LL={row['LL']}  ({time.time()-t:.0f}s)")

ms = pd.DataFrame(moran_rows); ms.to_csv(HOT / "moran_summary.csv", index=False)
print("\n" + ms.to_string(index=False))

# --- write ----------------------------------------------------------------------------------------
keep = ["unit_id", "k1", "k2", "k3", "label", "name", "oblast_en", "pseudo", "occupied", "occ_share", "pop_gn",
        "n_12m", "rep_12m", "score", "rate_12m", "alert_hp_12m", "area_km2"]
gp_path = HOT / "gi_hromada.gpkg"
if gp_path.exists():
    gp_path.unlink()
hpoly[keep + ["geometry"]].merge(res, on="unit_id", how="left").to_file(gp_path, layer="hromada_poly", driver="GPKG")
hpt[[c for c in keep if c != "area_km2"] + ["geometry"]].merge(res, on="unit_id", how="left").to_file(gp_path, layer="hromada_pt", driver="GPKG")

show = res.merge(fit[["unit_id", "label", "oblast_en", "n_12m", "alert_hp_12m"]], on="unit_id")
for wk in ("knn8", "db60"):
    cols = ["label", "oblast_en", "n_12m", f"n12_{wk}_gz", f"n12_{wk}_gp", f"n12_{wk}_gcls", f"n12_{wk}_lcls"]
    print(f"\nGi* hot spots (n12, {wk}, FDR-significant), top 25 by z:")
    print(show[show[f"n12_{wk}_gfdr"] == 1].sort_values(f"n12_{wk}_gz", ascending=False)[cols].head(25).to_string(index=False))
cols = ["label", "oblast_en", "n_12m", "n12_db60_gz", "n12_db60_gp", "n12_db60_gcls", "n12_db60_lcls"]
print("\nLISA high outliers (n12, db60, HL):")
print(show[show["n12_db60_lcls"] == "HL"].sort_values("n_12m", ascending=False)[cols].head(20).to_string(index=False))
west = show[show["oblast_en"].isin(["L'viv", "Ivano-Frankivs'k", "Transcarpathia", "Chernivtsi", "Ternopil'", "Volyn"])]
m = (west["n12_db60_gcls"] != "ns") | (west["n12_db60_lcls"] != "ns") | (west["n_12m"] >= 10)
print("\nwestern hromadas with any signal on n12 (db60) or >= 10 events:")
print(west[m][cols + ["n12_knn8_gcls", "alert_db60_gcls"]].to_string(index=False))
print(f"\nwritten: {HOT}/kde_*.tif, {gp_path}, {HOT}/moran_summary.csv   ({time.time()-t0:.0f}s)")
