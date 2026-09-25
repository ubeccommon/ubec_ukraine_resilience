#!/usr/bin/env python3
"""
13_bivariate.py — map layers for resilience v1.1 (data side; QGIS wiring comes separately)

  python 13_bivariate.py

Layers written to resilience_maps.gpkg (UA_LAEA, COD-AB polygons, all 1,763 hromadas):
  hromada_bivariate   exposure tercile x capacity tercile (3x3), two exposure variants:
                        bv_str  — strikes since 2022 (log1p count)
                        bv_alt  — air-raid alert hours, last 12 months
                      codes "EC" (E = exposure 1..3, C = capacity 1..3), "occ" occupied, "na" no data
  (same layer)        recovery_q (1..5, lit-pixel night-light recovery), engagement_q (DREAM),
                      carp (1 = Ivano-Frankivsk, Zakarpattia, Lviv, Chernivtsi oblasts),
                      bv_carp — alert hours x capacity with terciles computed WITHIN the four
                      Carpathian oblasts (regional classes; "out" elsewhere)
Styles (QGIS .qml, categorised): styles/bv_str.qml, styles/bv_alt.qml, styles/bv_carp.qml,
  styles/recovery_q.qml (build_qgis_project.py styles the layers itself; the .qml files are for manual use)
Legend table: tidy/bivariate_legend.csv
Exposure terciles: if >= 1/3 of units have zero strikes, class 1 = zero strikes and classes
  2/3 split the non-zero units at their median; otherwise plain terciles.
Terciles are computed among non-occupied hromadas only.
"""
from pathlib import Path
from xml.sax.saxutils import escape

import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio

BASE = Path(__file__).resolve().parent
QGIS = BASE.parent / "viina" / "qgis"
TIDY, LOGS, STY = BASE / "tidy", BASE / "logs", BASE / "styles"
for d in (TIDY, LOGS, STY):
    d.mkdir(parents=True, exist_ok=True)
UNITS = BASE / "units_hromada.gpkg"
OUT = BASE / "resilience_maps.gpkg"
CARP = {"26", "21", "46", "73"}
# Stevens 3x3 bivariate palette: rows = exposure (low->high), cols = capacity (low->high)
PAL = {"11": "#e8e8e8", "12": "#ace4e4", "13": "#5ac8c8",
       "21": "#dfb0d6", "22": "#a5add3", "23": "#5698b9",
       "31": "#be64ac", "32": "#8c62aa", "33": "#3b4994",
       "occ": "#bdbdbd", "na": "#ffffff"}
LBL_E = {"1": "low exposure", "2": "medium exposure", "3": "high exposure"}
LBL_C = {"1": "low capacity", "2": "medium capacity", "3": "high capacity"}
REC_PAL = {"1": "#d7191c", "2": "#fdae61", "3": "#ffffbf", "4": "#a6d96a", "5": "#1a9641",
           "occ": "#bdbdbd", "na": "#ffffff"}
_logf = open(LOGS / "13_bivariate.log", "w", encoding="utf-8")


def log(*a):
    m = " ".join(str(x) for x in a)
    print(m, flush=True)
    _logf.write(m + "\n")
    _logf.flush()


def terciles(s):
    s = pd.to_numeric(s, errors="coerce")
    ok = s.notna()
    out = pd.Series(pd.NA, index=s.index, dtype="object")
    if ok.sum() == 0:
        return out
    zero_share = (s[ok] == 0).mean()
    if zero_share >= 1 / 3:
        pos = s[ok & (s > 0)]
        med = pos.median()
        out[ok & (s == 0)] = "1"
        out[ok & (s > 0) & (s <= med)] = "2"
        out[ok & (s > med)] = "3"
        log(f"  {s.name}: {zero_share:.0%} zeros -> class 1 = zero, split non-zero at median {med:.3f}")
    else:
        q = pd.qcut(s[ok].rank(method="first"), 3, labels=["1", "2", "3"])
        out[ok] = q.astype(str)
        cuts = s[ok].quantile([1 / 3, 2 / 3]).round(3).tolist()
        log(f"  {s.name}: terciles at {cuts}")
    return out


