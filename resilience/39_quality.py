#!/usr/bin/env python3
"""
39_quality.py — step 1 of the pattern-language round (docs/pattern_language.md, section 7): the observation set.

  python 39_quality.py                    default: quartile cut, variant raw (see below)
  python 39_quality.py --cut 3            tercile cut instead of quartiles
  python 39_quality.py --variant spheres  flags from residuals that hold the 2021 sphere indices constant
  python 39_quality.py --reliable-light   light families only where tr_light_reliable (>= 30 pixels, noise <= 0.35)
  python 39_quality.py --no-lisa          skip the LISA step (esda/libpysal not installed)

"The spatial data without a name": a hromada has the quality when it held up under the same oblast conditions as
its neighbours and the models cannot say why from what they already contain. Operationally, its within-oblast
residual is high on more than one outcome family. Five families, each a residual of

    z(y) ~ z(controls) + oblast fixed effects            (sphere_common.ols_hc1, HC1 as 36/37)

  s24     y_s24    = log(light kept in June–July 2024 / H2 2023)        controls: exp, c_logpop, c_loglit, c_rad21
  recent  y_recent = log(recent light level, 2020–21 = 1)               controls: as s24
  econ    ll_econ_2025  like-for-like economic rank (as 37)            controls: ll_econ_2021, exp, c_logpop
  cult    ll_cult_2025  like-for-like cultural rank (as 37)            controls: ll_cult_2021, exp, c_logpop
  own     log(mean own_gf_rel 2024 Q1 – 2025 Q4 / mean 2022 Q4 – 2023 Q3)   controls: exp, c_logpop
          (own revenue relative to 2021 and to the national median, before and after military PIT left local
          budgets in Q4 2023; needs tidy/budget_quarterly_k3.csv from 20, local)
  variant 'raw' (default) controls for exposure, population and light conditions only: the residual keeps the
  pre-war standing of the spheres, so the configurations behind holding up can still be seen in the profile.
  variant 'spheres' adds econ_2021, rights_2021, cult_2021 to every family's controls: what the pre-war indices do
  not explain either — but it also removes the linear part of every pre-war condition before the profile is
  compared (first run, 28 Sep 2026: near-zero gaps on all 2021 variables by construction). Both residual sets are
  written (res_<f> with the spheres, res0_<f> without); the flags follow the chosen variant.
  --reliable-light: the two light families are set to NaN where tr_light_reliable is 0 (first run: 62 % of the
  held-up had reliable light against 46 % of the faltered — noisy light pushes small hromadas to the bottom).

Two populations, fitted separately (context pattern: the zone is a boundary): non-occupied hromadas outside the
30 km zone (28), and the 196 zone hromadas. Light families use the >= 10 lit-pixel sample of 22 (tr_* present);
tr_light_reliable is carried for checks.

Rule (7.1): held_up = residual in the top quarter (or third, --cut 3) of its population on >= 2 families and in the
bottom quarter on none; faltered = the reverse; middle = everything else with >= 2 families; na = < 2 families.
composite = mean of the available standardised residuals (z within population).

Also here, because it is cheap (7.3, method 1): the plain comparison. For every profile variable, the share of
held-up and of faltered hromadas above the median of their own oblast, and the group medians. The profile has two
parts: CONDITIONS — pre-war (2021) sphere inputs (32), 2020 election contestation, schools 2021 (34), population
2020, hromada type, balance 2021, Carpathian flag — and CONSEQUENCES — the 2025 inputs, DREAM, schools 2026,
balance 2025, modelled population change. The econ and cult families are built from the 2025 inputs, so the
consequences describe what holding up looks like, not what precedes it; only the conditions are candidates for a
pattern. Exposure is a control, listed with the consequences for reference.

LISA (KNN 6, as 36) on the composite, non-zone population: where the quality clusters, the configuration behind it
is probably regional (oblast row); where it is scattered, hromada-level.

Outputs
  tidy/quality_k3.csv          LOCAL (gitignored: holds hromada-level residuals of recent light, rule R2): one row
                               per non-occupied hromada — residuals, quartiles, flags, composite, LISA class
  tidy/quality_summary.json    counts per class and population, cut points, Moran's I, sample sizes — public
  tidy/quality_profile.csv     plain comparison: variable, group, n, share_above_oblast_median, median — public
                               (groups < 5 suppressed; no light values)
  resilience_maps.gpkg         layer hromada_quality (class; zone hromadas as "zone", occupied as "occ") — local
  logs/39_quality.log
Caveats: residuals inherit every limitation of the models (16.1–16.14 of the paper); the light families use a
window that ends after PUB_END, so quality_k3.csv stays local and the public files carry no hromada light value.
"""
import argparse
import importlib
import json
import sys
import time
import warnings

