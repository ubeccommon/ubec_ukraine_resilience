#!/usr/bin/env python3
"""
35_sphere_layers.py — map layer for the three-sphere pages (maps 21–24): sphere indices per hromada with rule R3,
national quintile classes and the threefold-balance colour.

  python 35_sphere_layers.py          (after 32_sphere_indices.py and 28_frontline_zone.py; venv)

Inputs: units_hromada.gpkg (layer hromada: k1, k2, k3, name, geometry), tidy/sphere_indices_k3.csv,
  tidy/sphere_indices_r3_raion.csv (population-weighted values of every raion touched by the zone, whole raion),
  tidy/frontline_zone_k3.csv.
Output: resilience_maps.gpkg layer hromada_spheres_r3 — non-occupied hromadas outside the zone (r3 = 0) and, rule R3,
  one dissolved polygon per raion for the zone hromadas carrying the raion values (r3 = 1). Fields per sphere s in
  econ, rights, cult and year y in 2021, 2025: s_y (index), s_y_q (quintile class "1".."5" or "na"); tern_y (hex colour
  of the balance), dom_y (dominant sphere).
  tidy/sphere_classes.json — quintile limits (for the legend labels) and the balance-colour parameters.
  ../viina/qgis/ternary_legend.png — triangle legend of the balance colours (not tracked; the builder places it).

Classes: quintiles of each index among non-occupied hromadas (national); raion values are classed with the same
limits, so colours mean the same inside and outside the zone.

Balance colour (centred ternary scheme, after Schöley 2021): the weights (w_econ, w_rights, w_cult) = each index /
sum of the three are centred on the national compositional mean of the year (closure of the geometric means) and
expressed in isometric log-ratio coordinates. Hue = direction of the departure (HUE: economic orange, cultural green,
rights blue; between two vertices the hue runs along the arc that avoids the third); chroma and lightness = size of
the departure, scaled to R_MAX = the 95th percentile of the departures of both years pooled (the top 5 % reach full
colour; the same scale in 2021 and 2025). Neutral = light grey. Colours in CIE LCh. The balance says nothing about the
level: a hromada low in all three spheres can be balanced. (Version of 28 Sep 2026; the first draft mixed three
vertex colours in CIELAB and gave muddy mid-tones.)
"""
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
TIDY = BASE / "tidy"
UNITS = BASE / "units_hromada.gpkg"
MAPS = BASE / "resilience_maps.gpkg"
LAYER = "hromada_spheres_r3"
CLASSES = TIDY / "sphere_classes.json"
LEGEND_PNG = BASE.parent / "viina" / "qgis" / "ternary_legend.png"
SPH = ("econ", "rights", "cult")
YEARS = (2021, 2025)
HUE = {"econ": 55.0, "cult": 150.0, "rights": 255.0}      # CIE LCh hue angles: orange, green, blue
C_MAX, L_NEUTRAL, L_FULL = 52.0, 80.0, 60.0                 # chroma at full departure; lightness neutral -> full
R_Q = 0.95                                                  # departure scale: this quantile reaches full colour
LABEL = {"econ": "economic", "rights": "rights", "cult": "cultural"}


def zf(df):
    for c, n in (("k1", 2), ("k2", 4), ("k3", 7)):
        if c in df:
            df[c] = df[c].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(n)
    return df


# ------------------------------------------------------------ colour
def _srgb_to_lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _lin_to_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, 12.92 * c, 1.055 * c ** (1 / 2.4) - 0.055)


M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
WHITE = M @ np.ones(3)


def hex_to_lab(h):
    rgb = np.array([int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)])
    xyz = M @ _srgb_to_lin(rgb) / WHITE
    f = np.where(xyz > (6 / 29) ** 3, np.cbrt(xyz), xyz / (3 * (6 / 29) ** 2) + 4 / 29)
    return np.array([116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2])])


def lab_to_hex(lab):
    L, a, b = lab[..., 0], lab[..., 1], lab[..., 2]
    fy = (L + 16) / 116
    f = np.stack([fy + a / 500, fy, fy - b / 200], axis=-1)
    xyz = np.where(f > 6 / 29, f ** 3, 3 * (6 / 29) ** 2 * (f - 4 / 29)) * WHITE
    rgb = _lin_to_srgb(xyz @ np.linalg.inv(M).T)
    rgb = np.round(rgb * 255).astype(int)
    return np.array(["#%02x%02x%02x" % tuple(v) for v in rgb.reshape(-1, 3)]).reshape(rgb.shape[:-1])


def closure(p):
    return p / p.sum(axis=-1, keepdims=True)


