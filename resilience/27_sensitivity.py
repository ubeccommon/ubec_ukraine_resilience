"""27_sensitivity.py — paper Table 7 (recovery models M1–M7, request 4), Figure 1 (β3 with 95 % intervals,
request 4) and Table 8 (sensitivity variants, request 7).

Run after 12_moderation.py (it reads the main results), with the venv Python.
Table 7 / Figure 1: from tidy/moderation_results.csv. Intervals for β3: wild-cluster bootstrap by oblast,
test inversion (M1–M6); normal approximation b ± 1.96 SE for the spatial lag model M7 (S2SLS).
Table 8: for each variant 27 runs 12_moderation.py with the matching options and a tag, then collects
  M5 (pre-war 2021 capacity, FE + controls) — the primary specification of the paper, and
  M3 (2025 capacity, FE + controls).
Variants: excluding garrison hromadas; excluding frontline (Donetsk 14, Zaporizhzhia 23, Kherson 65) and
Russian-border oblasts (Sumy 59, Kharkiv 63, Chernihiv 74); winter light ratio only; annual ratio only;
2025 capacity without civilian income-tax growth (2021 capacity unchanged, shown as —).
Outputs publication/figures/table07_models.{csv,md}, fig01_interaction.{svg,png},
table08_sensitivity.{csv,md}."""
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
TIDY = BASE / "tidy"
FIG = ROOT / "publication" / "figures"
FRONT_BORDER = "14,23,65,59,63,74"
VARIANTS = [
    ("primary", "Primary specification", None),
    ("no_garrison", "Excluding garrison hromadas", ["--drop-garrison"]),
    ("no_front_border", "Excluding frontline and Russian-border oblasts", ["--drop-k1", FRONT_BORDER]),
    ("winter", "Outcome: winter light ratio only", ["--outcome", "winter"]),
    ("annual", "Outcome: annual light ratio only", ["--outcome", "annual"]),
    ("no_pitgrowth", "2025 capacity without income-tax growth",
     ["--cap", "sens_cap_without_pdfo_civ_growth_rel_2125"]),
]
M21, M25 = "M5 pre-war capacity", "M3 + FE + controls"
KEEP = ("variant '", "dropping", "outcome from", "capacity column", "analysis sample")
# model: (label, oblast FE, controls, capacity, exposure, sample / method, figure label)
SPEC = {
    "M1 baseline": ("M1", "No", "No", "2025", "Strikes", "All", "M1 — no oblast FE"),
    "M2 + oblast FE": ("M2", "Yes", "No", "2025", "Strikes", "All", "M2 — oblast FE"),
    "M3 + FE + controls": ("M3", "Yes", "Yes", "2025", "Strikes", "All", "M3 — FE + controls"),
    "M4 alert hours": ("M4", "Yes", "Yes", "2025", "Alert hours", "All", "M4 — alert hours as exposure"),
    "M5 pre-war capacity": ("M5", "Yes", "Yes", "2021 (pre-war)", "Strikes", "All", "M5 — pre-war (2021) capacity"),
    "M6 without frontline oblasts": ("M6", "Yes", "Yes", "2025", "Strikes", "Without Donetsk, Zaporizhzhia, Kherson",
                                     "M6 — without frontline oblasts"),
    "M7 spatial lag": ("M7", "Yes", "Yes", "2025", "Strikes", "All; spatial lag (S2SLS, KNN 6)",
                       "M7 — spatial lag (S2SLS)"),
}
SOURCE = ("Source: VIINA (Zhukov & Ayers 2023); air-raid alerts (V. Klymenko archive); NASA Black Marble VNP46A3; "
          "openbudget.gov.ua; OCHA COD-AB. Own calculations.")


def num(v, dp, sign):
    """Rounded number with a typographic minus; values that round to zero print without a sign."""
    if pd.isna(v):
        return "—"
    r = round(float(v), dp)
    if r == 0:
        return f"{0:.{dp}f}"
    s = f"{r:+.{dp}f}" if sign else f"{r:.{dp}f}"
    return s.replace("-", "−")