import numpy as np
import pandas as pd

from sphere_common import (BASE, CARP, SPH, TIDY, UNITS, lisa, load_base, log, ols_hc1, open_log, rd,
                           reliable_light, z)

warnings.simplefilter("ignore", pd.errors.PerformanceWarning)
OUT = TIDY / "quality_k3.csv"
OUT_S = TIDY / "quality_summary.json"
OUT_P = TIDY / "quality_profile.csv"
MAPS = BASE / "resilience_maps.gpkg"
FAM = ("s24", "recent", "econ", "cult", "own")
MIN_N = 5
MIN_FIT = 50
COMMON = {
    "econ": [("pdfo_civ_pc_2021", "pdfo_civ_pc_2025"), ("single_tax_pc_2021", "single_tax_pc_2025"),
             ("property_tax_pc_2021", "property_tax_pc_2025")],
    "rights": [("transfer_dep_civ_2021", "transfer_dep_civ_2025"), ("capex_share_2021", "capex_share_2325"),
               ("social_pc_2021", "social_pc_2025")],
    "cult": [("culture_arts_pc_2021", "culture_arts_pc_2025"), ("education_pc_2021", "education_pc_2025"),
             ("extracurricular_pc_2021", "extracurricular_pc_2025")],
}
PROFILE_SKIP = {"k1", "k2", "k3", "name", "occupied"}


def htype(name):
    n = str(name).lower()
    if "міськ" in n:
        return "city"
    if "селищ" in n:
        return "settlement"
    if "сільськ" in n:
        return "village"
    return "other"


def like_for_like(d):
    """Like-for-like sphere ranks as 37_why_there.py: percentile ranks of the indicators measured in both years
    (transform, direction and winsorising of 32), mean of >= 2 of 3."""
    sys.path.insert(0, str(BASE))
    s32 = importlib.import_module("32_sphere_indices")
    spec = {}
    for (s, yr), sp in s32.SPHERES.items():
        spec.update(sp)
    R = s32.ranks(d, spec, pd.Series(True, index=d.index))
    out = {}
    for s, items in COMMON.items():
        for yr, pos in ((2021, 0), (2025, 1)):
            cols = [it[pos] for it in items if it[pos] in R]
            M3 = R[cols]
            out[f"ll_{s}_{yr}"] = M3.mean(axis=1).where(M3.notna().sum(axis=1) >= 2)
    return pd.DataFrame(out, index=d.index)


def own_retention():
    """log(mean own_gf_rel 2024 Q1 – 2025 Q4) − log(mean own_gf_rel 2022 Q4 – 2023 Q3) per hromada, from 20."""
    bq = rd("budget_quarterly_k3.csv", required=False)
    if bq is None:
        return None
    bq["t"] = bq["year"].astype(int) + (bq["q"].astype(int) - 1) / 4
    v = pd.to_numeric(bq["own_gf_rel"], errors="coerce")
    before = bq[(bq["t"] >= 2022.75) & (bq["t"] < 2023.75)].assign(v=v).groupby("k3")["v"]
    after = bq[(bq["t"] >= 2024.0) & (bq["t"] < 2026.0)].assign(v=v).groupby("k3")["v"]
    b = before.mean().where(before.count() >= 3)
    a = after.mean().where(after.count() >= 5)
    r = np.log(a.where(a > 0)) - np.log(b.where(b > 0))
    log(f"own-revenue retention: {int(r.notna().sum())} hromadas with >= 3 quarters before and >= 5 after the break")
    return r.rename("y_own")


