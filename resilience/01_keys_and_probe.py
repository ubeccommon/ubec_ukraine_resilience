#!/usr/bin/env python3
"""
01_keys_and_probe.py  —  resilience step 4a
  A. load our hromada keys (k1/k2/k3) from ../viina/qgis/admin_units.gpkg
  B. print schema of the occupation mask (hromada_control.gpkg)
  C. pull OCHA COD-AB ADM3 attributes (no geometry) from the ITOS FeatureServer
  D. test ADM3_PCODE == "UA" + k3, ADM2 consistency, name agreement
  E. probe openbudget.gov.ua local-budget CSV endpoints (format check only)
  F. create tidy/data_dictionary.csv scaffold
Outputs: raw/cod_ab/, raw/openbudget_probe/, tidy/keys_hromada.csv,
         tidy/crosswalk_k3_codpcode.csv, logs/01_keys_and_probe.log
"""
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd
import pyogrio

BASE = Path(__file__).resolve().parent
VIINA = BASE.parent / "viina"
QGIS = VIINA / "qgis"
RAW, TIDY, LOGS = BASE / "raw", BASE / "tidy", BASE / "logs"
for d in (RAW / "cod_ab", RAW / "openbudget_probe", TIDY, LOGS):
    d.mkdir(parents=True, exist_ok=True)

LOGFILE = LOGS / "01_keys_and_probe.log"
_logf = open(LOGFILE, "w", encoding="utf-8")


def log(*a):
    msg = " ".join(str(x) for x in a)
    print(msg)
    _logf.write(msg + "\n")
    _logf.flush()


HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) resilience-research/0.1",
           "Accept": "*/*"}


def get(url, params=None, timeout=90):
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.headers.get("Content-Type", ""), r.read(), url
    except urllib.error.HTTPError as e:
        body = e.read() if hasattr(e, "read") else b""
        return e.code, (e.headers.get("Content-Type", "") if e.headers else ""), body, url
    except Exception as e:  # network, timeout, DNS
        return None, type(e).__name__, str(e).encode(), url


def norm_code(s, n):
    s = s.astype("string").str.strip().str.replace(r"\.0$", "", regex=True)
    return s.str.zfill(n)


def norm_name(s):
    s = s.astype("string").str.lower().fillna("")
    s = s.str.replace(r"[’'ʼ`\"]", "", regex=True)
    s = s.str.replace(r"\b(територіальна|громада|міська|сільська|селищна|тг)\b", "", regex=True)
    return s.str.replace(r"[^0-9a-zа-яіїєґ]+", "", regex=True)


def decode(b):
    for enc in ("utf-8-sig", "cp1251"):
        try:
            return b.decode(enc), enc
        except UnicodeDecodeError:
            continue
    return b.decode("latin-1", errors="replace"), "latin-1"


# ---------------------------------------------------------------- A. our keys
log("=" * 70)
log("A. Our hromada keys")
gpkg = QGIS / "admin_units.gpkg"
if not gpkg.exists():
    sys.exit(f"missing {gpkg}")
layers = pyogrio.list_layers(gpkg)
log("admin_units.gpkg layers:", [(str(l[0]), str(l[1])) for l in layers])

chosen = None
for lname, _ in layers:
    df = pyogrio.read_dataframe(gpkg, layer=lname, read_geometry=False)
    if "level" in df.columns:
        sub = df[df["level"].astype("string").str.lower().str.startswith("hrom")]
        if len(sub) and "k3" in sub.columns:
            chosen = (lname, sub.copy())
            break
    if "k3" in df.columns and ("hrom" in lname.lower() or 1700 < len(df) < 1800):
        chosen = (lname, df.copy())
if chosen is None:
    sys.exit("could not find a hromada layer with a k3 column — paste the layer list above")

lname, ours = chosen
log(f"using layer '{lname}', rows={len(ours)}, columns={list(ours.columns)}")
ours["k3"] = norm_code(ours["k3"], 7)
ours["k1"] = ours["k3"].str[:2]
ours["k2"] = ours["k3"].str[:4]
name_cols = [c for c in ours.columns if re.search(r"name|назв|_ua|_uk", c, re.I)]
log("name columns detected:", name_cols)
dups = ours["k3"].duplicated().sum()
bad = (~ours["k3"].str.fullmatch(r"\d{7}")).sum()
log(f"k3 unique={ours['k3'].nunique()}  duplicated={dups}  malformed={bad}")
keep = ["k1", "k2", "k3"] + name_cols
ours[keep].drop_duplicates("k3").to_csv(TIDY / "keys_hromada.csv", index=False)
log("wrote", TIDY / "keys_hromada.csv")