def quintiles(s):
    s = pd.to_numeric(s, errors="coerce")
    out = pd.Series(pd.NA, index=s.index, dtype="object")
    ok = s.notna()
    out[ok] = pd.qcut(s[ok].rank(method="first"), 5, labels=["1", "2", "3", "4", "5"]).astype(str)
    return out


def hex_rgba(h):
    h = h.lstrip("#")
    return f"{int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},255"


def write_qml(path, attr, cats):
    """cats: list of (value, label, hex colour) -> categorised fill renderer."""
    c_xml, s_xml = [], []
    for i, (val, lab, col) in enumerate(cats):
        c_xml.append(f'<category value="{escape(val)}" symbol="{i}" label="{escape(lab)}" render="true"/>')
        s_xml.append(
            f'<symbol type="fill" name="{i}" alpha="1" clip_to_extent="1" force_rhr="0">'
            f'<layer class="SimpleFill" enabled="1" locked="0" pass="0"><Option type="Map">'
            f'<Option name="color" type="QString" value="{hex_rgba(col)}"/>'
            f'<Option name="outline_color" type="QString" value="255,255,255,255"/>'
            f'<Option name="outline_style" type="QString" value="solid"/>'
            f'<Option name="outline_width" type="QString" value="0.05"/>'
            f'<Option name="outline_width_unit" type="QString" value="MM"/>'
            f'<Option name="style" type="QString" value="solid"/>'
            f'</Option></layer></symbol>')
    xml = ("<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>\n"
           '<qgis version="3.40" styleCategories="Symbology">\n'
           f'<renderer-v2 type="categorizedSymbol" attr="{attr}" symbollevels="0" '
           'enableorderby="0" forceraster="0">\n'
           "<categories>\n" + "\n".join(c_xml) + "\n</categories>\n"
           "<symbols>\n" + "\n".join(s_xml) + "\n</symbols>\n"
           "</renderer-v2>\n</qgis>\n")
    path.write_text(xml, encoding="utf-8")
    log(f"wrote {path.relative_to(BASE)}")


