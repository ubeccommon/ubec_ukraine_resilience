#!/usr/bin/env python3
"""
19_nl_monthly.py — monthly Black Marble VNP46A3 (Collection 2) panel, 2020-01 … latest.

  python 19_nl_monthly.py status [--from 2021-01] [--to 2026-08]
  python 19_nl_monthly.py pull   [--from 2021-01] [--to 2026-08]
  python 19_nl_monthly.py zonal  [--from 2020-01] [--to 2026-08]

Reuses 04_nightlights.py: tile_files, load_units, zonal_month, lit mask (pixels lit in
2021, mean >= LIT_THRESHOLD), label rasters and the per-month cache
tidy/ntl_cache/ntl_<tag>_<CACHE_V>_YYYYMM.csv (shared with 04 — nothing recomputed).
zonal only processes months whose 6 tiles are on disk (never downloads).

Outputs:
  tidy/nightlights_panel_k3.csv — k3 x month, lit-pixel radiance, rad_base, n_base, ntl_idx
    rad_base = mean of the same calendar month in 2020 and 2021 (each year counted only if
               valid_frac_lit >= 0.5 and radiance > 0.05); n_base = years used (1 or 2)
    ntl_idx  = radiance / rad_base, valid only if n_lit >= MIN_LIT_PIX, valid_frac_lit >= 0.5
  tidy/nightlights_noise_k3.csv — pre-war noise per hromada:
    noise_sd = SD over months of log(radiance 2021 / radiance 2020), >= 6 valid month pairs
Biases: blackouts and lighting policy (curfews, dimming) both lower radiance; 2020 includes
COVID restrictions (spring 2020; street lighting largely unaffected); snow-covered composite
used where snow-free is missing; short summer nights reduce valid observations.
Licence: NASA Black Marble, public domain.
"""
import sys, argparse, importlib, time, shutil
from datetime import date
from pathlib import Path
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
if "__name__" not in (BASE / "04_nightlights.py").read_text():
    sys.exit("04_nightlights.py has no __main__ guard — importing it would run it")
sys.path.insert(0, str(BASE))
nl = importlib.import_module("04_nightlights")
NT = len(nl.TILES)
TIDY = BASE / "tidy"
CTRL = BASE.parent / "viina" / "qgis" / "hromada_control.gpkg"
OUT = TIDY / "nightlights_panel_k3.csv"
NOISE = TIDY / "nightlights_noise_k3.csv"
CARP = {"21", "26", "46", "73"}
BASE_YEARS = (2020, 2021)


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def months(frm, to):
    y, m = map(int, frm.split("-"))
    ye, me = map(int, to.split("-"))
    out = []
    while (y, m) <= (ye, me):
        out.append((y, m))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def doy1(y, m):
    return date(y, m, 1).timetuple().tm_yday


def files_for(y, m):
    return sorted(nl.RAW.rglob(f"VNP46A3.A{y}{doy1(y, m):03d}.*.h5"))


def default_to():
    t = date.today()
    return f"{t.year - (t.month == 1)}-{12 if t.month == 1 else t.month - 1:02d}"


# ------------------------------------------------------------ status / pull
def cmd_status(a):
    tot_n, tot_b, rows = 0, 0, []
    ms = months(a.frm, a.to)
    for y, m in ms:
        f = files_for(y, m)
        b = sum(p.stat().st_size for p in f)
        tot_n += len(f); tot_b += b
        rows.append(f"{y}-{m:02d} {len(f)}/{NT} {b/1e6:7.0f} MB")
    print("\n".join(rows))
    done = sum(len(files_for(y, m)) == NT for y, m in ms)
    print(f"complete months {done}/{len(ms)}, files {tot_n}, {tot_b/1e9:.1f} GB; "
          f"disk free {shutil.disk_usage(nl.RAW).free/1e9:.0f} GB")


