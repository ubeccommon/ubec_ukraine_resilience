#!/usr/bin/env python3
"""
15_digital_probe.py — locate the data behind the Digital Transformation Index of hromadas
(Mintsyfra, platform "Дія.Цифрова громада", https://hromada.gov.ua/index; 1,265 hromadas in Q2 2025)

  python 15_digital_probe.py

Fetches the index page, embedded JSON (e.g. __NEXT_DATA__ / __NUXT__), and the JavaScript
bundles it loads; lists API-looking URLs and JSON keys so that the extractor can target the
real endpoint. Stores everything under raw/digital/. No personal data involved.
"""
import hashlib
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent
RAW = BASE / "raw" / "digital"
RAW.mkdir(parents=True, exist_ok=True)
SEEDS = ["https://hromada.gov.ua/index", "https://hromada.gov.ua/"]
HDR = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
       "Accept-Language": "uk-UA,uk;q=0.9"}
API_RE = re.compile(r"""["'`](https?://[^"'`\s]{4,200}|/api/[^"'`\s]{1,200}|/v\d/[^"'`\s]{1,200})["'`]""")
KEY_RE = re.compile(r"index|rating|indeks|hromad|community|communit|score|region|measure|вимір", re.I)


def get(url):
    p = RAW / (hashlib.sha1(url.encode()).hexdigest()[:12] + "_" + re.sub(r"\W+", "_", url)[-60:])
    if p.exists():
        return p.read_bytes()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=HDR), timeout=60) as r:
            b = r.read()
            print(f"GET {url} -> {r.status} {r.headers.get('Content-Type', '')} {len(b):,} B")
    except urllib.error.HTTPError as e:
        print(f"GET {url} -> HTTP {e.code}")
        return b""
    except Exception as e:
        print(f"GET {url} -> {e}")
        return b""
    p.write_bytes(b)
    return b


def walk_keys(o, prefix="", out=None, depth=0):
    out = out if out is not None else []
    if depth > 6:
        return out
    if isinstance(o, dict):
        for k, v in o.items():
            path = f"{prefix}.{k}"
            out.append((path, type(v).__name__, len(v) if isinstance(v, (list, dict)) else ""))
            walk_keys(v, path, out, depth + 1)
    elif isinstance(o, list) and o:
        walk_keys(o[0], prefix + "[0]", out, depth + 1)
    return out


def main():
    endpoints, scripts = set(), set()
    for seed in SEEDS:
        html = get(seed).decode("utf-8", "replace")
        if not html:
            continue
        for m in re.finditer(r"<script[^>]+src=[\"']([^\"']+)[\"']", html):
            scripts.add(urllib.parse.urljoin(seed, m.group(1)))
        for tag in ("__NEXT_DATA__", "__NUXT_DATA__"):
            m = re.search(rf'<script[^>]*id="{tag}"[^>]*>(.*?)</script>', html, re.S)
            if m:
                try:
                    js = json.loads(m.group(1))
                    keys = [k for k in walk_keys(js) if KEY_RE.search(k[0])]
                    print(f"\n{tag} on {seed}: {len(m.group(1)):,} chars; matching keys:")
                    for k in keys[:40]:
                        print(f"   {k[0][:110]}  {k[1]} {k[2]}")
                except Exception as e:
                    print(f"{tag}: not JSON ({e})")
        endpoints |= {u for u in API_RE.findall(html)}
    print(f"\nscripts referenced: {len(scripts)}")
    for s in sorted(scripts)[:40]:
        b = get(s).decode("utf-8", "replace")
        endpoints |= {u for u in API_RE.findall(b)}
    hits = sorted(u for u in endpoints if KEY_RE.search(u) or "/api" in u)
    print(f"\nAPI-looking URLs ({len(hits)} of {len(endpoints)} found):")
    for u in hits[:80]:
        print("  ", u)
    (RAW / "endpoints.txt").write_text("\n".join(sorted(endpoints)), encoding="utf-8")
    print(f"\nall {len(endpoints)} URLs -> raw/digital/endpoints.txt")


if __name__ == "__main__":
    main()
