#!/usr/bin/env python3
"""
14_idp_dtm.py — registered IDPs per raion (IOM DTM Area Baseline Assessment, raion level)

  python 14_idp_dtm.py [--round N]      # default: latest round on HDX

Sources, tried in order:
  1. HDX dataset "ukraine-displacement-data-baseline-assessment-raion-level-iom-dtm" (XLSX per round)
  2. HDX resource_show for the known Round 39 raion file (in case the dataset is hidden from the API)
  3. dtm.iom.int dataset pages "ukraine-area-baseline-assessment[-raion-level]-round-N" (XLSX link)
  4. HDX "ukr-iom-dtm-from-api" (API extract; admin 0-1 only at present -> stops with a message)
  The hromada-level file is request-only and is not used.
Parsing is robust: finds the ADM2 P-code column (UA + 4 digits), the IDP count column and,
for API extracts, the latest reporting date / round; prints what it picked.
Outputs: raw/dtm/<file>.xlsx, tidy/idp_raion_k2.csv (k2, idp_registered, idp_per1k_pop2020),
         tidy/idp_hromada_broadcast_k3.csv (raion value repeated for each hromada, flagged),
         data dictionary rows, logs/14_idp_dtm.log
Caveats: registered IDPs (Ministry of Social Policy register) counted where registered, not
         necessarily where living; people who never registered or de-registered are missing;
         raion values broadcast to hromadas carry no within-raion variation.
Licence: IOM DTM terms — cite "IOM DTM Ukraine, Area Baseline Assessment Round N".
"""
import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent
RAW = BASE / "raw" / "dtm"
TIDY, LOGS = BASE / "tidy", BASE / "logs"
for d in (RAW, TIDY, LOGS):
    d.mkdir(parents=True, exist_ok=True)
DATASETS = ["ukraine-displacement-data-baseline-assessment-raion-level-iom-dtm", "ukr-iom-dtm-from-api"]
R39_RESOURCE = "ba9a8cd8-2d25-414e-bd8f-79852c127798"     # "Round 39 — Area Baseline Assessment (Raion level).xlsx"
DTM_PAGES = ["https://dtm.iom.int/datasets/ukraine-area-baseline-assessment-round-{n}",
             "https://dtm.iom.int/datasets/ukraine-area-baseline-assessment-raion-level-round-{n}"]
DTM_ROUNDS = range(46, 35, -1)
HDR = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"}
_logf = open(LOGS / "14_idp_dtm.log", "w", encoding="utf-8")


def log(*a):
    m = " ".join(str(x) for x in a)
    print(m, flush=True)
    _logf.write(m + "\n")
    _logf.flush()


def fetch(url, dest=None, timeout=300):
    req = urllib.request.Request(url, headers=HDR)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
    if dest:
        dest.write_bytes(data)
        return dest
    return data


def hdx(action, **params):
    url = f"https://data.humdata.org/api/3/action/{action}?" + urllib.parse.urlencode(params)
    return json.loads(fetch(url))["result"]


def pick_resources(pkg, round_no):
    """XLSX 'Round N' files (baseline dataset) or all CSV/XLSX files (API extract)."""
    res = pkg.get("resources", [])
    for r in res:
        log(f"  resource: {r.get('name')}  [{r.get('format')}]  modified {str(r.get('last_modified'))[:10]}")
    rounds = []
    for r in res:
        m = re.search(r"round\s*(\d+)", r.get("name", ""), re.I)
        if m and re.search(r"xlsx?", r.get("name", "") + " " + (r.get("format") or ""), re.I):
            rounds.append((int(m.group(1)), r))
    if rounds:
        rounds.sort(key=lambda x: x[0])
        sel = [x for x in rounds if x[0] == round_no] if round_no else [rounds[-1]]
        if not sel:
            sys.exit(f"round {round_no} not found")
        return "baseline", sel[0][0], [sel[0][1]]
    tab = [r for r in res if re.search(r"csv|xlsx?", (r.get("format") or "") + r.get("name", ""), re.I)]
    if not tab:
        sys.exit("no CSV/XLSX resources in dataset")
    return "api", None, tab


