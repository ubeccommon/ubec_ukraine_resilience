#!/usr/bin/env python3
"""
18_dtm_hromada.py — join a hromada- (ADM3) or raion- (ADM2) level IDP file
from IOM DTM (on request; not in the API) to the k3 / k2 keys.

  python 18_dtm_hromada.py selftest
      synthetic file -> full join -> report -> synthetic outputs deleted
  python 18_dtm_hromada.py join FILE [--sheet S] [--pcode-col C] [--value-col V]
                                     [--date YYYY-MM] [--tag T]
      FILE: csv/xlsx in raw/dtm_iom/. P-code column and IDP value column are
      auto-detected (override with --pcode-col / --value-col).
      Output: tidy/dtm_hromada_k3{T}.csv or tidy/dtm_raion_k2{T}.csv

P-codes: COD "UA"+k3 (UA2602003) or full KATOTTH (UA26...17 digits); first 7
digits = k3, first 4 = k2. Denominator: GHS-POP 2020 (pre-war) — IDPs per 1,000
pre-war residents, not per current residents.
Licence: IOM DTM data-sharing terms of the file received; attribution required.
"""
import sys, re, argparse
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
TIDY = ROOT / "tidy"
RAWI = ROOT / "raw" / "dtm_iom"
RAWI.mkdir(parents=True, exist_ok=True)
RES = TIDY / "resilience_v1_k3.csv"
CTRL = ROOT.parent / "viina" / "qgis" / "hromada_control.gpkg"
OBL = TIDY / "dtm_oblast_latest_k1.csv"
CARP = ["21", "26", "46", "73"]
PC_RE = re.compile(r"^UA\d{4,}")


# ------------------------------------------------------------ universe
def universe():
    r = pd.read_csv(RES, dtype={"k3": str, "k2": str, "k1": str})
    if "k3" not in r:
        sys.exit(f"no k3 in {RES.name}: {list(r.columns)}")
    r["k3"] = r["k3"].str.zfill(7)
    r["k2"] = r["k3"].str[:4]
    r["k1"] = r["k3"].str[:2]
    pc = [c for c in r.columns if "pop" in c.lower() and "2020" in c]
    if not pc:
        sys.exit(f"no 2020 population column in {RES.name}: "
                 f"{[c for c in r.columns if 'pop' in c.lower()]}")
    pop = pc[0]
    if "occupied" not in r:
        import pyogrio
        c = pyogrio.read_dataframe(CTRL, read_geometry=False)
        c["k3"] = c["k3"].astype(str).str.zfill(7)
        r = r.merge(c[["k3", "occupied"]], on="k3", how="left")
    r["occupied"] = r["occupied"].fillna(0).astype(int)
    print(f"universe: {len(r)} hromadas ({(r.occupied == 0).sum()} non-occupied), "
          f"population column '{pop}'")
    return r[["k1", "k2", "k3", "occupied", pop]].rename(columns={pop: "pop2020"})


# ------------------------------------------------------------ reading
def read_any(path, sheet=None):
    p = Path(path)
    if p.suffix.lower() in (".xlsx", ".xls"):
        xl = pd.ExcelFile(p)
        print(f"sheets: {xl.sheet_names}")
        sh = sheet or xl.sheet_names[0]
        # find header row: first row with >= 3 non-null cells in first 15 rows
        head = pd.read_excel(p, sheet_name=sh, header=None, nrows=15)
        hdr = next((i for i, row in head.iterrows() if row.notna().sum() >= 3), 0)
        return pd.read_excel(p, sheet_name=sh, header=hdr)
    return pd.read_csv(p, sep=None, engine="python", encoding="utf-8-sig")


def pick_pcode(df, forced=None):
    if forced:
        return forced
    cands = []
    for c in df.columns:
        s = df[c].dropna().astype(str).str.strip()
        if len(s) and s.str.match(PC_RE).mean() > 0.8:
            digits = s.str.replace(r"\D", "", regex=True).str.len().median()
            cands.append((c, s.nunique(), digits))
    if not cands:
        sys.exit(f"no P-code column found; columns: {list(df.columns)}")
    print("P-code candidates (col, distinct, median digits):", cands)
    return max(cands, key=lambda t: (t[2] >= 7, t[1]))[0]


def pick_value(df, forced=None):
    if forced:
        return forced
    num = [c for c in df.columns if pd.to_numeric(df[c], errors="coerce").notna().mean() > 0.8]
    idp = [c for c in num if "idp" in str(c).lower()
           and not any(w in str(c).lower() for w in ("hh", "household", "%", "pct", "share"))]
    if len(idp) == 1:
        return idp[0]
    sys.exit(f"cannot choose value column; numeric: {num}; idp-like: {idp}. "
             f"Use --value-col")


