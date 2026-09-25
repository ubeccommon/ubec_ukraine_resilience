#!/usr/bin/env python3
"""
09_stat_edrpou.py — registered legal entities (LE) and sole proprietors (FOP) per
hromada from regional offices of the State Statistics Service (ЄДРПОУ counts by
"районами та територіями територіальних громад").

  python 09_stat_edrpou.py [--oblasts 56,63,26 | --all] [--depth 3] [--max-pages 150]

Crawls each oblast office's seed pages (same host, prioritised links), parses every
HTML table with >= 5 hromada rows and a detectable kind (LE / FOP), reads the snapshot date
("на 01 <month> <year>"), matches rows to k3 by name within oblast/raion, reports coverage.
Name overrides: tidy/stat_name_aliases.csv (k1,table_name,k3) — applied on rerun.
Licence: official statistics, reuse with mandatory attribution to the regional office.
Caveats: counts are registrations by legal address (stock incl. dormant entities);
some offices withhold hromada tables under martial law (e.g. Zhytomyr LE, Chernivtsi);
raion totals can exceed the sum of hromadas (entities coded at raion level).
Outputs: raw/stat_edrpou/*.html (cache), tidy/stat_edrpou_long.csv, tidy/stat_edrpou_k3.csv
"""
import argparse
import difflib
import hashlib
import heapq
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd
import pyogrio
from lxml import html as LH

BASE = Path(__file__).resolve().parent
QGIS = BASE.parent / "viina" / "qgis"
RAW = BASE / "raw" / "stat_edrpou"
TIDY, LOGS = BASE / "tidy", BASE / "logs"
for d in (RAW, TIDY, LOGS):
    d.mkdir(parents=True, exist_ok=True)
ALIASES = TIDY / "stat_name_aliases.csv"

