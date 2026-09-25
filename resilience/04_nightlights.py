#!/usr/bin/env python3
"""
04_nightlights.py — VIIRS Black Marble VNP46A3 monthly radiance per hromada (k3), v1.1

  python 04_nightlights.py pull                 # download tiles (resumable)
  python 04_nightlights.py zonal                # per-month zonal means (all pixels + lit pixels)
  python 04_nightlights.py indicators           # recovery + winter ratios (lit pixels = primary)
  python 04_nightlights.py all                  # the three above in order

v1.1: ratios are computed over pixels lit in 2021 only (mean 2021 radiance >= LIT_THRESHOLD),
      so that unlit rural areas (snow, moonlight residue, noise) no longer produce spurious
      ratios; hromadas with fewer than MIN_LIT_PIX lit pixels get no ratio.
Units: units_hromada.gpkg (COD-AB ADM3, from 00_units_cod.py); falls back to admin_units.gpkg.
Auth: NASA Earthdata bearer token in ~/.earthdata_token (needed for downloads).
Product: VNP46A3 Collection 2 (LAADS 5200, version .002), 15 arcsec, tiles h20-h22 x v03-v04.
Licence: NASA open data / public domain. Cite NASA Black Marble (VNP46A3 C2).
Caveats: street-lighting policy and blackouts change radiance independently of economic
activity; snow-covered fallback biases winter months upward.
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio.features
from affine import Affine

BASE = Path(__file__).resolve().parent
QGIS = BASE.parent / "viina" / "qgis"
UNITS = BASE / "units_hromada.gpkg"
RAW = BASE / "raw" / "nightlights"
TIDY, LOGS = BASE / "tidy", BASE / "logs"
CACHE = TIDY / "ntl_cache"
for d in (RAW, TIDY, LOGS, CACHE):
    d.mkdir(parents=True, exist_ok=True)

ARCHIVES = ["https://ladsweb.modaps.eosdis.nasa.gov/archive/allData/5200/VNP46A3",
            "https://ladsweb.modaps.eosdis.nasa.gov/archive/allData/5000/VNP46A3"]
TILES = [(h, v) for h in (20, 21, 22) for v in (3, 4)]
SIZE = 2400
DEG = 10.0
SNOW_FREE = "AllAngle_Composite_Snow_Free"
SNOW_COV = "AllAngle_Composite_Snow_Covered"
MONTHS = ([(2020, 12)] + [(2021, m) for m in range(1, 13)]
          + [(2024, m) for m in range(1, 13)] + [(2025, m) for m in (1, 2)])
BASE_MONTHS = [(2021, m) for m in range(1, 13)]
LIT_THRESHOLD = 1.0      # nW/cm2/sr, mean of 2021 months
MIN_LIT_PIX = 10         # ~2 km2 of lit area at 15 arcsec
CACHE_V = "v11"
TOKEN_FILE = Path.home() / ".earthdata_token"
_logf = None
_ds_logged = False


def log(*a):
    m = " ".join(str(x) for x in a)
    print(m, flush=True)
    if _logf:
        _logf.write(m + "\n")
        _logf.flush()


def token(required=True):
    if TOKEN_FILE.exists() and TOKEN_FILE.read_text().strip():
        return TOKEN_FILE.read_text().strip()
    if required:
        sys.exit(f"missing or empty {TOKEN_FILE} — generate a token at "
                 f"https://urs.earthdata.nasa.gov (Generate Token) and save it there")
    return None


def http(url, dest=None, timeout=300, auth=True):
    h = {"User-Agent": "resilience-research/0.1"}
    t = token(required=False) if auth else None
    if t:
        h["Authorization"] = f"Bearer {t}"
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        if dest is None:
            return r.read()
        tmp = dest.with_suffix(dest.suffix + ".tmp")
        with open(tmp, "wb") as f:
            while chunk := r.read(1 << 20):
                f.write(chunk)
        tmp.rename(dest)
    return dest


def doy(y, m):
    return date(y, m, 1).timetuple().tm_yday


def list_dir(y, m):
    """(archive_base, [file names]) for this month's day-of-year directory."""
    d = f"{doy(y, m):03d}"
    for base in ARCHIVES:
        url = f"{base}/{y}/{d}.json"
        try:
            body = http(url, timeout=120, auth=False).decode("utf-8", "replace")
            js = json.loads(body)
            items = js.get("content", []) if isinstance(js, dict) else js
            names = sorted({i.get("name", "") for i in items if i.get("name", "").endswith(".h5")})
            if names:
                return base, names
        except urllib.error.HTTPError as e:
            if e.code != 404:
                log(f"  listing {url}: HTTP {e.code}")
        except Exception as e:
            log(f"  listing {url}: {e}")
    return None, []