def pval(p):
    return "—" if pd.isna(p) else ("< 0.001" if p < 0.001 else f"{p:.3f}")


def md_write(path, title, df, note):
    cols = list(df.columns)
    lines = [f"**{title}**", "", "| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    lines += ["| " + " | ".join(str(v) for v in r) + " |" for r in df.itertuples(index=False)]
    lines += ["", note, ""]
    path.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


# --- Table 7 and Figure 1 (request 4) ----------------------------------------------------------------
mr = pd.read_csv(TIDY / "moderation_results.csv")
assert "ci_lo_interaction" in mr, "moderation_results.csv has no interval columns: re-run 12_moderation.py"
mr = mr[mr["model"].isin(SPEC)].copy()
mr["ci_lo"] = mr["ci_lo_interaction"]
mr["ci_hi"] = mr["ci_hi_interaction"]
m7 = mr["model"] == "M7 spatial lag"
mr.loc[m7, "ci_lo"] = mr.loc[m7, "b_interaction"] - 1.96 * mr.loc[m7, "se_interaction"]
mr.loc[m7, "ci_hi"] = mr.loc[m7, "b_interaction"] + 1.96 * mr.loc[m7, "se_interaction"]
mr["ci_method"] = np.where(m7, "normal (S2SLS SE)", "wild-cluster bootstrap by oblast")
keep = ["model", "n", "r2", "r2_within", "b_capacity", "t_capacity", "p_wcb_capacity", "b_interaction",
        "t_interaction", "p_wcb_interaction", "ci_lo", "ci_hi", "ci_method", "note"]
mr[keep].round(4).to_csv(FIG / "table07_models.csv", index=False)

t7 = pd.DataFrame([{
    "Model": SPEC[r.model][0], "Oblast FE": SPEC[r.model][1], "Controls": SPEC[r.model][2],
    "Capacity": SPEC[r.model][3], "Exposure": SPEC[r.model][4], "Sample / method": SPEC[r.model][5],
    "n": f"{int(r.n):,}", "R²": num(r.r2, 2, False), "Within-R²": num(r.r2_within, 2, False),
    "β₁ capacity (t)": f"{num(r.b_capacity, 2, True)} ({num(r.t_capacity, 1, False)})",
    "p β₁": pval(r.p_wcb_capacity),
    "β₃ interaction (t)": f"{num(r.b_interaction, 2, True)} ({num(r.t_interaction, 1, False)})",
    "p β₃": pval(r.p_wcb_interaction),
    "β₃ 95 % interval": f"{num(r.ci_lo, 2, True)} to {num(r.ci_hi, 2, True)}"} for r in mr.itertuples()])
rho = mr.loc[m7, "note"].iloc[0].replace("rho=", "") if m7.any() else ""
md_write(FIG / "table07_models.md", "Table 7. Recovery models M1–M7", t7,
         "Outcome: night-light recovery index; all variables standardised. Controls: log population 2020, log lit "
         "pixels, log 2021 radiance. t-values with HC1 standard errors; p-values from a restricted wild-cluster "
         "bootstrap by oblast (24 clusters, Webb weights, 9,999 draws). β₃ intervals invert that test (M1–M6); "
         f"for M7 (spatial lag, ρ = {rho}) they use the S2SLS standard error. R² is not defined for M7. Within-R²: "
         "share of the variation around oblast means explained.")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
rev = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"], capture_output=True, text=True)
commit = rev.stdout.strip() or "unknown"
fg = mr.iloc[::-1].reset_index(drop=True)
fig, ax = plt.subplots(figsize=(170 / 25.4, 3.3))
for i, r in fg.iterrows():
    col = "#b2182b" if r["model"] == "M1 baseline" else "#2166ac"
    mk = "D" if r["model"] == "M7 spatial lag" else "o"
    ax.plot([r["ci_lo"], r["ci_hi"]], [i, i], color=col, lw=1.8)
    ax.plot(r["b_interaction"], i, marker=mk, color=col, ms=6)
ax.axvline(0, color="0.4", lw=0.8, ls="--")
ax.set_yticks(np.arange(len(fg)))
ax.set_yticklabels([SPEC[m][6] for m in fg["model"]], fontsize=8)
ax.set_xlabel("β₃ capacity × exposure (standardised), 95 % interval", fontsize=9)
ax.tick_params(axis="x", labelsize=8)
for sp in ("top", "right"):
    ax.spines[sp].set_visible(False)
fig.text(0.01, 0.01, f"M1 without, M2–M7 with oblast fixed effects. Intervals: wild-cluster bootstrap by oblast "
                     f"(M1–M6); normal approximation (M7, diamond). {SOURCE} Run {commit}.",
         fontsize=6, wrap=True, color="0.3")
fig.tight_layout(rect=(0, 0.07, 1, 1))
for ext in ("svg", "png"):
    fig.savefig(FIG / f"fig01_interaction.{ext}", dpi=300)
plt.close(fig)
print(f"\nwrote fig01_interaction.svg/png (run {commit})")
fe = mr[mr["model"] != "M1 baseline"]
print("\nnumbers.yaml:")
print(f'  r2_within_range: "{num(fe["r2_within"].min(), 2, False)}–{num(fe["r2_within"].max(), 2, False)}"')
print(f'  int_fe_ci: "{num(fe["ci_lo"].min(), 2, True)} to {num(fe["ci_hi"].max(), 2, True)}"   # widest FE interval')

# --- Table 8 (request 7) -------------------------------------------------------------------------------
rows = []
for tag, label, opts in VARIANTS:
    if opts is None:
        f = TIDY / "moderation_results.csv"
    else:
        cmd = [sys.executable, str(BASE / "12_moderation.py"), *opts, "--tag", tag]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            sys.exit(f"12_moderation.py failed for {tag}:\n{res.stderr[-2000:]}")
        for line in res.stdout.splitlines():
            if line.startswith(KEEP):
                print(f"  [{tag}] {line}")
        f = TIDY / f"moderation_results_{tag}.csv"
    r = pd.read_csv(f).set_index("model")
    assert "t_capacity" in r, f"{f.name} has no t_capacity: re-run 12_moderation.py first"
    for model, cap in ((M21, "2021"), (M25, "2025")):
        x = r.loc[model]
        same = tag == "no_pitgrowth" and cap == "2021"
        rows.append({"variant": tag, "label": label, "capacity": cap, "n": int(x["n"]),
                     "b_capacity": None if same else x["b_capacity"], "t_capacity": None if same else x["t_capacity"],
                     "b_interaction": None if same else x["b_interaction"],
                     "t_interaction": None if same else x["t_interaction"]})

t8 = pd.DataFrame(rows)
t8.round(4).to_csv(FIG / "table08_sensitivity.csv", index=False)
cell = lambda b, t: "—" if pd.isna(b) else f"{num(b, 2, True)} ({num(t, 1, False)})"
W = t8.pivot(index="variant", columns="capacity")
out = []
for tag, label, _ in VARIANTS:
    w = W.loc[tag]
    out.append({"Variant": label, "n": f"{int(w[('n', '2025')]):,}",
                "β₁ capacity 2021": cell(w[("b_capacity", "2021")], w[("t_capacity", "2021")]),
                "β₃ interaction 2021": cell(w[("b_interaction", "2021")], w[("t_interaction", "2021")]),
                "β₁ capacity 2025": cell(w[("b_capacity", "2025")], w[("t_capacity", "2025")]),
                "β₃ interaction 2025": cell(w[("b_interaction", "2025")], w[("t_interaction", "2025")])})
md_write(FIG / "table08_sensitivity.md", "Table 8. Sensitivity of the capacity estimates", pd.DataFrame(out),
         "Standardised coefficients with t-values (HC1) in brackets; all models with oblast fixed effects and "
         "controls (log population 2020, log lit pixels, log 2021 radiance). Outcome: night-light recovery index. "
         "Exposure: strikes since 24 Feb 2022. 2021 capacity: own revenue per capita and transfer dependency, "
         "2021 budgets. Frontline and border oblasts: Donetsk, Zaporizhzhia, Kherson, Sumy, Kharkiv, Chernihiv. "
         "— = unchanged (the 2021 index does not include income-tax growth).")
