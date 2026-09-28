#!/usr/bin/env python3
"""
40_configurations.py — step 2 of the pattern-language round (docs/pattern_language.md, section 5.3): isolate the
configurations that held-up hromadas share and faltered ones lack.

  python 40_configurations.py                 outside-zone population, conditions below
  python 40_configurations.py --pop zone      the 30 km zone population (small: read with care)
  python 40_configurations.py --max-k 2       conjunctions of at most two conditions (default 3)
  python 40_configurations.py --with-region   add is_village, is_city and carp as conditions (default: covariates only)

Input: tidy/quality_k3.csv from 39_quality.py (local), sphere_inputs_k3.csv (32), schools_k3.csv (34),
population_k3.csv (05). Alexander's question is which COMBINATION recurs in the places that work, so the
methods are configurational, not regression:

  1. Conditions. Pre-war (2021) and structural variables only — nothing that defines the quality. Each is
     calibrated to a fuzzy set as its within-oblast percentile rank (0 = lowest in its oblast, 1 = highest;
     crisp version: above the oblast median), because context pattern C1 says every hromada is judged inside
     its oblast. Directed conditions (autonomy = 1 − transfer dependency; balance = 1 − imbalance) so that
     "present" reads the same way everywhere. Derived here: local_tax_share_2021 = (property + single tax) /
     (property + single + civilian PIT) per resident — the share of the tax base that is local rather than
     payroll booked at employers.
  2. Rule induction: a classification tree (depth <= 3, >= 20 hromadas per leaf) on held_up vs faltered, its
     accuracy cross-validated with oblasts held out (GroupKFold 5); the rules printed. Leaves are conjunctions.
  3. Fuzzy-set consistency and coverage (Ragin 2008) of every conjunction of 1..max_k conditions, each present or
     absent, against the fuzzy outcome Y = within-population percentile rank of the composite residual (held up)
     and 1 − Y (faltered):  consistency = sum(min(X, Y)) / sum(X)   coverage = sum(min(X, Y)) / sum(Y).
     Baseline for two independent uniform sets is 2/3; a configuration counts when consistency >= 0.80 and
     coverage >= 0.10 (fuzzy), AND in crisp terms (all conditions above / below the oblast median) it covers
     >= 20 hromadas of the extremes with precision >= 0.60 among held_up + faltered (baseline 0.50). Minimal
     sufficient configurations are retained (as QCA minimisation): a superset of a passing configuration is
     dropped unless it raises consistency by >= 0.05, in which case it is kept and marked 'sharpens'.
     Retained configurations are listed shortest first. Necessary conditions:
     sum(min(X, Y)) / sum(Y) >= 0.90 with relevance (sum X / n) reported.
  4. Kinds of held-up hromada: k-means (k = 2..4, best silhouette) on the condition memberships of the held-up
     group alone; mean membership profile per kind, with region and hromada type shares.
  5. Noise ceiling: the outcome is shuffled within oblasts (--perms, default 20) and every conjunction rescored;
     the 95th percentile of the best chance consistency is the ceiling, and 'above_ceiling' marks the
     configurations that beat it; only those are retained. With 5,000+ conjunctions scored, this is the
     multiple-comparison check (pure-noise test, 28 Sep 2026: 400 pass the thresholds, none the ceiling).
  6. Regional check for every retained configuration: crisp coverage of the held-up group by macro-region
     (west, centre, south, east) and in the Carpathian oblasts; a configuration that holds in >= 3 of 4
     macro-regions is marked 'regional_ok'.

Outputs (public: no hromada-level values)
  tidy/configurations.csv            every conjunction scored (outcome, k, conditions, fuzzy and crisp stats,
                                     regional coverage, retained flag)
  tidy/configurations_summary.json   conditions used, tree rules and cross-validated accuracy, necessary
                                     conditions, retained configurations, kinds
  logs/40_configurations.log
Caveats: the outcome is a residual with every limitation of the models behind it; consistency and coverage are
descriptive, not tests; the crisp counts are what a reader can check against the profile table of 39.
"""
import argparse
import itertools
import json
import time
import warnings

