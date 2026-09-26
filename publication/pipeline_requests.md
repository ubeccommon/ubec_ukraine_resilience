# Requests from the publication conversation (v0.2 draft)

## Status after the trajectory update (25 Sep 2026)

**Answered, now in the drafts:**
- **12**, mostly: national trajectory, Carpathian vs rest, change classes, outage, level and worst-quarter models, slope interaction.
- **27**: variables standardised, HC1 errors.

**Partly answered:**
| Request | Answered | Still open |
|---|---|---|
| 10 | Exposure, capacity and light for the Carpathian oblasts, via the Carpathian dispatch | Table 11 medians for capacity 2021, capacity 2025 and the annual recovery ratio |
| 11 | Own revenue 2025 = 1.62–1.81 × 2021 | CPI series used; see also 34 |
| 19 | Source author Klimenko | Repository URL and exact MIT notice |
| 22 | Lit pixels = lit in 2021; minimum 10 pixels; monthly baseline = 2020–21 mean | Radiance threshold for "lit"; winter months and combination rule for the v1.1 annual ratio |
| 29 | The three missing months | Base month for the % changes; per-1,000 denominator; Figure 3 |

**Still open from request 12:**
- Capacity (2025 and pre-war) coefficients and residual Moran's I for the 2024–26 slope model.
- Exact interaction estimates for outage loss, level and worst quarter. The update says "≈ 0"; the paper needs the numbers.

**Now more important:** 15 (Lviv trust). Lviv is the fiscally strongest Carpathian oblast, and section 10.3 has no trust value for it.

## New requests (33–38)

**33. Maps 19 and 20 (right panel) under rule R2.** Both show last-12-month light by hromada. Provide versions with the "recent" window ending at least 6 months before the planned release, or aggregated to raion. Apply rule R3 (30 km zone) as well.

**34. Basis of "2026 H1 = 2.16 × 2021".** Is it H1 2026 annualised against full-year 2021, or H1 against H1? Also the CPI series used for "about cumulative inflation".

**35. Robust inference for the trajectory models.** Because residual Moran's I is 0.15–0.22 for level and worst quarter, the HC1 t-values are optimistic. Add wild-cluster bootstrap p-values (oblast) and, if feasible, Conley or spatial-HAC errors for outage loss, level, worst quarter and slope. This extends requests 4 and 5.

**36. Registered IDPs, Carpathian range.** The v1.1 figures give 78–80 per 1,000 for Ivano-Frankivsk, Lviv and Chernivtsi, while the Carpathian dispatch gives 77–98 for the four oblasts. Confirm the values and the date.

**37. Class definitions.** Define "weak and hit" (33 Carpathian hromadas) and "strong and steady": the capacity and outage-loss cut points, and whether national or regional terciles are used. Also the national count of "weak and hit" hromadas.

**38. Publication threshold for single-hromada light.** The Carpathian dispatch shows single-hromada values only where at least 30 pixels are lit, while the models use at least 10. Confirm 30 as the general publication rule, and the number of hromadas below it nationally and in the Carpathian oblasts.

Also for request 14: a figure export of the national median monthly index (paper Figure 2, essay Chart 1) and `fig1_carpathian_light.svg` into `publication/figures/`.

---


These are the numbers, tables, figures and method details the publication drafts still need. The drafts are `publication/paper/paper.md`, `brief/brief.md`, `essay/essay.md` and `data_package/`.

- Numbers go into `publication/numbers.yaml` under the key named. Tables and figures go into `publication/figures/` or a CSV, as noted.
- Request numbers match the `[[PENDING: … request N]]` markers in the drafts.
- **Priority:** A = blocks a core claim; B = needed for tables and methods; C = needed before release.

---

## A. Core claims (do first)

