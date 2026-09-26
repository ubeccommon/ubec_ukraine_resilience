"""Step 1: oblast / raion / hromada polygons and centre points.
Codes, hierarchy and names from katotth_UA_tess.geojson + KATOTTG codifier:
UA + ob(2) + rn(2) + hr(3) + st(3) + ds(2) + tail(5).
Geometry: hromada polygons from OCHA COD-AB ADM3 (SSPE Kartographia, v05 of Jan 2026, CC BY 3.0 IGO)
where ADM3_PCODE == "UA" + k3; Crimea and Sevastopol (k1 01, 85) keep the settlement
tessellation (COD codes there do not match KATOTTH keys; occupied, outside the analysis).
Raion and oblast polygons are dissolved from the hromadas.
Names: official KATOTTG register (katottg.csv, CC BY 4.0, mykhailoklimnyk/ua-administrative-codes) if present,
plus manual fills for rows the register lacks; otherwise heuristics from the tessellation.
Outputs (UA_LAEA):
  qgis/admin_units.gpkg    layers oblast, raion, hromada           (polygons; hromada has geom_src)
  qgis/admin_centres.gpkg  layers <level>_centroid, <level>_inside, <level>_centre
     _centre = centroid where it lies inside the polygon, otherwise the inside point -> use for interpolation / Gi*."""
import re, time
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 40)

UA_LAEA = "+proj=laea +lat_0=48.5 +lon_0=31 +x_0=0 +y_0=0 +ellps=GRS80 +units=m +no_defs"
OUT = Path("qgis"); OUT.mkdir(exist_ok=True)
UNITS_GPKG = OUT / "admin_units.gpkg"
CENTRES_GPKG = OUT / "admin_centres.gpkg"
CODIFIER = Path("katottg.csv")
COD_ZIP = Path("../resilience/raw/cod_ab/ukr_admin_boundaries.shp.zip")
TESS_ONLY_K1 = {"01", "85"}
# level-2 rows missing from the register
RAION_MANUAL = {"1204": "Кам'янський район", "6308": "Куп'янський район", "6802": "Кам'янець-Подільський район"}
ZONE_NAME = "Зона відчуження (Прип'ять, Чорнобиль)"
CHECK_K3 = ["8000000", "6312027", "2306007", "1202001", "4806015"]
for p in (UNITS_GPKG, CENTRES_GPKG):
    if p.exists():
        p.unlink()

t0 = time.time()
g = gpd.read_file("katotth_UA_tess.geojson", engine="pyogrio")
g = g[g["kod"].str.match(r"^UA\d{17}$")].copy()
d = g["kod"].str[2:]
g["ob"] = d.str[0:2]
g["rn"] = d.str[2:4]
g["hr"] = d.str[4:7]
g["st"] = d.str[7:10]
g["ds"] = d.str[10:12]
g["k1"] = g["ob"]
g["k2"] = g["ob"] + g["rn"]
g["k3"] = g["k2"] + g["hr"]
z_rn, z_hr, z_st, z_ds = (g["rn"] == "00"), (g["hr"] == "000"), (g["st"] == "000"), (g["ds"] == "00")
g["level"] = np.select(
    [z_rn & z_hr & z_st & z_ds, z_hr & z_st & z_ds, z_st & z_ds, z_ds],
    [1, 2, 3, 4], default=5,
)
print("rows by code-derived level:", g["level"].value_counts().sort_index().to_dict())

