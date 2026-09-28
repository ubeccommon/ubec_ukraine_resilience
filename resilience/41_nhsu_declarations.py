#!/usr/bin/env python3
"""
41_nhsu_declarations.py — present population per hromada from declarations with a primary-care doctor (NHSU).

  python 41_nhsu_declarations.py probe            list the dataset's resources on data.gov.ua and the columns of each
  python 41_nhsu_declarations.py pull             download the resources named in RESOURCES to raw/nhsu/<date>/
  python 41_nhsu_declarations.py build            aggregate to hromada -> tidy/nhsu_declarations_k3.csv
  python 41_nhsu_declarations.py build --raw-dir raw/nhsu/2026-09-28

Source: "Інформація щодо статистики поданих декларацій про вибір лікаря первинної медичної допомоги", National Health
Service of Ukraine, data.gov.ua dataset a8228262-5576-4a14-beb8-789573573546 (CC BY 4.0, weekly). The dataset
describes declarations by region, community (hromada), settlement, facility, doctor, age group and sex. The exact
files and columns were not visible from Claude's workspace (28 Sep 2026): run `probe` first and set RESOURCES and the
column map (COLS) from its output, then `pull` and `build`.

Why: the paper's per-resident measures use GHS-POP 2020 (limitation 16.6). Active declarations are the closest open
measure of the people actually present now, with an age structure, for every hromada. Declarations lag moves (IDPs
often keep their declaration), so the CHANGE since 2021/2022 is the signal, and the level is read with that caveat.
The pattern-language round (docs/pattern_language.md, 5.5) needs it as a candidate condition: population inflow.

Rules: R6 — the doctor-level and facility-level files may carry names of doctors; nothing below hromada level is
written to tidy/, the raw download stays in raw/ (gitignored), and only counts per hromada and age band leave this
script. R1 — no facility locations. Output per hromada: declarations total, by age band (0-17, 18-64, 65+ where the
source allows), by sex, per 1,000 GHS-POP 2020 residents, and the date of the snapshot. Rerun monthly to build a
series; each run appends a dated row set to tidy/nhsu_declarations_long.csv.

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
# hromada (hromada name), oblast (oblast name), settlement (settlement name), age (age band label),
# sex, count (number of active declarations), date (snapshot date, if a column; else the file date is used)
COLS = {
    # "katottg": "katottg",     # e.g. "КАТОТТГ" or "katottg_code"
    # "Громада": "hromada",
    # "Область": "oblast",
    # "Вікова група": "age",
    # "Стать": "sex",
    # "Кількість декларацій": "count",
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


def read_any(content, name):
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
        for sep in (",", ";", "\t"):
            try:
                df = pd.read_csv(io.BytesIO(content), dtype=str, sep=sep, encoding=enc, low_memory=False)
                if df.shape[1] > 1:
                    return df
            except Exception:
                continue
    raise ValueError(f"could not parse {name}")


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
            df = read_any(chunk, res.get("url", "").split("?")[0] or res.get("name", ""))
            log(f"  columns ({df.shape[1]}): {list(df.columns)}")
            log("  first rows:\n" + df.head(3).to_string())
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


def cmd_build(raw_dir):
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
    if "katottg" in df:
        import importlib
        sys.path.insert(0, str(BASE))
        ob = importlib.import_module("03_openbudget")
        df["k3"], _ = ob.katottg_parts(df["katottg"].astype("string"))     # UA + oblast + raion + hromada -> k3
    elif {"hromada", "oblast"} <= set(df.columns):
        # name match: hromada name + oblast (k1 from keys) — the same route as 34_schools.py; ambiguous names are dropped
        import importlib
        sys.path.insert(0, str(BASE))
        norm_oblast = importlib.import_module("33_elections_2020").norm_oblast
        kk = keys.copy()
        kk["_n"] = kk["name"].astype(str).str.lower().str.replace(r"\s+", " ", regex=True)
        kk["_ob"] = kk["oblast_uk"].map(norm_oblast)
        df["_n"] = df["hromada"].astype(str).str.lower().str.replace(r"\s+", " ", regex=True)
        df["_ob"] = df["oblast"].map(norm_oblast)
        m = df.merge(kk[["_n", "_ob", "k3"]].drop_duplicates(), on=["_n", "_ob"], how="left")
        dup = m.groupby(["_n", "_ob"])["k3"].transform("nunique") > 1
        m.loc[dup, "k3"] = np.nan
        df["k3"] = m["k3"].values
    else:
        sys.exit("COLS must map either a katottg column or hromada + oblast columns")
    unmatched = df["k3"].isna().mean()
    log(f"rows {len(df)}, unmatched to a hromada {unmatched:.1%}")
    df = df[df["k3"].notna()]

    def band(v):
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
    log(f"wrote {OUT.relative_to(BASE)}: {int(out['decl_total'].notna().sum())} hromadas with declarations; "
        f"median per 1,000 residents (2020) {out['decl_per1000_pop2020'].median():.0f}")
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
    a = ap.parse_args()
    if a.cmd == "probe":
        cmd_probe()
    elif a.cmd == "pull":
        cmd_pull()
    else:
        cmd_build(a.raw_dir)


if __name__ == "__main__":
    main()