def main():
    g = gpd.read_file(UNITS, layer="hromada")[["k1", "k2", "k3", "name", "geometry"]]
    g["k3"] = g["k3"].astype(str).str.zfill(7)
    ctrl = pyogrio.read_dataframe(QGIS / "hromada_control.gpkg", layer="hromada_control",
                                  read_geometry=False)[["k3", "occupied"]]
    ctrl["k3"] = ctrl["k3"].astype(str).str.zfill(7)
    idx = pd.read_csv(TIDY / "resilience_index_v11_k3.csv", dtype={"k1": str, "k2": str, "k3": str})
    idx["k3"] = idx["k3"].str.zfill(7)
    keep = [c for c in ("capacity_index", "recovery_index", "engagement_index", "exp_strikes_log",
                        "alert_h_12m", "dream_per10k", "garrison_flag") if c in idx]
    d = g.merge(ctrl, on="k3", how="left").merge(idx[["k3"] + keep], on="k3", how="left")
    occ = d["occupied"].astype(str).str.lower().isin(["true", "1"])
    d["carp"] = d["k1"].isin(CARP).astype(int)

    free = ~occ
    log("tercile / quintile cut points (non-occupied):")
    cap_t = pd.Series(pd.NA, index=d.index, dtype="object")
    cap_t[free] = terciles(d.loc[free, "capacity_index"].rename("capacity_index"))
    d["cap_t"] = cap_t
    for name, col in (("str", "exp_strikes_log"), ("alt", "alert_h_12m")):
        if col not in d:
            continue
        et = pd.Series(pd.NA, index=d.index, dtype="object")
        et[free] = terciles(d.loc[free, col].rename(col))
        d[f"exp_t_{name}"] = et
        code = (et.astype("string") + d["cap_t"].astype("string"))
        code = code.where(et.notna() & d["cap_t"].notna(), "na")
        code[occ] = "occ"
        d[f"bv_{name}"] = code.astype(str)
        d[f"bv_{name}_col"] = d[f"bv_{name}"].map(PAL)
    # regional terciles for the Carpathian zoom
    cf = free & (d["carp"] == 1)
    if cf.sum() >= 9 and "alert_h_12m" in d:
        log(f"regional terciles (Carpathian, n={int(cf.sum())}):")
        ec = terciles(d.loc[cf, "alert_h_12m"].rename("alert_h_12m (carp)"))
        cc = terciles(d.loc[cf, "capacity_index"].rename("capacity_index (carp)"))
        d["exp_t_carp"], d["cap_t_carp"] = pd.NA, pd.NA
        d.loc[cf, "exp_t_carp"], d.loc[cf, "cap_t_carp"] = ec, cc
        code = (d["exp_t_carp"].astype("string") + d["cap_t_carp"].astype("string"))
        code = code.where(d["exp_t_carp"].notna() & d["cap_t_carp"].notna(), "na")
        code[d["carp"] != 1] = "out"
        code[occ] = "occ"
        d["bv_carp"] = code.astype(str)
    for col, qn in (("recovery_index", "recovery_q"), ("engagement_index", "engagement_q")):
        q = pd.Series(pd.NA, index=d.index, dtype="object")
        q[free] = quintiles(d.loc[free, col])
        q = q.fillna("na")
        q[occ] = "occ"
        d[qn] = q.astype(str)

    d = d.drop(columns=["occupied"]).assign(occupied=occ.astype(int))
    d.to_file(OUT, layer="hromada_bivariate", driver="GPKG", engine="pyogrio")
    log(f"wrote {OUT.name}:hromada_bivariate ({len(d)} polygons, crs {d.crs.to_string()[:30]})")

    # counts per class, national and Carpathian
    for name in ("str", "alt", "carp"):
        col = f"bv_{name}"
        if col not in d:
            continue
        nat = d[col].value_counts()
        car = d.loc[d["carp"] == 1, col].value_counts()
        tab = pd.DataFrame({"national": nat, "carpathian": car}).fillna(0).astype(int)
        tab = tab.reindex([k for k in PAL if k in tab.index])
        log(f"\n{col} class counts:\n" + tab.T.to_string())

    # legend + styles
    rows = []
    for e in "123":
        for c in "123":
            rows.append({"code": e + c, "exposure": LBL_E[e], "capacity": LBL_C[c], "colour": PAL[e + c]})
    rows += [{"code": "occ", "exposure": "occupied", "capacity": "", "colour": PAL["occ"]},
             {"code": "na", "exposure": "no data", "capacity": "", "colour": PAL["na"]}]
    leg = pd.DataFrame(rows)
    leg.to_csv(TIDY / "bivariate_legend.csv", index=False)
    cats = [(r.code, f"{r.exposure} · {r.capacity}".strip(" ·"), r.colour) for r in leg.itertuples()]
    for name in ("str", "alt", "carp"):
        if f"bv_{name}" in d:
            write_qml(STY / f"bv_{name}.qml", f"bv_{name}", cats)
    rq = [(str(i), f"recovery quintile {i}" + (" (lowest)" if i == 1 else " (highest)" if i == 5 else ""),
           REC_PAL[str(i)]) for i in range(1, 6)]
    rq += [("occ", "occupied", REC_PAL["occ"]), ("na", "no data / too few lit pixels", REC_PAL["na"])]
    write_qml(STY / "recovery_q.qml", "recovery_q", rq)

    vk = d[d["k3"] == "2602003"]
    if len(vk):
        log("\nVerkhovyna: " + ", ".join(f"{c}={vk.iloc[0][c]}" for c in
                                          ["cap_t", "exp_t_str", "bv_str", "bv_alt", "bv_carp", "recovery_q", "engagement_q", "carp"]
                                          if c in vk))


if __name__ == "__main__":
    main()
