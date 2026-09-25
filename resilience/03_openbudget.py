#!/usr/bin/env python3
"""
03_openbudget.py — local-budget indicators per hromada (k3) from openbudget.gov.ua

  python 03_openbudget.py crosswalk
  python 03_openbudget.py pull --items INCOMES --years 2021,2025 [--workers 4] [--test 5] [--all-units]
  python 03_openbudget.py pull --items EXPENSES_ECONOMIC --years 2023-2025
  python 03_openbudget.py indicators

API: https://api.openbudget.gov.ua/api/public/localBudgetData
     budgetCode, budgetItem (INCOMES | EXPENSES), classificationType=ECONOMIC
     (expenses), period=MONTH, year. FAKT_AMT is cumulative YTD -> December = annual.
Budget list with KATOTTG: openbudget.gov.ua/api/localBudgets/aboutBudgets/plain/CSV
Licence: open data per CMU Resolution 835 — attribution to openbudget.gov.ua / MinFin.
"""
import argparse
import gzip
import http.cookiejar
import io
import re
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
import pyogrio

BASE = Path(__file__).resolve().parent
QGIS = BASE.parent / "viina" / "qgis"
RAW = BASE / "raw" / "openbudget"
PROBE_2025 = BASE / "raw" / "openbudget_probe" / "about_IF_oblast_11d.txt"
TIDY, LOGS = BASE / "tidy", BASE / "logs"
for d in (RAW, TIDY, LOGS):
    d.mkdir(parents=True, exist_ok=True)

YEARS = [2021, 2022, 2023, 2024, 2025]
ABOUT = "https://openbudget.gov.ua/api/localBudgets/aboutBudgets/plain/CSV"
DATA = "https://api.openbudget.gov.ua/api/public/localBudgetData"
ITEMS = {"INCOMES": {"budgetItem": "INCOMES"},
         "EXPENSES_ECONOMIC": {"budgetItem": "EXPENSES", "classificationType": "ECONOMIC"}}
HDR = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
       "Accept": "text/csv,text/plain,application/json,*/*;q=0.8",
       "Accept-Language": "uk-UA,uk;q=0.9,en;q=0.8",
       "Referer": "https://openbudget.gov.ua/"}
XW = TIDY / "crosswalk_budget_k3.csv"
JOBS = TIDY / "budget_jobs.csv"
_lock = threading.Lock()
_logf = None
_cj = http.cookiejar.CookieJar()
_opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(_cj))
_warm = False


def log(*a):
    m = " ".join(str(x) for x in a)
    with _lock:
        print(m, flush=True)
        if _logf:
            _logf.write(m + "\n")
            _logf.flush()


def warm_up():
    global _warm
    with _lock:
        if _warm:
            return
        _warm = True
    try:
        req = urllib.request.Request("https://openbudget.gov.ua/",
                                     headers={**HDR, "Accept": "text/html,*/*;q=0.8"})
        with _opener.open(req, timeout=60) as r:
            r.read()
        log(f"warm-up ok, cookies={len(_cj)}")
    except Exception as e:
        log(f"warm-up failed: {e}")


def http_get(url, params, timeout=180):
    warm_up()
    full = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(full, headers=HDR)
    try:
        with _opener.open(req, timeout=timeout) as r:
            return r.status, r.read(), full
    except urllib.error.HTTPError as e:
        return e.code, (e.read() if hasattr(e, "read") else b""), full
    except Exception as e:
        return None, str(e).encode(), full


def decode(b):
    for enc in ("utf-8-sig", "cp1251"):
        try:
            return b.decode(enc)
        except UnicodeDecodeError:
            pass
    return b.decode("latin-1", errors="replace")


def katottg_parts(s):
    s = s.astype("string").str.strip().str.upper()
    ok = s.str.fullmatch(r"UA[0-9]{17}").fillna(False)
    oo, rr, hhh, ppp, mm = s.str[2:4], s.str[4:6], s.str[6:9], s.str[9:12], s.str[12:14]
    k3 = (oo + rr + hhh).where(ok & (hhh != "000"))
    city = ok & oo.isin(["80", "85"]) & (rr == "00") & (hhh == "000")
    k3 = k3.mask(city, oo + "00000")
    hromada_level = ok & (ppp == "000") & (mm == "00")
    return k3, hromada_level


