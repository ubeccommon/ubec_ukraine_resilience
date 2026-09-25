#!/usr/bin/env python3
"""
05_population.py — GHS-POP R2023A (JRC) population per hromada (k3)

  python 05_population.py [--epochs 2020,2025]

Units: units_hromada.gpkg (COD-AB ADM3, from 00_units_cod.py); falls back to admin_units.gpkg.
Source: Schiavina, Freire, Carioli, MacManus (2023) GHS-POP R2023A, 100 m Mollweide
        tiles, https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_POP_GLOBE_R2023A/
Licence: European Commission reuse notice — reuse authorised, source acknowledged.
Caveat: disaggregated from GPW4.11 (pre-war census inputs); does not reflect
        2022+ displacement. E2020 = pre-war baseline denominator.
Outputs: raw/ghs_pop/*.zip, tidy/population_k3.csv, dictionary rows.
"""
import argparse
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio
import rasterio
from rasterio.features import rasterize
from rasterio.windows import Window, from_bounds

BASE = Path(__file__).resolve().parent
QGIS = BASE.parent / "viina" / "qgis"
UNITS = BASE / "units_hromada.gpkg"
RAW = BASE / "raw" / "ghs_pop"
TIDY, LOGS = BASE / "tidy", BASE / "logs"
for d in (RAW, TIDY, LOGS):
    d.mkdir(parents=True, exist_ok=True)
FTP = "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_POP_GLOBE_R2023A"
MOLL = "ESRI:54009"
BLOCK = 1500
_logf = open(LOGS / "05_population.log", "w", encoding="utf-8")


def log(*a):
    m = " ".join(str(x) for x in a)
    print(m, flush=True)
    _logf.write(m + "\n")
    _logf.flush()


def load_units():
    src = UNITS if UNITS.exists() else QGIS / "admin_units.gpkg"
    g = gpd.read_file(src, layer="hromada")[["k3", "name", "geometry"]]
    g["k3"] = g["k3"].astype("string").str.zfill(7)
    log(f"units from {src.name}: {len(g)}")
    return g


def tiles_for(bounds, step=50_000):
    xmin, ymin, xmax, ymax = bounds
    out = set()
    for x in np.arange(xmin, xmax + step, step):
        for y in np.arange(ymin, ymax + step, step):
            row = int((9_000_000 - y) / 1e6) + 1
            col = min(int((18_041_000 + x) / 1e6) + 1, 36)
            out.add((row, col))
    return sorted(out)