**4. Recovery model table M1–M7**
- For each model: the specification (oblast FE, capacity measure, exposure measure, sample), plus β₁ capacity, β₂ exposure and β₃ interaction, each with SE and t.
- For each model: n, R², and within-R² for the FE models.
- Wild-cluster bootstrap p-values at oblast level for β₁ and β₃.
- The t-value for the 2021-capacity main effect (+0.08).
- Which exposure measure the baseline interaction (+0.15, t 6.3) uses.
- Figure 1: β₃ with 95 % intervals across M1–M7.
- Keys: `int_fe_range`, `n_model`. Used in paper Table 7 and sections 0, 7.2–7.4; brief finding 4.

**27. Variable scaling and SE type**
Are variables standardised (z), percentile ranks or raw? Which standard errors are used? This determines how the coefficients are described in the paper and brief.

**6. Capacity index without civilian income-tax growth**
Rebuild the index from own revenue, transfer dependency and capex share only, re-run M2–M7, and report β₁ and β₃. Key: `cap_main_fe_no_pitgrowth`. Used in paper sections 0.5, 7.4 and 11.11.

**5. Spatial models**
- Which model the spatial lag ρ = 0.85 comes from.
- Spatial lag and spatial error models with oblast FE: β₁ and β₃.
- Residual Moran's I for each model.
- Used in paper section 7.5.

**7. Sensitivity table (paper Table 8)**
β₁ and β₃ with oblast FE for each of these variants:
- primary (2021 capacity);
- excluding the 36 garrison hromadas;
- excluding frontline and border oblasts;
- winter ratio only as the outcome;
- annual ratio only as the outcome;
- capacity without income-tax growth.

**8. Capacity × exposure correlations (paper Table 5)**
Spearman ρ with 95 % CI for capacity 2025 and capacity 2021 against strikes and against alert hours. Also within-oblast partial ρ for 2025. Keys: `rho_cap_*`, `ci_cap_*`.

**10. Carpathian vs national medians (paper Table 11)**
Strike exposure, alert hours, capacity 2021, capacity 2025 and recovery ratio. This confirms or corrects three claims in section 10.1 and in the essay: lower exposure, lower capacity and better recovery in the Carpathian oblasts.

**1. Coverage**
- The reasons for each drop: 1,290 → 1,288 (capacity), 1,290 → 1,021 (recovery), and the engagement n.
- A table of excluded hromadas by oblast and reason.
- Keys: `n_engagement`, `n_model`. Used in paper Table 1 and section 11.5.

---

## B. Tables and method description

**2. Exposure periods and descriptives (paper Table 3)**
VIINA and alert date ranges. Median, IQR and maximum of strikes and alert hours, nationally and by oblast. Keys: `period_viina`, `period_alerts`.

**3. Capacity index PCA (paper Table 4)**
Loadings, eigenvalues and leave-one-out ρ for each component.

**9. reSCORE 2024 by oblast (paper Table 10)**
For all oblasts: the four indicators (trust in local administration, community cohesion, locality satisfaction, belonging), with n and 95 % CI. Also the number of oblasts covered. Key: `n_rescore_oblasts`.

**15. Lviv trust difference** (reSCORE 2024). Key: `trust_diff_lv`.

**28. reSCORE change 2021 → 2024** in trust and cohesion, by oblast.

**29. IDP details**
- Confirm the base month for the percentage changes. The drafts assume February 2023 for all of them.
- The denominator for the per-1,000 figures.
- Figure 3: registered vs present IDPs per 1,000, by oblast.
- Key: `n_dtm_oblasts`.

**26. Tercile cross-tab (paper Table 6)**
Hromada counts in each capacity × exposure tercile cell, for alert hours and for strikes, nationally and for the Carpathian oblasts. The brief quotes the national high-exposure / low-capacity count.

**16. Occupation classification.** Source and reference date.

**17. UA_LAEA projection.** Full parameters (PROJ string or WKT).

**18. VIINA processing.** Event categories included, deduplication rule, and normalisation (count, per km² or per 10,000 residents).

**19. Air-raid alerts**
- Source name and URL.
- The exact copyright line and MIT notice from its LICENSE file.
- The rule for assigning oblast- and raion-level alerts to hromadas.

