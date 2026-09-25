#!/usr/bin/env python3
"""
16_oblast_context.py — oblast context layer: reSCORE citizen resilience + IDPs (one row per k1)

  python 16_oblast_context.py [--years 2024,2021]

reSCORE / SCORE Ukraine (SeeD, UNDP; General Population stream, public dashboard API):
  GET https://api.scoreforpeace.org/api/viz/map?language=en&country_id=ukraine&type=score
      &year=<Y>&data_stream=1&auth_key=      -> all indicators x regions (0-10 scale)
  Indicator names come from the dashboard tree (treeNav: dimension -> indicator -> row).
  2024: n = 7,758, face-to-face, government-controlled areas excl. Luhansk, Donetsk, Crimea.
  SeeD treats only differences > 0.5 points as significant.
IOM DTM (HDX "ukr-iom-dtm-from-api", admin 1, already in raw/dtm/):
  idp_present_est  operation "Displacement due to Conflict in Ukraine", latest date (where people live)
  idp_registered   operation "... (Registration)", latest date, summed over origin oblasts (where registered)
Outputs: tidy/rescore_long.csv (all indicators x oblasts x years), tidy/oblast_context_k1.csv
         (selected indicators + IDPs), resilience_maps.gpkg:oblast_context, dictionary rows,
         logs/16_oblast_context.log
"""
import argparse
import glob
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
QGIS = BASE.parent / "viina" / "qgis"
RAW = BASE / "raw" / "rescore"
TIDY, LOGS = BASE / "tidy", BASE / "logs"
for d in (RAW, TIDY, LOGS):
    d.mkdir(parents=True, exist_ok=True)
API = "https://api.scoreforpeace.org/api/viz/map"
HDR = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
       "Accept": "application/json"}
OBLAST_K1 = {
    "Vinnytsia": "05", "Volyn": "07", "Dnipropetrovsk": "12", "Donetsk": "14", "Zhytomyr": "18",
    "Zakarpattia": "21", "Zaporizhzhia": "23", "Ivano-Frankivsk": "26", "Kyiv oblast": "32",
    "Kirovohrad": "35", "Luhansk": "44", "Lviv": "46", "Mykolaiv": "48", "Odesa": "51", "Poltava": "53",
    "Rivne": "56", "Sumy": "59", "Ternopil": "61", "Kharkiv": "63", "Kherson": "65", "Khmelnytskyi": "68",
    "Cherkasy": "71", "Chernivtsi": "73", "Chernihiv": "74", "Kyiv": "80",
}
# context indicators: (short name, dashboard dimension, indicator name) — names repeat across
# dimensions ("overall", "all"), so the dimension is part of the key; '*' and case are ignored
SELECT = [
    ("trust_local_admin", "Trust in Institutions", "town or village administration"),
    ("community_cohesion", "Civic Attitudes & Behaviours", "Community cohesion"),
    ("civic_engagement", "Civic Attitudes & Behaviours", "Civic engagement"),
    ("belonging_settlement", "Belonging & Identity", "to the settlement"),
    ("economic_security", "Human Security", "Economic security"),
    ("mental_wellbeing", "Psychosocial Assets & Skills", "Mental wellbeing (Meta)"),
    ("locality_satisfaction", "Governance & Services", "Locality satisfaction"),
]
_logf = open(LOGS / "16_oblast_context.log", "w", encoding="utf-8")


def log(*a):
    m = " ".join(str(x) for x in a)
    print(m, flush=True)
    _logf.write(m + "\n")
    _logf.flush()


def region_k1(name):
    """Oblast rows ('<Name> oblast') and Kyiv city only; city boosters (Kharkiv, Odesa, Dnipro, ...)
    and contact-line strata are kept in the long table but not assigned to an oblast."""
    n = str(name).strip()
    if n == "Kyiv":
        return "80"
    if n.lower() == "kyiv oblast":
        return "32"
    if not re.search(r"\s+oblast$", n, flags=re.I) or n.lower().startswith("contact line"):
        return None
    return OBLAST_K1.get(re.sub(r"\s+oblast$", "", n, flags=re.I))


