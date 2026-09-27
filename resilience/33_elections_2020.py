#!/usr/bin/env python3
"""
33_elections_2020.py — local elections of 25 October 2020 per hromada (k3): electoral competition.
Rights-sphere input (resilience/docs/threefolding_framework.md, section 6, step 4a).

  python 33_elections_2020.py probe [--refresh]   # counts from both CEC files, structure, match
  python 33_elections_2020.py build               # -> tidy/elections_2020_k3.csv

Sources: Central Election Commission, IAS "Місцеві вибори 2020" (election id 695), open data,
reuse with attribution ("посилання на джерело обов'язкове"); the data.gov.ua copy is CC BY.
  candidates  opendata_kandpt001f01=695.xml (~150 MB): rada > candidates_for_deputies
              (> part > candidates > candidate where the council is elected by party list;
              > candidates > candidate where it is elected in multi-member districts) and, for city
              councils only, candidates_for_mayor.
  elected     opendata_obr.xml: rada > head, deputies (elected persons).
Both files name persons. Each is downloaded to a temporary file (resumable), parsed, and deleted in
all cases; only counts per council are kept (rule R6). Nothing that identifies a person is printed
or written.

Indicator: cand_per_seat = deputy candidates / deputies elected, per hromada council — contestation
of the council election. The level depends on the electoral system (probe 27 Sep 2026: median 8.5
with proportional lists, >10,000 voters; 2.9 in multi-member districts), so the index input is
cand_per_seat_rel = cand_per_seat / median of the same system. electoral_system records which.
Context only: n_head_candidates (listed for city councils only, 370 of 1,419 hromada councils).
Not feasible (probe of 27 Sep 2026): turnout — no structured source; protocol PDFs cannot be
linked to the open-data council ids (29 of 29 returned 404) and are partly handwritten scans.
"""
import argparse
import importlib
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent
TIDY, LOGS = BASE / "tidy", BASE / "logs"
RAW = BASE / "raw" / "cvk"
CAND_CSV = RAW / "councils_695.csv"       # counts only, no personal data
ELECT_CSV = RAW / "elected_695.csv"       # counts only, no personal data
OUT = TIDY / "elections_2020_k3.csv"
CVK = "https://cvk.gov.ua/pls/vm2020/"
CAND_XML = CVK + "opendata_kandpt001f01=695.xml"
ELECT_XML = CVK + "opendata_obr.xml"
HDR = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"}
TEST_K3 = "2602003"
DEP_CAND = "n_cand__candidates_for_deputies"
HEAD_CAND = "n_cand__candidates_for_mayor"
LIST_TAG = "part"
# renamed since 2020 (council-name stem 2020 -> name stem in keys_hromada)
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


# ------------------------------------------------------------ parsing
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


def count_candidates(el):
    rec = {}
    for child in el:
        ct = tag(child)
        rec[f"n_cand__{ct}"] = sum(1 for d in child.iter() if tag(d) == "candidate")
        rec[f"n_{LIST_TAG}__{ct}"] = sum(1 for d in child.iter() if tag(d) == LIST_TAG)
    return rec


def count_persons(el):
    """Elected file: persons = elements with a PIB child; counted per direct child of the council."""
    rec = {}
    for child in el:
        n = sum(1 for d in child.iter() if any(tag(g) == "PIB" for g in d))
        if n or tag(child) not in rec:
            rec[f"n_pers__{tag(child)}"] = rec.get(f"n_pers__{tag(child)}", 0) + n
    return rec