def centre_of(W):
    g = np.exp(np.nanmean(np.log(W), axis=0))
    return g / g.sum()


def ilr(p):
    """isometric log-ratio coordinates of 3-part compositions (econ, rights, cult)."""
    l = np.log(p)
    return np.stack([np.sqrt(0.5) * (l[..., 0] - l[..., 1]),
                     np.sqrt(2 / 3) * (0.5 * (l[..., 0] + l[..., 1]) - l[..., 2])], axis=-1)


def departure(W, centre):
    z = ilr(closure(W / centre))
    return np.hypot(z[:, 0], z[:, 1]), np.arctan2(z[:, 1], z[:, 0])


def _vertex_angles():
    eps = 1e-3
    V = closure(np.full((3, 3), eps) + np.eye(3))
    z = ilr(V)
    return np.arctan2(z[:, 1], z[:, 0])


VANG = _vertex_angles()                   # direction of each pure sphere (same for any centre)
VHUE = np.array([HUE[s] for s in SPH])


def hue_of(theta):
    """piecewise-linear hue between the vertex directions; each arc avoids the third vertex hue."""
    order = np.argsort(VANG)
    a = VANG[order]; h = VHUE[order]
    out = np.empty_like(theta)
    for k in range(3):
        a0, a1 = a[k], a[(k + 1) % 3] + (2 * np.pi if k == 2 else 0)
        h0, h1, hc = h[k], h[(k + 1) % 3], h[(k + 2) % 3]
        d = (h1 - h0) % 360
        if 0 < (hc - h0) % 360 < d:        # the upward arc would pass the third vertex: go the other way
            d -= 360
        th = np.where(theta < a[0], theta + 2 * np.pi, theta)
        m = (th >= a0) & (th < a1)
        out[m] = (h0 + (th[m] - a0) / (a1 - a0) * d) % 360
    return out


def lch_to_hex(L, C, H):
    lab = np.stack([L, C * np.cos(np.radians(H)), C * np.sin(np.radians(H))], axis=-1)
    return lab_to_hex(lab)


def tern_colour(W, centre, r_max):
    """W: (n, 3) compositions (may contain NaN rows) -> hex colours ('' for NaN rows)."""
    out = np.full(len(W), "", dtype=object)
    ok = np.isfinite(W).all(axis=1) & (W > 0).all(axis=1)
    if ok.any():
        r, th = departure(W[ok], centre)
        f = np.clip(r / r_max, 0, 1)
        out[ok] = lch_to_hex(L_NEUTRAL - (L_NEUTRAL - L_FULL) * f, C_MAX * f, hue_of(th))
    return out


