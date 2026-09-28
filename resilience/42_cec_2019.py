#!/usr/bin/env python3
"""
42_cec_2019.py — pre-war civic participation per hromada: turnout in the 2019 national elections by polling station.

  python 42_cec_2019.py probe            list the CEC's datasets on data.gov.ua and the DRV open-data links; sample columns
  python 42_cec_2019.py pull             download the resources named in RESOURCES to raw/cec2019/
  python 42_cec_2019.py build            polling stations -> settlements -> hromadas -> tidy/elections_2019_k3.csv

Why: the 2020 local elections give no structured turnout (33_elections_2020.py, probe of 27 Sep 2026). The 2019
presidential (31 March, 21 April) and parliamentary (21 July) elections were counted by polling station, with the
results open on data.gov.ua (Central Election Commission, CC BY) and the stations listed with their addresses by the
State Voter Register (drv.gov.ua, open data). Turnout per station, placed in its settlement and so in its hromada,
gives a pre-war measure of participation for every hromada — a rights-sphere condition the pattern-language round
lacks (docs/pattern_language.md, 6.1).

The exact resources and columns were not visible from Claude's workspace (28 Sep 2026): run `probe`, then set
RESOURCES and the two column maps (COLS_RESULTS for the results table, COLS_STATIONS for the station list) from its
output, then `pull` and `build`. Placement by settlement name reuses 34_schools.py (KATOTTG codifier; ambiguous
names dropped and counted). Rules: R6 — no candidate names or per-candidate figures leave this script, only voters,
ballots and turnout per hromada; polling-station addresses stay in raw/ (gitignored).

Output tidy/elections_2019_k3.csv: k1, k2, k3, name, per election (pres1, pres2, parl): voters_2019_<e>,
ballots_2019_<e>, turnout_2019_<e>, n_stations_<e>, share_stations_placed_<e>. Licence: CC BY (CEC); DRV open data
with attribution.
"""
import argparse
import importlib
import io
import json
import re
import sys
import time
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import requests

BASE = Path(__file__).resolve().parent
TIDY, RAW = BASE / "tidy", BASE / "raw" / "cec2019"
CKAN = "https://data.gov.ua/api/3/action"
CEC_ORG = "858f48bc-e753-4d61-a2f8-d3e7d2ce24e0"
DRV_OPEN = "https://www.drv.gov.ua/ords/portal/!cm_core.cm_index?option=ext_static_page&ppg_id=262&pmn_id=161"
OUT = TIDY / "elections_2019_k3.csv"
HEAD = {"User-Agent": "ubec-resilience/1.3 (stewardship@ubec.network)"}

# ---- to set after `probe` -------------------------------------------------------------------------------
# {election: [substrings of resource names or urls to download]}
RESOURCES = {
    "pres1": ["Президента", "1 тур"],
    "pres2": ["Президента", "2 тур"],
    "parl": ["народних депутатів", "2019"],
    "stations": [],          # the DRV polling-station list (url(s) pasted from the probe output)
}
# results table: source column -> role. Roles: ps (polling-station number), okrug (electoral district number),
# oblast, voters (voters on the list), ballots (ballots issued or votes cast), election (if one file holds several)
COLS_RESULTS = {}
# station list: ps, okrug, oblast, raion (optional), settlement (settlement name), address (optional)
COLS_STATIONS = {}


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def ckan(action, **params):
    r = requests.get(f"{CKAN}/{action}", params=params, headers=HEAD, timeout=60)
    r.raise_for_status()
    j = r.json()
    if not j.get("success"):
        sys.exit(f"CKAN error: {j}")
    return j["result"]


def read_any(content, name):
    name = name.lower()
    if name.endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            inner = [n for n in zf.namelist() if n.lower().endswith((".csv", ".xlsx", ".xls", ".json"))]
            if not inner:
                raise ValueError("zip without a readable file")
            return read_any(zf.read(inner[0]), inner[0])
    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(io.BytesIO(content), dtype=str)
    if name.endswith(".json"):
        j = json.loads(content.decode("utf-8", errors="replace"))
        return pd.json_normalize(j if isinstance(j, list) else next(v for v in j.values() if isinstance(v, list)))
    for enc in ("utf-8-sig", "utf-8", "cp1251"):
        for sep in (",", ";", "\t"):
            try:
                df = pd.read_csv(io.BytesIO(content), dtype=str, sep=sep, encoding=enc, low_memory=False)
                if df.shape[1] > 1:
                    return df
            except Exception:
                continue
    raise ValueError(f"could not parse {name}")


