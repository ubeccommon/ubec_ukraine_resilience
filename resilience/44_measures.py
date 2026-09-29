#!/usr/bin/env python3
"""
44_measures.py — round 3, step 4 (docs/pattern_language.md, 5.7 and 5.9): the nearest open measure for each candidate
pattern, one value per hromada, from the sources of section 6. Counts, shares and per-10,000 rates per hromada
only (rules R1, R6, R7): no locations, no names, no religious affiliation.

  python 44_measures.py civil                            civil protection (functional code 0320) from 31's local full table
  python 44_measures.py prozorro probe|pull|build        generators and generating sets bought 2022–2024 (Prozorro search API)
  python 44_measures.py nonprofit probe|pull|build       register of non-profit organisations (State Tax Service, data.gov.ua)
  python 44_measures.py w3 probe|pull|build              OCHA Ukraine 3W operational presence (HDX): organisations per hromada
  python 44_measures.py formation probe|pull|build       Wikidata (CC0): when the hromada was formed, voluntary or administrative
  python 44_measures.py places --file F --kind K         any list of institutions or points (invincibility points, youth
                                                         centres, veteran spaces, libraries, IDP councils, service centres,
                                                         community officers) -> counts per hromada
        options: --cols "oblast=Область,settlement=Населений пункт"   name the columns if the guess is wrong
                 --by <column>                                        also count by the values of one column
                 --delete-source                                      delete the file after the build (point files, R1)
  python 44_measures.py assemble                         tidy/measures_k3.csv from tidy/measures_*_k3.csv, + data dictionary

Every sub-command writes tidy/measures_<kind>_k3.csv (k1, k2, k3, name, m_<kind>_* columns, snapshot) and a sidecar
tidy/measures_<kind>_k3.json (source, licence, method per column) that `assemble` folds into the data dictionary.
Raw downloads go to raw/<kind>/<date>/ (gitignored). The tidy tables are public: nothing below hromada level.

Placement engine (used by every source): a row is given its hromada (k3) by the first route that applies —
  katottg   a KATOTTG code (UA + 17 digits)                          -> 03_openbudget.katottg_parts
  pcode     an OCHA COD pcode (UA + 7 digits, = "UA" + k3)
  hromada   hromada or council name + oblast                          -> 33_elections_2020.match_k3 (as 41)
  settlement settlement name + oblast [+ raion]                       -> KATOTTG codifier (34_schools.settlements):
            unique within the raion when a raion is given, else unique within the oblast; the rest is dropped
  lat/lon   coordinates                                              -> spatial join with units_hromada.gpkg; the
            coordinates are dropped from memory right after the join and never written (R1)
  address   one free-text Ukrainian address                          -> parsed into oblast, raion, settlement, then as above
The log reports rows per route and the share left unplaced. Names of organisations are read for placement and
classification only; nothing but counts leaves the script (R6).

Why these measures (section 6 and Annex A, which is opened only after the field round): a candidate pattern seen
in the held-up member of several pairs is given the nearest thing an open register counts for every hromada,
and 45_candidates.py tests it on all hromadas. Measures dated after February 2022 describe; they do not precede
(40_configurations.py, --with-present). The date of each measure is in its dictionary row.

Licences: openbudget (CMU 835, attribution); Prozorro (open API, CMU 835); State Tax Service register (CC BY 4.0);
HDX 3W (CC BY); Wikidata (CC0). Cite the accessed date printed in the sidecar.
"""
import argparse
import importlib
import json
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
TIDY, RAW = BASE / "tidy", BASE / "raw"
KEYS = TIDY / "keys_hromada.csv"
POP = TIDY / "population_k3.csv"
UNITS = BASE / "units_hromada.gpkg"
HEAD = {"User-Agent": "ubec-resilience/1.3 (stewardship@ubec.network)"}
CKAN_UA = "https://data.gov.ua/api/3/action"
CKAN_HDX = "https://data.humdata.org/api/3/action"
sys.path.insert(0, str(BASE))

# ---- source settings (set after `probe`) ---------------------------------------------------------------------
PROZORRO_SEARCH = "https://prozorro.gov.ua/api/search/tenders"
PROZORRO_QUERIES = ["генератор", "генераторна установка", "електрогенератор", "дизельна електростанція", "31120000", "31121000"]
PROZORRO_YEARS = (2022, 2023, 2024)
NONPROFIT_DATASET = "5c78eb60"          # prefix noted 28 Sep 2026; `probe` searches data.gov.ua for the full id
NONPROFIT_QUERY = "Реєстр неприбуткових установ та організацій"
# codes of the non-profit register (ознака неприбутковості, MinFin order 553/2016) — confirm on the probe against the
# register's own legend. Religious organisations (0035) and parties (0033) are never counted (R7); budget
# institutions (0031) and pension funds (0037) are not civic life outside the budget.
NONPROFIT_CODES = {"0032": "assoc", "0034": "assoc", "0036": "charity", "0038": "assoc", "0039": "housing", "0040": "housing",
                   "0041": "union", "0042": "union", "0043": "agri_coop", "0044": "agri_coop", "0045": "other"}
W3_QUERY = "ukraine 3w operational presence"
W3_DATASET = ""                          # set from the probe (HDX dataset name), else the first search hit is used
WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"
WIKIDATA_API = "https://www.wikidata.org/w/api.php"
KATOTTG_PROP = ""                        # set from the probe (property "KATOTTG ID"), e.g. "P9435"
ADMIN_WAVE = "2020-06-12"                # CMU orders of 12 June 2020: the administrative formation of the remaining hromadas

_logf = None


def log(*a):
    m = time.strftime("%H:%M:%S") + " " + " ".join(str(x) for x in a)
    print(m, flush=True)
    if _logf:
        _logf.write(m + "\n")
        _logf.flush()


def open_log(name):
    global _logf
    (BASE / "logs").mkdir(exist_ok=True)
    _logf = open(BASE / "logs" / f"{name}.log", "a", encoding="utf-8")