def resid(d, ycol, extra):
    """Residual of z(y) ~ z(extra) + oblast FE on the rows where everything is present; NaN elsewhere."""
    yv = pd.to_numeric(d[ycol], errors="coerce")
    ok = yv.notna() & np.isfinite(yv)
    for c in extra:
        v = pd.to_numeric(d[c], errors="coerce")
        ok &= v.notna() & np.isfinite(v)
    s = d[ok]
    out = pd.Series(np.nan, index=d.index)
    if len(s) < MIN_FIT:
        log(f"  {ycol}: n={len(s)} too small, skipped")
        return out, len(s), np.nan
    Xd = pd.DataFrame({c: z(s[c]) for c in extra}, index=s.index)
    D = pd.get_dummies(s["k1"], prefix="ob", drop_first=True, dtype=float)
    Xd = pd.concat([Xd, D.loc[:, D.std() > 0]], axis=1)
    Xd = Xd.loc[:, Xd.std() > 0]
    Xd.insert(0, "const", 1.0)
    yz = z(yv[ok]).values
    b, se, e = ols_hc1(yz, Xd.values.astype(float))
    r2 = 1 - (e @ e) / (yz @ yz)
    out[s.index] = e
    log(f"  {ycol:14s} n={len(s):5d}  R2={r2:.3f}  controls={','.join(extra)}")
    return out, len(s), r2


def quantile_class(x, n):
    """1 = lowest … n = highest; NaN stays NaN."""
    r = x.rank(pct=True)
    return np.ceil(r * n).clip(1, n).where(x.notna())


