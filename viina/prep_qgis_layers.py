#!/usr/bin/env python3
"""
prep_qgis_layers.py (v2) — run inside the GEODATA venv, from the viina/ folder.

Replaces the earlier strikes_map.py / risk_index.py / prep_qgis_layers.py chain.
Adds:  * "Ukrainian-controlled on the event date" filter from VIINA control_latest_*.zip
       * H3 res-5 national risk index and res-7 Carpathian/Lviv zoom index
Writes to qgis/:
  ukraine_outline.gpkg, oblasts.gpkg, strikes_by_settlement.gpkg,
  strike_points_12m.gpkg, risk_index_h3r5.gpkg, risk_index_west_h3r7.gpkg
"""
import glob, zipfile, re, unicodedata, os
import pandas as pd, geopandas as gpd, h3
from shapely.geometry import Polygon

OUT = "qgis"; os.makedirs(OUT, exist_ok=True)
STRIKE_COLS = ["t_airstrike_b", "t_uav_b", "t_artillery_b", "t_aad_b"]
WEST_BBOX = (22.0, 47.7, 26.6, 50.8)   # lon/lat: Lviv, Ivano-Frankivsk, Zakarpattia, Chernivtsi, Ternopil

def read_zip_csv(z, **kw):
    with zipfile.ZipFile(z) as zf:
        name = [n for n in zf.namelist() if n.endswith(".csv")][0]
        return pd.read_csv(zf.open(name), low_memory=False, **kw)

# ---------------------------------------------------------------- 1. events
ev = pd.concat([read_zip_csv(z) for z in sorted(glob.glob("event_1pd_latest_*.zip"))], ignore_index=True)
ev["date"] = pd.to_datetime(ev["date"].astype(str), format="%Y%m%d")
is_strike = ev[STRIKE_COLS].fillna(0).sum(axis=1) > 0
st = ev[is_strike & (ev["a_rus_b"] == 1) & (ev["a_ukr_init_b"].fillna(0) != 1)].copy()
st = st.dropna(subset=["geonameid"])
st["geonameid"] = st["geonameid"].astype("int64")
print(f"{len(st):,} candidate Russian strike events")

# ---------------------------------------------------------------- 2. control status on event date
need_ids = set(st["geonameid"].unique())
ctrl_parts = []
for z in sorted(glob.glob("control_latest_*.zip")):
    with zipfile.ZipFile(z) as zf:
        name = [n for n in zf.namelist() if n.endswith(".csv")][0]
        for chunk in pd.read_csv(zf.open(name), usecols=["geonameid", "date", "status"], chunksize=2_000_000):
            ctrl_parts.append(chunk[chunk["geonameid"].isin(need_ids)])
    print("  read", z)
ctrl = pd.concat(ctrl_parts, ignore_index=True).dropna(subset=["geonameid"])
ctrl["geonameid"] = ctrl["geonameid"].astype("int64")
ctrl["date"] = pd.to_datetime(ctrl["date"].astype(int).astype(str), format="%Y%m%d")
ctrl = ctrl.sort_values(["geonameid", "date"]).drop_duplicates(["geonameid", "date"], keep="last")
print(f"  {len(ctrl):,} control rows for {ctrl.geonameid.nunique():,} places")

# nearest control record on or before the event date, per place
st = st.sort_values("date")
st = pd.merge_asof(st, ctrl.sort_values("date").rename(columns={"date": "ctrl_date"}),
                   left_on="date", right_on="ctrl_date", by="geonameid", direction="backward")
print("  control status of strike events:\n" + st["status"].value_counts(dropna=False).to_string())

# keep events in Ukrainian-controlled places; unknown status (no control record) kept unless in Crimea
keep = (st["status"] == "UA") | (st["status"].isna() & (st["ADM1_NAME"] != "Crimea"))
st = st[keep].copy()
END = st["date"].max(); START12 = END - pd.DateOffset(months=12)
print(f"{len(st):,} events in Ukrainian-controlled places, to {END.date()}")

# ---------------------------------------------------------------- 3. settlement-precision subset, points
stp = st[st["GEO_PRECISION"].isin(["ADM3", "STREET"])].copy()

# drop likely geocoding artefacts: tiny places (or unknown pop) hit only by single-report events
tess_pop = gpd.read_file("gn_UA_tess.geojson")[["geonameid", "population"]]
tess_pop["population"] = pd.to_numeric(tess_pop["population"], errors="coerce").fillna(0)
stp = stp.merge(tess_pop, on="geonameid", how="left")
artefact = (stp["population"] < 2000) & (stp["n_reports"] <= 1)
print(f"  dropping {artefact.sum():,} single-report events in places < 2,000 pop")
stp = stp[~artefact].drop(columns=["population"]).copy()

def strike_type(r):
    if r.get("t_airstrike_b", 0) == 1: return "airstrike/missile"
    if r.get("t_uav_b", 0) == 1:       return "UAV"
    if r.get("t_artillery_b", 0) == 1: return "artillery"
    return "air defence engagement"
pts = stp[stp["date"] >= START12].copy()
pts["strike_type"] = pts.apply(strike_type, axis=1)
pts["date_str"] = pts["date"].dt.strftime("%Y-%m-%d")
gpd.GeoDataFrame(pts[["event_id_1pd", "date_str", "asciiname", "ADM1_NAME", "strike_type", "n_reports", "GEO_PRECISION"]],
                 geometry=gpd.points_from_xy(pts["longitude"], pts["latitude"]), crs="EPSG:4326"
                 ).to_file(f"{OUT}/strike_points_12m.gpkg", driver="GPKG")
