#!/usr/bin/env python3
"""
33_elections_2020.py — local elections of 25 October 2020 per hromada (k3): turnout in the election
of the hromada head and the number of candidates for head. Rights-sphere inputs
(resilience/docs/threefolding_framework.md, section 6, step 4a).

  python 33_elections_2020.py probe [--n 30]
  python 33_elections_2020.py pull  [--workers 2]
  python 33_elections_2020.py build

Sources (Central Election Commission, cvk.gov.ua, IAS "Місцеві вибори 2020", election id 695;
reuse with attribution — "посилання на джерело обов'язкове"; the data.gov.ua copy is CC BY):
  candidates   opendata_kandpt001f01=695.xml (windows-1251): region > rada > candidates_for_mayor.
               Structured, all councils, ~150 MB. Contains names and biographies: downloaded to a
               temporary file (resumable), parsed, and deleted in all cases; only council id,
               council name, oblast and the count of head candidates are kept (rule R6).
  protocols    TVK protocol on the results of the head election, one PDF per council:
               showpprotpt001f01=695pid102=<rada id>pt004f01=0pid494=3pasatt=1.pdf
               The CEC does not publish turnout as structured data for local elections. Protocols
               are partly text PDFs, partly handwritten scans; only text PDFs are parsed
               (pdftotext); scans are recorded as 'scan' and left empty — no OCR, no guessing.
               PDFs are cached in raw/cvk/protocols/ (not tracked: they name candidates and
               commission members). Only the numbers are kept.

probe   streams the candidate XML: councils with head elections, match to k3 (oblast + name + type),
        then fetches --n protocols (Verkhovyna first) and reports how many have a text layer, the
        label lines found and the values parsed. Decide from this whether turnout is feasible.
pull    all matched councils' protocols; resume from cache; failures logged, rerun to retry.
build   -> tidy/elections_2020_k3.csv: k3, rada_id, n_head_candidates, voters_list, voters_voted,
        turnout, protocol_status. Hromadas without elections in 2020 stay empty.

Turnout = voters who took part in the vote / voters on the lists, first round, whole hromada.
"""
import argparse
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent
TIDY, LOGS = BASE / "tidy", BASE / "logs"
RAW = BASE / "raw" / "cvk"
PROT = RAW / "protocols"
COUNCILS = RAW / "councils_695.csv"       # derived: id, name, oblast, n_head_candidates (no names)
OUT = TIDY / "elections_2020_k3.csv"
ELECTION = 695
CVK = "https://cvk.gov.ua/pls/vm2020/"
CAND_XML = CVK + f"opendata_kandpt001f01={ELECTION}.xml"
PROT_URL = CVK + "showpprotpt001f01={e}pid102={rid}pt004f01=0pid494=3pasatt=1.pdf"
HDR = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"}
TEST_K3 = "2602003"
_logf = None

# protocol labels (Ukrainian form); value = first integer after the label
LABELS = {
    "voters_list": r"внесених\s+до\s+спис\w*\s+виборців",
    "voters_ballots": r"отримали\s+виборч\w*\s+бюлетен\w*",
    "voters_voted": r"(?:взяли|брали)\s+участь\s+у\s+голосуванні",
}
NUM = re.compile(r"(?<![\d.])(\d{1,3}(?:[  ]\d{3})+|\d+)(?![\d.])")


def log(*a):
    m = " ".join(str(x) for x in a)
    print(m, flush=True)
    if _logf:
        _logf.write(m + "\n")
        _logf.flush()


def open_log(name, mode="w"):
    global _logf
    LOGS.mkdir(exist_ok=True)
    _logf = open(LOGS / name, mode, encoding="utf-8")


def get(url, timeout=180):
    req = urllib.request.Request(url, headers=HDR)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, b""
    except Exception as e:
        return None, str(e).encode()