# --- official names from the codifier ---------------------------------------------
cod_names = {2: dict(RAION_MANUAL), 3: {}}
if CODIFIER.exists():
    cod = pd.read_csv(CODIFIER, dtype=str)
    cod = cod[cod["code"].str.match(r"^UA\d{17}$", na=False)].copy()
    cod["name"] = (cod["name"].str.replace(r"\s*\([^)]*\)\s*", " ", regex=True)
                   .str.replace(r"\s+", " ", regex=True).str.strip())
    for L, n in ((2, 4), (3, 7)):
        sub = cod[cod["level"] == str(L)].drop_duplicates("code", keep="last")
        sub = sub.assign(key=sub["code"].str[2:2 + n]).drop_duplicates("key", keep="last")
        cod_names[L].update(dict(zip(sub["key"], sub["name"])))
    print(f"codifier: {len(cod_names[2])} raion names (incl. {len(RAION_MANUAL)} manual), {len(cod_names[3])} hromada names")
else:
    print("WARNING: katottg.csv not found -> heuristic names only")

# --- projected, valid geometry ------------------------------------------------
g = g.to_crs(UA_LAEA)
g["geometry"] = g.geometry.make_valid()

def dissolve(parts, key):
    allp = pd.concat([p[[key, "geometry"]] for p in parts], ignore_index=True)
    u = allp.dissolve(by=key)
    u["geometry"] = u.geometry.make_valid().buffer(0)
    return u

has_lower = g.loc[g["level"] >= 2, "k1"].unique()
special = g[(g["level"] == 1) & ~g["k1"].isin(has_lower)]
print("special-status cities carried down as pseudo units:", special["name"].tolist())
t = time.time()
hro = dissolve([g[g["level"] >= 3], special], "k3")
print(f"hromada dissolve: {len(hro)} units  ({time.time()-t:.0f}s)")
tess_area = (hro.geometry.area / 1e6)

# --- replace hromada geometry with COD-AB ADM3 ----------------------------------------
use_cod = COD_ZIP.exists()
if use_cod:
    c3 = gpd.read_file(f"zip://{COD_ZIP}!ukr_admin3.shp", engine="pyogrio").to_crs(UA_LAEA)
    c3["k3"] = c3["adm3_pcode"].str[2:]
    c3["geometry"] = c3.geometry.make_valid().buffer(0)
    c3 = c3[["k3", "geometry"]].dissolve(by="k3")
    swap = hro.index[hro.index.isin(c3.index) & ~hro.index.str[:2].isin(TESS_ONLY_K1)]
    hro.loc[swap, "geometry"] = c3.loc[swap, "geometry"].values
    hro["geom_src"] = np.where(hro.index.isin(swap), "COD-AB ADM3", "tessellation")
    print(f"hromada geometry: {len(swap)} from COD-AB ADM3, {len(hro) - len(swap)} tessellation "
          f"(k1 in {sorted(TESS_ONLY_K1)} or no COD match)")
    nomatch = hro.index[~hro.index.isin(c3.index) & ~hro.index.str[:2].isin(TESS_ONLY_K1)]
    if len(nomatch):
        print("  WARNING mainland k3 without COD polygon (tessellation kept):", list(nomatch))
else:
    hro["geom_src"] = "tessellation"
    print(f"WARNING: {COD_ZIP} not found -> tessellation geometry (approximate, cities undersized)")

new_area = hro.geometry.area / 1e6
chk = pd.DataFrame({"tess_km2": tess_area, "new_km2": new_area}).loc[
    [k for k in CHECK_K3 if k in hro.index]].round(1)
print("city check (km2):\n" + chk.to_string())
un = hro.union_all() if hasattr(hro, "union_all") else hro.unary_union
print(f"hromada sum of areas {new_area.sum():,.0f} km2 | union {un.area/1e6:,.0f} km2 "
      f"(difference = overlaps)")

hro_r = hro.reset_index()
hro_r["k2"] = hro_r["k3"].str[:4]
lvl2 = g[g["level"] == 2]
lvl1 = g[g["level"] == 1]
if use_cod:
    lvl2 = lvl2[lvl2["k1"].isin(TESS_ONLY_K1)]
    lvl1 = lvl1[lvl1["k1"].isin(TESS_ONLY_K1)]