def norm(s):
    return re.sub(r"\s+", " ", str(s).replace("*", "")).strip().lower()


def load_year(year):
    f = RAW / f"viz_map_ukraine_{year}_score_1.json"
    if not f.exists():
        p = {"language": "en", "country_id": "ukraine", "type": "score", "year": year, "data_stream": 1, "auth_key": ""}
        u = API + "?" + urllib.parse.urlencode(p)
        try:
            b = urllib.request.urlopen(urllib.request.Request(u, headers=HDR), timeout=120).read()
        except Exception as e:
            log(f"{year}: request failed ({e})")
            return None
        f.write_bytes(b)
    js = json.loads(f.read_text(encoding="utf-8"))
    res = js.get("data", {}).get("resource", {})
    rows = res.get("data") or []
    names = {}

    def walk(nodes, dim=None):
        for n in nodes or []:
            d = dim or n.get("name")
            if n.get("target_row") not in (None, ""):
                names[int(n["target_row"])] = (d, n.get("name"))
            walk(n.get("children"), d)

    walk(res.get("treeNav"))
    rec = []
    for i, r in enumerate(rows):
        dim, ind = names.get(i, (None, None))
        for region, cell in (r.get("data") or {}).items():
            if not isinstance(cell, dict):
                continue
            title = cell.get("title")
            if ind is None and title and region == "Whole Sample":
                ind = title
            v = pd.to_numeric(str(cell.get("value", "")).replace(",", "."), errors="coerce")
            rec.append({"year": year, "row": i, "dimension": dim, "indicator": ind or title,
                        "region": region, "value": v})
    df = pd.DataFrame(rec)
    if df.empty:
        log(f"{year}: no rows")
        return None
    df["indicator"] = df.groupby("row")["indicator"].transform(lambda s: s.dropna().iloc[0] if s.notna().any() else None)
    df["k1"] = df["region"].map(region_k1)
    n_ind = df["row"].nunique()
    log(f"reSCORE {year}: {n_ind} indicator rows, regions {df['region'].nunique()} "
        f"(mapped to k1: {df.dropna(subset=['k1'])['k1'].nunique()}), "
        f"sample size {res.get('country', [{}])[0].get('sample_size')}")
    unm = sorted(set(df.loc[df["k1"].isna(), "region"]) - {"Whole Sample"})
    if unm:
        log(f"   regions not mapped to an oblast: {unm}")
    return df