def fetch(url, dest):
    if dest.exists() and dest.stat().st_size > 0:
        return True
    req = urllib.request.Request(url, headers={"User-Agent": "resilience-research/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            tmp = dest.with_suffix(".tmp")
            with open(tmp, "wb") as f:
                while chunk := r.read(1 << 20):
                    f.write(chunk)
            tmp.rename(dest)
        log(f"  downloaded {dest.name} {dest.stat().st_size/1e6:.1f} MB")
        return True
    except urllib.error.HTTPError as e:
        log(f"  {dest.name}: HTTP {e.code} (no tile — skipped)")
        return False


def zonal_epoch(gdf, epoch):
    name = f"GHS_POP_E{epoch}_GLOBE_R2023A_54009_100"
    ub = gdf.total_bounds
    n = len(gdf) + 1
    s = np.zeros(n)
    for row, col in tiles_for(ub):
        zname = f"{name}_V1_0_R{row}_C{col}.zip"
        zp = RAW / zname
        if not fetch(f"{FTP}/{name}/V1-0/tiles/{zname}", zp):
            continue
        with zipfile.ZipFile(zp) as z:
            tifs = [m for m in z.namelist() if m.lower().endswith(".tif")]
        if not tifs:
            continue
        with rasterio.open(f"/vsizip/{zp}/{tifs[0]}") as src:
            b = src.bounds
            xmin, ymin = max(b.left, ub[0]), max(b.bottom, ub[1])
            xmax, ymax = min(b.right, ub[2]), min(b.top, ub[3])
            if xmin >= xmax or ymin >= ymax:
                continue
            w0 = from_bounds(xmin, ymin, xmax, ymax, src.transform)
            c0, r0 = max(int(w0.col_off), 0), max(int(w0.row_off), 0)
            wc = min(int(np.ceil(w0.width)) + 1, src.width - c0)
            wh = min(int(np.ceil(w0.height)) + 1, src.height - r0)
            tile_sum = 0.0
            for rr in range(0, wh, BLOCK):
                w = Window(c0, r0 + rr, wc, min(BLOCK, wh - rr))
                arr = src.read(1, window=w).astype("float64")
                bb = rasterio.windows.bounds(w, src.transform)
                idx = list(gdf.sindex.intersection(bb))
                if not idx:
                    continue
                lab = rasterize(((gdf.geometry.iloc[i], i + 1) for i in idx),
                                out_shape=arr.shape, transform=src.window_transform(w),
                                fill=0, dtype="int32")
                ok = (lab > 0) & (arr > 0)
                if ok.any():
                    s += np.bincount(lab[ok], weights=arr[ok], minlength=n)
                    tile_sum += arr[ok].sum()
            log(f"  E{epoch} R{row}_C{col}: {tile_sum:,.0f} persons inside hromadas")
    return s[1:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", default="2020,2025")
    a = ap.parse_args()
    epochs = [int(e) for e in a.epochs.split(",")]

    g = load_units()
    g = g[g.geometry.notna()].to_crs(MOLL).reset_index(drop=True)
    out = g[["k3", "name"]].copy()
    for e in epochs:
        log(f"epoch {e}")
        out[f"pop_ghs_{e}"] = zonal_epoch(g, e)

    ctrl = pyogrio.read_dataframe(QGIS / "hromada_control.gpkg", layer="hromada_control",
                                  read_geometry=False)[["k3", "occupied"]]
    ctrl["k3"] = ctrl["k3"].astype("string").str.zfill(7)
    us = pyogrio.read_dataframe(QGIS / "unit_stats.gpkg", layer="hromada_poly",
                                read_geometry=False)[["k3", "pop_gn"]]
    us["k3"] = us["k3"].astype("string").str.zfill(7)
    out = out.merge(ctrl, on="k3", how="left").merge(us.drop_duplicates("k3"), on="k3", how="left")
    out.drop(columns=["name"]).to_csv(TIDY / "population_k3.csv", index=False)
    log("wrote tidy/population_k3.csv")

    for e in epochs:
        c = f"pop_ghs_{e}"
        free = out[out["occupied"] == False]  # noqa: E712
        log(f"{c}: all={out[c].sum():,.0f}  non-occupied={free[c].sum():,.0f}  "
            f"zero={int((out[c] <= 0).sum())}  median={out[c].median():,.0f}")
    both = out.dropna(subset=["pop_gn"])
    both = both[both["pop_gn"] > 0]
    r = np.corrcoef(np.log(both["pop_gn"]), np.log(both[f"pop_ghs_{epochs[0]}"].clip(lower=1)))[0, 1]
    log(f"pop_gn vs GHS (n={len(both)}): log-corr={r:.3f}  "
        f"median ratio GHS/gn={(both[f'pop_ghs_{epochs[0]}'] / both['pop_gn']).median():.2f}")
    chk = ["8000000", "6312027", "6312005", "6312013", "2306007", "2306027", "3210013", "2602003"]
    log("\ncontrol units:\n" + out[out["k3"].isin(chk)].round(0).to_string(index=False))

    src = "JRC GHS-POP R2023A, 100 m (doi:10.2905/2FF68A52-5B5B-4A22-8F40-C41DA8332CFE)"
    lic = "EC reuse notice — reuse authorised, source acknowledged"
    dd_new = pd.DataFrame(
        [[f"pop_ghs_{e}", src, lic, "persons", str(e), "hromada",
          "Sum of 100 m cells whose centre falls in the COD-AB ADM3 polygon; GPW4.11-based, "
          "pre-war inputs, no displacement adjustment"] for e in epochs],
        columns=["indicator", "source", "licence", "unit", "year", "level", "method"])
    ddp = TIDY / "data_dictionary.csv"
    dd = pd.read_csv(ddp, dtype=str) if ddp.exists() else pd.DataFrame(columns=dd_new.columns)
    dd = pd.concat([dd[~dd["indicator"].isin(dd_new["indicator"])], dd_new], ignore_index=True)
    dd.to_csv(ddp, index=False)
    log(f"data dictionary updated: {len(dd)} indicators")


if __name__ == "__main__":
    main()
