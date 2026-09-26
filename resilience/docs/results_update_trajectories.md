# Results update for the publication conversation — time dimension (step 2), 25 Sep 2026

This replaces the "In progress" section of the publication prompt. All figures are for non-occupied hromadas. The coefficients are standardised; t-values use HC1 standard errors.

## New data layers

**Displacement.** IOM DTM API v3, oblast level only.
- Registration series: monthly Feb 2022 – Aug 2026, host × origin oblast. Three months are missing (2024-12, 2025-01, 2025-03).
- Survey of IDPs present: 7 rounds, Aug 2024 – Mar 2026.
- The hromada-level file has been requested from IOM and is pending. The join is prepared and tested.

**Night lights.** NASA Black Marble VNP46A3, monthly, Jan 2020 – Aug 2026 (80 months).
- Lit pixels are those lit in 2021. The index is radiance divided by the mean of the same calendar month in 2020 and 2021; 91 % of unit-months have a two-year baseline.
- June 2025 is excluded as a retrieval artefact.
- n = 1,021 hromadas with at least 10 lit pixels.

**Local budgets.** openbudget, quarterly 2021 Q1 – 2026 Q2 (22 quarters), n = 1,288.
- The four quarters of 2025 reproduce the v1.1 annual values exactly.
- The "relative" measure is the ratio to the same quarter of 2021, divided by the national median. This makes it inflation-neutral.

## Method facts the text must carry

- **Pre-war trend.** 2021 is about 24 % brighter than 2020 at the median, probably from LED retrofits and possibly COVID-dimmed 2020. The choice of baseline shifts levels by about 10 %. The 2020–21 mean is the conservative choice. The v1.1 ratios (2021-only baseline) understate recovery by about that much; their ranking is unaffected.
- **Monthly noise is large.** Before the war, month-to-month variation is 28 % at the median, falling from 32 % in units with 10–30 lit pixels to 14 % in those with more than 1,000. Trajectories therefore use windows and quarters, and "change" is judged against each hromada's own pre-war noise (|z| > 2).
- **Light is not only damage.** Radiance also reflects blackout orders, street-lighting policy (lights off or dimmed since 2022) and oblast-wide grid conditions.
- **Military PIT was moved to the state budget from Q4 2023.** From Q2 2022 to Q3 2023 it was 31–35 % of local PIT. Civilian PIT stays comparable across that break only because military lines are identified by name.
- **Nominal growth mostly tracks inflation.** Own revenue in 2025 is 1.62–1.81× its 2021 level, which is about cumulative inflation; 2026 H1 is 2.16×. Real own revenue is roughly flat.

## National trajectory (median night-light index; 1 = pre-war level)

- **March 2022:** 0.05, a near-total dark-out (blackout orders, curfews).
- **Sep 2022:** partial rise to 0.18.
- **Oct–Nov 2022:** back to 0.08–0.09 with the energy-strike campaign.
- **Jul–Dec 2023:** recovery to 0.40.
- **Jun–Jul 2024:** 0.10–0.11, the rolling outages.
- **Sep 2025 – Aug 2026:** 0.37. No upward trend since late 2024: light has plateaued at about 40 % of pre-war.
- **Worst quarter** fell in 2022 for 75 % of hromadas (Q2 36 %, Q4 25 %, Q3 14 %).
- **Change, last 12 months vs Jul–Dec 2023,** against each hromada's own noise:
  - Nationally: declined 37 %, stable 51 %, improved 12 %.
  - Carpathian oblasts: 25 / 67 / 8 %.

## Carpathian oblasts vs the rest (medians)

| | Carpathian | Rest |
|---|---|---|
| Recent light level | 0.62 | 0.30 |
| H2 2023 light level | 0.69 | 0.33 |
| Worst quarter | 0.21 | 0.04 |
| Share of quarters below 0.5 | 0.39 | 0.94 |
| Summer-2024 light as share of H2 2023 | 0.38 | 0.26 |

Relative civilian PIT in the Carpathian oblasts peaked in 2022 Q2–Q3 (1.11–1.21), which fits business and worker relocation westward. From late 2023 it settles at 1.04–1.12 (above the national median).

## Models (within oblasts = with oblast fixed effects)

**Summer-2024 outage loss.** Light in Jun–Jul 2024 relative to the same hromada's H2 2023 level. This is the most robust capacity result.
- Capacity +0.20 (t 6.3) with fixed effects and controls; +0.16 (t 4.1) when weighted by measurement precision.
- With **pre-war 2021 capacity**: +0.13 (t 3.6).
- Residual spatial dependence is low (Moran's I 0.07).
- Reading: hromadas with more fiscal capacity lost relatively less light when the grid failed. The data cannot identify the mechanism (backup power, maintained networks, economic mix).

**Recent light level.**
- Capacity +0.19 to +0.22 (t 7–8), robust to weighting and to alert hours as the exposure.
- Pre-war capacity only +0.09 (t 3.0). Part of the 2025 association runs from local economic activity to both lights and revenue.
- Alert hours are the dominant exposure: Spearman −0.65; within oblasts −0.54 (t −8.5). Updated 26 Sep 2026: alert window fixed at 1 Sep 2025 – 31 Aug 2026 (yellow/red alert levels from Sep 2026).

**Worst quarter.** Oblast-wide. Within oblasts capacity is weak (+0.09), and pre-war capacity is about 0 (+0.02). In the acute phase local capacity did not protect.

**Buffering.** Exposure × capacity is about 0 for level, trough and outage loss after oblast effects. This is the same as v1.1. For the 2024–26 slope it is slightly negative (−0.06, t −2.3 to −3.4, R² 0.11–0.17): capacity helps the trend less where exposure is high.

**Civilian PIT.**
- Higher exposure goes with lower relative PIT within oblasts: −0.24 recent, −0.18 in 2022. This fits taxpayers relocating away from exposed areas.
- The negative pre-war-capacity coefficient is partly mechanical (ratio to own 2021 value, regression to the mean). Do not interpret it as "strong hromadas declined".

**Residual spatial dependence** remains for level and trough (Moran's I 0.15–0.22).

## New maps

- **19** Recent light deficit × capacity: bivariate 3×3, national terciles. Light-deficit cut points: the brightest third is above 0.49 of pre-war, the darkest third below 0.25.
- **20** Left panel: summer-2024 outage loss in quintiles; the lowest fifth kept less than 7 % of its H2 2023 light. Right panel: change classes since H2 2023.

Captions on both pages read their numbers from the current model output.

## Files (resilience/tidy)

`nightlights_panel_k3.csv`, `nightlights_noise_k3.csv`, `budget_quarterly_k3.csv`, `ntl_quarterly_k3.csv`, `trajectories_k3.csv`, `trajectory_models.csv`, `trajectory_classes.json`, `dtm_oblast_*_k1.csv`; dictionary rows `bq_*`, `tr_*`, `bt_*`, `dtm_*`.

## Claims to frame carefully

1. **"Capacity helps."** Only as an association within oblasts. The outage-loss result with pre-war capacity is the strongest version. Level results are partly reverse-causal.
2. **"No buffering."** State plainly that the interaction disappears once oblast effects are included, in every outcome.
3. **"Light = recovery."** Light also reflects lighting policy and grid-wide outages. The 40 % plateau is not "60 % destroyed".
4. **Wartime sensitivity.** Recent (last-12-month) hromada light levels describe current power conditions. Propose to publish recent-period maps only at hromada level and with a time lag, or to aggregate them. Historical windows (2022–2024) carry lower risk.
