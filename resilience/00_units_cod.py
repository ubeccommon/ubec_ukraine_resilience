#!/usr/bin/env python3
"""
00_units_cod.py — hromada polygons for zonal statistics, keyed to k3

COD-AB ADM3 (OCHA / SSPE Kartographia, v05 of Jan 2026, CC BY 3.0 IGO) where ADM3_PCODE == "UA"+k3;
admin_units.gpkg geometry for keys without a COD match (Crimean pseudo-units).
admin_units.gpkg hromada polygons are approximations (cities undersized up to 5x) and
must not be used for area-based sums.
Output: units_hromada.gpkg (layer hromada, CRS of admin_units = UA_LAEA)
"""
from pathlib import Path

import geopandas as gpd
import pandas as pd

BASE = Path(__file__).resolve().parent
QGIS = BASE.parent / "viina" / "qgis"
COD_ZIP = BASE / "raw" / "cod_ab" / "ukr_admin_boundaries.shp.zip"
OUT = BASE / "units_hromada.gpkg"
LOGS = BASE / "logs"
LOGS.mkdir(exist_ok=True)
_logf = open(LOGS / "00_units_cod.log", "w", encoding="utf-8")


def log(*a):
    m = " ".join(str(x) for x in a)
    print(m, flush=True)
    _logf.write(m + "\n")


own = gpd.read_file(QGIS / "admin_units.gpkg", layer="hromada")[["k1", "k2", "k3", "name", "geometry"]]
own["k3"] = own["k3"].astype(str).str.zfill(7)
crs = own.crs

cod = gpd.read_file(f"zip://{COD_ZIP}!ukr_admin3.shp").to_crs(crs)
cod["k3"] = cod["adm3_pcode"].str.replace("UA", "", regex=False)
cod["geometry"] = cod.geometry.buffer(0)
cod = cod[cod["k3"].isin(own["k3"])][["k3", "geometry"]].dissolve(by="k3").reset_index()
cod["geom_src"] = "COD-AB ADM3"
miss = own[~own["k3"].isin(cod["k3"])][["k3", "geometry"]].assign(geom_src="admin_units (no COD match)")
geo = gpd.GeoDataFrame(pd.concat([cod, miss], ignore_index=True), geometry="geometry", crs=crs)
u = gpd.GeoDataFrame(own[["k1", "k2", "k3", "name"]].merge(geo, on="k3", how="left"),
                     geometry="geometry", crs=crs)
u["area_km2"] = u.area / 1e6
u.to_file(OUT, layer="hromada", driver="GPKG", engine="pyogrio")
log(f"wrote {OUT.name}: {len(u)} units  {u['geom_src'].value_counts().to_dict()}")

un = u.union_all() if hasattr(u, "union_all") else u.unary_union
log(f"sum of areas {u['area_km2'].sum():,.0f} km2 | union {un.area/1e6:,.0f} km2 | "
    f"admin_units total {own.area.sum()/1e6:,.0f} km2 | missing geom {int(u.geometry.isna().sum())}")
cmp = u[["k3", "name", "area_km2"]].merge(
    own.assign(a_own=own.area / 1e6)[["k3", "a_own"]], on="k3")
chk = ["8000000", "6312027", "6312005", "6312013", "2306007", "2306027", "3210013", "2602003"]
log("\ncontrol units (km2):\n" + cmp[cmp["k3"].isin(chk)].round(1).to_string(index=False))
_logf.close()
