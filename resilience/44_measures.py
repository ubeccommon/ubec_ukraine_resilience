#!/usr/bin/env python3
"""
44_measures.py — round 3, step 4 (docs/pattern_language.md, 5.7 and 5.9): the nearest open measure for each candidate
pattern, one value per hromada, from the sources of section 6. Counts, shares and per-10,000 rates per hromada
only (rules R1, R6, R7): no locations, no names, no religious affiliation.

  python 44_measures.py civil                            civil protection (functional code 0320) from 31's local full table
  python 44_measures.py prozorro probe|pull|build        generators and generating sets bought 2022–2024 (Prozorro search API)
  python 44_measures.py nonprofit probe|pull|build       register of non-profit organisations (State Tax Service, data.gov.ua);
                                                         it carries no address: `edr build` first (EDRPOU -> hromada, below)
  python 44_measures.py edr probe|build                  ЄДР legal-entity dump (07_edr.py's UO.zip): EDRPOU -> hromada from the
                                                         registered address, for the register's entities; raw/edr/edrpou_k3.csv (local)
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
PROZORRO_QUERIES = ["генератор", "електрогенератор", "електростанція", "генераторна установка"]
PROZORRO_EXCLUDE = r"кисн|кисен|озон|азот|парогенер|пари|льод|льоду|димов|піно|імпульс|сигнал|ультразвук|водн|функці|числ|аерозол"
                                         # oxygen, steam, ozone, nitrogen, ice, smoke, foam, signal … generators are not power
PROZORRO_YEARS = (2022, 2023, 2024)
NONPROFIT_DATASET = "f41f0e6d-135a-4ad9-b961-5da30bfc7a19"   # probe of 29 Sep 2026: newest resource reestr_nuo_2022-02-23.zip (pre-war)
NONPROFIT_QUERY = "Реєстр неприбуткових установ та організацій"
# codes of the non-profit register (ознака неприбутковості, MinFin order 553/2016) — confirm on the probe against the
# register's own legend. Religious organisations (0035) and parties (0033) are never counted (R7); budget
# institutions (0031) and pension funds (0037) are not civic life outside the budget.
# classes read from the register's own label column (nonpr), not from the code: the code legend differs between
# releases (2022: 0043 = ОСББ). Religious organisations, parties, budget institutions and pension funds never count (R7).
NONPROFIT_CLASSES = (("religious", r"реліг"), ("party", r"політичн"), ("budget", r"бюджетн"), ("pension", r"пенсійн"),
                     ("assoc", r"громадськ|творч|асоціац|спілк|об'єднанн[яь] юридичн"), ("charity", r"благодійн"),
                     ("housing", r"співвласник|житлов|гаражн|садів|дачн"), ("agri_coop", r"сільськогосподарськ"),
                     ("coop", r"кооперат"), ("union", r"профспілк|професійн|роботодавц"), ("other", r"."))
NONPROFIT_EXCLUDED = {"religious", "party", "budget", "pension"}
EDR_XW = BASE / "raw" / "edr" / "edrpou_k3.csv"     # local: EDRPOU -> k3 from the ЄДР legal-entity dump (`edr build`)
W3_QUERY = "ukraine 3w operational presence"
W3_DATASET = "ukraine-who-does-what-where-3w"   # probe of 29 Sep 2026: 5W cumulative files, January–August 2026 the newest
WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"
WIKIDATA_API = "https://www.wikidata.org/w/api.php"
KATOTTG_PROP = "P9435"                   # probe of 29 Sep 2026: "KATOTTH ID" on hromada items (value UA + 17 digits)
HROMADA_CLASSES = ["Q104841013"]         # probe of 29 Sep 2026: P31 "hromada" (route without the property)
PROBE_ITEM = "Верховинська селищна громада"   # a hromada the probe looks up to find those
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
    if name.lower().endswith(".zip"):                           # every table inside the archive, not only the first
        import io
        import zipfile
        frames = []
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            for inner in zf.namelist():
                if inner.lower().endswith((".csv", ".xlsx", ".xls", ".txt")):
                    try:
                        frames.append(m41.read_any(zf.read(inner), inner if not inner.lower().endswith(".txt") else inner[:-4] + ".csv"))
                        log(f"    {name}: {inner} ({len(frames[-1])} rows, {frames[-1].shape[1]} columns)")
                    except ValueError as ex:
                        log(f"    {name}: {inner} not read ({ex})")
        if not frames:
            raise ValueError(f"no table inside {name}")
        return pd.concat(frames, ignore_index=True)
    try:
        return m41.read_any(content, name)
    except ValueError:
        if name.lower().endswith(".csv"):                       # a one-column list
            import io
            return pd.read_csv(io.BytesIO(content), dtype=str, encoding="utf-8-sig")
        raise


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
    # by the values, when the header says nothing: a code, a pcode, a council name, an address
    by_value = (("katottg", r"^UA\d{17}$"), ("pcode", r"^UA\d{7}$"),
                ("hromada", r"(?:сільськ|селищн|міськ|територіальн).*(?:громад|рад)"),
                ("address", r"(?:обл|область).*(?:вул|просп|пров|пл\.|буд)"))
    for role, pat in by_value:
        if role in cols:
            continue
        for c in df.columns:
            if c in cols.values():
                continue
            v = df[c].dropna().astype(str).str.strip()
            if len(v) and v.str.contains(pat, regex=True, case=False).mean() > 0.5:
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
    if "hromada" in cols:
        e33 = importlib.import_module("33_elections_2020")
        if "oblast" not in cols:
            df["_oblast"] = None
            cols["oblast"] = "_oblast"
        has_ob = df[cols["oblast"]].notna() & (df[cols["oblast"]].astype(str).str.strip() != "")
        todo = df.index[df["k3"].isna() & df[cols["hromada"]].notna() & has_ob]
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
        todo = df.index[df["k3"].isna() & df[cols["hromada"]].notna() & ~has_ob]
        if len(todo):                                            # no oblast given: the stem + type must be unique in the country
            k = keys()
            st_ = k["name"].map(e33.stem_type)
            k["key"] = st_.str[0] + "|" + st_.str[1]
            kk = k.drop_duplicates("key", keep=False).set_index("key")["k3"]
            q = df.loc[todo, cols["hromada"]].map(lambda nme: "|".join(e33.stem_type(nme)))
            got = q.map(kk)
            m = got.notna()
            df.loc[got.index[m], "k3"], df.loc[got.index[m], "route"] = got[m], "hromada_national"
            allk = set(k["key"])
            amb = int(sum(1 for v in q[~m] if v in allk))
            log(f"  hromada names without an oblast: {len(todo)}, unique in the country {int(m.sum())}, ambiguous (dropped) {amb}")
    if "settlement" in cols:
        try:
            s34 = importlib.import_module("34_schools")
            st, _ = s34.settlements()
            st = st.dropna(subset=["k3"])
            st["k2"] = st["k3"].str[:4]
            uniq_ob = st.groupby(["obl", "nn"])["k3"].agg(lambda x: x.iloc[0] if x.nunique() == 1 else None).dropna()
            if "oblast" not in cols:
                df["_oblast"] = None
                cols["oblast"] = "_oblast"
            todo = df.index[df["k3"].isna() & df[cols["settlement"]].notna()]
            if len(todo):
                o = df.loc[todo, cols["oblast"]].map(lambda v: s34.obl_norm(v) if pd.notna(v) and str(v).strip() else "")
                uniq_nat = st.groupby("nn")["k3"].agg(lambda x: x.iloc[0] if x.nunique() == 1 else None).dropna()
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
                no_ob = (o == "") & got.isna()
                if no_ob.any():                                  # no oblast: the settlement name must be unique in the country
                    g3 = nn[no_ob].map(uniq_nat)
                    got[g3.index[g3.notna()]] = g3[g3.notna()]
                    route[g3.index[g3.notna()]] = "settlement_national"
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
    f["year"] = pd.to_numeric(f["year"], errors="coerce").astype("Int64")
    if "last_month" in f:
        f["last_month"] = pd.to_numeric(f["last_month"], errors="coerce")
        diag = f.groupby("year").agg(rows=("k3", "size"), full_year=("last_month", lambda v: int((v >= 12).sum())),
                                     last_month_median=("last_month", "median"), with_0320=(col, lambda v: int((v > 0).sum())))
        log("cache by year (rows, full years, median last month, hromadas with 0320 > 0):\n" + diag.to_string())
        # one row per hromada and year: the latest reporting month (as 31 does for 2026); partial years are logged, not dropped
        f = f.sort_values(["k3", "year", "last_month"]).drop_duplicates(["k3", "year"], keep="last")
        part = f[f["last_month"] < 12].groupby("year").size()
        if len(part):
            log(f"note: partial years kept (latest month used): { {int(k): int(v) for k, v in part.items()} }")
    piv_s = f.pivot_table(index="k3", columns="year", values="share", aggfunc="first")
    piv_p = f.pivot_table(index="k3", columns="year", values="pc", aggfunc="first")
    out = pd.DataFrame(index=piv_s.index)
    out["m_civil_share_2021"] = piv_s.get(2021)
    out["m_civil_share_2223"] = piv_s[[y for y in (2022, 2023) if y in piv_s]].mean(axis=1)
    out["m_civil_share_2425"] = piv_s[[y for y in (2024, 2025) if y in piv_s]].mean(axis=1)
    out["m_civil_pc_2021"] = piv_p.get(2021)
    out["m_civil_pc_2223"] = piv_p[[y for y in (2022, 2023) if y in piv_p]].mean(axis=1)
    out["m_civil_share_2025"] = piv_s.get(2025)
    out["m_civil_pc_2025"] = piv_p.get(2025)
    out["m_civil_change"] = out["m_civil_share_2223"] - out["m_civil_share_2021"]
    out["m_civil_change_2125"] = out["m_civil_share_2025"] - out["m_civil_share_2021"]
    if out["m_civil_share_2223"].notna().sum() < 100:
        log("note: 2022–2023 are all but absent from 31's cache — run `31_functional_spending.py pull --years 2022-2024` "
            "then `shares`, and rerun this; until then use m_civil_share_2025 and m_civil_change_2125")
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
        "m_civil_share_2025": ("share", "2025", "0320 / civilian service expenditure (31)"),
        "m_civil_pc_2025": ("UAH per resident", "2025", "0320 / GHS-POP 2020, nominal"),
        "m_civil_change": ("share points", "2021→2022-23", "m_civil_share_2223 − m_civil_share_2021: what the hromada set aside once the war came"),
        "m_civil_change_2125": ("share points", "2021→2025", "m_civil_share_2025 − m_civil_share_2021"),
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


PROZORRO_METHOD = "POST"                 # the site's search endpoint answers 405 to GET (probe of 29 Sep 2026); POST with the
                                         # filters in the query string is what the prozorro.gov.ua front end sends


def prozorro_page(q, year, page):
    import requests
    params = {"text": q, "page": page, "date[tender][start]": f"{year}-01-01", "date[tender][end]": f"{year}-12-31"}
    tried = []
    for method in ([PROZORRO_METHOD] + [m for m in ("POST", "GET") if m != PROZORRO_METHOD]):
        r = requests.request(method, PROZORRO_SEARCH, params=params, headers={**HEAD, "Accept": "application/json"}, timeout=90)
        if r.status_code == 200:
            try:
                return r.json()
            except ValueError:
                tried.append(f"{method}: 200 but not JSON (starts {r.text[:60]!r})")
                continue
        tried.append(f"{method}: {r.status_code}")
        if r.status_code in (403, 429, 503):                 # rate limit or block: do not fall through to the other method
            break
    raise RuntimeError("Prozorro search not answered (" + "; ".join(tried) + ")")


def prozorro_page_retry(q, year, page, tries=6):
    """Back off on a refusal: 30, 60, 120, 240, 480 s; then give up on this page."""
    for i in range(tries):
        try:
            return prozorro_page(q, year, page)
        except Exception as ex:
            if i == tries - 1:
                raise
            wait = 30 * 2 ** i
            log(f"    {q} {year} page {page}: {ex}; waiting {wait} s")
            time.sleep(wait)


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
            keys_top = sorted({k for r in data for k in r})
            keys_pe = sorted({k for r in data for k in (r.get("procuringEntity") or {}) if k != "contactPoint"})
            keys_ad = sorted({k for r in data for k in ((r.get("procuringEntity") or {}).get("address") or {})})
            log(f"keys over the page — record: {keys_top}\n  procuringEntity: {keys_pe}\n  address: {keys_ad}")
            n_reg = sum(1 for r in data if dig(r, "procuringEntity.address.region"))
            n_cls = sum(1 for r in data if dig(r, "classification.id", "items.classification.id"))
            log(f"  with address.region {n_reg}/{len(data)}, with a CPV classification {n_cls}/{len(data)}")
            rows = pd.DataFrame([build_prozorro_row(r) for r in data])
            log("  as build reads them (buyer, locality, region, amount, date):\n" + rows[["buyer", "locality", "region", "amount", "date"]].head(8).to_string(index=False))
        log("Next: check that the fields read in build_prozorro_rows() exist (buyer name, identifier, address.region, "
            "address.locality, value.amount, tenderID, dateCreated, classification); adjust PROZORRO_QUERIES; then `pull`.")
        return
    if a.step == "pull":
        out = raw_dir("prozorro", new=True)
        for q in PROZORRO_QUERIES:
            for y in PROZORRO_YEARS:
                fn = out / (re.sub(r"\W+", "_", q) + f"_{y}.jsonl")
                done = fn.with_suffix(".done")
                if done.exists():
                    continue
                n = sum(1 for _ in open(fn, encoding="utf-8")) if fn.exists() else 0
                page = n // 20 + 1                               # resume where the last run stopped (20 per page)
                stopped = False
                with open(fn, "a", encoding="utf-8") as f:
                    while True:
                        try:
                            j = prozorro_page_retry(q, y, page)
                        except Exception as ex:
                            log(f"  {q} {y} page {page}: {ex}; stopping this query — rerun `pull` later to resume")
                            stopped = True
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
                        time.sleep(a.pause)
                if not stopped:
                    done.write_text(time.strftime("%Y-%m-%d %H:%M"))
                log(f"  {q} {y}: {n} tenders in {fn.name}" + (" (incomplete)" if stopped else ""))
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
    title = df["title"].astype(str).str.lower()
    keep = (cls.str.startswith("3112") | cls.str.startswith("31100") | title.str.contains("генератор|електростанц")) \
        & ~title.str.contains(PROZORRO_EXCLUDE)
    log(f"  generators by CPV 3112*/31100* or title, after exclusions ({PROZORRO_EXCLUDE[:40]}…): {int(keep.sum())} of {len(df)}")
    df = df[keep]
    nm = df["buyer"].astype(str).str.lower()
    df["kind"] = np.select([nm.str.contains(r"комунальн|\bкп\b|кнп|ліцей|школа|гімназ|лікарн|бібліотек|будинок культури|дитяч|садок|цнап|водоканал|тепло"),
                            nm.str.contains(r"\bрада\b|ради\b|виконавч|виконком|управління.*ради|відділ.*ради")],
                           ["communal", "council"], "other")       # communal entities first: 'КП … міської ради' is not the council
    df["oblast"] = df["region"].map(lambda v: re.sub(r"\s*область", "", str(v)) if pd.notna(v) and str(v).strip() else None)
    df["council"] = df["buyer"].map(council_name)                   # the council named in the buyer, nominative
    df.loc[df["council"].notna() & (df["kind"] == "other"), "kind"] = "council"
    sp = df["locality"].map(split_locality)
    df["settlement"], df["raion"] = [t[0] for t in sp], [t[1] for t in sp]
    log(f"  buyers: {df['kind'].value_counts().to_dict()}; council named in {int(df['council'].notna().sum())}; "
        f"locality gives a settlement for {int(df['settlement'].notna().sum())}, a raion for {int(df['raion'].notna().sum())}")
    cols = {"hromada": "council", "oblast": "oblast", "settlement": "settlement", "raion": "raion"}   # no region -> nationwide routes
    df = place(df, cols, "tenders")
    df["year"] = pd.to_datetime(df["date"].astype(str).str.slice(0, 10), errors="coerce").dt.year
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


def council_name(buyer):
    """'ВІДДІЛ ОСВІТИ … ВИКОНАВЧОГО КОМІТЕТУ МІЖГІРСЬКОЇ СЕЛИЩНОЇ РАДИ' -> 'Міжгірська селищна рада';
    'Верховинська селищна рада' -> itself; None when no council is named."""
    b = str(buyer or "")
    m = re.search(r"([А-ЯІЇЄҐа-яіїєґ'’\-]+(?:ої|ая|а))\s+(сільськ|селищн|міськ)(?:ої|а|ая)\s+(?:територіальн(?:ої|а)\s+)?(?:громад[иа]|рад[иа])", b, re.I)
    if not m:
        return None
    adj, typ = m.group(1), m.group(2).lower()
    adj = re.sub(r"ої$", "а", adj, flags=re.I)
    adj = adj[:1].upper() + adj[1:].lower()
    return f"{adj} {typ}а рада"


def split_locality(loc):
    """'смт Козин, Обухівський район' -> ('Козин', 'Обухівський'); 'Міжгірський р-н' -> (None, 'Міжгірський')."""
    loc = str(loc or "")
    parts = [p.strip() for p in loc.split(",") if p.strip()]
    settlement = raion = None
    for p in parts:
        if re.search(r"\b(р-н|район)\b", p):
            m = re.search(r"([А-ЯІЇЄҐ][\w'’\-]+)\s*(?:р-н|район)", p)
            raion = m.group(1) if m else raion
        elif settlement is None and not re.search(r"обл|область", p):
            settlement = re.sub(r"^" + ADDR_TYPE + r"\s*", "", p).strip() or None
    return settlement, raion


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


def newest_resource(pk, formats):
    rs = [r for r in pk.get("resources", []) if (r.get("format") or "").lower() in formats]
    if not rs:
        sys.exit(f"no resource in {formats} for {pk.get('name') or pk.get('id')}")
    return max(rs, key=lambda r: (r.get("last_modified") or r.get("created") or ""))


def cmd_nonprofit(a):
    if a.step == "probe":
        res = ckan(CKAN_UA, "package_search", q=NONPROFIT_QUERY, rows=10)
        for pk in res.get("results", []):
            log(f"dataset {pk['id']}  {pk.get('title')}  licence={pk.get('license_title')}  modified={pk.get('metadata_modified')}")
            for r in pk.get("resources", [])[:6]:
                log(f"    resource {r.get('name')}  format={r.get('format')}  size={r.get('size')}  url={r.get('url')}")
        hit = next((pk for pk in res.get("results", []) if pk["id"].startswith(NONPROFIT_DATASET)), None)
        if hit and hit.get("resources"):
            r = newest_resource(hit, ("zip", "csv", "xlsx", "xls"))
            log(f"newest resource: {r.get('name')}  {r.get('last_modified')} — downloading it whole (this is the pull)")
            try:
                out = raw_dir("nonprofit", new=True)
                fn = out / (re.sub(r"[^\w.-]+", "_", r.get("name") or "register") + "." + r["format"].lower())
                if not fn.exists():
                    with get(r["url"], stream=True, timeout=900) as resp:
                        with open(fn, "wb") as f:
                            for chunk in resp.iter_content(chunk_size=8_000_000):
                                f.write(chunk)
                (out / "meta.json").write_text(json.dumps({"accessed": out.name, "dataset": hit["id"], "licence": hit.get("license_title")}),
                                               encoding="utf-8")
                df = read_any(fn.read_bytes(), fn.name)
                safe = [c for c in df.columns if not re.search(r"name|pib|фіо|прізвище|назва", str(c), re.I)]
                log(f"  columns: {list(df.columns)}\n  first rows (name columns hidden):\n{df[safe].head(3).to_string()}")
                lab_col = "nonpr" if "nonpr" in df else next((c for c in df.columns if re.search(r"ознак|код", str(c), re.I)), None)
                if lab_col:
                    log("  legend (label: rows):\n" + df[lab_col].value_counts().head(25).to_string())
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
        for r in [newest_resource(hit, ("zip", "csv", "xlsx", "xls"))]:
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
    lab_col = "nonpr" if "nonpr" in df else next((c for c in df.columns if re.search(r"ознак|непр", str(c), re.I)), None)
    if lab_col is None:
        sys.exit(f"no non-profit label column found in {list(df.columns)}")
    lab = df[lab_col].astype(str).str.lower().str.replace("i", "і")     # the register mixes Latin i into Cyrillic words
    df["cls"] = "other"
    for name, pat in reversed(NONPROFIT_CLASSES):                        # first pattern wins
        df.loc[lab.str.contains(pat, regex=True), "cls"] = name
    if "d_anul" in df:
        ann = df["d_anul"].notna() & (df["d_anul"].astype(str).str.strip() != "")
        log(f"annulled entries excluded: {int(ann.sum())}")
        df = df[~ann]
    log(f"register rows {len(df)}; by class {df['cls'].value_counts().to_dict()}")
    df = df[~df["cls"].isin(NONPROFIT_EXCLUDED)]
    tin = "tin" if "tin" in df else next((c for c in df.columns if re.search(r"tin|єдрпоу|edrpou|код", str(c), re.I)), None)
    if not any(k in cols for k in ("katottg", "address", "settlement")):
        if tin and EDR_XW.exists():
            xw = pd.read_csv(EDR_XW, dtype=str)
            xw["k3"] = xw["k3"].str.zfill(7)
            df["_edrpou"] = df[tin].astype(str).str.replace(r"\D", "", regex=True).str.zfill(8)
            df["k3"] = df["_edrpou"].map(xw.set_index("edrpou")["k3"])
            df["route"] = np.where(df["k3"].notna(), "edrpou", "")
            log(f"  placed non-profits through the ЄДР crosswalk: {int(df['k3'].notna().sum())} of {len(df)}")
        else:
            sys.exit("parked (29 Sep 2026): the register carries no address, only the tax office (c_sti), and the ЄДР legal-entity "
                     "dump has no address either, so non-profits cannot be counted per hromada from open registers; the regional "
                     "statistics offices' counts by legal form (09_stat_edrpou.py, 10 oblasts) are the nearest substitute")
    else:
        df = place(df, cols, "non-profits")
    if "d_nonpr" in df:
        yr = pd.to_datetime(df["d_nonpr"], errors="coerce").dt.year
        df["since"] = np.where(yr >= 2018, "1821", "pre18")
    out = counts_to_table(df, "npo", by="cls")
    if "since" in df:
        out["m_npo_new_1821_n"] = out["k3"].map(df[df["since"] == "1821"].groupby("k3").size()).fillna(0).astype(int)
    meta = {"accessed": d.name, "source": "Register of non-profit institutions and organisations, State Tax Service, data.gov.ua",
            "licence": "CC BY 4.0; counts per hromada by class only (R6, R7: religious organisations and parties excluded)",
            "level": "hromada", "columns": {
                "m_npo_n": ("count", d.name, "civic organisations registered as non-profit (assoc., charities, housing and agricultural co-ops, unions, other)"),
                "m_npo_per10k": ("per 10,000", d.name, "per 10,000 residents 2020"),
                "m_npo_assoc_n": ("count", d.name, "public associations, creative unions, associations of legal persons"),
                "m_npo_charity_n": ("count", d.name, "charitable organisations"),
                "m_npo_housing_n": ("count", d.name, "OSBB, housing, garage, garden and dacha co-operatives"),
                "m_npo_agri_coop_n": ("count", d.name, "agricultural service co-operatives"),
                "m_npo_coop_n": ("count", d.name, "other co-operatives"),
                "m_npo_union_n": ("count", d.name, "trade unions and employers' organisations"),
                "m_npo_new_1821_n": ("count", d.name, "of the above, given non-profit status 2018–2021 (recent civic formation)")}}
    write("nonprofit", out, meta)


# ---- OCHA 3W ----------------------------------------------------------------------------------------------------------
def cmd_w3(a):
    if a.step == "probe":
        if W3_DATASET:
            pk = ckan(CKAN_HDX, "package_show", id=W3_DATASET)
            log(f"dataset {pk['name']}  {pk.get('title')}  licence={pk.get('license_title')}  modified={pk.get('metadata_modified')}  "
                f"resources {len(pk.get('resources', []))}")
            for r in pk.get("resources", []):
                log(f"    resource {r.get('name')}  format={r.get('format')}  modified={r.get('last_modified')}")
            log("Next: `pull --resource <substring of a name>` for a file likely to carry hromada pcodes (the 2022–2024 3W files), "
                "then `build`; the build takes the sheet whose pcode values are UA + 7 digits.")
        else:
            res = ckan(CKAN_HDX, "package_search", q=W3_QUERY, rows=8)
            for pk in res.get("results", []):
                log(f"dataset {pk['name']}  {pk.get('title')}  licence={pk.get('license_title')}  modified={pk.get('metadata_modified')}")
                for r in pk.get("resources", [])[:8]:
                    log(f"    resource {r.get('name')}  format={r.get('format')}  modified={r.get('last_modified')}  url={r.get('url')}")
            log("Next: set W3_DATASET, then `probe` again to list all its resources.")
        return
    if a.step == "pull":
        res = ckan(CKAN_HDX, "package_search", q=W3_QUERY, rows=8)
        hit = next((pk for pk in res.get("results", []) if pk["name"] == W3_DATASET), None) or (res.get("results") or [None])[0]
        if not hit:
            sys.exit("no 3W dataset found on HDX")
        out = raw_dir("w3", new=True)
        rs = [r for r in hit.get("resources", []) if (r.get("format") or "").lower() in ("csv", "xlsx", "xls")]
        if a.resource:
            rs = [r for r in rs if a.resource.lower() in (r.get("name") or "").lower()]
            if not rs:
                sys.exit(f"no resource matching '{a.resource}'")
        else:
            rs = [newest_resource(hit, ("csv", "xlsx", "xls"))]
        for r in rs:
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
    def hromada_pcode_col(sh):
        """The column whose values are hromada pcodes (UA + 7 digits) in most rows, else None."""
        for c in sh.columns:
            v = sh[c].dropna().astype(str).str.strip()
            if len(v) >= 20 and v.str.fullmatch(r"UA\d{7}").mean() > 0.5:
                return c
        return None

    frames, p3 = [], None
    for p in sorted(d.iterdir()):
        if p.suffix.lower() in (".xlsx", ".xls"):
            sheets = pd.read_excel(p, sheet_name=None, dtype=str)
            for nm, sh in sheets.items():
                if sh.iloc[:1].astype(str).apply(lambda r: r.str.startswith("#").any(), axis=1).any():
                    sh = sh.iloc[1:]                                  # HXL tag row
                c = hromada_pcode_col(sh)
                if c:
                    log(f"  {p.name}: sheet '{nm}' carries hromada pcodes in '{c}' ({len(sh)} rows)")
                    sh = sh.rename(columns={c: "_pcode"})
                    frames.append(sh)
                    break
            else:
                log(f"  {p.name}: no sheet with hromada-level pcodes (UA + 7 digits); sheets: "
                    + "; ".join(f"{nm}: {list(sh.columns)[:6]}" for nm, sh in sheets.items()))
        elif p.suffix.lower() == ".csv":
            sh = read_any(p.read_bytes(), p.name)
            if sh.iloc[:1].astype(str).apply(lambda r: r.str.startswith("#").any(), axis=1).any():
                sh = sh.iloc[1:]
            c = hromada_pcode_col(sh)
            if c:
                log(f"  {p.name}: hromada pcodes in '{c}' ({len(sh)} rows)")
                frames.append(sh.rename(columns={c: "_pcode"}))
            else:
                log(f"  {p.name}: no hromada-level pcode column; columns {list(sh.columns)[:10]}")
    if not frames:
        sys.exit("parked (29 Sep 2026): every 3W/5W file on HDX, the 2022 weekly rounds included, is by oblast (ADMIN1); "
                 "operational presence per hromada is not in the public files")
    df = pd.concat(frames, ignore_index=True)
    cols = guess_cols(df, a.cols)
    cols["pcode"] = "_pcode"
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


def wd_labels(ids):
    """Labels (en, else uk) for a list of P/Q ids."""
    out = {}
    ids = [i for i in ids if i]
    for i in range(0, len(ids), 50):
        j = get(WIKIDATA_API, params={"action": "wbgetentities", "ids": "|".join(ids[i:i + 50]), "props": "labels",
                                      "languages": "en|uk", "format": "json"}).json()
        for k, e in j.get("entities", {}).items():
            lb = e.get("labels", {})
            out[k] = (lb.get("en") or lb.get("uk") or {}).get("value", "")
    return out


def cmd_formation(a):
    if a.step == "probe":
        # find one hromada item and read its claims: the property whose value is a UA… code, its classes (P31), its inception
        j = get(WIKIDATA_API, params={"action": "wbsearchentities", "search": PROBE_ITEM, "language": "uk", "type": "item",
                                      "limit": 5, "format": "json"}).json()
        hits = j.get("search", [])
        if not hits:
            sys.exit(f"no Wikidata item found for '{PROBE_ITEM}'")
        for h in hits:
            log(f"item {h['id']}  {h.get('label')}  — {h.get('description')}")
        qid = hits[0]["id"]
        e = get(WIKIDATA_API, params={"action": "wbgetentities", "ids": qid, "props": "claims", "format": "json"}).json()["entities"][qid]
        claims = e.get("claims", {})
        lab = wd_labels(list(claims))
        code_props, classes = [], []
        for pid, cl in claims.items():
            vals = []
            for c in cl:
                dv = (c.get("mainsnak") or {}).get("datavalue", {}).get("value")
                if isinstance(dv, dict):
                    dv = dv.get("id") or dv.get("time") or dv.get("text") or str(dv)
                vals.append(str(dv))
            if any(re.fullmatch(r"UA\d{17}", v) for v in vals):
                code_props.append(pid)
            if pid == "P31":
                classes = vals
            log(f"  {pid:8s} {lab.get(pid, ''):40s} {'; '.join(vals)[:100]}")
        cl_lab = wd_labels(classes)
        log(f"\ncode property (value UA + 17 digits): {code_props or 'none on this item'}")
        log(f"P31 classes: " + ", ".join(f"{c} ({cl_lab.get(c, '')})" for c in classes))
        log(f"P571 inception: {'present' if 'P571' in claims else 'absent on this item'}")
        log("Next: set KATOTTG_PROP to the code property (preferred), or HROMADA_CLASSES to the P31 class ids; then `pull`.")
        return
    if a.step == "pull":
        if not KATOTTG_PROP and not HROMADA_CLASSES:
            sys.exit("set KATOTTG_PROP or HROMADA_CLASSES from the probe first")
        if KATOTTG_PROP:
            q = f"""SELECT ?item ?code ?inception ?dissolved WHERE {{
  ?item wdt:{KATOTTG_PROP} ?code .
  FILTER(STRLEN(?code) = 19 && SUBSTR(?code, 10, 3) = "000" && SUBSTR(?code, 13, 2) = "00" && SUBSTR(?code, 7, 3) != "000")
  OPTIONAL {{ ?item wdt:P571 ?inception . }}
  OPTIONAL {{ ?item wdt:P576 ?dissolved . }}
}}"""
        else:
            vals = " ".join(f"wd:{c}" for c in HROMADA_CLASSES)
            q = f"""SELECT ?item ?itemLabel ?code ?inception ?dissolved ?obl ?oblLabel WHERE {{
  VALUES ?cls {{ {vals} }}
  ?item wdt:P31 ?cls .
  OPTIONAL {{ ?item wdt:P571 ?inception . }}
  OPTIONAL {{ ?item wdt:P576 ?dissolved . }}
  OPTIONAL {{ ?item wdt:P131 ?r . ?r wdt:P131* ?obl . ?obl wdt:P31 wd:Q3348196 . }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "uk". }}
}}"""
        rows = sparql(q)
        out = raw_dir("formation", new=True)
        recs = [{"item": r["item"]["value"].rsplit("/", 1)[-1], "katottg": r.get("code", {}).get("value"),
                 "name": r.get("itemLabel", {}).get("value"), "oblast": r.get("oblLabel", {}).get("value"),
                 "inception": r.get("inception", {}).get("value"), "dissolved": r.get("dissolved", {}).get("value")} for r in rows]
        df = pd.DataFrame(recs).drop_duplicates("item")
        df.to_csv(out / "hromadas.csv", index=False)
        (out / "meta.json").write_text(json.dumps({"accessed": out.name, "property": KATOTTG_PROP, "classes": HROMADA_CLASSES,
                                                   "licence": "CC0"}), encoding="utf-8")
        log(f"  {len(df)} items; with a code {int(df['katottg'].notna().sum())}; inception given for {int(df['inception'].notna().sum())}")
        return
    d = raw_dir("formation")
    df = pd.read_csv(d / "hromadas.csv", dtype=str)
    df = df[df["dissolved"].isna()] if "dissolved" in df else df
    cols = {}
    if "katottg" in df and df["katottg"].notna().any():
        cols["katottg"] = "katottg"
    if "name" in df and df["name"].notna().any():
        cols["hromada"] = "name"
        if "oblast" in df and df["oblast"].notna().any():
            cols["oblast"] = "oblast"
    df = place(df, cols, "Wikidata items")
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


# ---- ЄДР legal-entity dump: EDRPOU -> hromada ------------------------------------------------------------------------------------
def edr_records(zpath, limit=None):
    """Yield (edrpou, address, extra) from the UO.zip of the Ministry of Justice (07_edr.py downloads it): the XML is
    streamed, a record is the parent of the EDRPOU tag, and only address-like tags are read (names never, R6)."""
    import zipfile
    from lxml import etree

    def members(z, prefix=""):
        for nm in z.namelist():
            low = nm.lower()
            if low.endswith(".xml"):
                yield prefix + nm, z.open(nm)
            elif low.endswith(".zip"):
                import io
                with zipfile.ZipFile(io.BytesIO(z.read(nm))) as inner:
                    yield from members(inner, prefix + nm + "/")

    n = 0
    with zipfile.ZipFile(zpath) as z:
        for nm, fh in members(z):
            if re.search(r"fop", nm, re.I):
                continue                                         # personal data: never read
            rec_el, edrpou, addr, extra = None, None, None, {}
            for ev, el in etree.iterparse(fh, events=("end",), recover=True, huge_tree=True):
                tag = etree.QName(el).localname.upper() if isinstance(el.tag, str) else ""
                if rec_el is None and "EDRPOU" in tag and el.text and el.text.strip():
                    rec_el, edrpou = el.getparent(), el.text.strip()
                    continue
                if rec_el is not None and el is rec_el:
                    for ch in rec_el.iter():
                        t = etree.QName(ch).localname.upper() if isinstance(ch.tag, str) else ""
                        if ch.text and ch.text.strip():
                            if "ADDRESS" in t or t == "ADDR":
                                addr = ch.text.strip()
                            elif "KATOT" in t or "KOATUU" in t or "ATU" in t:
                                extra[t] = ch.text.strip()
                    yield edrpou, addr, extra
                    n += 1
                    rec_el, edrpou, addr, extra = None, None, None, {}
                    el.clear()
                    while el.getprevious() is not None:
                        del el.getparent()[0]
                    if limit and n >= limit:
                        return


def cmd_edr(a):
    zs = sorted((BASE / "raw" / "edr").glob("*.zip")) if (BASE / "raw" / "edr").exists() else []
    zs = [z for z in zs if re.search(r"uo", z.name, re.I) and not re.search(r"schema|fop", z.name, re.I)]
    if not zs:
        sys.exit("no UO.zip in raw/edr — run `07_edr.py probe` first (it downloads the legal-entity resource only)")
    zpath = zs[-1]
    if a.step == "probe":
        seen, ex = {}, {}
        for edrpou, addr, extra in edr_records(zpath, limit=3000):
            seen["records"] = seen.get("records", 0) + 1
            if addr:
                seen["with_address"] = seen.get("with_address", 0) + 1
                ex.setdefault("address", addr)
            for k, v in extra.items():
                seen[k] = seen.get(k, 0) + 1
                ex.setdefault(k, v)
        log(f"{zpath.name}: first records {seen}")
        for k, v in ex.items():
            log(f"  example {k}: {v[:120]}")
        if ex.get("address"):
            log(f"  parsed: {parse_address(ex['address'])}")
            log("Next: `edr build` (streams the whole dump; EDRPOU -> hromada for the non-profit register's entities, local).")
        else:
            log("the dump carries no address tag (probe of 29 Sep 2026: the UO schema has no ADDRESS element, only names, "
                "codes, states and dates) — the ЄДР route to a hromada is closed; the non-profit register stays at tax-office level")
        return
    if a.step == "build":
        log("note: the UO dump has no address (29 Sep 2026); the build is kept for a future release that carries one")
    tins = None
    if a.tins or not a.all:
        src = Path(a.tins) if a.tins else None
        if src is None:
            d = raw_dir("nonprofit")
            src = next((p for p in d.iterdir() if p.suffix.lower() in (".zip", ".csv")), None)
        if src is None:
            sys.exit("no non-profit register found: pass --tins <file> or --all")
        reg = read_any(src.read_bytes(), src.name)
        tin = "tin" if "tin" in reg else next((c for c in reg.columns if re.search(r"tin|єдрпоу|edrpou", str(c), re.I)), None)
        tins = set(reg[tin].astype(str).str.replace(r"\D", "", regex=True).str.zfill(8))
        log(f"restricting to {len(tins)} EDRPOU codes of {src.name}")
    rows, n, t0 = [], 0, time.time()
    for edrpou, addr, extra in edr_records(zpath):
        n += 1
        code = re.sub(r"\D", "", edrpou).zfill(8)
        if tins is not None and code not in tins:
            continue
        rows.append({"edrpou": code, "address": addr, **{k.lower(): v for k, v in extra.items()}})
        if n % 200_000 == 0:
            log(f"  {n:,} records read, {len(rows):,} kept ({time.time() - t0:.0f} s)")
    df = pd.DataFrame(rows).drop_duplicates("edrpou")
    log(f"{n:,} records in {zpath.name}; kept {len(df):,}; with an address {int(df['address'].notna().sum()) if 'address' in df else 0}")
    cols = {}
    kat = next((c for c in df.columns if "katot" in c), None)
    if kat:
        cols["katottg"] = kat
    if "address" in df:
        cols["address"] = "address"
    if not cols:
        sys.exit("the dump carries neither an address nor a KATOTTG tag for these records")
    df = place(df, cols, "legal entities")
    EDR_XW.parent.mkdir(parents=True, exist_ok=True)
    df.loc[df["k3"].notna(), ["edrpou", "k3", "route"]].to_csv(EDR_XW, index=False)
    log(f"wrote {EDR_XW.relative_to(BASE)} (local): {int(df['k3'].notna().sum()):,} entities placed; now `nonprofit build`")


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
    ap.add_argument("kind", choices=("civil", "prozorro", "nonprofit", "edr", "w3", "formation", "places", "assemble"))
    ap.add_argument("step", nargs="?", default="build", choices=("probe", "pull", "build"))
    ap.add_argument("--file", help="places: the list to count (csv, xlsx, json, geojson)")
    ap.add_argument("--kind", dest="kind_label", default="", help="places: short label, e.g. invincibility, youth, veteran, library, idp_council, cnap, officer")
    ap.add_argument("--cols", default="", help="role=column pairs: katottg, pcode, hromada, oblast, raion, settlement, lat, lon, address")
    ap.add_argument("--by", default=None, help="places: also count by this column's values")
    ap.add_argument("--source", default="", help="places: source label for the dictionary")
    ap.add_argument("--licence", default="", help="places: licence for the dictionary")
    ap.add_argument("--year", default="", help="places: reference date for the dictionary")
    ap.add_argument("--delete-source", action="store_true", help="places: delete the input file after the build (R1)")
    ap.add_argument("--resource", default="", help="w3 pull: substring of the resource name to download (default: the newest)")
    ap.add_argument("--pause", type=float, default=1.0, help="prozorro pull: seconds between pages (default 1.0)")
    ap.add_argument("--tins", default="", help="edr build: register file whose EDRPOU codes to place (default: the latest non-profit pull)")
    ap.add_argument("--all", action="store_true", help="edr build: place every legal entity (slow, large)")
    a = ap.parse_args()
    open_log("44_measures")
    log(f"44_measures.py {a.kind} {a.step}")
    if a.kind == "civil":
        cmd_civil(a)
    elif a.kind == "prozorro":
        cmd_prozorro(a)
    elif a.kind == "nonprofit":
        cmd_nonprofit(a)
    elif a.kind == "edr":
        cmd_edr(a)
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
