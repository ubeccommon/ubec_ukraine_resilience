#!/usr/bin/env python3
"""
43_pairs.py — round 3 of the pattern-language work (docs/pattern_language.md, 5.7): pairs of hromadas to observe.

  python 43_pairs.py                          8 pairs (4 functional, 4 fiscal) + 2 reserves per quality, Carpathian
  python 43_pairs.py --pairs 6                6 pairs (3 + 3): the minimum for a recurrence to show in each quality
  python 43_pairs.py --max-km 120             only hromadas within 120 km (straight line) of the base
  python 43_pairs.py --base 2602003           base hromada for distances (default Verkhovyna)
  python 43_pairs.py --oblasts 26,46          restrict to some oblasts (k1); default the four Carpathian oblasts
  python 43_pairs.py --caliper 1.5            allow less similar partners (default 1.0)

A pair is one hromada that HELD UP and one that FALTERED on the same quality (39_quality.py: functional = light in
summer 2024 and recently; fiscal = tax base, cultural provision, own revenue after Q4 2023), in the same oblast, of
the same type (city, settlement, village), and similar in what the models already control: population 2020 (log),
strikes since 2022 (log), alert hours in the last 12 months. Similarity = Euclidean distance of those three,
standardised within the chosen oblasts; pairs beyond the caliper are not formed. Among the admissible pairs the
largest contrast (held-up composite minus faltered composite, same quality) is taken first, alternating between the
two qualities, at most --per-oblast pairs per oblast and quality, each hromada in one pair only. So what differs
between the two members of a pair is what the data do not see — which is what the visit is for.

Inputs (local): tidy/quality_k3.csv (39, --reliable-light run recommended), tidy/population_k3.csv, exposure from
tidy/resilience_index_v11_k3.csv (local) or public/resilience_index_v11_k3.csv, units_hromada.gpkg for distances.

Outputs — LOCAL ONLY, never committed and never published (rule R2: the classes come from recent light residuals;
and the list names places singled out for a visit):
  field/pairs_<date>_<scope>.csv        one row per hromada in a pair or reserve (scope: all | <km>km, + oblasts)
  field/field_sheets_<date>_<scope>.md  one sheet per pair (L = light / functional, B = budgets / fiscal, -R = reserve):
                                the two hromadas, what the data say, the open questions, space for notes
  logs/43_pairs.log
field/ is outside the repository's whitelist (.gitignore denies /resilience/*), so nothing there can be staged.

Field rule (R6): notes record places, practices and institutions, never the names of people.

Questions reviewed 29 Sep 2026 before the first pairs (docs/pattern_language.md, 5.8): the outcome of the light pairs is no
longer named in question 1; question 2 asks for roles; question 4 asks for kinds and numbers, not stories; question 5
asks where the money comes from (the fiscal quality had no question); the sheet now says who is asked, what is seen
without asking, and since when each practice exists. A seventh question on how the hromada was formed is held in
reserve and asked only if the first two pairs leave it unreached.
"""
import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from sphere_common import BASE, CARP, TIDY, UNITS, LAEA, log, open_log, rd, zf

FIELD = BASE / "field"
OBL = {"21": "Zakarpattia", "26": "Ivano-Frankivsk", "46": "Lviv", "73": "Chernivtsi"}
QUALITY = {"func": ("quality_func", "composite_func", "functional (light kept in the summer-2024 outages and recently)"),
           "fisc": ("quality_fisc", "composite_fisc", "fiscal (tax base, cultural provision and own revenue held)")}
FAM_WORDS = {"s24": "light in the summer-2024 outages", "recent": "light level 2025–26",
             "econ": "tax base 2021→2025", "cult": "cultural provision 2021→2025", "own": "own revenue after Q4 2023"}