# ------------------------------------------------------------ join
def join(path, sheet=None, pcol=None, vcol=None, date=None, tag=""):
    u = universe()
    df = read_any(path, sheet)
    print(f"file: {Path(path).name}, {len(df)} rows, columns: {list(df.columns)[:15]}")
    pcol = pick_pcode(df, pcol)
    vcol = pick_value(df, vcol)
    print(f"using P-code '{pcol}', value '{vcol}'")

    d = df[[pcol, vcol]].copy()
    d["digits"] = d[pcol].astype(str).str.replace(r"\D", "", regex=True)
    d["val"] = pd.to_numeric(d[vcol], errors="coerce")
    nd = d["digits"].str.len().median()
    level = "k3" if nd >= 7 else "k2"
    d[level] = d["digits"].str[: 7 if level == "k3" else 4]
    print(f"level: {'hromada (ADM3)' if level == 'k3' else 'raion (ADM2)'}; "
          f"{d[level].nunique()} units, {d['val'].isna().sum()} missing values, "
          f"{d.duplicated(level).sum()} duplicate keys (summed)")
    g = d.groupby(level)["val"].sum(min_count=1).rename("idp").reset_index()

    base = u if level == "k3" else (u.groupby(["k1", "k2"])
                                      .agg(pop2020=("pop2020", "sum"),
                                           occupied=("occupied", "max"),
                                           n_hromada=("k3", "size")).reset_index())
    unmatched = sorted(set(g[level]) - set(base[level]))
    print(f"matched {len(g) - len(unmatched)}/{len(g)}; unmatched sample: {unmatched[:10]}")

    m = base.merge(g, on=level, how="left")
    m["idp_per1000"] = 1000 * m["idp"] / m["pop2020"].replace(0, np.nan)
    m["dtm_date"] = date or ""
    no = m[m.occupied == 0]
    print(f"coverage non-occupied: {no['idp'].notna().sum()}/{len(no)} "
          f"({no['idp'].notna().mean():.1%}); zeros: {(no['idp'] == 0).sum()}")

    # oblast check vs survey totals
    if OBL.exists():
        o = pd.read_csv(OBL, dtype={"k1": str})
        o = o[o.k1.str.fullmatch(r"\d\d", na=False)]
        s = m.groupby("k1")["idp"].sum(min_count=1).rename("sum_file")
        chk = o.set_index("k1")[["admin1Name", "dtm_svy_latest", "dtm_reg_latest"]].join(s)
        chk["file/svy"] = chk["sum_file"] / chk["dtm_svy_latest"]
        chk["file/reg"] = chk["sum_file"] / chk["dtm_reg_latest"]
        print("\noblast sums vs API (survey = present; registration = registered):")
        print(chk.sort_values("sum_file", ascending=False)
                 .to_string(float_format=lambda v: f"{v:,.2f}" if v < 10 else f"{v:,.0f}"))

    q = no["idp_per1000"].describe(percentiles=[.1, .5, .9])
    print(f"\nidp_per1000 (non-occupied): median {q['50%']:.1f}, p10 {q['10%']:.1f}, "
          f"p90 {q['90%']:.1f}, max {q['max']:.1f}")
    cz = no[no.k1.isin(CARP)]
    print("Carpathian oblasts, per-1000 median / p90 / units with data:")
    print(cz.groupby("k1")["idp_per1000"].agg(["median", lambda x: x.quantile(.9), "count"])
            .rename(columns={"<lambda_0>": "p90"}).to_string(float_format=lambda v: f"{v:.1f}"))

    out = TIDY / (f"dtm_hromada_k3{tag}.csv" if level == "k3" else f"dtm_raion_k2{tag}.csv")
    m.to_csv(out, index=False)
    print(f"\nwrote {out.name} ({len(m)} rows)")
    return out


# ------------------------------------------------------------ selftest
def selftest():
    u = universe()
    rng = np.random.default_rng(42)
    per = 0.09
    if OBL.exists():
        o = pd.read_csv(OBL, dtype={"k1": str}).set_index("k1")
        per = (o["dtm_svy_latest"] / o["pop_ghs_2020"]).dropna() if "pop_ghs_2020" in o else per
    syn = u[u.occupied == 0].copy()
    rate = syn["k1"].map(per).fillna(0.08) if isinstance(per, pd.Series) else per
    syn["IDPs (individuals)"] = np.round(syn["pop2020"] * rate *
                                         rng.lognormal(0, 0.5, len(syn))).astype(int)
    syn["IDPs (households)"] = (syn["IDPs (individuals)"] / 2.4).round().astype(int)
    syn["ADM3_PCODE"] = "UA" + syn["k3"]
    syn["ADM2_PCODE"] = "UA" + syn["k2"]
    syn["ADM1_PCODE"] = "UA" + syn["k1"]
    syn = syn.sample(frac=0.95, random_state=1)  # simulate 5 % missing
    fn = RAWI / "_SYNTHETIC_selftest.csv"
    syn[["ADM1_PCODE", "ADM2_PCODE", "ADM3_PCODE", "IDPs (individuals)",
         "IDPs (households)"]].to_csv(fn, index=False)
    print(f"== SYNTHETIC file {fn.name} ({len(syn)} rows) — not real data\n")
    try:
        out = join(fn, tag="_SELFTEST")
        print("\n== raion variant")
        r = syn.groupby("ADM2_PCODE")["IDPs (individuals)"].sum().reset_index()
        fr = RAWI / "_SYNTHETIC_selftest_raion.csv"
        r.to_csv(fr, index=False)
        out2 = join(fr, tag="_SELFTEST")
    finally:
        for f in [fn, RAWI / "_SYNTHETIC_selftest_raion.csv",
                  TIDY / "dtm_hromada_k3_SELFTEST.csv", TIDY / "dtm_raion_k2_SELFTEST.csv"]:
            f.unlink(missing_ok=True)
        print("\nsynthetic files and outputs deleted")


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("selftest", "join"):
        sys.exit(__doc__)
    if sys.argv[1] == "selftest":
        selftest()
    else:
        ap = argparse.ArgumentParser()
        ap.add_argument("cmd"); ap.add_argument("file")
        ap.add_argument("--sheet"); ap.add_argument("--pcode-col")
        ap.add_argument("--value-col"); ap.add_argument("--date")
        ap.add_argument("--tag", default="")
        a = ap.parse_args()
        join(a.file, a.sheet, a.pcode_col, a.value_col, a.date, a.tag)