def cmd_pull(a):
    ms = months(a.frm, a.to)
    todo = [(y, m) for y, m in ms if len(files_for(y, m)) < NT]
    log(f"{len(ms)} months {a.frm} … {a.to}; {len(todo)} incomplete")
    fails, unpublished = 0, []
    for i, (y, m) in enumerate(todo, 1):
        t0 = time.time()
        try:
            nl.tile_files(y, m, download=True)
        except SystemExit as e:
            log(f"{y}-{m:02d} stopped: {e}"); break
        except Exception as e:
            msg = repr(e)[:200]
            log(f"{y}-{m:02d} ERROR {msg}")
            if "401" in msg or "Unauthorized" in msg:
                log("token rejected — refresh ~/.earthdata_token and rerun (resumes)"); break
            fails += 1
            if fails >= 3:
                log("3 consecutive errors — stopping; rerun to resume"); break
            continue
        n = len(files_for(y, m))
        fails = 0
        if n == 0:
            unpublished.append(f"{y}-{m:02d}")
        log(f"[{i}/{len(todo)}] {y}-{m:02d} {n}/{NT} tiles ({time.time()-t0:.0f}s)")
    if unpublished:
        log(f"not (yet) published on LAADS: {unpublished}")
    cmd_status(a)


# ------------------------------------------------------------ zonal
def occupied_k3():
    try:
        import pyogrio
        c = pyogrio.read_dataframe(CTRL, read_geometry=False)
        c["k3"] = c["k3"].astype(str).str.zfill(7)
        return set(c.loc[c["occupied"].fillna(0).astype(int) == 1, "k3"])
    except Exception as e:
        log(f"occupied flag not read ({e}); summary over all units")
        return set()


def valid_val(df):
    return df["mean_radiance_lit"].where((df["valid_frac_lit"] >= 0.5) &
                                         (df["mean_radiance_lit"] > 0.05))