def keys():
    k = pd.read_csv(KEYS, dtype=str)
    k["k3"] = k["k3"].str.zfill(7)
    return k


def population():
    p = pd.read_csv(POP, dtype={"k3": str})
    p["k3"] = p["k3"].str.zfill(7)
    p["occupied"] = p["occupied"].astype(str).str.lower().isin(["true", "1"])
    return p


def raw_dir(kind, new=False):
    d = RAW / kind
    if new:
        out = d / time.strftime("%Y-%m-%d")
        out.mkdir(parents=True, exist_ok=True)
        return out
    dirs = sorted(p for p in d.glob("20*") if p.is_dir())
    if not dirs:
        sys.exit(f"no raw download in raw/{kind}: run `pull` first")
    return dirs[-1]


def get(url, **kw):
    import requests
    r = requests.get(url, headers=HEAD, timeout=kw.pop("timeout", 120), **kw)
    r.raise_for_status()
    return r


def read_any(content, name):
    m41 = importlib.import_module("41_nhsu_declarations")
    return m41.read_any(content, name)


# ---- placement engine ------------------------------------------------------------------------------------------
GUESS = {"katottg": r"katottg|катоттг", "pcode": r"pcode|p_code", "hromada": r"громад|hromada|gromada|community|council|рада",
         "oblast": r"област|oblast|region|area|регіон", "raion": r"район|raion|rayon|district",
         "settlement": r"населен|settlement|locality|city|town|village|місто|село",
         "lat": r"^lat|latitude|широт|^y$", "lon": r"^lon|^lng|longitude|довгот|^x$", "address": r"адрес|address|місцезнаходж"}
ADDR_TYPE = r"(?:м\.|смт\.?|с\.|с-ще|селище міського типу|селище|село|місто)"


def guess_cols(df, given=""):
    cols = {}
    for kv in (given or "").split(","):
        if "=" in kv:
            k, v = kv.split("=", 1)
            cols[k.strip()] = v.strip()
    for role, pat in GUESS.items():
        if role in cols:
            continue
        for c in df.columns:
            if re.search(pat, str(c), re.I) and c not in cols.values():
                cols[role] = c
                break
    return cols


def parse_address(s):
    """'Івано-Франківська обл., Верховинський р-н, смт Верховина, вул. …' -> oblast, raion, settlement, hromada."""
    s = str(s or "")
    ob = re.search(r"([А-ЯІЇЄҐ][\w'’-]+)\s*(?:обл\.?|область)", s)
    ra = re.search(r"([А-ЯІЇЄҐ][\w'’-]+)\s*(?:р-н|район)", s)
    hr = re.search(r"([А-ЯІЇЄҐ][\w'’-]+)\s+(?:територіальна\s+громада|тер\.?\s*громада|(?:сільська|селищна|міська)\s+(?:територіальна\s+)?громада)", s)
    st = re.search(ADDR_TYPE + r"\s*([А-ЯІЇЄҐ][\w'’ -]+?)(?:,|$|\s+вул|\s+пров|\s+пл\.|\s+просп|\s+буд)", s)
    kyiv = bool(re.search(r"\bм\.?\s*Київ\b|\bКиїв\b", s)) and not ob
    return {"oblast": "м. Київ" if kyiv else (ob.group(1) if ob else None), "raion": ra.group(1) if ra else None,
            "settlement": st.group(1).strip() if st else None,
            "hromada": re.sub(r"\bтер\.\s*|\bтер\s+(?=громада)", "територіальна ", hr.group(0)) if hr else None}


