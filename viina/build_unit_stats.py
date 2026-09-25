"""Step 2b: attach strike and air-raid statistics to admin units (oblast / raion / hromada).
Inputs : qgis/admin_units.gpkg, qgis/admin_centres.gpkg (<level>_centre), qgis/strike_events_*.pkl,
         ../air_raid/official_data_en.csv + qgis/alert_unit_map.csv, gn_UA_tess.geojson (population)
Outputs: qgis/unit_stats.gpkg  layers <level>_poly (polygons) and <level>_pt (centre points), same columns;
         qgis/unit_stats_<level>.csv
Windows: strikes  = 365 days ending on the last strike event (END);
         alerts   = 365 days ending on the last alert record, capped at END (the alert CSV usually lags the events).
Columns: n_all, n_12m (strike events), rep_all, rep_12m (sum of n_reports), score (recency-weighted, 6-month half-life),
         civcas_all, civcas_12m, last_strike, pop_gn, area_km2, dens_12m (per 1,000 km2), rate_12m (per 100k pop),
         alert_h_12m / alert_h_all   = hours any part of the unit was under alert (union of all alert rows of the unit,
                                       its ancestors and its descendants), alert_n_* = merged alert episodes,
         alert_hp_12m / alert_hp_all = population-weighted mean of the hromada hours inside the unit (== alert_h at hromada level),
         alert_share_12m = alert_hp_12m / hours in the alert window."""
import time
from collections import defaultdict
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd

pd.set_option("display.width", 230); pd.set_option("display.max_columns", 40)
OUT = Path("qgis")
STATS_GPKG = OUT / "unit_stats.gpkg"
if STATS_GPKG.exists():
    STATS_GPKG.unlink()
HALF_LIFE = 182.5
EPOCH = pd.Timestamp("1970-01-01", tz="UTC")
t0 = time.time()

def to_sec(ts):
    ts = pd.to_datetime(ts, utc=True)
    return (ts - EPOCH).dt.total_seconds()

def sec_to_date(s):
    return pd.to_datetime(s, unit="s").date()

# --- units ------------------------------------------------------------------------------
units = {L: gpd.read_file(OUT / "admin_units.gpkg", layer=L, engine="pyogrio") for L in ("oblast", "raion", "hromada")}
centres = {L: gpd.read_file(OUT / "admin_centres.gpkg", layer=f"{L}_centre", engine="pyogrio") for L in units}
CRS = units["hromada"].crs
KEYCOL = {"oblast": "k1", "raion": "k2", "hromada": "k3"}
PREFIX = {"oblast": 2, "raion": 4, "hromada": 7}
hro = units["hromada"]

# --- strike events ----------------------------------------------------------------------
st = pd.read_pickle(OUT / "strike_events_filtered.pkl")      # all precisions (oblast level)
stp = pd.read_pickle(OUT / "strike_events_settlement.pkl")   # ADM3/STREET (raion + hromada level)
END = st["date"].max()
START12 = END - pd.Timedelta(days=365)
print(f"events: all {len(st):,}, settlement-precision {len(stp):,}; strike window 12m = {START12.date()} .. {END.date()}")

def prep(df):
    d = df.copy()
    d["w"] = 0.5 ** ((END - d["date"]).dt.days / HALF_LIFE)
    d["civcas"] = (d["t_civcas_b"].fillna(0) == 1).astype(int) if "t_civcas_b" in d else 0
    d["n_reports"] = d["n_reports"].fillna(1)
    pts = gpd.GeoDataFrame(d, geometry=gpd.points_from_xy(d["longitude"], d["latitude"]), crs="EPSG:4326").to_crs(CRS)
    j = gpd.sjoin(pts, hro[["k3", "geometry"]], how="left", predicate="within")
    j = j[~j.index.duplicated(keep="first")]
    j["k2"] = j["k3"].str[:4]
    j["k1"] = j["k3"].str[:2]
    print(f"  events not inside any hromada polygon: {j['k3'].isna().sum():,}")
    return j.drop(columns=["geometry", "index_right"])

ev_all = prep(st)
ev_set = prep(stp)

def agg_events(df, key, ids):
    out = pd.DataFrame(index=pd.Index(ids, name="unit_id"))
    g = df.dropna(subset=[key]).groupby(key)
    out["n_all"] = g.size()
    out["rep_all"] = g["n_reports"].sum()
    out["score"] = g["w"].sum()
    out["civcas_all"] = g["civcas"].sum()
    out["last_strike"] = g["date"].max().dt.strftime("%Y-%m-%d")
    g12 = df[df["date"] >= START12].dropna(subset=[key]).groupby(key)
    out["n_12m"] = g12.size()
    out["rep_12m"] = g12["n_reports"].sum()
    out["civcas_12m"] = g12["civcas"].sum()
    num = ["n_all", "rep_all", "score", "civcas_all", "n_12m", "rep_12m", "civcas_12m"]
    out[num] = out[num].fillna(0)
    out["score"] = out["score"].round(3)
    return out