# ------------------------------------------------------------ legend
def legend_png(centre, r_max, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon

    n = 60
    V = np.array([[0.0, 0.0], [1.0, 0.0], [0.5, np.sqrt(3) / 2]])   # econ bottom-left, rights bottom-right, cult top
    fig, ax = plt.subplots(figsize=(2.6, 2.6), dpi=300)
    for i in range(n):
        for j in range(n - i):
            for up in (True, False):
                if up:
                    tri = [(i, j), (i + 1, j), (i, j + 1)]
                else:
                    if i + j + 2 > n:
                        continue
                    tri = [(i + 1, j), (i + 1, j + 1), (i, j + 1)]
                bary = np.array([[1 - (a + b) / n, a / n, b / n] for a, b in tri])
                c = bary.mean(axis=0)[None, :]
                col = tern_colour(closure(np.clip(c, 1e-6, None)), centre, r_max)[0]
                xy = bary @ V
                ax.add_patch(Polygon(xy, closed=True, facecolor=col, edgecolor=col, linewidth=0.2))
    cx = centre @ V
    ax.plot(*cx, marker="o", ms=3, mfc="none", mec="#222222", mew=0.6)
    ax.annotate("national\naverage", cx, xytext=(cx[0] + 0.12, cx[1] + 0.02), fontsize=5.5,
                arrowprops=dict(arrowstyle="-", lw=0.4, color="#222222"))
    for k, s in enumerate(SPH):
        x, y = V[k]
        ax.text(x + (-0.04 if k == 0 else 0.04 if k == 1 else 0), y + (-0.07 if k < 2 else 0.04),
                f"{LABEL[s]}\nweighs more", ha="center", va="top" if k < 2 else "bottom", fontsize=6)
    ax.set_xlim(-0.15, 1.15); ax.set_ylim(-0.2, 1.0); ax.set_aspect("equal"); ax.axis("off")
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight", transparent=True)
    plt.close(fig)


# ------------------------------------------------------------ main
def classify(v, lim):
    v = pd.to_numeric(v, errors="coerce")
    c = pd.Series(np.digitize(v, lim) + 1, index=v.index).astype(str)
    return c.where(v.notna(), "na")


def main():
    g = zf(gpd.read_file(UNITS, layer="hromada", engine="pyogrio"))[["k1", "k2", "k3", "name", "geometry"]]
    si = zf(pd.read_csv(TIDY / "sphere_indices_k3.csv", dtype={"k1": str, "k2": str, "k3": str}))
    r3 = zf(pd.read_csv(TIDY / "sphere_indices_r3_raion.csv", dtype={"k1": str, "k2": str}))
    zone = zf(pd.read_csv(TIDY / "frontline_zone_k3.csv", dtype=str))
    zset = set(zone.loc[zone["zone"] == "1", "k3"])

    si["occupied"] = si["occupied"].astype(str).str.lower().isin(["true", "1"])
    free = si[~si["occupied"]].copy()
    cols = [f"{s}_{y}" for y in YEARS for s in SPH]
    lims = {c: [float(x) for x in free[c].quantile([0.2, 0.4, 0.6, 0.8])] for c in cols}

    centre, deps = {}, []
    for y in YEARS:
        W = free[[f"w_{s}_{y}" for s in SPH]].to_numpy(float)
        W = W[np.isfinite(W).all(axis=1) & (W > 0).all(axis=1)]
        centre[y] = centre_of(W)
        deps.append(departure(W, centre[y])[0])
    r_max = float(np.quantile(np.concatenate(deps), R_Q))

    def attach(df):
        for c in cols:
            df[f"{c}_q"] = classify(df[c], lims[c])
        for y in YEARS:
            W = df[[f"w_{s}_{y}" for s in SPH]].to_numpy(float)
            df[f"tern_{y}"] = tern_colour(W, centre[y], r_max)
            dom = pd.Series(np.nan, index=df.index, dtype=object)
            full = np.isfinite(W).all(axis=1)
            dom[full] = np.array(SPH)[np.argmax(W[full], axis=1)]
            df[f"dom_{y}"] = dom.fillna("na")
        return df

    keep = ["k1", "k2", "k3", "name"] + cols + [f"w_{s}_{y}" for y in YEARS for s in SPH]
    out_h = g.merge(attach(free.copy())[keep + [f"{c}_q" for c in cols] + [f"tern_{y}" for y in YEARS]
                                         + [f"dom_{y}" for y in YEARS]].drop(columns=["k1", "k2", "name"]),
                    on="k3", how="inner")
    in_zone = out_h["k3"].isin(zset)
    outside = out_h[~in_zone].assign(r3=0)

    zp = out_h[in_zone][["k2", "geometry"]].dissolve(by="k2", as_index=False)
    rv = attach(r3.copy())
    zp = zp.merge(rv, on="k2", how="left", validate="1:1")
    zp["k3"], zp["name"], zp["r3"] = "", "raion value (R3)", 1
    zp = zp[[c for c in outside.columns if c in zp.columns]]
    lay = gpd.GeoDataFrame(pd.concat([outside, zp], ignore_index=True), geometry="geometry", crs=g.crs)
    lay.to_file(MAPS, layer=LAYER, driver="GPKG", engine="pyogrio")
    print(f"wrote {MAPS.name}:{LAYER}: {len(outside)} hromadas outside the zone + {len(zp)} raion zone parts "
          f"(replacing {int(in_zone.sum())} hromadas); crs {lay.crs.to_string()[:20]}")
    for c in cols:
        print(f"  {c}: limits {np.round(lims[c], 3).tolist()}  classes {lay[f'{c}_q'].value_counts().sort_index().to_dict()}")
    for y in YEARS:
        print(f"  balance {y}: national centre (econ, rights, cult) = {np.round(centre[y], 3).tolist()}; "
              f"dominant {lay[f'dom_{y}'].value_counts().to_dict()}")

    CLASSES.write_text(json.dumps({"quintile_limits": lims, "balance_centre": {str(k): v.tolist() for k, v in centre.items()},
                                   "r_max": r_max, "r_quantile": R_Q, "hue": HUE, "chroma_max": C_MAX,
                                   "lightness": [L_NEUTRAL, L_FULL]}, indent=1), encoding="utf-8")
    print(f"  departure scale r_max = {r_max:.3f} (quantile {R_Q} of both years pooled)")
    legend_png(centre[2025], r_max, LEGEND_PNG)
    print(f"wrote {CLASSES.name} and {LEGEND_PNG} (legend drawn with the 2025 centre)")


if __name__ == "__main__":
    main()
