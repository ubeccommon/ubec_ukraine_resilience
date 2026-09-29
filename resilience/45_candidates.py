#!/usr/bin/env python3
"""
45_candidates.py — round 3, step 4 (docs/pattern_language.md, 5.7 and 5.9): test a candidate pattern's nearest open
measure on all hromadas, with the method of 40_configurations.py and the paper's inference, and give it its stars.

  python 45_candidates.py --measure m_civil_change --quality func
  python 45_candidates.py --measure m_npo_per10k,m_gen_council_per10k --quality fisc     each alone, then their conjunction
  python 45_candidates.py --measure m_formed_voluntary --quality fisc --sign -1          absence is the condition
  python 45_candidates.py --measure m_x --quality func --absolute 0,1                     natural thresholds instead of the
                                                                                          within-oblast rank (0 -> absent, 1 -> present)
  python 45_candidates.py --measure m_x --quality func --label "generator_shared"         the candidate's working name (English)
  python 45_candidates.py --measure m_x --quality func --file tidy/other_k3.csv           measure from another tidy table
  python 45_candidates.py --measure m_x --quality func --pop zone --perms 50

Inputs: tidy/quality_k3.csv (39, local), tidy/measures_k3.csv (44) or --file, and 40's condition set (sphere_inputs_k3.csv,
population_k3.csv, sphere_indices_k3.csv). The candidate is calibrated like 40's conditions: within-oblast percentile
rank times sign (or --absolute lo,hi: 0 below lo, 1 above hi, linear between). Outcome: the quality's composite
(rank = fuzzy held-up), classes held_up / faltered from 39.

Checks — the design's stars (section 7) made explicit; a check passes or fails, and the log says why:
  C1 plain      share of held-up above the oblast median minus the share of faltered, in the expected direction
  C2 linear     Spearman of the candidate's oblast rank with the outcome rank beats the chance ceiling (95th percentile of
                |rho| with the outcome permuted within oblasts, 10 x --perms draws)
  C3 bootstrap  z(composite) ~ z(candidate) + oblast fixed effects; wild-cluster bootstrap by oblast p < 0.05
                (robust_inference.wild_cluster_p, as the paper)
  C4 families   the sign holds (same sign, |rho| >= 0.05) on the families that did NOT define the quality: for the
                functional quality the three budget families, for the fiscal quality the two light families, for the
                composite the leave-one-out rule (each family against the others); a majority must hold
  C5 regions    the sign holds in at least three of the four macro-regions (west, centre, south, east; oblast-rank
                Spearman within the region, n >= 40)
  C6 zone       the sign holds in the 30 km zone population (n >= 30); a caveat, not a failure, when it does not
  C7 pattern    configurational: the candidate alone (k = 1) or in a conjunction with 40's conditions (k <= 3) beats the
                permutation ceiling for its k by the margin, with 40's coverage and crisp thresholds — the difference
                between an association and a configuration in Alexander's sense
Stars: ** C1–C5 and C7 pass; * C1–C5 pass but C7 fails (an association, not a configuration), or exactly one of C4–C6
fails; none otherwise (a hypothesis, published as such). Timing: a measure dated after February 2022 (data dictionary
'year') accompanies holding up, it does not precede it; the row says which.

Outputs (public — aggregates only)
  tidy/candidates.csv                 one row per candidate x quality x population (appended; same key replaced)
  tidy/candidates_<label>.json        the details of the last run
  logs/45_candidates.log
Calibration for the profile table (section 7): the thresholds that make the candidate present (>= 0.67), partial and
absent are printed as values of the measure per oblast (median of the oblast thresholds) or as the --absolute pair.
"""
import argparse
import importlib
import itertools
import json
import sys
import time
import warnings

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from sphere_common import BASE, CARP, SPH, TIDY, centre_of, closure, ilr, log, open_log, rd, z
from robust_inference import wild_cluster_p