# ------------------------------------------------------------- councils
def download_resumable(url, dest, tries=10):
    """HTTP download with Range resume; returns bytes written. Raises on failure."""
    total = None
    for att in range(1, tries + 1):
        have = dest.stat().st_size if dest.exists() else 0
        h = dict(HDR, **({"Range": f"bytes={have}-"} if have else {}))
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=600) as r:
                if have and r.status != 206:          # server ignored Range: start again
                    have = 0
                    dest.unlink(missing_ok=True)
                cl = r.headers.get("Content-Length")
                if cl is not None:
                    total = have + int(cl)
                with open(dest, "ab") as f:
                    while True:
                        chunk = r.read(1 << 20)
                        if not chunk:
                            break
                        f.write(chunk)
        except Exception as e:
            log(f"  attempt {att}: {type(e).__name__} at {dest.stat().st_size / 1e6 if dest.exists() else 0:.1f} MB — resuming")
            time.sleep(5 * att)
            continue
        size = dest.stat().st_size
        if total is None or size >= total:
            return size
        log(f"  attempt {att}: {size / 1e6:.1f} of {total / 1e6:.1f} MB — resuming")
    raise SystemExit(f"download incomplete after {tries} attempts: {url}")


def stream_councils():
    """Download the candidate XML to a temporary file, parse it, delete it; keep counts only."""
    RAW.mkdir(parents=True, exist_ok=True)
    tmp = RAW / "_cand_695.xml.part"
    log(f"downloading {CAND_XML} (temporary; contains personal data; deleted after parsing)")
    rows, region, tags = [], None, {}
    try:
        tmp.unlink(missing_ok=True)
        size = download_resumable(CAND_XML, tmp)
        log(f"  {size / 1e6:.1f} MB received")
        for ev, el in ET.iterparse(str(tmp), events=("start", "end")):
            tag = el.tag.split("}")[-1]
            if ev == "start":
                tags[tag] = tags.get(tag, 0) + 1
                if tag == "region":
                    region = el.get("name")
                continue
            if tag == "rada":
                mayor = [c for c in el.iter() if c.tag.split("}")[-1] == "candidates_for_mayor"]
                n = sum(1 for m in mayor for c in m if len(c) or (c.text or "").strip())
                rows.append({"rada_id": el.get("id"), "rada_name": el.get("name"), "oblast": region,
                             "has_head_election": bool(mayor), "n_head_candidates": n if mayor else None})
                el.clear()
    finally:
        tmp.unlink(missing_ok=True)
        log("  temporary XML deleted")
    log("  element counts: " + ", ".join(f"{k}={v}" for k, v in sorted(tags.items(), key=lambda x: -x[1])[:12]))
    df = pd.DataFrame(rows)
    RAW.mkdir(parents=True, exist_ok=True)
    df.to_csv(COUNCILS, index=False)
    log(f"  councils={len(df)}  with head election={int(df['has_head_election'].sum())}  -> {COUNCILS}")
    return df


def norm(s):
    s = str(s).lower().replace("’", "'").replace("ʼ", "'")
    s = re.sub(r"['`\"]", "", s)
    typ = "m" if re.search(r"\bміськ", s) else "s" if re.search(r"\bселищн", s) else \
          "v" if re.search(r"\bсільськ", s) else "?"
    s = re.sub(r"\b(міська|міської|селищна|селищної|сільська|сільської|територіальна|територіальної|"
               r"громада|громади|рада|ради|об'єднана)\b", "", s)
    return re.sub(r"[^0-9a-zа-яіїєґ]+", "", s) + "|" + typ


def match_k3(c):
    keys = pd.read_csv(TIDY / "keys_hromada.csv", dtype=str)
    keys["key"] = keys["oblast_uk"].str.lower().str.strip() + "#" + keys["name"].map(norm)
    kk = keys.drop_duplicates("key", keep=False).set_index("key")["k3"]
    c = c[c["has_head_election"]].copy()
    c["key"] = c["oblast"].str.lower().str.strip() + "#" + c["rada_name"].map(norm)
    c["k3"] = c["key"].map(kk)
    dup = c["k3"].duplicated(keep=False) & c["k3"].notna()
    c.loc[dup, "k3"] = None
    log(f"  matched to k3: {c['k3'].notna().sum()} / {len(c)} councils with a head election "
        f"(ambiguous dropped: {int(dup.sum())})")
    miss = c[c["k3"].isna()]
    if len(miss):
        log("  unmatched (first 15): " + "; ".join(f"{r.oblast[:12]}|{r.rada_name}" for r in miss.head(15).itertuples()))
    return c


