#!/usr/bin/env python3
"""
33_elections_2020.py — local elections of 25 October 2020 per hromada (k3): electoral competition.
Rights-sphere inputs (resilience/docs/threefolding_framework.md, section 6, step 4a).

  python 33_elections_2020.py probe      # download, structure report, counts, match to k3
  python 33_elections_2020.py build      # -> tidy/elections_2020_k3.csv (from the saved counts)

Source: Central Election Commission, IAS "Місцеві вибори 2020", election id 695, open data
  opendata_kandpt001f01=695.xml (windows-1251, ~150 MB): region > rada > candidate lists.
  Reuse with attribution ("посилання на джерело обов'язкове"); the data.gov.ua copy is CC BY.
  The file names every candidate with a biography. It is downloaded to a temporary file (resumable),
  parsed, and deleted in all cases. Only counts per council are kept (rule R6): nothing that
  identifies a person is printed or written.

Turnout is not available: the CEC publishes no structured turnout for local elections (territorial
commissions hold it); the protocol PDFs cannot be linked to the open-data council ids (probe of
27 Sep 2026: 29 of 29 returned 404) and are partly handwritten scans. Decided: not feasible.

probe   writes raw/cvk/councils_695.csv (council id, name, oblast, candidate counts per list type,
        number of party lists) and reports the XML structure: all element names with counts, and
        the element tree of one council of each type (tags and child counts only, no text).
build   n_head_candidates  candidates for hromada head (HEAD_TAGS)
        n_council_lists    party lists (and self-nomination groups) standing for the council
        -> tidy/elections_2020_k3.csv. Hromadas without elections in 2020 stay empty.
"""
import argparse
import re
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent
TIDY, LOGS = BASE / "tidy", BASE / "logs"
RAW = BASE / "raw" / "cvk"
COUNCILS = RAW / "councils_695.csv"       # counts only, no personal data
OUT = TIDY / "elections_2020_k3.csv"
CAND_XML = "https://cvk.gov.ua/pls/vm2020/opendata_kandpt001f01=695.xml"
HDR = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"}
TEST_K3 = "2602003"
HEAD_TAGS = {"candidates_for_mayor"}      # wrapper(s) of head candidates; confirm with probe
LIST_TAG = "part"                         # a party list inside the deputies wrapper
# renamed since 2020 (council name 2020 stem -> name stem in keys_hromada)
RENAMED = {"берестинська": "красноградська", "багачевська": "ватутінська",
           "хутірмихайлівська": "дружбівська", "шахтарська": "першотравенська"}  # Шахтарське (Дніпропетровська), 2024
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


def tag(el):
    return el.tag.split("}")[-1]


# ------------------------------------------------------------ download
def download_resumable(url, dest, tries=10):
    """HTTP download with Range resume; returns bytes written."""
    total = None
    for att in range(1, tries + 1):
        have = dest.stat().st_size if dest.exists() else 0
        h = dict(HDR, **({"Range": f"bytes={have}-"} if have else {}))
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=600) as r:
                if have and r.status != 206:
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
            got = dest.stat().st_size / 1e6 if dest.exists() else 0
            log(f"  attempt {att}: {type(e).__name__} at {got:.1f} MB — resuming")
            time.sleep(5 * att)
            continue
        size = dest.stat().st_size
        if total is None or size >= total:
            return size
        log(f"  attempt {att}: {size / 1e6:.1f} of {total / 1e6:.1f} MB — resuming")
    raise SystemExit(f"download incomplete after {tries} attempts: {url}")


# ------------------------------------------------------------ structure
def tree(el, depth=0, maxdepth=4, out=None):
    """Element tree as tag names with repeat counts; no text, attribute names only."""
    out = [] if out is None else out
    kids = {}
    for c in el:
        kids.setdefault(tag(c), []).append(c)
    attrs = ",".join(sorted(el.attrib)) if el.attrib else ""
    out.append("    " + "  " * depth + tag(el) + (f" [{attrs}]" if attrs else ""))
    if depth < maxdepth:
        for t, cs in kids.items():
            if len(cs) > 1:
                out.append("    " + "  " * (depth + 1) + f"({len(cs)} × {t})")
            tree(cs[0], depth + 1, maxdepth, out)
    return out


def council_type(name):
    n = str(name).lower()
    for t in ("обласна", "районна", "міська", "селищна", "сільська"):
        if t in n:
            return t
    return "other"