**20. Risk index (Map 01).** Formula and weights.

**21. Capacity index aggregation.** PC1 score or mean of percentile ranks.

**22. Night-light recovery ratio**
- Lit-pixel radiance threshold.
- Baseline months, and the months defining "winter".
- How the annual and winter ratios are combined.
- The minimum-lit-pixel exclusion rule.
- The baseline months for the monthly index.

**24. OSM and ЄДРПОУ.** Which layers and tables are actually used, and for what. If they're unused in the published results, they are dropped from the paper's Table 2 and from the attribution file.

---

## C. Trajectories, security, release

**12. Trajectory results (paper section 8, Table 9)**
- The last month of the monthly panel. Keys: `nl_panel_end`, `nl_panel_end_year`.
- The threshold for "months below baseline".
- The four metrics per hromada: trough depth, winter dips, months below baseline, 2024–26 slope.
- Models for each metric: β for capacity (2021), exposure and interaction, and R² without and with FE.
- Figure 2: national median monthly index with IQR band and major outage periods marked.
- Trajectory maps, and the Carpathian vs national comparison.
- Final values for `nl_trough_2024_median` and `nl_calm_range`.

**11. Real own revenue.** CPI-deflated own revenue 2021–2025, national and Carpathian, with the CPI source. Also `budget_panel_end`.

**31. Front-line zone for rule R3**
- Source and date of the front-line geometry.
- The list of hromadas within 30 km of the front line or the Russian/Belarusian border.
- The raion aggregation for these hromadas.

**13. Security audit (paper Table 12, Annex E)**
List every map, table and GeoPackage with its finest spatial level and finest time step. Flag anything below hromada level, and any hromada-level monthly data for the last 12 months. Specifically check:
- Map 03 (strike points) and the Carpathian zoom pages;
- whether any interpolated surface is exported as data.

**32. Data package export**
Actual file names and layout for `data/tables/` and `data/geo/`, following the proposed tree in `data_package/README.md`. Apply these rules in the export:
- **R2:** hromada monthly values end 6 months before release; the last 12 months are at oblast level only.
- **R3:** raion aggregation in the front-line zone.
- **R4:** no garrison flag and no military income-tax fields.
- **R5:** no event points.
- **R6:** no names or free text.

Also a `missing_reason` column with its codes added to the data dictionary.

**14. Figure exports**
170 mm wide, 300 dpi, with the source attribution line and run commit hash on every map. Save into `publication/figures/`.

| Output | Figures needed |
|---|---|
| Paper | Maps 01, 04, 07, 09, 14, 15, 16, 17, 18; Figures 1–3; trajectory maps |
| Brief | Maps 14 and 18 at half-page size |
| Essay | Maps 01, 14, 17, 18 and the Figure 2 chart |

**23. Terms of use**
- DREAM: terms, and the definition of a "valid" project.
- reSCORE: terms.
- IOM DTM: whether oblast aggregates may be redistributed, and the required wording.

**25. Versions and access dates**
- VIINA version or date, alerts, DREAM extract, COD-AB version, OSM extract, and DTM, reSCORE and openbudget access dates.
- Operating system and QGIS plugin versions.
- Full `run_all.sh` run time.
- Keys: `version_*`, `access_*`, `run_time`.

**30. (Optional) Mountain vs lowland hromadas** within the Carpathian oblasts: capacity, recovery and exposure compared.

---

## Checks on values already in `numbers.yaml`

- `carpathian_oblasts`: confirm that Zakarpattia, Ivano-Frankivsk, Lviv and Chernivtsi is the set used for Map 17.
- `n_crimea_units` = 292: confirm against the tessellation (computed as 1,763 − 1,471).
- `idp_west_gap`: the source figures give roughly 30–75 %, not the ~40–75 % in the original brief. Confirm.
- `idp_rise_*` and `idp_carp_decline`: confirm that all use February 2023 as the base.

