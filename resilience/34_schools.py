#!/usr/bin/env python3
"""
34_schools.py — general secondary schools and pupils per hromada (k3). Cultural-sphere input
(resilience/docs/threefolding_framework.md, section 6, step 4b).

  python 34_schools.py probe [--rg 26]

Sources (Ministry of Education and Science):
  ZNZ-1     administrative report form ЗНЗ-1 per school, data.gov.ua dataset
            cbcab622-d464-4c25-ab64-247c7e9a6122, CC BY 4.0. One sheet, one row per school (15,676),
            2,675 columns: 11 descriptive columns (SNAME name, SOBL oblast, SRJN raion, SPNT settlement,
            SADDR address, SPINX postal code, SOWN ownership, SLCT urban/rural, SPHN phone, SEML e-mail,
            SOP) and the form indicators "ЗНЗ1 <section>.<row>.<col>". No KATOTTG or EDRPOU.
            Pre-war content (schools in places occupied since 2022 are present): a 2021 baseline.
  register  ЄДЕБО, Реєстр суб'єктів освітньої діяльності (general secondary, ut=3). Endpoint variants
            are probed; licence statement to be confirmed.

Location: schools are placed in a hromada through the KATOTTG codifier (viina/katottg.csv, CC BY
4.0): oblast + settlement name (+ raion where given). Ambiguous names are dropped, never guessed.

Rules. R6/R7: this script never prints or stores a school's name, address, postal code, phone or
e-mail; only column names, category counts and match rates. Results are counts per hromada. Language
fields are never used at hromada level.
"""
import argparse
import importlib
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent
TIDY, LOGS = BASE / "tidy", BASE / "logs"
RAW = BASE / "raw" / "schools"
ZNZ_XLSX = RAW / "sc_info_znz1_out.xlsx"
ZNZ_META = RAW / "znz1_meta.pkl"      # descriptive columns only (local, not tracked)
ZNZ_URL = ("https://data.gov.ua/dataset/7091f713-b44e-4362-a48a-3a528cb64446/resource/"
           "eb236da2-eca9-4dc2-8773-a726d50dd3b2/download/sc_info_znz1_out.xlsx")
META = ["SNAME", "SOBL", "SRJN", "SPNT", "SADDR", "SPINX", "SOWN", "SLCT", "SPHN", "SEML", "SOP"]
PRIVATE = {"SNAME", "SADDR", "SPINX", "SPHN", "SEML"}     # never printed, never stored downstream
REG_VARIANTS = [
    "https://registry.edbo.gov.ua/api/opendata/institutions/?ut=3&rg={rg}&exp=json",
    "https://registry.edbo.gov.ua/api/opendata/institutions/?ut=3&lc={rg}&exp=json",
    "https://registry.edbo.gov.ua/api/universities/?ut=3&lc={rg}&exp=json",
    "https://registry.edbo.gov.ua/api/institutions/?ut=3&lc={rg}&exp=json",
]
HDR = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
       "Accept": "application/json,*/*", "Referer": "https://registry.edbo.gov.ua/opendata/institutions"}
CODIFIER = [BASE.parent / "viina" / "katottg.csv", BASE.parent / "viina" / "qgis" / "katottg.csv"]
SAFE_FIELD = re.compile(r"(^id$|_id$|code|koatuu|katott|region_id|type|status|financ|ownership|"
                        r"level|category|kind|year|count|qty)", re.I)
UNSAFE_FIELD = re.compile(r"(boss|head|director|fio|pib|name|phone|tel|fax|mail|site|www|address|"
                          r"adres|street|house|post|zip|index|lat|lon|coord)", re.I)
_logf = None


def log(*a):
    m = " ".join(str(x) for x in a)
    print(m, flush=True)
    if _logf:
        _logf.write(m + "\n")
        _logf.flush()


def open_log(name):
    global _logf
    LOGS.mkdir(exist_ok=True)
    _logf = open(LOGS / name, "w", encoding="utf-8")


def get(url, timeout=300, tries=3):
    for att in range(1, tries + 1):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HDR), timeout=timeout) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            if e.code in (400, 403, 404):
                return e.code, b""
        except Exception as e:
            log(f"  attempt {att}: {type(e).__name__}")
        time.sleep(5 * att)
    return None, b""


# ---------------------------------------------------------------- register
def probe_register(rg):
    log(f"\n=== register (EDBO), general secondary, region {rg}")
    for tpl in REG_VARIANTS:
        url = tpl.format(rg=rg)
        st, body = get(url)
        log(f"  {st}  {len(body) / 1e6:6.2f} MB  {url.split('edbo.gov.ua')[1]}")
        if st != 200 or not body:
            continue
        try:
            data = json.loads(body.decode("utf-8-sig"))
        except Exception:
            log(f"    not JSON: {body[:60]!r}")
            continue
        recs = data if isinstance(data, list) else next((v for v in data.values() if isinstance(v, list)), [])
        df = pd.json_normalize(recs)
        log(f"    records={len(df)} fields={len(df.columns)}")
        for c in df.columns:
            shown = "(not shown)"
            if SAFE_FIELD.search(c) and not UNSAFE_FIELD.search(c):
                v = df[c].dropna().astype(str)
                shown = ", ".join(v.head(3)) if len(v) else "(empty)"
            log(f"      {c:40s} non-null={int(df[c].notna().sum()):5d}  e.g. {shown}")
        return df
    log("  no endpoint variant answered with data")
    return None