print(f"  points 12m: {len(pts):,}")

# ---------------------------------------------------------------- 4. settlements
tess = gpd.read_file("gn_UA_tess.geojson")
last12 = stp[stp["date"] >= START12]
per_place = (stp.groupby("geonameid").size().rename("n_all").to_frame()
             .join(last12.groupby("geonameid").size().rename("n_12m")).fillna(0))
g = tess[["geonameid", "asciiname", "ADM1_NAME", "population", "geometry"]].merge(
        per_place, left_on="geonameid", right_index=True, how="left").fillna({"n_all": 0, "n_12m": 0})
g["pop"] = pd.to_numeric(g["population"], errors="coerce")
g["rate_12m"] = (g["n_12m"] / g["pop"] * 10_000).where(g["pop"] >= 1000)
g.drop(columns=["population"]).to_file(f"{OUT}/strikes_by_settlement.gpkg", driver="GPKG")

st.to_pickle(f"{OUT}/strike_events_filtered.pkl")     # all Russian strikes in UA-controlled places
stp.to_pickle(f"{OUT}/strike_events_settlement.pkl")  # ADM3/STREET precision, single-report <2k pop dropped

# ---------------------------------------------------------------- 5. oblasts + outline + air-raid hours
obl = tess[["ADM1_NAME", "geometry"]].dissolve(by="ADM1_NAME", as_index=False)
obl["geometry"] = obl.buffer(0)
obl.dissolve()[["geometry"]].to_file(f"{OUT}/ukraine_outline.gpkg", driver="GPKG")
obl = obl.merge(st.groupby("ADM1_NAME").size().rename("strikes_all"), left_on="ADM1_NAME", right_index=True, how="left") \
         .merge(st[st["date"] >= START12].groupby("ADM1_NAME").size().rename("strikes_12m"), left_on="ADM1_NAME", right_index=True, how="left")

ar = pd.read_csv("../air_raid/official_data_en.csv")
ar = ar[ar["level"] == "oblast"].dropna(subset=["finished_at"]).copy()
ar["started_at"] = pd.to_datetime(ar["started_at"], utc=True); ar["finished_at"] = pd.to_datetime(ar["finished_at"], utc=True)
ar["hours"] = (ar["finished_at"] - ar["started_at"]).dt.total_seconds() / 3600
ar12 = ar[ar["started_at"] >= pd.Timestamp(START12, tz="UTC")].copy()

def stem(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"(autonomous republic of |oblast|city|'|`|ʼ)", "", s)
    s = re.sub(r"(ska|s'ka|ivs|yi|iy|a|ia)$", "", s.strip())
    return re.sub(r"[^a-z]", "", s)[:5]
OVERRIDE = {"kyiv": "Kiev City", "kyiv city": "Kiev City", "kyivska oblast": "Kiev", "odeska oblast": "Odessa",
            "sumska oblast": "Sumy",
            "zakarpatska oblast": "Transcarpathia", "sevastopol": "Sevastopol City",
            "autonomous republic of crimea": "Crimea", "zaporizka oblast": "Zaporizhzhya",
            "vinnytska oblast": "Vinnytsya", "khmelnytska oblast": "Khmel'nyts'kyy"}
by_stem = {stem(n): n for n in obl["ADM1_NAME"]}
ar12["ADM1_NAME"] = ar12["oblast"].map(lambda n: OVERRIDE.get(str(n).strip().lower(), by_stem.get(stem(n))))
um = sorted(ar12.loc[ar12["ADM1_NAME"].isna(), "oblast"].unique())
if um: print("  WARNING unmatched oblast names:", um)
obl = obl.merge(ar12.groupby("ADM1_NAME").agg(alert_hours_12m=("hours", "sum"), alert_count_12m=("hours", "size")),
                left_on="ADM1_NAME", right_index=True, how="left")
for c in ["strikes_all", "strikes_12m", "alert_hours_12m", "alert_count_12m"]:
    obl[c] = obl[c].fillna(0).round(1)
obl.to_file(f"{OUT}/oblasts.gpkg", driver="GPKG")

# ---------------------------------------------------------------- 6. H3 risk indices
def h3_index(df, res, half_life_days=182.5):
    d = df.copy()
    d["w"] = 0.5 ** ((END - d["date"]).dt.days / half_life_days)
    d["h3"] = [h3.latlng_to_cell(la, lo, res) for la, lo in zip(d["latitude"], d["longitude"])]
    agg = d.groupby("h3").agg(n_all=("w", "size"),
                              n_12m=("date", lambda x: (x >= START12).sum()),
                              score=("w", "sum")).reset_index()
    agg["score_idx"] = (100 * agg["score"] / agg["score"].max()).round(1)
    polys = [Polygon([(lon, lat) for lat, lon in h3.cell_to_boundary(h)]) for h in agg["h3"]]
    return gpd.GeoDataFrame(agg, geometry=polys, crs="EPSG:4326")

h3_index(stp, 5).to_file(f"{OUT}/risk_index_h3r5.gpkg", driver="GPKG")
w = WEST_BBOX
west = stp[(stp.longitude.between(w[0], w[2])) & (stp.latitude.between(w[1], w[3]))]
h3_index(west, 7).to_file(f"{OUT}/risk_index_west_h3r7.gpkg", driver="GPKG")
print(f"  west (Carpathian) events: {len(west):,} all, {(west.date >= START12).sum():,} last 12 m")
print(west[west.date >= START12].groupby("asciiname").size().sort_values(ascending=False).head(10).to_string())
print("done ->", os.path.abspath(OUT))
