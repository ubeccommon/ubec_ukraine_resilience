#!/usr/bin/env python3
"""
41_nhsu_declarations.py — present population per hromada from declarations with a primary-care doctor (NHSU).

  python 41_nhsu_declarations.py probe            list the dataset's resources on data.gov.ua and the columns of each
  python 41_nhsu_declarations.py pull             download the resources named in RESOURCES to raw/nhsu/<date>/
  python 41_nhsu_declarations.py build            aggregate to hromada -> tidy/nhsu_declarations_k3.csv
  python 41_nhsu_declarations.py build --raw-dir raw/nhsu/2026-09-28
  python 41_nhsu_declarations.py build --koatuu-xw raw/nhsu/koatuu_katottg.xlsx   # if the file carries KOATUU codes

Source: "Інформація щодо статистики поданих декларацій про вибір лікаря первинної медичної допомоги", National Health
Service of Ukraine, data.gov.ua dataset a8228262-5576-4a14-beb8-789573573546 (CC BY 4.0, weekly). The dataset
describes declarations by region, community (hromada), settlement, facility, doctor, age group and sex. Probe of
28 Sep 2026: the file used is active_declarations_by_age_gender.csv (158 MB; columns legal_entity_id, area,
gromada_koatuu, gromada_name, settlement_koatuu, settlement, settlement_type, person_gender, person_age in single
years, count_declarations). The hromada carries a KOATUU code, not KATOTTG: it is placed by name within its oblast
through the matcher of 33_elections_2020.py (synthetic test on 400 real hromada names: 399 placed, all correctly;
first real build: 1,351 of 1,387), then renamed hromadas and names repeated within an oblast by a declarations-
weighted vote of the settlements named in their rows (KATOTTG codifier, as 34_schools.py);
--koatuu-xw offers the code route if a KOATUU-KATOTTG table is at hand. The other two files (by doctor; doctor info)
carry doctors' identifiers or names and are never downloaded (R6).
Caveat to check on the first build: the rows carry the provider (legal_entity_id), so the geography may be the
provider's division rather than the patient's settlement. Hromadas with very few declarations per resident are
then served from a neighbouring hromada; the log prints their share.

Why: the paper's per-resident measures use GHS-POP 2020 (limitation 16.6). Active declarations are the closest open
measure of the people actually present now, with an age structure, for every hromada. Declarations lag moves (IDPs
often keep their declaration), so the CHANGE since 2021/2022 is the signal, and the level is read with that caveat.
The pattern-language round (docs/pattern_language.md, 5.5) needs it as a candidate condition: population inflow.

Rules: R6 — the doctor-level and facility-level files may carry names of doctors; nothing below hromada level is
written to tidy/, the raw download stays in raw/ (gitignored), and only counts per hromada and age band leave this
script. R1 — no facility locations. Output per hromada: declarations total, by age band (0-17, 18-64, 65+ where the
source allows), by sex, per 1,000 GHS-POP 2020 residents, and the date of the snapshot. Rerun monthly to build a
series; each run appends a dated row set to tidy/nhsu_declarations_long.csv.

Outputs stay LOCAL (.gitignore): they give present population per hromada including the 30 km zone (rule R3).
Publication only through the data package, with zone hromadas as raion values.

Licence: CC BY 4.0 — cite "National Health Service of Ukraine, data.gov.ua, accessed <date>".
"""
import argparse
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
TIDY, RAW = BASE / "tidy", BASE / "raw" / "nhsu"
DATASET = "a8228262-5576-4a14-beb8-789573573546"
CKAN = "https://data.gov.ua/api/3/action/package_show"
OUT = TIDY / "nhsu_declarations_k3.csv"
OUT_LONG = TIDY / "nhsu_declarations_long.csv"
KEYS = TIDY / "keys_hromada.csv"
POP = TIDY / "population_k3.csv"