def norm_bname(s):
    s = s.astype("string").str.lower().fillna("")
    s = s.str.replace(r"[’'ʼ`\"]", "", regex=True)
    s = s.str.replace(r"\b(бюджет|зведений|територіальної|громади|міської|сільської|селищної|"
                      r"міська|сільська|селищна|територіальна|громада)\b", "", regex=True)
    return s.str.replace(r"[^0-9a-zа-яіїєґ]+", "", regex=True)


def load_keys():
    keys = pd.read_csv(TIDY / "keys_hromada.csv", dtype=str)
    ctrl = pyogrio.read_dataframe(QGIS / "hromada_control.gpkg", layer="hromada_control",
                                  read_geometry=False)[["k3", "occupied"]]
    ctrl["k3"] = ctrl["k3"].astype("string").str.zfill(7)
    return keys.merge(ctrl, on="k3", how="left")


# ------------------------------------------------------------- crosswalk
def cmd_crosswalk(args):
    keys = load_keys()
    ours = set(keys["k3"])
    free = set(keys.loc[keys["occupied"] == False, "k3"])  # noqa: E712
    frames = {}
    for y in YEARS:
        dest = RAW / f"about_{y}.csv"
        if not dest.exists():
            st, body, url = http_get(ABOUT, {"year": y, "monthFrom": 1, "monthTo": 12,
                                            "fundType": "TOTAL", "codeBudget": "0910000000"})
            if st == 200 and b";" in body[:300]:
                dest.write_bytes(body)
            else:
                log(f"about {y}: HTTP {st} {body[:120]!r}")
                if y == 2025 and PROBE_2025.exists():
                    dest.write_bytes(PROBE_2025.read_bytes())
                    log(f"about 2025: using probe file {PROBE_2025.name}")
                else:
                    continue
            time.sleep(1.5)
        df = pd.read_csv(io.StringIO(decode(dest.read_bytes())), sep=";", skiprows=1, dtype=str)
        df.columns = [c.strip() for c in df.columns]
        if "katottg" not in df.columns:
            log(f"about {y}: no katottg column, columns={list(df.columns)}")
            continue
        df["year"] = y
        k3, lvl = katottg_parts(df["katottg"])
        df["k3"], df["hromada_level"] = k3, lvl
        frames[y] = df
        log(f"about {y}: rows={len(df)} with_katottg={df['katottg'].notna().sum()} "
            f"k3={df['k3'].notna().sum()} hromada_level={df['hromada_level'].sum()} "
            f"code_len={df['budgetCode'].str.len().value_counts().to_dict()}")

    if not frames:
        sys.exit("no budget list could be read — nothing to crosswalk")

    rows = []
    for y, df in frames.items():
        d = df[df["k3"].notna()].copy()
        d["rank"] = (~d["hromada_level"]).astype(int) * 2 + \
                    (~d["budgetName"].str.match(r"(?i)^бюджет").fillna(False)).astype(int)
        d = d.sort_values(["k3", "rank"]).drop_duplicates("k3")
        d["method"] = "katottg"
        rows.append(d[["year", "budgetCode", "budgetName", "katottg", "k3", "method"]])
    xw = pd.concat(rows, ignore_index=True)

    ref_year = max(frames)
    ref = xw[xw["year"] == ref_year].copy()
    ref["reg"] = ref["budgetCode"].str[:2]
    ref["nn"] = norm_bname(ref["budgetName"])
    ref_u = ref.drop_duplicates(["reg", "nn"], keep=False)
    for y, df in frames.items():
        got = set(xw.loc[xw["year"] == y, "k3"])
        if len(got) >= 0.9 * len(ours):
            continue
        c = df[df["budgetName"].str.contains(r"(?i)територіальн", na=False)
               & ~df["budgetName"].str.contains(r"(?i)зведен", na=False)].copy()
        c["reg"] = c["budgetCode"].str[:2]
        c["nn"] = norm_bname(c["budgetName"])
        mm = c.drop(columns=["k3"]).merge(ref_u[["reg", "nn", "k3"]], on=["reg", "nn"], how="inner")
        mm = mm[~mm["k3"].isin(got)].drop_duplicates("k3")
        mm["method"] = "name"
        log(f"name fallback {y}: +{len(mm)}")
        xw = pd.concat([xw, mm[["year", "budgetCode", "budgetName", "katottg", "k3", "method"]]],
                       ignore_index=True)

    xw.to_csv(XW, index=False)
    log(f"\nwrote {XW}")
    for y in sorted(xw["year"].unique()):
        s = set(xw.loc[xw["year"] == y, "k3"])
        log(f"  {y}: budgets={len(s)} match_ours={len(s & ours)}/{len(ours)} "
            f"non_occupied={len(s & free)}/{len(free)} not_in_ours={len(s - ours)}")
    miss = keys[keys["k3"].isin(free - set(xw.loc[xw["year"] == ref_year, "k3"]))]
    if len(miss):
        log(f"non-occupied without a {ref_year} budget ({len(miss)}, first 20):\n"
            + miss[["k3", "name"]].head(20).to_string(index=False))