def sample(url, name):
    try:
        r = requests.get(url, headers=HEAD, timeout=120, stream=True)
        r.raise_for_status()
        chunk = next(r.iter_content(chunk_size=3_000_000))
        df = read_any(chunk, url.split("?")[0] or name)
        log(f"    columns ({df.shape[1]}): {list(df.columns)[:40]}")
        log("    first rows:\n" + df.head(2).to_string()[:1500])
    except Exception as ex:
        log(f"    (could not read a sample: {ex})")


def cmd_probe():
    log("== CEC datasets on data.gov.ua")
    res = ckan("package_search", fq=f"owner_org:{CEC_ORG}", rows=200)
    if res["count"] == 0:
        res = ckan("package_search", q="Результати виборів Президента України 2019", rows=50)
    log(f"{res['count']} datasets")
    for pk in res["results"]:
        title = pk.get("title", "")
        if not re.search(r"2019|Президент|народних депутатів|дільниц", title, re.I):
            continue
        log(f"\n[{pk['name']}] {title}  licence={pk.get('license_title')}  modified={pk.get('metadata_modified')}")
        for r in pk.get("resources", []):
            log(f"  - {r.get('name')}  format={r.get('format')}  size={r.get('size')}\n    url: {r.get('url')}")
            if re.search(r"2019|Президент", (r.get("name") or "") + title, re.I):
                sample(r["url"], r.get("name") or "")
    log("\n== polling-station lists on data.gov.ua (State Voter Register / CEC)")
    for q in ("виборчі дільниці", "перелік виборчих дільниць", "Державний реєстр виборців"):
        try:
            hits = ckan("package_search", q=q, rows=20)
            for pk in hits["results"]:
                log(f"  [{pk['name']}] {pk.get('title')}  org={pk.get('organization', {}).get('title')}  "
                    f"licence={pk.get('license_title')}")
                for r in pk.get("resources", [])[:8]:
                    log(f"      - {r.get('name')}  {r.get('format')}  {r.get('url')}")
        except Exception as ex:
            log(f"  ({q}: {ex})")
    log("\n== State Voter Register open data page (polling stations with addresses)")
    try:
        r = requests.get(DRV_OPEN, headers=HEAD, timeout=60, allow_redirects=False)
        if r.is_redirect:
            log(f"  redirected to {r.headers.get('Location')} — open it in a browser; the server refuses the plain-http hop from here")
        r.raise_for_status()
        links = re.findall(r'href="([^"]+\.(?:xlsx|xls|csv|zip|json)[^"]*)"', r.text, re.I)
        for l in links[:60]:
            log("  " + l)
        if not links:
            log("  no file links found on the page; open it in a browser and paste the links for the station list")
    except Exception as ex:
        log(f"  (page not readable: {ex})")
    log("\nNext: set RESOURCES, COLS_RESULTS and COLS_STATIONS from this output, then `pull` and `build`.")


def cmd_pull():
    RAW.mkdir(parents=True, exist_ok=True)
    res = ckan("package_search", fq=f"owner_org:{CEC_ORG}", rows=200)
    if res["count"] == 0:
        res = ckan("package_search", q="Результати виборів Президента України 2019", rows=50)
    all_res = [(pk.get("title", ""), r) for pk in res["results"] for r in pk.get("resources", [])]
    for el, subs in RESOURCES.items():
        if not subs:
            continue
        hits = []
        for title, r in all_res:
            hay = f"{title} {r.get('name')} {r.get('url')}"
            if all(s.lower() in hay.lower() for s in subs) or any(s.startswith("http") and s == r.get("url") for s in subs):
                hits.append(r)
        for s in subs:
            if s.startswith("http") and not any(r.get("url") == s for r in hits):
                hits.append({"name": el, "url": s, "format": s.rsplit(".", 1)[-1]})
        if not hits:
            log(f"{el}: no resource matched {subs}")
            continue
        for i, r in enumerate(hits):
            fn = RAW / f"{el}_{i}.{(r.get('format') or 'bin').lower()}"
            log(f"{el}: {r.get('name')} -> {fn.relative_to(BASE)}")
            with requests.get(r["url"], headers=HEAD, timeout=900, stream=True) as g:
                g.raise_for_status()
                with open(fn, "wb") as f:
                    for chunk in g.iter_content(chunk_size=8_000_000):
                        f.write(chunk)
    (RAW / "meta.json").write_text(json.dumps({"accessed": time.strftime("%Y-%m-%d"), "resources": RESOURCES},
                                              ensure_ascii=False, indent=1), encoding="utf-8")


def load(prefix, cols):
    files = sorted(RAW.glob(f"{prefix}_*"))
    if not files:
        return None
    df = pd.concat([read_any(p.read_bytes(), p.name) for p in files], ignore_index=True)
    return df.rename(columns={k: v for k, v in cols.items() if k in df})