# --- population from GeoNames settlement points ---------------------------------------------
gn = gpd.read_file("gn_UA_tess.geojson", engine="pyogrio")[["geonameid", "population", "longitude", "latitude"]]
gn = gpd.GeoDataFrame(gn, geometry=gpd.points_from_xy(gn["longitude"], gn["latitude"]), crs="EPSG:4326").to_crs(CRS)
gj = gpd.sjoin(gn, hro[["k3", "geometry"]], how="inner", predicate="within")
gj = gj[~gj.index.duplicated(keep="first")]
pop3 = gj.groupby("k3")["population"].sum()
print(f"population: {gn['population'].sum():,} in GeoNames, {pop3.sum():,} assigned to hromadas")

# --- air-raid alerts: any-part union over ancestors + descendants ----------------------------------
a = pd.read_csv("../air_raid/official_data_en.csv", dtype=str)
amap = pd.read_csv(OUT / "alert_unit_map.csv", dtype=str)
for c in ("raion", "hromada"):
    a[c] = a[c].fillna(""); amap[c] = amap[c].fillna("")
a = a.merge(amap[["oblast", "raion", "hromada", "level", "k1", "k2", "k3"]], on=["oblast", "raion", "hromada", "level"], how="left")
a["s"] = to_sec(a["started_at"])
a["e"] = to_sec(a["finished_at"])
a = a[a["e"] > a["s"]]
ALERT_START = a["s"].min()
A_END = min(a["e"].max(), to_sec(pd.Series([END + pd.Timedelta(days=1)])).iloc[0])
W12 = (A_END - 365 * 86400, A_END)
WALL = (ALERT_START, A_END)
HOURS12 = (W12[1] - W12[0]) / 3600
print(f"alerts: {len(a):,} rows, {sec_to_date(ALERT_START)} .. {sec_to_date(a['e'].max())}; "
      f"unmapped raion/hromada rows: {((a['level'] == 'raion') & a['k2'].isna()).sum() + ((a['level'] == 'hromada') & a['k3'].isna()).sum()}")
print(f"alert window 12m = {sec_to_date(W12[0])} .. {sec_to_date(W12[1])} "
      f"({(to_sec(pd.Series([END + pd.Timedelta(days=1)])).iloc[0] - A_END) / 86400:.0f} days before the strike window end)")

def arrays(df, key):
    return {k: (g["s"].to_numpy(), g["e"].to_numpy()) for k, g in df.groupby(key)}

A1 = arrays(a[a["level"] == "oblast"], "k1")
A2 = arrays(a[a["level"] == "raion"], "k2")
A3 = arrays(a[a["level"] == "hromada"], "k3")
EMPTY = (np.array([]), np.array([]))
K2_BY_K1, K3_BY_K1, K3_BY_K2 = defaultdict(list), defaultdict(list), defaultdict(list)
for k in A2: K2_BY_K1[k[:2]].append(k)
for k in A3: K3_BY_K1[k[:2]].append(k); K3_BY_K2[k[:4]].append(k)

def parts_for(level, u):
    if level == "hromada":
        return [A1.get(u[:2], EMPTY), A2.get(u[:4], EMPTY), A3.get(u, EMPTY)]
    if level == "raion":
        return [A1.get(u[:2], EMPTY), A2.get(u, EMPTY)] + [A3[k] for k in K3_BY_K2.get(u, [])]
    return [A1.get(u, EMPTY)] + [A2[k] for k in K2_BY_K1.get(u, [])] + [A3[k] for k in K3_BY_K1.get(u, [])]

def union_hours(parts, lo, hi):
    s = np.concatenate([p[0] for p in parts]); e = np.concatenate([p[1] for p in parts])
    s = np.clip(s, lo, hi); e = np.clip(e, lo, hi)
    keep = e > s
    s, e = s[keep], e[keep]
    if len(s) == 0:
        return 0.0, 0
    o = np.argsort(s); s, e = s[o], e[o]
    cm = np.maximum.accumulate(e)
    new = np.r_[True, s[1:] > cm[:-1]]
    idx = np.flatnonzero(new)
    hours = (np.maximum.reduceat(e, idx) - s[idx]).sum() / 3600
    return hours, len(idx)