rai = dissolve([hro_r, lvl2], "k2")
print(f"raion dissolve:   {len(rai)} units")
rai_r = rai.reset_index()
rai_r["k1"] = rai_r["k2"].str[:2]
obl = dissolve([rai_r, lvl1], "k1")
print(f"oblast dissolve:  {len(obl)} units")

# --- names and attributes --------------------------------------------------------
def mode_or_none(s):
    s = s.dropna()
    return s.mode().iloc[0] if len(s) else None

ob_en = g.groupby("k1")["ADM1_NAME"].agg(mode_or_none)
ob_uk = g.groupby("k1")["ADM1_NAME_ALT"].agg(mode_or_none)
own_kod = {L: g[g["level"] == L].groupby(f"k{L}")["kod"].first() for L in (1, 2, 3)}
own_name = {L: g[g["level"] == L].groupby(f"k{L}")["name"].first() for L in (1, 2, 3)}
n_settl = g[g["level"] >= 4].groupby("k3").size()
s001 = g[(g["level"] == 4) & (g["st"] == "001")].groupby("k3")["name"].first()
first_settl = g[g["level"] >= 4].sort_values("kod").groupby("k3")["name"].first()

TYPE_WORDS = r"\b(сільська|селищна|міська|територіальна|громада|рада|район|область)\b"
def short(s):
    return re.sub(r"\s+", " ", re.sub(TYPE_WORDS, " ", str(s))).strip()

def attach_names(u, L, key):
    u = u.reset_index()
    u["level"] = L
    u["kod"] = u[key].map(own_kod[L])
    u["k1"] = u[key].str[:2]
    u["oblast_en"] = u["k1"].map(ob_en)
    u["oblast_uk"] = u["k1"].map(ob_uk)
    if L == 1:
        u["name"] = u["oblast_uk"]
        u["name_src"] = "ADM1_NAME_ALT mode"
        u["label"] = u["name"].map(short)
    elif L == 2:
        u["name"] = u[key].map(cod_names[2])
        u["name_src"] = np.where(u["name"].notna(), "KATOTTG codifier / manual", None)
        m = u["name"].isna()
        u.loc[m, "name"] = u.loc[m, key].map(own_name[2])
        u.loc[m & u["name"].notna(), "name_src"] = "own level-2 row"
        m = u["name"].isna()
        u.loc[m, "name"] = u.loc[m, "oblast_uk"] + ", район " + u.loc[m, key].str[2:]
        u.loc[m, "name_src"] = "oblast fallback"
        u["label"] = u["name"].map(short)
        u["k2"] = u[key]
    else:
        u["centre"] = u[key].map(s001)
        m = u["centre"].isna()
        u.loc[m, "centre"] = u.loc[m, key].map(first_settl)
        u["name"] = u[key].map(cod_names[3])
        u["name_src"] = np.where(u["name"].notna(), "KATOTTG codifier", None)
        m = u["name"].isna()
        u.loc[m, "name"] = u.loc[m, key].map(own_name[3]).str.replace(r"\s+за винятком.*$", "", regex=True)
        u.loc[m & u["name"].notna(), "name_src"] = "own level-3 row"
        m = u["name"].isna()
        u.loc[m, "name"] = u.loc[m, "centre"]
        u.loc[m & u["name"].notna(), "name_src"] = "centre settlement"
        m = u["name"].isna()
        u.loc[m, "name"] = u.loc[m, "oblast_uk"]
        u.loc[m, "name_src"] = "oblast fallback"
        u["label"] = u["centre"].where(u["centre"].notna(), u["name"].map(short))
        u["k2"] = u[key].str[:4]
        u["k3"] = u[key]
        u["n_settlements"] = u[key].map(n_settl).fillna(0).astype(int)
    u["unit_id"] = u[key]
    u["pseudo"] = (L >= 2) & (u[key].str[2:4] == "00")
    ps = u["pseudo"]
    city = ps & u["k1"].isin(["80", "85"])
    zone = ps & ~u["k1"].isin(["80", "85"])
    u.loc[city, "kod"] = u.loc[city, "k1"].map(own_kod[1])
    u.loc[city, "name"] = u.loc[city, "k1"].map(own_name[1])
    u.loc[city, "name_src"] = "special-status city"
    u.loc[zone, "name"] = ZONE_NAME
    u.loc[zone, "name_src"] = "oblast-subordinated territory (no raion)"
    u.loc[ps, "label"] = u.loc[ps, "name"].str.replace(r"\s*\(.*\)", "", regex=True)
    u["area_km2"] = (u.geometry.area / 1e6).round(2)
    cols = ["unit_id", "kod", "level", "name", "label", "name_src", "pseudo", "k1", "oblast_en", "oblast_uk"]
    if L >= 2: cols.append("k2")
    if L == 3: cols += ["k3", "centre", "n_settlements", "geom_src"]
    cols += ["area_km2", "geometry"]
    return gpd.GeoDataFrame(u[cols], geometry="geometry", crs=UA_LAEA)