# ------------------------------------------------------------------ pull
def cache_path(item, year, code):
    return RAW / item / str(year) / f"{code}.csv.gz"


def fetch_one(item, year, code, retries=4, pause=0.3):
    dest = cache_path(item, year, code)
    if dest.exists() and dest.stat().st_size > 0:
        return "cached", 0
    dest.parent.mkdir(parents=True, exist_ok=True)
    params = {"budgetCode": code, **ITEMS[item], "period": "MONTH", "year": year}
    last = ""
    for att in range(retries):
        st, body, url = http_get(DATA, params)
        if st == 200:
            tmp = dest.with_suffix(".tmp")
            with gzip.open(tmp, "wb") as f:
                f.write(body)
            tmp.rename(dest)
            time.sleep(pause)
            return "ok", len(body)
        last = f"HTTP {st} {body[:120]!r}"
        time.sleep({429: 10, 403: 30}.get(st, 3))
    return "fail:" + last, 0


def read_cached(item, year, code):
    p = cache_path(item, year, code)
    if not p.exists():
        return None
    txt = decode(gzip.open(p).read())
    if not txt.strip():
        return pd.DataFrame()
    try:
        return pd.read_csv(io.StringIO(txt), sep=";", dtype=str)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def build_jobs(xw):
    """All k3 x all YEARS -> budget code (year-specific, else latest). Always complete."""
    xw = xw.copy()
    xw["year"] = xw["year"].astype(int)
    latest = xw[xw["year"] == xw["year"].max()].set_index("k3")["budgetCode"]
    per_year = {(r.k3, r.year): r.budgetCode for r in xw.itertuples()}
    rows = []
    for k3, code_latest in latest.items():
        for y in YEARS:
            code = per_year.get((k3, y))
            rows.append({"k3": k3, "year": y, "budgetCode": code or code_latest,
                         "code_source": "year" if code else "latest"})
    jobs = pd.DataFrame(rows)
    jobs.to_csv(JOBS, index=False)
    return jobs