import numpy as np
import pandas as pd

from sphere_common import BASE, CARP, SPH, TIDY, centre_of, closure, ilr, log, open_log, rd

warnings.filterwarnings("ignore")
OUT = TIDY / "configurations.csv"
OUT_S = TIDY / "configurations_summary.json"
REGION = {"west": {"07", "21", "26", "46", "56", "61", "68", "73"},
          "centre": {"05", "18", "32", "35", "53", "71", "74", "80"},
          "south": {"23", "48", "51", "65"},
          "east": {"12", "14", "44", "59", "63"}}
CONS_MIN, COV_MIN, CRISP_N, CRISP_PREC, NEC_MIN, GAIN_MIN = 0.80, 0.10, 20, 0.60, 0.90, 0.05
# name: (source column, direction, label)
CONDITIONS = {
    "local_tax_base": ("local_tax_share_2021", +1, "local taxes (property, land, single) as share of the tax base 2021"),
    "property_tax": ("property_tax_pc_2021", +1, "property and land payments per resident 2021"),
    "single_tax": ("single_tax_pc_2021", +1, "single tax per resident 2021 (sole proprietors, farms)"),
    "payroll_pit": ("pdfo_civ_pc_2021", +1, "civilian PIT per resident 2021 (booked at employers)"),
    "autonomy": ("transfer_dep_civ_2021", -1, "fiscal autonomy 2021 (low transfer dependency)"),
    "investment": ("capex_share_2021", +1, "capital-expenditure share 2021"),
    "social": ("social_pc_2021", +1, "social protection spending per resident 2021"),
    "culture": ("culture_arts_pc_2021", +1, "culture and arts spending per resident 2021"),
    "education": ("education_pc_2021", +1, "education spending per resident 2021"),
    "extracurricular": ("extracurricular_pc_2021", +1, "extracurricular education per resident 2021"),
    "contestation": ("cand_per_seat_rel_2020", +1, "candidates per council seat 2020, relative"),
    "balance": ("imbalance_2021", -1, "three-sphere balance 2021 (small distance from the national centre)"),
    "small": ("pop_ghs_2020", -1, "small population 2020"),
}
STRUCT = {"is_village": "village hromada", "is_city": "city hromada", "carp": "Carpathian oblast"}


def htype(name):
    n = str(name).lower()
    return "city" if "міськ" in n else "settlement" if "селищ" in n else "village" if "сільськ" in n else "other"


def oblast_rank(x, k1):
    """Within-oblast percentile rank in (0, 1]; NaN stays NaN."""
    return x.groupby(k1).rank(pct=True)


def fuzzy_stats(X, Y):
    m = np.minimum(X, Y).sum()
    sx, sy = X.sum(), Y.sum()
    return (m / sx if sx > 0 else np.nan), (m / sy if sy > 0 else np.nan)


