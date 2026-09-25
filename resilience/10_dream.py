#!/usr/bin/env python3
"""
10_dream.py — DREAM recovery / public-investment projects per hromada (k3)

  python 10_dream.py list                       # all project ids (paged by update time)
  python 10_dream.py fetch [--limit N] [--workers 3]   # project JSON, cached, resumable
  python 10_dream.py probe                      # field structure of cached projects
  python 10_dream.py aggregate                  # tidy/dream_k3.csv + coverage

API: https://public-api.dream.gov.ua/marketplace/public/dream/ideas[/{id}]
     (OpenAPI: github.com/open-contracting/dream-api-docs). Locations are KATOTTG codes
     (gazetteer scheme UA-CATOTTG); a project counts once per hromada it touches.
Licence: public open data of the Ministry for Development / Restoration Agency — attribute DREAM.
Caveat: a DREAM entry measures administrative capacity to prepare and publish projects
(and donor attention) as much as need; damage-heavy hromadas file more.
Privacy: probe prints no names or contacts; aggregate stores counts only.
"""
import argparse
import gzip
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
import pyogrio

BASE = Path(__file__).resolve().parent
QGIS = BASE.parent / "viina" / "qgis"
RAW = BASE / "raw" / "dream"
DET = RAW / "ideas"
TIDY, LOGS = BASE / "tidy", BASE / "logs"
for d in (RAW, DET, TIDY, LOGS):
    d.mkdir(parents=True, exist_ok=True)
API = "https://public-api.dream.gov.ua/marketplace/public/dream/ideas"
IDS = RAW / "ids.csv"
HDR = {"User-Agent": "resilience-research/0.1", "Accept": "application/json"}
UNSAFE = re.compile(r"name|contact|email|phone|tel|person|fio|signer|author|user", re.I)
SHOW = re.compile(r"status|stage|scheme|identifiers|date|period|sector|type|category|currency", re.I)
_logf = None


def log(*a):
    m = " ".join(str(x) for x in a)
    print(m, flush=True)
    if _logf:
        _logf.write(m + "\n")
        _logf.flush()


def get_json(url, params=None, retries=4):
    full = url + ("?" + urllib.parse.urlencode(params) if params else "")
    last = ""
    for att in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(full, headers=HDR), timeout=120) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}"
            if e.code == 404:
                return None
            time.sleep(10 if e.code == 429 else 3)
        except Exception as e:
            last = str(e)
            time.sleep(3)
    raise RuntimeError(f"{full}: {last}")


def cmd_list(a):
    ids, frm, page = {}, None, 0
    while page < 5000:
        params = {"order": "asc"}
        if frm:
            params["from"] = frm
        js = get_json(API, params)
        data = js.get("data", []) if isinstance(js, dict) else (js or [])
        if page == 0:
            log(f"first page: {len(data)} items; keys of first item: "
                f"{list(data[0].keys()) if data else '-'}")
        new, last = 0, frm
        for it in data:
            i = (it.get("internal") or {}).get("id")
            u = (it.get("external") or {}).get("updated")
            if i and i not in ids:
                ids[i] = u
                new += 1
            if u and (last is None or u > last):
                last = u
        page += 1
        if page % 20 == 0:
            log(f"  page {page}: ids {len(ids):,}  last updated {last}")
        if not data or new == 0 or last == frm:
            break
        frm = last
        time.sleep(0.2)
    pd.DataFrame({"id": list(ids), "updated": list(ids.values())}).to_csv(IDS, index=False)
    log(f"wrote {IDS}  ids={len(ids):,}  pages={page}")


def path_of(i):
    return DET / f"{i}.json.gz"


def fetch_one(i):
    p = path_of(i)
    if p.exists() and p.stat().st_size > 0:
        return "cached"
    js = get_json(f"{API}/{i}")
    if js is None:
        return "404"
    tmp = p.with_suffix(".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8") as f:
        json.dump(js, f, ensure_ascii=False)
    tmp.rename(p)
    time.sleep(0.2)
    return "ok"


def cmd_fetch(a):
    ids = pd.read_csv(IDS)["id"].tolist()
    if a.limit:
        ids = ids[: a.limit]
    todo = [i for i in ids if not path_of(i).exists()]
    log(f"fetch: {len(ids):,} ids, to fetch {len(todo):,}, workers {a.workers}")
    t0, done, st = time.time(), 0, Counter()
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = {ex.submit(fetch_one, i): i for i in todo}
        for f in as_completed(futs):
            try:
                st[f.result()] += 1
            except Exception as e:
                st["fail"] += 1
                if st["fail"] <= 3:
                    log(f"  fail: {e}")
            done += 1
            if done % 200 == 0 or done == len(todo):
                rate = done / max(time.time() - t0, 1)
                log(f"  {done:,}/{len(todo):,}  {dict(st)}  {rate:.2f}/s  "
                    f"eta {(len(todo)-done)/max(rate,1e-6)/60:.0f} min")


def load(p):
    with gzip.open(p, "rt", encoding="utf-8") as f:
        js = json.load(f)
    return js.get("data", js) if isinstance(js, dict) else js


