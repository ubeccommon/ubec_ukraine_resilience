import pandas as pd, geopandas as gpd, zipfile, glob, h3, numpy as np
from shapely.geometry import Polygon
import matplotlib.pyplot as plt

frames = []
for z in sorted(glob.glob("event_1pd_latest_*.zip")):
    with zipfile.ZipFile(z) as zf:
        frames.append(pd.read_csv(zf.open([n for n in zf.namelist() if n.endswith(".csv")][0]), low_memory=False))
ev = pd.concat(frames, ignore_index=True)
ev["date"] = pd.to_datetime(ev["date"].astype(str), format="%Y%m%d")

strike_cols = ["t_airstrike_b", "t_uav_b", "t_artillery_b", "t_aad_b"]
st = ev[(ev[strike_cols].fillna(0).sum(axis=1) > 0)
        & (ev["a_rus_b"] == 1) & (ev["a_ukr_init_b"].fillna(0) != 1)
        & ev["GEO_PRECISION"].isin(["ADM3", "STREET"])
        & (ev["ADM1_NAME"] != "Crimea")].copy()          # TODO: replace with control-status filter

# recency weight: half-life 6 months
age_days = (st["date"].max() - st["date"]).dt.days
st["w"] = 0.5 ** (age_days / 182.5)

RES = 5
st["h3"] = [h3.latlng_to_cell(la, lo, RES) for la, lo in zip(st["latitude"], st["longitude"])]
agg = st.groupby("h3").agg(n_all=("w", "size"), n_12m=("date", lambda d: (d >= d.max() - pd.DateOffset(months=12)).sum()),
                           score=("w", "sum")).reset_index()
agg["score_idx"] = (100 * agg["score"] / agg["score"].max()).round(1)   # 0–100, 100 = worst cell

# hex geometries
def hex_poly(h):
    b = h3.cell_to_boundary(h)
    return Polygon([(lon, lat) for lat, lon in b])
hexes = gpd.GeoDataFrame(agg, geometry=[hex_poly(h) for h in agg["h3"]], crs="EPSG:4326")
hexes.to_file("risk_index_h3r5.gpkg", driver="GPKG")

# Ukraine outline from the settlement tessellation for context
outline = gpd.read_file("gn_UA_tess.geojson")[["geometry"]].dissolve()

fig, ax = plt.subplots(figsize=(12, 8))
outline.plot(ax=ax, color="#f2f2f2", edgecolor="#999999", linewidth=0.5)
hexes.plot(column="score_idx", ax=ax, cmap="OrRd", scheme="fisherjenks", k=7, legend=True, alpha=0.9, edgecolor="none")
ax.set_axis_off(); ax.set_title("Russian strike risk index, H3 res 5, 6-month half-life (data to %s)" % st["date"].max().date())
plt.tight_layout(); plt.savefig("risk_index_h3r5.png", dpi=150)

print(hexes.nlargest(10, "score_idx")[["h3", "n_all", "n_12m", "score_idx"]].to_string(index=False))
print("wrote risk_index_h3r5.gpkg, risk_index_h3r5.png")