def load_councils(refresh=False):
    c = stream_councils() if refresh or not COUNCILS.exists() else pd.read_csv(COUNCILS, dtype={"rada_id": str})
    c["has_head_election"] = c["has_head_election"].astype(str).str.lower() == "true"
    return match_k3(c)


# ------------------------------------------------------------ protocols
def prot_path(rid):
    return PROT / f"{rid}.pdf"


def fetch_protocol(rid, pause=1.0):
    p = prot_path(rid)
    if p.exists() and p.stat().st_size > 0:
        return "cached"
    PROT.mkdir(parents=True, exist_ok=True)
    for att in range(3):
        st, body = get(PROT_URL.format(e=ELECTION, rid=rid))
        if st == 200 and body[:4] == b"%PDF":
            p.write_bytes(body)
            time.sleep(pause)
            return "ok"
        if st == 200:
            return "fail:not pdf " + repr(body[:80])
        time.sleep({429: 20, 403: 60}.get(st, 5))
    return f"fail:HTTP {st}"


def pdf_text(p):
    try:
        r = subprocess.run(["pdftotext", "-layout", str(p), "-"], capture_output=True, timeout=120)
        return r.stdout.decode("utf-8", errors="replace")
    except FileNotFoundError:
        sys.exit("pdftotext not found: install poppler-utils")


def parse_protocol(txt):
    """-> dict of values and status. 'scan' when there is no usable text layer."""
    flat = re.sub(r"\s+", " ", txt)
    if len(re.findall(r"[а-яіїєґ]{4,}", flat.lower())) < 30:
        return {"protocol_status": "scan"}
    out, ctx = {}, {}
    for k, pat in LABELS.items():
        m = re.search(pat, flat, flags=re.I)
        if not m:
            continue
        tail = flat[m.end(): m.end() + 250]
        tail = re.sub(r"\(\s*[^)]*\)", " ", tail)          # drop "(прописом)"
        n = NUM.search(tail)
        ctx[k] = flat[m.start(): m.end() + 80]
        if n:
            out[k] = int(re.sub(r"\D", "", n.group(1)))
    ok = "voters_list" in out and "voters_voted" in out and 0 < out["voters_voted"] <= out["voters_list"]
    out["protocol_status"] = "text" if ok else "text_unparsed"
    out["_ctx"] = ctx
    return out


# ---------------------------------------------------------------- modes
def cmd_probe(a):
    open_log("33_probe.log")
    c = load_councils(refresh=True)
    log("  head candidates per council: " + str(c["n_head_candidates"].describe().round(1).to_dict()))
    m = c[c["k3"].notna()]
    pick = pd.concat([m[m["k3"] == TEST_K3], m[m["k3"] != TEST_K3].sample(min(a.n - 1, len(m) - 1), random_state=1)])
    log(f"\nprotocol test on {len(pick)} councils:")
    stat = {}
    for r in pick.itertuples():
        st = fetch_protocol(r.rada_id)
        if st.startswith("fail"):
            log(f"  {r.k3} {r.rada_name}: {st}")
            stat["fail"] = stat.get("fail", 0) + 1
            continue
        res = parse_protocol(pdf_text(prot_path(r.rada_id)))
        s = res["protocol_status"]
        stat[s] = stat.get(s, 0) + 1
        vals = {k: res.get(k) for k in LABELS}
        log(f"  {r.k3} {r.rada_name[:40]:40s} {s:14s} {vals}")
        if s != "scan" and (r.k3 == TEST_K3 or s == "text_unparsed"):
            for k, v in res.get("_ctx", {}).items():
                log(f"      [{k}] …{v}…")
    log("\nsummary: " + ", ".join(f"{k}={v}" for k, v in stat.items())
        + f"   parsed share={stat.get('text', 0) / max(len(pick), 1):.2f}")


