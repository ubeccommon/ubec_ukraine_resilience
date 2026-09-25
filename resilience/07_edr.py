#!/usr/bin/env python3
"""
07_edr.py — Unified State Register (ЄДР) aggregates per hromada — step 1: probe

  python 07_edr.py probe [--records 30000]

Downloads ONLY the legal-entity resource (UO.zip) and its schema (UO_schema.zip) from
data.gov.ua dataset 03cc1239-3988-4451-aa0d-aadb77448714 (Ministry of Justice, CC BY).
The FOP (sole proprietor) resource is personal data and is never downloaded.
Prints the XSD element tree, archive members, and tag statistics for the first N records.
Privacy: example values only for address/date/code/legal-form/status tags; names, heads,
founders and beneficiaries are never printed or stored.
"""
import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import zipfile
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent
RAW = BASE / "raw" / "edr"
LOGS = BASE / "logs"
for d in (RAW, LOGS):
    d.mkdir(parents=True, exist_ok=True)
CKAN = "https://data.gov.ua/api/3/action/"
DATASET = "03cc1239-3988-4451-aa0d-aadb77448714"
HDR = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"}
SAFE = re.compile(r"ADDRESS|ADDR|ATO|ATU|KOATUU|KATOT|DATE|OPF|STAN|STATE|KVED|REGIST|TERMIN|"
                  r"ZIP|INDEX|REGION|CODE|EDRPOU|STATUS", re.I)
UNSAFE = re.compile(r"NAME|BOSS|FOUNDER|BENEF|PERSON|SIGNER|HEAD|MEMBER|EXECUT|FIO|PIB|"
                    r"CONTACT|PHONE|TEL|EMAIL|PASSPORT|BIRTH|RNOKPP|IPN|CITIZEN", re.I)
_logf = open(LOGS / "07_edr_probe.log", "w", encoding="utf-8")


def log(*a):
    m = " ".join(str(x) for x in a)
    print(m, flush=True)
    _logf.write(m + "\n")
    _logf.flush()


def api(action, **params):
    url = CKAN + action + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(urllib.request.Request(url, headers=HDR), timeout=120) as r:
        return json.loads(r.read())["result"]


def download(url, dest):
    if re.search(r"fop", url, re.I):
        sys.exit("refusing to download the FOP resource (personal data)")
    if dest.exists() and dest.stat().st_size > 0:
        log(f"cached {dest.name} {dest.stat().st_size/1e6:.1f} MB")
        return dest
    tmp = dest.with_suffix(dest.suffix + ".part")
    have = tmp.stat().st_size if tmp.exists() else 0
    h = dict(HDR)
    if have:
        h["Range"] = f"bytes={have}-"
    t0, last = time.time(), 0
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=600) as r:
        mode = "ab" if have and r.status == 206 else "wb"
        got = have if mode == "ab" else 0
        with open(tmp, mode) as f:
            while chunk := r.read(1 << 20):
                f.write(chunk)
                got += len(chunk)
                if got - last >= 100 << 20:
                    last = got
                    log(f"  {got/1e6:.0f} MB  {got/1e6/max(time.time()-t0, 1):.1f} MB/s")
    tmp.rename(dest)
    log(f"downloaded {dest.name} {dest.stat().st_size/1e6:.1f} MB")
    return dest


def print_schema(zpath):
    from lxml import etree
    with zipfile.ZipFile(zpath) as z:
        xsds = [m for m in z.namelist() if m.lower().endswith(".xsd")]
        log(f"\nschema members: {z.namelist()}")
        for m in xsds:
            doc = etree.parse(z.open(m))
            log(f"\n--- {m}")
            ns = {"xs": "http://www.w3.org/2001/XMLSchema"}
            for el in doc.iter("{http://www.w3.org/2001/XMLSchema}element"):
                name = el.get("name") or el.get("ref")
                if not name:
                    continue
                depth = sum(1 for a in el.iterancestors("{http://www.w3.org/2001/XMLSchema}element"))
                docs = el.xpath("./xs:annotation/xs:documentation/text()", namespaces=ns)
                txt = " ".join(t.strip() for t in docs)[:110]
                log(f"  {'  ' * depth}{name}  {txt}")