def read_any(path):
    if str(path).lower().endswith((".xlsx", ".xls")):
        sheets = pd.read_excel(path, sheet_name=None, dtype=object)
        return pd.concat(sheets.values(), ignore_index=True)
    return pd.read_csv(path, dtype=object, low_memory=False)


def parse_api(paths):
    """DTM API extract: rows with admin2 P-code, latest reporting date; sum IDPs per raion."""
    frames = []
    for p in paths:
        df = read_any(p)
        cols = {c.lower().replace("_", "").replace(" ", ""): c for c in df.columns}
        pc = next((cols[k] for k in cols if "admin2pcode" in k), None)
        val = next((cols[k] for k in cols if k in ("numpresentidpind", "idpnumbers", "numberidps")), None)
        if val is None:
            val = next((cols[k] for k in cols if "idp" in k and pd.to_numeric(df[cols[k]], errors="coerce").notna().mean() > 0.8), None)
        dt = next((cols[k] for k in cols if k in ("reportingdate", "date")), None)
        rd = next((cols[k] for k in cols if k in ("roundnumber", "round")), None)
        op = next((cols[k] for k in cols if k == "operation"), None)
        log(f"  {Path(p).name}: rows {len(df):,}  admin2 col={pc}  value col={val}  date col={dt}  round col={rd}")
        if pc is None or val is None:
            continue
        d = pd.DataFrame({"pcode": df[pc].astype(str).str.strip(),
                          "idp": pd.to_numeric(df[val], errors="coerce"),
                          "date": pd.to_datetime(df[dt], errors="coerce") if dt else pd.NaT,
                          "round": df[rd] if rd else None,
                          "operation": df[op] if op else ""})
        frames.append(d[d["pcode"].str.fullmatch(r"UA\d{4}")])
    if not frames or sum(len(f) for f in frames) == 0:
        sys.exit("no admin2 (raion) rows in the API extract — only oblast-level data available")
    d = pd.concat(frames, ignore_index=True)
    log("  admin2 rows by operation / latest date:")
    for (opn), g in d.groupby("operation", dropna=False):
        log(f"    {str(opn)[:60]:60s} rows {len(g):5d}  dates {g['date'].min()} .. {g['date'].max()}")
    latest = d["date"].max()
    cur = d[d["date"] == latest] if pd.notna(latest) else d
    if cur["operation"].nunique() > 1:
        best = cur.groupby("operation")["pcode"].nunique().idxmax()
        cur = cur[cur["operation"] == best]
        log(f"  several operations on {latest}; using '{best}'")
    dup = cur["pcode"].duplicated().sum()
    if dup:
        log(f"  {dup} repeated raion rows on the latest date (breakdowns) — summed")
    r = cur.groupby("pcode", as_index=False)["idp"].sum()
    r["k2"] = r["pcode"].str[2:6]
    tag = f"API {latest.date() if pd.notna(latest) else '?'}"
    return r.rename(columns={"idp": "idp_registered"})[["k2", "idp_registered"]], tag, str(latest)[:10]


def find_table(xlsx):
    """Return (sheet, df with header, pcode2 column, idp column) or exit with diagnostics."""
    sheets = pd.read_excel(xlsx, sheet_name=None, header=None, dtype=object)
    diag = []
    for sh, raw in sheets.items():
        for hr in range(min(15, len(raw))):
            hdr = [str(x).strip() if pd.notna(x) else "" for x in raw.iloc[hr]]
            if not any(re.search(r"p\s*-?code|pcode|код", h, re.I) for h in hdr):
                continue
            df = raw.iloc[hr + 1:].copy()
            df.columns = [h if h else f"col{i}" for i, h in enumerate(hdr)]
            df = df.dropna(how="all")
            pc2 = None
            for c in df.columns:
                v = df[c].astype(str).str.strip()
                if v.str.fullmatch(r"UA\d{4}").mean() > 0.6:
                    pc2 = c
                    break
            if pc2 is None:
                diag.append(f"{sh} row {hr}: header {hdr[:12]} — no ADM2 P-code column")
                continue
            cands = []
            for c in df.columns:
                if c == pc2 or re.search(r"%|share|female|male|women|men|child|disab|age|name|pcode|code|"
                                         r"oblast|raion|hromada|date|жін|чол|діт", str(c), re.I):
                    continue
                num = pd.to_numeric(df[c], errors="coerce")
                if num.notna().mean() > 0.8 and num.sum() > 1000:
                    score = 2 if re.search(r"idp|впо|внутрішньо|displac", str(c), re.I) else 1
                    cands.append((score, num.sum(), c))
            if cands:
                cands.sort(reverse=True)
                return sh, hr, df, pc2, cands[0][2], [c for _, _, c in cands]
            diag.append(f"{sh} row {hr}: P-code column '{pc2}' but no numeric IDP column")
    sys.exit("could not identify the table:\n  " + "\n  ".join(diag or ["no header row with a P-code"]) +
             "\nsheets: " + ", ".join(sheets))


