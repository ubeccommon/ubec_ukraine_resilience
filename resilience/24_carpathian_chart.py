#!/usr/bin/env python3
"""
24_carpathian_chart.py — Figure 1 for the Carpathian brief: monthly night-light index,
median hromada per oblast vs national, Jan 2021 – latest.

  python 24_carpathian_chart.py

Input:  tidy/carpathian_ntl_monthly.csv (23_carpathian.py)
Output: docs/fig1_carpathian_light.png (200 dpi) and .svg
Index = lit-pixel radiance / same calendar month 2020–21 (1 = pre-war); non-occupied
hromadas with >= 10 lit pixels; June 2025 blank (retrieval artefact).
Palette: Okabe–Ito (colour-blind safe); national = dashed grey; names at line ends (no legend).
"""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

BASE = Path(__file__).resolve().parent
IN = BASE / "tidy" / "carpathian_ntl_monthly.csv"
OUT = BASE / "docs" / "fig1_carpathian_light"
SERIES = [("Zakarpattia", "#0072B2"), ("Lviv", "#009E73"), ("Chernivtsi", "#E69F00"),
          ("Ivano-Frankivsk", "#D55E00")]

d = pd.read_csv(IN)
d["date"] = pd.to_datetime(d.iloc[:, 0] + "-15")
d = d[d["date"] >= "2021-01-01"].set_index("date").sort_index()
last = d.index.max()

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})
fig, ax = plt.subplots(figsize=(10, 5.4))
ax.axvspan(pd.Timestamp("2024-06-01"), pd.Timestamp("2024-08-01"), color="#eeeeee", zorder=0)
ax.axhline(1.0, color="#999999", lw=0.8, zorder=1)
ax.axvline(pd.Timestamp("2022-02-24"), color="#555555", lw=0.8, ls=":", zorder=1)
ax.axvline(pd.Timestamp("2022-10-10"), color="#555555", lw=0.8, ls=":", zorder=1)
ax.plot(d.index, d["national"], color="#666666", lw=2.0, ls="--", zorder=2)
ax.annotate("Ukraine", (last, d["national"].dropna().iloc[-1]), xytext=(6, 0), textcoords="offset points",
            color="#666666", fontsize=9, va="center")
for name, col in SERIES:
    if name in d:
        ax.plot(d.index, d[name], color=col, lw=1.8, zorder=3)
        ax.annotate(name, (last, d[name].dropna().iloc[-1]), xytext=(6, 0), textcoords="offset points",
                    color=col, fontsize=9, va="center", fontweight="bold")

ymax = max(1.4, float(d.max().max()) * 1.05)
ax.set_ylim(0, ymax)
ax.set_xlim(pd.Timestamp("2021-01-01"), last + pd.Timedelta(days=150))
for x, txt in [("2022-02-24", "full-scale\ninvasion"), ("2022-10-10", "strikes on\nenergy begin")]:
    ax.text(pd.Timestamp(x) + pd.Timedelta(days=12), ymax * 0.97, txt, fontsize=8, color="#444444", va="top")
ax.text(pd.Timestamp("2024-07-01"), ymax * 0.97, "outage\nsummer\n2024", fontsize=8, color="#444444",
        va="top", ha="center")

ax.set_xticks([pd.Timestamp(f"{y}-01-01") for y in range(2021, last.year + 1)])
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.set_ylabel("Night light vs same month 2020–21 (1 = pre-war)")
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(axis="y", color="#e5e5e5", lw=0.6)
ax.set_title("Four Carpathians: night light in the median hromada, 2021–2026", loc="left",
             fontsize=13, fontweight="bold", pad=12)
fig.text(0.01, 0.01,
         "Monthly lit-pixel radiance of the median non-occupied hromada (≥ 10 lit pixels) relative to the same month "
         "in 2020–21. 2021 lies above 1 because it was\nbrighter than 2020. Single months vary with snow, cloud and "
         "moonlight — read the trend. June 2025 omitted (retrieval artefact). Light also reflects\ncurfews, "
         "street-lighting policy and grid schedules, not only damage. Data: NASA Black Marble VNP46A3 (public domain); "
         "boundaries OCHA COD-AB (CC BY-IGO).",
         fontsize=7, color="#555555", va="bottom")
fig.subplots_adjust(left=0.08, right=0.87, top=0.9, bottom=0.17)
for ext, kw in (("png", {"dpi": 200}), ("svg", {})):
    fig.savefig(f"{OUT}.{ext}", **kw)
    print(f"wrote {OUT.relative_to(BASE)}.{ext}")
