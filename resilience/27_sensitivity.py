"""27_sensitivity.py — paper Table 8 (request 7): capacity main effect (β1) and capacity × strike exposure
interaction (β3) with oblast fixed effects and controls, under sensitivity variants.

Run after 12_moderation.py (it reads the main results as the primary row), with the venv Python.
For each variant it runs 12_moderation.py with the matching options and a tag, then collects
  M5 (pre-war 2021 capacity, FE + controls) — the primary specification of the paper, and
  M3 (2025 capacity, FE + controls).
Variants: excluding garrison hromadas; excluding frontline (Donetsk 14, Zaporizhzhia 23, Kherson 65) and
Russian-border oblasts (Sumy 59, Kharkiv 63, Chernihiv 74); winter light ratio only; annual ratio only;
2025 capacity without civilian income-tax growth (2021 capacity unchanged, shown as —).
Standard errors HC1, as in 12. Outputs publication/figures/table08_sensitivity.{csv,md}."""
import subprocess
import sys
from pathlib import Path

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


def num(v, dp, sign):
    """Rounded number with a typographic minus; values that round to zero print without a sign."""
    r = round(float(v), dp)
    if r == 0:
        return f"{0:.{dp}f}"
    s = f"{r:+.{dp}f}" if sign else f"{r:.{dp}f}"
    return s.replace("-", "−")


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
o = pd.DataFrame(out)
cols = list(o.columns)
lines = ["**Table 8. Sensitivity of the capacity estimates**", "",
         "| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
lines += ["| " + " | ".join(str(v) for v in r) + " |" for r in o.itertuples(index=False)]
lines += ["", "Standardised coefficients with t-values (HC1) in brackets; all models with oblast fixed effects and "
          "controls (log population 2020, log lit pixels, log 2021 radiance). Outcome: night-light recovery index. "
          "Exposure: strikes since 24 Feb 2022. 2021 capacity: own revenue per capita and transfer dependency, "
          "2021 budgets. Frontline and border oblasts: Donetsk, Zaporizhzhia, Kherson, Sumy, Kharkiv, Chernihiv. "
          "— = unchanged (the 2021 index does not include income-tax growth).", ""]
(FIG / "table08_sensitivity.md").write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))