def try_hdx_resource():
    try:
        r = hdx("resource_show", id=R39_RESOURCE)
        log(f"HDX resource_show: {r.get('name')}  modified {str(r.get('last_modified'))[:10]}")
        return 39, r.get("name") or "Round_39_raion.xlsx", r["url"], str(r.get("last_modified"))[:10]
    except Exception as e:
        log(f"HDX resource_show {R39_RESOURCE}: {e}")
        return None


def try_dtm_pages():
    for n in DTM_ROUNDS:
        for pat in DTM_PAGES:
            url = pat.format(n=n)
            try:
                html = fetch(url, timeout=60).decode("utf-8", "replace")
            except Exception:
                continue
            links = re.findall(r'href="([^"]+\.xlsx[^"]*)"', html, re.I)
            links = [urllib.parse.urljoin(url, l) for l in links]
            log(f"dtm.iom.int round {n}: page found, {len(links)} xlsx link(s)")
            if links:
                rl = [l for l in links if re.search(r"raion|rayon", l, re.I)] or links
                return n, Path(urllib.parse.urlparse(rl[0]).path).name, rl[0], f"round {n}"
    log("dtm.iom.int: no dataset page with an xlsx link found for rounds "
        f"{DTM_ROUNDS.start}..{DTM_ROUNDS.stop + 1}")
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, default=0)
    a = ap.parse_args()

    pkg, kind, rnd, paths, modified = None, None, None, [], ""
    try:
        pkg = hdx("package_show", id=DATASETS[0])
        kind, rnd, resources = pick_resources(pkg, a.round)
    except urllib.error.HTTPError as e:
        log(f"package_show '{DATASETS[0]}': HTTP {e.code}")
        resources = []
    if resources:
        res = resources[0]
        cand = (rnd, res.get("name"), res["url"], str(res.get("last_modified"))[:10])
    else:
        cand = try_hdx_resource() or try_dtm_pages()
        kind = "baseline" if cand else None
    if cand:
        rnd, name, url, modified = cand
        dest = RAW / re.sub(r"[^\w.\-]+", "_", name or f"round_{rnd}.xlsx")
        if dest.suffix.lower() not in (".xlsx", ".xls"):
            dest = dest.with_suffix(".xlsx")
        if not dest.exists():
            fetch(url, dest)
        paths = [dest]
        log(f"downloaded {dest.name} ({dest.stat().st_size / 1e3:.0f} kB)")
    else:
        pkg = hdx("package_show", id=DATASETS[1])
        log(f"falling back to {DATASETS[1]}")
        kind, rnd, resources = pick_resources(pkg, a.round)
        for res in resources:
            dest = RAW / re.sub(r"[^\w.\-]+", "_", res.get("name") or "dtm_api.csv")
            if not dest.suffix:
                dest = dest.with_suffix(".csv")
            if not dest.exists():
                fetch(res["url"], dest)
            paths.append(dest)
    if kind == "baseline":
        sh, hr, df, pc2, idp_col, cands = find_table(paths[0])
        log(f"table: sheet '{sh}', header row {hr}, P-code column '{pc2}', IDP column '{idp_col}'")
        log(f"  other numeric candidates: {cands[1:6]}")
        df["k2"] = df[pc2].astype(str).str.strip().str[2:6]
        df["idp_registered"] = pd.to_numeric(df[idp_col], errors="coerce")
        r = (df[df["k2"].str.fullmatch(r"\d{4}")].groupby("k2", as_index=False)["idp_registered"].sum())
        tag = f"Round {rnd}"
    else:
        r, tag, modified = parse_api(paths)
    rnd = tag
    log(f"raions with values: {len(r)}  total IDPs: {r['idp_registered'].sum():,.0f}  ({tag})")

    keys = pd.read_csv(TIDY / "keys_hromada.csv", dtype=str)
    pop = pd.read_csv(TIDY / "population_k3.csv", dtype={"k3": str})
    pop["k3"] = pop["k3"].str.zfill(7)
    pop["k2"] = pop["k3"].str[:4]
    free = pop[pop["occupied"].astype(str).str.lower().isin(["false", "0"])]
    praion = pop.groupby("k2")["pop_ghs_2020"].sum()
    r["pop_ghs_2020_raion"] = r["k2"].map(praion)
    r["idp_per1k_pop2020"] = r["idp_registered"] / r["pop_ghs_2020_raion"] * 1e3
    r["dtm_round"] = rnd
    our_k2 = set(keys["k3"].str[:4])
    free_k2 = set(free["k2"])
    log(f"match: {len(set(r['k2']) & our_k2)} of {len(r)} DTM raions in our keys; "
        f"raions with non-occupied hromadas covered: {len(set(r['k2']) & free_k2)} of {len(free_k2)}")
    miss = sorted(free_k2 - set(r["k2"]))
    if miss:
        log(f"  non-occupied raions without DTM value: {miss[:20]}")
    r.to_csv(TIDY / "idp_raion_k2.csv", index=False)
    log("wrote tidy/idp_raion_k2.csv")
    log("\nhighest registered IDPs per 1,000 (pre-war GHS population):\n" +
        r.nlargest(8, "idp_per1k_pop2020")[["k2", "idp_registered", "pop_ghs_2020_raion",
                                             "idp_per1k_pop2020"]].round(1).to_string(index=False))

    b = keys[["k1", "k2", "k3", "name"]].merge(r[["k2", "idp_registered", "idp_per1k_pop2020", "dtm_round"]],
                                                on="k2", how="left")
    b["idp_level"] = "raion (broadcast)"
    b.to_csv(TIDY / "idp_hromada_broadcast_k3.csv", index=False)
    vk = b[b["k3"] == "2602003"]
    if len(vk):
        log("\nVerkhovyna raion (2602): " + vk[["idp_registered", "idp_per1k_pop2020"]].round(1).to_string(
            index=False, header=False))
    log("wrote tidy/idp_hromada_broadcast_k3.csv")

    src = f"IOM DTM Ukraine, Area Baseline Assessment (raion level), {rnd}"
    lic = "IOM DTM terms of use — attribution required"
    dd_new = pd.DataFrame([
        ["idp_registered", src, lic, "persons", str(modified)[:10], "raion (k2)",
         "Officially registered IDPs (displaced since 24 Feb 2022) by raion of registration; not where living"],
        ["idp_per1k_pop2020", src + " + JRC GHS-POP", lic + "; EC reuse", "per 1,000 pre-war residents",
         str(modified)[:10], "raion (k2), broadcast to hromadas",
         "idp_registered / sum of pop_ghs_2020 over the raion's hromadas × 1,000"],
    ], columns=["indicator", "source", "licence", "unit", "year", "level", "method"])
    ddp = TIDY / "data_dictionary.csv"
    dd = pd.read_csv(ddp, dtype=str) if ddp.exists() else pd.DataFrame(columns=dd_new.columns)
    dd = pd.concat([dd[~dd["indicator"].isin(dd_new["indicator"])], dd_new], ignore_index=True)
    dd.to_csv(ddp, index=False)
    log(f"data dictionary updated: {len(dd)} indicators")


if __name__ == "__main__":
    main()