PROMPTS = """**Who is asked** (the same three in both hromadas of the pair, recorded by role only — rule R6): the council
(head, starosta or secretary); one institution (school, library, house of culture, church, fire unit, clinic); one
from the market, a shop or a farm.

**Open questions** (ask in both hromadas of the pair; do not bring the data or the expectations of Annex A)

1. What kept going here since 2022 — through the winters, the outages, the alerts? What stopped, and when?
2. When something failed, who decided what to do, and how fast? (Answer by role or institution — the head, the
   starosta, the school, the fire unit, the church, a farmer — never by name.) What did people do without being asked?
3. Where do people meet now? What happens there that did not happen before 2022?
4. Who came here since 2022 — how many, what kind of households — and what became of them: work, housing, school?
   Who left, and why?
5. What does the hromada make, grow, repair or store for itself? Where does the money for it come from — own means,
   the oblast, donors, people abroad?
6. What would you tell another hromada to do first?

**Seen without asking** (the observer's walk, before the conversations): the council building and its hours; the
market or shop; the school gate; the club or house of culture; the church; the notice board and what it announces;
generators, fuel, a heating point; fields worked or abandoned; houses repaired, new or empty; the bus.

**Observer's notes** (places, practices, institutions — never names of people, rule R6)

- Seen without asking:
- Seen here and not in the partner:
- Seen in the partner and not here:
- Said in both, in the words used:
- Since when, for each practice noted (before 2014 / 2014–21 / 2022 / 2024 — a condition or a response?):
- Candidate pattern (one sentence, if one appears):
"""


def htype(name):
    n = str(name).lower()
    return "city" if "міськ" in n else "settlement" if "селищ" in n else "village" if "сільськ" in n else "other"


def zs(x):
    x = pd.to_numeric(x, errors="coerce")
    sd = x.std()
    return (x - x.mean()) / sd if sd and sd > 0 else x * 0