def tile_files(y, m, download=True):
    """{(h,v): local path} for one month, downloading what is missing."""
    ddir = RAW / str(y) / f"{doy(y, m):03d}"
    ddir.mkdir(parents=True, exist_ok=True)
    have = {}
    for h, v in TILES:
        hit = [p for p in sorted(ddir.glob(f"VNP46A3.A{y}*.h{h:02d}v{v:02d}.*.h5"))
               if p.stat().st_size > 0]
        if hit:
            have[(h, v)] = hit[-1]
    if len(have) == len(TILES) or not download:
        return have
    base, names = list_dir(y, m)
    if not names:
        log(f"  {y}-{m:02d}: no directory listing in 5200 or 5000")
        return have
    for h, v in TILES:
        if (h, v) in have:
            continue
        match = sorted(n for n in names if f".h{h:02d}v{v:02d}." in n)
        if not match:
            log(f"  {y}-{m:02d} h{h:02d}v{v:02d}: not in listing")
            continue
        dest = ddir / match[-1]
        try:
            http(f"{base}/{y}/{doy(y, m):03d}/{match[-1]}", dest)
            have[(h, v)] = dest
            log(f"  {y}-{m:02d} h{h:02d}v{v:02d} {dest.stat().st_size/1e6:.1f} MB")
            time.sleep(0.3)
        except urllib.error.HTTPError as e:
            hint = " (token rejected — regenerate it)" if e.code in (401, 403) else ""
            log(f"  {y}-{m:02d} h{h:02d}v{v:02d}: HTTP {e.code}{hint}")
            if e.code in (401, 403):
                sys.exit("authentication failed — stopping")
        except Exception as e:
            log(f"  {y}-{m:02d} h{h:02d}v{v:02d}: {e}")
    return have


def tile_transform(h, v):
    return Affine(DEG / SIZE, 0, -180 + h * DEG, 0, -DEG / SIZE, 90 - v * DEG)


def read_band(path, name):
    global _ds_logged
    import h5py
    with h5py.File(path, "r") as f:
        found, alln = [], []

        def visit(n, obj):
            if isinstance(obj, h5py.Dataset):
                alln.append(n)
                if n.rsplit("/", 1)[-1] == name:
                    found.append(n)
        f.visititems(visit)
        if not found:
            if not _ds_logged:
                log(f"  band '{name}' not found in {path.name}; datasets: {alln}")
                _ds_logged = True
            return None
        d = f[found[0]]
        arr = d[:].astype("float32")
        a = dict(d.attrs)
        fill = a.get("_FillValue")
        if fill is not None:
            arr[arr == float(np.ravel(fill)[0])] = np.nan
        sf = a.get("scale_factor", a.get("Scale", 1.0))
        off = a.get("add_offset", a.get("Offset", 0.0))
        return arr * float(np.ravel(sf)[0]) + float(np.ravel(off)[0])


def composite(path):
    """(radiance, used_snow_fallback) — snow-free where valid, else snow-covered."""
    free = read_band(path, SNOW_FREE)
    cov = read_band(path, SNOW_COV)
    if free is None and cov is None:
        return None, None
    if free is None:
        free = np.full((SIZE, SIZE), np.nan, "float32")
    used_snow = np.isnan(free)
    if cov is not None:
        val = np.where(used_snow, cov, free)
        used_snow &= ~np.isnan(cov)
    else:
        val = free
        used_snow[:] = False
    return val, used_snow