# ------------------------------------------------------ B. occupation mask
log("=" * 70)
log("B. Occupation mask schema")
ctrl = QGIS / "hromada_control.gpkg"
if ctrl.exists():
    for cl, _ in pyogrio.list_layers(ctrl):
        cdf = pyogrio.read_dataframe(ctrl, layer=cl, read_geometry=False)
        log(f"layer '{cl}' rows={len(cdf)} columns={list(cdf.columns)}")
        for c in cdf.columns:
            if cdf[c].nunique(dropna=False) <= 8:
                log(f"  {c}: {cdf[c].value_counts(dropna=False).to_dict()}")
else:
    log("hromada_control.gpkg not found")

kat = [p for p in (VIINA / "katottg.csv", QGIS / "katottg.csv") if p.exists()]
if kat:
    kdf = pd.read_csv(kat[0], nrows=3, dtype=str)
    log(f"katottg.csv at {kat[0]} columns={list(kdf.columns)}")

# ------------------------------------------------------------ C. COD-AB ADM3
log("=" * 70)
log("C. COD-AB ADM3 attributes (ITOS FeatureServer, no geometry)")
FS = "https://codgis.itos.uga.edu/arcgis/rest/services/COD_External/UKR_pcode/FeatureServer"
st, ct, body, url = get(FS, {"f": "json"})
log(f"GET {url} -> {st} {ct} {len(body)} bytes")
cod = None
if st == 200:
    meta = json.loads(body)
    lyrs = meta.get("layers", []) + meta.get("tables", [])
    log("FeatureServer layers:", [(l["id"], l["name"]) for l in lyrs])
    adm3_id = None
    for l in lyrs:
        st2, _, b2, _ = get(f"{FS}/{l['id']}", {"f": "json"})
        if st2 != 200:
            continue
        fields = [f["name"] for f in json.loads(b2).get("fields", [])]
        has3 = any(re.fullmatch(r"(?i)adm3_?pcode", f) for f in fields)
        has4 = any(re.fullmatch(r"(?i)adm4_?pcode", f) for f in fields)
        if has3 and not has4:
            adm3_id = l["id"]
            log(f"ADM3 layer = {l['id']} '{l['name']}' fields={fields}")
            break
    if adm3_id is not None:
        rows, off = [], 0
        while True:
            p = {"where": "1=1", "outFields": "*", "returnGeometry": "false",
                 "f": "json", "resultOffset": off, "resultRecordCount": 1000}
            st3, _, b3, _ = get(f"{FS}/{adm3_id}/query", p)
            js = json.loads(b3) if st3 == 200 else {"error": st3}
            if "error" in js:
                log("query error:", js["error"])
                break
            feats = js.get("features", [])
            rows += [f["attributes"] for f in feats]
            if not feats or not js.get("exceededTransferLimit"):
                break
            off += len(feats)
            time.sleep(0.5)
        if rows:
            cod = pd.DataFrame(rows)
            cod.to_csv(RAW / "cod_ab" / "cod_adm3_attributes.csv", index=False)
            log(f"COD ADM3 rows={len(cod)} -> raw/cod_ab/cod_adm3_attributes.csv")

# HDX resource list (for geometry download later; may be bot-blocked)
st, ct, body, url = get("https://data.humdata.org/api/3/action/package_show", {"id": "cod-ab-ukr"})
log(f"HDX package_show -> {st} {ct}")
if st == 200:
    pkg = json.loads(body)["result"]
    res = [{"name": r.get("name"), "format": r.get("format"), "url": r.get("url"),
            "last_modified": r.get("last_modified")} for r in pkg.get("resources", [])]
    pd.DataFrame(res).to_csv(RAW / "cod_ab" / "hdx_cod_ab_resources.csv", index=False)
    log(f"license: {pkg.get('license_title')}  resources={len(res)}")

