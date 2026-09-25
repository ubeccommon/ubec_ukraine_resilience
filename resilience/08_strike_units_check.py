#!/usr/bin/env python3
"""
08_strike_units_check.py — are strikes assigned to hromadas with the approximated
admin_units polygons? Read-only: changes nothing in ../viina.

  python 08_strike_units_check.py [--layer path.gpkg:layer]

Reports: code references, candidate point layers, reassignment admin_units -> COD,
per-hromada gains/losses, match of recomputed counts against unit_stats.gpkg.
Output: tidy/strike_reassignment_k3.csv, logs/08_strike_units_check.log
"""
import argparse
import re
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio

BASE = Path(__file__).resolve().parent
VIINA = BASE.parent / "viina"
QGIS = VIINA / "qgis"
UNITS = BASE / "units_hromada.gpkg"
TIDY, LOGS = BASE / "tidy", BASE / "logs"
_logf = open(LOGS / "08_strike_units_check.log", "w", encoding="utf-8")
pd.set_option("display.width", 200)


def log(*a):
    m = " ".join(str(x) for x in a)
    print(m, flush=True)
    _logf.write(m + "\n")
    _logf.flush()


ap = argparse.ArgumentParser()
ap.add_argument("--layer", default="", help="path.gpkg:layer of strike points")
args = ap.parse_args()

# 1. code references --------------------------------------------------------
log("=" * 70 + "\n1. code references in ../viina")
pat = re.compile(r"admin_units|sjoin|within|intersects|contains|point_in|hromada_poly")
for f in sorted(list(VIINA.glob("*.py")) + list(VIINA.glob("*.sh"))):
    hits = [(i, ln.strip()) for i, ln in enumerate(f.read_text(errors="replace").splitlines(), 1)
            if pat.search(ln)]
    for i, ln in hits[:15]:
        log(f"  {f.name}:{i}: {ln[:150]}")
    if len(hits) > 15:
        log(f"  {f.name}: … {len(hits) - 15} more")

# 2. candidate point layers ---------------------------------------------------
log("=" * 70 + "\n2. point layers")
cands = []
for gp in sorted(set(QGIS.glob("*.gpkg")) | set(VIINA.glob("*.gpkg"))):
    try:
        layers = pyogrio.list_layers(gp)
    except Exception:
        continue
    for name, gt in layers:
        if gt and "point" in str(gt).lower():
            info = pyogrio.read_info(gp, layer=name)
            cands.append((gp, name, str(gt), int(info["features"]), list(info["fields"])[:14]))
for gp, name, gt, n, flds in cands:
    log(f"  {gp.name}:{name}  {gt}  n={n:,}  fields={flds}")
if args.layer:
    p, lname = args.layer.rsplit(":", 1)
    gp, name = Path(p), lname
else:
    pool = [c for c in cands if not re.search(r"centre|center|centroid|admin|label", c[1], re.I)]
    if not pool:
        raise SystemExit("no strike point layer found — rerun with --layer path.gpkg:layer")
    gp, name = max(pool, key=lambda c: c[3])[:2]
log(f"using {gp.name}:{name}")

# 3. assignment with both geometries -------------------------------------------
log("=" * 70 + "\n3. reassignment")
own = gpd.read_file(QGIS / "admin_units.gpkg", layer="hromada")[["k3", "name", "geometry"]]
own["k3"] = own["k3"].astype(str).str.zfill(7)
cod = gpd.read_file(UNITS, layer="hromada")[["k3", "geometry"]]
cod["k3"] = cod["k3"].astype(str).str.zfill(7)
pts = gpd.read_file(gp, layer=name)
pts = pts[pts.geometry.notna() & ~pts.geometry.is_empty].to_crs(own.crs)[["geometry"]]


def assign(units):
    j = gpd.sjoin(pts, units[["k3", "geometry"]], how="left", predicate="within")
    j = j[~j.index.duplicated(keep="first")]
    return j["k3"].reindex(pts.index)