units = {"oblast": attach_names(obl, 1, "k1"),
         "raion": attach_names(rai, 2, "k2"),
         "hromada": attach_names(hro, 3, "k3")}

for lvl, u in units.items():
    print(f"\n{lvl}: {len(u)} units; name_src counts: {u['name_src'].value_counts(dropna=False).to_dict()}")
    if lvl != "oblast":
        miss = u[~u["name_src"].str.startswith("KATOTTG") & (u["k1"] != "01")]
        print(miss[["unit_id", "name", "label", "name_src", "oblast_en", "area_km2"]].to_string())

cov = units["oblast"].set_index("k1")[["oblast_en", "area_km2"]].rename(columns={"area_km2": "obl_km2"})
cov["hrom_km2"] = units["hromada"].groupby("k1")["area_km2"].sum()
cov["n_raion"] = units["raion"].groupby("k1").size()
cov["n_hrom"] = units["hromada"].groupby("k1").size()
cov["gap_hrom_%"] = (100 * (1 - cov["hrom_km2"] / cov["obl_km2"])).round(1)
print(f"\ntotal area: {units['oblast']['area_km2'].sum():,.0f} km2; max hromada gap: {cov['gap_hrom_%'].max()}% ({cov['gap_hrom_%'].idxmax()})")

def with_coords(c):
    c["x_laea"] = c.geometry.x.round(1)
    c["y_laea"] = c.geometry.y.round(1)
    ll = c.to_crs(4326)
    c["lon"] = ll.geometry.x.round(5)
    c["lat"] = ll.geometry.y.round(5)
    return c

for lvl, u in units.items():
    u.to_file(UNITS_GPKG, layer=lvl, driver="GPKG")
    base = u.drop(columns="geometry")
    cen = gpd.GeoDataFrame(base.copy(), geometry=u.geometry.centroid, crs=UA_LAEA)
    cen["inside"] = cen.geometry.within(u.geometry).values
    cen["centre_kind"] = "centroid"
    rep = gpd.GeoDataFrame(base.copy(), geometry=u.representative_point(), crs=UA_LAEA)
    rep["centre_kind"] = "inside"
    best = cen.copy()
    out = ~best["inside"]
    best.loc[out, "geometry"] = rep.loc[out, "geometry"]
    best["centre_kind"] = np.where(best["inside"], "centroid", "inside")
    with_coords(cen).to_file(CENTRES_GPKG, layer=f"{lvl}_centroid", driver="GPKG")
    with_coords(rep).to_file(CENTRES_GPKG, layer=f"{lvl}_inside", driver="GPKG")
    with_coords(best).to_file(CENTRES_GPKG, layer=f"{lvl}_centre", driver="GPKG")
    print(f"{lvl}: centroids outside their polygon: {out.sum()} of {len(cen)} -> inside point used in {lvl}_centre")

print(f"\ndone in {time.time()-t0:.0f}s")