def cmd_pull(args):
    global _logf
    _logf = open(LOGS / "03_pull.log", "a", encoding="utf-8")
    if not XW.exists() or XW.stat().st_size == 0:
        sys.exit("run 'crosswalk' first")
    jobs = build_jobs(pd.read_csv(XW, dtype=str))
    jobs = jobs[jobs["year"].isin(args.years)]
    keys = load_keys()
    free = set(keys.loc[keys["occupied"] == False, "k3"])  # noqa: E712
    if not args.all_units:
        jobs = jobs[jobs["k3"].isin(free)]
    if args.test:
        pool = [k for k in sorted(set(jobs["k3"])) if k != "2602003"]
        jobs = jobs[jobs["k3"].isin(["2602003"] + pool[: args.test - 1])]
    req = list(dict.fromkeys((it, int(r.year), r.budgetCode)
                             for r in jobs.itertuples() for it in args.items))
    todo = [j for j in req if not (cache_path(*j).exists() and cache_path(*j).stat().st_size > 0)]
    log(f"pull items={args.items} years={args.years} units={jobs['k3'].nunique()} "
        f"requests={len(req)} cached={len(req)-len(todo)} to_fetch={len(todo)} workers={args.workers}")
    fails, t0, done = [], time.time(), 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(fetch_one, *j): j for j in todo}
        for f in as_completed(futs):
            status, n = f.result()
            done += 1
            if status.startswith("fail"):
                fails.append((*futs[f], status))
            if done % 100 == 0 or done == len(todo):
                rate = done / max(time.time() - t0, 1)
                log(f"  {done}/{len(todo)}  fails={len(fails)}  {rate:.2f}/s  "
                    f"eta {(len(todo)-done)/max(rate,1e-6)/60:.0f} min")
    if fails:
        fp = LOGS / "03_pull_failures.csv"
        pd.DataFrame(fails, columns=["item", "year", "code", "status"]).to_csv(
            fp, mode="a", header=not fp.exists(), index=False)
        log(f"failures appended to {fp} ({len(fails)}); first: {fails[0]}  — rerun same command to retry")
    if args.test:
        y = max(args.years)
        sel = jobs[(jobs["year"] == y) & (jobs["k3"] == "2602003")]
        r = sel.iloc[0] if len(sel) else jobs[jobs["year"] == y].iloc[0]
        for it in args.items:
            df = read_cached(it, y, r.budgetCode)
            log(f"\n[{it} {y} k3={r.k3} code={r.budgetCode}] rows={0 if df is None else len(df)}")
            if df is not None and len(df):
                log("REP_PERIOD last: " + str(sorted(df["REP_PERIOD"].unique(),
                                                     key=lambda s: s.split(".")[::-1])[-2:]))
                log("FUND_TYP: " + str(df["FUND_TYP"].value_counts().to_dict()))


# ------------------------------------------------------------ indicators
def annual(df, code_col):
    """December (or latest) cumulative row per fund type and code."""
    if df is None or df.empty or "REP_PERIOD" not in df.columns:
        return None, None
    d = df.copy()
    d["m"] = d["REP_PERIOD"].str.extract(r"^(\d{1,2})\.")[0].astype(int)
    last = d["m"].max()
    d = d[d["m"] == last]
    d["amt"] = pd.to_numeric(d["FAKT_AMT"].astype("string").str.replace(",", ".", regex=False),
                             errors="coerce").fillna(0)
    d["code"] = pd.to_numeric(d[code_col], errors="coerce")
    return d, last


def income_metrics(df):
    d, last = annual(df, "COD_INCO")
    if d is None:
        return None
    T, C = d[d["FUND_TYP"] == "T"], d[d["FUND_TYP"] == "C"]
    pdfo = T[(T["code"] >= 11010000) & (T["code"] < 11020000)]
    mil = pdfo["NAME_INC"].str.contains("військовослуж", case=False, na=False)
    return {"rev_total": T["amt"].sum(),
            "transfers": T[(T["code"] >= 40000000) & (T["code"] < 50000000)]["amt"].sum(),
            "own_gf": C[C["code"] < 40000000]["amt"].sum(),
            "pdfo": pdfo["amt"].sum(),
            "pdfo_mil": pdfo.loc[mil, "amt"].sum(),
            "inc_last_month": last}


def expense_metrics(df):
    d, last = annual(df, "COD_CONS_EK")
    if d is None:
        return None
    T = d[d["FUND_TYP"] == "T"]
    return {"exp_total": T["amt"].sum(),
            "capex": T[(T["code"] >= 3000) & (T["code"] < 4000)]["amt"].sum(),
            "exp_last_month": last}