def dtm_oblast():
    files = sorted(glob.glob(str(BASE / "raw" / "dtm" / "*admin_levels_0-1*.csv")))
    if not files:
        log("DTM admin 0-1 extract not found in raw/dtm/ — run 14_idp_dtm.py first")
        return None
    d = pd.read_csv(files[0], dtype=str, low_memory=False)
    d["date"] = pd.to_datetime(d["reportingDate"], errors="coerce")
    d["idp"] = pd.to_numeric(d["numPresentIdpInd"], errors="coerce")
    a1 = d[d["admin1Pcode"].fillna("").str.fullmatch(r"UA\d{2}")].copy()
    a1["k1"] = a1["admin1Pcode"].str[2:4]
    out = {}
    for label, pat in (("idp_present_est", r"^Displacement due to Conflict in Ukraine$"),
                       ("idp_registered", r"\(Registration\)")):
        g = a1[a1["operation"].fillna("").str.contains(pat, regex=True)]
        if g.empty:
            log(f"DTM: no rows for {label}")
            continue
        last = g["date"].max()
        gl = g[g["date"] == last]
        orig = gl.get("idpOriginAdmin1Pcode", pd.Series(index=gl.index, dtype=object)).fillna("")
        has_total = (orig == "").groupby(gl["k1"]).any()
        parts = []
        for k1, gg in gl.groupby("k1"):
            o = gg.get("idpOriginAdmin1Pcode", pd.Series(index=gg.index, dtype=object)).fillna("")
            parts.append((k1, gg.loc[o == "", "idp"].sum() if has_total.get(k1, False) and (o == "").any()
                          else gg["idp"].sum()))
        s = pd.Series(dict(parts), name=label)
        out[label] = s
        out[label + "_date"] = pd.Series(str(last.date()), index=s.index)
        log(f"DTM {label}: {last.date()}  oblasts {len(s)}  total {s.sum():,.0f}")
    return pd.DataFrame(out) if out else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", default="2024,2021")
    a = ap.parse_args()
    years = [int(y) for y in a.years.split(",")]

    frames = [f for f in (load_year(y) for y in years) if f is not None]
    if not frames:
        raise SystemExit("no reSCORE data")
    long = pd.concat(frames, ignore_index=True)
    long.to_csv(TIDY / "rescore_long.csv", index=False)
    log(f"wrote tidy/rescore_long.csv rows={len(long)}")

    latest = max(years)
    long["ind_norm"] = long["indicator"].map(norm)
    long["dim_norm"] = long["dimension"].map(norm)
    chosen, rows_by_year = {}, {}
    for short, dim, name in SELECT:
        rows_by_year[short] = {}
        for y in years:
            t = long[long["year"] == y].drop_duplicates("row")
            hit = t[(t["dim_norm"] == norm(dim)) & (t["ind_norm"] == norm(name))]
            if hit.empty:
                alt = t[t["ind_norm"] == norm(name)]
                hit = alt if len(alt) == 1 else hit
            if len(hit):
                rows_by_year[short][y] = int(hit.iloc[0]["row"])
        if latest in rows_by_year[short]:
            chosen[short] = name
            log(f"  {short:24s} <- [{dim}] '{name}'  rows {rows_by_year[short]}")
        else:
            log(f"  {short:24s} <- NOT FOUND in {latest}: [{dim}] '{name}'")

    pop = pd.read_csv(TIDY / "population_k3.csv", dtype={"k3": str})
    pop["k1"] = pop["k3"].str.zfill(7).str[:2]
    pop_k1 = pop.groupby("k1")["pop_ghs_2020"].sum()
    ob = long.dropna(subset=["k1"])
    wide = pd.DataFrame(index=sorted(set(ob["k1"])))
    wide.index.name = "k1"
    nat = long[long["region"] == "Whole Sample"]
    for short in chosen:
        for y, r in rows_by_year[short].items():
            s = ob[(ob["year"] == y) & (ob["row"] == r)].groupby("k1")["value"].mean()
            if len(s):
                wide[f"{short}_{y}"] = s
        if len(years) > 1 and f"{short}_{min(years)}" in wide:
            wide[f"{short}_chg"] = wide[f"{short}_{latest}"] - wide[f"{short}_{min(years)}"]
        v = nat[(nat["year"] == latest) & (nat["row"] == rows_by_year[short][latest])]["value"].dropna()
        if len(v):
            natv, how = float(v.iloc[0]), "whole-sample value"
        else:
            x = wide[f"{short}_{latest}"].dropna()
            w = pop_k1.reindex(x.index).fillna(0)
            natv, how = float((x * w).sum() / w.sum()), "population-weighted mean of oblast values (no whole-sample value)"
        wide[f"{short}_{latest}_vs_nat"] = wide[f"{short}_{latest}"] - natv
        wide.attrs.setdefault("national", {})[short] = (round(natv, 2), how)
        log(f"  national {short:24s} {natv:.2f}  ({how})")

    dtm = dtm_oblast()
    if dtm is not None:
        wide = wide.join(dtm, how="outer")
    wide["pop_ghs_2020"] = pop_k1
    for c in ("idp_present_est", "idp_registered"):
        if c in wide:
            wide[f"{c}_per1k"] = wide[c] / wide["pop_ghs_2020"] * 1e3
    wide = wide.reset_index()

    units = gpd.read_file(QGIS / "admin_units.gpkg", layer="oblast")[["k1", "name", "geometry"]]
    units["k1"] = units["k1"].astype(str).str.zfill(2)
    out = units.merge(wide, on="k1", how="left")
    out.drop(columns="geometry").to_csv(TIDY / "oblast_context_k1.csv", index=False)
    out.to_file(BASE / "resilience_maps.gpkg", layer="oblast_context", driver="GPKG", engine="pyogrio")
    log(f"\nwrote tidy/oblast_context_k1.csv and resilience_maps.gpkg:oblast_context ({len(out)} oblasts)")

    show = ["k1", "name"] + [f"{s}_{latest}" for s in chosen] + \
           [c for c in ("idp_present_est_per1k", "idp_registered_per1k") if c in out]
    log("\n" + out[show].sort_values("k1").round(2).to_string(index=False))
    if len(years) > 1:
        chg = [f"{s}_chg" for s in chosen if f"{s}_chg" in out]
        if chg:
            log(f"\nchange {min(years)} -> {latest} (points on 0-10; |change| > 0.5 = meaningful per SeeD):\n"
                + out[["name"] + chg].round(2).to_string(index=False))
    for s in chosen:
        c = f"{s}_{latest}"
        if c in out:
            v = out[c]
            log(f"  {c:32s} range {v.min():.1f}-{v.max():.1f}  spread {v.max() - v.min():.1f}  "
                f"oblasts {v.notna().sum()}")

    src_r = f"SCORE / reSCORE Ukraine (SeeD, UNDP), General Population, public dashboard api.scoreforpeace.org"
    lic_r = "SCORE public dashboard — cite SeeD/UNDP reSCORE Ukraine; aggregated oblast scores only"
    dims = {sh: d for sh, d, _ in SELECT}
    rows = [[f"{s}_{latest}", src_r, lic_r, "score 0-10", str(latest), "oblast (k1)",
             f"[{dims[s]}] '{ind}'; face-to-face survey, n={7758 if latest == 2024 else 'see source'}; excl. Luhansk, Donetsk, "
             "Crimea; differences < 0.5 not significant"] for s, ind in chosen.items()]
    if len(years) > 1:
        rows += [[f"{s}_chg", src_r, lic_r, "points", f"{min(years)}-{latest}", "oblast (k1)",
                  f"{s}_{latest} - {s}_{min(years)}; indicator definitions may differ between rounds"]
                 for s in chosen]
    src_d = "IOM DTM Ukraine via HDX (ukr-iom-dtm-from-api, admin 0-1)"
    lic_d = "IOM DTM terms of use — attribution required"
    rows += [["idp_present_est_per1k", src_d + " + JRC GHS-POP", lic_d, "per 1,000 pre-war residents", "latest",
              "oblast (k1)", "IOM estimate of IDPs present (where living) / oblast pop_ghs_2020 x 1,000"],
             ["idp_registered_per1k", src_d + " + JRC GHS-POP", lic_d, "per 1,000 pre-war residents", "latest",
              "oblast (k1)", "Registered IDPs (MoSP register, summed over origin oblasts) / pop_ghs_2020 x 1,000; "
              "counted where registered, not where living"]]
    dd_new = pd.DataFrame(rows, columns=["indicator", "source", "licence", "unit", "year", "level", "method"])
    ddp = TIDY / "data_dictionary.csv"
    dd = pd.read_csv(ddp, dtype=str) if ddp.exists() else pd.DataFrame(columns=dd_new.columns)
    dd = pd.concat([dd[~dd["indicator"].isin(dd_new["indicator"])], dd_new], ignore_index=True)
    dd.to_csv(ddp, index=False)
    log(f"data dictionary updated: {len(dd)} indicators")


if __name__ == "__main__":
    main()
