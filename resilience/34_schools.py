#!/usr/bin/env python3
"""
34_schools.py — general secondary schools and pupils per hromada (k3). Cultural-sphere input
(resilience/docs/threefolding_framework.md, section 6, step 4b).

  python 34_schools.py probe [--rg 26]     # one oblast from the register + the national ZNZ-1 file

Sources (Ministry of Education and Science):
  register  ЄДЕБО, Реєстр суб'єктів освітньої діяльності, open data export of general secondary
            schools (ut=3) per region: registry.edbo.gov.ua/api/opendata/institutions/?ut=3&rg=<rg>&exp=json
            State open data (CMU Resolution 835); licence statement to be confirmed.
  ZNZ-1     administrative report form ЗНЗ-1 per school, data.gov.ua dataset
            cbcab622-d464-4c25-ab64-247c7e9a6122, CC BY 4.0: pupils by grade, classes, clubs, staff, …

Rules. R7: schools are counted per hromada, never mapped or listed by location; language-of-
instruction fields are never used at hromada level. R6: names of directors, phones, e-mails and
addresses are never printed or stored — the probe prints field names, and example values only for
code-like fields (whitelist).

probe   register: fields, record count, the location field and its format, match to k3 for one
        oblast; ZNZ-1: sheets, header rows, row counts, identifier and year columns.
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
REG_URL = "https://registry.edbo.gov.ua/api/opendata/institutions/?ut=3&rg={rg}&exp=json"
ZNZ_URL = ("https://data.gov.ua/dataset/7091f713-b44e-4362-a48a-3a528cb64446/resource/"
           "eb236da2-eca9-4dc2-8773-a726d50dd3b2/download/sc_info_znz1_out.xlsx")
HDR = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
       "Accept": "application/json,*/*"}
SAFE = re.compile(r"(^id$|_id$|code|koatuu|katott|region|type|status|financ|ownership|owner|"
                  r"level|edrpou|edebo|parent|category|kind|form|year|date|count|number|qty)", re.I)
UNSAFE = re.compile(r"(boss|head|director|fio|pib|name|phone|tel|fax|mail|site|www|address|adres|"
                    r"street|house|post|zip|index|lat|lon|coord)", re.I)
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


def get(url, timeout=300, tries=4):
    for att in range(1, tries + 1):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HDR), timeout=timeout) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            if e.code in (404, 400):
                return e.code, b""
            log(f"  attempt {att}: HTTP {e.code}")
        except Exception as e:
            log(f"  attempt {att}: {type(e).__name__}")
        time.sleep(5 * att)
    return None, b""


def safe_example(col, series):
    if UNSAFE.search(col) or not SAFE.search(col):
        return "(not shown)"
    v = series.dropna().astype(str)
    return ", ".join(v.head(3).tolist()) if len(v) else "(empty)"


# ---------------------------------------------------------------- register
def probe_register(rg):
    log(f"\n=== register, region rg={rg}")
    st, body = get(REG_URL.format(rg=rg))
    log(f"  HTTP {st}, {len(body) / 1e6:.2f} MB")
    if st != 200 or not body:
        return None
    RAW.mkdir(parents=True, exist_ok=True)
    try:
        data = json.loads(body.decode("utf-8-sig"))
    except Exception as e:
        log(f"  not JSON ({e}); first bytes: {body[:120]!r}")
        return None
    recs = data if isinstance(data, list) else next((v for v in data.values() if isinstance(v, list)), [])
    if isinstance(data, dict):
        log(f"  top-level keys: {list(data)[:15]}")
    df = pd.json_normalize(recs)
    log(f"  records: {len(df)}   fields: {len(df.columns)}")
    for c in df.columns:
        nn = int(df[c].notna().sum())
        log(f"    {c:45s} non-null={nn:5d}  e.g. {safe_example(c, df[c])}")
    return df


def locate(df):
    """Find a KATOTTG-like (UA + 17 digits) or KOATUU-like (10 digits) field; report k3 match."""
    sys.path.insert(0, str(BASE))
    ob = importlib.import_module("03_openbudget")
    keys = pd.read_csv(TIDY / "keys_hromada.csv", dtype=str)
    for c in df.columns:
        v = df[c].dropna().astype(str).str.strip()
        if not len(v):
            continue
        kat = v.str.upper().str.fullmatch(r"UA\d{17}").mean()
        koa = v.str.fullmatch(r"\d{10}").mean()
        if kat > 0.5:
            k3, _ = ob.katottg_parts(df[c].astype("string"))
            hit = k3.isin(set(keys["k3"])).mean()
            log(f"  location field {c}: KATOTTG share={kat:.2f}; -> k3 matched {hit:.2%}; "
                f"hromadas covered: {k3.dropna().nunique()}")
        elif koa > 0.5:
            log(f"  field {c}: looks like KOATUU (10 digits, share {koa:.2f}) — needs a KOATUU->KATOTTG table")


# ---------------------------------------------------------------- ZNZ-1
def probe_znz():
    log("\n=== ZNZ-1 national file")
    RAW.mkdir(parents=True, exist_ok=True)
    p = RAW / "sc_info_znz1_out.xlsx"
    if not p.exists():
        st, body = get(ZNZ_URL, timeout=900)
        log(f"  HTTP {st}, {len(body) / 1e6:.1f} MB")
        if st != 200 or not body:
            return
        p.write_bytes(body)
    else:
        log(f"  cached {p} ({p.stat().st_size / 1e6:.1f} MB)")
    xl = pd.ExcelFile(p)
    log(f"  sheets ({len(xl.sheet_names)}): {xl.sheet_names[:30]}")
    for sh in xl.sheet_names[:6]:
        raw = xl.parse(sh, header=None, nrows=8, dtype=str)
        n = len(xl.parse(sh, header=None, usecols=[0], dtype=str))
        log(f"\n  sheet '{sh}': rows={n} cols={raw.shape[1]}")
        for i in range(min(6, len(raw))):
            cells = [str(x)[:28] for x in raw.iloc[i].tolist()[:18]]
            log(f"    r{i}: " + " | ".join(cells))
    first = xl.parse(xl.sheet_names[0], header=None, dtype=str)
    for j in range(min(first.shape[1], 40)):
        v = first.iloc[:, j].dropna().astype(str).str.strip()
        if len(v) < 20:
            continue
        s = {"edrpou8": v.str.fullmatch(r"\d{8}").mean(), "katottg": v.str.upper().str.fullmatch(r"UA\d{17}").mean(),
             "koatuu10": v.str.fullmatch(r"\d{10}").mean(), "year": v.str.fullmatch(r"20\d\d(/20\d\d|-20\d\d)?").mean()}
        hit = {k: round(x, 2) for k, x in s.items() if x > 0.3}
        if hit:
            log(f"  column {j} ({first.iloc[0, j]!s:.30}): {hit}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("mode", choices=["probe"])
    ap.add_argument("--rg", default="26")
    a = ap.parse_args()
    open_log("34_probe.log")
    df = probe_register(a.rg)
    if df is not None and len(df):
        locate(df)
    probe_znz()


if __name__ == "__main__":
    main()