def main():
    ap = argparse.ArgumentParser(description="pattern-language step 1: the observation set")
    ap.add_argument("--cut", type=int, default=4, choices=(3, 4), help="quantile cut: 4 quartiles (default) or 3 terciles")
    ap.add_argument("--variant", default="raw", choices=("raw", "spheres"),
                    help="residuals without the 2021 sphere indices (default) or given them")
    ap.add_argument("--reliable-light", action="store_true",
                    help="light families only where tr_light_reliable (>= 30 lit pixels, noise <= 0.35)")
    ap.add_argument("--no-lisa", action="store_true", help="skip LISA")
    a = ap.parse_args()
    open_log("39_quality")
    t0 = time.time()
    log(f"39_quality.py  {time.strftime('%Y-%m-%d %H:%M')}  cut={a.cut}  variant={a.variant}  "
        f"reliable_light={'yes' if a.reliable_light else 'no'}")

    # ---- data ------------------------------------------------------------------------------------------
    d = load_base()
    inp = rd("sphere_inputs_k3.csv")
    d = d.merge(inp.drop(columns=[c for c in ("k1", "k2") if c in inp]), on="k3", how="left")
    d = pd.concat([d, like_for_like(d)], axis=1)
    own = own_retention()
    d["y_own"] = d["k3"].map(own) if own is not None else np.nan
    sc = rd("schools_k3.csv", required=False)
    if sc is not None:
        keep = [c for c in ("schools_suspended_2026", "schools_mountain_2026",
                            "class_size_2021", "pupils_per1000_2021") if c in sc]
        sc["rural_school_share"] = pd.to_numeric(sc.get("schools_rural_2026"), errors="coerce") / \
            pd.to_numeric(sc.get("schools_2026"), errors="coerce").where(lambda v: v > 0)
        d = d.merge(sc[["k3"] + keep + ["rural_school_share"]], on="k3", how="left",
                    suffixes=("", "_sc"))
    pop = rd("population_k3.csv", required=False)
    if pop is not None:
        pop["pop_change"] = np.log(pd.to_numeric(pop["pop_ghs_2025"], errors="coerce") /
                                   pd.to_numeric(pop["pop_ghs_2020"], errors="coerce").where(lambda v: v > 0))
        d = d.merge(pop[["k3", "pop_change"]], on="k3", how="left")
    d["htype"] = d["name"].map(htype)
    for t in ("city", "settlement", "village"):
        d[f"is_{t}"] = (d["htype"] == t).astype(float)
    d["carp"] = d["k1"].isin(CARP).astype(float)
    d["light_reliable"] = reliable_light(d).astype(int)
    d["pop"] = np.where(d["in_zone"], "zone", "outside")
    has_light = "y_s24" in d
    if not has_light:
        log("no light trajectories (22): families s24 and recent skipped")
    elif a.reliable_light:
        unrel = d["light_reliable"] == 0
        d.loc[unrel, ["y_s24", "y_recent"]] = np.nan
        log(f"reliable light only: {int(unrel.sum())} hromadas without reliable light drop out of the light families")

    # ---- residuals, per population and variant ----------------------------------------------------------
    ctrl_light = ["exp", "c_logpop", "c_loglit", "c_rad21"]
    sph21 = [f"{s}_2021" for s in SPH]
    fams = {
        "s24": ("y_s24", ctrl_light), "recent": ("y_recent", ctrl_light),
        "econ": ("ll_econ_2025", ["ll_econ_2021", "exp", "c_logpop"]),
        "cult": ("ll_cult_2025", ["ll_cult_2021", "exp", "c_logpop"]),
        "own": ("y_own", ["exp", "c_logpop"]),
    }
    fit_n = {}
    for pop_lab in ("outside", "zone"):
        sub = d[d["pop"] == pop_lab]
        log(f"\n== population: {pop_lab}  n={len(sub)}")
        for variant, add in (("res", sph21), ("res0", [])):
            log(f"-- {variant}: {'with' if add else 'without'} the 2021 sphere indices")
            for f, (ycol, ctrl) in fams.items():
                col = f"{variant}_{f}"
                if col not in d:
                    d[col] = np.nan
                if ycol not in d or d.loc[sub.index, ycol].notna().sum() == 0:
                    log(f"  {ycol}: not available, skipped")
                    fit_n[f"{pop_lab}_{variant}_{f}"] = 0
                    continue
                e, n, r2 = resid(sub, ycol, ctrl + add)
                d.loc[e.index, col] = e.values
                fit_n[f"{pop_lab}_{variant}_{f}"] = {"n": int(n), "r2": None if not np.isfinite(r2) else round(float(r2), 3)}

    # ---- classes ---------------------------------------------------------------------------------------
    pre = "res" if a.variant == "spheres" else "res0"
    n = a.cut
    for f in FAM:
        d[f"q_{f}"] = np.nan
    d["composite"] = np.nan
    for pop_lab in ("outside", "zone"):
        m = d["pop"] == pop_lab
        zs = []
        for f in FAM:
            x = pd.to_numeric(d.loc[m, f"{pre}_{f}"], errors="coerce")
            d.loc[m, f"q_{f}"] = quantile_class(x, n)
            zs.append(z(x))
        d.loc[m, "composite"] = pd.concat(zs, axis=1).mean(axis=1, skipna=True)
    Q = d[[f"q_{f}" for f in FAM]]
    d["n_families"] = Q.notna().sum(axis=1)
    d["n_top"] = (Q == n).sum(axis=1)
    d["n_bottom"] = (Q == 1).sum(axis=1)
    d["quality"] = np.select(
        [d["n_families"] < 2,
         (d["n_top"] >= 2) & (d["n_bottom"] == 0),
         (d["n_bottom"] >= 2) & (d["n_top"] == 0)],
        ["na", "held_up", "faltered"], default="middle")
    log("\n== are the families one quality? rank correlations of the residuals (outside the zone)")
    R5 = d.loc[d["pop"] == "outside", [f"{pre}_{f}" for f in FAM]].apply(pd.to_numeric, errors="coerce")
    R5.columns = list(FAM)
    corr = R5.corr(method="spearman")
    log(corr.round(2).to_string())
    off = corr.values[np.triu_indices(len(FAM), 1)]
    log(f"mean off-diagonal correlation {np.nanmean(off):.2f}  (near 0: the families are separate qualities; "
        f"the composite then averages unrelated residuals)")
    Qo = d.loc[d["pop"] == "outside", [f"q_{f}" for f in FAM]]
    hu = d.loc[d["pop"] == "outside", "quality"] == "held_up"
    top = (Qo[hu] == n)
    log("families on which the held-up hromadas are in the top quarter (share of the held-up):")
    log("  " + "  ".join(f"{f}: {top[f'q_{f}'].mean():.2f}" for f in FAM))
    pairs = top.apply(lambda r: "+".join(f for f in FAM if r[f"q_{f}"]), axis=1).value_counts().head(12)
    log("most frequent combinations:\n" + pairs.to_string())
    fam_diag = {"residual_corr": corr.round(3).to_dict(), "mean_offdiag": round(float(np.nanmean(off)), 3),
                "held_up_top_share": {f: round(float(top[f"q_{f}"].mean()), 3) for f in FAM},
                "held_up_combinations": pairs.to_dict()}

    log("\n== classes (rows = population)")
    tab = pd.crosstab(d["pop"], d["quality"])
    log(tab.to_string())
    log(f"families available per hromada: {d['n_families'].value_counts().sort_index().to_dict()}")
    for f in FAM:
        c = f"{pre}_{f}"
        log(f"  {f:7s} residual available: {int(d[c].notna().sum())}")

    # ---- LISA on the composite (non-zone) ---------------------------------------------------------------
    d["lisa_composite"] = ""
    moran = {}
    if not a.no_lisa:
        try:
            s, g, cls, cls_f, cut = lisa(d[(d["pop"] == "outside") & d["composite"].notna()], "composite", "national")
            d.loc[cls.index, "lisa_composite"] = cls
            moran = {"I": round(float(g.I), 3), "p_sim": round(float(g.p_sim), 4), "n": int(len(s)),
                     "classes": cls.value_counts().to_dict(), "classes_fdr": cls_f.value_counts().to_dict()}
            log(f"\nLISA composite (outside zone): Moran's I = {g.I:.3f} (p = {g.p_sim:.4f})  "
                f"classes {cls.value_counts().to_dict()}  after FDR {cls_f.value_counts().to_dict()}")
            for k1 in sorted(CARP):
                cc = cls[s["k1"] == k1].value_counts().to_dict()
                log(f"  Carpathian {k1}: {cc}")
        except Exception as ex:
            log(f"note: LISA skipped ({ex})")

    # ---- plain comparison (7.3, method 1) -----------------------------------------------------------------
    log("\n== plain comparison: share above own-oblast median, held up vs faltered (outside the zone)")
    inputs = [c for c in inp.columns if c not in PROFILE_SKIP]
    cond = [c for c in inputs if c.endswith("_2021") or c.endswith("_2020")]
    cond += [c for c in ("class_size_2021", "pupils_per1000_2021", "pop_ghs_2020", "imbalance_2021",
                         "lean_cult_2021", "lean_econ_rights_2021") if c in d and c not in cond]
    cons = [c for c in inputs if c not in cond]
    cons += [c for c in ("schools_suspended_2026", "rural_school_share", "pop_change", "imbalance_2025",
                         "lean_cult_2025", "lean_econ_rights_2025", "exp", "exp_alert") if c in d and c not in cons]
    binary = [c for c in ("is_city", "is_settlement", "is_village", "carp", "light_reliable") if c in d]
    rows = []
    out = d[d["pop"] == "outside"].copy()
    for part, vs in (("condition", cond), ("consequence", cons)):
        for v in vs:
            x = pd.to_numeric(out[v], errors="coerce")
            med = x.groupby(out["k1"]).transform("median")
            above = (x > med).where(x.notna())
            for grp in ("held_up", "faltered", "middle"):
                m = out["quality"] == grp
                nv = int(x[m].notna().sum())
                rows.append({"part": part, "variable": v, "group": grp, "n": int(m.sum()), "n_valid": nv,
                             "share_above_oblast_median": float(above[m].mean()) if nv >= MIN_N else np.nan,
                             "median": float(x[m].median()) if nv >= MIN_N else np.nan})
    for v in binary:
        x = pd.to_numeric(out[v], errors="coerce")
        for grp in ("held_up", "faltered", "middle"):
            m = out["quality"] == grp
            nv = int(x[m].notna().sum())
            rows.append({"part": "structure", "variable": v, "group": grp, "n": int(m.sum()), "n_valid": nv,
                         "share_above_oblast_median": np.nan,
                         "median": float(x[m].mean()) if nv >= MIN_N else np.nan})
    P = pd.DataFrame(rows)
    P.to_csv(OUT_P, index=False)
    for part, vs in (("condition", cond), ("consequence", cons)):
        wide = P[P["part"] == part].pivot_table(index="variable", columns="group",
                                                values="share_above_oblast_median", sort=False)
        wide = wide.reindex(vs)
        if {"held_up", "faltered"} <= set(wide.columns):
            wide["gap"] = wide["held_up"] - wide["faltered"]
            wide = wide.sort_values("gap", ascending=False)
        title = ("CONDITIONS (pre-war and structural: candidates for a pattern)" if part == "condition"
                 else "CONSEQUENCES (2025 values, part of what defines the quality: not conditions)")
        log(f"\n-- {title}\n" + wide.round(3).to_string())
    log("\nshares of hromada type, Carpathian and reliable light by group:")
    log(P[P["part"] == "structure"].pivot_table(index="variable", columns="group", values="median",
                                                sort=False).round(3).to_string())
    log(f"wrote {OUT_P.relative_to(BASE)}")

    # ---- outputs ---------------------------------------------------------------------------------------
    cols = ["k1", "k2", "k3", "name", "pop", "in_zone", "carp", "light_reliable", "n_families", "n_top",
            "n_bottom", "quality", "composite", "lisa_composite"] + \
           [f"q_{f}" for f in FAM] + [f"res_{f}" for f in FAM] + [f"res0_{f}" for f in FAM]
    d[cols].sort_values("k3").to_csv(OUT, index=False)
    log(f"wrote {OUT.relative_to(BASE)}  (local: hromada-level light residuals, rule R2)")

    summ = {
        "date": time.strftime("%Y-%m-%d"), "cut": n, "variant": a.variant, "reliable_light": bool(a.reliable_light),
        "rule": f"held_up: top 1/{n} on >= 2 families and bottom 1/{n} on none; faltered: the reverse",
        "families": {f: {"y": fams[f][0], "controls": fams[f][1] + (sph21 if a.variant == "spheres" else [])}
                     for f in FAM},
        "fits": fit_n,
        "classes": {p: d.loc[d["pop"] == p, "quality"].value_counts().to_dict() for p in ("outside", "zone")},
        "n_families": d["n_families"].value_counts().sort_index().to_dict(),
        "carpathian_outside": d.loc[(d["pop"] == "outside") & (d["carp"] == 1), "quality"].value_counts().to_dict(),
        "by_type_outside": {t: d.loc[(d["pop"] == "outside") & (d["htype"] == t), "quality"].value_counts().to_dict()
                            for t in ("city", "settlement", "village")},
        "lisa_composite": moran, "families_diagnostic": fam_diag,
    }
    OUT_S.write_text(json.dumps(summ, ensure_ascii=False, indent=1, default=int), encoding="utf-8")
    log(f"wrote {OUT_S.relative_to(BASE)}")

    # ---- data dictionary (rows qual_*; replaced on every run, as 22) -----------------------------------
    dd_fn = TIDY / "data_dictionary.csv"
    if dd_fn.exists():
        src = "39_quality.py from tidy tables of 22, 32, 28 (and 20 where present)"
        lic = "derived; ODbL 1.0 (inherits upstream terms); quality_k3.csv local under rule R2"
        rows_dd = [
            ("qual_res_<family>", src, lic, "SD", "2021-2026", "hromada",
             f"residual of z(y) ~ z(controls) + oblast FE, fitted separately outside and inside the 30 km zone; "
             f"families s24, recent, econ, cult, own; variant '{a.variant}'"),
            ("qual_quality", src, lic, "class", "", "hromada",
             f"held_up / faltered / middle / na: top 1/{n} on >= 2 families and bottom 1/{n} on none (and the reverse)"),
            ("qual_composite", src, lic, "SD", "", "hromada", "mean of the standardised residuals available"),
            ("qual_lisa_composite", src, lic, "class", "", "hromada", "local Moran class of the composite (KNN 6), outside the zone"),
        ]
        new = pd.DataFrame(rows_dd, columns=["indicator", "source", "licence", "unit", "year", "level", "method"])
        dd = pd.read_csv(dd_fn)
        dd = dd[~dd["indicator"].astype(str).str.startswith("qual_")]
        for col in dd.columns:
            if col not in new:
                new[col] = ""
        pd.concat([dd, new[dd.columns]], ignore_index=True).to_csv(dd_fn, index=False)

    # ---- map layer (local; zone hromadas as 'zone', rule R3; occupied as 'occ') --------------------------
    try:
        import geopandas as gpd
        g = gpd.read_file(UNITS, layer="hromada")[["k3", "geometry"]]
        g["k3"] = g["k3"].astype(str).str.zfill(7)
        cls = d.set_index("k3")["quality"]
        g["quality_cls"] = g["k3"].map(cls).fillna("occ")
        g.loc[g["k3"].isin(d.loc[d["in_zone"], "k3"]), "quality_cls"] = "zone"
        g["composite"] = g["k3"].map(d.set_index("k3")["composite"])
        g.loc[g["quality_cls"].isin(["zone", "occ"]), "composite"] = np.nan
        g["lisa_composite"] = g["k3"].map(d.set_index("k3")["lisa_composite"]).fillna("")
        g.to_file(MAPS, layer="hromada_quality", driver="GPKG")
        log(f"wrote {MAPS.name} layer hromada_quality  {g['quality_cls'].value_counts().to_dict()}")
    except Exception as ex:
        log(f"note: map layer not written ({ex})")

    log(f"\ndone in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