def walk(o, prefix=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from walk(v, f"{prefix}/{k}")
    elif isinstance(o, list):
        for v in o:
            yield from walk(v, f"{prefix}[]")
    else:
        yield prefix, o


def gazetteers(o):
    if isinstance(o, dict):
        if o.get("scheme") in ("UA-CATOTTG", "UA-COATU") and "identifiers" in o:
            yield o["scheme"], o.get("identifiers") or []
        for v in o.values():
            yield from gazetteers(v)
    elif isinstance(o, list):
        for v in o:
            yield from gazetteers(v)


def cmd_probe(a):
    files = sorted(DET.glob("*.json.gz"))[:300]
    if not files:
        sys.exit("run 'fetch --limit 200' first")
    paths, ex = Counter(), {}
    for p in files:
        seen = set()
        for k, v in walk(load(p)):
            if k in seen:
                continue
            seen.add(k)
            paths[k] += 1
            leaf = k.rsplit("/", 1)[-1]
            if SHOW.search(leaf) and not UNSAFE.search(k) and v not in (None, ""):
                ex.setdefault(k, Counter())[str(v)[:60]] += 1
    log(f"{len(files)} projects; field paths present in >=10%:")
    for k, n in sorted(paths.items(), key=lambda x: (-x[1], x[0])):
        if n >= 0.1 * len(files):
            top = ", ".join(f"{v} ({c})" for v, c in ex.get(k, Counter()).most_common(4))
            log(f"  {n/len(files):5.0%}  {k[:90]:90s} {top[:110]}")


def status_of(o):
    """internal.status like 'cancelled:mistaken' / 'pending:defined' / 'active:approved'."""
    if isinstance(o, dict):
        st = (o.get("internal") or {}).get("status")
        if isinstance(st, str) and st:
            return st
        cdu = o.get("cdu_response") or {}
        if isinstance(cdu.get("status"), str):
            det = cdu.get("statusDetails")
            return cdu["status"] + (f":{det}" if isinstance(det, str) else "")
    return "unknown"


def cmd_aggregate(a):
    files = sorted(DET.glob("*.json.gz"))
    rec, st, kinds = [], Counter(), Counter()
    for p in files:
        o = load(p)
        s = status_of(o)
        st[s] += 1
        main = s.split(":")[0]
        valid = main not in ("cancelled", "unsuccessful")
        k3s, coarse, coatu = set(), 0, 0
        for scheme, idents in gazetteers(o):
            for code in idents:
                code = str(code).strip().upper()
                if scheme == "UA-COATU":
                    coatu += 1
                    continue
                if re.fullmatch(r"UA\d{17}", code):
                    if code[6:9] != "000":
                        k3s.add(code[2:9])
                    elif code[2:4] in ("80", "85"):
                        k3s.add(code[2:4] + "00000")
                    else:
                        coarse += 1
        if valid:
            kinds["with_k3" if k3s else ("coarse_only" if coarse else ("coatu_only" if coatu else "none"))] += 1
        for k in k3s:
            rec.append({"k3": k, "main": main, "valid": valid})
    log(f"projects {len(files):,}")
    log("status counts: " + str(dict(st.most_common(12))))
    log(f"valid (not cancelled/unsuccessful) by location type: {dict(kinds)}")
    if not rec:
        sys.exit("no hromada-level locations found — run probe and paste output")
    df = pd.DataFrame(rec)
    v = df[df["valid"]]
    out = pd.DataFrame({"dream_n": v.groupby("k3").size(),
                        "dream_n_active": v[v["main"] == "active"].groupby("k3").size(),
                        "dream_n_pending": v[v["main"] == "pending"].groupby("k3").size(),
                        "dream_n_cancelled": df[~df["valid"]].groupby("k3").size()})
    out = out.fillna(0).astype(int)
    out.index.name = "k3"
    out = out.reset_index()
    keys = pd.read_csv(TIDY / "keys_hromada.csv", dtype=str)[["k1", "k2", "k3", "name"]]
    ctrl = pyogrio.read_dataframe(QGIS / "hromada_control.gpkg", layer="hromada_control",
                                  read_geometry=False)[["k3", "occupied"]]
    ctrl["k3"] = ctrl["k3"].astype(str).str.zfill(7)
    w = keys.merge(ctrl, on="k3", how="left").merge(out, on="k3", how="left")
    for c in ["dream_n", "dream_n_active", "dream_n_pending", "dream_n_cancelled"]:
        w[c] = w[c].fillna(0).astype(int)
    w.to_csv(TIDY / "dream_k3.csv", index=False)
    free = w[w["occupied"] == False]  # noqa: E712
    log(f"wrote tidy/dream_k3.csv  | k3 codes not in our keys: {len(set(out['k3']) - set(keys['k3']))}")
    log(f"non-occupied hromadas {len(free)}: with >=1 valid project {int((free['dream_n'] > 0).sum())}  "
        f"median {free['dream_n'].median():.0f}  p95 {free['dream_n'].quantile(.95):.0f}  "
        f"max {free['dream_n'].max()}  | with >=1 active {int((free['dream_n_active'] > 0).sum())}")
    log("top 8:\n" + free.nlargest(8, "dream_n")[["k3", "name", "dream_n", "dream_n_active"]].to_string(index=False))
    vk = w[w["k3"] == "2602003"]
    if len(vk):
        log("Verkhovyna:\n" + vk.T.to_string(header=False))


def main():
    global _logf
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["list", "fetch", "probe", "aggregate"])
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    _logf = open(LOGS / f"10_dream_{a.mode}.log", "w", encoding="utf-8")
    {"list": cmd_list, "fetch": cmd_fetch, "probe": cmd_probe, "aggregate": cmd_aggregate}[a.mode](a)


if __name__ == "__main__":
    main()