def labels_for_tile(gdf, h, v, tag):
    """Label grid (0 = none, i+1 = gdf row i) cached per tile and unit source."""
    p = CACHE / f"labels_{tag}_h{h:02d}v{v:02d}.npy"
    if p.exists():
        return np.load(p)
    t = tile_transform(h, v)
    west, north = t.c, t.f
    sel = gdf.cx[west:west + DEG, north - DEG:north]
    lab = np.zeros((SIZE, SIZE), dtype="int32")
    if len(sel):
        shapes = [(geom, idx + 1) for idx, geom in zip(sel.index, sel.geometry)]
        lab = rasterio.features.rasterize(shapes, out_shape=(SIZE, SIZE), transform=t,
                                          fill=0, dtype="int32")
    np.save(p, lab)
    log(f"  labels {tag} h{h:02d}v{v:02d}: {len(sel)} polygons, {int((lab > 0).sum())} pixels")
    return lab


def lit_mask(h, v):
    """Pixels whose mean 2021 radiance >= LIT_THRESHOLD (cached per tile)."""
    p = CACHE / f"litmask_{LIT_THRESHOLD:g}_h{h:02d}v{v:02d}.npy"
    if p.exists():
        return np.load(p)
    s = np.zeros((SIZE, SIZE), "float64")
    c = np.zeros((SIZE, SIZE), "int16")
    for y, m in BASE_MONTHS:
        path = tile_files(y, m, download=False).get((h, v))
        if path is None:
            continue
        val, _ = composite(path)
        if val is None:
            continue
        ok = np.isfinite(val)
        s[ok] += val[ok]
        c[ok] += 1
    mean = np.where(c >= 6, s / np.maximum(c, 1), np.nan)
    mask = np.nan_to_num(mean, nan=0.0) >= LIT_THRESHOLD
    np.save(p, mask)
    log(f"  lit mask h{h:02d}v{v:02d}: {int(mask.sum()):,} lit pixels (2021 mean >= {LIT_THRESHOLD})")
    return mask


def load_units():
    src = UNITS if UNITS.exists() else QGIS / "admin_units.gpkg"
    g = gpd.read_file(src, layer="hromada")[["k3", "name", "geometry"]]
    g["k3"] = g["k3"].astype("string").str.zfill(7)
    g = g[g.geometry.notna()].to_crs("EPSG:4326").reset_index(drop=True)
    tag = "cod" if src == UNITS else "own"
    log(f"units from {src.name}: {len(g)} (tag {tag})")
    return g, tag


def zonal_month(gdf, tag, y, m):
    """Sums/counts per unit across the 6 tiles for one month: all pixels and lit pixels."""
    files = tile_files(y, m, download=True)
    if len(files) < len(TILES):
        log(f"{y}-{m:02d}: only {len(files)}/{len(TILES)} tiles — skipped")
        return None
    n = len(gdf) + 1
    acc = {k: np.zeros(n) for k in ("s", "c", "sn", "tot", "sl", "cl", "totl")}
    for (h, v), path in files.items():
        lab = labels_for_tile(gdf, h, v, tag)
        if not lab.any():
            continue
        lit = lit_mask(h, v)
        inside = lab > 0
        acc["tot"] += np.bincount(lab[inside], minlength=n)
        acc["totl"] += np.bincount(lab[inside & lit], minlength=n)
        val, used_snow = composite(path)
        if val is None:
            continue
        ok = inside & np.isfinite(val)
        if not ok.any():
            continue
        acc["s"] += np.bincount(lab[ok], weights=val[ok], minlength=n)
        acc["c"] += np.bincount(lab[ok], minlength=n)
        sc = ok & used_snow
        if sc.any():
            acc["sn"] += np.bincount(lab[sc], minlength=n)
        okl = ok & lit
        if okl.any():
            acc["sl"] += np.bincount(lab[okl], weights=val[okl], minlength=n)
            acc["cl"] += np.bincount(lab[okl], minlength=n)
    i = np.arange(1, n)
    a = {k: v[i] for k, v in acc.items()}
    div = lambda x, y: np.where(y > 0, x / np.maximum(y, 1), np.nan)  # noqa: E731
    return pd.DataFrame({
        "k3": gdf["k3"].values, "year": y, "month": m,
        "mean_radiance": div(a["s"], a["c"]),
        "n_pixels": a["tot"].astype(int),
        "valid_frac": div(a["c"], a["tot"]),
        "snow_frac": div(a["sn"], a["c"]),
        "mean_radiance_lit": div(a["sl"], a["cl"]),
        "n_lit": a["totl"].astype(int),
        "valid_frac_lit": div(a["cl"], a["totl"])})