# --------------------------------------------------------- D. key comparison
log("=" * 70)
log("D. k3 vs COD ADM3_PCODE")
if cod is not None:
    pc3 = next(c for c in cod.columns if re.fullmatch(r"(?i)adm3_?pcode", c))
    pc2 = next((c for c in cod.columns if re.fullmatch(r"(?i)adm2_?pcode", c)), None)
    nm3 = next((c for c in cod.columns if re.fullmatch(r"(?i)adm3_?(ua|uk)", c)), None)
    cod["k3"] = cod[pc3].astype("string").str.upper().str.replace(r"^UA", "", regex=True)
    log(f"COD pcode format ok (7 digits): {cod['k3'].str.fullmatch(r'\\d{7}').sum()}/{len(cod)}")
    s_ours, s_cod = set(ours["k3"]), set(cod["k3"].dropna())
    both = s_ours & s_cod
    log(f"ours={len(s_ours)}  cod={len(s_cod)}  matched={len(both)}  "
        f"only_ours={len(s_ours - s_cod)}  only_cod={len(s_cod - s_ours)}")
    nm_ours = name_cols[0] if name_cols else None
    oo = ours[ours["k3"].isin(s_ours - s_cod)][["k3"] + name_cols].head(20)
    oc = cod[cod["k3"].isin(s_cod - s_ours)][["k3", pc3] + ([nm3] if nm3 else [])].head(20)
    if len(oo):
        log("only in ours (first 20):\n" + oo.to_string(index=False))
    if len(oc):
        log("only in COD (first 20):\n" + oc.to_string(index=False))
    if pc2:
        k2cod = cod[pc2].astype("string").str.upper().str.replace(r"^UA", "", regex=True)
        log(f"COD internal ADM2 == k3[:4]: {(k2cod == cod['k3'].str[:4]).sum()}/{len(cod)}")
    m = ours.merge(cod[["k3", pc3] + ([nm3] if nm3 else [])], on="k3", how="left")
    if nm3 and nm_ours:
        mm = m[m[pc3].notna()].copy()
        mm["same_name"] = norm_name(mm[nm_ours]) == norm_name(mm[nm3])
        log(f"name agreement on matched ({nm_ours} vs {nm3}): {mm['same_name'].sum()}/{len(mm)}")
        diff = mm[~mm["same_name"]][["k3", nm_ours, nm3]].head(15)
        if len(diff):
            log("name differences (first 15):\n" + diff.to_string(index=False))
    m["in_cod"] = m[pc3].notna()
    m[["k3", pc3, "in_cod"]].rename(columns={pc3: "adm3_pcode"}) \
        .to_csv(TIDY / "crosswalk_k3_codpcode.csv", index=False)
    log("wrote", TIDY / "crosswalk_k3_codpcode.csv")
else:
    log("COD attributes not retrieved — step D skipped")

# ------------------------------------------------------ E. openbudget probe
log("=" * 70)
log("E. openbudget.gov.ua endpoint probe")
OB = "https://openbudget.gov.ua/api/localBudgets"
base = {"year": 2025, "monthFrom": 1, "monthTo": 12, "fundType": "TOTAL"}
probes = [
    ("about_IF_oblast_11d", f"{OB}/aboutBudgets/plain/CSV", {**base, "codeBudget": "09100000000"}),
    ("about_IF_oblast_10d", f"{OB}/aboutBudgets/plain/CSV", {**base, "codeBudget": "0910000000"}),
    ("about_1951000000", f"{OB}/aboutBudgets/plain/CSV", {**base, "codeBudget": "1951000000"}),
    ("incomes_1951000000_2025", f"{OB}/incomesLocal/CSV", {**base, "codeBudget": "1951000000"}),
    ("incomes_1951000000_2021", f"{OB}/incomesLocal/CSV", {**base, "year": 2021, "codeBudget": "1951000000"}),
    ("expenses_1951000000_2025", f"{OB}/functional/CSV",
     {**base, "codeBudget": "1951000000", "treeType": "WITHOUT_DETALISATION"}),
    ("incomes_IF_oblast_10d_2025", f"{OB}/incomesLocal/CSV", {**base, "codeBudget": "0910000000"}),
]
for name, ep, params in probes:
    st, ct, body, url = get(ep, params)
    text, enc = decode(body)
    out = RAW / "openbudget_probe" / f"{name}.txt"
    out.write_bytes(body)
    lines = text.splitlines()
    log(f"\n[{name}] {st} {ct} {len(body)} bytes enc={enc} lines={len(lines)}")
    log(f"  {url}")
    for ln in lines[:6]:
        log("  | " + ln[:220])
    time.sleep(1.2)

# ---------------------------------------------------- F. data dictionary
dd = TIDY / "data_dictionary.csv"
if not dd.exists():
    pd.DataFrame(columns=["indicator", "source", "licence", "unit", "year",
                          "level", "method"]).to_csv(dd, index=False)
    log("\ncreated", dd)

log("=" * 70)
log(f"done — full log: {LOGFILE}")
_logf.close()
