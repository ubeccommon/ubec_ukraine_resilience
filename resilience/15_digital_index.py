#!/usr/bin/env python3
"""
15_digital_index.py — Digital Transformation Index of hromadas (Mintsyfra, hromada.gov.ua)
step 1: probe the public API used by the portal (endpoints found in its Angular chunks)

  python 15_digital_index.py probe

Endpoints (from the portal code; apiUrl = backend base + /api/front):
  GET {api}/{kind}_region                  region list          (kind unknown: tried below)
  GET {api}/community?region_id=<id>       hromadas of a region (refreshToken may be empty)
  GET {api}/region/<id>?<filters>          region page with hromada index values
  GET {api}/community/<id>                 one hromada
The probe tries the candidate base URLs and kinds, prints status, top-level JSON keys and one
example record per endpoint, and caches responses in raw/digital/api/. No login, no personal data.
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent
CACHE = BASE / "raw" / "digital" / "api"
CACHE.mkdir(parents=True, exist_ok=True)
BASES = ["https://backend.hromada.gov.ua/api/front", "https://hromada.gov.ua/api/front"]
KINDS = ["index", "community", "digital", "general", "cdto", "cnap", "network", "instrumentList", ""]
HDR = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
       "Accept": "application/json", "Referer": "https://hromada.gov.ua/index",
       "Origin": "https://hromada.gov.ua"}


def get(url, params=None):
    full = url + ("?" + urllib.parse.urlencode(params) if params else "")
    p = CACHE / (urllib.parse.quote(full.split("//", 1)[1], safe="")[:180] + ".json")
    if p.exists():
        return 200, json.loads(p.read_text(encoding="utf-8")), full
    try:
        with urllib.request.urlopen(urllib.request.Request(full, headers=HDR), timeout=60) as r:
            body = r.read().decode("utf-8", "replace")
            st = r.status
    except urllib.error.HTTPError as e:
        return e.code, (e.read() or b"")[:300].decode("utf-8", "replace"), full
    except Exception as e:
        return None, str(e), full
    time.sleep(0.4)
    try:
        js = json.loads(body)
    except json.JSONDecodeError:
        return st, body[:300], full
    p.write_text(json.dumps(js, ensure_ascii=False), encoding="utf-8")
    return st, js, full


def shape(js, depth=0, maxd=3):
    if depth > maxd:
        return "…"
    if isinstance(js, dict):
        return "{" + ", ".join(f"{k}: {shape(v, depth + 1, maxd)}" for k, v in list(js.items())[:14]) + "}"
    if isinstance(js, list):
        return f"[{len(js)} × {shape(js[0], depth + 1, maxd) if js else ''}]"
    s = str(js)
    return repr(s[:40])


def first_list(js):
    if isinstance(js, list):
        return js
    if isinstance(js, dict):
        for k in ("data", "items", "result", "list", "regions", "communities"):
            if isinstance(js.get(k), list):
                return js[k]
        for v in js.values():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                return v
    return []


def probe():
    api, regions = None, []
    for b in BASES:
        for k in KINDS:
            url = f"{b}/{k}_region" if k else f"{b}/region"
            st, js, full = get(url)
            ok = st == 200 and not isinstance(js, str)
            print(f"{st}  {full}" + (f"   -> {shape(js, maxd=2)[:220]}" if ok else f"   {str(js)[:120]}"))
            if ok and first_list(js):
                api, regions = b, first_list(js)
                break
        if api:
            break
    if not api:
        sys.exit("no region list found — paste the lines above")
    print(f"\nAPI base: {api}   regions: {len(regions)}")
    print("region record:", json.dumps(regions[0], ensure_ascii=False)[:500])
    rid = regions[0].get("id")

    for label, url, params in [
        ("community list", f"{api}/community", {"region_id": rid, "refreshToken": ""}),
        ("community list (no token)", f"{api}/community", {"region_id": rid}),
        ("region page", f"{api}/region/{rid}", None),
        ("region page by slug", f"{api}/region/{regions[0].get('slug', rid)}", None),
    ]:
        st, js, full = get(url, params)
        print(f"\n[{label}] {st}  {full}")
        if st == 200 and not isinstance(js, str):
            print("  shape:", shape(js, maxd=3)[:600])
            lst = first_list(js)
            if lst:
                print("  first record:", json.dumps(lst[0], ensure_ascii=False)[:700])
        else:
            print("  ", str(js)[:200])

    st, js, full = get(f"{api}/community", {"region_id": rid, "refreshToken": ""})
    lst = first_list(js) if st == 200 else []
    if lst:
        cid = lst[0].get("id") or lst[0].get("slug")
        st, js, full = get(f"{api}/community/{urllib.parse.quote(str(cid))}", {"refreshToken": ""})
        print(f"\n[community item] {st}  {full}")
        print("  shape:", shape(js, maxd=4)[:1200] if st == 200 else str(js)[:200])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["probe"])
    ap.parse_args()
    probe()


if __name__ == "__main__":
    main()