a_own, a_cod = assign(own), assign(cod)
chg = a_own.fillna("none") != a_cod.fillna("none")
log(f"points {len(pts):,} | unassigned own={int(a_own.isna().sum()):,} cod={int(a_cod.isna().sum()):,} | "
    f"change hromada: {int(chg.sum()):,} ({chg.mean():.1%}) | "
    f"change raion: {int((a_own.str[:4].fillna('x') != a_cod.str[:4].fillna('x')).sum()):,} | "
    f"change oblast: {int((a_own.str[:2].fillna('x') != a_cod.str[:2].fillna('x')).sum()):,}")

ctrl = pyogrio.read_dataframe(QGIS / "hromada_control.gpkg", layer="hromada_control",
                              read_geometry=False)[["k3", "occupied"]]
ctrl["k3"] = ctrl["k3"].astype(str).str.zfill(7)
c = pd.DataFrame({"n_own": a_own.value_counts(), "n_cod": a_cod.value_counts()}).fillna(0).astype(int)
c.index.name = "k3"
c = c.reset_index().merge(own[["k3", "name"]], on="k3", how="left").merge(ctrl, on="k3", how="left")
c["diff"] = c["n_cod"] - c["n_own"]
c["ratio"] = (c["n_cod"] + 1) / (c["n_own"] + 1)
c.to_csv(TIDY / "strike_reassignment_k3.csv", index=False)
free = c[c["occupied"] == False]  # noqa: E712
log(f"non-occupied hromadas with any change: {int((free['diff'] != 0).sum())} / {len(free)} | "
    f"|diff|>=10: {int((free['diff'].abs() >= 10).sum())} | ratio >2 or <0.5: "
    f"{int(((free['ratio'] > 2) | (free['ratio'] < 0.5)).sum())}")
cols = ["k3", "name", "n_own", "n_cod", "diff"]
log("\nlargest gains with COD (non-occupied):\n" + free.nlargest(12, "diff")[cols].to_string(index=False))
log("\nlargest losses with COD (non-occupied):\n" + free.nsmallest(12, "diff")[cols].to_string(index=False))
cities = ["8000000", "6312027", "2306007", "1202001", "4806015", "5110137"]
log("\ncity hromadas:\n" + c[c["k3"].isin(cities)][cols].to_string(index=False))
rho = free[["n_own", "n_cod"]].corr(method="spearman").iloc[0, 1]
log(f"\nSpearman n_own vs n_cod (non-occupied): {rho:.3f}")

# 4. which geometry did unit_stats use? ------------------------------------------
log("=" * 70 + "\n4. unit_stats.gpkg comparison")
us_path = QGIS / "unit_stats.gpkg"
for lname, _ in pyogrio.list_layers(us_path):
    df = pyogrio.read_dataframe(us_path, layer=lname, read_geometry=False)
    if "k3" not in df.columns or len(df) < 1500:
        continue
    df["k3"] = df["k3"].astype(str).str.zfill(7)
    m = df.merge(c[["k3", "n_own", "n_cod"]], on="k3", how="left").fillna({"n_own": 0, "n_cod": 0})
    num = [x for x in df.columns if df[x].dtype.kind in "iuf" and x not in ("k1", "k2")]
    log(f"layer {lname}: numeric columns {num}")
    for x in num:
        v = pd.to_numeric(m[x], errors="coerce").fillna(0)
        if v.sum() <= 0:
            continue
        eq_own = float((v == m["n_own"]).mean())
        eq_cod = float((v == m["n_cod"]).mean())
        r_own = np.corrcoef(v, m["n_own"])[0, 1] if m["n_own"].std() > 0 else np.nan
        log(f"  {x:28s} sum={v.sum():>12,.0f}  equal-own={eq_own:.3f}  equal-cod={eq_cod:.3f}  "
            f"r(own)={r_own:.3f}")
log(f"\nwrote tidy/strike_reassignment_k3.csv")
_logf.close()