def main():
    ap = argparse.ArgumentParser(description="pattern-language step 2: configurations")
    ap.add_argument("--pop", default="outside", choices=("outside", "zone"))
    ap.add_argument("--max-k", type=int, default=3, choices=(1, 2, 3))
    ap.add_argument("--with-region", action="store_true", help="is_village, is_city, carp as conditions")
    ap.add_argument("--perms", type=int, default=20, help="permutations of the outcome within oblasts for the noise ceiling (0 = skip)")
    a = ap.parse_args()
    open_log("40_configurations")
    t0 = time.time()
    log(f"40_configurations.py  {time.strftime('%Y-%m-%d %H:%M')}  pop={a.pop}  max_k={a.max_k}  "
        f"with_region={'yes' if a.with_region else 'no'}")

    # ---- data ------------------------------------------------------------------------------------------
    q = rd("quality_k3.csv")
    q = q[q["pop"] == a.pop].copy()
    inp = rd("sphere_inputs_k3.csv")
    d = q.merge(inp.drop(columns=[c for c in ("k1", "k2") if c in inp]), on="k3", how="left")
    pop = rd("population_k3.csv", required=False)
    if pop is not None and "pop_ghs_2020" not in d:
        d = d.merge(pop[["k3", "pop_ghs_2020"]], on="k3", how="left")
    for c in ("property_tax_pc_2021", "single_tax_pc_2021", "pdfo_civ_pc_2021"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    tb = d["property_tax_pc_2021"].clip(lower=0) + d["single_tax_pc_2021"].clip(lower=0) + d["pdfo_civ_pc_2021"].clip(lower=0)
    d["local_tax_share_2021"] = (d["property_tax_pc_2021"].clip(lower=0) + d["single_tax_pc_2021"].clip(lower=0)) / tb.where(tb > 0)
    si = rd("sphere_indices_k3.csv")
    W = si[[f"w_{s}_2021" for s in SPH]].to_numpy(float)
    okw = np.isfinite(W).all(axis=1) & (W > 0).all(axis=1)
    imb = np.full(len(si), np.nan)
    zc = ilr(closure(W[okw] / centre_of(W[okw])))
    imb[okw] = np.hypot(zc[:, 0], zc[:, 1])
    d["imbalance_2021"] = d["k3"].map(pd.Series(imb, index=si["k3"]))   # as sphere_common.load_base (35)
    d["htype"] = d["name"].map(htype)
    d["is_village"] = (d["htype"] == "village").astype(float)
    d["is_city"] = (d["htype"] == "city").astype(float)
    d["carp"] = d["k1"].isin(CARP).astype(float)
    d["region"] = d["k1"].map({k: r for r, ks in REGION.items() for k in ks}).fillna("other")
    n_all = len(d)
    ext = d["quality"].isin(["held_up", "faltered"])
    log(f"{a.pop}: {n_all} hromadas; held_up {int((d['quality'] == 'held_up').sum())}, "
        f"faltered {int((d['quality'] == 'faltered').sum())}, middle {int((d['quality'] == 'middle').sum())}")
    log(f"local tax share 2021: median {d['local_tax_share_2021'].median():.3f}  "
        f"(held up {d.loc[d['quality'] == 'held_up', 'local_tax_share_2021'].median():.3f}, "
        f"faltered {d.loc[d['quality'] == 'faltered', 'local_tax_share_2021'].median():.3f})")

    # ---- calibration -----------------------------------------------------------------------------------
    F = pd.DataFrame(index=d.index)      # fuzzy memberships in (0, 1]
    for nm, (col, sign, _) in CONDITIONS.items():
        x = pd.to_numeric(d[col], errors="coerce") * sign
        F[nm] = oblast_rank(x, d["k1"])
    conds = list(CONDITIONS)
    if a.with_region:
        for nm in STRUCT:
            F[nm] = d[nm]
        conds += list(STRUCT)
    C = (F > 0.5).astype(float).where(F.notna())          # crisp: above the oblast median
    comp = pd.to_numeric(d["composite"], errors="coerce")
    Y = comp.rank(pct=True)                                # fuzzy held-up
    ok = F[conds].notna().all(axis=1) & Y.notna()
    log(f"complete cases: {int(ok.sum())} of {n_all}  (conditions: {', '.join(conds)})")
    Fo, Co, Yo, do = F[ok], C[ok], Y[ok], d[ok]
    held, falt = (do["quality"] == "held_up").values, (do["quality"] == "faltered").values

    # ---- 2. tree ----------------------------------------------------------------------------------------
    tree_info = {}
    try:
        from sklearn.model_selection import GroupKFold, cross_val_score
        from sklearn.tree import DecisionTreeClassifier, export_text
        e = held | falt
        Xt, yt, gt = Fo.loc[e, conds].values, held[e].astype(int), do.loc[e, "k1"].values
        clf = DecisionTreeClassifier(max_depth=3, min_samples_leaf=20, random_state=20260928)
        cv = GroupKFold(n_splits=5)
        acc = cross_val_score(clf, Xt, yt, groups=gt, cv=cv, scoring="balanced_accuracy")
        clf.fit(Xt, yt)
        rules = export_text(clf, feature_names=conds, decimals=2)
        log(f"\n== tree (depth <= 3) on held_up vs faltered, n={len(yt)}: balanced accuracy with oblasts held out "
            f"= {acc.mean():.3f} ± {acc.std():.3f} (chance 0.5)\n{rules}")
        imp = sorted(zip(conds, clf.feature_importances_), key=lambda t: -t[1])
        log("importance: " + ", ".join(f"{c} {v:.2f}" for c, v in imp if v > 0))
        tree_info = {"n": int(len(yt)), "balanced_accuracy_cv": round(float(acc.mean()), 3),
                     "sd": round(float(acc.std()), 3), "rules": rules,
                     "importance": {c: round(float(v), 3) for c, v in imp if v > 0}}
    except Exception as ex:
        log(f"note: tree skipped ({ex})")

    # ---- 3. necessary conditions and conjunctions ---------------------------------------------------------
    outcomes = {"held_up": (Yo, held, falt), "faltered": (1 - Yo, falt, held)}
    log("\n== necessary conditions (consistency of necessity >= 0.90)")
    nec = []
    for oc, (Yv, _, _) in outcomes.items():
        for nm in conds:
            for present, X in ((1, Fo[nm]), (0, 1 - Fo[nm])):
                cons, cov = fuzzy_stats(X.values, Yv.values)
                if cov >= NEC_MIN:
                    rel = float(X.mean())
                    nec.append({"outcome": oc, "condition": nm, "present": present,
                                "necessity": round(float(cov), 3), "relevance": round(rel, 3)})
                    log(f"  {oc:8s} {'' if present else 'NOT '}{nm:18s} necessity={cov:.3f}  relevance={rel:.3f}")
    if not nec:
        log("  none")

    rows = []
    for oc, (Yv, pos, neg) in outcomes.items():
        yv = Yv.values
        for k in range(1, a.max_k + 1):
            for combo in itertools.combinations(conds, k):
                for signs in itertools.product((1, 0), repeat=k):
                    X = np.ones(len(Fo))
                    Xc = np.ones(len(Fo), dtype=bool)
                    for nm, s in zip(combo, signs):
                        f = Fo[nm].values
                        c = Co[nm].values
                        X = np.minimum(X, f if s else 1 - f)
                        Xc &= (c == 1) if s else (c == 0)
                    cons, cov = fuzzy_stats(X, yv)
                    n_c = int(Xc.sum())
                    n_pos, n_neg = int((Xc & pos).sum()), int((Xc & neg).sum())
                    prec = n_pos / (n_pos + n_neg) if n_pos + n_neg else np.nan
                    recall = n_pos / pos.sum() if pos.sum() else np.nan
                    reg = {}
                    for r in REGION:
                        m = (do["region"] == r).values & pos
                        reg[r] = round(float((Xc & m).sum() / m.sum()), 3) if m.sum() >= 10 else np.nan
                    mc = do["carp"].values == 1
                    carp_cov = round(float((Xc & mc & pos).sum() / (mc & pos).sum()), 3) if (mc & pos).sum() >= 10 else np.nan
                    n_reg_ok = sum(1 for v in reg.values() if np.isfinite(v) and v >= 0.5 * recall) if np.isfinite(recall) else 0
                    rows.append({"outcome": oc, "k": k,
                                 "configuration": " AND ".join(("" if s else "NOT ") + nm for nm, s in zip(combo, signs)),
                                 "conditions": ";".join(combo), "signs": "".join(str(s) for s in signs),
                                 "consistency": round(float(cons), 3), "coverage": round(float(cov), 3),
                                 "crisp_n": n_c, "crisp_n_outcome": n_pos, "crisp_precision": round(prec, 3) if np.isfinite(prec) else np.nan,
                                 "crisp_recall": round(recall, 3) if np.isfinite(recall) else np.nan,
                                 **{f"cov_{r}": v for r, v in reg.items()}, "cov_carpathian": carp_cov,
                                 "regions_ok": n_reg_ok})
    R = pd.DataFrame(rows)

    # noise ceiling, per number of conditions k: the outcome shuffled within oblasts; what consistency does the
    # best conjunction of k conditions reach by chance?
    ceiling = {}
    if a.perms > 0:
        rng = np.random.default_rng(20260928)
        fuzz = {nm: (Fo[nm].values, 1 - Fo[nm].values) for nm in conds}
        combos = [(k, combo, signs) for k in range(1, a.max_k + 1) for combo in itertools.combinations(conds, k)
                  for signs in itertools.product((1, 0), repeat=k)]
        k1v = do["k1"].values
        maxes = {k: [] for k in range(1, a.max_k + 1)}
        for _ in range(a.perms):
            yp = Yo.values.copy()
            for g in np.unique(k1v):
                idx = np.where(k1v == g)[0]
                yp[idx] = yp[rng.permutation(idx)]
            best = {k: 0.0 for k in maxes}
            for k, combo, signs in combos:
                X = np.ones(len(yp))
                for nm, sg in zip(combo, signs):
                    X = np.minimum(X, fuzz[nm][0] if sg else fuzz[nm][1])
                sx = X.sum()
                if sx > 0:
                    best[k] = max(best[k], np.minimum(X, yp).sum() / sx)
            for k in maxes:
                maxes[k].append(best[k])
        ceiling = {"perms": a.perms,
                   "p95_by_k": {int(k): round(float(np.percentile(v, 95)), 3) for k, v in maxes.items()},
                   "median_by_k": {int(k): round(float(np.median(v)), 3) for k, v in maxes.items()}}
        log(f"\nnoise ceiling ({a.perms} permutations of the outcome within oblasts), best chance consistency by number "
            f"of conditions: " + "  ".join(f"k={k}: {ceiling['median_by_k'][k]} (median) {ceiling['p95_by_k'][k]} (95th pct)"
                                           for k in ceiling["p95_by_k"]) + ". Only configurations above the 95th "
            f"percentile for their k are retained.")
    R["above_ceiling"] = R.apply(lambda r: r["consistency"] > ceiling["p95_by_k"].get(int(r["k"]), 0)
                                 if ceiling else True, axis=1)
    R["passes"] = (R["consistency"] >= CONS_MIN) & (R["coverage"] >= COV_MIN) & (R["crisp_n"] >= CRISP_N) & \
                  (R["crisp_precision"] >= CRISP_PREC)
    # minimal sufficient configurations (as QCA minimisation): a passing configuration is retained only if none
    # of the shorter configurations it contains passes on its own; a superset that beats its subset by >= GAIN_MIN
    # consistency is kept beside it and marked 'sharpens'
    R["retained"] = R["passes"] & (R["above_ceiling"] if a.perms > 0 else True)
    R["sharpens"] = ""
    passing = {}
    for _, r in R[R["retained"]].iterrows():
        passing[(r["outcome"], tuple(sorted(zip(r["conditions"].split(";"), r["signs"]))))] = r["consistency"]
    for i, r in R[R["retained"]].iterrows():
        items = list(zip(r["conditions"].split(";"), r["signs"]))
        for sub_k in range(1, r["k"]):
            for sub in itertools.combinations(items, sub_k):
                prev = passing.get((r["outcome"], tuple(sorted(sub))))
                if prev is not None:
                    if r["consistency"] - prev >= GAIN_MIN:
                        R.loc[i, "sharpens"] = " AND ".join(("" if s == "1" else "NOT ") + nm for nm, s in sub)
                    else:
                        R.loc[i, "retained"] = False
    R["regional_ok"] = R["regions_ok"] >= 3
    R = R.sort_values(["outcome", "retained", "k", "consistency", "coverage"], ascending=[True, False, True, False, False])
    R.to_csv(OUT, index=False)
    log(f"\n== conjunctions scored: {len(R)}  passing {int(R['passes'].sum())}  retained {int(R['retained'].sum())}")
    show = ["configuration", "consistency", "coverage", "crisp_n", "crisp_precision", "crisp_recall",
            "cov_west", "cov_centre", "cov_south", "cov_east", "cov_carpathian", "regional_ok", "above_ceiling", "sharpens"]
    for oc in outcomes:
        sub = R[(R["outcome"] == oc) & R["retained"]].head(25)
        log(f"\n-- {oc}: retained minimal configurations (shortest first, then consistency; top 25)\n"
            + (sub[show].to_string(index=False) if len(sub) else "  none"))
        top1 = R[(R["outcome"] == oc) & (R["k"] == 1)].sort_values("consistency", ascending=False).head(8)
        log(f"\n-- {oc}: single conditions, for reference\n" + top1[show[:6]].to_string(index=False))
    log(f"wrote {OUT.relative_to(BASE)}")

    # ---- 4. kinds of held-up hromada -------------------------------------------------------------------------
    kinds = {}
    try:
        from sklearn.cluster import KMeans
        from sklearn.metrics import silhouette_score
        H = Fo.loc[held, list(CONDITIONS)]
        if len(H) >= 40:
            best = None
            for k in (2, 3, 4):
                km = KMeans(n_clusters=k, n_init=20, random_state=20260928).fit(H.values)
                s = silhouette_score(H.values, km.labels_)
                if best is None or s > best[1]:
                    best = (k, s, km)
            k, s, km = best
            lab = pd.Series(km.labels_, index=H.index)
            log(f"\n== kinds of held-up hromada: k={k} (silhouette {s:.3f}), sizes {lab.value_counts().sort_index().to_dict()}")
            prof = H.groupby(lab).mean().round(2)
            prof["n"] = lab.value_counts().sort_index()
            prof["village"] = do.loc[H.index, "is_village"].groupby(lab).mean().round(2)
            prof["carp"] = do.loc[H.index, "carp"].groupby(lab).mean().round(2)
            for r in REGION:
                prof[r] = (do.loc[H.index, "region"] == r).groupby(lab).mean().round(2)
            log(prof.T.to_string())
            kinds = {"k": int(k), "silhouette": round(float(s), 3),
                     "profiles": {str(i): prof.loc[i].to_dict() for i in prof.index}}
        else:
            log("\nkinds: fewer than 40 held-up hromadas, skipped")
    except Exception as ex:
        log(f"note: kinds skipped ({ex})")

    summ = {"date": time.strftime("%Y-%m-%d"), "population": a.pop, "n": int(n_all), "complete_cases": int(ok.sum()),
            "conditions": {nm: CONDITIONS[nm][2] for nm in CONDITIONS} | ({nm: STRUCT[nm] for nm in STRUCT} if a.with_region else {}),
            "thresholds": {"consistency": CONS_MIN, "coverage": COV_MIN, "crisp_n": CRISP_N, "crisp_precision": CRISP_PREC,
                           "necessity": NEC_MIN, "superset_gain": GAIN_MIN},
            "tree": tree_info, "necessary": nec, "noise_ceiling": ceiling,
            "retained": {oc: R[(R["outcome"] == oc) & R["retained"]][show].head(25).to_dict("records") for oc in outcomes},
            "kinds": kinds}
    OUT_S.write_text(json.dumps(summ, ensure_ascii=False, indent=1, default=lambda o: None if (isinstance(o, float) and np.isnan(o)) else str(o)),
                     encoding="utf-8")
    log(f"wrote {OUT_S.relative_to(BASE)}\ndone in {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