def cmd_pull(a):
    open_log("33_pull.log", "a")
    c = load_councils()
    todo = [r for r in c[c["k3"].notna()]["rada_id"] if not prot_path(r).exists()]
    log(f"{time.strftime('%F %T')} protocols: councils={c['k3'].notna().sum()} to_fetch={len(todo)}")
    fails, t0 = [], time.time()
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = {ex.submit(fetch_protocol, rid): rid for rid in todo}
        for i, f in enumerate(as_completed(futs), 1):
            st = f.result()
            if st.startswith("fail"):
                fails.append((futs[f], st))
            if i % 50 == 0 or i == len(todo):
                log(f"  {i}/{len(todo)} fails={len(fails)} {i / max(time.time() - t0, 1):.2f}/s")
    if fails:
        fp = LOGS / "33_pull_failures.csv"
        pd.DataFrame(fails, columns=["rada_id", "status"]).to_csv(fp, mode="a", header=not fp.exists(), index=False)
        log(f"{len(fails)} failures -> {fp}; rerun to retry")


def cmd_build(a):
    open_log("33_build.log")
    c = load_councils()
    c = c[c["k3"].notna()]
    recs = []
    for r in c.itertuples():
        rec = {"k3": r.k3, "rada_id": r.rada_id, "n_head_candidates": r.n_head_candidates}
        p = prot_path(r.rada_id)
        if p.exists():
            res = parse_protocol(pdf_text(p))
            rec.update({k: v for k, v in res.items() if not k.startswith("_")})
        else:
            rec["protocol_status"] = "missing"
        recs.append(rec)
    df = pd.DataFrame(recs)
    for k in LABELS:
        if k not in df:
            df[k] = None
    df["turnout"] = (df["voters_voted"] / df["voters_list"]).round(4)
    keys = pd.read_csv(TIDY / "keys_hromada.csv", dtype=str)[["k1", "k2", "k3", "name"]]
    out = keys.merge(df, on="k3", how="inner")[
        ["k1", "k2", "k3", "name", "rada_id", "n_head_candidates", "voters_list", "voters_voted",
         "turnout", "protocol_status"]].sort_values("k3")
    out.to_csv(OUT, index=False)
    log(f"wrote {OUT.name} rows={len(out)}")
    log("protocol status: " + str(out["protocol_status"].value_counts().to_dict()))
    t = out["turnout"].dropna()
    if len(t):
        log(f"turnout: n={len(t)} median={t.median():.3f} p05={t.quantile(.05):.3f} p95={t.quantile(.95):.3f}")
        by = out.assign(has=out["turnout"].notna()).groupby("k1")["has"].mean().round(2)
        log("share with turnout by oblast: " + ", ".join(f"{k}={v}" for k, v in by.items()))

    src = "Central Election Commission (cvk.gov.ua), IAS Місцеві вибори 2020, election 695"
    lic = "open data, attribution required (data.gov.ua copy CC BY)"
    dd_new = pd.DataFrame([
        ["n_head_candidates", src + ", opendata_kand XML", lic, "count", "2020", "hromada",
         "registered candidates for hromada head, 25 Oct 2020; names not stored"],
        ["turnout", src + ", TVK head-election protocols (PDF)", lic, "ratio", "2020", "hromada",
         "voters who took part / voters on the lists, first round; text PDFs only, scans left empty"],
        ["protocol_status", src, lic, "flag", "2020", "hromada",
         "text = parsed; text_unparsed; scan (no text layer, not read); missing"],
    ], columns=["indicator", "source", "licence", "unit", "year", "level", "method"])
    ddp = TIDY / "data_dictionary.csv"
    dd = pd.read_csv(ddp, dtype=str) if ddp.exists() else pd.DataFrame(columns=dd_new.columns)
    dd = pd.concat([dd[~dd["indicator"].isin(dd_new["indicator"])], dd_new], ignore_index=True)
    dd.to_csv(ddp, index=False)
    log(f"data dictionary updated: {len(dd)} indicators")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("mode", choices=["probe", "pull", "build"])
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--workers", type=int, default=2)
    a = ap.parse_args()
    {"probe": cmd_probe, "pull": cmd_pull, "build": cmd_build}[a.mode](a)


if __name__ == "__main__":
    main()