def main():
    ap = argparse.ArgumentParser(description="round 3: pairs of hromadas to observe")
    ap.add_argument("--pairs", type=int, default=8, help="pairs in total, split evenly between the two qualities")
    ap.add_argument("--reserves", type=int, default=2, help="reserve pairs per quality")
    ap.add_argument("--oblasts", default=",".join(sorted(CARP)), help="oblast codes k1, comma-separated")
    ap.add_argument("--per-oblast", type=int, default=0, help="max pairs per oblast and quality (0 = spread evenly)")
    ap.add_argument("--caliper", type=float, default=1.0, help="max distance on population, strikes, alert hours (SD)")
    ap.add_argument("--base", default="2602003", help="k3 of the base for distances (default Verkhovyna)")
    ap.add_argument("--max-km", type=float, default=0, help="only hromadas within this straight-line distance (0 = all)")
    a = ap.parse_args()
    open_log("43_pairs")
    day = time.strftime("%Y-%m-%d")
    obls = [o.strip().zfill(2) for o in a.oblasts.split(",") if o.strip()]
    per_q = max(1, a.pairs // 2)
    cap = a.per_oblast or max(1, int(np.ceil(per_q / len(obls))))
    log(f"43_pairs.py  {day}  pairs={a.pairs} ({per_q} per quality)  reserves={a.reserves}/quality  oblasts={obls}  "
        f"per_oblast={cap}  caliper={a.caliper}  base={a.base}  max_km={a.max_km or '-'}")

    # ---- data ----------------------------------------------------------------------------------------------
    q = rd("quality_k3.csv")
    q = q[(q["pop"] == "outside") & q["k1"].isin(obls)].copy()
    pop = rd("population_k3.csv")
    q = q.merge(pop[["k3", "pop_ghs_2020"]], on="k3", how="left")
    idx = rd("resilience_index_v11_k3.csv", required=False)
    if idx is None:
        idx = zf(pd.read_csv(BASE / "public" / "resilience_index_v11_k3.csv", dtype={"k1": str, "k2": str, "k3": str}))
    q = q.merge(idx[["k3", "exp_strikes_log", "alert_h_12m"]], on="k3", how="left")
    q["htype"] = q["name"].map(htype)
    q["m_pop"] = zs(np.log(pd.to_numeric(q["pop_ghs_2020"], errors="coerce").clip(lower=1)))
    q["m_exp"] = zs(q["exp_strikes_log"])
    q["m_alert"] = zs(q["alert_h_12m"])
    for c in ("m_pop", "m_exp", "m_alert"):
        q[c] = q[c].fillna(0)

    q["km"] = np.nan
    try:
        import geopandas as gpd
        g = zf(gpd.read_file(UNITS, layer="hromada")[["k3", "geometry"]]).to_crs(LAEA)
        pts = g.set_index("k3").geometry.representative_point()
        if a.base in pts.index:
            b = pts[a.base]
            q["km"] = q["k3"].map(pts.distance(b) / 1000).round(0)
        else:
            log(f"note: base {a.base} not in the units layer; no distances")
    except Exception as ex:
        log(f"note: distances skipped ({ex})")
    if a.max_km:
        before = len(q)
        q = q[q["km"] <= a.max_km]
        log(f"within {a.max_km:.0f} km of the base: {len(q)} of {before} hromadas")
    log(f"hromadas in scope: {len(q)}  by type {q['htype'].value_counts().to_dict()}")
    for k, (qc, _, _) in QUALITY.items():
        log(f"  {k}: {q[qc].value_counts().to_dict()}")

    # ---- admissible pairs ----------------------------------------------------------------------------------
    cand = []
    for k, (qc, cc, _) in QUALITY.items():
        H = q[q[qc] == "held_up"]
        F = q[q[qc] == "faltered"]
        m = H.merge(F, on=["k1", "htype"], suffixes=("_h", "_f"))
        if m.empty:
            continue
        m["dist"] = np.sqrt((m["m_pop_h"] - m["m_pop_f"]) ** 2 + (m["m_exp_h"] - m["m_exp_f"]) ** 2
                            + (m["m_alert_h"] - m["m_alert_f"]) ** 2)
        m["contrast"] = pd.to_numeric(m[f"{cc}_h"], errors="coerce") - pd.to_numeric(m[f"{cc}_f"], errors="coerce")
        m = m[m["dist"] <= a.caliper].copy()
        m["quality"] = k
        cand.append(m)
        log(f"{k}: admissible pairs within the caliper {len(m)}")
    if not cand:
        raise SystemExit("no admissible pairs: widen --caliper, --oblasts or --max-km")
    C = pd.concat(cand, ignore_index=True).sort_values("contrast", ascending=False)

    # ---- greedy selection, alternating qualities -----------------------------------------------------------
    used, chosen, count = set(), [], {}
    target = {k: per_q + a.reserves for k in QUALITY}
    pools = {k: C[C["quality"] == k] for k in QUALITY}
    progress = True
    while progress:
        progress = False
        for k in QUALITY:
            n_k = sum(1 for r in chosen if r["quality"] == k)
            if n_k >= target[k]:
                continue
            role = "pair" if n_k < per_q else "reserve"
            free = pools[k][~pools[k]["k3_h"].isin(used) & ~pools[k]["k3_f"].isin(used)]
            if free.empty:
                continue
            spread = free[[count.get((k, o), 0) < cap for o in free["k1"]]] if role == "pair" else free
            pick = spread if not spread.empty else free     # spread the main pairs over the oblasts where possible
            r = pick.iloc[0]
            chosen.append({**r.to_dict(), "role": role})
            used |= {r["k3_h"], r["k3_f"]}
            count[(k, r["k1"])] = count.get((k, r["k1"]), 0) + 1
            progress = True
    if not chosen:
        raise SystemExit("no pairs selected")

    # ---- outputs (local) -----------------------------------------------------------------------------------
    FIELD.mkdir(exist_ok=True)
    rows, sheets = [], [f"# Field sheets — round 3, {day}\n\nLOCAL — do not publish or commit (rules R2, R6). "
                         f"Pairs: {per_q} functional and {per_q} fiscal, with reserves. Each pair: one hromada that held "
                         f"up and one that faltered on the same quality, same oblast and type, similar population and "
                         f"exposure.\n"]
    seq = {}
    for r in sorted(chosen, key=lambda r: (r["role"] != "pair", r["quality"], r["k1"])):
        pref = "L" if r["quality"] == "func" else "B"           # L = light (functional), B = budgets (fiscal)
        seq[pref] = seq.get(pref, 0) + 1
        pid = f"{pref}{seq[pref]}" + ("-R" if r["role"] == "reserve" else "")
        lines = [f"\n## {pid} — {QUALITY[r['quality']][2]}", f"\n{OBL.get(r['k1'], r['k1'])} oblast, {r['htype']} hromadas"
                 + (" (reserve)" if r["role"] == "reserve" else "") + "\n",
                 "| | Held up | Faltered |", "| --- | --- | --- |"]
        vals = {}
        for side in ("h", "f"):
            fams_top = [FAM_WORDS[f] for f in FAM_WORDS if pd.to_numeric(r.get(f"q_{f}_{side}"), errors="coerce") == 4]
            fams_bot = [FAM_WORDS[f] for f in FAM_WORDS if pd.to_numeric(r.get(f"q_{f}_{side}"), errors="coerce") == 1]
            vals[side] = {
                "name": r[f"name_{side}"], "pop": f"{pd.to_numeric(r[f'pop_ghs_2020_{side}'], errors='coerce'):,.0f}",
                "alert": f"{pd.to_numeric(r[f'alert_h_12m_{side}'], errors='coerce'):.0f}",
                "km": "" if pd.isna(r.get(f"km_{side}")) else f"{r[f'km_{side}']:.0f}",
                "top": "; ".join(fams_top) or "—", "bottom": "; ".join(fams_bot) or "—",
                "other": r.get(f"quality_{'fisc' if r['quality'] == 'func' else 'func'}_{side}", "")}
            rows.append({"pair": pid, "role": r["role"], "quality": r["quality"], "side": "held_up" if side == "h" else "faltered",
                         "k1": r["k1"], "k3": r[f"k3_{side}"], "name": r[f"name_{side}"], "htype": r["htype"],
                         "pop_2020": r[f"pop_ghs_2020_{side}"], "alert_h_12m": r[f"alert_h_12m_{side}"],
                         "km_from_base": r.get(f"km_{side}"), "top_families": vals[side]["top"],
                         "bottom_families": vals[side]["bottom"], "other_quality": vals[side]["other"],
                         "distance": round(r["dist"], 2), "contrast": round(r["contrast"], 2)})
        for lab, key in (("Hromada", "name"), ("Population 2020", "pop"), ("Alert hours, last 12 months", "alert"),
                         ("Km from base (straight line)", "km"),
                         ("Top quarter (all non-zone hromadas, given exposure and oblast) on", "top"),
                         ("Bottom quarter on", "bottom"), ("Other quality", "other")):
            lines.append(f"| {lab} | {vals['h'][key]} | {vals['f'][key]} |")
        lines.append(f"\nSimilarity distance {r['dist']:.2f} SD; contrast {r['contrast']:.2f}.\n\n{PROMPTS}")
        sheets.extend(lines)
        log(f"{pid:6s} {r['quality']}  {OBL.get(r['k1'], r['k1']):15s} {r['htype']:10s}  "
            f"held up: {r['name_h']}  |  faltered: {r['name_f']}  (dist {r['dist']:.2f}, contrast {r['contrast']:.2f}"
            + (f", {r.get('km_h', np.nan):.0f} / {r.get('km_f', np.nan):.0f} km" if pd.notna(r.get('km_h')) else "") + ")")
    tag = f"{day}_" + (f"{a.max_km:.0f}km" if a.max_km else "all") + (f"_{'-'.join(obls)}" if a.oblasts != ",".join(sorted(CARP)) else "")
    out = FIELD / f"pairs_{tag}.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    md = FIELD / f"field_sheets_{tag}.md"
    md.write_text("\n".join(sheets), encoding="utf-8")
    (FIELD / "README.txt").write_text("LOCAL field material for round 3 (docs/pattern_language.md 5.7). Never commit "
                                      "or publish: rules R2 and R6.\n", encoding="utf-8")
    n_pair = sum(1 for r in chosen if r["role"] == "pair")
    log(f"\nselected {n_pair} pairs and {len(chosen) - n_pair} reserves; wrote {out.relative_to(BASE)} and "
        f"{md.relative_to(BASE)} (local)")
    short = {k: per_q - sum(1 for r in chosen if r["quality"] == k and r["role"] == "pair") for k in QUALITY}
    if any(v > 0 for v in short.values()):
        log(f"short of the target: {short} — widen --caliper or --max-km, or add oblasts")
    log(json.dumps({"pairs_by_oblast": {f"{k}|{OBL.get(o, o)}": v for (k, o), v in count.items()}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