def cmd_pull(args):
    token(required=True)
    for y, m in MONTHS:
        log(f"{y}-{m:02d}")
        f = tile_files(y, m)
        log(f"  tiles {len(f)}/{len(TILES)}")


def cmd_zonal(args):
    gdf, tag = load_units()
    frames = []
    for y, m in MONTHS:
        p = CACHE / f"ntl_{tag}_{CACHE_V}_{y}{m:02d}.csv"
        if p.exists():
            frames.append(pd.read_csv(p, dtype={"k3": str}))
            continue
        log(f"zonal {y}-{m:02d}")
        df = zonal_month(gdf, tag, y, m)
        if df is None or df["mean_radiance"].notna().sum() == 0:
            log("  no valid values — not cached")
            continue
        df.to_csv(p, index=False)
        frames.append(df)
        log(f"  all: mean={df['mean_radiance'].mean():.3f} valid={df['valid_frac'].median():.2f} "
            f"snow={df['snow_frac'].median():.2f} | lit: units with >= {MIN_LIT_PIX} lit px "
            f"{int((df['n_lit'] >= MIN_LIT_PIX).sum())}, mean={df['mean_radiance_lit'].mean():.2f}")
    if not frames:
        sys.exit("no months processed")
    allm = pd.concat(frames, ignore_index=True)
    allm.to_csv(TIDY / "nightlights_monthly_k3.csv", index=False)
    log(f"wrote tidy/nightlights_monthly_k3.csv rows={len(allm)} "
        f"months={allm.groupby(['year', 'month']).ngroups}")
    zero = allm[allm["n_pixels"] == 0]["k3"].nunique()
    if zero:
        log(f"WARNING {zero} hromadas have 0 raster pixels (too small at 15 arcsec)")


def ratios(d, val_col, frac_col, suffix):
    d = d[d[frac_col].fillna(0) >= 0.5]

    def annual(y):
        s = d[d["year"] == y].groupby("k3").agg(v=(val_col, "mean"), n=(val_col, "count"))
        return s.loc[s["n"] >= 9, "v"]

    def winter(keys):
        sel = d[pd.Series(list(zip(d["year"], d["month"])), index=d.index).isin(keys)]
        s = sel.groupby("k3").agg(v=(val_col, "mean"), n=(val_col, "count"))
        return s.loc[s["n"] == 3, "v"]

    o = pd.DataFrame({f"ntl_2021{suffix}": annual(2021), f"ntl_2024{suffix}": annual(2024),
                      f"ntl_winter_2021{suffix}": winter({(2020, 12), (2021, 1), (2021, 2)}),
                      f"ntl_winter_2025{suffix}": winter({(2024, 12), (2025, 1), (2025, 2)})})
    o[f"ntl_recovery_2124{suffix}"] = o[f"ntl_2024{suffix}"] / o[f"ntl_2021{suffix}"].where(o[f"ntl_2021{suffix}"] > 0.05)
    o[f"ntl_winter_ratio_2125{suffix}"] = (o[f"ntl_winter_2025{suffix}"] /
                                          o[f"ntl_winter_2021{suffix}"].where(o[f"ntl_winter_2021{suffix}"] > 0.05))
    o.index.name = "k3"
    return o


