"""26_publication_tables.py — paper Table 1 (coverage and exclusions), Table 3 (exposure descriptives),
Table 5 (capacity × exposure rank correlations), Table 6 (capacity × exposure terciles), Table 12
(Carpathian vs national), the capacity × outage-loss classes (request 37) and the light publication
threshold counts (request 38).

Run from anywhere with the venv Python.
Inputs : viina/qgis/unit_stats_hromada.csv, viina/qgis/hromada_control.gpkg,
         resilience/tidy/trajectories_k3.csv, resilience/tidy/resilience_v1_k3.csv,
         resilience/tidy/resilience_index_v11_k3.csv, resilience/**/units_hromada.gpkg,
         resilience/resilience_maps.gpkg:hromada_bivariate, resilience/tidy/carpathian_profiles_k3.csv,
         resilience/tidy/nightlights_noise_k3.csv
Outputs: publication/figures/table03_exposure.{csv,md}, publication/figures/table11_carpathian.{csv,md},
         publication/figures/table01_coverage.{csv,md}, publication/figures/table01_exclusions.{csv,md},
         publication/figures/table05_correlations.{csv,md}, publication/figures/table06_terciles.{csv,md},
         publication/figures/table06_hilo_oblast.csv, publication/figures/carp_typology.{csv,md},
         publication/figures/light_reliability.csv

Non-occupied hromadas only. Strikes = settlement-precision events since 24 Feb 2022 (n_all, as used in the
models via exp_strikes_log); because most hromadas have none, the share with at least one event is reported
alongside the distribution. Alert hours = fixed 12-month window 1 Sep 2025 – 31 Aug 2026 (alert_h_12m).
Oblast names are standardised from the VIINA transliteration. All outputs are oblast-level or regional
aggregates (rules R1–R6).

Table 1 reproduces the sample rules of 11_composite.py (capacity >= 3 of 4 indicators, recovery >= 1 of 2
light ratios, engagement = DREAM projects per 10k with population >= 100) and 12_moderation.py (model sample =
recovery, capacity and strike exposure present, unit geometry present). Each excluded hromada gets one reason
code per stage; the model stage records the first failing condition.

Table 5: Spearman rho on average ranks; 95 % CI by Fisher z with the Bonett–Wright standard error
sqrt((1 + rho²/2) / (n − 3)), checked against a percentile bootstrap (2,000 draws, seed 26). Within-oblast
values (2025 and 2021 capacity): ranks demeaned within oblast, Pearson correlation of the residuals, degrees
of freedom reduced by the number of oblasts − 1. rho_cap_exp_min/max refer to the 2025 capacity score.

Table 6: counts from the classes drawn on Maps 14, 15 and 17 (13_bivariate.py, codes = exposure tercile +
capacity tercile, 1 = low). Strike classes follow the zero rule of 13: class 1 = no strike, classes 2 and 3
split the struck hromadas at their median. Carpathian panels are shown on national terciles and, for alert
hours, on the regional terciles of Map 17.

Request 37: classes as in 23_carpathian.py — terciles (qcut on first-rank order) of capacity_index and of
tr_s24_rel (summer-2024 light as share of H2 2023; high = kept most light), each over the hromadas with a
value. "weak & hit" = low capacity and low retention; "strong & steady" = high and high. Regional = terciles
within the four Carpathian oblasts (the published definition); national = same rule over all non-occupied.

Request 38: light values are reliable for single-hromada publication if >= 30 pixels lit in 2021 and the
pre-war month-to-month noise (noise_sd, 19_nl_monthly.py) is <= 0.35 (23_carpathian.py)."""
from pathlib import Path
import numpy as np
import pandas as pd
import pyogrio
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "publication" / "figures"
FIG.mkdir(parents=True, exist_ok=True)
CARP = {"21": "Zakarpattia", "26": "Ivano-Frankivsk", "46": "Lviv", "73": "Chernivtsi"}
NAT = "Ukraine (non-occupied)"
KEYS = {"k1": str, "k2": str, "k3": str}
NAMES = {"Cherkasy": "Cherkasy", "Chernihiv": "Chernihiv", "Chernivtsi": "Chernivtsi",
         "Dnipropetrovs'k": "Dnipropetrovsk", "Donets'k": "Donetsk", "Ivano-Frankivs'k": "Ivano-Frankivsk",
         "Kharkiv": "Kharkiv", "Kherson": "Kherson", "Khmel'nyts'kyy": "Khmelnytskyi", "Kiev": "Kyiv",
         "Kiev City": "Kyiv City", "Kirovohrad": "Kirovohrad", "L'viv": "Lviv", "Luhans'k": "Luhansk",
         "Mykolayiv": "Mykolaiv", "Odessa": "Odesa", "Poltava": "Poltava", "Rivne": "Rivne", "Sumy": "Sumy",
         "Ternopil'": "Ternopil", "Transcarpathia": "Zakarpattia", "Vinnytsya": "Vinnytsia", "Volyn": "Volyn",
         "Zaporizhzhya": "Zaporizhzhia", "Zhytomyr": "Zhytomyr"}