def parse_xml(url, label, counter, dest_csv):
    RAW.mkdir(parents=True, exist_ok=True)
    tmp = RAW / f"_{label}.xml.part"
    log(f"downloading {url} (temporary; contains personal data; deleted after parsing)")
    rows, region, tags, shown = [], None, {}, set()
    try:
        tmp.unlink(missing_ok=True)
        log(f"  {download_resumable(url, tmp) / 1e6:.1f} MB received")
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
            rec.update(counter(el))
            if rec["council_type"] not in shown:
                shown.add(rec["council_type"])
                log(f"\n  {label}: structure, first {rec['council_type']} council (tags only):")
                log("\n".join(tree(el)))
            rows.append(rec)
            el.clear()
    finally:
        tmp.unlink(missing_ok=True)
        log(f"\n  temporary {label} XML deleted")
    log("  element counts: " + ", ".join(f"{k}={v}" for k, v in sorted(tags.items(), key=lambda x: -x[1])))
    df = pd.DataFrame(rows)
    df.to_csv(dest_csv, index=False)
    log(f"  councils={len(df)} -> {dest_csv}")
    return df


def read_counts(p):
    return pd.read_csv(p, dtype={"rada_id": str}) if p.exists() else None


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
    kyiv = c["ob"].eq("київ") & c["k3"].isna()
    c.loc[kyiv, ["k3", "match"]] = ["8000000", "city"]
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
    return c


def combined():
    cand, elec = read_counts(CAND_CSV), read_counts(ELECT_CSV)
    if cand is None or elec is None:
        raise SystemExit("run 'probe' first (both count files are needed)")
    pers = [x for x in elec.columns if x.startswith("n_pers__")]
    dep = [x for x in pers if "deput" in x.lower()]
    if not dep:
        raise SystemExit(f"no deputies wrapper among {pers}; check the probe structure")
    e = elec[["rada_id"]].copy()
    e["n_seats"] = elec[dep].sum(axis=1)
    both = cand.merge(e, on="rada_id", how="left")
    return both, dep


# ---------------------------------------------------------------- modes
def cmd_probe(a):
    open_log("33_probe.log")
    cand = read_counts(CAND_CSV)
    if cand is None or a.refresh or DEP_CAND not in cand.columns:
        cand = parse_xml(CAND_XML, "candidates", count_candidates, CAND_CSV)
    else:
        log(f"candidate counts: reusing {CAND_CSV} ({len(cand)} councils); --refresh to download again")
    elec = parse_xml(ELECT_XML, "elected", count_persons, ELECT_CSV)
    pers = [x for x in elec.columns if x.startswith("n_pers__")]
    log("\n  elected persons per council by wrapper and council type (median / councils with >0):")
    for t, g in elec.groupby("council_type"):
        log(f"    {t:8s} n={len(g):4d}  " + "  ".join(
            f"{x[8:]}: {g[x].median():.0f}/{int((g[x] > 0).sum())}" for x in pers if g[x].notna().any()))
    ids = set(cand["rada_id"]) & set(elec["rada_id"])
    log(f"  council ids in both files: {len(ids)} (candidates {len(cand)}, elected {len(elec)})")
    both, dep = combined()
    m = match_k3(both)
    m["cand_per_seat"] = m[DEP_CAND] / m["n_seats"].where(m["n_seats"] > 0)
    m["system"] = (m.get(f"n_{LIST_TAG}__candidates_for_deputies", 0) > 0).map(
        {True: "proportional", False: "districts"})
    log("\n  candidates per seat by electoral system (hromada councils):")
    for s, g in m.groupby("system"):
        v = g["cand_per_seat"].dropna()
        log(f"    {s:12s} n={len(g):4d} with seats={len(v):4d}  median={v.median():.2f}  "
            f"p05={v.quantile(.05):.2f}  p95={v.quantile(.95):.2f}")
    vk = m[m["k3"] == TEST_K3]
    if len(vk):
        log("\n  Verkhovyna 2602003:\n" + vk[["rada_id", "rada_name", DEP_CAND, "n_seats", "cand_per_seat",
                                             "system"]].T.to_string(header=False))