warnings.filterwarnings("ignore")
sys.path.insert(0, str(BASE))
c40 = importlib.import_module("40_configurations")
OUT = TIDY / "candidates.csv"
FAM = {"func": ("s24", "recent"), "fisc": ("econ", "cult", "own"), "composite": ("s24", "recent", "econ", "cult", "own")}
SEED = 20260929
RHO_MIN = 0.05


def rho(x, y):
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < 20:
        return np.nan
    return float(spearmanr(x[m], y[m]).statistic)


def permute_within(y, groups, rng):
    yp = y.copy()
    for g in np.unique(groups):
        idx = np.where(groups == g)[0]
        yp[idx] = yp[rng.permutation(idx)]
    return yp


def calibrate(x, k1, sign, absolute):
    x = pd.to_numeric(x, errors="coerce") * sign
    if absolute:
        lo, hi = absolute
        if sign < 0:
            lo, hi = -hi, -lo
        return ((x - lo) / (hi - lo)).clip(0, 1) if hi > lo else (x >= lo).astype(float).where(x.notna())
    return c40.oblast_rank(x, k1)


def load(a):
    q = rd("quality_k3.csv")
    q = q[q["pop"] == a.pop].copy()
    src = rd(a.file) if a.file else rd("measures_k3.csv")
    cols = [m for m in a.measures if m in src]
    miss = [m for m in a.measures if m not in src]
    if miss:
        raise SystemExit(f"measure(s) not in {a.file or 'tidy/measures_k3.csv'}: {miss}; available: {[c for c in src.columns if c.startswith('m_')][:40]}")
    d = q.drop(columns=[c for c in cols if c in q]).merge(src[["k3"] + cols], on="k3", how="left")
    inp = rd("sphere_inputs_k3.csv")
    d = d.merge(inp.drop(columns=[c for c in ("k1", "k2", "name") if c in inp]), on="k3", how="left")
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
    d["imbalance_2021"] = d["k3"].map(pd.Series(imb, index=si["k3"]))
    d["region"] = d["k1"].map({k: r for r, ks in c40.REGION.items() for k in ks}).fillna("other")
    d["carp"] = d["k1"].isin(CARP)
    return d


def measure_year(m):
    ddp = TIDY / "data_dictionary.csv"
    if not ddp.exists():
        return ""
    dd = pd.read_csv(ddp, dtype=str)
    r = dd[dd["indicator"] == m]
    return str(r["year"].iloc[0]) if len(r) else ""


def timing(years):
    ys = [int(v) for y in years for v in __import__("re").findall(r"(20\d\d)", str(y))]
    if not ys:
        return "undated"
    return "precedes (pre-war)" if max(ys) <= 2021 else "accompanies (measured after February 2022)"