# ---------------------------------------------------------------- ZNZ-1
def znz_meta():
    RAW.mkdir(parents=True, exist_ok=True)
    if ZNZ_META.exists():
        return pd.read_pickle(ZNZ_META)
    if not ZNZ_XLSX.exists():
        st, body = get(ZNZ_URL, timeout=1200)
        if st != 200:
            raise SystemExit(f"ZNZ-1 download failed: HTTP {st}")
        ZNZ_XLSX.write_bytes(body)
    log(f"  reading descriptive columns of {ZNZ_XLSX.name} (slow the first time)")
    m = pd.read_excel(ZNZ_XLSX, usecols=META, dtype=str)
    m.to_pickle(ZNZ_META)
    return m


def norm(s):
    s = str(s).lower().replace("’", "'").replace("ʼ", "'").replace("`", "'")
    s = re.sub(r"\([^)]*\)", " ", s)
    s = re.sub(r"^(м\.|смт\.?|с\.|с-ще|селище|село|місто)\s*", "", s.strip())
    return re.sub(r"[^0-9a-zа-яіїєґ']+", "", s).replace("'", "")


def obl_norm(s):
    s = str(s).lower().split("/")[0]
    s = re.sub(r"\b(область|обл\.|автономна республіка|м\.|місто)\s*", " ", s)
    return norm(s)


def settlements():
    p = next((c for c in CODIFIER if c.exists()), None)
    if p is None:
        raise SystemExit("katottg.csv not found in viina/ or viina/qgis/")
    cod = pd.read_csv(p, dtype=str)
    log(f"  codifier {p.relative_to(BASE.parent)}: rows={len(cod)} columns={list(cod.columns)}")
    log(f"  levels: {cod['level'].value_counts().sort_index().to_dict()}")
    sys.path.insert(0, str(BASE))
    ob = importlib.import_module("03_openbudget")
    cod = cod[cod["code"].str.match(r"^UA\d{17}$", na=False)].copy()
    cod["k3"], _ = ob.katottg_parts(cod["code"].astype("string"))
    cod["oo"] = cod["code"].str[2:4]
    obl = cod[cod["level"] == "1"].set_index("oo")["name"].map(obl_norm)
    s = cod[cod["level"] == "4"].copy()
    s["obl"] = s["oo"].map(obl)
    s["nn"] = s["name"].map(norm)
    return s, obl


def probe_znz():
    log("\n=== ZNZ-1")
    m = znz_meta()
    head = pd.read_excel(ZNZ_XLSX, nrows=0).columns.tolist() if ZNZ_XLSX.exists() else []
    ind = [c for c in head if str(c).startswith("ЗНЗ1")]
    log(f"  schools={len(m)}  indicator columns={len(ind)}")
    sec = pd.Series([re.sub(r"^ЗНЗ1\s+", "", c).split(".")[0] for c in ind]).value_counts().sort_index()
    log("  indicator columns per form section: " + ", ".join(f"{k}:{v}" for k, v in sec.items()))
    rows = pd.Series([".".join(re.sub(r"^ЗНЗ1\s+", "", c).split(".")[:2]) for c in ind]).value_counts()
    log("  largest section.row blocks: " + ", ".join(f"{k}:{v}" for k, v in rows.head(12).items()))
    for c in ("SOWN", "SLCT", "SOP"):
        log(f"  {c}: {m[c].value_counts(dropna=False).head(8).to_dict()}")
    log(f"  SRJN (raion) given: {m['SRJN'].notna().mean():.2%}")
    log("  schools per oblast: " + ", ".join(f"{k.split()[0]}={v}" for k, v in m["SOBL"].value_counts().items()))

    s, obl = settlements()
    m = m.copy()
    m["obl"] = m["SOBL"].map(lambda n: obl_norm(n) if pd.notna(n) else None)
    m["nn"] = m["SPNT"].map(norm)
    known = set(obl.values)
    log(f"  oblast names matched to codifier: {m['obl'].isin(known).mean():.2%}")
    grp = s.groupby(["obl", "nn"])["k3"].agg(lambda x: sorted(set(x.dropna())))
    look = m.join(grp, on=["obl", "nn"])
    n_k3 = look["k3"].map(lambda v: len(v) if isinstance(v, list) else 0)
    look["res"] = n_k3.map(lambda n: "unique" if n == 1 else ("none" if n == 0 else "ambiguous"))
    log(f"\n  settlement -> hromada (oblast + settlement name): {look['res'].value_counts(normalize=True).round(3).to_dict()}")
    for t, g in look.groupby(look["SLCT"].fillna("?")):
        log(f"    {t:10s} n={len(g):5d}  " + str(g["res"].value_counts(normalize=True).round(3).to_dict()))
    amb = look[look["res"] == "ambiguous"]
    if len(amb):
        log(f"  ambiguous: median {n_k3[look['res'] == 'ambiguous'].median():.0f} candidate hromadas per name")
    hit = look.loc[look["res"] == "unique", "k3"].map(lambda v: v[0])
    keys = pd.read_csv(TIDY / "keys_hromada.csv", dtype=str)
    log(f"  hromadas with >= 1 uniquely placed school: {hit.nunique()} of {keys['k3'].nunique()}")
    by = look.assign(ok=look["res"] == "unique").groupby("SOBL")["ok"].mean().round(2)
    log("  unique share by oblast: " + ", ".join(f"{k.split()[0]}={v}" for k, v in by.items()))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("mode", choices=["probe"])
    ap.add_argument("--rg", default="26")
    a = ap.parse_args()
    open_log("34_probe.log")
    probe_register(a.rg)
    probe_znz()


if __name__ == "__main__":
    main()
