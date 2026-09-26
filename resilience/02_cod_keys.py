#!/usr/bin/env python3
"""
02_cod_keys.py — COD-AB ADM3 attributes from HDX (ITOS unreachable) and
test ADM3_PCODE == "UA" + k3.
Outputs: raw/cod_ab/<download>, raw/cod_ab/cod_adm3_attributes.csv,
         tidy/crosswalk_k3_codpcode.csv, logs/02_cod_keys.log
"""
import json
import re
import sys
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd
import pyogrio

BASE = Path(__file__).resolve().parent
RAW, TIDY, LOGS = BASE / "raw" / "cod_ab", BASE / "tidy", BASE / "logs"
for d in (RAW, TIDY, LOGS):
    d.mkdir(parents=True, exist_ok=True)
_logf = open(LOGS / "02_cod_keys.log", "w", encoding="utf-8")


def log(*a):
    m = " ".join(str(x) for x in a)
    print(m)
    _logf.write(m + "\n")
    _logf.flush()


HDR = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
       "Accept": "*/*"}


def fetch(url, dest=None, timeout=300):
    req = urllib.request.Request(url, headers=HDR)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        if dest is None:
            return r.read()
        with open(dest, "wb") as f:
            while chunk := r.read(1 << 20):
                f.write(chunk)
    return dest


def norm_name(s):
    s = s.astype("string").str.lower().fillna("")
    s = s.str.replace(r"[’'ʼ`\"]", "", regex=True)
    s = s.str.replace(r"\b(територіальна|громада|міська|сільська|селищна|тг)\b", "", regex=True)
    return s.str.replace(r"[^0-9a-zа-яіїєґ]+", "", regex=True)


# ---------------------------------------------------------- resource list
zips = sorted(RAW.glob("*shp*.zip"))
if zips:
    dest = zips[0]
    log(f"using cached {dest.name}")
else:
    api = "https://data.humdata.org/api/3/action/package_show?" + urllib.parse.urlencode({"id": "cod-ab-ukr"})
    pkg = json.loads(fetch(api))["result"]
    res = pd.DataFrame([{"name": r.get("name"), "format": (r.get("format") or "").upper(),
                         "url": r.get("url"), "size": r.get("size")} for r in pkg["resources"]])
    log("HDX cod-ab-ukr resources:\n" + res[["name", "format", "size"]].to_string())
    cand = res[res["format"] == "SHP"]
    if cand.empty:
        sys.exit("no SHP resource found")
    row = cand.iloc[0]
    dest = RAW / Path(urllib.parse.urlparse(row["url"]).path).name
    log(f"downloading {row['name']} -> {dest}")
    fetch(row["url"], dest)
log(f"file {dest} {dest.stat().st_size/1e6:.1f} MB")

with zipfile.ZipFile(dest) as z:
    shps = [n for n in z.namelist() if n.lower().endswith(".shp")]
log("shapefiles in zip:", shps)
adm3 = [n for n in shps if re.search(r"adm(in)?_?3\b|adm(in)?3\.shp$", n, re.I)
        and not re.search(r"line|point|capital", n, re.I)]
if not adm3:
    sys.exit("no ADM3 polygon shapefile in zip")
cod = pyogrio.read_dataframe(f"/vsizip/{dest}/{adm3[0]}", read_geometry=False)
cod.to_csv(RAW / "cod_adm3_attributes.csv", index=False)
log(f"COD ADM3 '{adm3[0]}' rows={len(cod)} columns={list(cod.columns)}")

# ------------------------------------------------------------ comparison
ours = pd.read_csv(TIDY / "keys_hromada.csv", dtype=str)
pc3 = next((c for c in cod.columns if re.fullmatch(r"(?i)adm(in)?3_?pcode", c)), None)
if pc3 is None:
    sys.exit(f"no ADM3 pcode column among {list(cod.columns)}")
pc2 = next((c for c in cod.columns if re.fullmatch(r"(?i)adm(in)?2_?pcode", c)), None)
nm3 = next((c for c in cod.columns if re.fullmatch(r"(?i)adm(in)?3_?(ua|uk|name_ua|name_uk)", c)), None)
log(f"pcode col={pc3}  adm2 col={pc2}  name col={nm3}")
cod["k3"] = cod[pc3].astype("string").str.upper().str.replace(r"^UA", "", regex=True)
log(f"COD pcodes with 7 digits after UA: {cod['k3'].str.fullmatch(r'[0-9]{7}').sum()}/{len(cod)}")
s_o, s_c = set(ours["k3"]), set(cod["k3"].dropna())
log(f"ours={len(s_o)} cod={len(s_c)} matched={len(s_o & s_c)} "
    f"only_ours={len(s_o - s_c)} only_cod={len(s_c - s_o)}")
if s_o - s_c:
    log("only in ours:\n" + ours[ours["k3"].isin(s_o - s_c)][["k3", "name"]].head(20).to_string(index=False))
if s_c - s_o:
    cols = ["k3", pc3] + ([nm3] if nm3 else [])
    log("only in COD:\n" + cod[cod["k3"].isin(s_c - s_o)][cols].head(20).to_string(index=False))
if pc2:
    k2c = cod[pc2].astype("string").str.upper().str.replace(r"^UA", "", regex=True)
    log(f"COD ADM2 == k3[:4]: {(k2c == cod['k3'].str[:4]).sum()}/{len(cod)}")
m = ours.merge(cod[["k3", pc3] + ([nm3] if nm3 else [])], on="k3", how="left")
if nm3:
    mm = m[m[pc3].notna()].copy()
    mm["same"] = norm_name(mm["name"]) == norm_name(mm[nm3])
    log(f"name agreement on matched: {mm['same'].sum()}/{len(mm)}")
    if (~mm["same"]).any():
        log("name differences (first 15):\n" + mm[~mm["same"]][["k3", "name", nm3]].head(15).to_string(index=False))
m["in_cod"] = m[pc3].notna()
m[["k3", pc3, "in_cod"]].rename(columns={pc3: "adm3_pcode"}).to_csv(TIDY / "crosswalk_k3_codpcode.csv", index=False)
log("wrote tidy/crosswalk_k3_codpcode.csv   licence: CC BY 3.0 IGO (OCHA COD-AB, SSPE Kartographia)")
_logf.close()