def cmd_build():
    if not COLS_RESULTS or not COLS_STATIONS:
        sys.exit("set COLS_RESULTS and COLS_STATIONS from the probe output first")
    sys.path.insert(0, str(BASE))
    s34 = importlib.import_module("34_schools")
    st = load("stations", COLS_STATIONS)
    if st is None:
        sys.exit("no station list in raw/cec2019 (RESOURCES['stations'])")
    need = {"ps", "oblast", "settlement"}
    if not need <= set(st.columns):
        sys.exit(f"station list needs {need}; has {list(st.columns)}")
    # place stations in hromadas by settlement name within oblast (34_schools.place: unique / ambiguous / none)
    v = pd.DataFrame({"SOBL": st["oblast"], "SPNT": st["settlement"]})
    placed = s34.place(v, pd.DataFrame({"settlement": []}))
    st["k3"] = placed["k3"].values
    st["res"] = placed["res"].values
    log(f"stations {len(st)}: placed {st['res'].value_counts().to_dict()}")
    st["ps"] = st["ps"].astype(str).str.extract(r"(\d+)")[0]
    st["okrug"] = st["okrug"].astype(str).str.extract(r"(\d+)")[0] if "okrug" in st else ""
    key = ["ps", "okrug"] if "okrug" in st else ["ps"]

    keys = pd.read_csv(TIDY / "keys_hromada.csv", dtype=str)[["k1", "k2", "k3", "name"]]
    out = keys.copy()
    for el in ("pres1", "pres2", "parl"):
        r = load(el, COLS_RESULTS)
        if r is None:
            log(f"{el}: no results file, skipped")
            continue
        for c in ("voters", "ballots"):
            r[c] = pd.to_numeric(r[c].astype(str).str.replace(r"[^\d]", "", regex=True), errors="coerce")
        r["ps"] = r["ps"].astype(str).str.extract(r"(\d+)")[0]
        if "okrug" in r:
            r["okrug"] = r["okrug"].astype(str).str.extract(r"(\d+)")[0]
        m = r.merge(st[key + ["k3"]].drop_duplicates(key), on=[k for k in key if k in r], how="left")
        share = m["k3"].notna().mean()
        g = m.dropna(subset=["k3"]).groupby("k3").agg(voters=("voters", "sum"), ballots=("ballots", "sum"),
                                                        n=("ps", "count"))
        g[f"turnout_2019_{el}"] = g["ballots"] / g["voters"].where(g["voters"] > 0)
        g = g.rename(columns={"voters": f"voters_2019_{el}", "ballots": f"ballots_2019_{el}", "n": f"n_stations_{el}"})
        out = out.merge(g.reset_index(), on="k3", how="left")
        out[f"share_stations_placed_{el}"] = round(float(share), 3)
        log(f"{el}: stations {len(r)}, placed {share:.1%}, hromadas with a value {int(g.shape[0])}, "
            f"median turnout {g[f'turnout_2019_{el}'].median():.3f}")
    out.to_csv(OUT, index=False)
    log(f"wrote {OUT.relative_to(BASE)}")
    dd_fn = TIDY / "data_dictionary.csv"
    if dd_fn.exists():
        src = "CEC 2019 results by polling station (data.gov.ua, CC BY) + State Voter Register station list"
        lic = "CC BY (CEC); DRV open data with attribution; counts per hromada only (R6)"
        rows = [(f"turnout_2019_{el}", src, lic, "share", "2019", "hromada",
                 f"ballots / voters on the list, summed over the polling stations placed in the hromada ({el}: "
                 f"{'presidential round 1' if el == 'pres1' else 'presidential round 2' if el == 'pres2' else 'parliamentary'})")
                for el in ("pres1", "pres2", "parl")]
        new = pd.DataFrame(rows, columns=["indicator", "source", "licence", "unit", "year", "level", "method"])
        dd = pd.read_csv(dd_fn)
        dd = dd[~dd["indicator"].astype(str).str.startswith("turnout_2019_")]
        for c in dd.columns:
            if c not in new:
                new[c] = ""
        pd.concat([dd, new[dd.columns]], ignore_index=True).to_csv(dd_fn, index=False)


def main():
    ap = argparse.ArgumentParser(description="2019 turnout per hromada")
    ap.add_argument("cmd", choices=("probe", "pull", "build"))
    a = ap.parse_args()
    {"probe": cmd_probe, "pull": cmd_pull, "build": cmd_build}[a.cmd]()


if __name__ == "__main__":
    main()