## Outside the pipeline

- Hromada-level IOM DTM file: requested from IOM, pending.
- Contact address for the README, brief and essay: to be decided by Michel.

---

## Answers (26 Sep 2026, repository session)

Written into `paper/paper.md` and `numbers.yaml`:

- **16.** VIINA territorial control, latest status per GeoNames settlement, 19 Sep 2026. `occ_share` = population-weighted share of places with status RU or CONTESTED; occupied if ≥ 0.5; Crimea and Sevastopol always occupied (`viina/build_surfaces.py`).
- **17.** `+proj=laea +lat_0=48.5 +lon_0=31 +x_0=0 +y_0=0 +ellps=GRS80 +units=m +no_defs`.
- **18.** Types airstrike, UAV, artillery, air defence (`t_*_b`); `a_rus_b == 1` and `a_ukr_init_b != 1`; VIINA `event_1pd` (reports merged, `n_reports` kept); events in RU/contested places dropped; hromada level ADM3/STREET only, single-report events in places < 2,000 residents dropped (`viina/prep_qgis_layers.py`). Rates per 1,000 km² and per **100,000** residents (not 10,000). `exp_strikes_log = log1p(n_all)`: all events since 24 Feb 2022 (`resilience/11_composite.py:186`). Note for section 5: strike exposure is cumulative, alert exposure is the last 12 months.
- **19.** Source https://github.com/Vadimkin/ukrainian-air-raid-sirens-dataset, "Copyright (c) 2022 Vadym Klymenko", MIT. Assignment: union of hromada, raion and oblast alerts, overlaps merged. Window fixed at 1 Sep 2025 – 31 Aug 2026 (`viina/alert_window.py`).
- **20.** Map 01 is strikes only (the draft said strikes and alerts): H3 res 5, Σ 0.5^(age/182.5), scaled 0–100 to the maximum cell (`viina/risk_index.py`).
- **21.** Mean of percentile ranks, indicators winsorised at 2 %/98 % and oriented; `CAP_MIN = 3` of 4. PCA is a diagnostic only.
- **22.** Lit: 2021 mean ≥ 1.0 nW/cm²/sr; `MIN_LIT_PIX = 10`. Annual 2024/2021; winter Dec–Feb 2024–25 / 2020–21; snow-free composite, snow-covered fallback. Recovery index = mean of the two ratios' percentile ranks, `REC_MIN = 1`.
- **24.** OSM: basemap only. ЄДРПОУ: regional supplement (`*_reg`), Carpathian profile only, not in indices or models.
- **2 (periods).** `period_viina` 24 Feb 2022 – 19 Sep 2026; `period_alerts` 15 Mar 2022 – 31 Aug 2026 (models: 12-month window).