def parse_councils():
    RAW.mkdir(parents=True, exist_ok=True)
    tmp = RAW / "_cand_695.xml.part"
    log(f"downloading {CAND_XML} (temporary; contains personal data; deleted after parsing)")
    rows, region, tags, shown = [], None, {}, set()
    try:
        tmp.unlink(missing_ok=True)
        log(f"  {download_resumable(CAND_XML, tmp) / 1e6:.1f} MB received")
        for ev, el in ET.iterparse(str(tmp), events=("start", "end")):
            t = tag(el)
            if ev == "start":
                tags[t] = tags.get(t, 0) + 1
                if t == "region":
                    region = el.get("name")
                continue
            if t != "rada":
                continue
            rec = {"rada_id": el.get("id"), "rada_name": el.get("name"), "oblast": region,
                   "council_type": council_type(el.get("name"))}
            for child in el:                   # candidates under each list type of this council
                ct = tag(child)
                rec[f"n_cand__{ct}"] = sum(1 for d in child.iter() if tag(d) == "candidate")
                rec[f"n_{LIST_TAG}__{ct}"] = sum(1 for d in child.iter() if tag(d) == LIST_TAG)
            ctype = rec["council_type"]
            if ctype not in shown:
                shown.add(ctype)
                log(f"\n  structure, first {ctype} council (tags only):")
                log("\n".join(tree(el)))
            rows.append(rec)
            el.clear()
    finally:
        tmp.unlink(missing_ok=True)
        log("\n  temporary XML deleted")
    log("  element counts: " + ", ".join(f"{k}={v}" for k, v in sorted(tags.items(), key=lambda x: -x[1])))
    df = pd.DataFrame(rows)
    df.to_csv(COUNCILS, index=False)
    log(f"  councils={len(df)} -> {COUNCILS}")
    return df


# ------------------------------------------------------------ matching
def norm_oblast(s):
    s = str(s).lower().replace("м.", "").strip()
    return re.sub(r"\s+", " ", s)


def stem_type(s):
    s = str(s).lower().replace("’", "'").replace("ʼ", "'")
    typ = "m" if re.search(r"\bміськ", s) else "s" if re.search(r"\bселищн", s) else \
          "v" if re.search(r"\bсільськ", s) else "?"
    s = re.sub(r"['`\"]", "", s)
    s = re.sub(r"\b(міська|міської|селищна|селищної|сільська|сільської|територіальна|територіальної|"
               r"громада|громади|рада|ради|обєднана)\b", "", s)
    s = re.sub(r"[^0-9a-zа-яіїєґ]+", "", s)
    return RENAMED.get(s, s), typ


def match_k3(c):
    keys = pd.read_csv(TIDY / "keys_hromada.csv", dtype=str)
    keys["ob"] = keys["oblast_uk"].map(norm_oblast)
    st = keys["name"].map(stem_type)
    keys["stem"], keys["typ"] = st.str[0], st.str[1]
    keys["key"] = keys["ob"] + "#" + keys["stem"] + "|" + keys["typ"]
    kk = keys.drop_duplicates("key", keep=False).set_index("key")["k3"]

    c = c[c["council_type"].isin(["міська", "селищна", "сільська"])].copy()
    c["ob"] = c["oblast"].map(norm_oblast)
    st = c["rada_name"].map(stem_type)
    c["stem"], c["typ"] = st.str[0], st.str[1]
    c["k3"] = (c["ob"] + "#" + c["stem"] + "|" + c["typ"]).map(kk)
    c["match"] = c["k3"].notna().map({True: "name", False: None})

    # special-status city: one council, one key
    kyiv = c["ob"].eq("київ") & c["k3"].isna()
    c.loc[kyiv, ["k3", "match"]] = ["8000000", "city"]
    # keys named after the centre settlement (Обухів, Комарно, Тернівка, …): prefix match, unique
    cen = keys[keys["name_src"] == "centre settlement"]
    for i in c.index[c["k3"].isna()]:
        ob, stem = c.at[i, "ob"], c.at[i, "stem"]
        cand = cen[(cen["ob"] == ob) & cen["name"].map(
            lambda n: len(stem_type(n)[0]) >= 4 and stem.startswith(stem_type(n)[0][:-2]))]
        if len(cand) == 1:
            c.at[i, "k3"], c.at[i, "match"] = cand["k3"].iloc[0], "centre"
    dup = c["k3"].duplicated(keep=False) & c["k3"].notna()
    c.loc[dup, ["k3", "match"]] = [None, None]
    log(f"  hromada councils: {len(c)}  matched to k3: {c['k3'].notna().sum()} "
        f"({c['match'].value_counts().to_dict()}); ambiguous dropped: {int(dup.sum())}")
    miss = c[c["k3"].isna()]
    if len(miss):
        log("  unmatched (first 25): " + "; ".join(f"{r.oblast[:12]}|{r.rada_name}" for r in miss.head(25).itertuples()))
    return c


