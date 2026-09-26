#!/usr/bin/env python3
"""
28_frontline_zone.py — front-line and border zone for security rule R3 (publication request 31).

  python 28_frontline_zone.py

Front line: the parts of the occupied area's outline that touch non-occupied hromadas (tolerance 200 m), from
  viina/qgis/hromada_control.gpkg — VIINA territorial control, occupied if the population-weighted share of places
  held by Russia or contested is >= 0.5 (control date in viina/qgis/meta.json). Hromada-level approximation: the
  line follows hromada boundaries and can be off by up to a hromada width; its length exceeds the contact line
  because hromada boundaries are jagged. Sea coasts and the border inside occupied territory drop out.
Border: the outer boundary of the hromada polygons (same geometry as all other layers) where it lies within 5 km
  of Russia or Belarus in Natural Earth 1:10m admin-0 (public domain; raw/naturalearth/), kept only next to
  non-occupied hromadas.
Zone (R3): non-occupied hromadas within ZONE_KM of the front line or the border. ZONE_RULE "any" = any part of the
  hromada polygon within the distance (conservative); "centre" = its representative point. Both flags are written.
Outputs: tidy/frontline_zone_k3.csv (k1, k2, k3, distances, zone flags), frontline_zone.gpkg layers "lines" and
  "zone" (local only), printed summary by oblast and raion. Distances in km, computed in UA_LAEA metres.
"""
import json
from pathlib import Path

import geopandas as gpd
import pandas as pd

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
TIDY = BASE / "tidy"
CTRL = ROOT / "viina/qgis/hromada_control.gpkg"
META = ROOT / "viina/qgis/meta.json"
NE = BASE / "raw/naturalearth/ne_10m_admin_0_countries.shp"
OUT_CSV = TIDY / "frontline_zone_k3.csv"
OUT_GPKG = BASE / "frontline_zone.gpkg"
ZONE_KM = 30
ZONE_RULE = "any"          # "any" = any part within ZONE_KM; "centre" = representative point within ZONE_KM
TOL = 200                  # m, shared-edge tolerance between hromada polygons
NE_TOL = 5000              # m, Natural Earth 1:10m vs COD-AB generalisation along the border


def main():
    g = gpd.read_file(CTRL)[["k1", "k2", "k3", "oblast_en", "occupied", "occ_share", "geometry"]]
    for c, n in (("k1", 2), ("k2", 4), ("k3", 7)):
        g[c] = g[c].astype(str).str.zfill(n)
    g["occupied"] = pd.to_numeric(g["occupied"], errors="coerce").fillna(0).astype(int)
    crs = g.crs
    unit = crs.axis_info[0].unit_name.lower()
    assert unit in ("metre", "meter"), f"hromada_control.gpkg is not in metres ({unit})"
    ctrl_date = json.loads(META.read_text(encoding="utf-8")).get("control_date", "?") if META.exists() else "?"

    occ_u = g[g["occupied"] == 1].union_all()
    free = g[g["occupied"] == 0].copy()
    free_u = free.union_all()
    front = occ_u.boundary.intersection(free_u.buffer(TOL))

    outer = g.union_all().boundary
    ne = gpd.read_file(NE)[["ADM0_A3", "geometry"]].to_crs(crs)
    borders = {}
    for iso in ("RUS", "BLR"):
        nb = ne.loc[ne["ADM0_A3"] == iso].union_all()
        borders[iso] = outer.intersection(nb.buffer(NE_TOL)).intersection(free_u.buffer(TOL))
    border = borders["RUS"].union(borders["BLR"])
    print(f"control date {ctrl_date}; non-occupied hromadas {len(free):,}")
    print(f"line lengths: front {front.length / 1000:,.0f} km, border with Russia (next to non-occupied) "
          f"{borders['RUS'].length / 1000:,.0f} km, with Belarus {borders['BLR'].length / 1000:,.0f} km")

    pts = free.geometry.representative_point()
    free["dist_front_km"] = free.geometry.distance(front) / 1000
    free["dist_border_km"] = free.geometry.distance(border) / 1000
    free["dist_front_centre_km"] = pts.distance(front) / 1000
    free["dist_border_centre_km"] = pts.distance(border) / 1000
    free["zone_any"] = ((free["dist_front_km"] <= ZONE_KM) | (free["dist_border_km"] <= ZONE_KM)).astype(int)
    free["zone_centre"] = ((free["dist_front_centre_km"] <= ZONE_KM) |
                           (free["dist_border_centre_km"] <= ZONE_KM)).astype(int)
    free["zone"] = free[f"zone_{ZONE_RULE}"]
    free["zone_reason"] = ""
    near_f = free["dist_front_km" if ZONE_RULE == "any" else "dist_front_centre_km"] <= ZONE_KM
    near_b = free["dist_border_km" if ZONE_RULE == "any" else "dist_border_centre_km"] <= ZONE_KM
    free.loc[near_f & ~near_b, "zone_reason"] = "front"
    free.loc[~near_f & near_b, "zone_reason"] = "border"
    free.loc[near_f & near_b, "zone_reason"] = "front+border"

    cols = ["k1", "k2", "k3", "dist_front_km", "dist_border_km", "dist_front_centre_km", "dist_border_centre_km",
            "zone_any", "zone_centre", "zone", "zone_reason"]
    out = free[cols].copy()
    out[[c for c in cols if c.endswith("_km")]] = out[[c for c in cols if c.endswith("_km")]].round(1)
    out.sort_values("k3").to_csv(OUT_CSV, index=False)

    lines = gpd.GeoDataFrame({"kind": ["front_line", "border_RUS", "border_BLR"],
                              "source": [f"VIINA control {ctrl_date}, hromada level",
                                         "COD-AB hromada outline, Natural Earth 1:10m neighbours",
                                         "COD-AB hromada outline, Natural Earth 1:10m neighbours"]},
                             geometry=[front, borders["RUS"], borders["BLR"]], crs=crs)
    lines.to_file(OUT_GPKG, layer="lines", driver="GPKG", engine="pyogrio")
    z = free[free["zone"] == 1]
    gpd.GeoDataFrame({"rule": [f"{ZONE_RULE} within {ZONE_KM} km"], "n_hromadas": [len(z)]},
                     geometry=[z.union_all()], crs=crs).to_file(OUT_GPKG, layer="zone", driver="GPKG",
                                                                engine="pyogrio")

    print(f"\nzone ({ZONE_RULE} within {ZONE_KM} km): {int(free['zone'].sum())} hromadas "
          f"(rule 'any' {int(free['zone_any'].sum())}, rule 'centre' {int(free['zone_centre'].sum())}); "
          f"reasons {free.loc[free['zone'] == 1, 'zone_reason'].value_counts().to_dict()}")
    by = free.groupby("oblast_en").agg(hromadas=("k3", "size"), zone_any=("zone_any", "sum"),
                                       zone_centre=("zone_centre", "sum"))
    print("\nby oblast (oblasts with zone hromadas):\n" + by[by["zone_any"] > 0].sort_values("zone_any", ascending=False)
          .to_string())
    r = free.groupby("k2").agg(n=("k3", "size"), nz=("zone", "sum"))
    touched = r[r["nz"] > 0]
    print(f"\nraions touched by the zone: {len(touched)} (fully {int((touched['nz'] == touched['n']).sum())}, "
          f"partly {int((touched['nz'] < touched['n']).sum())})")
    print(f"\nwrote {OUT_CSV.relative_to(ROOT)}, {OUT_GPKG.relative_to(ROOT)} (layers lines, zone)")


if __name__ == "__main__":
    main()