def run(a, d, measures, sign, label):
    ccol = "composite" if a.quality == "composite" else f"composite_{a.quality}"
    qcol = "quality" if a.quality == "composite" else f"quality_{a.quality}"
    rng = np.random.default_rng(SEED)
    # ---- candidate membership: one measure, or the conjunction (min) of several
    F = pd.DataFrame(index=d.index)
    for m in measures:
        F[m] = calibrate(d[m], d["k1"], sign, a.absolute)
    cand = F[measures].min(axis=1) if len(measures) > 1 else F[measures[0]]
    Y = pd.to_numeric(d[ccol], errors="coerce").rank(pct=True)
    ok = cand.notna() & Y.notna()
    do, cv, yv = d[ok], cand[ok].values, Y[ok].values
    held, falt = (do[qcol] == "held_up").values, (do[qcol] == "faltered").values
    k1v = do["k1"].astype(str).values
    log(f"\n== candidate {label}: {' AND '.join(measures)}  sign {sign:+d}  quality {a.quality}  pop {a.pop}  "
        f"n {int(ok.sum())} (held up {int(held.sum())}, faltered {int(falt.sum())}), missing {int((~ok).sum())}")
    checks, det = {}, {}

    # C1 plain
    above = cv > 0.5
    sh_h, sh_f = float(above[held].mean()), float(above[falt].mean())
    diff = sh_h - sh_f
    checks["C1_plain"] = diff > 0
    det["plain"] = {"share_above_median_held_up": round(sh_h, 3), "share_above_median_faltered": round(sh_f, 3), "difference": round(diff, 3)}
    log(f"C1 plain: above the oblast median — held up {sh_h:.2f}, faltered {sh_f:.2f}, difference {diff:+.3f}  -> {'pass' if checks['C1_plain'] else 'fail'}")

    # C2 linear vs ceiling
    r_obs = rho(cv, yv)
    perm = [abs(rho(cv, permute_within(yv, k1v, rng))) for _ in range(max(a.perms, 1) * 10)]
    ceil = float(np.percentile(perm, 95))
    checks["C2_linear"] = np.isfinite(r_obs) and r_obs > ceil
    det["linear"] = {"rho": round(r_obs, 3), "ceiling_p95": round(ceil, 3)}
    log(f"C2 linear: Spearman {r_obs:+.3f} vs chance ceiling {ceil:.3f}  -> {'pass' if checks['C2_linear'] else 'fail'}")

    # C3 within-oblast regression with wild-cluster bootstrap
    yz = z(pd.to_numeric(do[ccol], errors="coerce")).values
    xz = z(pd.Series(cv)).values
    D = pd.get_dummies(k1v, prefix="ob", drop_first=True, dtype=float)
    D = D.loc[:, D.std() > 0]
    X = np.column_stack([np.ones(len(xz)), xz, D.values])
    m = np.isfinite(yz) & np.isfinite(xz)
    b = np.linalg.pinv(X[m].T @ X[m]) @ X[m].T @ yz[m]
    wb = wild_cluster_p(yz[m], X[m], [1], k1v[m], B=a.boot)
    p_wcb = float(wb[1][1])
    checks["C3_bootstrap"] = p_wcb < 0.05 and b[1] > 0
    det["regression"] = {"b_sd": round(float(b[1]), 3), "t_cr1": round(float(wb[1][0]), 2), "p_wcb": round(p_wcb, 3), "B": a.boot}
    log(f"C3 bootstrap: z(composite) ~ z(candidate) + oblast FE: b = {b[1]:+.3f} SD, CR1 t = {wb[1][0]:+.2f}, wild-cluster p = {p_wcb:.3f}  "
        f"-> {'pass' if checks['C3_bootstrap'] else 'fail'}")

    # C4 families: defining vs validating
    fam_all = FAM["composite"]
    defining = FAM[a.quality]
    validating = [f for f in fam_all if f not in defining] if a.quality != "composite" else list(fam_all)
    fam_r = {}
    for f in fam_all:
        col = f"res0_{f}" if f"res0_{f}" in do else f"res_{f}"
        if col in do:
            fam_r[f] = rho(cv, pd.to_numeric(do[col], errors="coerce").rank(pct=True).values)
    val_ok = [f for f in validating if np.isfinite(fam_r.get(f, np.nan)) and fam_r[f] >= RHO_MIN]
    val_n = sum(1 for f in validating if np.isfinite(fam_r.get(f, np.nan)))
    checks["C4_families"] = val_n > 0 and len(val_ok) * 2 > val_n
    det["families"] = {f: round(v, 3) for f, v in fam_r.items()} | {"validating": validating, "hold": val_ok}
    log(f"C4 families: " + "  ".join(f"{f} {fam_r.get(f, np.nan):+.3f}{'*' if f in validating else ''}" for f in fam_all)
        + f"  (* = validating; hold on {len(val_ok)} of {val_n})  -> {'pass' if checks['C4_families'] else 'fail'}")

    # C5 regions and the Carpathian oblasts
    reg_r = {}
    for r in c40.REGION:
        mr = (do["region"] == r).values
        reg_r[r] = rho(cv[mr], yv[mr]) if mr.sum() >= 40 else np.nan
    n_ok = sum(1 for v in reg_r.values() if np.isfinite(v) and v >= RHO_MIN)
    checks["C5_regions"] = n_ok >= 3
    mc = do["carp"].values
    carp_r = rho(cv[mc], yv[mc]) if mc.sum() >= 40 else np.nan
    det["regions"] = {r: (round(v, 3) if np.isfinite(v) else None) for r, v in reg_r.items()} | {"carpathian": round(carp_r, 3) if np.isfinite(carp_r) else None}
    log(f"C5 regions: " + "  ".join(f"{r} {v:+.3f}" if np.isfinite(v) else f"{r} n/a" for r, v in reg_r.items())
        + f"  Carpathian {carp_r:+.3f}" + f"  ({n_ok} of 4 hold)  -> {'pass' if checks['C5_regions'] else 'fail'}")

    # C6 zone (only when the run is the outside population)
    zone_r = np.nan
    if a.pop == "outside":
        qz = rd("quality_k3.csv")
        qz = qz[qz["pop"] == "zone"]
        src = rd(a.file) if a.file else rd("measures_k3.csv")
        dz = qz.drop(columns=[c for c in measures if c in qz]).merge(src[["k3"] + measures], on="k3", how="left")
        Fz = pd.DataFrame({mm: calibrate(dz[mm], dz["k1"], sign, a.absolute) for mm in measures})
        cz = Fz.min(axis=1).values
        yz_ = pd.to_numeric(dz[ccol], errors="coerce").rank(pct=True).values
        zone_r = rho(cz, yz_) if np.isfinite(cz).sum() >= 30 else np.nan
    checks["C6_zone"] = (not np.isfinite(zone_r)) or zone_r >= RHO_MIN
    det["zone"] = {"rho": round(zone_r, 3) if np.isfinite(zone_r) else None}
    log(f"C6 zone: Spearman {zone_r:+.3f}" if np.isfinite(zone_r) else "C6 zone: too few hromadas or not applicable"
        + ("" if not np.isfinite(zone_r) else f"  -> {'holds' if checks['C6_zone'] else 'does not hold (caveat)'}"))

    # C7 configurational: the candidate alone and in conjunctions with 40's conditions
    G = pd.DataFrame(index=do.index)
    for nm, (col, sg, _) in c40.CONDITIONS.items():
        G[nm] = c40.oblast_rank(pd.to_numeric(do[col], errors="coerce") * sg, do["k1"])
    G["CAND"] = cv
    conds = [c for c in G.columns if G[c].notna().all()]
    if "CAND" not in conds:
        G = G.dropna()
        conds = list(G.columns)
    Gv = G[conds]
    Yc = pd.Series(yv, index=do.index).loc[Gv.index].values
    hc, fc = pd.Series(held, index=do.index).loc[Gv.index].values, pd.Series(falt, index=do.index).loc[Gv.index].values
    others = [c for c in conds if c != "CAND"]
    combos = [("CAND",)] + [("CAND",) + c for k in (1, 2) if k < a.max_k for c in itertools.combinations(others, k)]
    fuzz = {nm: (Gv[nm].values, 1 - Gv[nm].values) for nm in conds}

    def score(combo, signs, y):
        X = np.ones(len(y))
        for nm, s in zip(combo, signs):
            X = np.minimum(X, fuzz[nm][0] if s else fuzz[nm][1])
        return c40.fuzzy_stats(X, y), X

    rows = []
    for combo in combos:
        for signs in itertools.product((1, 0), repeat=len(combo) - 1):
            signs = (1,) + signs
            (cons, cov), X = score(combo, signs, Yc)
            Xc = X > 0.5
            n_pos, n_neg = int((Xc & hc).sum()), int((Xc & fc).sum())
            prec = n_pos / (n_pos + n_neg) if n_pos + n_neg else np.nan
            rows.append({"k": len(combo), "configuration": " AND ".join(("" if s else "NOT ") + nm for nm, s in zip(combo, signs)),
                         "consistency": round(float(cons), 3), "coverage": round(float(cov), 3), "crisp_n": int(Xc.sum()),
                         "crisp_precision": round(prec, 3) if np.isfinite(prec) else np.nan})
    R = pd.DataFrame(rows)
    k1c = do.loc[Gv.index, "k1"].astype(str).values
    maxes = {k: [] for k in R["k"].unique()}
    for _ in range(a.perms):
        yp = permute_within(Yc, k1c, rng)
        best = {k: 0.0 for k in maxes}
        for combo in combos:
            for signs in itertools.product((1, 0), repeat=len(combo) - 1):
                (cons, _), _ = score(combo, (1,) + signs, yp)
                if np.isfinite(cons):
                    best[len(combo)] = max(best[len(combo)], cons)
        for k in maxes:
            maxes[k].append(best[k])
    ceil_k = {int(k): round(float(np.percentile(v, 95)), 3) for k, v in maxes.items()} if a.perms else {}
    R["excess"] = R.apply(lambda r: round(r["consistency"] - ceil_k.get(int(r["k"]), c40.CONS_MIN - c40.MARGIN), 3), axis=1)
    R["passes"] = (R["excess"] >= c40.MARGIN) & (R["coverage"] >= c40.COV_MIN) & (R["crisp_n"] >= c40.CRISP_N) & (R["crisp_precision"] >= c40.CRISP_PREC)
    R = R.sort_values(["passes", "k", "consistency"], ascending=[False, True, False])
    checks["C7_pattern"] = bool(R["passes"].any())
    alone = R[R["k"] == 1].iloc[0]
    det["configurational"] = {"ceiling_p95_by_k": ceil_k, "alone": alone.to_dict(),
                              "passing": R[R["passes"]].head(10).to_dict("records"), "scored": int(len(R))}
    log(f"C7 pattern: alone consistency {alone['consistency']:.3f} (ceiling k=1 {ceil_k.get(1, 'n/a')}, excess {alone['excess']:+.3f}), "
        f"coverage {alone['coverage']:.3f}, crisp n {alone['crisp_n']}, precision {alone['crisp_precision']:.2f}; "
        f"{int(R['passes'].sum())} of {len(R)} conjunctions with the candidate pass  -> {'pass' if checks['C7_pattern'] else 'fail'}")
    if R["passes"].any():
        log(R[R["passes"]].head(10).to_string(index=False))

    # stars
    core = all(checks[c] for c in ("C1_plain", "C2_linear", "C3_bootstrap", "C4_families", "C5_regions"))
    soft_fails = sum(1 for c in ("C4_families", "C5_regions", "C6_zone") if not checks[c])
    hard = all(checks[c] for c in ("C1_plain", "C2_linear", "C3_bootstrap"))
    if core and checks["C7_pattern"]:
        stars = "**"
    elif core or (hard and soft_fails == 1):
        stars = "*"
    else:
        stars = ""
    kind = "configuration" if checks["C7_pattern"] else "association" if hard else "none"
    years = [measure_year(m) for m in measures]
    tm = timing(years)
    # calibration thresholds for the profile table (section 7): oblast medians of the values at rank 0.33 and 0.67
    cal = {}
    if a.absolute:
        cal = {"absent_below": a.absolute[0], "present_at_or_above": a.absolute[1], "kind": "absolute"}
    elif len(measures) == 1:
        x = pd.to_numeric(do[measures[0]], errors="coerce")
        qs = x.groupby(k1v).quantile([0.33, 0.67]).unstack()
        cal = {"partial_from_median_oblast": round(float(qs[0.33].median()), 4), "present_from_median_oblast": round(float(qs[0.67].median()), 4),
               "kind": "within-oblast rank (thresholds vary by oblast; medians shown)"}
    log(f"stars: {stars or 'none'}  ({kind}; {tm}; checks " + ", ".join(f"{c} {'ok' if v else 'x'}" for c, v in checks.items()) + ")")
    row = {"label": label, "measures": ";".join(measures), "sign": sign, "quality": a.quality, "pop": a.pop, "n": int(ok.sum()),
           "held_up": int(held.sum()), "faltered": int(falt.sum()), "timing": tm, "years": ";".join(y for y in years if y),
           "plain_diff": det["plain"]["difference"], "rho": det["linear"]["rho"], "rho_ceiling": det["linear"]["ceiling_p95"],
           "b_sd": det["regression"]["b_sd"], "p_wcb": det["regression"]["p_wcb"],
           "families_hold": f"{len(val_ok)}/{val_n}", "regions_hold": n_ok, "rho_carpathian": det["regions"]["carpathian"],
           "rho_zone": det["zone"]["rho"], "cons_alone": alone["consistency"], "excess_alone": alone["excess"],
           "conjunctions_pass": int(R["passes"].sum()), **{c: int(v) for c, v in checks.items()}, "kind": kind, "stars": stars,
           "calibration": json.dumps(cal, ensure_ascii=False), "date": time.strftime("%Y-%m-%d")}
    return row, {"row": row, "details": det, "checks": checks}