def load_councils():
    if not COUNCILS.exists():
        raise SystemExit("run 'probe' first")
    return pd.read_csv(COUNCILS, dtype={"rada_id": str})


# ---------------------------------------------------------------- modes
def cmd_probe(a):
    open_log("33_probe.log")
    c = parse_councils()
    cand = [x for x in c.columns if x.startswith("n_cand__")]
    lists = [x for x in c.columns if x.startswith(f"n_{LIST_TAG}__")]
    log("\n  candidates per council by list type and council type (median / councils with >0):")
    for t, g in c.groupby("council_type"):
        parts = [f"{x[8:]}: {g[x].median():.0f}/{int((g[x] > 0).sum())}" for x in cand if g[x].notna().any()]
        log(f"    {t:8s} n={len(g):4d}  " + "  ".join(parts))
    log("  party lists per council by wrapper and council type (median / councils with >0):")
    for t, g in c.groupby("council_type"):
        parts = [f"{x[len(LIST_TAG) + 4:]}: {g[x].median():.0f}/{int((g[x] > 0).sum())}"
                 for x in lists if g[x].notna().any() and g[x].sum() > 0]
        log(f"    {t:8s} " + "  ".join(parts))
    m = match_k3(c)
    vk = m[m["k3"] == TEST_K3]
    if len(vk):
        log("\n  Verkhovyna 2602003:\n" + vk[["rada_id", "rada_name"] + cand + lists].T.to_string(header=False))


def cmd_build(a):
    open_log("33_build.log")
    c = match_k3(load_councils())
    c = c[c["k3"].notna()].copy()
    head = [f"n_cand__{t}" for t in HEAD_TAGS if f"n_cand__{t}" in c.columns]
    if not head:
        raise SystemExit(f"none of HEAD_TAGS {HEAD_TAGS} in the counts; check the probe")
    c["n_head_candidates"] = c[head].sum(axis=1, min_count=1)
    lists = [x for x in c.columns if x.startswith(f"n_{LIST_TAG}__") and x[len(LIST_TAG) + 4:] not in HEAD_TAGS]
    c["n_council_lists"] = c[lists].sum(axis=1, min_count=1)
    keys = pd.read_csv(TIDY / "keys_hromada.csv", dtype=str)[["k1", "k2", "k3", "name"]]
    out = keys.merge(c[["k3", "rada_id", "n_head_candidates", "n_council_lists"]], on="k3", how="inner")
    out = out.sort_values("k3")
    out.to_csv(OUT, index=False)
    log(f"wrote {OUT.name} rows={len(out)}")
    for x in ("n_head_candidates", "n_council_lists"):
        log(f"  {x}: " + str(out[x].describe().round(1).to_dict()))

    src = "Central Election Commission (cvk.gov.ua), IAS Місцеві вибори 2020, election 695, opendata_kand XML"
    lic = "open data, attribution required (data.gov.ua copy CC BY)"
    dd_new = pd.DataFrame([
        ["n_head_candidates", src, lic, "count", "2020", "hromada",
         "registered candidates for hromada head, 25 Oct 2020; counts only, names not stored"],
        ["n_council_lists", src, lic, "count", "2020", "hromada",
         "candidate lists (parties, local organisations) standing for the hromada council, 25 Oct 2020"],
    ], columns=["indicator", "source", "licence", "unit", "year", "level", "method"])
    ddp = TIDY / "data_dictionary.csv"
    dd = pd.read_csv(ddp, dtype=str) if ddp.exists() else pd.DataFrame(columns=dd_new.columns)
    drop = set(dd_new["indicator"]) | {"turnout", "protocol_status"}
    dd = pd.concat([dd[~dd["indicator"].isin(drop)], dd_new], ignore_index=True)
    dd.to_csv(ddp, index=False)
    log(f"data dictionary updated: {len(dd)} indicators")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("mode", choices=["probe", "build"])
    a = ap.parse_args()
    {"probe": cmd_probe, "build": cmd_build}[a.mode](a)


if __name__ == "__main__":
    main()