def find_population():
    p = QGIS / "unit_stats.gpkg"
    for ln, _ in pyogrio.list_layers(p):
        df = pyogrio.read_dataframe(p, layer=ln, read_geometry=False)
        if "k3" in df.columns and len(df) > 1500:
            pc = [c for c in df.columns if re.search(r"pop", c, re.I) and df[c].dtype.kind in "if"]
            if pc:
                df["k3"] = df["k3"].astype("string").str.zfill(7)
                log(f"population: {p.name}:{ln}.{pc[0]} (other pop cols: {pc[1:]})")
                return df[["k3", pc[0]]].drop_duplicates("k3").rename(columns={pc[0]: "pop"})
    log("population column not found — per-capita indicators skipped")
    return None


def cmd_indicators(args):
    global _logf
    _logf = open(LOGS / "03_indicators.log", "w", encoding="utf-8")
    jobs = build_jobs(pd.read_csv(XW, dtype=str))
    recs = []
    for r in jobs.itertuples():
        im = income_metrics(read_cached("INCOMES", r.year, r.budgetCode))
        em = expense_metrics(read_cached("EXPENSES_ECONOMIC", r.year, r.budgetCode))
        if not (im or em):
            continue
        rec = {"k3": r.k3, "year": r.year, "code_source": r.code_source}
        rec.update(im or {})
        rec.update(em or {})
        recs.append(rec)
    long = pd.DataFrame(recs)
    long.to_csv(TIDY / "budget_long_k3_year.csv", index=False)
    log(f"long table: {len(long)} k3-year rows -> tidy/budget_long_k3_year.csv")
    log("rows per year: " + str(long.groupby("year").size().to_dict()))
    for c in ("inc_last_month", "exp_last_month"):
        if c in long:
            part = long[long[c].notna() & (long[c] < 12)]
            if len(part):
                log(f"WARNING {len(part)} k3-years with {c} < 12")

    vals = [c for c in ["rev_total", "transfers", "own_gf", "pdfo", "pdfo_mil", "exp_total", "capex"]
            if c in long]
    w = long.pivot_table(index="k3", columns="year", values=vals, aggfunc="first")
    w.columns = [f"{a}_{b}" for a, b in w.columns]
    w = w.reset_index()
    g = lambda c: w[c] if c in w else pd.Series(float("nan"), index=w.index)  # noqa: E731
    out = pd.DataFrame({"k3": w["k3"]})
    out["own_rev_gf_2025"] = g("own_gf_2025")
    out["transfer_dep_2025"] = g("transfers_2025") / g("rev_total_2025")
    civ25 = g("pdfo_2025") - g("pdfo_mil_2025")
    civ21 = g("pdfo_2021") - g("pdfo_mil_2021")
    out["pdfo_civ_2025"] = civ25
    ratio = civ25 / civ21.where(civ21 > 0)
    out["pdfo_civ_growth_rel_2125"] = ratio / ratio.median()
    caps = [g(f"capex_{y}") / g(f"exp_total_{y}").where(g(f"exp_total_{y}") > 0) for y in (2023, 2024, 2025)]
    out["capex_share_2325"] = pd.concat(caps, axis=1).mean(axis=1, skipna=True)
    out["pdfo_mil_share_2025"] = g("pdfo_mil_2025") / g("pdfo_2025").where(g("pdfo_2025") > 0)

    pop = find_population()
    if pop is not None:
        out = out.merge(pop, on="k3", how="left")
        out["own_rev_gf_pc_2025"] = out["own_rev_gf_2025"] / out["pop"].where(out["pop"] > 0)
        out["pdfo_civ_pc_2025"] = out["pdfo_civ_2025"] / out["pop"].where(out["pop"] > 0)

    keys = load_keys()
    out = keys[["k1", "k2", "k3", "name", "occupied"]].merge(out, on="k3", how="left")
    out.to_csv(TIDY / "budget_indicators_k3.csv", index=False)
    log(f"wrote tidy/budget_indicators_k3.csv rows={len(out)}")

    free = out[out["occupied"] == False]  # noqa: E712
    log(f"\ncoverage on {len(free)} non-occupied hromadas:")
    for c in [c for c in out.columns if c not in ("k1", "k2", "k3", "name", "occupied", "pop")]:
        v = pd.to_numeric(free[c], errors="coerce")
        log(f"  {c:26s} n={v.notna().sum():5d}  median={v.median():>14,.3f}  "
            f"p05={v.quantile(.05):>14,.3f}  p95={v.quantile(.95):>14,.3f}")
    vk = free[free["k3"] == "2602003"]
    if len(vk):
        log("\nVerkhovyna 2602003:\n" + vk.T.to_string(header=False))

    src = "openbudget.gov.ua (MinFin/Treasury), api.openbudget.gov.ua/api/public/localBudgetData"
    lic = "Ukrainian open data, CMU Resolution 835 — attribution required"
    dd_new = pd.DataFrame([
        ["own_rev_gf_2025", src, lic, "UAH", "2025", "hromada",
         "General fund revenue excl. transfers (codes <40000000, FUND_TYP=C), December YTD"],
        ["own_rev_gf_pc_2025", src, lic, "UAH/person", "2025", "hromada",
         "own_rev_gf_2025 / population from unit_stats.gpkg (dated GeoNames baseline — biased)"],
        ["transfer_dep_2025", src, lic, "ratio", "2025", "hromada",
         "Official transfers (codes 4xxxxxxx) / total revenue, FUND_TYP=T"],
        ["pdfo_civ_2025", src, lic, "UAH", "2025", "hromada",
         "PIT 1101xxxx excl. lines naming військовослужбовці; paid at employer's address"],
        ["pdfo_civ_pc_2025", src, lic, "UAH/person", "2025", "hromada",
         "pdfo_civ_2025 / population (dated baseline)"],
        ["pdfo_civ_growth_rel_2125", src, lic, "ratio to national median", "2021-2025", "hromada",
         "(civilian PIT 2025 / 2021) / median of that ratio; inflation-neutral; 2021 codes via name match"],
        ["capex_share_2325", src, lic, "ratio", "2023-2025", "hromada",
         "Capital expenditure (KEK 3xxx) / total expenditure, FUND_TYP=T, mean of 3 years"],
        ["pdfo_mil_share_2025", src, lic, "ratio", "2025", "hromada",
         "Military PIT share of PIT — flag for garrison hromadas, not a resilience indicator"],
    ], columns=["indicator", "source", "licence", "unit", "year", "level", "method"])
    ddp = TIDY / "data_dictionary.csv"
    dd = pd.read_csv(ddp, dtype=str) if ddp.exists() else pd.DataFrame(columns=dd_new.columns)
    dd = pd.concat([dd[~dd["indicator"].isin(dd_new["indicator"])], dd_new], ignore_index=True)
    dd.to_csv(ddp, index=False)
    log(f"data dictionary updated: {len(dd)} indicators")


def parse_years(s):
    out = []
    for part in s.split(","):
        part = part.strip()
        if "-" in part:
            a, b = (int(x) for x in part.split("-"))
            out += list(range(a, b + 1))
        elif part:
            out.append(int(part))
    return sorted(set(out))


def main():
    global _logf
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["crosswalk", "pull", "indicators"])
    ap.add_argument("--test", type=int, default=0)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--years", default="2021-2025")
    ap.add_argument("--items", default="INCOMES,EXPENSES_ECONOMIC")
    ap.add_argument("--all-units", action="store_true", help="include occupied hromadas")
    a = ap.parse_args()
    a.years = parse_years(a.years)
    a.items = [i.strip() for i in a.items.split(",") if i.strip()]
    bad = [i for i in a.items if i not in ITEMS]
    if bad:
        sys.exit(f"unknown items {bad}; choose from {list(ITEMS)}")
    if a.mode == "crosswalk":
        _logf = open(LOGS / "03_crosswalk.log", "w", encoding="utf-8")
        cmd_crosswalk(a)
    elif a.mode == "pull":
        cmd_pull(a)
    else:
        cmd_indicators(a)


if __name__ == "__main__":
    main()
