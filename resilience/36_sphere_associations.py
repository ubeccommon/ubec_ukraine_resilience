#!/usr/bin/env python3
"""
36_sphere_associations.py — step 7: how the three spheres go with war exposure, with functional
resilience, with each other, and where they cluster.

  python 36_sphere_associations.py            full run (about 10–20 minutes; wild-cluster intervals included)
  python 36_sphere_associations.py --no-ci    skip the wild-cluster confidence intervals (quicker)
  python 36_sphere_associations.py --B 1999   fewer bootstrap draws (test runs only)

Shared data assembly, models and LISA: sphere_common.py.
Inputs (tidy/): sphere_indices_k3.csv (32), resilience_index_v11_k3.csv (11: exp_strikes_log, alert_h_12m,
  recovery_index), resilience_v1_k3.csv (pop_ghs_2020, ntl_n_lit_px, ntl_2021), trajectories_k3.csv (22:
  tr_s24_rel, tr_recent, tr_noise_sd; optional), frontline_zone_k3.csv (zone flag); units_hromada.gpkg.
Sample: non-occupied hromadas with the variables of each model. Zone hromadas are in the models (the tables
  are national aggregates, rule R3 concerns published hromada values); a sensitivity drops them.

Standardisation and inference (as 12_moderation.py and 22_trajectories.py): y and the focus variables are
  z-scored within each model sample, so b is in standard deviations. HC1 standard errors; oblast fixed effects
  where stated (within-R2 = 1 - SSR / sum of squares of y around its oblast mean). For every focus coefficient:
  restricted wild-cluster bootstrap p by oblast (robust_inference.py: Webb weights, B = 9,999, seed 20260926)
  and Conley spatial-HAC t (Bartlett kernel, 50 and 100 km, representative points in UA_LAEA). Key rows add a
  95 % interval by inverting the wild-cluster test (ci_lo / ci_hi). Moran's I of the residuals: KNN k = 6.

Part A — exposure. y = sphere index (2021 or 2025), x = z(log1p strikes since 2022) (alt: alert hours, 12 m),
  control z(log population 2020).
  A1 2021 level (no FE / FE): where the strikes fell relative to pre-war sphere strength. The strikes come
     after 2021, so this row describes geography and targeting, not an effect on the sphere.
  A2 2025 level (no FE / FE).
  A3 2025 given 2021 (FE, + z(sphere 2021)): did more-exposed hromadas move up or down relative to their
     neighbours in the same oblast. Variants: alert hours; without the frontline oblasts (Donetsk 14,
     Zaporizhzhia 23, Kherson 65); without zone hromadas.
  The same A2/A3 FE rows for the balance measures (see Part D).
Part B — functional resilience. y = recovery_index (11), log summer-2024 light relative to H2 2023
  (tr_s24_rel, 22: higher = smaller outage loss), log recent light level (tr_recent). The spheres are the
  2021 values (before the war; the 2025 values are contemporaneous with the outcomes).
  B1 all three spheres together + exposure + controls (log population, log lit pixels, log 2021 radiance) + FE.
  B1r the same on hromadas with reliable light data (>= 30 lit pixels, pre-war noise_sd <= 0.35), light outcomes.
  B2 one sphere at a time with the sphere x exposure interaction (does the sphere buffer exposure?), as 12.
Part C — spheres against each other. z(a) ~ z(b) + z(log population) + FE, for 2021, 2025 and the change
  2021 -> 2025 (difference of the percentile-rank indices = change of relative position). Also the plain
  Spearman rho and the within-oblast rho (ranks demeaned by oblast). Per-resident indicators share the
  population denominator, hence the population control.
Part D — local clusters (LISA, esda Moran_Local, KNN k = 6 on UA_LAEA representative points, row-standardised,
  9,999 permutations, fixed seed). Variables: the three spheres 2021 and 2025, their change, and the balance
  (as 35_sphere_layers.py: weights w_* / national centre -> isometric log-ratio coordinates):
    imbalance_Y         distance from the national centre (size of the departure on map 24)
    lean_cult_Y         cultural weight against the geometric mean of economic and rights (+ = cultural-leaning)
    lean_econ_rights_Y  economic against rights (+ = economic-leaning)
  Scopes: national (all non-occupied) and Carpathian (Zakarpattia 21, Ivano-Frankivsk 26, Lviv 46,
  Chernivtsi 73; weights built within the four oblasts). Classes HH, LL, HL, LH at p < 0.05 and after a
  false-discovery-rate cut (esda.fdr, 0.05).

Outputs
  tidy/sphere_associations.csv   one row per model and focus coefficient (national aggregates; published)
  tidy/sphere_lisa_summary.csv   global Moran's I and LISA class counts by scope, variable and oblast (published)
  tidy/sphere_lisa_k3.csv        hromada LISA classes for step 8 (local only, .gitignore: zone hromadas, R3)
  logs/36_sphere_associations.log
Caveat: cross-sectional and associational; no coefficient here is a causal effect.
"""
import argparse
import time

