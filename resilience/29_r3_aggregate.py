#!/usr/bin/env python3
"""
29_r3_aggregate.py — security rule R3 on the hromada map layers: in the front-line and border zone (28), hromada
values are replaced by raion values.

  python 29_r3_aggregate.py          (after 13_bivariate.py, 22_trajectories.py and 28_frontline_zone.py)

Zone hromadas (tidy/frontline_zone_k3.csv, zone == 1) are dissolved per raion into one polygon (r3 = 1) that carries
the raion value, computed over all non-occupied hromadas of that raion:
  capacity_index, alert_h_12m, exp_strikes_log  population-weighted mean (GHS-POP 2020)
  recovery_index                                lit-pixel-weighted mean (hromadas with a value)
  light (maps 19–20)                            lit-pixel-weighted mean over reliable hromadas only
                                                (tr_light_reliable == 1): tr_recent_pub, tr_h2_23, tr_s24_rel,
                                                tr_noise_sd; change class from the raion z-score
                                                dlog / (noise * sqrt(1/11 + 1/6)) (conservative: pooling lowers
                                                noise); raions without a reliable hromada -> "na"
Raion values are classed with the national hromada thresholds taken from the existing classes (class upper bound =
largest hromada value in the class), so colours mean the same inside and outside the zone. Strike classes keep the
zero rule of 13 (class 1 only if no hromada of the raion was struck).
The trajectory layer carries no raion key; k2 is taken from the bivariate layer by k3.
Outputs: resilience_maps.gpkg layers hromada_bivariate_r3 and hromada_trajectories_r3 (non-zone hromadas unchanged,
r3 = 0; zone parts r3 = 1), tidy/r3_raion_values.csv (raion values and classes for the raions touched by the zone).
"""
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
TIDY = BASE / "tidy"
MAPS = BASE / "resilience_maps.gpkg"
CARP = {"21", "26", "46", "73"}
N_PUB, N_H2 = 11, 6          # months in the publication window (June 2025 excluded) and in H2 2023


def zf(df):
    for c, n in (("k1", 2), ("k2", 4), ("k3", 7)):
        if c in df:
            df[c] = df[c].astype(str).str.zfill(n)
    return df


def wmean(v, w):
    v, w = pd.to_numeric(v, errors="coerce"), pd.to_numeric(w, errors="coerce")
    ok = v.notna() & w.notna() & (w > 0)
    return float(np.average(v[ok], weights=w[ok])) if ok.any() else np.nan


def upper_bounds(val, cls, labels):
    """upper bound of each class except the last = largest value in that class (classes ordered by value)."""
    val, cls = pd.to_numeric(val, errors="coerce"), cls.astype(str)
    ub = [val[cls == c].max() for c in labels[:-1]]
    lo = [val[cls == c].min() for c in labels[1:]]
    assert all(a <= b for a, b in zip(ub, lo)), f"classes overlap: {ub} vs {lo}"
    return ub


def classify(v, ub, labels):
    if pd.isna(v):
        return "na"
    for b, lab in zip(ub, labels):
        if v <= b:
            return lab
    return labels[-1]


