"""26_publication_tables.py — paper Table 3 (exposure descriptives) and Table 11 (Carpathian vs national).

Run from anywhere with the venv Python.
Inputs : viina/qgis/unit_stats_hromada.csv, viina/qgis/hromada_control.gpkg,
         resilience/tidy/trajectories_k3.csv, resilience/tidy/resilience_v1_k3.csv
Outputs: publication/figures/table03_exposure.{csv,md}, publication/figures/table11_carpathian.{csv,md}

Non-occupied hromadas only. Strikes = settlement-precision events since 24 Feb 2022 (n_all, as used in the
models via exp_strikes_log); because most hromadas have none, the share with at least one event is reported
alongside the distribution. Alert hours = fixed 12-month window 1 Sep 2025 – 31 Aug 2026 (alert_h_12m).
Oblast names are standardised from the VIINA transliteration. All outputs are oblast-level or regional
aggregates (rules R1–R6)."""
from pathlib import Path
import pandas as pd
import pyogrio

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "publication" / "figures"
FIG.mkdir(parents=True, exist_ok=True)
CARP = {"21": "Zakarpattia", "26": "Ivano-Frankivsk", "46": "Lviv", "73": "Chernivtsi"}
NAT = "Ukraine (non-occupied)"
KEYS = {"k1": str, "k2": str, "k3": str}
NAMES = {"Cherkasy": "Cherkasy", "Chernihiv": "Chernihiv", "Chernivtsi": "Chernivtsi",
         "Dnipropetrovs'k": "Dnipropetrovsk", "Donets'k": "Donetsk", "Ivano-Frankivs'k": "Ivano-Frankivsk",
         "Kharkiv": "Kharkiv", "Kherson": "Kherson", "Khmel'nyts'kyy": "Khmelnytskyi", "Kiev": "Kyiv",
         "Kiev City": "Kyiv City", "Kirovohrad": "Kirovohrad", "L'viv": "Lviv", "Luhans'k": "Luhansk",
         "Mykolayiv": "Mykolaiv", "Odessa": "Odesa", "Poltava": "Poltava", "Rivne": "Rivne", "Sumy": "Sumy",
         "Ternopil'": "Ternopil", "Transcarpathia": "Zakarpattia", "Vinnytsya": "Vinnytsia", "Volyn": "Volyn",
         "Zaporizhzhya": "Zaporizhzhia", "Zhytomyr": "Zhytomyr"}