def find_uo(z, prefix=""):
    for m in z.infolist():
        n = m.filename
        log(f"  member {prefix}{n}  {m.file_size/1e9:.2f} GB")
        if n.lower().endswith(".zip"):
            yield from find_uo(zipfile.ZipFile(z.open(m)), prefix + n + "/")
        elif n.lower().endswith(".xml") and not re.search(r"FOP|ФОП", n, re.I):
            yield prefix + n, (lambda zz=z, mm=m: zz.open(mm))


def probe_xml(label, opener, nrec):
    from lxml import etree
    paths, examples, values = Counter(), {}, {}
    depth, n, root_tag, rec_tag = 0, 0, None, None
    with opener() as fh:
        for ev, el in etree.iterparse(fh, events=("start", "end"), recover=True, huge_tree=True):
            if ev == "start":
                depth += 1
                if depth == 1:
                    root_tag = el.tag
                continue
            if depth == 2:
                rec_tag = el.tag
                n += 1
                seen = set()
                for sub in el.iter():
                    if sub is el:
                        continue
                    p, a = [], sub
                    while a is not None and a is not el:
                        p.append(a.tag)
                        a = a.getparent()
                    path = "/".join(reversed(p))
                    if path in seen:
                        continue
                    seen.add(path)
                    paths[path] += 1
                    txt = (sub.text or "").strip()
                    if txt and SAFE.search(path) and not UNSAFE.search(path):
                        examples.setdefault(path, txt[:70])
                        if re.search(r"STAN|STATE|STATUS|OPF", path, re.I) and len(txt) < 120:
                            values.setdefault(path, Counter())[txt] += 1
                el.clear()
                while el.getprevious() is not None:
                    del el.getparent()[0]
                if n >= nrec:
                    break
            depth -= 1
    log(f"\n{label}: root <{root_tag}> record <{rec_tag}>  records read {n:,}")
    log("tag paths (share of records containing it; example only for safe tags):")
    for p, k in sorted(paths.items(), key=lambda x: (-x[1], x[0])):
        log(f"  {k/max(n,1):6.1%}  {p:60s} {examples.get(p, '')}")
    for p, cnt in values.items():
        log(f"\nvalues of {p} (top 15):")
        for v, k in cnt.most_common(15):
            log(f"  {k:7,}  {v}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["probe"])
    ap.add_argument("--records", type=int, default=30000)
    a = ap.parse_args()

    pkg = api("package_show", id=DATASET)
    log(f"dataset: {pkg['title']}\nlicence: {pkg.get('license_title')}")
    rs = {r.get("name", ""): r for r in pkg.get("resources", [])}
    for nm, r in rs.items():
        log(f"  {str(r.get('last_modified') or r.get('created'))[:19]}  {nm:16s} {(r.get('size') or 0)/1e6:8.1f} MB")
    uo = next((r for nm, r in rs.items() if re.fullmatch(r"UO\.zip", nm, re.I)), None)
    sch = next((r for nm, r in rs.items() if re.fullmatch(r"UO_schema\.zip", nm, re.I)), None)
    if uo is None:
        sys.exit("UO.zip resource not found — paste the list above")
    if sch is not None:
        print_schema(download(sch["url"], RAW / "uo_schema.zip"))
    dest = download(uo["url"], RAW / "uo.zip")
    with zipfile.ZipFile(dest) as z:
        log("\narchive members:")
        found = list(find_uo(z))
        if not found:
            sys.exit("no XML member found — see member list above")
        label, opener = found[0]
        probe_xml(label, opener, a.records)


if __name__ == "__main__":
    main()