def alert_any(level, ids):
    rows = []
    for u in ids:
        parts = parts_for(level, u)
        h12, n12 = union_hours(parts, *W12)
        hall, nall = union_hours(parts, *WALL)
        rows.append((u, round(h12, 1), n12, round(hall, 1), nall))
    return pd.DataFrame(rows, columns=["unit_id", "alert_h_12m", "alert_n_12m", "alert_h_all", "alert_n_all"]).set_index("unit_id")

def wmean(hs, n, col):
    """population-weighted mean of hromada column per parent prefix; area-weighted where the parent has no population."""
    key = hs.index.str[:n]
    wp = hs["pop_gn"].astype(float)
    wa = hs["area_km2"].astype(float)
    p = (hs[col] * wp).groupby(key).sum() / wp.groupby(key).sum()
    q = (hs[col] * wa).groupby(key).sum() / wa.groupby(key).sum()
    return p.where(p.notna(), q).round(1)

# --- assemble: hromada first (parents use its alert values) -------------------------------------
results = {}
for L in ("hromada", "raion", "oblast"):
    key = KEYCOL[L]
    u = units[L].set_index("unit_id")
    ev = ev_all if L == "oblast" else ev_set
    stats = agg_events(ev, key, u.index)
    if L == "hromada":
        stats["pop_gn"] = pop3.reindex(u.index).fillna(0).astype(int)
    else:
        stats["pop_gn"] = pop3.groupby(pop3.index.str[:PREFIX[L]]).sum().reindex(u.index).fillna(0).astype(int)
    stats["area_km2"] = u["area_km2"]
    stats["dens_12m"] = (1000 * stats["n_12m"] / stats["area_km2"]).round(3)
    stats["rate_12m"] = np.where(stats["pop_gn"] >= 1000, 1e5 * stats["n_12m"] / stats["pop_gn"].clip(lower=1), np.nan).round(2)
    stats = stats.join(alert_any(L, u.index))
    if L == "hromada":
        stats["alert_hp_12m"] = stats["alert_h_12m"]
        stats["alert_hp_all"] = stats["alert_h_all"]
    else:
        hs = results["hromada"]
        stats["alert_hp_12m"] = wmean(hs, PREFIX[L], "alert_h_12m").reindex(u.index)
        stats["alert_hp_all"] = wmean(hs, PREFIX[L], "alert_h_all").reindex(u.index)
    stats["alert_share_12m"] = (stats["alert_hp_12m"] / HOURS12).round(3)
    results[L] = stats

for L in ("oblast", "raion", "hromada"):
    u = units[L].set_index("unit_id")
    stats = results[L].drop(columns="area_km2")
    poly = u.join(stats).reset_index()
    pt = centres[L].set_index("unit_id").join(stats).reset_index()
    poly.to_file(STATS_GPKG, layer=f"{L}_poly", driver="GPKG")
    pt.to_file(STATS_GPKG, layer=f"{L}_pt", driver="GPKG")
    poly.drop(columns="geometry").to_csv(OUT / f"unit_stats_{L}.csv", index=False)
    print(f"\n{L}: {len(poly)} units; events all={int(stats['n_all'].sum()):,} 12m={int(stats['n_12m'].sum()):,}; "
          f"units with n_12m>0: {(stats['n_12m'] > 0).sum()}; alert_hp_12m max {stats['alert_hp_12m'].max():,.0f} median {stats['alert_hp_12m'].median():,.0f}")
    show = ["label", "oblast_en", "n_all", "n_12m", "score", "civcas_12m", "pop_gn", "rate_12m", "alert_h_12m", "alert_hp_12m", "alert_share_12m"]
    if L == "oblast":
        print(poly[show].sort_values("alert_hp_12m", ascending=False).to_string())
    else:
        print("top 12 by n_12m:")
        print(poly[show].sort_values("n_12m", ascending=False).head(12).to_string())
        print("top 8 by alert_hp_12m:")
        print(poly[show].sort_values("alert_hp_12m", ascending=False).head(8).to_string())
    if L == "hromada":
        m = poly["label"].isin(["Верховина", "Львів", "Косів", "Рахів", "Івано-Франківськ", "Ужгород", "Тернопіль", "Луцьк"]) & (poly["k1"] != "05")
        print("Carpathian / western examples:")
        print(poly.loc[m, show].to_string())

print(f"\nwritten: {STATS_GPKG} (layers <level>_poly, <level>_pt), qgis/unit_stats_<level>.csv")
print(f"done in {time.time()-t0:.0f}s")
