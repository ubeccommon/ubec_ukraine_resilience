#!/usr/bin/env python3
"""
34_schools.py — general secondary schools and pupils per hromada (k3). Cultural-sphere input
(resilience/docs/threefolding_framework.md, section 6, step 4b).

  python 34_schools.py probe [--rg 26]
  python 34_schools.py build [--refresh]     # -> tidy/schools_k3.csv

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

build   register (current network): schools_2026 working, suspended_2026, schools_per10k_2026
        (working / pop_ghs_2020); rural, mountain, hub and branch counts as context.
        ZNZ-1 (pre-war): pupils_2021 (row 1.12 col 1), classes_2021 (row 1.1 col 1), class_size_2021,
        pupils_per1000_2021. A school is placed by oblast + settlement name; where the name repeats
        in the oblast, only settlements with a school in the register are kept; Kyiv city directly.
        Unresolved schools (repeated names) are not assigned. For each hromada, pupils_unres_max
        sums the pupils of every unresolved school that could belong to it (upper bound of what may
        be missing); pupil counts are kept where that bound is at most MAX_MISSING (5 %) of placed +
        bound (znz_complete), otherwise left empty. Class size is a ratio over placed schools and is
        computed wherever schools are placed.

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
ZNZ_VALS = RAW / "znz1_values.pkl"    # oblast, settlement, pupils, classes (local, not tracked)
REG_MIN = RAW / "register_min.pkl"    # settlement code, k3, status, type, flags — no names (local)
OUT = TIDY / "schools_k3.csv"
PUPILS, CLASSES = "ЗНЗ1 1.12.1", "ЗНЗ1 1.1.1"
MAX_MISSING = 0.05
ZNZ_URL = ("https://data.gov.ua/dataset/7091f713-b44e-4362-a48a-3a528cb64446/resource/"
           "eb236da2-eca9-4dc2-8773-a726d50dd3b2/download/sc_info_znz1_out.xlsx")
META = ["SNAME", "SOBL", "SRJN", "SPNT", "SADDR", "SPINX", "SOWN", "SLCT", "SPHN", "SEML", "SOP"]
PRIVATE = {"SNAME", "SADDR", "SPINX", "SPHN", "SEML"}     # never printed, never stored downstream
# register fields whose category counts may be printed (no names, addresses, contacts, director)
REG_CATEGORIES = ["Статус", "Тип закладу", "Форма власності", "Регіон", "Опорний / Філія", "Сільський",
                  "Гірський", "Інтернат", "ОУО підтвердив дані"]
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
        log(f"    records={len(df)} fields={len(df.columns)} (lc filter ignored if records cover all oblasts)")
        log("    fields: " + " | ".join(df.columns))
        for c in REG_CATEGORIES:
            if c in df.columns:
                log(f"    {c}: {df[c].astype(str).value_counts(dropna=False).head(10).to_dict()}")
        kc = next((c for c in df.columns if "КАТОТТГ" in c and "Населений" not in c), None)
        if kc:
            sys.path.insert(0, str(BASE))
            ob = importlib.import_module("03_openbudget")
            k3, _ = ob.katottg_parts(df[kc].astype("string"))
            keys = pd.read_csv(TIDY / "keys_hromada.csv", dtype=str)
            ok = k3.isin(set(keys["k3"]))
            log(f"    {kc}: valid KATOTTG -> k3 in keys: {ok.mean():.2%}; hromadas with >= 1 school: {k3[ok].nunique()}")
            n = k3[ok].value_counts()
            log(f"    schools per hromada: median {n.median():.0f}, p05 {n.quantile(.05):.0f}, p95 {n.quantile(.95):.0f}")
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
    obl = cod[cod["level"] == "1"].drop_duplicates("oo").set_index("oo")["name"].map(obl_norm)
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
    sec1 = [c for c in ind if re.match(r"^ЗНЗ1\s+1\.(1|2|3|10|11|12|13|14|15)\.\d+$", c)]
    if sec1:
        log("  national column sums, section 1 (rows 1-3, 10-15; aggregates only):")
        big = pd.read_excel(ZNZ_XLSX, usecols=sec1)
        tot = big.apply(pd.to_numeric, errors="coerce").sum()
        for r in sorted({c.split(".")[1] for c in sec1}, key=int):
            vals = [f"{tot[c]:,.0f}" for c in sec1 if c.split(".")[1] == r]
            log(f"    row 1.{r}: " + " | ".join(vals))
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


# ---------------------------------------------------------------- build
def register_min(refresh=False):
    if REG_MIN.exists() and not refresh:
        return pd.read_pickle(REG_MIN)
    url = REG_VARIANTS[1].format(rg="26")
    st, body = get(url)
    if st != 200 or not body:
        raise SystemExit(f"register download failed: HTTP {st}")
    data = json.loads(body.decode("utf-8-sig"))
    del body
    recs = data if isinstance(data, list) else next((v for v in data.values() if isinstance(v, list)), [])
    df = pd.json_normalize(recs)
    del data, recs
    keep = {"Код КАТОТТГ": "settlement", "Статус": "status", "Тип закладу": "type",
            "Опорний / Філія": "hub", "Сільський": "rural", "Гірський": "mountain"}
    miss = [c for c in keep if c not in df.columns]
    if miss:
        raise SystemExit(f"register fields missing: {miss}")
    df = df[list(keep)].rename(columns=keep)        # names, addresses, contacts, director dropped here
    sys.path.insert(0, str(BASE))
    ob = importlib.import_module("03_openbudget")
    df["settlement"] = df["settlement"].astype("string").str.strip().str.upper()
    df["k3"], _ = ob.katottg_parts(df["settlement"])
    RAW.mkdir(parents=True, exist_ok=True)
    df.to_pickle(REG_MIN)
    log(f"  register: {len(df)} schools, fields kept: {list(df.columns)}")
    return df


def znz_values():
    if ZNZ_VALS.exists():
        return pd.read_pickle(ZNZ_VALS)
    if not ZNZ_XLSX.exists():
        znz_meta()
    log(f"  reading {PUPILS}, {CLASSES} from {ZNZ_XLSX.name} (slow the first time)")
    v = pd.read_excel(ZNZ_XLSX, usecols=["SOBL", "SPNT", "SLCT", PUPILS, CLASSES], dtype={"SOBL": str, "SPNT": str})
    v = v.rename(columns={PUPILS: "pupils", CLASSES: "classes"})
    for c in ("pupils", "classes"):
        v[c] = pd.to_numeric(v[c], errors="coerce")
    v.to_pickle(ZNZ_VALS)
    return v


def place(v, reg):
    s, _ = settlements()
    s = s.dropna(subset=["k3"])
    cand = s.groupby(["obl", "nn"]).apply(lambda g: list(zip(g["code"].str.upper(), g["k3"])),
                                          include_groups=False)
    with_school = set(reg["settlement"].dropna())
    v = v.copy()
    v["obl"] = v["SOBL"].map(lambda n: obl_norm(n) if pd.notna(n) else None)
    v["nn"] = v["SPNT"].map(norm)
    res, k3s, touch = [], [], []
    for r in v.itertuples():
        if r.obl == "київ":
            res.append("city"); k3s.append("8000000"); touch.append(None)
            continue
        c = cand.get((r.obl, r.nn), [])
        ks = sorted({k for _, k in c})
        if len(ks) == 1:
            res.append("unique"); k3s.append(ks[0]); touch.append(None)
            continue
        if not ks:
            res.append("none"); k3s.append(None); touch.append(None)
            continue
        ks2 = sorted({k for code, k in c if code in with_school})
        if len(ks2) == 1:
            res.append("register"); k3s.append(ks2[0]); touch.append(None)
        else:
            res.append("ambiguous"); k3s.append(None); touch.append(ks2 or ks)
    v["res"], v["k3"], v["touch"] = res, k3s, touch
    return v


def cmd_build(a):
    open_log("34_build.log")
    keys = pd.read_csv(TIDY / "keys_hromada.csv", dtype=str)[["k1", "k2", "k3", "name"]]
    pop = pd.read_csv(TIDY / "population_k3.csv", dtype={"k3": str})[["k3", "pop_ghs_2020"]]
    pop["k3"] = pop["k3"].str.zfill(7)
    pop.loc[pop["pop_ghs_2020"] < 100, "pop_ghs_2020"] = float("nan")

    reg = register_min(a.refresh)
    r = reg[reg["k3"].notna()]
    work = r["status"].eq("працює")
    agg = pd.DataFrame({
        "schools_2026": r[work].groupby("k3").size(),
        "schools_suspended_2026": r[~work].groupby("k3").size(),
        "schools_rural_2026": r[work & r["rural"].eq("Так")].groupby("k3").size(),
        "schools_mountain_2026": r[work & r["mountain"].eq("Так")].groupby("k3").size(),
        "schools_hub_2026": r[work & r["hub"].eq("Опорний заклад")].groupby("k3").size(),
        "schools_branch_2026": r[work & r["hub"].eq("Філія")].groupby("k3").size(),
    }).fillna(0).astype(int).rename_axis("k3").reset_index()
    log(f"register: {len(reg)} schools, {len(r)} placed by KATOTTG in {r['k3'].nunique()} hromadas; "
        f"working {int(work.sum())}, suspended/other {int((~work).sum())}")

    v = place(znz_values(), reg)
    log("ZNZ-1 placement: " + str(v["res"].value_counts().to_dict()))
    tot = v.groupby("SOBL")["pupils"].sum()
    placed = v[v["k3"].notna()].groupby("SOBL")["pupils"].sum()
    log("  pupils placed / oblast total: " + ", ".join(
        f"{k.split()[0]}={placed.get(k, 0) / t:.2f}" for k, t in tot.items() if t > 0))
    z = v[v["k3"].notna()].groupby("k3").agg(znz_schools_2021=("pupils", "size"),
                                             pupils_2021=("pupils", "sum"),
                                             classes_2021=("classes", "sum")).reset_index()
    amb = v[v["touch"].notna()][["touch", "pupils"]].explode("touch").rename(columns={"touch": "k3"})
    t = amb.groupby("k3").agg(znz_unresolved=("pupils", "size"), pupils_unres_max=("pupils", "sum")).reset_index()

    out = keys.merge(agg, on="k3", how="left").merge(z, on="k3", how="left").merge(t, on="k3", how="left") \
              .merge(pop, on="k3", how="left")
    out = out[out[["schools_2026", "schools_suspended_2026", "znz_schools_2021"]].notna().any(axis=1)].copy()
    out["znz_unresolved"] = out["znz_unresolved"].fillna(0).astype(int)
    out["pupils_unres_max"] = out["pupils_unres_max"].fillna(0)
    out["class_size_2021"] = (out["pupils_2021"] / out["classes_2021"].where(out["classes_2021"] > 0)).round(2)
    out["pupils_missing_max_share"] = (out["pupils_unres_max"] /
                                       (out["pupils_2021"].fillna(0) + out["pupils_unres_max"]).where(lambda x: x > 0)).round(3)
    out["znz_complete"] = out["znz_schools_2021"].notna() & (out["pupils_missing_max_share"].fillna(0) <= MAX_MISSING)
    for c in ("pupils_2021", "classes_2021"):
        out.loc[~out["znz_complete"], c] = float("nan")
    out["schools_per10k_2026"] = (out["schools_2026"] / out["pop_ghs_2020"] * 1e4).round(3)
    out["pupils_per1000_2021"] = (out["pupils_2021"] / out["pop_ghs_2020"] * 1e3).round(2)
    cols = ["k1", "k2", "k3", "name", "schools_2026", "schools_suspended_2026", "schools_per10k_2026",
            "schools_rural_2026", "schools_mountain_2026", "schools_hub_2026", "schools_branch_2026",
            "znz_schools_2021", "znz_unresolved", "pupils_missing_max_share", "znz_complete", "pupils_2021", "classes_2021", "pupils_per1000_2021",
            "class_size_2021"]
    out = out[cols].sort_values("k3")
    out.to_csv(OUT, index=False)
    log(f"wrote {OUT.name} rows={len(out)}; pupil values kept for {int(out['znz_complete'].sum())} hromadas "
        f"(missing pupils at most {MAX_MISSING:.0%}); strictly complete: {int(out['znz_unresolved'].eq(0).sum())}")
    kk = out.assign(ok=out["znz_complete"]).groupby("k1")["ok"].mean().round(2)
    log("  share of hromadas with pupil values by oblast: " + ", ".join(f"{k}={x}" for k, x in kk.items()))
    for c in ("schools_per10k_2026", "pupils_per1000_2021", "class_size_2021"):
        x = out[c].dropna()
        log(f"  {c}: n={len(x)} median={x.median():.2f} p05={x.quantile(.05):.2f} p95={x.quantile(.95):.2f}")
    vk = out[out["k3"] == "2602003"]
    if len(vk):
        log("Verkhovyna 2602003:\n" + vk.T.to_string(header=False))

    reg_src = "Ministry of Education, ЄДЕБО Реєстр суб'єктів освітньої діяльності, open data (ut=3)"
    znz_src = "Ministry of Education, form ЗНЗ-1 per school, data.gov.ua cbcab622-…, pre-war school year"
    lic_reg = "state open data (CMU Resolution 835) — attribution; licence statement to confirm"
    lic_znz = "CC BY 4.0"
    dd_new = pd.DataFrame([
        ["schools_2026", reg_src, lic_reg, "count", "2026", "hromada", "general secondary schools with status 'працює', incl. branches; KATOTTG of the school"],
        ["schools_suspended_2026", reg_src, lic_reg, "count", "2026", "hromada", "schools with status 'призупинено' (or blank)"],
        ["schools_per10k_2026", reg_src + " + GHS-POP", lic_reg, "per 10,000 persons", "2026", "hromada", "schools_2026 / pop_ghs_2020"],
        ["pupils_2021", znz_src, lic_znz, "persons", "2021", "hromada", "ЗНЗ-1 row 1.12 col 1 summed over schools placed in the hromada; empty unless znz_complete"],
        ["pupils_per1000_2021", znz_src + " + GHS-POP", lic_znz, "per 1,000 persons", "2021", "hromada", "pupils_2021 / pop_ghs_2020"],
        ["class_size_2021", znz_src, lic_znz, "pupils per class", "2021", "hromada", "pupils / classes (row 1.1 col 1) over all placed schools"],
        ["znz_complete", znz_src, lic_znz, "flag", "2021", "hromada", "true if pupils of unresolved ZNZ-1 schools (repeated settlement names) that could belong to the hromada are at most 5 % of placed + unresolved"],
        ["pupils_missing_max_share", znz_src, lic_znz, "ratio", "2021", "hromada", "upper bound of the share of pupils possibly missing (unresolved schools that could belong to the hromada)"],
    ], columns=["indicator", "source", "licence", "unit", "year", "level", "method"])
    ddp = TIDY / "data_dictionary.csv"
    dd = pd.read_csv(ddp, dtype=str) if ddp.exists() else pd.DataFrame(columns=dd_new.columns)
    dd = pd.concat([dd[~dd["indicator"].isin(dd_new["indicator"])], dd_new], ignore_index=True)
    dd.to_csv(ddp, index=False)
    log(f"data dictionary updated: {len(dd)} indicators")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("mode", choices=["probe", "build"])
    ap.add_argument("--rg", default="26")
    ap.add_argument("--refresh", action="store_true", help="build: download the register again")
    a = ap.parse_args()
    if a.mode == "probe":
        open_log("34_probe.log")
        probe_register(a.rg)
        probe_znz()
    else:
        cmd_build(a)


if __name__ == "__main__":
    main()