def main():
    zone = zf(pd.read_csv(TIDY / "frontline_zone_k3.csv", dtype=str))
    zset = set(zone.loc[zone["zone"] == "1", "k3"])
    base = zf(pd.read_csv(TIDY / "resilience_v1_k3.csv", dtype={"k1": str, "k2": str, "k3": str}))[
        ["k3", "pop_ghs_2020", "ntl_n_lit_px"]]

    # ---------------- bivariate layer (maps 14, 15, 16)
    bv = zf(gpd.read_file(MAPS, layer="hromada_bivariate"))
    bv = bv.merge(base, on="k3", how="left", validate="1:1")
    free = pd.to_numeric(bv["occupied"], errors="coerce").fillna(0).astype(int) == 0
    assert not (bv["k3"].isin(zset) & bv["k1"].isin(CARP)).any(), "zone hromadas in Carpathian oblasts (map 17)"
    f = bv[free]
    L3, L5 = ["1", "2", "3"], ["1", "2", "3", "4", "5"]
    ub_cap = upper_bounds(f["capacity_index"], f["cap_t"], L3)
    ub_alt = upper_bounds(f["alert_h_12m"], f["exp_t_alt"], L3)
    ub_str2 = pd.to_numeric(f.loc[f["exp_t_str"].astype(str) == "2", "exp_strikes_log"]).max()
    ub_rec = upper_bounds(f["recovery_index"], f["recovery_q"], L5)
    print(f"thresholds: capacity {np.round(ub_cap, 3)}, alert h {np.round(ub_alt, 0)}, strikes class 2 <= "
          f"{ub_str2:.3f}, recovery {np.round(ub_rec, 3)}")

    touched = sorted(set(zone.loc[zone["zone"] == "1", "k2"]))
    rows = []
    for k2 in touched:
        d = f[f["k2"] == k2]
        cap = wmean(d["capacity_index"], d["pop_ghs_2020"])
        alt = wmean(d["alert_h_12m"], d["pop_ghs_2020"])
        stl = wmean(d["exp_strikes_log"], d["pop_ghs_2020"])
        rec = wmean(d["recovery_index"], d["ntl_n_lit_px"])
        cap_t, alt_t = classify(cap, ub_cap, L3), classify(alt, ub_alt, L3)
        str_t = "na" if pd.isna(stl) else ("1" if stl == 0 else ("2" if stl <= ub_str2 else "3"))
        rows.append({"k1": d["k1"].iloc[0], "k2": k2, "n_hromadas": len(d), "n_zone": int(d["k3"].isin(zset).sum()),
                     "capacity_index": cap, "alert_h_12m": alt, "exp_strikes_log": stl, "recovery_index": rec,
                     "cap_t": cap_t, "exp_t_alt": alt_t, "exp_t_str": str_t,
                     "bv_alt": alt_t + cap_t if "na" not in (alt_t, cap_t) else "na",
                     "bv_str": str_t + cap_t if "na" not in (str_t, cap_t) else "na",
                     "recovery_q": classify(rec, ub_rec, L5)})
    rv = pd.DataFrame(rows)

    zp = bv[free & bv["k3"].isin(zset)][["k2", "geometry"]].dissolve(by="k2", as_index=False)
    zp = zp.merge(rv, on="k2", how="left", validate="1:1")
    zp["occupied"], zp["carp"], zp["bv_carp"], zp["engagement_q"], zp["r3"] = 0, 0, "out", "na", 1
    keep_bv = bv[~bv["k3"].isin(zset)].drop(columns=["pop_ghs_2020", "ntl_n_lit_px"]).assign(r3=0)
    bv3 = gpd.GeoDataFrame(pd.concat([keep_bv, zp[[c for c in zp.columns if c in keep_bv.columns]]],
                                     ignore_index=True), geometry="geometry", crs=bv.crs)
    bv3.to_file(MAPS, layer="hromada_bivariate_r3", driver="GPKG", engine="pyogrio")
    print(f"hromada_bivariate_r3: {len(keep_bv):,} hromadas outside the zone + {len(zp)} raion zone parts "
          f"(replacing {len(zset)} hromadas)")
    print("  zone parts bv_alt: " + str(zp["bv_alt"].value_counts().sort_index().to_dict()))
    print("  zone parts with bv_alt na: " + str(zp.loc[zp["bv_alt"] == "na", ["k2", "n_hromadas", "cap_t",
                                                                              "exp_t_alt"]].to_dict("records")))

    # ---------------- trajectory layer (maps 19, 20)
    tj = zf(gpd.read_file(MAPS, layer="hromada_trajectories"))
    if "k2" not in tj:
        tj = tj.merge(bv[["k3", "k2"]], on="k3", how="left", validate="1:1")
    assert tj["k2"].notna().all() and (tj["k2"] != "0nan").all(), "hromadas without raion key"
    tj = tj.merge(base[["k3", "ntl_n_lit_px"]], on="k3", how="left", validate="1:1")
    tfree = pd.to_numeric(tj["occupied"], errors="coerce").fillna(0).astype(int) == 0
    rel = tfree & (pd.to_numeric(tj["tr_light_reliable"], errors="coerce") == 1)
    t = tj[rel]
    ub_dark = upper_bounds(-pd.to_numeric(t["tr_recent_pub"]), t["bv_rec_cap_pub"].str[0], L3)
    ub_s24 = upper_bounds(t["tr_s24_rel"], t["s24_q_pub"], L5)
    lrows = []
    for k2 in touched:
        d = t[t["k2"] == k2]
        w = d["ntl_n_lit_px"]
        recent, h2 = wmean(d["tr_recent_pub"], w), wmean(d["tr_h2_23"], w)
        s24, noise = wmean(d["tr_s24_rel"], w), wmean(d["tr_noise_sd"], w)
        if len(d) and recent > 0 and h2 > 0 and noise > 0:
            zc = (np.log(recent) - np.log(h2)) / (noise * np.sqrt(1 / N_PUB + 1 / N_H2))
            chg = "improved" if zc > 2 else ("declined" if zc < -2 else "stable")
        else:
            zc, chg = np.nan, "na"
        cap_t = rv.loc[rv["k2"] == k2, "cap_t"].iloc[0]
        dark = classify(-recent, ub_dark, L3) if pd.notna(recent) else "na"
        lrows.append({"k2": k2, "n_reliable": len(d), "tr_recent_pub": recent, "tr_h2_23": h2, "tr_s24_rel": s24,
                      "tr_noise_sd": noise, "change_z": zc, "chg_cls_pub": chg,
                      "s24_q_pub": classify(s24, ub_s24, L5) if pd.notna(s24) else "na",
                      "bv_rec_cap_pub": dark + cap_t if "na" not in (dark, cap_t) else "na"})
    lv = pd.DataFrame(lrows)
    tzp = tj[tfree & tj["k3"].isin(zset)][["k1", "k2", "geometry"]].dissolve(by="k2", as_index=False)
    tzp = tzp.merge(lv[["k2", "chg_cls_pub", "s24_q_pub", "bv_rec_cap_pub"]], on="k2", how="left", validate="1:1")
    tzp["occupied"], tzp["r3"] = 0, 1
    keep_tj = tj[~tj["k3"].isin(zset)].drop(columns=["ntl_n_lit_px"]).assign(r3=0)
    tj3 = gpd.GeoDataFrame(pd.concat([keep_tj, tzp], ignore_index=True), geometry="geometry", crs=tj.crs)
    tj3.to_file(MAPS, layer="hromada_trajectories_r3", driver="GPKG", engine="pyogrio")
    print(f"hromada_trajectories_r3: {len(keep_tj):,} outside + {len(tzp)} raion zone parts; "
          f"raions without a reliable hromada: {int((lv['n_reliable'] == 0).sum())}")
    print("  zone parts chg_cls_pub: " + str(tzp["chg_cls_pub"].value_counts().to_dict()) +
          "  bv_rec_cap_pub: " + str(tzp["bv_rec_cap_pub"].value_counts().sort_index().to_dict()))

    out = rv.merge(lv, on="k2", how="left")
    out.round(4).to_csv(TIDY / "r3_raion_values.csv", index=False)
    print(f"wrote tidy/r3_raion_values.csv ({len(out)} raions)")


if __name__ == "__main__":
    main()