def place(df, cols, label=""):
    """Add k3 and route to df (rows that cannot be placed keep k3 NaN); coordinates are dropped afterwards."""
    df = df.copy()
    df["k3"], df["route"] = pd.NA, ""
    n = len(df)
    if "address" in cols and not ({"oblast", "settlement"} <= set(cols)):
        parsed = pd.DataFrame([parse_address(v) for v in df[cols["address"]]], index=df.index)
        for k in ("oblast", "raion", "settlement", "hromada"):
            if k not in cols and parsed[k].notna().any():
                df[f"_{k}"] = parsed[k]
                cols[k] = f"_{k}"
        log(f"  address parsed: oblast {parsed['oblast'].notna().mean():.0%}, raion {parsed['raion'].notna().mean():.0%}, "
            f"settlement {parsed['settlement'].notna().mean():.0%}, hromada {parsed['hromada'].notna().mean():.0%}")
    ob = importlib.import_module("03_openbudget")
    if "katottg" in cols:
        k3, _ = ob.katottg_parts(df[cols["katottg"]].astype("string"))
        m = k3.notna()
        df.loc[m, "k3"], df.loc[m, "route"] = k3[m], "katottg"
    if "pcode" in cols:
        pc = df[cols["pcode"]].astype(str).str.strip().str.upper().str.extract(r"^UA(\d{7})$")[0]
        m = df["k3"].isna() & pc.notna()
        df.loc[m, "k3"], df.loc[m, "route"] = pc[m], "pcode"
    if {"hromada", "oblast"} <= set(cols):
        e33 = importlib.import_module("33_elections_2020")
        todo = df.index[df["k3"].isna() & df[cols["hromada"]].notna()]
        if len(todo):
            u = df.loc[todo, [cols["oblast"], cols["hromada"]]].drop_duplicates()
            u.columns = ["oblast", "hromada"]
            c = pd.DataFrame(index=u.index)
            obs = u["oblast"].astype(str).str.strip()
            low = obs.str.lower()
            c["oblast"] = np.where(low.str.contains("київ") & ~low.str.contains("област"), "м. Київ",
                                   np.where(low.str.contains("крим"), "Автономна Республіка Крим",
                                            obs.str.capitalize() + np.where(low.str.contains("област"), "", " область")))
            typ = u["hromada"].map(lambda nme: e33.stem_type(nme)[1])
            c["council_type"] = typ.map({"m": "міська", "s": "селищна", "v": "сільська"}).fillna("сільська")
            c["rada_name"] = u["hromada"].astype(str)
            mm = e33.match_k3(c)
            u["k3"] = mm["k3"].reindex(u.index)
            u = u.dropna(subset=["k3"])
            lk = dict(zip(zip(u["oblast"], u["hromada"]), u["k3"]))
            got = pd.Series([lk.get((o, h)) for o, h in zip(df.loc[todo, cols["oblast"]], df.loc[todo, cols["hromada"]])], index=todo)
            m = got.notna()
            df.loc[got.index[m], "k3"], df.loc[got.index[m], "route"] = got[m], "hromada"
    if {"settlement", "oblast"} <= set(cols):
        try:
            s34 = importlib.import_module("34_schools")
            st, _ = s34.settlements()
            st = st.dropna(subset=["k3"])
            st["k2"] = st["k3"].str[:4]
            uniq_ob = st.groupby(["obl", "nn"])["k3"].agg(lambda x: x.iloc[0] if x.nunique() == 1 else None).dropna()
            todo = df.index[df["k3"].isna() & df[cols["settlement"]].notna()]
            if len(todo):
                o = df.loc[todo, cols["oblast"]].map(s34.obl_norm)
                nn = df.loc[todo, cols["settlement"]].map(s34.norm)
                got = pd.Series(list(zip(o, nn)), index=todo).map(uniq_ob)
                route = pd.Series("settlement", index=todo)
                if "raion" in cols:                                  # disambiguate repeated names within the raion
                    cod = st.drop_duplicates("k2")
                    rname = raion_names()
                    if rname is not None:
                        rn = df.loc[todo, cols["raion"]].map(lambda v: s34.norm(re.sub(r"(ський|ська|цький|цька)$", "", str(v))))
                        uniq_ra = st.assign(rn=st["k2"].map(rname)).dropna(subset=["rn"]) \
                            .groupby(["rn", "nn"])["k3"].agg(lambda x: x.iloc[0] if x.nunique() == 1 else None).dropna()
                        g2 = pd.Series(list(zip(rn, nn)), index=todo).map(uniq_ra)
                        use = got.isna() & g2.notna()
                        got[use] = g2[use]
                        route[use] = "settlement+raion"
                m = got.notna()
                df.loc[got.index[m], "k3"], df.loc[got.index[m], "route"] = got[m], route[m]
        except SystemExit as ex:
            log(f"  settlement route skipped ({ex})")
    if {"lat", "lon"} <= set(cols):
        todo = df.index[df["k3"].isna()]
        if len(todo):
            try:
                import geopandas as gpd
                g = gpd.read_file(UNITS, layer="hromada")[["k3", "geometry"]]
                g["k3"] = g["k3"].astype(str).str.zfill(7)
                la = pd.to_numeric(df.loc[todo, cols["lat"]], errors="coerce")
                lo = pd.to_numeric(df.loc[todo, cols["lon"]], errors="coerce")
                pts = gpd.GeoDataFrame({"_i": todo}, geometry=gpd.points_from_xy(lo, la), crs="EPSG:4326").to_crs(g.crs)
                j = gpd.sjoin(pts, g, how="left", predicate="within").drop_duplicates("_i").set_index("_i")["k3"]
                m = j.notna()
                df.loc[j.index[m], "k3"], df.loc[j.index[m], "route"] = j[m], "coordinates"
            except Exception as ex:
                log(f"  coordinate route skipped ({ex})")
        df = df.drop(columns=[cols["lat"], cols["lon"]])            # R1: coordinates leave memory here
    df["k3"] = df["k3"].astype("string").str.zfill(7)
    rt = df["route"].replace("", "unplaced").value_counts().to_dict()
    log(f"  placed {label}: {int(df['k3'].notna().sum())} of {n} rows ({rt})")
    return df


def raion_names():
    """k2 -> normalised raion name stem from the KATOTTG codifier (level 2)."""
    try:
        s34 = importlib.import_module("34_schools")
        p = next((c for c in s34.CODIFIER if c.exists()), None)
        if p is None:
            return None
        cod = pd.read_csv(p, dtype=str)
        cod = cod[cod["code"].str.match(r"^UA\d{17}$", na=False) & (cod["level"] == "2")]
        return pd.Series(cod["name"].map(lambda v: s34.norm(re.sub(r"(ський|ська|цький|цька)$", "", str(v)))).values,
                         index=cod["code"].str[2:6]).to_dict()
    except Exception:
        return None


def counts_to_table(df, kind, by=None, weight=None):
    """Rows with k3 -> one row per hromada: m_<kind>_n, m_<kind>_per10k [, m_<kind>_<by value>_n]."""
    pop = population()
    k = keys()
    d = df.dropna(subset=["k3"])
    out = d.groupby("k3").size().rename(f"m_{kind}_n").to_frame()
    if weight is not None and weight in d:
        out[f"m_{kind}_sum"] = d.groupby("k3")[weight].sum()
    if by and by in d:
        vals = d[by].astype(str).str.strip()
        for v in sorted(vals.unique()):
            safe = re.sub(r"[^0-9a-zA-Zа-яіїєґА-ЯІЇЄҐ]+", "_", v).strip("_").lower()[:24]
            out[f"m_{kind}_{safe}_n"] = d[vals == v].groupby("k3").size()
    out = out.reset_index()
    out = k[["k1", "k2", "k3", "name"]].merge(out, on="k3", how="left").merge(pop[["k3", "pop_ghs_2020"]], on="k3", how="left")
    ncol = [c for c in out.columns if c.endswith("_n")]
    out[ncol] = out[ncol].fillna(0).astype(int)
    out[f"m_{kind}_per10k"] = 10_000 * out[f"m_{kind}_n"] / pd.to_numeric(out["pop_ghs_2020"], errors="coerce").where(lambda v: v > 0)
    if f"m_{kind}_sum" in out:
        out[f"m_{kind}_sum_pc"] = out[f"m_{kind}_sum"] / pd.to_numeric(out["pop_ghs_2020"], errors="coerce").where(lambda v: v > 0)
    return out.drop(columns=["pop_ghs_2020"])