SOURCES = {
    "05": {"oblast": "Вінницька", "index": [
        "https://www.vn.ukrstat.gov.ua/index.php/component/content/article/732/8261-----------2025.html",
        "https://www.vn.ukrstat.gov.ua/index.php/statistical-information.html",
        "https://www.vn.ukrstat.gov.ua/index.php/statistical-information/arhiv2022.html",
        "https://www.vn.ukrstat.gov.ua/index.php/statistical-information/arhiv2023.html"]},
    "07": {"oblast": "Волинська", "index": ["http://www.lutsk.ukrstat.gov.ua/"]},
    "12": {"oblast": "Дніпропетровська", "index": ["http://www.dneprstat.gov.ua/"]},
    "14": {"oblast": "Донецька", "index": ["http://www.dn.ukrstat.gov.ua/"]},
    "18": {"oblast": "Житомирська", "index": ["https://www.zt.ukrstat.gov.ua/StatInfo/reestr/reestrfiz.htm",
                                             "https://www.zt.ukrstat.gov.ua/"]},
    "21": {"oblast": "Закарпатська", "index": ["http://www.uz.ukrstat.gov.ua/"]},
    "23": {"oblast": "Запорізька", "index": ["http://www.zp.ukrstat.gov.ua/"]},
    "26": {"oblast": "Івано-Франківська", "index": ["https://ifstat.gov.ua/EX_IN/re3.htm",
                                                    "https://ifstat.gov.ua/EX_IN/re4.htm",
                                                    "https://ifstat.gov.ua/EX_IN/"]},
    "32": {"oblast": "Київська", "index": ["http://kyivobl.ukrstat.gov.ua/p.php3?c=1665&lang=1",
                                          "http://kyivobl.ukrstat.gov.ua/"]},
    "35": {"oblast": "Кіровоградська", "index": [
        "https://www.kr.ukrstat.gov.ua/?r=stat%2F2026%2F07%2Fedrpou%2Fed_reestr_kilkist15",
        "https://www.kr.ukrstat.gov.ua/"]},
    "46": {"oblast": "Львівська", "index": [f"https://lv.ukrstat.gov.ua/ukr/news/oblik_inf_{y}.php"
                                          for y in (26, 25, 24, 23, 22)] + ["https://www.lv.ukrstat.gov.ua/"]},
    "48": {"oblast": "Миколаївська", "index": ["http://www.mk.ukrstat.gov.ua/"]},
    "51": {"oblast": "Одеська", "index": ["https://od.ukrstat.gov.ua/stat_info/reestr/reestr2.htm",
                                         "https://od.ukrstat.gov.ua/"]},
    "53": {"oblast": "Полтавська", "index": ["http://pl.ukrstat.gov.ua/"]},
    "56": {"oblast": "Рівненська", "index": [f"https://www.gusrv.gov.ua/edrpou/pokazn{y}.htm"
                                           for y in (26, 25, 24, 23, 22, 21)]
                                          + ["https://www.gusrv.gov.ua/edrpou/pokazn.htm"]},
    "59": {"oblast": "Сумська", "index": ["https://sumy.ukrstat.gov.ua/?article_id=12090&menu=1078",
                                         "https://sumy.ukrstat.gov.ua/"]},
    "61": {"oblast": "Тернопільська", "index": ["https://www.te.ukrstat.gov.ua/", "https://te.ukrstat.gov.ua/files/EDR/"]},
    "63": {"oblast": "Харківська", "index": [
        "https://kh.ukrstat.gov.ua/dani-pro-kilkist-sub-iektiv-yedrpou",
        "https://kh.ukrstat.gov.ua/kilkist-zareiestrovanykh-iurydychnykh-osib-za-raionamy-ta-terytoriiamy-terytorialnykh-hromad",
        "https://kh.ukrstat.gov.ua/kilkist-zareiestrovanykh-fizychnykh-osib-pidpryiemtsiv-za-raionamy-ta-terytoriiamy-terytorialnykh-hromad"]},
    "65": {"oblast": "Херсонська", "index": ["http://www.ks.ukrstat.gov.ua/"]},
    "68": {"oblast": "Хмельницька", "index": [
        f"https://www.km.ukrstat.gov.ua/ukr/statinf/edrpoy/20{y}/{k}_{m}{y}.htm"
        for y in ("26", "25", "22") for m in ("01", "07") for k in ("katottg", "fop")]
        + ["https://www.km.ukrstat.gov.ua/"]},
    "71": {"oblast": "Черкаська", "index": ["https://www.ck.ukrstat.gov.ua/"]},
    "73": {"oblast": "Чернівецька", "index": ["http://www.cv.ukrstat.gov.ua/"]},
    "74": {"oblast": "Чернігівська", "index": [
        f"https://www.chernigivstat.gov.ua/reestr/{y}/katottg_{m}.htm"
        for y in (2026, 2025, 2022) for m in ("01", "07")] + ["https://www.chernigivstat.gov.ua/"]},
}
PILOT = "56,63,26"
HDR = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
       "Accept-Language": "uk-UA,uk;q=0.9"}
LINK_RE = re.compile(r"громад|\bТГ\b|юридичн|фізичн|ЄДРПОУ|edrpo|kilk|kilfiz|reestr|реєстр|osib|суб.єкт|katottg", re.I)
STRONG_RE = re.compile(r"юридичн|фізичн|ЄДРПОУ|edrpo|реєстр|reestr|kilk|kilfiz|katottg", re.I)
NAV_RE = re.compile(r"статистична інформація|економічна статистика|stat_?info|statinf|реєстр респондент|"
                    r"суб.єкти господарювання|діяльність підприємств", re.I)
SKIP_RE = re.compile(r"\.(pdf|docx?|xlsx?|zip|rar|jpe?g|png|gif)(\?|$)|facebook|youtube|mailto:|javascript:|#", re.I)
MONTHS = {"січня": 1, "квітня": 4, "липня": 7, "жовтня": 10}
DATE_RE = re.compile(r"на\s+0?1\s+(січня|квітня|липня|жовтня)\s+(20\d\d)", re.I)
HROM_RE = re.compile(r"\bТГ\b|громад", re.I)
RAION_RE = re.compile(r"район\s*$", re.I)
TYPE_RE = re.compile(r"(міськ|селищн|сільськ)", re.I)
STOP = r"\b(міська|сільська|селищна|територіальна|громада|тг|район|рада|область)\b"
_logf = open(LOGS / "09_stat_edrpou.log", "w", encoding="utf-8")