# ---- to set after `probe` -------------------------------------------------------------------------------
# resource names (or substrings) to download: the file with declarations by community/settlement/age/sex
RESOURCES = ["active_declarations_by_age_gender"]
# column map for the build: source column -> role. Roles: katottg (KATOTTG code of the hromada or settlement),
# koatuu (KOATUU code of the hromada, with --koatuu-xw), hromada (hromada name), oblast (oblast name),
# settlement (settlement name), age (age band label),
# sex, count (number of active declarations), date (snapshot date, if a column; else the file date is used)
COLS = {                                   # set from the probe of 28 Sep 2026 (attribute file of the dataset)
    "gromada_koatuu": "koatuu",            # КОАТУУ of the hromada (code of its centre)
    "gromada_name": "hromada",
    "area": "oblast",                      # oblast name in capitals, without "область"
    "person_gender": "sex",                # чоловіча / жіноча
    "person_age": "age",                   # single years of age
    "count_declarations": "count",
}
AGE_BANDS = {"0-17": ("0-5", "6-11", "12-17", "0-17", "до 18"), "18-64": ("18-39", "40-64", "18-64"),
             "65+": ("65+", "65 і старше", "65 та старше")}
HEAD = {"User-Agent": "ubec-resilience/1.3 (stewardship@ubec.network)"}


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def package():
    r = requests.get(CKAN, params={"id": DATASET}, headers=HEAD, timeout=60)
    r.raise_for_status()
    j = r.json()
    if not j.get("success"):
        sys.exit(f"CKAN error: {j}")
    return j["result"]


def read_any(content, name, partial=False):
    """CSV/XLSX/ZIP bytes -> DataFrame (first sheet / first csv in a zip); tries utf-8, cp1251, windows separators."""
    name = name.lower()
    if name.endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            inner = [n for n in zf.namelist() if n.lower().endswith((".csv", ".xlsx"))]
            if not inner:
                raise ValueError("zip without csv/xlsx")
            return read_any(zf.read(inner[0]), inner[0])
    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(io.BytesIO(content), dtype=str)
    for enc in ("utf-8-sig", "utf-8", "cp1251"):
        try:
            text = content.decode(enc, errors="ignore" if partial else "strict")   # a chunk may cut a character
        except UnicodeDecodeError:
            continue
        if partial:
            text = text[:text.rfind("\n")]           # a streamed chunk ends mid-line: drop the partial line
        for sep in (",", ";", "\t", "|"):
            try:
                df = pd.read_csv(io.StringIO(text), dtype=str, sep=sep, on_bad_lines="skip")
                if df.shape[1] > 1:
                    return df
            except Exception:
                continue
    raise ValueError(f"could not parse {name} (first bytes: {content[:120]!r})")


def cmd_probe():
    pk = package()
    log(f"dataset: {pk.get('title')}  licence: {pk.get('license_title')}  updated: {pk.get('metadata_modified')}")
    for res in pk.get("resources", []):
        log(f"\nresource: {res.get('name')}  format={res.get('format')}  size={res.get('size')}  "
            f"modified={res.get('last_modified')}\n  url: {res.get('url')}")
        try:
            r = requests.get(res["url"], headers=HEAD, timeout=120, stream=True)
            r.raise_for_status()
            chunk = next(r.iter_content(chunk_size=2_000_000))
            nm = res.get("url", "").split("?")[0] or res.get("name", "")
            df = read_any(chunk, nm, partial=not nm.lower().endswith((".xlsx", ".xls", ".zip")))
            if "атрибут" in (res.get("name") or "").lower():
                pd.set_option("display.width", 200)
                log("  attribute description, all rows:\n" + df.to_string())
            else:
                log(f"  columns ({df.shape[1]}): {list(df.columns)}")
                safe = [c for c in df.columns if not re.search(r"name|party|pib|фіо|прізвище", c, re.I)]
                log("  first rows (name columns hidden, R6):\n" + df[safe].head(3).to_string())
        except Exception as ex:
            log(f"  (could not read a sample: {ex})")
    log("\nNext: set RESOURCES (which file holds declarations by community and age/sex) and COLS, then `pull`.")