def cmd_build(a):
    open_log("33_build.log")
    both, _ = combined()
    m = match_k3(both)
    m = m[m["k3"].notna()].copy()
    m["n_deputy_candidates"] = m[DEP_CAND]
    m["cand_per_seat"] = (m[DEP_CAND] / m["n_seats"].where(m["n_seats"] > 0)).round(3)
    lists = f"n_{LIST_TAG}__candidates_for_deputies"
    m["electoral_system"] = (m[lists].fillna(0) > 0).map({True: "proportional", False: "districts"})
    med = m.groupby("electoral_system")["cand_per_seat"].transform("median")
    m["cand_per_seat_rel"] = (m["cand_per_seat"] / med).round(3)
    m["n_head_candidates"] = m[HEAD_CAND] if HEAD_CAND in m.columns else None
    cols = ["k3", "rada_id", "electoral_system", "n_deputy_candidates", "n_seats", "cand_per_seat",
            "cand_per_seat_rel", "n_head_candidates"]
    keys = pd.read_csv(TIDY / "keys_hromada.csv", dtype=str)[["k1", "k2", "k3", "name"]]
    out = keys.merge(m[cols], on="k3", how="inner").sort_values("k3")
    out.to_csv(OUT, index=False)
    log(f"wrote {OUT.name} rows={len(out)}")
    for s_, g in out.groupby("electoral_system"):
        log(f"  {s_:12s} n={len(g)}  cand_per_seat median={g['cand_per_seat'].median():.2f}  "
            f"rel p05={g['cand_per_seat_rel'].quantile(.05):.2f} p95={g['cand_per_seat_rel'].quantile(.95):.2f}")

    try:                                   # non-occupied hromadas without a value
        sys.path.insert(0, str(BASE))
        ob = importlib.import_module("03_openbudget")
        k = ob.load_keys()
        k["k3"] = k["k3"].astype(str).str.zfill(7)
        free = k[k["occupied"] == False]  # noqa: E712
        miss = free[~free["k3"].isin(out.loc[out["cand_per_seat"].notna(), "k3"])]
        log(f"  non-occupied hromadas: {len(free)}, without cand_per_seat: {len(miss)}"
            + (": " + "; ".join(f"{r.k3} {r.name}" for r in miss.head(40).itertuples()) if len(miss) else ""))
    except Exception as e:
        log(f"  occupation check skipped ({e})")

    src = "Central Election Commission (cvk.gov.ua), IAS Місцеві вибори 2020, election 695, open data XML"
    lic = "open data, attribution required (data.gov.ua copy CC BY)"
    dd_new = pd.DataFrame([
        ["cand_per_seat", src, lic, "ratio", "2020", "hromada",
         "deputy candidates registered / deputies elected, hromada council, 25 Oct 2020; counts only"],
        ["cand_per_seat_rel", src, lic, "ratio to system median", "2020", "hromada",
         "cand_per_seat / national median of the same electoral system (index input: proportional "
         "lists carry about three times more candidates per seat than district elections)"],
        ["electoral_system", src, lic, "category", "2020", "hromada",
         "proportional (party lists, >10,000 voters) or districts (multi-member districts)"],
        ["n_head_candidates", src, lic, "count", "2020", "hromada",
         "candidates for head; listed for city councils only — context, not an index input"],
    ], columns=["indicator", "source", "licence", "unit", "year", "level", "method"])
    ddp = TIDY / "data_dictionary.csv"
    dd = pd.read_csv(ddp, dtype=str) if ddp.exists() else pd.DataFrame(columns=dd_new.columns)
    drop = set(dd_new["indicator"]) | {"turnout", "protocol_status", "n_council_lists"}
    dd = pd.concat([dd[~dd["indicator"].isin(drop)], dd_new], ignore_index=True)
    dd.to_csv(ddp, index=False)
    log(f"data dictionary updated: {len(dd)} indicators")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("mode", choices=["probe", "build"])
    ap.add_argument("--refresh", action="store_true", help="download the candidate XML again")
    a = ap.parse_args()
    {"probe": cmd_probe, "build": cmd_build}[a.mode](a)


if __name__ == "__main__":
    main()