- **1 (coverage).** Universe is **1,289** non-occupied hromadas (not 1,290; resilience_v1, index file and hromada_control.gpkg agree). Capacity 1,288: one Kyiv-oblast hromada with none of the four budget indicators. Recovery 1,021: all 268 exclusions have < 10 pixels lit in 2021 (Rivne 34, Chernihiv 32, Volyn 31, Sumy 27, …); none for missing ratios. Engagement 1,289 (no exclusions). Model sample `n_model` = 1,020 (recovery sample minus the capacity gap; no exposure or geometry drops). Tables: `publication/figures/table01_coverage.{csv,md}`, `table01_exclusions.{csv,md}` from `resilience/26_publication_tables.py`.
- **8 (Table 5).** Spearman ρ, Fisher z CI with Bonett–Wright SE (bootstrap agrees within 0.01), n = 1,288. Capacity 2025: strikes 0.09 [0.03, 0.14], alerts 0.19 [0.13, 0.24]; within oblasts 0.06 [0.01, 0.12] and −0.03 [−0.09, 0.02]. Capacity 2021: strikes 0.26 [0.21, 0.31], alerts 0.50 [0.46, 0.55]; within oblasts 0.14 [0.09, 0.20] and 0.03 [−0.03, 0.08]. The pre-war alert association is regional (east–west gradient). `rho_cap_exp_min/max` now 0.09/0.19 (2025 score; was 0.07/0.18 from v1.1 measures). Table: `publication/figures/table05_correlations.{csv,md}`.
- **26 (Table 6).** Counts read from `resilience_maps.gpkg:hromada_bivariate` (Maps 14, 15, 17), n = 1,288 classified. Strike classes are not terciles: class 1 = no strike (997), classes 2/3 split the 291 struck at their median. High exposure / low capacity: alerts 104 (Sumy 20, Kharkiv 18, Kherson 15, Dnipropetrovsk 11, Chernihiv/Donetsk/Zaporizhzhia 9 each; 11 oblasts), strikes 55. All 251 Carpathian hromadas are in the national lowest alert tercile; on the Map 17 regional terciles 36 are high-exposure / low-capacity (not the 33 of request 37, which uses outage loss). Tables: `publication/figures/table06_terciles.{csv,md}`, `table06_hilo_oblast.csv`. Open: R3 status of map pages 14/15 (request 31).
- **37 (classes).** As `23_carpathian.py`: rank-order terciles, within the four oblasts, of `capacity_index` (low 7.2–30.3, mid 30.4–52.0, high 52.4–97.6 on 0–100) and `tr_s24_rel` (low 0.00–0.24, mid 0.25–0.47, high 0.47–1.07); n = 209 with both. Weak & hit = low/low: 33 (Chernivtsi 15, Ivano-Frankivsk 12, Zakarpattia 4, Lviv 2). Strong & steady = high/high: 34 (Lviv 15, Zakarpattia 12, Ivano-Frankivsk 4, Chernivtsi 3). National terciles, same rule: 136 weak & hit (n = 1,020); Carpathian count on national cuts also 33. Checks vs `carpathian_profiles_k3.csv`: 0 mismatches. Table: `publication/figures/carp_typology.{csv,md}`.
- **38 (light threshold).** The dispatch rule has two conditions: ≥ 30 lit pixels and pre-war `noise_sd` ≤ 0.35. National: 1,021 modelled (≥ 10 px), 779 ≥ 30 px, 622 reliable (157 reach 30 px but fail the noise condition). Carpathian: 209, 169, 134. R2 in the README names only the 30 pixels — decision pending on adding the noise condition. `publication/figures/light_reliability.csv`.
- **Alert hours check.** National median 674.0 (not 670), Carpathian 114.2; `nat_alert_hours_12m` set to 674.
- **6 (capacity without civilian PIT growth).** Capacity = `sens_cap_without_pdfo_civ_growth_rel_2125` from `11` (own revenue pc, transfer dependency, capex share; ≥ 2 of 3; Spearman 0.93 with the main index), run as `12_moderation.py --cap … --tag no_pitgrowth` → `tidy/moderation_results_no_pitgrowth.csv`. With oblast FE (M2–M4, M6, M7): β₁ capacity +0.13 to +0.16 (t 3.9–5.2; main +0.14 to +0.19, t 5.3–6.5); β₃ −0.02 to −0.00 (|t| < 1). M1 without FE: β₁ −0.02 (t −0.6; main +0.08, t 2.5), β₃ +0.18 (t 7.1). M5 unchanged (pre-war capacity). PIT growth carries the raw between-oblast capacity effect, not the within-oblast one. `cap_main_fe_no_pitgrowth` = 0.13–0.16.
- **7 (Table 8).** `resilience/27_sensitivity.py` (in `run_all.sh` after `26`) runs `12_moderation.py` variants and collects M5 (2021 capacity) and M3 (2025 capacity), both with oblast FE and controls, HC1. 2021 capacity: β₁ +0.07 to +0.08 (t 1.9–2.4), β₃ −0.01 to 0.00 in all variants. 2025 capacity: β₁ +0.15 to +0.21 (t 4.6–6.1), β₃ −0.01 to +0.01. Garrison: 36 dropped (n 993). Frontline + Russian-border oblasts (14, 23, 65, 59, 63, 74): n 881. Winter only n 1,006. Tables: `publication/figures/table08_sensitivity.{csv,md}`; variant results `resilience/tidy/moderation_results_*.csv`.
- **4/35 (robust inference).** `resilience/robust_inference.py`, used by `12` and `22`: restricted wild-cluster bootstrap by oblast (24 clusters, Webb weights, B = 9,999, CR1 t) and Conley spatial-HAC t (Bartlett, 50/100 km, UA_LAEA). Recovery (`moderation_results.csv`): 2025 capacity M2–M4, M6 WCB p < 0.001, Conley t 4.9–6.2; pre-war capacity M5 β₁ +0.08, HC1 t 2.3, CR1 t 2.0, **WCB p 0.058**, Conley t 2.1; all FE interactions p 0.29–0.89; M1 interaction +0.15 WCB p < 0.001. Trajectories (`trajectory_models.csv`, M3/M5): outage loss 2025 cap +0.20 p < 0.001, pre-war +0.13 p 0.001 (Conley t 3.5–3.7); recent level 2025 +0.21 p < 0.001, pre-war +0.10 p 0.003; worst quarter 2025 +0.09 p 0.004, pre-war 0; slope 2024–26 interaction −0.06 HC1 t −2.3 but WCB p 0.057 (pre-war p 0.18) — not robust.
- **4 (Table 7, Figure 1).** `27_sensitivity.py` writes `table07_models.{csv,md}` and `fig01_interaction.{svg,png}` from `moderation_results.csv`. Within-R² (FE models) 0.02–0.09. β₃ 95 % intervals by inverting the wild-cluster test: M1 +0.09 to +0.22; M2–M6 all straddle zero, widest −0.09 to +0.06; M7 normal approximation −0.06 to +0.01 (ρ = 0.845). The spatial lag ρ = 0.85 in section 7.5 is M7 (S2SLS on the M3 specification, KNN 6) — part of request 5.
- **5 (spatial models).** ρ = 0.85 is M7: S2SLS spatial lag on the M3 specification (oblast FE + controls), KNN 6. New in `12`: M7b lag with pre-war capacity (ρ 0.97), M8/M8b spatial error, `spreg.GM_Error_Het` (λ 0.41, filtered-residual Moran's I −0.01). Capacity: SEM 2025 +0.17 (z 5.9), pre-war +0.08 (z 2.3); interaction z −0.7 to −0.1. Lag residuals negatively autocorrelated (I −0.14 and −0.16) — lag over-corrects; the error model is the spatial check of record. Residual Moran's I for M1–M8b in `moderation_results.csv`.
- **33 (maps 19–20 under R2) — R2 part done.** `22_trajectories.py`: `PUB_END = 2026-03` (publication window Apr 2025 – Mar 2026, safe for releases from 1 Oct 2026); reliability rule ≥ 30 lit pixels and pre-war noise_sd ≤ 0.35 (`tr_light_reliable`, 622 hromadas). Publication classes `bv_rec_cap_pub`, `s24_q_pub`, `chg_cls_pub` (terciles/quintiles among reliable hromadas); `trajectory_classes.json` gains `pub_window`, cut points and `change_share_pub` (national declined / stable / improved 27 / 55 / 18 %, Carpathian 25 / 65 / 10 %). `build_qgis_project.py` pages 19–20 use the `_pub` fields and name the window; models unchanged. **Open:** R3 (raion aggregation in the 30 km zone) needs request 31; pages 19–20 stay in `HELD` until then. Cosmetic: legend swatch for 'No reliable light data' needs an outline (next builder change).
- **31 (front-line zone for R3).** `resilience/28_frontline_zone.py` → `tidy/frontline_zone_k3.csv`. Front line: boundary between occupied and non-occupied hromadas (VIINA control, 19 Sep 2026; hromada-level, 1,847 km because hromada edges are jagged). Border: hromada outer boundary within 5 km of Russia / Belarus in Natural Earth 1:10m, next to non-occupied territory (956 km / 1,115 km). Zone = any part of a non-occupied hromada within 30 km: 196 hromadas (by centre: 146); front 97, border 88, both 11; Sumy 32, Dnipropetrovsk 28, Kharkiv 28, Zaporizhzhia 18, Chernihiv 16, Kherson 15, Volyn 14, Donetsk 11, Mykolaiv 11, Rivne 11, Kyiv 6, Zhytomyr 6. 34 raions touched (8 fully, 26 partly). Line and zone layers in `resilience/frontline_zone.gpkg` (local). Decision pending: how R3 is applied (raion aggregation vs masking) on maps 14/15/19/20 and in the data package.
- **33 (maps 19–20) — R3 part done; R3 applied to maps 14–16 as well.** `resilience/29_r3_aggregate.py` → `resilience_maps.gpkg` layers `hromada_bivariate_r3`, `hromada_trajectories_r3`; `tidy/r3_raion_values.csv`. Zone hromadas (196) dissolved per raion into 34 parts carrying raion values over all non-occupied hromadas of the raion: capacity, alert hours, strikes (log) population-weighted; recovery lit-pixel-weighted; light (19–20) lit-pixel-weighted over reliable hromadas only (6 raions without one → white); change class from the raion z-score. Classed with the national hromada thresholds. Builder: pages 14, 15, 16, 19, 20 use the `_r3` layers with a dashed zone outline and an R3 sentence in the captions; map 17 unchanged (no zone hromadas). Also fixed: hatched occupied layer on pages 01–03; page 20 caption position. Open: page 11 (Gi*) under R3.
- **32 (data package) — done.** `resilience/30_data_package.py` → `publication/data_package/out/` (not in git): 7 tables, `hromadas.gpkg` (layers units, frontline_border), `oblasts.gpkg`, generated `docs/data_dictionary.csv` (106 rows incl. codes), source catalogue, README / ATTRIBUTION / CITATION with placeholders from `numbers.yaml`, licence texts, `SHA256SUMS`; 19 files, 33.7 MB. R2: hromada light to Mar 2026, reliable hromadas only, trajectory metrics recomputed at `PUB_END`. R3: the 34 touched raions aggregated as a whole (337 hromadas; zone part alone would allow recovery by subtraction), 1,460 unit rows. R4: military PIT removed from revenue and own funds. Oblast context (DTM, reSCORE) not included (terms). Code not copied; README points to the repository release. Automatic checks: no R4 columns, no light after PUB_END, no hromada of a touched raion. Still pending: DREAM reply, contact address, access dates and versions (request 25), release date and DOIs, run time.
- **25 (access dates and versions) — done.** From raw download timestamps and source metadata: COD-AB v05 (valid from 1 Sep 2025, HDX release 26 Jan 2026, accessed 22 Sep 2026; the earlier "January 2025" was wrong); openbudget 22–25 Sep, DREAM 24 Sep, reSCORE 24 Sep, DTM 24–25 Sep 2026; OSM = live basemap tiles, retrieved 26 Sep 2026 (no extract); DREAM period 5 Sep 2023 – 30 Jul 2026 (`cdu_response.date`, all 16,172 projects).
- **15 (Lviv trust) — done.** reSCORE 2024 trust in local administration: Lviv 4.9, national 4.5 → `trust_diff_lv` = 0.4 (same basis as IF 1.8, CV 1.3, ZK −2.2, TE −1.1).
- **9 (reSCORE by oblast) — key only.** `n_rescore_oblasts` = 23 (22 oblasts + Kyiv city with 2024 values). Still open: n and 95 % CI per indicator for Table 10.
- **29 (IDP details) — key only.** `n_dtm_oblasts`: registered IDPs 24 oblasts (Jul 2026), IDPs present 21 (Mar 2026). Base month, denominator and Figure 3 still open.
