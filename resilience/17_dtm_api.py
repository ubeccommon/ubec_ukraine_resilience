#!/usr/bin/env python3
"""
17_dtm_api.py — IOM DTM API (v3) for Ukraine IDP figures.

  python 17_dtm_api.py probe            # endpoints, Ukraine operations, coverage
  python 17_dtm_api.py pull [--refresh] # admin0/admin1 Ukraine -> raw/dtm_api/ (cached)
  python 17_dtm_api.py tidy             # oblast x month tables, OD matrix, latest

Key: ~/.dtm_key (Ocp-Apim-Subscription-Key). Raw JSON cached in raw/dtm_api/.
Admin2/Admin3 are NOT served for Ukraine (checked 2026-09-25): hromada data on
request from IOM only.

Operations (never sum across them):
  registration = "Displacement due to Conflict in Ukraine (Registration)":
                 IDPs registered (MoSP register) by host oblast x origin oblast,
                 monthly. Registered location, not residence; deregistration lags.
  survey       = "Displacement due to Conflict in Ukraine":
                 General Population Survey rounds, IDPs present (estimate).
Licence: IOM DTM terms (https://dtm.iom.int/terms-and-conditions);
cite "IOM DTM API, accessed <date>". Aggregated non-sensitive figures only.
"""
import sys, json, time, urllib.request, urllib.parse, urllib.error
from pathlib import Path
from collections import Counter
from datetime import date

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw" / "dtm_api"
TIDY = ROOT / "tidy"
RAW.mkdir(parents=True, exist_ok=True)
TIDY.mkdir(parents=True, exist_ok=True)
KEY_FILE = Path.home() / ".dtm_key"

BASE = "https://dtmapi.iom.int/v3/displacement"
OPS = {"Displacement due to Conflict in Ukraine (Registration)": "registration",
       "Displacement due to Conflict in Ukraine": "survey"}
# frontline / heavily occupied origin oblasts (for origin-share indicator)
FRONT_K1 = {"14", "44", "23", "65", "63", "01", "85"}  # Donetsk, Luhansk, Zaporizhzhia,
                                                     # Kherson, Kharkiv, Crimea, Sevastopol


def key():
    return KEY_FILE.read_text().strip()