def md_table(df, path, title, note):
    cols = list(df.columns)
    lines = [f"**{title}**", "", "| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    lines += ["| " + " | ".join(str(x) for x in r) + " |" for r in df.itertuples(index=False)]
    lines += ["", note, ""]
    path.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


# --- non-occupied hromadas ------------------------------------------------------------------------
us = pd.read_csv(ROOT / "viina/qgis/unit_stats_hromada.csv", dtype=KEYS)
ctl = pyogrio.read_dataframe(ROOT / "viina/qgis/hromada_control.gpkg", read_geometry=False)[["k3", "occupied"]]
ctl["k3"] = ctl["k3"].astype(str)
d = us.merge(ctl, on="k3", how="left", validate="1:1")
assert d["occupied"].notna().all(), "hromadas without control status"
d = d[~d["occupied"].astype(bool)].copy()
unmapped = sorted(set(d["oblast_en"]) - set(NAMES))
assert not unmapped, f"oblast names without a standard form: {unmapped}"
d["oblast"] = d["oblast_en"].map(NAMES)
print(f"non-occupied hromadas: {len(d):,}")

# --- Table 3: exposure descriptives by oblast -----------------------------------------------------
def desc(g):
    s, a = g["n_all"], g["alert_h_12m"]
    return pd.Series({"hromadas": len(g), "struck_share": 100 * (s > 0).mean(),
                      "strikes_median": s.median(), "strikes_q1": s.quantile(.25), "strikes_q3": s.quantile(.75),
                      "strikes_max": s.max(),
                      "alert_h_median": a.median(), "alert_h_q1": a.quantile(.25), "alert_h_q3": a.quantile(.75),
                      "alert_h_max": a.max()})

t3 = d.groupby("oblast").apply(desc, include_groups=False).sort_index()
t3.loc[NAT] = desc(d)
t3.index.name = "oblast"
t3.round(1).to_csv(FIG / "table03_exposure.csv")

f0 = lambda x: f"{x:,.0f}"
t3md = pd.DataFrame({
    "Oblast": t3.index,
    "Hromadas": t3["hromadas"].map(f0).values,
    "With ≥ 1 strike, %": t3["struck_share"].map(f0).values,
    "Strikes, median": t3["strikes_median"].map(f0).values,
    "Strikes, IQR": [f"{f0(a)}–{f0(b)}" for a, b in zip(t3["strikes_q1"], t3["strikes_q3"])],
    "Strikes, max": t3["strikes_max"].map(f0).values,
    "Alert hours, median": t3["alert_h_median"].map(f0).values,
    "Alert hours, IQR": [f"{f0(a)}–{f0(b)}" for a, b in zip(t3["alert_h_q1"], t3["alert_h_q3"])],
    "Alert hours, max": t3["alert_h_max"].map(f0).values,
})
md_table(t3md, FIG / "table03_exposure.md",
         "Table 3. Exposure of non-occupied hromadas, by oblast",
         "Strikes: VIINA settlement-precision events attributed to Russian forces, 24 Feb 2022 – 19 Sep 2026, per "
         "hromada. Alert hours: hours under air-raid alert, 1 Sep 2025 – 31 Aug 2026 (hromada, raion or oblast "
         "alert; overlaps merged). IQR = interquartile range.")

# --- Table 11: Carpathian vs national -----------------------------------------------------------------
tr = pd.read_csv(ROOT / "resilience/tidy/trajectories_k3.csv", dtype=KEYS)[["k3", "capacity_prewar", "capacity_index"]]
rv = pd.read_csv(ROOT / "resilience/tidy/resilience_v1_k3.csv", dtype=KEYS)[["k3", "ntl_recovery_2124"]]
m = d[["k1", "k3", "n_all", "alert_h_12m"]].merge(tr, on="k3", how="left").merge(rv, on="k3", how="left")
m["struck"] = (m["n_all"] > 0).astype(float)
for c in ("capacity_prewar", "capacity_index"):
    assert m[c].max() <= 1.0, f"{c} not on a 0–1 scale"

# (column, label, statistic, scale, decimals)
MEAS = [("struck", "Hromadas with ≥ 1 strike since 24 Feb 2022, %", "mean", 100, 0),
        ("alert_h_12m", "Alert hours, 1 Sep 2025 – 31 Aug 2026 (median)", "median", 1, 0),
        ("capacity_prewar", "Capacity 2021, mean percentile rank 0–100 (median)", "median", 100, 1),
        ("capacity_index", "Capacity 2025, mean percentile rank 0–100 (median)", "median", 100, 1),
        ("ntl_recovery_2124", "Night-light recovery ratio 2024 / 2021 (median)", "median", 1, 2)]
groups = {**{name: m[m["k1"] == k] for k, name in CARP.items()},
          "Carpathian (4 oblasts)": m[m["k1"].isin(CARP)], NAT: m}

long, wide = [], []
for col, label, stat, scale, dp in MEAS:
    row = {"Measure": label}
    for g, gd in groups.items():
        v = gd[col].dropna()
        val = round(getattr(v, stat)() * scale, dp)
        long.append({"measure": col, "statistic": stat, "group": g, "value": val, "n": len(v)})
        row[g] = f"{val:,.{dp}f} ({len(v):,})"
    wide.append(row)
pd.DataFrame(long).to_csv(FIG / "table11_carpathian.csv", index=False)
md_table(pd.DataFrame(wide), FIG / "table11_carpathian.md",
         "Table 11. Carpathian oblasts and Ukraine, non-occupied hromadas",
         "Number of hromadas with a value in brackets. Capacity: mean percentile rank of the capacity components "
         "(2021 budgets for 2021; 2025 index). Recovery: mean radiance of pixels lit in 2021, 2024 relative to 2021.")

# --- verdict on the paper's three Carpathian claims ---------------------------------------------------
L = pd.DataFrame(long).set_index(["measure", "group"])["value"]
c, n = "Carpathian (4 oblasts)", NAT
yes = lambda b: "yes" if b else "NO"
print("\nclaims (Carpathian vs national):")
print(f"  lower exposure : struck {L['struck', c]} % vs {L['struck', n]} %, alert hours {L['alert_h_12m', c]} vs "
      f"{L['alert_h_12m', n]} -> {yes(L['struck', c] < L['struck', n] and L['alert_h_12m', c] < L['alert_h_12m', n])}")
print(f"  lower capacity : 2021 {L['capacity_prewar', c]} vs {L['capacity_prewar', n]}, 2025 {L['capacity_index', c]} vs "
      f"{L['capacity_index', n]} -> {yes(L['capacity_index', c] < L['capacity_index', n])}")
print(f"  better recovery: region {L['ntl_recovery_2124', c]} vs {L['ntl_recovery_2124', n]} -> "
      f"{yes(L['ntl_recovery_2124', c] > L['ntl_recovery_2124', n])}; by oblast: "
      + ", ".join(f"{g} {L['ntl_recovery_2124', g]}" for g in CARP.values()))