def md_lines(df, title, note):
    cols = list(df.columns)
    lines = [f"**{title}**", "", "| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    lines += ["| " + " | ".join(str(x) for x in r) + " |" for r in df.itertuples(index=False)]
    lines += ["", note, ""]
    return lines


def md_table(df, path, title, note):
    lines = md_lines(df, title, note)
    path.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


# --- non-occupied hromadas ------------------------------------------------------------------------
us = pd.read_csv(ROOT / "viina/qgis/unit_stats_hromada.csv", dtype=KEYS)
ctl = pyogrio.read_dataframe(ROOT / "viina/qgis/hromada_control.gpkg", read_geometry=False)[["k3", "occupied"]]
ctl["k3"] = ctl["k3"].astype(str)
d = us.merge(ctl, on="k3", how="left", validate="1:1")
assert d["occupied"].notna().all(), "hromadas without control status"
d = d[~d["occupied"].astype(bool)].copy()
unmapped = sorted(set(d["oblast_en"]) - set(NAMES))
assert not unmapped, f"oblast names without a standard form: {unmapped}"
d["oblast"] = d["oblast_en"].map(NAMES)
print(f"non-occupied hromadas: {len(d):,}")

# --- Table 3: exposure descriptives by oblast -----------------------------------------------------
def desc(g):
    s, a = g["n_all"], g["alert_h_12m"]
    return pd.Series({"hromadas": len(g), "struck_share": 100 * (s > 0).mean(),
                      "strikes_median": s.median(), "strikes_q1": s.quantile(.25), "strikes_q3": s.quantile(.75),
                      "strikes_max": s.max(),
                      "alert_h_median": a.median(), "alert_h_q1": a.quantile(.25), "alert_h_q3": a.quantile(.75),
                      "alert_h_max": a.max()})

t3 = d.groupby("oblast").apply(desc, include_groups=False).sort_index()
t3.loc[NAT] = desc(d)
t3.index.name = "oblast"
t3.round(1).to_csv(FIG / "table03_exposure.csv")

f0 = lambda x: f"{x:,.0f}"
t3md = pd.DataFrame({
    "Oblast": t3.index,
    "Hromadas": t3["hromadas"].map(f0).values,
    "With ≥ 1 strike, %": t3["struck_share"].map(f0).values,
    "Strikes, median": t3["strikes_median"].map(f0).values,
    "Strikes, IQR": [f"{f0(a)}–{f0(b)}" for a, b in zip(t3["strikes_q1"], t3["strikes_q3"])],
    "Strikes, max": t3["strikes_max"].map(f0).values,
    "Alert hours, median": t3["alert_h_median"].map(f0).values,
    "Alert hours, IQR": [f"{f0(a)}–{f0(b)}" for a, b in zip(t3["alert_h_q1"], t3["alert_h_q3"])],
    "Alert hours, max": t3["alert_h_max"].map(f0).values,
})
md_table(t3md, FIG / "table03_exposure.md",
         "Table 3. Exposure of non-occupied hromadas, by oblast",
         "Strikes: VIINA settlement-precision events attributed to Russian forces, 24 Feb 2022 – 19 Sep 2026, per "
         "hromada. Alert hours: hours under air-raid alert, 1 Sep 2025 – 31 Aug 2026 (hromada, raion or oblast "
         "alert; overlaps merged). IQR = interquartile range.")

# --- Table 11: Carpathian vs national -----------------------------------------------------------------
tr = pd.read_csv(ROOT / "resilience/tidy/trajectories_k3.csv", dtype=KEYS)[["k3", "capacity_prewar", "capacity_index"]]
rv = pd.read_csv(ROOT / "resilience/tidy/resilience_v1_k3.csv", dtype=KEYS)[["k3", "ntl_recovery_2124"]]
m = d[["k1", "k3", "n_all", "alert_h_12m"]].merge(tr, on="k3", how="left").merge(rv, on="k3", how="left")
m["struck"] = (m["n_all"] > 0).astype(float)
for c in ("capacity_prewar", "capacity_index"):
    assert m[c].max() <= 1.0, f"{c} not on a 0–1 scale"

# (column, label, statistic, scale, decimals)
MEAS = [("struck", "Hromadas with ≥ 1 strike since 24 Feb 2022, %", "mean", 100, 0),
        ("alert_h_12m", "Alert hours, 1 Sep 2025 – 31 Aug 2026 (median)", "median", 1, 0),
        ("capacity_prewar", "Capacity 2021, mean percentile rank 0–100 (median)", "median", 100, 1),
        ("capacity_index", "Capacity 2025, mean percentile rank 0–100 (median)", "median", 100, 1),
        ("ntl_recovery_2124", "Night-light recovery ratio 2024 / 2021 (median)", "median", 1, 2)]
groups = {**{name: m[m["k1"] == k] for k, name in CARP.items()},
          "Carpathian (4 oblasts)": m[m["k1"].isin(CARP)], NAT: m}

long, wide = [], []
for col, label, stat, scale, dp in MEAS:
    row = {"Measure": label}
    for g, gd in groups.items():
        v = gd[col].dropna()
        val = round(getattr(v, stat)() * scale, dp)
        long.append({"measure": col, "statistic": stat, "group": g, "value": val, "n": len(v)})
        row[g] = f"{val:,.{dp}f} ({len(v):,})"
    wide.append(row)
pd.DataFrame(long).to_csv(FIG / "table11_carpathian.csv", index=False)
md_table(pd.DataFrame(wide), FIG / "table11_carpathian.md",
         "Table 12. Carpathian oblasts and Ukraine, non-occupied hromadas",
         "Number of hromadas with a value in brackets. Capacity: mean percentile rank of the capacity components "
         "(2021 budgets for 2021; 2025 index). Recovery: mean radiance of pixels lit in 2021, 2024 relative to 2021.")

# --- verdict on the paper's three Carpathian claims ---------------------------------------------------
L = pd.DataFrame(long).set_index(["measure", "group"])["value"]
c, n = "Carpathian (4 oblasts)", NAT
yes = lambda b: "yes" if b else "NO"
print("\nclaims (Carpathian vs national):")
print(f"  lower exposure : struck {L['struck', c]} % vs {L['struck', n]} %, alert hours {L['alert_h_12m', c]} vs "
      f"{L['alert_h_12m', n]} -> {yes(L['struck', c] < L['struck', n] and L['alert_h_12m', c] < L['alert_h_12m', n])}")
print(f"  lower capacity : 2021 {L['capacity_prewar', c]} vs {L['capacity_prewar', n]}, 2025 {L['capacity_index', c]} vs "
      f"{L['capacity_index', n]} -> {yes(L['capacity_index', c] < L['capacity_index', n])}")
print(f"  better recovery: region {L['ntl_recovery_2124', c]} vs {L['ntl_recovery_2124', n]} -> "
      f"{yes(L['ntl_recovery_2124', c] > L['ntl_recovery_2124', n])}; by oblast: "
      + ", ".join(f"{g} {L['ntl_recovery_2124', g]}" for g in CARP.values()))

# --- Table 1: coverage and exclusions (request 1) ----------------------------------------------------
print("\n=== Table 1: coverage ===")
TIDY = ROOT / "resilience/tidy"
CAPC = {"own_rev_gf_pc_2025": "own revenue per capita", "transfer_dep_2025": "transfer dependency",
        "capex_share_2325": "capital spending share", "pdfo_civ_growth_rel_2125": "civilian PIT growth"}
LOGC = {"own_rev_gf_pc_2025", "pdfo_civ_growth_rel_2125"}      # log-transformed in 11: values <= 0 drop out
RECC = ["ntl_recovery_2124", "ntl_winter_ratio_2125"]          # both log-transformed in 11
MIN_LIT_PIX, CAP_MIN = 10, 3
CODES = {"cap_lt3": "Capacity: fewer than 3 of 4 indicators",
         "rec_no_ntl": "Recovery: no night-light record",
         "rec_lit_lt10": f"Recovery: fewer than {MIN_LIT_PIX} pixels lit in 2021",
         "rec_no_ratio": "Recovery: no valid annual or winter light ratio",
         "eng_pop_lt100": "Engagement: population denominator missing or < 100",
         "eng_no_dream": "Engagement: no DREAM record",
         "eng_other": "Engagement: other",
         "mod_no_recovery": "Model: no recovery index",
         "mod_no_capacity": "Model: no capacity index",
         "mod_no_exposure": "Model: no strike exposure",
         "mod_no_geometry": "Model: no unit geometry"}

rv1 = pd.read_csv(TIDY / "resilience_v1_k3.csv", dtype=KEYS)
ix = pd.read_csv(TIDY / "resilience_index_v11_k3.csv", dtype=KEYS)
for t in (rv1, ix):
    t["k3"] = t["k3"].str.zfill(7)
    t["k1"] = t["k1"].str.zfill(2)
occ = rv1["occupied"].astype(str).str.lower().isin(["true", "1"])
keep = ["k1", "k3", "ntl_n_lit_px", "pop_ghs_2020", "dream_n", "dream_per10k"] + list(CAPC) + RECC
u = rv1.loc[~occ, keep].merge(
    ix[["k3", "capacity_index", "n_cap", "recovery_index", "n_rec", "engagement_index", "exp_strikes_log",
        "alert_h_12m"]],
    on="k3", how="left", validate="1:1")
print(f"non-occupied (resilience_v1, as 11): {len(u):,}   rows in index file: {len(ix):,}   "
      f"non-occupied (hromada_control.gpkg, Tables 3/11): {len(d):,}")
dk = set(d["k3"].astype(str).str.zfill(7))
only_rv, only_ctl = set(u["k3"]) - dk, dk - set(u["k3"])
if only_rv or only_ctl:
    print(f"  universe difference: {len(only_rv)} only in resilience_v1, {len(only_ctl)} only in control gpkg")

obl = d.assign(k1=d["k1"].astype(str).str.zfill(2)).drop_duplicates("k1").set_index("k1")["oblast"]
missing_k1 = sorted(set(u["k1"]) - set(obl.index))
assert not missing_k1, f"k1 without an oblast name: {missing_k1}"
u["oblast"] = u["k1"].map(obl)

# units with geometry (as the inner join in 12_moderation.py)
gp = [p for p in (ROOT / "resilience").rglob("units_hromada.gpkg") if "raw" not in p.parts]
assert len(gp) == 1, f"units_hromada.gpkg found {len(gp)} times: {gp}"
geo_k3 = set(pyogrio.read_dataframe(gp[0], layer="hromada", read_geometry=False, columns=["k3"])["k3"]
             .astype(str).str.zfill(7))
print(f"unit geometries: {len(geo_k3):,} ({gp[0].relative_to(ROOT)})")

# capacity: which indicators are usable after the 11 transforms
av = pd.DataFrame({c: u[c].notna() & ((u[c] > 0) if c in LOGC else True) for c in CAPC})
u["cap_avail"] = av.sum(axis=1)
chk = u["n_cap"].notna()
mis = (u.loc[chk, "cap_avail"] != u.loc[chk, "n_cap"]).sum()
print(f"capacity indicator check vs 11 n_cap: {mis} mismatches"
      + ("" if mis == 0 else "  <-- reason detail for capacity may be wrong; check the transforms in 11"))
cap_ok_rule = u["cap_avail"] >= CAP_MIN
print(f"capacity rule check: rule {cap_ok_rule.sum():,} vs index {u['capacity_index'].notna().sum():,}")

# recovery: usable light ratios
ra = sum((u[c].notna() & (u[c] > 0)).astype(int) for c in RECC)
chk = u["n_rec"].notna()
mis = (ra[chk] != u.loc[chk, "n_rec"]).sum()
print(f"recovery ratio check vs 11 n_rec: {mis} mismatches")
lit_ge = u["ntl_n_lit_px"] >= MIN_LIT_PIX
print(f"lit >= {MIN_LIT_PIX} but no recovery: {(lit_ge & u['recovery_index'].isna()).sum()}   "
      f"lit < {MIN_LIT_PIX} with recovery: {(~lit_ge & u['recovery_index'].notna()).sum()}")

rows = []
for i, r in u.iterrows():
    base = {"k1": r["k1"], "oblast": r["oblast"]}
    if pd.isna(r["capacity_index"]):
        miss = ", ".join(CAPC[c] for c in CAPC if not av.at[i, c])
        rows.append({**base, "stage": "capacity", "code": "cap_lt3", "detail": f"missing: {miss or 'none'}"})
    if pd.isna(r["recovery_index"]):
        if pd.isna(r["ntl_n_lit_px"]):
            code = "rec_no_ntl"
        elif r["ntl_n_lit_px"] < MIN_LIT_PIX:
            code = "rec_lit_lt10"
        else:
            code = "rec_no_ratio"
        rows.append({**base, "stage": "recovery", "code": code, "detail": ""})
    if pd.isna(r["engagement_index"]):
        if pd.isna(r["pop_ghs_2020"]) or r["pop_ghs_2020"] < 100:
            code = "eng_pop_lt100"
        elif pd.isna(r["dream_n"]):
            code = "eng_no_dream"
        else:
            code = "eng_other"
        rows.append({**base, "stage": "engagement", "code": code, "detail": ""})
    for cond, code in ((pd.isna(r["recovery_index"]), "mod_no_recovery"),
                       (pd.isna(r["capacity_index"]), "mod_no_capacity"),
                       (pd.isna(r["exp_strikes_log"]), "mod_no_exposure"),
                       (r["k3"] not in geo_k3, "mod_no_geometry")):
        if cond:
            rows.append({**base, "stage": "model", "code": code, "detail": ""})
            break
ex = pd.DataFrame(rows, columns=["k1", "oblast", "stage", "code", "detail"])

u["in_model"] = (u["recovery_index"].notna() & u["capacity_index"].notna() & u["exp_strikes_log"].notna()
                 & u["k3"].isin(geo_k3))

# coverage by oblast
def cov(g):
    return pd.Series({"non_occupied": len(g), "capacity": g["capacity_index"].notna().sum(),
                      "recovery": g["recovery_index"].notna().sum(),
                      "engagement": g["engagement_index"].notna().sum(), "model": g["in_model"].sum()})

cols = ["capacity_index", "recovery_index", "engagement_index", "in_model"]
t1 = pd.DataFrame({ob: cov(g) for ob, g in u.groupby("oblast")[cols]}).T.sort_index()
t1.loc["Carpathian (4 oblasts)"] = cov(u.loc[u["k1"].isin(CARP), cols])
t1.loc[NAT] = cov(u[cols])
t1 = t1.astype(int)
t1.index.name = "oblast"
t1.to_csv(FIG / "table01_coverage.csv")
md_table(pd.DataFrame({"Oblast": t1.index, "Non-occupied": t1["non_occupied"].map(f0).values,
                       "Capacity": t1["capacity"].map(f0).values, "Recovery": t1["recovery"].map(f0).values,
                       "Engagement": t1["engagement"].map(f0).values, "Model sample": t1["model"].map(f0).values}),
         FIG / "table01_coverage.md",
         "Table 1. Coverage of non-occupied hromadas, by oblast",
         f"Capacity: at least {CAP_MIN} of 4 budget indicators. Recovery: at least one of the annual (2024/2021) "
         f"and winter (2024–25/2020–21) night-light ratios, from pixels lit in 2021 (≥ {MIN_LIT_PIX} pixels). "
         "Engagement: DREAM projects per 10,000 residents (GHS-POP 2020 ≥ 100). Model sample: recovery, capacity "
         "and strike exposure all present. Exclusion reasons in Table 1b.")

# exclusions: long (with capacity detail) and oblast x reason
exl = (ex.groupby(["stage", "code", "detail", "oblast"]).size().rename("hromadas").reset_index())
exl["label"] = exl["code"].map(CODES)
exl.to_csv(FIG / "table01_exclusions.csv", index=False)
xt = pd.crosstab(ex["oblast"], ex["code"])
order = [c for c in CODES if c in xt.columns]
xt = xt[order]
xt.loc[NAT] = xt.sum()
md_table(pd.concat([pd.Series(xt.index, name="Oblast"), xt.reset_index(drop=True).map(f0)], axis=1),
         FIG / "table01_exclusions.md",
         "Table 1b. Excluded non-occupied hromadas, by oblast and reason",
         "Codes: " + "; ".join(f"{c} = {CODES[c]}" for c in order) + ". Oblasts without exclusions are omitted. "
         "Stages overlap: a hromada without a recovery index is counted under rec_* and under mod_no_recovery. "
         "The model stage records only the first failing condition.")

print("\ncapacity exclusions, missing indicators:")
print(ex.loc[ex["stage"] == "capacity", "detail"].value_counts().to_string())
print("\nnumbers.yaml:")
print(f'  n_nonocc: "{len(u):,}"')
print(f'  n_capacity: "{u["capacity_index"].notna().sum():,}"')
print(f'  n_recovery: "{u["recovery_index"].notna().sum():,}"')
print(f'  n_engagement: "{u["engagement_index"].notna().sum():,}"')
print(f'  n_model: "{int(u["in_model"].sum()):,}"')

# --- Table 5: capacity x exposure rank correlations (request 8) --------------------------------------
print("\n=== Table 5: capacity x exposure ===")
B, SEED = 2000, 26
pre = pd.read_csv(TIDY / "trajectories_k3.csv", dtype=KEYS)[["k3", "capacity_prewar"]]
pre["k3"] = pre["k3"].str.zfill(7)
c5 = u[["k1", "k3", "capacity_index", "exp_strikes_log", "alert_h_12m"]].merge(
    pre, on="k3", how="left", validate="1:1")


def fisher_ci(r, n, k=0):
    se = np.sqrt((1 + r ** 2 / 2) / (n - 3 - k))
    lo, hi = np.tanh(np.arctanh(r) + np.array([-1.96, 1.96]) * se)
    return lo, hi


def rho_row(cap, exp, within=False):
    s = c5[["k1", cap, exp]].dropna()
    rx, ry = rankdata(s[cap]), rankdata(s[exp])
    n, k = len(s), 0
    if within:
        g = s["k1"].to_numpy()
        rx = rx - pd.Series(rx).groupby(g).transform("mean").to_numpy()
        ry = ry - pd.Series(ry).groupby(g).transform("mean").to_numpy()
        k = s["k1"].nunique() - 1
    r = float(np.corrcoef(rx, ry)[0, 1])
    lo, hi = fisher_ci(r, n, k)
    bl = bh = np.nan
    if not within:
        rng = np.random.default_rng(SEED)
        xv, yv = s[cap].to_numpy(), s[exp].to_numpy()
        bs = np.empty(B)
        for b in range(B):
            j = rng.integers(0, n, n)
            bs[b] = np.corrcoef(rankdata(xv[j]), rankdata(yv[j]))[0, 1]
        bl, bh = np.quantile(bs, [0.025, 0.975])
    return {"capacity": cap, "exposure": exp, "scope": "within oblasts" if within else "national",
            "rho": r, "ci_lo": lo, "ci_hi": hi, "n": n, "oblasts": s["k1"].nunique(), "boot_lo": bl, "boot_hi": bh}


EXPS = {"exp_strikes_log": "strikes", "alert_h_12m": "alerts"}
CAPS = {"capacity_index": "2025", "capacity_prewar": "2021"}
res = [rho_row(cap, e) for cap in CAPS for e in EXPS]
res += [rho_row(cap, e, within=True) for cap in CAPS for e in EXPS]
t5 = pd.DataFrame(res)
t5.round(4).to_csv(FIG / "table05_correlations.csv", index=False)
print(t5.round(3).to_string(index=False))

mn = lambda x: f"{x:.2f}".replace("-", "−")
ci = lambda r: f"{mn(r['ci_lo'])}, {mn(r['ci_hi'])}"
get = lambda cap, e, sc="national": t5[(t5.capacity == cap) & (t5.exposure == e) & (t5.scope == sc)].iloc[0]
cell = lambda cap, e, sc="national": f"{mn(get(cap, e, sc)['rho'])} [{ci(get(cap, e, sc))}]"
W = "within oblasts"
md_table(pd.DataFrame({
    "": ["Capacity 2025", "Capacity 2021 (pre-war)", "Capacity 2025, within oblasts",
         "Capacity 2021 (pre-war), within oblasts"],
    "Strike exposure": [cell("capacity_index", "exp_strikes_log"), cell("capacity_prewar", "exp_strikes_log"),
                        cell("capacity_index", "exp_strikes_log", W), cell("capacity_prewar", "exp_strikes_log", W)],
    "Alert hours": [cell("capacity_index", "alert_h_12m"), cell("capacity_prewar", "alert_h_12m"),
                    cell("capacity_index", "alert_h_12m", W), cell("capacity_prewar", "alert_h_12m", W)]}),
    FIG / "table05_correlations.md",
    "Table 5. Rank correlations between fiscal capacity and exposure",
    f"Spearman ρ with 95 % confidence intervals (Fisher z, Bonett–Wright standard error). n = "
    f"{get('capacity_index', 'alert_h_12m')['n']:,} for capacity 2025 and "
    f"{get('capacity_prewar', 'alert_h_12m')['n']:,} for capacity 2021. Within-oblast values are partial "
    "correlations after removing oblast means of the ranks. Strike exposure: all events since 24 Feb 2022; "
    "alert hours: 1 Sep 2025 – 31 Aug 2026.")

print("\nnumbers.yaml:")
for cap, yr in CAPS.items():
    for e, lab in EXPS.items():
        r = get(cap, e)
        print(f'  rho_cap_{lab}_{yr}: "{mn(r["rho"])}"')
        print(f'  ci_cap_{lab}_{yr}: "{ci(r)}"')
for cap, yr in CAPS.items():
    for e, lab in EXPS.items():
        r = get(cap, e, W)
        key = f"rho_cap_{lab}_within" if yr == "2025" else f"rho_cap_{lab}_2021_within"
        print(f'  {key}: "{mn(r["rho"])}"   # CI {ci(r)}')
nat25 = t5[(t5.scope == "national") & (t5.capacity == "capacity_index")]["rho"]
print(f'  rho_cap_exp_min: "{mn(nat25.min())}"')
print(f'  rho_cap_exp_max: "{mn(nat25.max())}"')

# --- Table 6: capacity x exposure terciles (request 26) ----------------------------------------------
print("\n=== Table 6: tercile cross-tab ===")
bv = pyogrio.read_dataframe(ROOT / "resilience/resilience_maps.gpkg", layer="hromada_bivariate",
                            read_geometry=False)[["k3", "bv_alt", "bv_str", "bv_carp", "carp", "occupied"]]
bv["k3"] = bv["k3"].astype(str).str.zfill(7)
bv = bv[bv["occupied"] == 0].merge(u[["k3", "oblast"]], on="k3", how="left", validate="1:1")
assert len(bv) == len(u) and bv["oblast"].notna().all(), "bivariate layer and index universe differ"
carp = bv["carp"] == 1
print(f"bivariate layer, non-occupied: {len(bv):,} (Carpathian {int(carp.sum())})")
print(f"strike class 1 (no strike): {(bv['bv_str'].str[0] == '1').sum():,}   "
      f"struck, split at median: {bv['bv_str'].str.fullmatch(r'[23][123]').sum():,}")

EXP_LAB = {"3": "High exposure", "2": "Middle", "1": "Low exposure"}
CAP_LAB = {"1": "Low capacity", "2": "Middle", "3": "High capacity"}
PANELS = [("alerts_national", "bv_alt", slice(None), "Alert hours, national terciles, Ukraine (non-occupied)"),
          ("strikes_national", "bv_str", slice(None), "Strike exposure, national classes, Ukraine (non-occupied)"),
          ("alerts_carp", "bv_alt", carp, "Alert hours, national terciles, Carpathian oblasts"),
          ("strikes_carp", "bv_str", carp, "Strike exposure, national classes, Carpathian oblasts"),
          ("alerts_carp_regional", "bv_carp", carp, "Alert hours, regional terciles (Map 17), Carpathian oblasts")]


def grid(codes):
    ok = codes.str.fullmatch(r"[123][123]")
    c = codes[ok]
    g = pd.crosstab(c.str[0], c.str[1]).reindex(index=list("321"), columns=list("123"), fill_value=0)
    return g, int((~ok).sum())


t6long, md6, hilo = [], [], {}
for key, col, sel, title in PANELS:
    g, unc = grid(bv.loc[sel, col])
    hilo[key] = int(g.loc["3", "1"])
    for e in "321":
        for c_ in "123":
            t6long.append({"panel": key, "exposure_class": e, "capacity_class": c_, "hromadas": int(g.loc[e, c_])})
    tab = pd.DataFrame({"": [EXP_LAB[e] for e in "321"],
                        **{CAP_LAB[c_]: [f0(g.loc[e, c_]) for e in "321"] for c_ in "123"}})
    md6 += md_lines(tab, title, f"n = {int(g.values.sum()):,} classified" + (f"; {unc} without a class." if unc else "."))
pd.DataFrame(t6long).to_csv(FIG / "table06_terciles.csv", index=False)
note = ("Classes as drawn on Maps 14, 15 and 17 (codes = exposure class + capacity class; 1 = low). Capacity "
        "and alert hours: terciles among non-occupied hromadas. Strikes: low = no strike since 24 Feb 2022; "
        "middle and high split the struck hromadas at their median. Carpathian panels on national classes are "
        "subsets of the national tables; the regional panel re-computes terciles within the four oblasts.")
text = ["**Table 6. Hromadas by capacity and exposure class**", "", note, ""] + md6
(FIG / "table06_terciles.md").write_text("\n".join(text), encoding="utf-8")
print("\n".join(text))

# where the high-exposure / low-capacity hromadas are (national classes)
rows = []
for key, col in (("alerts", "bv_alt"), ("strikes", "bv_str")):
    hl = bv[bv[col] == "31"]
    cnt = hl.groupby("oblast").size()
    tot = bv[bv[col].str.fullmatch(r"[123][123]")].groupby("oblast").size()
    for ob, v in cnt.items():
        rows.append({"exposure": key, "oblast": ob, "hromadas_hilo": int(v), "classified": int(tot[ob]),
                     "share": round(v / tot[ob], 3)})
hl_ob = pd.DataFrame(rows).sort_values(["exposure", "hromadas_hilo"], ascending=[True, False])
hl_ob.to_csv(FIG / "table06_hilo_oblast.csv", index=False)
for key in ("alerts", "strikes"):
    s = hl_ob[hl_ob["exposure"] == key]
    print(f"\nhigh exposure / low capacity ({key}), {s['hromadas_hilo'].sum()} hromadas in {len(s)} oblasts:")
    print(s.head(10).to_string(index=False))

print("\nnumbers.yaml:")
print(f'  n_hilo_alerts: "{hilo["alerts_national"]}"')
print(f'  n_hilo_strikes: "{hilo["strikes_national"]}"')
print(f'  n_hilo_alerts_carp: "{hilo["alerts_carp"]}"   # national terciles')
print(f'  n_hilo_carp_regional: "{hilo["alerts_carp_regional"]}"   # Map 17 regional terciles')

# --- Request 37: capacity x outage-loss classes -------------------------------------------------------
print("\n=== Request 37: capacity x summer-2024 outage-loss classes ===")
tj = pd.read_csv(TIDY / "trajectories_k3.csv", dtype=KEYS)[["k3", "tr_s24_rel"]]
tj["k3"] = tj["k3"].str.zfill(7)
w = u[["k1", "k3", "oblast", "capacity_index", "ntl_n_lit_px"]].merge(tj, on="k3", how="left", validate="1:1")
TYPE = {("high", "high"): "strong & steady", ("high", "low"): "strong but hit",
        ("low", "high"): "weak but steady", ("low", "low"): "weak & hit"}


def t3(s):
    out = pd.Series(pd.NA, index=s.index, dtype="object")
    ok = s.notna()
    out[ok] = pd.qcut(s[ok].rank(method="first"), 3, labels=["low", "mid", "high"]).astype(str)
    return out


def classify(x):
    x = x.copy()
    x["cap_t"], x["s24_t"] = t3(x["capacity_index"]), t3(x["tr_s24_rel"])
    both = x["cap_t"].notna() & x["s24_t"].notna()
    x["type"] = [TYPE.get((a, b), "") if ok else "" for a, b, ok in zip(x["cap_t"], x["s24_t"], both)]
    return x, both


def cuts(x, col, tcol, scale=1):
    return {t: f"{x.loc[x[tcol] == t, col].min() * scale:.2f}–{x.loc[x[tcol] == t, col].max() * scale:.2f}"
            for t in ("low", "mid", "high")}


cw = w[w["k1"].isin(CARP)]
rg, rboth = classify(cw)
na_, nboth = classify(w)

# check against 23_carpathian.py
prof = pd.read_csv(TIDY / "carpathian_profiles_k3.csv", dtype={"k3": str})
prof["k3"] = prof["k3"].str.zfill(7)
chk = rg.merge(prof[["k3", "cap_t_carp", "s24_t_carp", "type_carp"]], on="k3", how="left", validate="1:1")
for a, b in (("cap_t", "cap_t_carp"), ("s24_t", "s24_t_carp")):
    mis = (chk[a].fillna("") != chk[b].fillna("")).sum()
    print(f"check vs 23 ({b}): {mis} mismatches")
print(f"check vs 23 (type_carp, 4 corners): {((chk['type'] != '') != chk['type_carp'].isin(TYPE.values())).sum()} "
      f"mismatches; 23 weak & hit = {(chk['type_carp'] == 'weak & hit').sum()}")

rows, mdp = [], []
for scope, x, both in (("carpathian_regional", rg, rboth), ("national", na_, nboth)):
    xt = pd.crosstab(x.loc[both, "cap_t"], x.loc[both, "s24_t"]).reindex(
        index=["high", "mid", "low"], columns=["low", "mid", "high"], fill_value=0)
    for a in xt.index:
        for b in xt.columns:
            rows.append({"scope": scope, "capacity_tercile": a, "retention_tercile": b, "hromadas": int(xt.loc[a, b]),
                         "type": TYPE.get((a, b), "")})
    cc, sc = cuts(x, "capacity_index", "cap_t", 100), cuts(x, "tr_s24_rel", "s24_t")
    tab = pd.DataFrame({"Capacity tercile (range, 0–100)": [f"{a} ({cc[a]})" for a in xt.index],
                        **{f"Retention {b} ({sc[b]})": [f0(xt.loc[a, b]) for a in xt.index] for b in xt.columns}})
    lab = "within the four Carpathian oblasts" if scope != "national" else "all non-occupied hromadas"
    mdp += md_lines(tab, f"Capacity × summer-2024 light retention, terciles {lab}",
                    f"n = {int(both.sum()):,} with both values (capacity {x['capacity_index'].notna().sum():,}, "
                    f"retention {x['tr_s24_rel'].notna().sum():,}). Corners: weak & hit = low/low; strong & steady "
                    "= high/high; strong but hit = high/low; weak but steady = low/high.")
typ = pd.DataFrame(rows)
typ.to_csv(FIG / "carp_typology.csv", index=False)
intro = ("Retention = light in Jun–Jul 2024 as a share of H2 2023 (tr_s24_rel); low retention = large outage "
         "loss. Terciles by rank order (ties broken by position), as in 23_carpathian.py.")
text = ["**Capacity and outage-loss classes (request 37)**", "", intro, ""] + mdp
(FIG / "carp_typology.md").write_text("\n".join(text), encoding="utf-8")
print("\n".join(text))

wh_r = rg[rg["type"] == "weak & hit"]
ss_r = rg[rg["type"] == "strong & steady"]
wh_n = na_[na_["type"] == "weak & hit"]
wh_c_nat = na_[(na_["type"] == "weak & hit") & na_["k1"].isin(CARP)]
print("\nweak & hit, regional, by oblast:", wh_r.groupby("oblast").size().to_dict())
print("strong & steady, regional, by oblast:", ss_r.groupby("oblast").size().to_dict())
print("weak & hit, national terciles, top oblasts:",
      wh_n.groupby("oblast").size().sort_values(ascending=False).head(8).to_dict())

# --- Request 38: light publication threshold ----------------------------------------------------------
print("\n=== Request 38: light reliability ===")
REL_NLIT, REL_NOISE = 30, 0.35
nz = pd.read_csv(TIDY / "nightlights_noise_k3.csv", dtype={"k3": str})
assert "noise_sd" in nz, f"nightlights_noise_k3.csv columns: {list(nz.columns)}"
nz["k3"] = nz["k3"].str.zfill(7)
w = w.merge(nz[["k3", "noise_sd"]], on="k3", how="left", validate="1:1")
w["reliable"] = (w["ntl_n_lit_px"] >= REL_NLIT) & (w["noise_sd"] <= REL_NOISE)
pchk = w.merge(prof[["k3", "light_reliable"]], on="k3", how="inner")
print(f"check vs 23 light_reliable (Carpathian): {(pchk['reliable'].astype(int) != pchk['light_reliable']).sum()} "
      "mismatches")
rel = []
for scope, x in (("national", w), ("carpathian", w[w["k1"].isin(CARP)])):
    rel.append({"scope": scope, "non_occupied": len(x),
                "lit_ge10": int((x["ntl_n_lit_px"] >= MIN_LIT_PIX).sum()),
                "lit_ge30": int((x["ntl_n_lit_px"] >= REL_NLIT).sum()),
                "reliable": int(x["reliable"].sum()),
                "ge10_not_reliable": int(((x["ntl_n_lit_px"] >= MIN_LIT_PIX) & ~x["reliable"]).sum()),
                "ge30_noise_fail": int(((x["ntl_n_lit_px"] >= REL_NLIT) & ~(x["noise_sd"] <= REL_NOISE)).sum())})
rel = pd.DataFrame(rel)
rel.to_csv(FIG / "light_reliability.csv", index=False)
print(rel.to_string(index=False))

# alert-hours medians for the 670 / 674 check
print("\nalert hours, median 1 Sep 2025 – 31 Aug 2026:")
print(f"  national (u, n={u['alert_h_12m'].notna().sum()}): {u['alert_h_12m'].median():.1f}   "
      f"national (Table 3 frame, n={len(d)}): {d['alert_h_12m'].median():.1f}   "
      f"Carpathian: {u.loc[u['k1'].isin(CARP), 'alert_h_12m'].median():.1f}")

print("\nnumbers.yaml:")
print(f'  carp_weak_hit: "{len(wh_r)}"')
print(f'  carp_weak_hit_if_cv: "{int(wh_r["k1"].isin(["26", "73"]).sum())}"')
print(f'  carp_strong_steady: "{len(ss_r)}"')
print(f'  carp_strong_steady_lv: "{int((ss_r["k1"] == "46").sum())}"')
print(f'  nat_weak_hit: "{len(wh_n)}"   # national terciles')
print(f'  carp_weak_hit_natcuts: "{len(wh_c_nat)}"')
for k, r in rel.set_index("scope").iterrows():
    tag = "nat" if k == "national" else "carp"
    print(f'  n_light_reliable_{tag}: "{r["reliable"]:,}"   n_light_ge10_{tag}: "{r["lit_ge10"]:,}"')