def main():
    ap = argparse.ArgumentParser(description="round 3, step 4: test candidate measures with 40's method")
    ap.add_argument("--measure", required=True, help="m_* column(s), comma-separated: each alone, then their conjunction")
    ap.add_argument("--quality", default="func", choices=("func", "fisc", "composite"))
    ap.add_argument("--sign", type=int, default=1, choices=(1, -1), help="+1: presence is the condition; -1: absence")
    ap.add_argument("--absolute", default="", help="lo,hi natural thresholds instead of the within-oblast rank")
    ap.add_argument("--label", default="", help="working name of the candidate pattern")
    ap.add_argument("--file", default="", help="tidy table holding the measure (default measures_k3.csv)")
    ap.add_argument("--pop", default="outside", choices=("outside", "zone"))
    ap.add_argument("--perms", type=int, default=20)
    ap.add_argument("--boot", type=int, default=999)
    ap.add_argument("--max-k", type=int, default=3, choices=(1, 2, 3))
    a = ap.parse_args()
    a.measures = [m.strip() for m in a.measure.split(",") if m.strip()]
    a.absolute = tuple(float(v) for v in a.absolute.split(",")) if a.absolute else None
    label = a.label or "+".join(m.replace("m_", "") for m in a.measures)
    open_log("45_candidates")
    t0 = time.time()
    log(f"45_candidates.py  {time.strftime('%Y-%m-%d %H:%M')}  measures={a.measures}  quality={a.quality}  pop={a.pop}  "
        f"sign={a.sign:+d}  absolute={a.absolute or '-'}  perms={a.perms}  boot={a.boot}")
    d = load(a)
    runs = [[m] for m in a.measures] + ([a.measures] if len(a.measures) > 1 else [])
    rows, details = [], {}
    for ms in runs:
        lab = label if ms == a.measures else ms[0].replace("m_", "")
        row, det = run(a, d, ms, a.sign, lab)
        rows.append(row)
        details[lab] = det
    new = pd.DataFrame(rows)
    if OUT.exists():
        old = pd.read_csv(OUT)
        key = ["label", "measures", "sign", "quality", "pop"]
        old = old.merge(new[key].assign(_x=1), on=key, how="left")
        old = old[old["_x"].isna()].drop(columns="_x")
        new = pd.concat([old, new], ignore_index=True)
    new.to_csv(OUT, index=False)
    js = TIDY / f"candidates_{label}.json"
    js.write_text(json.dumps(details, ensure_ascii=False, indent=1, default=lambda o: None if isinstance(o, float) and np.isnan(o) else (o.item() if hasattr(o, "item") else str(o))),
                  encoding="utf-8")
    log(f"\nwrote {OUT.relative_to(BASE)} ({len(new)} rows) and {js.relative_to(BASE)}  in {time.time() - t0:.0f} s")
    log(new[["label", "quality", "rho", "p_wcb", "families_hold", "regions_hold", "conjunctions_pass", "kind", "stars", "timing"]].tail(len(rows)).to_string(index=False))


if __name__ == "__main__":
    main()
