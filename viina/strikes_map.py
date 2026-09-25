import pandas as pd, geopandas as gpd, zipfile, glob
import matplotlib.pyplot as plt

# --- load events
frames = []
for z in sorted(glob.glob("event_1pd_latest_*.zip")):
    with zipfile.ZipFile(z) as zf:
        name = [n for n in zf.namelist() if n.endswith(".csv")][0]
        frames.append(pd.read_csv(zf.open(name), low_memory=False))
ev = pd.concat(frames, ignore_index=True)
ev["date"] = pd.to_datetime(ev["date"].astype(str), format="%Y%m%d")
ev["month"] = ev["date"].dt.to_period("M")

# --- Russian strike events: strike type, Russia involved, Ukraine not the initiator
strike_cols = ["t_airstrike_b", "t_uav_b", "t_artillery_b", "t_aad_b"]
is_strike = ev[strike_cols].fillna(0).sum(axis=1) > 0
st = ev[is_strike & (ev["a_rus_b"] == 1) & (ev["a_ukr_init_b"].fillna(0) != 1)].copy()
print(f"{len(st):,} Russian strike events, {st.date.min().date()} to {st.date.max().date()}")
print(st["GEO_PRECISION"].value_counts(), "\n")

# --- settlement-precision subset for mapping (drops rows geocoded only to oblast/raion capital)
stp = st[st["GEO_PRECISION"].isin(["ADM3", "STREET"])]
print(f"{len(stp):,} at settlement precision\n")

# --- monthly counts by oblast (all precisions), saved
by_month = st.pivot_table(index="month", columns="ADM1_NAME", values="event_id_1pd",
                          aggfunc="count", fill_value=0)
by_month.to_csv("strikes_by_month_oblast.csv")
print(by_month.tail(6).T.sort_values(by_month.index[-2], ascending=False).head(12))

# --- per-settlement totals
last12 = stp[stp["date"] >= stp["date"].max() - pd.DateOffset(months=12)]
per_place = (stp.groupby("geonameid").size().rename("n_all").to_frame()
             .join(last12.groupby("geonameid").size().rename("n_12m")).fillna(0))

# --- join to tessellation, add population-normalised rate
tess = gpd.read_file("gn_UA_tess.geojson")[["geonameid", "asciiname", "ADM1_NAME", "population", "geometry"]]
g = tess.merge(per_place, left_on="geonameid", right_index=True, how="left").fillna({"n_all": 0, "n_12m": 0})
g["pop"] = pd.to_numeric(g["population"], errors="coerce")
g["rate_12m"] = (g["n_12m"] / g["pop"] * 10_000).where(g["pop"] >= 1000)   # events per 10k, min pop 1000
g.to_file("strikes_by_settlement.gpkg", driver="GPKG")

# --- maps: grey background, classify only settlements with events
fig, axes = plt.subplots(1, 3, figsize=(21, 7))
panels = [("n_all", "Strike events, Feb 2022 – present"),
          ("n_12m", "Strike events, last 12 months"),
          ("rate_12m", "Last 12 months per 10,000 residents (pop ≥ 1,000)")]
for ax, (col, title) in zip(axes, panels):
    g.plot(color="#eeeeee", edgecolor="none", ax=ax)
    sub = g[g[col] > 0]
    sub.plot(column=col, ax=ax, cmap="OrRd", scheme="fisherjenks", k=6, legend=True, edgecolor="none")
    ax.set_title(title); ax.set_axis_off()
plt.tight_layout(); plt.savefig("strikes_map.png", dpi=150)

# --- top settlements
print("\nTop 15 settlements, last 12 months:")
print(g.nlargest(15, "n_12m")[["asciiname", "ADM1_NAME", "n_12m", "n_all", "pop", "rate_12m"]].to_string(index=False))
print("wrote strikes_by_month_oblast.csv, strikes_by_settlement.gpkg, strikes_map.png")