def write(kind, out, meta):
    out["snapshot"] = meta.get("accessed", time.strftime("%Y-%m-%d"))
    fn = TIDY / f"measures_{kind}_k3.csv"
    out.to_csv(fn, index=False)
    (TIDY / f"measures_{kind}_k3.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    mcols = [c for c in out.columns if c.startswith("m_")]
    log(f"wrote {fn.relative_to(BASE)}: {len(out)} hromadas, columns {mcols}")
    for c in mcols:
        v = pd.to_numeric(out[c], errors="coerce")
        log(f"    {c:32s} non-zero {int((v.fillna(0) != 0).sum()):5d}  median {v.median():.3f}  p90 {v.quantile(.9):.3f}")


# ---- civil protection (0320) from 31's local table ------------------------------------------------------------
def cmd_civil(a):
    fn = TIDY / "functional_spending_full_k3_year.csv"
    if not fn.exists():
        sys.exit("tidy/functional_spending_full_k3_year.csv (local) not found — run 31_functional_spending.py shares")
    f = pd.read_csv(fn, dtype={"k3": str})
    f["k3"] = f["k3"].str.zfill(7)
    col = "fk_0320"
    if col not in f:
        cands = [c for c in f.columns if c.startswith("fk_032")]
        if not cands:
            sys.exit(f"no 0320 column in {fn.name}; functional columns present: {[c for c in f.columns if c.startswith('fk_03')]}")
        f[col] = f[cands].apply(pd.to_numeric, errors="coerce").sum(axis=1)
        log(f"0320 taken as the sum of {cands}")
    f[col] = pd.to_numeric(f[col], errors="coerce").fillna(0)
    f["exp_civil"] = pd.to_numeric(f["exp_civil"], errors="coerce")
    f["share"] = f[col] / f["exp_civil"].where(f["exp_civil"] > 0)
    pop = population()
    f = f.merge(pop[["k3", "pop_ghs_2020"]], on="k3", how="left")
    f["pc"] = f[col] / pd.to_numeric(f["pop_ghs_2020"], errors="coerce").where(lambda v: v > 0)
    full = f[f["last_month"] >= 12] if "last_month" in f else f
    piv_s = full.pivot_table(index="k3", columns="year", values="share", aggfunc="first")
    piv_p = full.pivot_table(index="k3", columns="year", values="pc", aggfunc="first")
    out = pd.DataFrame(index=piv_s.index)
    out["m_civil_share_2021"] = piv_s.get(2021)
    out["m_civil_share_2223"] = piv_s[[y for y in (2022, 2023) if y in piv_s]].mean(axis=1)
    out["m_civil_share_2425"] = piv_s[[y for y in (2024, 2025) if y in piv_s]].mean(axis=1)
    out["m_civil_pc_2021"] = piv_p.get(2021)
    out["m_civil_pc_2223"] = piv_p[[y for y in (2022, 2023) if y in piv_p]].mean(axis=1)
    out["m_civil_change"] = out["m_civil_share_2223"] - out["m_civil_share_2021"]
    out["m_civil_any_2225"] = (piv_s[[y for y in (2022, 2023, 2024, 2025) if y in piv_s]].fillna(0) > 0).any(axis=1).astype(int)
    out = keys()[["k1", "k2", "k3", "name"]].merge(out.reset_index(), on="k3", how="left")
    src = "openbudget.gov.ua EXPENSES PROGRAM cache (31_functional_spending.py), functional code 0320 civil protection"
    lic = "Ukrainian open data, CMU Resolution 835 — attribution; the 0320 line alone reveals no R4 amount"
    meta = {"accessed": time.strftime("%Y-%m-%d"), "source": src, "licence": lic, "level": "hromada", "columns": {
        "m_civil_share_2021": ("share", "2021", "0320 / civilian service expenditure (31), full years only"),
        "m_civil_share_2223": ("share", "2022-2023", "mean of the annual shares"),
        "m_civil_share_2425": ("share", "2024-2025", "mean of the annual shares"),
        "m_civil_pc_2021": ("UAH per resident", "2021", "0320 / GHS-POP 2020, nominal"),
        "m_civil_pc_2223": ("UAH per resident", "2022-2023", "mean, nominal"),
        "m_civil_change": ("share points", "2021→2022-23", "m_civil_share_2223 − m_civil_share_2021: what the hromada set aside once the war came"),
        "m_civil_any_2225": ("0/1", "2022-2025", "any 0320 spending in 2022–2025")}}
    write("civil", out, meta)


# ---- Prozorro: generators -----------------------------------------------------------------------------------------
def dig(d, *paths):
    """First value found along dotted paths in a nested dict/list ('procuringEntity.address.region')."""
    for p in paths:
        cur = d
        ok = True
        for part in p.split("."):
            if isinstance(cur, list):
                cur = cur[0] if cur else None
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                ok = False
                break
        if ok and cur not in (None, "", [], {}):
            return cur
    return None


def prozorro_page(q, year, page):
    params = {"text": q, "page": page, "date[tender][start]": f"{year}-01-01", "date[tender][end]": f"{year}-12-31"}
    r = get(PROZORRO_SEARCH, params=params, timeout=90)
    return r.json()


def cmd_prozorro(a):
    if a.step == "probe":
        j = prozorro_page(PROZORRO_QUERIES[0], PROZORRO_YEARS[0], 1)
        log(f"keys: {list(j.keys()) if isinstance(j, dict) else type(j)}")
        data = j.get("data") or j.get("items") or j.get("results") or []
        log(f"total: {j.get('total') or j.get('count')}  per page: {len(data)}")
        if data:
            rec = data[0]
            safe = json.dumps({k: (v if k not in ("procuringEntity",) else {kk: vv for kk, vv in v.items() if kk != "contactPoint"})
                               for k, v in rec.items()}, ensure_ascii=False)[:3000]
            log(f"first record (contact fields hidden, R6):\n{safe}")
        log("Next: check that the fields read in build_prozorro_rows() exist (buyer name, identifier, address.region, "
            "address.locality, value.amount, tenderID, dateCreated, classification); adjust PROZORRO_QUERIES; then `pull`.")
        return
    if a.step == "pull":
        out = raw_dir("prozorro", new=True)
        for q in PROZORRO_QUERIES:
            for y in PROZORRO_YEARS:
                fn = out / (re.sub(r"\W+", "_", q) + f"_{y}.jsonl")
                if fn.exists() and fn.stat().st_size > 0:
                    continue
                n = 0
                with open(fn, "w", encoding="utf-8") as f:
                    page = 1
                    while True:
                        try:
                            j = prozorro_page(q, y, page)
                        except Exception as ex:
                            log(f"  {q} {y} page {page}: {ex}; stopping this query")
                            break
                        data = j.get("data") or j.get("items") or j.get("results") or []
                        if not data:
                            break
                        for rec in data:
                            rec.pop("contactPoint", None)
                            if isinstance(rec.get("procuringEntity"), dict):
                                rec["procuringEntity"].pop("contactPoint", None)
                            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                            n += 1
                        page += 1
                        total = j.get("total") or j.get("count") or 0
                        if page > 500 or (total and n >= total):
                            break
                        time.sleep(0.3)
                log(f"  {q} {y}: {n} tenders -> {fn.name}")
        (out / "meta.json").write_text(json.dumps({"accessed": out.name, "queries": PROZORRO_QUERIES, "years": PROZORRO_YEARS}),
                                       encoding="utf-8")
        return
    # build
    d = raw_dir("prozorro")
    rows = []
    for fn in d.glob("*.jsonl"):
        for line in open(fn, encoding="utf-8"):
            try:
                rec = json.loads(line)
            except Exception:
                continue
            rows.append(build_prozorro_row(rec))
    df = pd.DataFrame(rows).dropna(subset=["tender_id"]).drop_duplicates("tender_id")
    log(f"tenders read: {len(df)}")
    cls = df["classification"].astype(str)
    df = df[cls.str.startswith("3112") | cls.str.startswith("31100") | df["title"].astype(str).str.lower().str.contains("генератор|електростанц")]
    log(f"  generators by CPV 3112*/31100* or title: {len(df)}")
    nm = df["buyer"].astype(str).str.lower()
    df["kind"] = np.select([nm.str.contains(r"\bрада\b|ради\b|виконавч|виконком|управління.*ради|відділ.*ради"),
                            nm.str.contains(r"комунальн|\bкп\b|кнп|ліцей|школа|гімназ|лікарн|бібліотек|будинок культури|дитяч|садок|цнап")],
                           ["council", "communal"], "other")
    df["oblast"] = df["region"].astype(str).str.replace(r"\s*область", "", regex=True)
    cols = {"hromada": "buyer", "oblast": "oblast", "settlement": "locality"}
    df.loc[df["kind"] != "council", "buyer"] = None                 # only councils are placed by name
    df = place(df, cols, "tenders")
    df["year"] = pd.to_datetime(df["date"], errors="coerce").dt.year
    out = None
    for kind, lab in (("council", "council"), (None, "local")):
        sub = df if kind is None else df[df["kind"] == kind]
        sub = sub[sub["kind"] != "other"] if kind is None else sub
        t = counts_to_table(sub, f"gen_{lab}", weight="amount")
        for y in PROZORRO_YEARS:
            t[f"m_gen_{lab}_{y}_n"] = t["k3"].map(sub[sub["year"] == y].groupby("k3").size()).fillna(0).astype(int)
        out = t if out is None else out.merge(t.drop(columns=["k1", "k2", "name"]), on="k3", how="left")
    src = "Prozorro search API (prozorro.gov.ua), tenders for generators and generating sets 2022–2024"
    meta = {"accessed": d.name, "source": src, "licence": "Prozorro open data, CMU Resolution 835 — attribution",
            "level": "hromada", "columns": {
                "m_gen_council_n": ("count", "2022-2024", "tenders by the hromada council and its executive bodies"),
                "m_gen_council_per10k": ("per 10,000", "2022-2024", "per 10,000 residents 2020"),
                "m_gen_council_sum_pc": ("UAH per resident", "2022-2024", "expected value of those tenders per resident"),
                "m_gen_local_n": ("count", "2022-2024", "tenders by the council and communal entities placed in the hromada"),
                "m_gen_local_per10k": ("per 10,000", "2022-2024", "per 10,000 residents 2020")}}
    write("prozorro", out, meta)


def build_prozorro_row(rec):
    return {"tender_id": dig(rec, "tenderID", "id"), "title": dig(rec, "title"),
            "date": dig(rec, "dateCreated", "date", "tenderPeriod.startDate", "enquiryPeriod.startDate"),
            "buyer": dig(rec, "procuringEntity.name", "procuringEntity.identifier.legalName", "buyer.name"),
            "edrpou": dig(rec, "procuringEntity.identifier.id", "buyer.identifier.id"),
            "region": dig(rec, "procuringEntity.address.region", "buyer.address.region", "region"),
            "locality": dig(rec, "procuringEntity.address.locality", "buyer.address.locality"),
            "classification": dig(rec, "classification.id", "items.classification.id", "cpv"),
            "amount": pd.to_numeric(dig(rec, "value.amount", "amount"), errors="coerce")}


# ---- register of non-profits ------------------------------------------------------------------------------------
def ckan(base, action, **params):
    j = get(f"{base}/{action}", params=params, timeout=90).json()
    if not j.get("success"):
        sys.exit(f"CKAN error: {j}")
    return j["result"]


def cmd_nonprofit(a):
    if a.step == "probe":
        res = ckan(CKAN_UA, "package_search", q=NONPROFIT_QUERY, rows=10)
        for pk in res.get("results", []):
            log(f"dataset {pk['id']}  {pk.get('title')}  licence={pk.get('license_title')}  modified={pk.get('metadata_modified')}")
            for r in pk.get("resources", [])[:6]:
                log(f"    resource {r.get('name')}  format={r.get('format')}  size={r.get('size')}  url={r.get('url')}")
        hit = next((pk for pk in res.get("results", []) if pk["id"].startswith(NONPROFIT_DATASET)), None)
        if hit and hit.get("resources"):
            r = hit["resources"][0]
            try:
                chunk = next(get(r["url"], stream=True, timeout=120).iter_content(chunk_size=1_500_000))
                m41 = importlib.import_module("41_nhsu_declarations")
                df = m41.read_any(chunk, r["url"].split("?")[0], partial=True)
                safe = [c for c in df.columns if not re.search(r"name|pib|фіо|прізвище|назва", str(c), re.I)]
                log(f"  columns: {list(df.columns)}\n  first rows (name columns hidden):\n{df[safe].head(3).to_string()}")
                code = guess_cols(df).get("katottg") or next((c for c in df.columns if re.search(r"ознак|код", str(c), re.I)), None)
                if code:
                    log(f"  value counts of {code}: {df[code].value_counts().head(15).to_dict()}")
            except Exception as ex:
                log(f"  (sample not read: {ex})")
        log("Next: set NONPROFIT_DATASET to the full id, confirm NONPROFIT_CODES against the legend, check which column "
            "carries an address or KATOTTG (else the register places by tax office only, which is not hromada level); then `pull`.")
        return
    if a.step == "pull":
        res = ckan(CKAN_UA, "package_search", q=NONPROFIT_QUERY, rows=10)
        hit = next((pk for pk in res.get("results", []) if pk["id"].startswith(NONPROFIT_DATASET)), None)
        if not hit:
            sys.exit("dataset not found: run `probe` and set NONPROFIT_DATASET")
        out = raw_dir("nonprofit", new=True)
        for r in hit.get("resources", []):
            if (r.get("format") or "").lower() not in ("csv", "xlsx", "zip", "xls"):
                continue
            fn = out / (re.sub(r"[^\w.-]+", "_", r.get("name") or "register") + "." + r["format"].lower())
            with get(r["url"], stream=True, timeout=900) as resp:
                with open(fn, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=8_000_000):
                        f.write(chunk)
            log(f"  {fn.name} {fn.stat().st_size / 1e6:.1f} MB")
        (out / "meta.json").write_text(json.dumps({"accessed": out.name, "dataset": hit["id"], "licence": hit.get("license_title")}),
                                       encoding="utf-8")
        return
    d = raw_dir("nonprofit")
    frames = [read_any(p.read_bytes(), p.name) for p in d.iterdir() if p.suffix.lower() in (".csv", ".xlsx", ".xls", ".zip")]
    df = pd.concat(frames, ignore_index=True)
    cols = guess_cols(df, a.cols)
    code_col = next((c for c in df.columns if re.search(r"ознак|непр", str(c), re.I)), None)
    if code_col is None:
        sys.exit(f"no non-profit code column found in {list(df.columns)}")
    df["code"] = df[code_col].astype(str).str.extract(r"(\d{4})")[0]
    df["cls"] = df["code"].map(NONPROFIT_CODES)
    log(f"register rows {len(df)}; by class {df['cls'].value_counts(dropna=False).to_dict()}")
    df = df[df["cls"].notna()]                                          # R7: 0035 religious and 0033 parties never counted
    if not any(k in cols for k in ("katottg", "address", "settlement")):
        sys.exit("the register carries no address or KATOTTG column: hromada placement is not possible (tax office = raion at best)")
    df = place(df, cols, "non-profits")
    out = counts_to_table(df, "npo", by="cls")
    meta = {"accessed": d.name, "source": "Register of non-profit institutions and organisations, State Tax Service, data.gov.ua",
            "licence": "CC BY 4.0; counts per hromada by class only (R6, R7: religious organisations and parties excluded)",
            "level": "hromada", "columns": {
                "m_npo_n": ("count", d.name, "civic organisations registered as non-profit (assoc., charities, housing and agricultural co-ops, unions, other)"),
                "m_npo_per10k": ("per 10,000", d.name, "per 10,000 residents 2020"),
                "m_npo_assoc_n": ("count", d.name, "public associations, creative unions, associations of legal persons (0032, 0034, 0038)"),
                "m_npo_charity_n": ("count", d.name, "charitable organisations (0036)"),
                "m_npo_housing_n": ("count", d.name, "OSBB and housing co-operatives (0039, 0040)"),
                "m_npo_agri_coop_n": ("count", d.name, "agricultural service co-operatives (0043, 0044)")}}
    write("nonprofit", out, meta)


# ---- OCHA 3W ----------------------------------------------------------------------------------------------------------
def cmd_w3(a):
    if a.step == "probe":
        res = ckan(CKAN_HDX, "package_search", q=W3_QUERY, rows=8)
        for pk in res.get("results", []):
            log(f"dataset {pk['name']}  {pk.get('title')}  licence={pk.get('license_title')}  modified={pk.get('metadata_modified')}")
            for r in pk.get("resources", [])[:8]:
                log(f"    resource {r.get('name')}  format={r.get('format')}  modified={r.get('last_modified')}  url={r.get('url')}")
        log("Next: set W3_DATASET to the dataset name whose resource carries admin3 pcodes (UA + 7 digits); then `pull`.")
        return
    if a.step == "pull":
        res = ckan(CKAN_HDX, "package_search", q=W3_QUERY, rows=8)
        hit = next((pk for pk in res.get("results", []) if pk["name"] == W3_DATASET), None) or (res.get("results") or [None])[0]
        if not hit:
            sys.exit("no 3W dataset found on HDX")
        out = raw_dir("w3", new=True)
        for r in hit.get("resources", []):
            if (r.get("format") or "").lower() not in ("csv", "xlsx", "xls"):
                continue
            fn = out / (re.sub(r"[^\w.-]+", "_", r.get("name") or "3w") + "." + r["format"].lower())
            with get(r["url"], stream=True, timeout=600) as resp:
                with open(fn, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=8_000_000):
                        f.write(chunk)
            log(f"  {fn.name} {fn.stat().st_size / 1e6:.1f} MB")
        (out / "meta.json").write_text(json.dumps({"accessed": out.name, "dataset": hit["name"], "licence": hit.get("license_title")}),
                                       encoding="utf-8")
        return
    d = raw_dir("w3")
    frames = []
    for p in d.iterdir():
        if p.suffix.lower() in (".csv", ".xlsx", ".xls"):
            df = read_any(p.read_bytes(), p.name)
            if df.iloc[0].astype(str).str.startswith("#").any():          # HXL tag row
                df = df.iloc[1:]
            frames.append(df)
    df = pd.concat(frames, ignore_index=True)
    cols = guess_cols(df, a.cols)
    p3 = next((c for c in df.columns if re.search(r"adm3|admin3", str(c), re.I) and re.search(r"pcode|code", str(c), re.I)), None)
    if p3 is None:
        sys.exit(f"no admin3 pcode column: {list(df.columns)}")
    cols["pcode"] = p3
    org = next((c for c in df.columns if re.search(r"org.*(name|acronym)|organisation|organization", str(c), re.I)), None)
    typ = next((c for c in df.columns if re.search(r"org.*type|type.*org", str(c), re.I)), None)
    df = place(df, cols, "3W rows")
    df = df.dropna(subset=["k3"])
    if org:
        df = df.drop_duplicates(["k3", org])
    df["otype"] = df[typ].astype(str).str.lower().map(lambda v: "local" if re.search(r"local|national ngo|nngo|cso", v) else "other") if typ else "other"
    out = counts_to_table(df, "w3", by="otype")
    meta = {"accessed": d.name, "source": "OCHA Ukraine 3W operational presence (HDX)", "licence": "CC BY (HDX); counts per hromada only",
            "level": "hromada (admin3 pcode)", "columns": {
                "m_w3_n": ("count", "series to mid-2024", "distinct organisations reporting activity in the hromada"),
                "m_w3_per10k": ("per 10,000", "series to mid-2024", "per 10,000 residents 2020"),
                "m_w3_local_n": ("count", "series to mid-2024", "of which local or national NGOs / CSOs (by the source's organisation type)")}}
    write("w3", out, meta)


# ---- Wikidata: formation -------------------------------------------------------------------------------------------------
def sparql(q):
    r = get(WIKIDATA_SPARQL, params={"query": q, "format": "json"}, timeout=300)
    return r.json()["results"]["bindings"]


def cmd_formation(a):
    if a.step == "probe":
        j = get(WIKIDATA_API, params={"action": "wbsearchentities", "search": "KATOTTG", "language": "en", "type": "property", "format": "json"}).json()
        for s in j.get("search", []):
            log(f"property {s['id']}  {s.get('label')}  — {s.get('description')}")
        log("Next: set KATOTTG_PROP to the property 'KATOTTG ID' (or the codifier code property), then `pull`.")
        return
    if a.step == "pull":
        if not KATOTTG_PROP:
            sys.exit("set KATOTTG_PROP from the probe first")
        q = f"""SELECT ?item ?code ?inception ?dissolved WHERE {{
  ?item wdt:{KATOTTG_PROP} ?code .
  FILTER(STRLEN(?code) = 19 && SUBSTR(?code, 10, 3) = "000" && SUBSTR(?code, 13, 2) = "00" && SUBSTR(?code, 7, 3) != "000")
  OPTIONAL {{ ?item wdt:P571 ?inception . }}
  OPTIONAL {{ ?item wdt:P576 ?dissolved . }}
}}"""
        rows = sparql(q)
        out = raw_dir("formation", new=True)
        recs = [{"item": r["item"]["value"].rsplit("/", 1)[-1], "katottg": r["code"]["value"],
                 "inception": r.get("inception", {}).get("value"), "dissolved": r.get("dissolved", {}).get("value")} for r in rows]
        pd.DataFrame(recs).to_csv(out / "hromadas.csv", index=False)
        (out / "meta.json").write_text(json.dumps({"accessed": out.name, "property": KATOTTG_PROP, "licence": "CC0"}), encoding="utf-8")
        log(f"  {len(recs)} hromada-level items with a KATOTTG code; inception given for {sum(1 for r in recs if r['inception'])}")
        return
    d = raw_dir("formation")
    df = pd.read_csv(d / "hromadas.csv", dtype=str)
    df = place(df, {"katottg": "katottg"}, "Wikidata items")
    df = df.dropna(subset=["k3"]).drop_duplicates("k3")
    inc = pd.to_datetime(df["inception"].str.slice(0, 10), errors="coerce")
    df["m_formed_year"] = inc.dt.year
    wave = pd.Timestamp(ADMIN_WAVE)
    df["m_formed_voluntary"] = (inc < wave - pd.Timedelta(days=30)).astype(float).where(inc.notna())
    df["m_formed_years_before_2020"] = ((wave - inc).dt.days / 365.25).clip(lower=0).where(inc.notna())
    out = keys()[["k1", "k2", "k3", "name"]].merge(df[["k3", "m_formed_year", "m_formed_voluntary", "m_formed_years_before_2020"]], on="k3", how="left")
    log(f"  inception known for {int(out['m_formed_year'].notna().sum())} of {len(out)} hromadas; "
        f"voluntary (before {ADMIN_WAVE}) {int((out['m_formed_voluntary'] == 1).sum())}")
    meta = {"accessed": d.name, "source": "Wikidata, items with a KATOTTG code at hromada level, inception (P571)", "licence": "CC0",
            "level": "hromada", "columns": {
                "m_formed_year": ("year", d.name, "year the hromada was formed (P571); coverage in the log"),
                "m_formed_voluntary": ("0/1", d.name, f"formed before the administrative wave of {ADMIN_WAVE} (voluntary amalgamation 2015–2019)"),
                "m_formed_years_before_2020": ("years", d.name, "years between formation and the 2020 wave (0 for the wave itself)")}}
    write("formation", out, meta)


# ---- any list of places ---------------------------------------------------------------------------------------------------
def cmd_places(a):
    p = Path(a.file)
    if not p.exists():
        sys.exit(f"{p} not found")
    if p.suffix.lower() in (".json", ".geojson"):
        j = json.loads(p.read_text(encoding="utf-8"))
        feats = j.get("features") if isinstance(j, dict) else None
        if feats:
            df = pd.json_normalize([{**f.get("properties", {}), "lon": (f.get("geometry") or {}).get("coordinates", [None, None])[0],
                                     "lat": (f.get("geometry") or {}).get("coordinates", [None, None])[1]} for f in feats])
        else:
            df = pd.json_normalize(j if isinstance(j, list) else next((v for v in j.values() if isinstance(v, list)), []))
    else:
        df = read_any(p.read_bytes(), p.name)
    cols = guess_cols(df, a.cols)
    log(f"{a.kind}: {len(df)} rows; columns used {cols}")
    if not cols:
        sys.exit(f"no usable columns: {list(df.columns)} — name them with --cols")
    df = place(df, cols, a.kind)
    out = counts_to_table(df, a.kind, by=a.by)
    meta = {"accessed": time.strftime("%Y-%m-%d"), "source": a.source or p.name, "licence": a.licence or "see source", "level": "hromada",
            "columns": {f"m_{a.kind}_n": ("count", a.year or time.strftime("%Y"), f"{a.kind}: rows of the list placed in the hromada"),
                        f"m_{a.kind}_per10k": ("per 10,000", a.year or time.strftime("%Y"), "per 10,000 residents 2020")}}
    write(a.kind, out, meta)
    if a.delete_source:
        p.unlink()
        log(f"deleted {p} (R1: point files are not kept)")


# ---- assemble ----------------------------------------------------------------------------------------------------------------
def cmd_assemble(a):
    k = keys()[["k1", "k2", "k3", "name"]]
    pop = population()
    k["occupied"] = k["k3"].map(pop.set_index("k3")["occupied"]).fillna(False)
    out = k.copy()
    dd_rows = []
    for fn in sorted(TIDY.glob("measures_*_k3.csv")):
        if fn.name == "measures_k3.csv":
            continue
        t = pd.read_csv(fn, dtype={"k1": str, "k2": str, "k3": str})
        t["k3"] = t["k3"].str.zfill(7)
        mcols = [c for c in t.columns if c.startswith("m_")]
        out = out.merge(t[["k3"] + mcols], on="k3", how="left")
        side = fn.with_suffix(".json")
        meta = json.loads(side.read_text(encoding="utf-8")) if side.exists() else {}
        for c in mcols:
            unit, year, method = meta.get("columns", {}).get(c, ("", "", ""))
            dd_rows.append({"indicator": c, "source": meta.get("source", fn.name), "licence": meta.get("licence", ""),
                            "unit": unit, "year": year, "level": meta.get("level", "hromada"), "method": method})
        log(f"  {fn.name}: {len(mcols)} columns, accessed {meta.get('accessed', '?')}")
    out.loc[out["occupied"], [c for c in out.columns if c.startswith("m_")]] = np.nan     # occupied hromadas carry no measure
    fn = TIDY / "measures_k3.csv"
    out.drop(columns=["occupied"]).to_csv(fn, index=False)
    log(f"wrote {fn.relative_to(BASE)}: {len(out)} hromadas, {sum(c.startswith('m_') for c in out.columns)} measures")
    ddp = TIDY / "data_dictionary.csv"
    if ddp.exists() and dd_rows:
        dd = pd.read_csv(ddp, dtype=str)
        new = pd.DataFrame(dd_rows)
        for c in dd.columns:
            if c not in new:
                new[c] = ""
        dd = pd.concat([dd[~dd["indicator"].isin(set(new["indicator"]))], new[dd.columns]], ignore_index=True)
        dd.to_csv(ddp, index=False)
        log(f"data dictionary: {len(new)} m_* rows written")


def main():
    ap = argparse.ArgumentParser(description="round 3, step 4: the nearest open measure per hromada")
    ap.add_argument("kind", choices=("civil", "prozorro", "nonprofit", "w3", "formation", "places", "assemble"))
    ap.add_argument("step", nargs="?", default="build", choices=("probe", "pull", "build"))
    ap.add_argument("--file", help="places: the list to count (csv, xlsx, json, geojson)")
    ap.add_argument("--kind", dest="kind_label", default="", help="places: short label, e.g. invincibility, youth, veteran, library, idp_council, cnap, officer")
    ap.add_argument("--cols", default="", help="role=column pairs: katottg, pcode, hromada, oblast, raion, settlement, lat, lon, address")
    ap.add_argument("--by", default=None, help="places: also count by this column's values")
    ap.add_argument("--source", default="", help="places: source label for the dictionary")
    ap.add_argument("--licence", default="", help="places: licence for the dictionary")
    ap.add_argument("--year", default="", help="places: reference date for the dictionary")
    ap.add_argument("--delete-source", action="store_true", help="places: delete the input file after the build (R1)")
    a = ap.parse_args()
    open_log("44_measures")
    log(f"44_measures.py {a.kind} {a.step}")
    if a.kind == "civil":
        cmd_civil(a)
    elif a.kind == "prozorro":
        cmd_prozorro(a)
    elif a.kind == "nonprofit":
        cmd_nonprofit(a)
    elif a.kind == "w3":
        cmd_w3(a)
    elif a.kind == "formation":
        cmd_formation(a)
    elif a.kind == "places":
        if not a.file or not a.kind_label:
            sys.exit("places needs --file and --kind")
        a.kind = re.sub(r"\W+", "_", a.kind_label).lower()
        cmd_places(a)
    else:
        cmd_assemble(a)


if __name__ == "__main__":
    main()