def log(*a):
    m = " ".join(str(x) for x in a)
    print(m, flush=True)
    _logf.write(m + "\n")
    _logf.flush()


def fetch(url):
    p = RAW / (hashlib.sha1(url.encode()).hexdigest()[:16] + ".html")
    if p.exists():
        return p.read_bytes().decode("utf-8", "replace")
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=HDR), timeout=30) as r:
            raw, ctype = r.read(), r.headers.get("Content-Type", "")
    except (urllib.error.URLError, TimeoutError, ValueError) as e:
        log(f"    fetch fail {url}: {e}")
        return None
    enc = None
    m = re.search(r"charset=([\w-]+)", ctype) or re.search(rb"charset=[\"']?([\w-]+)", raw[:3000])
    if m:
        enc = m.group(1).decode() if isinstance(m.group(1), bytes) else m.group(1)
    for e in [enc, "utf-8", "cp1251"]:
        if not e:
            continue
        try:
            txt = raw.decode(e)
            break
        except (UnicodeDecodeError, LookupError):
            continue
    else:
        txt = raw.decode("utf-8", "replace")
    p.write_text(txt, encoding="utf-8")
    time.sleep(0.5)
    return txt


def host(u):
    return urllib.parse.urlparse(u).netloc.lower().removeprefix("www.")


def crawl(k1, cfg, depth, max_pages):
    seeds = cfg["index"]
    hosts = {host(u) for u in seeds}
    seen, pages, n = set(), [], 0
    q = [(0, 0, i, u) for i, u in enumerate(seeds)]
    heapq.heapify(q)
    while q and len(pages) < max_pages:
        prio, dpt, _, url = heapq.heappop(q)
        if url in seen:
            continue
        seen.add(url)
        txt = fetch(url)
        if not txt:
            continue
        pages.append((url, txt))
        if dpt >= depth:
            continue
        try:
            doc = LH.fromstring(txt)
        except Exception:
            continue
        doc.make_links_absolute(url)
        for a in doc.iter("a"):
            href = (a.get("href") or "").split("#")[0]
            if not href or SKIP_RE.search(href) or host(href) not in hosts or href in seen:
                continue
            label = (a.text_content() or "") + " " + urllib.parse.unquote(href)
            if STRONG_RE.search(label):
                p = 0
            elif LINK_RE.search(label):
                p = 1
            elif NAV_RE.search(label):
                p = 2
            else:
                continue
            n += 1
            heapq.heappush(q, (p, dpt + 1, n, href))
    log(f"  {cfg['oblast']}: fetched {len(pages)} pages")
    return pages


def parse_int(s):
    s = s.replace("\xa0", "").replace(" ", "").strip()
    if s in ("-", "–", "—"):
        return 0
    return int(s) if re.fullmatch(r"\d+", s) else None


def parse_page(url, txt):
    try:
        doc = LH.fromstring(txt)
    except Exception:
        return []
    title = (doc.findtext(".//title") or "").strip()
    page_text = re.sub(r"\s+", " ", doc.text_content())
    out = []
    for ti, tab in enumerate(doc.iter("table")):
        rows, raion = [], None
        for tr in tab.iter("tr"):
            cells = [re.sub(r"\s+", " ", c.text_content()).strip() for c in tr.xpath("./td|./th")]
            cells = [c for c in cells if c != ""]
            if len(cells) < 2:
                continue
            name = re.sub(r"[;,.:*]+$", "", cells[0]).strip()
            val = next((v for v in (parse_int(c) for c in cells[1:]) if v is not None), None)
            if val is None:
                continue
            if HROM_RE.search(name):
                rows.append({"table_name": name, "level": "hromada", "value": val, "raion": raion})
            elif RAION_RE.search(name):
                raion = name
                rows.append({"table_name": name, "level": "raion", "value": val, "raion": name})
            elif re.search(r"област", name, re.I):
                rows.append({"table_name": name, "level": "oblast", "value": val, "raion": None})
        if sum(r["level"] == "hromada" for r in rows) < 5:
            continue
        ctx = re.sub(r"\s+", " ", tab.text_content())[:800] + " " + title
        kind = ("fop" if re.search(r"фізичн", ctx, re.I) else
                "le" if re.search(r"юридичн", ctx, re.I) else
                "fop" if re.search(r"фізичн", title + page_text[:3000], re.I) else
                "le" if re.search(r"юридичн", title + page_text[:3000], re.I) else None)
        if kind is None:
            continue
        m = DATE_RE.search(ctx) or DATE_RE.search(page_text)
        date = f"{m.group(2)}-{MONTHS[m.group(1).lower()]:02d}-01" if m else None
        for r in rows:
            r.update(kind=kind, date=date, url=url, table=ti)
        out.extend(rows)
    return out