def get(url, params=None):
    q = ("?" + urllib.parse.urlencode(params)) if params else ""
    req = urllib.request.Request(url + q, headers={
        "Ocp-Apim-Subscription-Key": key(),
        "User-Agent": "research-script/1.0",
        "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:300]
    except Exception as e:
        return -1, repr(e)[:300]


def rows_of(js):
    if isinstance(js, list):
        return js
    if isinstance(js, dict) and isinstance(js.get("result"), list):
        return js["result"]
    return []


# ---------------------------------------------------------------- probe
def probe():
    for name in ("country-list", "operation-list"):
        st, js = get(f"{BASE}/{name}")
        rows = rows_of(js)
        ua = [r for r in rows if "ukrain" in json.dumps(r).lower()]
        print(f"{name}: {st}, {len(rows)} rows, Ukraine: {ua}")
    for lvl in ("admin0", "admin1", "admin2"):
        st, js = get(f"{BASE}/{lvl}", {"CountryName": "Ukraine"})
        n = len(rows_of(js))
        tot = js.get("totalRecordsCount") if isinstance(js, dict) else None
        msg = js.get("errorMessages") if isinstance(js, dict) else js
        print(f"{lvl}: {st}, rows={n}, total={tot}, msg={msg}")
        time.sleep(1)


# ---------------------------------------------------------------- pull
def pull(refresh=False):
    for lvl in ("admin0", "admin1"):
        fn = RAW / f"{lvl}_ukraine.json"
        if fn.exists() and not refresh:
            print(f"{lvl}: cached {fn.name} ({len(json.loads(fn.read_text()))} rows)")
            continue
        st, js = get(f"{BASE}/{lvl}", {"CountryName": "Ukraine"})
        if st != 200:
            sys.exit(f"{lvl}: HTTP {st} {str(js)[:200]}")
        rows = rows_of(js)
        tot = js.get("totalRecordsCount")
        print(f"{lvl}: {len(rows)} rows (totalRecordsCount={tot})")
        if tot is not None and tot != len(rows):
            print(f"  WARNING: {tot - len(rows)} records not returned — paging needed")
        fn.write_text(json.dumps(rows, ensure_ascii=False))
        (RAW / f"{lvl}_ukraine.meta.json").write_text(json.dumps(
            {"accessed": date.today().isoformat(), "total": tot, "rows": len(rows),
             "url": f"{BASE}/{lvl}?CountryName=Ukraine"}))
        time.sleep(1)


# ---------------------------------------------------------------- tidy
def k1_of(pcode):
    p = str(pcode or "")
    return p[2:4] if p.startswith("UA") and len(p) >= 4 else p  # keeps 'Occupied'/'Incomplete'


def tidy():
    import pandas as pd

    fn = RAW / "admin1_ukraine.json"
    if not fn.exists():
        sys.exit("run: python 17_dtm_api.py pull")
    df = pd.DataFrame(json.loads(fn.read_text()))
    meta = RAW / "admin1_ukraine.meta.json"
    accessed = json.loads(meta.read_text())["accessed"] if meta.exists() else "2026-09-25"

    df["op"] = df["operation"].map(OPS).fillna("other")
    df["date"] = pd.to_datetime(df["reportingDate"]).dt.date.astype(str)
    df["k1"] = df["admin1Pcode"].map(k1_of)
    df["k1_origin"] = df["idpOriginAdmin1Pcode"].map(k1_of)
    for c in ("numPresentIdpInd", "numberMales", "numberFemales"):
        df[c] = pd.to_numeric(df[c], errors="coerce")

    n0 = len(df)
    df = df.drop_duplicates(subset=[c for c in df.columns if c != "id"])
    print(f"admin1 rows {n0}, after exact-duplicate drop {len(df)}")
    print("operations:", df["op"].value_counts().to_dict())
    print("host pcodes not UA##:", sorted(df.loc[~df["k1"].str.fullmatch(r"\d\d"), "k1"].unique()))
    print("origin pcodes not UA##:",
          sorted(df.loc[~df["k1_origin"].astype(str).str.fullmatch(r"\d\d"), "k1_origin"]
                 .astype(str).unique())[:10])

    # oblast x month x operation
    g = (df.groupby(["k1", "admin1Name", "op", "date", "roundNumber"], dropna=False)
           .agg(idp=("numPresentIdpInd", "sum"), males=("numberMales", "sum"),
                females=("numberFemales", "sum"), n_origin=("k1_origin", "nunique"))
           .reset_index().sort_values(["op", "k1", "date"]))
    g.to_csv(TIDY / "dtm_oblast_month_k1.csv", index=False)
    print(f"\ndtm_oblast_month_k1.csv: {len(g)} rows")
    for op, s in g.groupby("op"):
        d = s["date"].unique()
        print(f"  {op:12s} {len(d)} dates {d.min()} … {d.max()}, "
              f"{s['k1'].nunique()} host units, national latest "
              f"{s.loc[s.date == d.max(), 'idp'].sum():,.0f}")

    # OD matrix (registration)
    reg = df[df["op"] == "registration"]
    od = (reg.groupby(["date", "k1", "k1_origin"], dropna=False)["numPresentIdpInd"]
             .sum().reset_index().rename(columns={"k1": "k1_host",
                                                  "numPresentIdpInd": "idp_registered"}))
    od.to_csv(TIDY / "dtm_oblast_od_k1.csv", index=False)
    print(f"dtm_oblast_od_k1.csv: {len(od)} rows")

    # latest per oblast
    rg = g[g["op"] == "registration"]
    last = rg["date"].max()
    base = "2023-02-28" if "2023-02-28" in set(rg["date"]) else sorted(rg["date"])[12]
    lat = rg[rg.date == last].set_index("k1")[["admin1Name", "idp", "males", "females"]]
    lat = lat.rename(columns={"idp": "dtm_reg_latest", "males": "dtm_reg_m",
                              "females": "dtm_reg_f"})
    lat["dtm_reg_base"] = rg[rg.date == base].set_index("k1")["idp"]
    lat["dtm_reg_change"] = lat["dtm_reg_latest"] / lat["dtm_reg_base"] - 1
    odl = od[od.date == last]
    front = (odl[odl.k1_origin.isin(FRONT_K1)].groupby("k1_host")["idp_registered"].sum()
             / odl.groupby("k1_host")["idp_registered"].sum())
    lat["dtm_reg_front_share"] = front
    lat["dtm_reg_female_share"] = lat["dtm_reg_f"] / (lat["dtm_reg_m"] + lat["dtm_reg_f"])

    sv = g[g["op"] == "survey"]
    if len(sv):
        sl = sv["date"].max()
        lat["dtm_svy_latest"] = sv[sv.date == sl].set_index("k1")["idp"]
        lat["dtm_svy_date"] = sl
    lat["dtm_reg_date"] = last
    lat["dtm_reg_base_date"] = base
    lat = lat.reset_index()

    # per 1,000 if oblast context has a population column
    ctx = TIDY / "oblast_context_k1.csv"
    if ctx.exists():
        c = pd.read_csv(ctx, dtype={"k1": str})
        pc = [x for x in c.columns if "pop" in x.lower() and "per" not in x.lower()]
        print(f"oblast_context population candidates: {pc}")
        if pc:
            c["k1"] = c["k1"].str.zfill(2)
            lat = lat.merge(c[["k1", pc[0]]], on="k1", how="left")
            lat["dtm_reg_per1000"] = 1000 * lat["dtm_reg_latest"] / lat[pc[0]]
            if "dtm_svy_latest" in lat:
                lat["dtm_svy_per1000"] = 1000 * lat["dtm_svy_latest"] / lat[pc[0]]

    lat.to_csv(TIDY / "dtm_oblast_latest_k1.csv", index=False)
    pd.set_option("display.width", 200)
    show = [x for x in ("k1", "admin1Name", "dtm_reg_latest", "dtm_reg_change",
                        "dtm_reg_front_share", "dtm_svy_latest", "dtm_reg_per1000",
                        "dtm_svy_per1000") if x in lat]
    print(f"\ndtm_oblast_latest_k1.csv (registration {last}, base {base}):")
    print(lat[show].sort_values("dtm_reg_latest", ascending=False)
             .to_string(index=False, float_format=lambda v: f"{v:,.3f}" if abs(v) < 10 else f"{v:,.0f}"))
    carp = lat[lat.k1.isin(["21", "26", "46", "73"])]
    print("\nCarpathian oblasts:")
    print(carp[show].to_string(index=False, float_format=lambda v: f"{v:,.3f}" if abs(v) < 10 else f"{v:,.0f}"))

    # data dictionary
    dd_fn = TIDY / "data_dictionary.csv"
    src = f"IOM DTM API v3 /displacement/admin1, accessed {accessed}"
    lic = "IOM DTM terms of use (attribution)"
    new = pd.DataFrame([
        ("dtm_reg_latest", src, lic, "persons", last[:4], "oblast",
         "IDPs registered in host oblast (Registration operation), latest month"),
        ("dtm_reg_change", src, lic, "ratio-1", f"{base[:4]}-{last[:4]}", "oblast",
         f"change in registered IDPs {base} to {last}"),
        ("dtm_reg_front_share", src, lic, "share", last[:4], "oblast",
         "share of registered IDPs originating in Donetsk, Luhansk, Zaporizhzhia, Kherson, Kharkiv, Crimea, Sevastopol"),
        ("dtm_reg_female_share", src, lic, "share", last[:4], "oblast",
         "female share of registered IDPs"),
        ("dtm_svy_latest", src, lic, "persons", "", "oblast",
         "IDPs present, General Population Survey, latest round (not comparable with registration)"),
        ("dtm_oblast_od", src, lic, "persons", "2022-2026", "oblast x oblast x month",
         "registered IDPs by host and origin oblast, monthly (tidy/dtm_oblast_od_k1.csv)"),
    ], columns=["indicator", "source", "licence", "unit", "year", "level", "method"])
    if dd_fn.exists():
        dd = pd.read_csv(dd_fn)
        dd = dd[~dd["indicator"].astype(str).str.startswith("dtm_")]
        for col in dd.columns:
            if col not in new:
                new[col] = ""
        dd = pd.concat([dd, new[dd.columns]], ignore_index=True)
    else:
        dd = new
    dd.to_csv(dd_fn, index=False)
    print(f"\ndata_dictionary.csv: {len(dd)} rows ({len(new)} dtm_*)")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "probe"
    if cmd == "probe":
        probe()
    elif cmd == "pull":
        pull(refresh="--refresh" in sys.argv)
    elif cmd == "tidy":
        tidy()
    else:
        sys.exit(__doc__)