import numpy as np
import pandas as pd

from sphere_common import (BASE, CARP, FRONTLINE, LABEL, SPH, TIDY, YEARS, Models, lisa, load_base, log,
                           open_log, reliable_light)

OUT = TIDY / "sphere_associations.csv"
OUT_LS = TIDY / "sphere_lisa_summary.csv"
OUT_LK = TIDY / "sphere_lisa_k3.csv"


def main():
    ap = argparse.ArgumentParser(description="step 7: sphere associations")
    ap.add_argument("--no-ci", action="store_true", help="skip wild-cluster confidence intervals")
    ap.add_argument("--B", type=int, default=9999, help="bootstrap draws (default 9,999)")
    a = ap.parse_args()
    open_log("36_sphere_associations")
    t0 = time.time()
    log(f"36_sphere_associations.py  {time.strftime('%Y-%m-%d %H:%M')}  B={a.B}  ci={'no' if a.no_ci else 'yes'}")

    d = load_base()

    log("\ncorrelations (Spearman, non-occupied) of the spheres with exposure and outcomes:")
    xs = [c for c in ("exp", "exp_alert", "recovery_index", "y_s24", "y_recent") if c in d]
    ys = [f"{s}_{yr}" for yr in YEARS for s in SPH] + [f"d_{s}" for s in SPH]
    log(d[ys + xs].corr(method="spearman").loc[ys, xs].round(2).to_string())

    M = Models(d, a.B, not a.no_ci)

    # ---- Part A: exposure
    log("\n==== Part A — spheres and war exposure ====")
    for s in SPH:
        log(f"\n-- {LABEL[s]}")
        M.fit("A", "A1 2021, no FE", f"{s}_2021", ["exp"], ["c_logpop"], fe=False)
        M.fit("A", "A1 2021, FE", f"{s}_2021", ["exp"], ["c_logpop"])
        M.fit("A", "A2 2025, no FE", f"{s}_2025", ["exp"], ["c_logpop"], fe=False)
        M.fit("A", "A2 2025, FE", f"{s}_2025", ["exp"], ["c_logpop"])
        M.fit("A", "A3 2025 given 2021, FE", f"{s}_2025", ["exp"], [f"{s}_2021", "c_logpop"], ci=("exp",))
        if "exp_alert" in d:
            M.fit("A", "A3 alert hours", f"{s}_2025", ["exp_alert"], [f"{s}_2021", "c_logpop"])
        M.fit("A", "A3 without frontline oblasts", f"{s}_2025", ["exp"], [f"{s}_2021", "c_logpop"],
              data=d[~d["k1"].isin(FRONTLINE)], note="dropped k1 14, 23, 65")
        M.fit("A", "A3 without zone hromadas", f"{s}_2025", ["exp"], [f"{s}_2021", "c_logpop"],
              data=d[~d["in_zone"]], note="dropped zone hromadas")
    for bv in ("imbalance", "lean_cult", "lean_econ_rights"):
        log(f"\n-- balance: {bv}")
        M.fit("A", "A2 2025, FE", f"{bv}_2025", ["exp"], ["c_logpop"])
        M.fit("A", "A3 2025 given 2021, FE", f"{bv}_2025", ["exp"], [f"{bv}_2021", "c_logpop"])

    # ---- Part B: functional resilience
    log("\n==== Part B — pre-war spheres (2021) and functional resilience ====")
    ctrl = ["c_logpop", "c_loglit", "c_rad21"]
    sph21 = [f"{s}_2021" for s in SPH]
    outcomes = [c for c in ("recovery_index", "y_s24", "y_recent") if c in d]
    rel = reliable_light(d)
    for yc in outcomes:
        log(f"\n-- outcome {yc}")
        M.fit("B", "B1 three spheres, FE", yc, sph21, ["exp"] + ctrl, ci=tuple(sph21))
        if yc != "recovery_index" and rel.any():
            M.fit("B", "B1r reliable light data", yc, sph21, ["exp"] + ctrl, data=d[rel],
                  note=">= 30 lit pixels, noise_sd <= 0.35")
        for s in SPH:
            M.fit("B", f"B2 {LABEL[s]} x exposure, FE", yc, [f"{s}_2021", "exp"], ctrl,
                  inter=(f"{s}_2021", "exp"))

    # ---- Part C: spheres against each other
    log("\n==== Part C — the spheres against each other ====")
    rho = []
    for a_, b_ in (("econ", "rights"), ("econ", "cult"), ("rights", "cult")):
        for tag, ca, cb in ((2021, f"{a_}_2021", f"{b_}_2021"), (2025, f"{a_}_2025", f"{b_}_2025"),
                            ("change", f"d_{a_}", f"d_{b_}")):
            ok = d[[ca, cb]].notna().all(axis=1)
            s = d[ok]
            r_raw = s[ca].corr(s[cb], method="spearman")
            ra, rb = s[ca].rank(), s[cb].rank()
            ra_w = ra - ra.groupby(s["k1"]).transform("mean")
            rb_w = rb - rb.groupby(s["k1"]).transform("mean")
            r_w = ra_w.corr(rb_w)
            rho.append((f"{LABEL[a_]}–{LABEL[b_]}", tag, len(s), r_raw, r_w))
            log(f"\n-- {LABEL[a_]} ~ {LABEL[b_]} ({tag}): Spearman {r_raw:+.2f}, within oblasts {r_w:+.2f}")
            M.fit("C", f"C {tag}, FE", ca, [cb], ["c_logpop"], ci=(cb,), note=f"rho={r_raw:.3f}; rho_within={r_w:.3f}")
    log("\nrank correlations between the spheres (plain | within oblasts):")
    log(pd.DataFrame(rho, columns=["pair", "year", "n", "rho", "rho_within"]).round(3).to_string(index=False))

    res = pd.DataFrame(M.rows)
    res.to_csv(OUT, index=False, float_format="%.6g")
    log(f"\nwrote {OUT.relative_to(BASE)} ({len(res)} rows)   [{(time.time() - t0) / 60:.1f} min]")

    # ---- Part D: LISA
    log("\n==== Part D — local clusters (LISA) ====")
    try:
        import esda  # noqa: F401
    except Exception as ex:
        log(f"esda not available ({ex}); Part D skipped")
        return
    lvars = ([f"{s}_{yr}" for yr in YEARS for s in SPH] + [f"d_{s}" for s in SPH]
             + [f"{bv}_{yr}" for yr in YEARS for bv in ("imbalance", "lean_cult", "lean_econ_rights")])
    summ, hk = [], d[["k1", "k2", "k3", "name", "in_zone"]].copy()
    for scope, sub in (("national", d), ("carpathian", d[d["k1"].isin(CARP)])):
        log(f"\n-- scope {scope} (n={len(sub)})")
        for v in lvars:
            s, gm, cls, cls_f, cut = lisa(sub, v, scope)
            hk.loc[s.index, f"{v}_{scope}"] = cls
            hk.loc[s.index, f"{v}_{scope}_fdr"] = cls_f
            cnt, cntf = cls.value_counts(), cls_f.value_counts()
            log(f"   {v:26s} Moran I={gm.I:+.3f} (p={gm.p_sim:.3f})  "
                + "  ".join(f"{c} {int(cnt.get(c, 0)):3d}/{int(cntf.get(c, 0)):3d}" for c in ("HH", "LL", "HL", "LH"))
                + f"   [p<0.05 / FDR, cut {cut:.4f}]")
            groups = [("all", s.index)] + [(k1, s.index[s["k1"] == k1]) for k1 in sorted(s["k1"].unique())]
            for k1, ix in groups:
                row = {"scope": scope, "variable": v, "k1": k1, "n": len(ix),
                       "moran_I": gm.I if k1 == "all" else np.nan, "moran_p": gm.p_sim if k1 == "all" else np.nan,
                       "fdr_cut": cut if k1 == "all" else np.nan}
                for c in ("HH", "LL", "HL", "LH", "ns"):
                    row[c] = int((cls[ix] == c).sum())
                for c in ("HH", "LL", "HL", "LH"):
                    row[f"{c}_fdr"] = int((cls_f[ix] == c).sum())
                summ.append(row)
    S = pd.DataFrame(summ)
    S.to_csv(OUT_LS, index=False, float_format="%.6g")
    hk.to_csv(OUT_LK, index=False)
    log(f"\nwrote {OUT_LS.relative_to(BASE)} ({len(S)} rows) and {OUT_LK.relative_to(BASE)} (local only)")

    # Carpathian profile of the national clusters
    log("\nnational LISA classes inside the Carpathian oblasts (p < 0.05; counts HH/LL/HL/LH):")
    cp = S[(S["scope"] == "national") & S["k1"].isin(CARP)]
    log(cp.pivot_table(index="variable", columns="k1", values=["HH", "LL"], aggfunc="sum")
        .reindex(lvars).fillna(0).astype(int).to_string())
    log(f"\ndone in {(time.time() - t0) / 60:.1f} min")


if __name__ == "__main__":
    main()