def stype(s):
    m = TYPE_RE.search(str(s))
    return m.group(1).lower() if m else None


def stem(s):
    s = str(s).lower().replace("ʼ", "").replace("’", "").replace("'", "").replace("`", "")
    s = re.sub(STOP, " ", s)
    return re.sub(r"[^a-zа-яіїєґ]", "", s)


def match(df, keys, raions, aliases):
    df = df.copy()
    df["k2"], df["k3"], df["method"] = None, None, None
    df["st"] = df["table_name"].map(stem)
    for k1, sub in df.groupby("k1"):
        kk = keys[keys["k1"] == k1].assign(st=lambda x: x["name"].map(stem))
        rr = raions[raions["k1"] == k1].assign(st=lambda x: x["name"].map(stem))
        rmap = dict(zip(rr["st"], rr["k2"]))
        al = aliases[aliases["k1"] == k1].set_index("table_name")["k3"].to_dict() if len(aliases) else {}
        for i, r in sub.iterrows():
            if r["raion"]:
                rs = stem(r["raion"])
                k2 = rmap.get(rs)
                if k2 is None and rmap:
                    close = difflib.get_close_matches(rs, list(rmap), n=1, cutoff=0.75)
                    k2 = rmap[close[0]] if close else None
                df.at[i, "k2"] = k2
            if r["level"] != "hromada":
                continue
            if r["table_name"] in al:
                df.at[i, "k3"], df.at[i, "method"] = al[r["table_name"]], "alias"
                continue
            st, ty = r["st"], stype(r["table_name"])
            pool = kk[kk["k2"] == df.at[i, "k2"]] if df.at[i, "k2"] else kk
            hit = pool[pool["st"] == st]
            if len(hit) != 1:
                hit = kk[kk["st"] == st]
            if len(hit) > 1 and ty:
                hit = hit[hit["name"].map(stype) == ty]
            if len(hit) == 1:
                df.at[i, "k3"], df.at[i, "method"] = hit["k3"].iloc[0], "exact"
                continue
            close = difflib.get_close_matches(st, list(pool["st"]), n=1, cutoff=0.82)
            if close:
                df.at[i, "k3"] = pool.loc[pool["st"] == close[0], "k3"].iloc[0]
                df.at[i, "method"] = "fuzzy"
    h = df["level"] == "hromada"
    # raion rows the name lookup missed (renamed raions): majority k2 of matched hromadas
    vote = (df[h & df["k3"].notna() & df["raion"].notna()]
            .assign(k2v=lambda x: x["k3"].str[:4]).groupby(["k1", "raion"])["k2v"]
            .agg(lambda s: s.mode().iloc[0]))
    for (k1, rn), k2 in vote.items():
        m = (df["k1"] == k1) & (df["raion"] == rn) & df["k2"].isna()
        df.loc[m, "k2"] = k2
    # same table name matched at another date -> reuse
    known = (df[h & df["k3"].notna()].groupby(["k1", "st"])["k3"]
             .agg(lambda s: s.mode().iloc[0]).to_dict())
    for i in df.index[h & df["k3"].isna()]:
        k = known.get((df.at[i, "k1"], df.at[i, "st"]))
        if k:
            df.at[i, "k3"], df.at[i, "method"] = k, "other_date"
    # elimination: one unmatched row and one unused key in the same raion of the same table
    for (k1, kind, date, url, tab), g in df[h].groupby(["k1", "kind", "date", "url", "table"], dropna=False):
        for k2, gg in g.groupby("k2"):
            un_rows = gg.index[gg["k3"].isna()]
            if len(un_rows) != 1:
                continue
            used = set(gg["k3"].dropna())
            free_keys = [k for k in keys.loc[keys["k2"] == k2, "k3"] if k not in used]
            if len(free_keys) == 1:
                df.at[un_rows[0], "k3"], df.at[un_rows[0], "method"] = free_keys[0], "elimination"
    # a k3 may appear only once per table: keep exact/alias, drop the weaker duplicates
    rank = {"alias": 0, "exact": 1, "other_date": 2, "elimination": 3, "fuzzy": 4}
    for key, g in df[h & df["k3"].notna()].groupby(["k1", "kind", "date", "url", "table", "k3"], dropna=False):
        if len(g) > 1:
            keep = g["method"].map(rank).idxmin()
            drop = [i for i in g.index if i != keep]
            df.loc[drop, ["k3", "method"]] = [None, "duplicate_dropped"]
    return df.drop(columns="st")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--oblasts", default=PILOT)
    ap.add_argument("--all", action="store_true", help="all oblasts in SOURCES")
    ap.add_argument("--depth", type=int, default=3)
    ap.add_argument("--max-pages", type=int, default=150)
    a = ap.parse_args()

    keys = pd.read_csv(TIDY / "keys_hromada.csv", dtype=str)[["k1", "k2", "k3", "name"]]
    raions = pyogrio.read_dataframe(QGIS / "admin_units.gpkg", layer="raion",
                                    read_geometry=False)[["k1", "k2", "name"]].astype(str)
    ctrl = pyogrio.read_dataframe(QGIS / "hromada_control.gpkg", layer="hromada_control",
                                  read_geometry=False)[["k3", "occupied"]]
    ctrl["k3"] = ctrl["k3"].astype(str).str.zfill(7)
    aliases = (pd.read_csv(ALIASES, dtype=str) if ALIASES.exists()
               else pd.DataFrame(columns=["k1", "table_name", "k3"]))

    rows, found = [], {}
    todo = list(SOURCES) if a.all else [x.strip() for x in a.oblasts.split(",")]
    for k1 in todo:
        cfg = SOURCES[k1]
        log(f"\n== {k1} {cfg['oblast']}")
        for url, txt in crawl(k1, cfg, a.depth, a.max_pages):
            got = parse_page(url, txt)
            if got:
                nh = sum(r["level"] == "hromada" for r in got)
                kinds = {r["kind"] for r in got}
                dates = {r["date"] for r in got}
                log(f"  table page: {url}\n     hromada rows {nh}  kind {kinds}  date {dates}")
                for r in got:
                    r["k1"] = k1
                rows.extend(got)
                found[k1] = found.get(k1, 0) + 1
    none = [f"{k} {SOURCES[k]['oblast']}" for k in todo if k not in found]
    if none:
        log("\noblasts with NO hromada table found: " + "; ".join(none))
    if not rows:
        raise SystemExit("no hromada tables found in any oblast")
    df = pd.DataFrame(rows)
    # keep, per (k1, kind, date), the table with the most hromada rows
    nh = df[df["level"] == "hromada"].groupby(["k1", "kind", "date", "url", "table"], dropna=False).size()
    best = nh.reset_index(name="n").sort_values("n", ascending=False).drop_duplicates(["k1", "kind", "date"])
    df = df.merge(best[["k1", "kind", "date", "url", "table"]], on=["k1", "kind", "date", "url", "table"])
    df = match(df, keys, raions, aliases)
    df.to_csv(TIDY / "stat_edrpou_long.csv", index=False)
    log(f"\nwrote tidy/stat_edrpou_long.csv rows={len(df)}")

    free = set(ctrl.loc[ctrl["occupied"] == False, "k3"])  # noqa: E712
    log("\nsnapshots found (k1, kind, date -> hromada rows, matched):")
    for (k1, kind, date), g in df[df["level"] == "hromada"].groupby(["k1", "kind", "date"], dropna=False):
        log(f"  {k1} {kind} {date}: rows {len(g)}  matched {g['k3'].notna().sum()} "
            f"({g['method'].value_counts().to_dict()})")
    un = df[(df["level"] == "hromada") & df["k3"].isna()][["k1", "raion", "table_name", "method"]].drop_duplicates()
    if len(un):
        log(f"\nunmatched table names ({len(un)}) — add to {ALIASES.name} as k1,table_name,k3:\n"
            + un.to_string(index=False))
    fz = df[df["method"].isin(["fuzzy", "elimination"])][["k1", "table_name", "method", "k3"]].drop_duplicates()
    if len(fz):
        fz = fz.merge(keys[["k3", "name"]], on="k3", how="left")
        log("\nfuzzy / elimination matches to verify:\n" + fz.to_string(index=False))

    # raion consistency: sum of hromadas vs raion row (duplicate raion rows aggregated)
    h = (df[(df["level"] == "hromada") & df["k2"].notna()]
         .groupby(["k1", "kind", "date", "k2"], dropna=False)["value"].sum())
    r = (df[(df["level"] == "raion") & df["k2"].notna()]
         .groupby(["k1", "kind", "date", "k2"], dropna=False)["value"].max())
    cmp = pd.concat({"sum_hromada": h, "raion_row": r}, axis=1).dropna()
    if len(cmp):
        cmp["share"] = cmp["sum_hromada"] / cmp["raion_row"]
        log(f"\nraion check: sum(hromadas)/raion row median {cmp['share'].median():.3f}  "
            f"min {cmp['share'].min():.3f}  (n={len(cmp)})")

    # wide: latest snapshot and pre-war / early-war baseline per kind
    hh = df[(df["level"] == "hromada") & df["k3"].notna() & df["date"].notna()]
    wide = []
    for kind, g in hh.groupby("kind"):
        g = g.sort_values("date")
        last = g.groupby("k3").tail(1)[["k3", "value", "date"]].drop_duplicates("k3", keep="last")
        wide.append(last.rename(columns={"value": f"{kind}_count", "date": f"{kind}_date"}).set_index("k3"))
        b = g[g["date"] <= "2022-04-01"].groupby("k3").head(1)[["k3", "value", "date"]].drop_duplicates("k3")
        if len(b):
            wide.append(b.rename(columns={"value": f"{kind}_count_base",
                                          "date": f"{kind}_base_date"}).set_index("k3"))
    if wide:
        w = pd.concat(wide, axis=1).reset_index()
        w = keys.merge(w, on="k3", how="inner")
        w.to_csv(TIDY / "stat_edrpou_k3.csv", index=False)
        log(f"\nwrote tidy/stat_edrpou_k3.csv rows={len(w)}")
        tot_le = tot_fop = 0
        for k1 in sorted(set(w["k1"])):
            nf = len([k for k in free if k[:2] == k1])
            wk = w[w["k1"] == k1]
            msg = [f"  {k1}: non-occupied hromadas {nf}"]
            for kind in ("le", "fop"):
                if f"{kind}_count" in wk:
                    cov = int(wk[wk["k3"].isin(free)][f"{kind}_count"].notna().sum())
                    if kind == "le":
                        tot_le += cov
                    else:
                        tot_fop += cov
                    d = sorted(wk[f"{kind}_date"].dropna().unique())
                    bd = sorted(wk[f"{kind}_base_date"].dropna().unique()) if f"{kind}_base_date" in wk else []
                    msg.append(f"{kind}: {cov} non-occ, latest {d[-1] if d else '-'}, base {bd[0] if bd else '-'}")
            log(" | ".join(msg))
        log(f"\nNATIONAL COVERAGE of {len(free)} non-occupied hromadas: LE {tot_le} "
            f"({tot_le/len(free):.0%})  FOP {tot_fop} ({tot_fop/len(free):.0%})")
    _logf.close()


if __name__ == "__main__":
    main()