def cmd_zonal(a):
    gdf, tag = nl.load_units()
    frames, missing, new = [], [], 0
    for y, m in months(a.frm, a.to):
        p = nl.CACHE / f"ntl_{tag}_{nl.CACHE_V}_{y}{m:02d}.csv"
        if p.exists():
            frames.append(pd.read_csv(p, dtype={"k3": str}))
            continue
        if len(files_for(y, m)) < NT:
            missing.append(f"{y}-{m:02d}")
            continue
        log(f"zonal {y}-{m:02d}")
        df = nl.zonal_month(gdf, tag, y, m)
        if df is None or df["mean_radiance"].notna().sum() == 0:
            log("  no valid values — not cached")
            continue
        df.to_csv(p, index=False)
        frames.append(df); new += 1
        log(f"  lit: units >= {nl.MIN_LIT_PIX} px {int((df['n_lit'] >= nl.MIN_LIT_PIX).sum())}, "
            f"valid {df['valid_frac_lit'].median():.2f}, snow {df['snow_frac'].median():.2f}, "
            f"mean {df['mean_radiance_lit'].mean():.2f}")
    if missing:
        log(f"months without 6 tiles on disk (skipped): {len(missing)} — {missing[:6]}"
            f"{' …' if len(missing) > 6 else ''}")
    if not frames:
        sys.exit("no months available")
    d = pd.concat(frames, ignore_index=True)
    d["k3"] = d["k3"].astype(str).str.zfill(7)
    d = d[["k3", "year", "month", "mean_radiance_lit", "n_lit", "valid_frac_lit", "snow_frac"]]
    d = d.drop_duplicates(["k3", "year", "month"])
    log(f"months in panel: {d.groupby(['year', 'month']).ngroups} ({new} newly computed)")

    # --- baseline: same calendar month, mean of 2020 and 2021
    b = d[d["year"].isin(BASE_YEARS)].copy()
    b["v"] = valid_val(b)
    base = (b.groupby(["k3", "month"])
              .agg(rad_base=("v", "mean"), n_base=("v", "count")).reset_index())
    have_years = sorted(b["year"].unique())
    if 2021 not in have_years:
        sys.exit("2021 months missing — cannot build baseline")
    d = d.merge(base, on=["k3", "month"], how="left")
    d["n_base"] = d["n_base"].fillna(0).astype(int)
    ok = ((d["n_lit"] >= nl.MIN_LIT_PIX) & (d["valid_frac_lit"] >= 0.5) &
          (d["n_base"] >= 1) & (d["rad_base"] > 0.05))
    d["ntl_idx"] = np.where(ok, d["mean_radiance_lit"] / d["rad_base"], np.nan)
    d["date"] = d["year"].astype(str) + "-" + d["month"].astype(int).map("{:02d}".format)
    d = d.sort_values(["k3", "date"])
    d.to_csv(OUT, index=False)
    log(f"wrote {OUT.relative_to(BASE)} rows={len(d)} units={d['k3'].nunique()} "
        f"(base years present: {have_years})")

    # --- pre-war noise per unit: log(2021/2020) across months
    occ = occupied_k3()
    if 2020 in have_years:
        pv = b.pivot_table(index=["k3", "month"], columns="year", values="v")
        if 2020 in pv and 2021 in pv:
            lr = np.log(pv[2021] / pv[2020]).replace([np.inf, -np.inf], np.nan).dropna()
            nz = lr.groupby(level="k3").agg(["std", "count"]).rename(
                columns={"std": "noise_sd", "count": "n_pairs"})
            nz.loc[nz["n_pairs"] < 6, "noise_sd"] = np.nan
            nz["mean_lr_2120"] = lr.groupby(level="k3").mean()
            nz.reset_index().to_csv(NOISE, index=False)
            nn = nz[~nz.index.isin(occ)]
            log(f"wrote {NOISE.relative_to(BASE)}: units with noise_sd {nn['noise_sd'].notna().sum()}, "
                f"median SD(log 2021/2020) {nn['noise_sd'].median():.3f} "
                f"(p90 {nn['noise_sd'].quantile(.9):.3f}); median mean log ratio "
                f"{nn['mean_lr_2120'].median():+.3f}")
    else:
        log("2020 months not yet processed — single-year baseline; noise file not written")

    s = d[~d["k3"].isin(occ)].copy()
    s["carp"] = s["k3"].str[:2].isin(CARP)
    two = s.drop_duplicates(["k3", "month"])
    log(f"non-occupied unit-months with 2-year baseline: {(two['n_base'] == 2).mean():.1%}")
    j22 = s.loc[s["date"] == "2022-01", "ntl_idx"]
    if j22.notna().any():
        log(f"pre-invasion check Jan 2022: median {j22.median():.2f}, "
            f"IQR {j22.quantile(.25):.2f}–{j22.quantile(.75):.2f}")

    rows = []
    for dt, g in s.groupby("date"):
        x = g["ntl_idx"]
        rows.append({"date": dt, "n_idx": int(x.notna().sum()),
                     "p25": x.quantile(.25), "median": x.median(), "p75": x.quantile(.75),
                     "carp_med": g.loc[g["carp"], "ntl_idx"].median(),
                     "valid": g["valid_frac_lit"].median(), "snow": g["snow_frac"].mean()})
    t = pd.DataFrame(rows)
    pd.set_option("display.width", 160)
    print("\nnon-occupied hromadas, ntl_idx = lit radiance / mean same month 2020–21 (snow = mean):")
    print(t.to_string(index=False, float_format=lambda v: f"{v:.2f}"))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["status", "pull", "zonal"])
    ap.add_argument("--from", dest="frm", default=None)
    ap.add_argument("--to", default=default_to())
    a = ap.parse_args()
    if a.frm is None:
        a.frm = "2020-01" if a.cmd == "zonal" else "2021-01"
    {"status": cmd_status, "pull": cmd_pull, "zonal": cmd_zonal}[a.cmd](a)