def cmd_indicators(args):
    src = TIDY / "nightlights_monthly_k3.csv"
    if not src.exists():
        sys.exit("run 'zonal' first")
    d = pd.read_csv(src, dtype={"k3": str})
    if "mean_radiance_lit" not in d:
        sys.exit("monthly table has no lit-pixel columns — rerun 'zonal'")
    nlit = d.groupby("k3")["n_lit"].max()
    lit_ok = nlit[nlit >= MIN_LIT_PIX].index
    primary = ratios(d[d["k3"].isin(lit_ok)], "mean_radiance_lit", "valid_frac_lit", "")
    allpx = ratios(d, "mean_radiance", "valid_frac", "_all")
    out = primary.join(allpx, how="outer").reset_index()
    out = out.merge(nlit.rename("ntl_n_lit_px").reset_index(), on="k3", how="right")
    keys = pd.read_csv(TIDY / "keys_hromada.csv", dtype=str)[["k1", "k2", "k3", "name"]]
    out = keys.merge(out, on="k3", how="left")
    out.to_csv(TIDY / "nightlights_indicators_k3.csv", index=False)
    log(f"wrote tidy/nightlights_indicators_k3.csv rows={len(out)}  "
        f"(hromadas with >= {MIN_LIT_PIX} lit pixels: {len(lit_ok)})")
    for c in ["ntl_2021", "ntl_2024", "ntl_recovery_2124", "ntl_winter_ratio_2125",
              "ntl_recovery_2124_all", "ntl_winter_ratio_2125_all", "ntl_n_lit_px"]:
        v = pd.to_numeric(out[c], errors="coerce")
        log(f"  {c:28s} n={v.notna().sum():5d}  median={v.median():>10,.3f}  "
            f"p05={v.quantile(.05):>10,.3f}  p95={v.quantile(.95):>10,.3f}")
    chk = ["8000000", "6312027", "6312005", "2306007", "2602003", "2601001"]
    log("control units (lit-pixel ratios | all-pixel ratios):\n" + out[out["k3"].isin(chk)][
        ["k3", "name", "ntl_n_lit_px", "ntl_2021", "ntl_recovery_2124", "ntl_winter_ratio_2125",
         "ntl_recovery_2124_all", "ntl_winter_ratio_2125_all"]].round(3).to_string(index=False))

    s = "NASA Black Marble VNP46A3 Collection 2 (LAADS DAAC 5200)"
    lic = "NASA open data / public domain — cite NASA Black Marble"
    lit_txt = (f"over pixels lit in 2021 (mean >= {LIT_THRESHOLD} nW/cm2/sr), hromadas with "
               f">= {MIN_LIT_PIX} lit pixels only")
    dd_new = pd.DataFrame([
        ["ntl_recovery_2124", s, lic, "ratio", "2021 vs 2024", "hromada",
         f"Mean monthly radiance 2024 / 2021 {lit_txt}; >=9 valid months; "
         "confounded by lighting policy and grid outages"],
        ["ntl_winter_ratio_2125", s, lic, "ratio", "Dec20-Feb21 vs Dec24-Feb25", "hromada",
         f"Winter mean radiance ratio {lit_txt}; snow-covered composite used where snow-free is absent"],
        ["ntl_recovery_2124_all", s, lic, "ratio", "2021 vs 2024", "hromada",
         "As ntl_recovery_2124 but over all pixels (v1; noisy in unlit rural hromadas) — reference only"],
        ["ntl_winter_ratio_2125_all", s, lic, "ratio", "Dec20-Feb21 vs Dec24-Feb25", "hromada",
         "As ntl_winter_ratio_2125 but over all pixels — reference only"],
        ["ntl_n_lit_px", s, lic, "pixels", "2021", "hromada", "Number of 15-arcsec pixels lit in 2021"],
        ["ntl_2021", s, lic, "nW/cm2/sr", "2021", "hromada", "Annual mean radiance over lit pixels"],
        ["ntl_2024", s, lic, "nW/cm2/sr", "2024", "hromada", "Annual mean radiance over lit pixels"],
    ], columns=["indicator", "source", "licence", "unit", "year", "level", "method"])
    ddp = TIDY / "data_dictionary.csv"
    dd = pd.read_csv(ddp, dtype=str) if ddp.exists() else pd.DataFrame(columns=dd_new.columns)
    dd = pd.concat([dd[~dd["indicator"].isin(dd_new["indicator"])], dd_new], ignore_index=True)
    dd.to_csv(ddp, index=False)
    log(f"data dictionary updated: {len(dd)} indicators")


def main():
    global _logf
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["pull", "zonal", "indicators", "all"])
    a = ap.parse_args()
    _logf = open(LOGS / f"04_{a.mode}.log", "w", encoding="utf-8")
    if a.mode in ("pull", "all"):
        cmd_pull(a)
    if a.mode in ("zonal", "all"):
        cmd_zonal(a)
    if a.mode in ("indicators", "all"):
        cmd_indicators(a)


if __name__ == "__main__":
    main()