def cmd_pull():
    pk = package()
    day = time.strftime("%Y-%m-%d")
    out = RAW / day
    out.mkdir(parents=True, exist_ok=True)
    got = 0
    for res in pk.get("resources", []):
        nm = res.get("name") or ""
        if not any(s.lower() in (nm + res.get("url", "")).lower() for s in RESOURCES):
            continue
        url = res["url"]
        fn = out / (re.sub(r"[^\w.-]+", "_", nm) + "." + (res.get("format") or "bin").lower())
        log(f"downloading {nm} -> {fn.relative_to(BASE)}")
        with requests.get(url, headers=HEAD, timeout=600, stream=True) as r:
            r.raise_for_status()
            with open(fn, "wb") as f:
                for chunk in r.iter_content(chunk_size=8_000_000):
                    f.write(chunk)
        got += 1
    (out / "meta.json").write_text(json.dumps({"dataset": DATASET, "accessed": day, "licence": pk.get("license_title"),
                                               "resources": RESOURCES}, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"{got} file(s) in {out.relative_to(BASE)}")


def latest_raw_dir():
    dirs = sorted(p for p in RAW.glob("20*") if p.is_dir())
    if not dirs:
        sys.exit("no raw download: run `pull` first")
    return dirs[-1]


def koatuu_crosswalk(path):
    """KOATUU (10 digits) -> KATOTTG (UA + 17 digits) from the codifier's comparison table (xlsx or csv; columns
    found by the shape of their values). data.gov.ua: 'Кодифікатор адміністративно-територіальних одиниць та
    територій територіальних громад', resource 'Порівняльна таблиця КОАТУУ — КАТОТТГ' (Minregion, CC BY)."""
    if not path or not Path(path).exists():
        sys.exit("the source carries KOATUU codes: download the KOATUU-KATOTTG comparison table and pass --koatuu-xw <file>")
    p = Path(path)
    df = pd.read_excel(p, dtype=str) if p.suffix.lower() in (".xlsx", ".xls") else pd.read_csv(p, dtype=str)
    ko = ka = None
    for c in df.columns:
        v = df[c].astype(str).str.strip()
        if ka is None and v.str.fullmatch(r"UA\d{17}").mean() > 0.5:
            ka = c
        elif ko is None and v.str.replace(r"\D", "", regex=True).str.fullmatch(r"\d{10}").mean() > 0.5:
            ko = c
    if ko is None or ka is None:
        sys.exit(f"could not find KOATUU and KATOTTG columns in {p.name}: {list(df.columns)}")
    x = df[[ko, ka]].dropna()
    x[ko] = x[ko].astype(str).str.replace(r"\D", "", regex=True).str.zfill(10)
    x[ka] = x[ka].astype(str).str.strip().str.upper()
    x = x.drop_duplicates(ko)
    log(f"crosswalk {p.name}: {len(x)} KOATUU codes")
    return dict(zip(x[ko], x[ka]))


def cmd_build(raw_dir, koatuu_xw=None):
    if not COLS or "count" not in COLS.values():
        sys.exit("set COLS from the probe output first (at least the count column and katottg or hromada+oblast)")
    raw_dir = Path(raw_dir) if raw_dir else latest_raw_dir()
    day = raw_dir.name
    files = [p for p in raw_dir.iterdir() if p.suffix.lower() in (".csv", ".xlsx", ".zip")]
    frames = [read_any(p.read_bytes(), p.name) for p in files]
    df = pd.concat(frames, ignore_index=True)
    df = df.rename(columns={k: v for k, v in COLS.items() if k in df})
    missing = [v for v in ("count",) if v not in df]
    if missing:
        sys.exit(f"columns not found after mapping: {missing}; columns are {list(df.columns)}")
    df["count"] = pd.to_numeric(df["count"].astype(str).str.replace(r"[^\d.]", "", regex=True), errors="coerce")

    keys = pd.read_csv(KEYS, dtype=str)
    keys["k3"] = keys["k3"].str.zfill(7)
    import importlib
    sys.path.insert(0, str(BASE))
    if "koatuu" in df and not koatuu_xw and {"hromada", "oblast"} <= set(df.columns):
        df = df.rename(columns={"koatuu": "koatuu_h"})      # grouping key only; the name route places the hromada
    if "katottg" in df:
        ob = importlib.import_module("03_openbudget")
        df["k3"], _ = ob.katottg_parts(df["katottg"].astype("string"))     # UA + oblast + raion + hromada -> k3
    elif "koatuu" in df:
        ob = importlib.import_module("03_openbudget")
        xw = koatuu_crosswalk(koatuu_xw)
        code = df["koatuu"].astype(str).str.replace(r"\D", "", regex=True).str.zfill(10)
        kat = code.map(xw)
        df["k3"], _ = ob.katottg_parts(kat.astype("string"))
        log(f"KOATUU -> KATOTTG: {kat.notna().mean():.1%} of rows mapped through the crosswalk")
    elif {"hromada", "oblast"} <= set(df.columns):
        # name match, one row per hromada (oblast + hromada name, KOATUU as the grouping key), through the matcher of
        # 33_elections_2020.py (stem and council type within the oblast, centre settlement, stem only, close spelling;
        # ambiguous matches dropped). Hromada names are not personal data.
        e33 = importlib.import_module("33_elections_2020")
        grp = ["oblast", "hromada"] + (["koatuu_h"] if "koatuu_h" in df else [])
        u = df[grp].drop_duplicates().reset_index(drop=True)
        ob_ = u["oblast"].astype(str).str.strip()
        low = ob_.str.lower()
        c = pd.DataFrame(index=u.index)
        city = low.str.replace(r"[^а-яіїєґ]", "", regex=True).isin(["київ", "мкиїв", "містокиїв"])
        crimea = low.str.contains("крим") | low.str.contains("автономн")
        c["oblast"] = np.where(city, "м. Київ", np.where(crimea, "Автономна Республіка Крим",
                               ob_.str.capitalize() + np.where(low.str.contains("област"), "", " область")))
        typ = u["hromada"].map(lambda n: e33.stem_type(n)[1])
        c["council_type"] = typ.map({"m": "міська", "s": "селищна", "v": "сільська"}).fillna("сільська")
        c["rada_name"] = u["hromada"].astype(str)
        m = e33.match_k3(c)
        u["k3"] = m["k3"].reindex(u.index)
        u["route"] = np.where(u["k3"].notna(), "name", "")
        log(f"hromadas in the source: {len(u)}; placed by name {int(u['k3'].notna().sum())}")
        # fallback: settlement vote. Renamed hromadas and names repeated within an oblast (the source gives the name
        # without its type) are placed by the settlements named in their rows: each settlement name that is unique in
        # its oblast in the KATOTTG codifier (34_schools.settlements) votes for its hromada, weighted by declarations;
        # accepted when one hromada has >= 60 % of the placed weight and is not already taken by another row.
        if u["k3"].isna().any() and "settlement" in df:
            s34 = importlib.import_module("34_schools")
            st, _ = s34.settlements()
            st = st.dropna(subset=["k3"])
            uniq = st.groupby(["obl", "nn"])["k3"].agg(lambda x: x.iloc[0] if x.nunique() == 1 else None).dropna()
            taken = set(u["k3"].dropna())
            miss_i = u.index[u["k3"].isna()]
            sub = df.merge(u.loc[miss_i, grp].assign(_u=miss_i), on=grp, how="inner")
            sub["_obl"] = sub["oblast"].map(s34.obl_norm)
            sub["_nn"] = sub["settlement"].map(s34.norm)
            sub["_k3"] = pd.Series(list(zip(sub["_obl"], sub["_nn"]))).map(uniq).values
            placed = []
            for i, g in sub.groupby("_u"):
                w = g.dropna(subset=["_k3"]).groupby("_k3")["count"].sum().sort_values(ascending=False)
                if w.empty:
                    continue
                share = w.iloc[0] / w.sum()
                if share >= 0.6 and w.index[0] not in taken:
                    u.at[i, "k3"], u.at[i, "route"] = w.index[0], "settlements"
                    taken.add(w.index[0])
                    placed.append(f"{u.at[i, 'hromada']} -> {w.index[0]} ({share:.0%})")
            log(f"placed by settlement vote: {len(placed)}" + (": " + "; ".join(placed) if placed else ""))
        miss = u[u["k3"].isna()]
        if len(miss):
            log(f"still unplaced ({len(miss)}): " + "; ".join(f"{r.oblast[:14]}|{r.hromada}" for r in miss.itertuples()))
        df = df.merge(u[grp + ["k3"]], on=grp, how="left")
    else:
        sys.exit("COLS must map a katottg column, a koatuu column (with --koatuu-xw), or hromada + oblast columns")
    unmatched = df["k3"].isna().mean()
    log(f"rows {len(df)}, unmatched to a hromada {unmatched:.1%}")
    df = df[df["k3"].notna()]

    def band(v):
        m = re.search(r"\d+", str(v))
        if m:                                              # single years of age (the NHSU file, 2026)
            a = int(m.group())
            return "0-17" if a < 18 else "18-64" if a < 65 else "65+"
        v = str(v).strip().lower()
        for b, labels in AGE_BANDS.items():
            if any(v.startswith(l.lower()) for l in labels):
                return b
        return "other"
    df["band"] = df["age"].map(band) if "age" in df else "all"
    tot = df.groupby("k3")["count"].sum().rename("decl_total")
    byband = df.pivot_table(index="k3", columns="band", values="count", aggfunc="sum").add_prefix("decl_")
    out = pd.concat([tot, byband], axis=1).reset_index()
    if "sex" in df:
        sx = df.assign(_s=df["sex"].astype(str).str.lower().str[:1]).pivot_table(index="k3", columns="_s", values="count", aggfunc="sum")
        for c in sx.columns:
            out[f"decl_sex_{c}"] = out["k3"].map(sx[c])
    pop = pd.read_csv(POP, dtype={"k3": str})
    pop["k3"] = pop["k3"].str.zfill(7)
    out = out.merge(pop[["k3", "pop_ghs_2020"]], on="k3", how="left")
    out["decl_per1000_pop2020"] = 1000 * out["decl_total"] / pd.to_numeric(out["pop_ghs_2020"], errors="coerce").where(lambda v: v > 0)
    if "decl_65+" in out and "decl_total" in out:
        out["decl_share_65plus"] = out["decl_65+"] / out["decl_total"].where(out["decl_total"] > 0)
    if "decl_0-17" in out:
        out["decl_share_0_17"] = out["decl_0-17"] / out["decl_total"].where(out["decl_total"] > 0)
    out["snapshot"] = day
    out = keys[["k1", "k2", "k3", "name"]].merge(out.drop(columns=["pop_ghs_2020"]), on="k3", how="left")
    out.to_csv(OUT, index=False)
    r = out["decl_per1000_pop2020"]
    log(f"wrote {OUT.relative_to(BASE)}: {int(out['decl_total'].notna().sum())} hromadas with declarations; "
        f"per 1,000 residents (2020): median {r.median():.0f}, p10 {r.quantile(.1):.0f}, p90 {r.quantile(.9):.0f}; "
        f"below 300: {int((r < 300).sum())} hromadas (probably served from a neighbouring hromada), "
        f"above 1,200: {int((r > 1200).sum())} (serving neighbours, or inflow)")
    long = out.dropna(subset=["decl_total"])
    if OUT_LONG.exists():
        prev = pd.read_csv(OUT_LONG, dtype={"k1": str, "k2": str, "k3": str})
        prev = prev[prev["snapshot"] != day]
        long = pd.concat([prev, long], ignore_index=True)
    long.to_csv(OUT_LONG, index=False)
    log(f"wrote {OUT_LONG.relative_to(BASE)}: snapshots {sorted(long['snapshot'].unique())}")

    dd_fn = TIDY / "data_dictionary.csv"
    if dd_fn.exists():
        src = "NHSU declarations with a primary-care doctor, data.gov.ua a8228262 (weekly)"
        lic = "CC BY 4.0 — National Health Service of Ukraine; counts per hromada only (R1, R6)"
        rows = [("decl_total", src, lic, "count", day, "hromada", "active declarations, all ages"),
                ("decl_per1000_pop2020", src, lic, "per 1,000", day, "hromada", "decl_total / GHS-POP 2020 x 1,000 (declarations lag moves; read the change)"),
                ("decl_share_65plus", src, lic, "share", day, "hromada", "declarations aged 65+ / total"),
                ("decl_share_0_17", src, lic, "share", day, "hromada", "declarations aged 0-17 / total")]
        new = pd.DataFrame(rows, columns=["indicator", "source", "licence", "unit", "year", "level", "method"])
        dd = pd.read_csv(dd_fn)
        dd = dd[~dd["indicator"].astype(str).str.startswith("decl_")]
        for c in dd.columns:
            if c not in new:
                new[c] = ""
        pd.concat([dd, new[dd.columns]], ignore_index=True).to_csv(dd_fn, index=False)


def main():
    ap = argparse.ArgumentParser(description="NHSU declarations per hromada")
    ap.add_argument("cmd", choices=("probe", "pull", "build"))
    ap.add_argument("--raw-dir", default=None)
    ap.add_argument("--koatuu-xw", default=None, help="KOATUU-KATOTTG comparison table (xlsx/csv) if the source uses KOATUU")
    a = ap.parse_args()
    if a.cmd == "probe":
        cmd_probe()
    elif a.cmd == "pull":
        cmd_pull()
    else:
        cmd_build(a.raw_dir, a.koatuu_xw)


if __name__ == "__main__":
    main()
