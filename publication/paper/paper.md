---
title: "Strikes, fiscal capacity and night-light recovery in Ukraine's hromadas, 2022–2026"
subtitle: "A spatial analysis with open data"
author: "Michel Garand, UBEC Platform"
version: "v0.2 — internal draft (trajectory results added)"
date: "September 2026"
licence: "Text and figures CC BY 4.0. Data package ODbL 1.0. Code MIT."
---

<!--
Conventions
- {{key}}         value taken from publication/numbers.yaml at build time
- [[PENDING: …]]  missing result; the request number refers to the pipeline request list
- Annexes A–F are compiled from project files at build time; Annex G is written here.
-->

## 0. Key findings

This working paper links Russian strike exposure, local fiscal capacity and night-time light across Ukraine's hromadas (municipal communities), from 2021 to {{nl_panel_end}}. The analysis is descriptive and associational. It does not estimate causal effects.

1. **Fiscal capacity and exposure are nearly unrelated.** Across {{n_capacity}} non-occupied hromadas, the fiscal capacity index correlates with strike and air-raid-alert exposure at only ρ = {{rho_cap_exp_min}} to {{rho_cap_exp_max}}. Hromadas with stronger and weaker local finances are exposed at broadly similar levels.

2. **Night-time light is lower where exposure is higher, above all where alerts have lasted longest.** For the recent light level, the rank correlation with alert hours is {{rho_level_alerts}} nationally and {{rho_level_alerts_within}} within oblasts. Alert hours are a stronger predictor than recorded strike counts.

3. **Light has plateaued well below pre-war levels, and most of the variation is oblast-wide.**
   - Nationally, the median hromada fell to {{nl_march2022}} of its pre-war light in March 2022, recovered to {{nl_h2_2023}} in the second half of 2023, and fell again to {{nl_trough_2024_median}} in the outages of June–July 2024.
   - Since late 2024 it has stayed at about {{nl_plateau}}, with no upward trend. This plateau reflects darkened streets and grid conditions as much as damage: it does not mean that 60 % of the country is destroyed.
   - Oblast fixed effects raise the explained variance of the annual recovery ratio from R² = {{r2_no_fe}} to {{r2_fe}}. In July 2024 even the brightest oblasts dimmed together, a pattern shared across the grid.

4. **Within oblasts, hromadas with more capacity lost relatively less light when the grid failed.** During the summer-2024 outages, hromadas with higher *pre-war* fiscal capacity kept more of their own previous light than others in the same oblast (+{{outage_cap_prewar}}, t = {{outage_cap_prewar_t}}; low residual spatial dependence). This is the most robust capacity result in the study. The data cannot identify the mechanism: backup power, better-maintained networks or a different local economy are all possible.

5. **Capacity did not help in the acute phase, and its association with light levels is partly reverse.**
   - In each hromada's worst quarter, mostly in 2022, pre-war capacity made no difference ({{worstq_cap_prewar}}).
   - For the annual recovery ratio and the recent light level, the association with 2025 capacity (+{{cap_main_fe_min}} to +{{cap_main_fe_max}}; +{{level_cap_fe}}) roughly halves with pre-war capacity (+{{cap_main_fe_2021}}; +{{level_cap_prewar}}). Part of the 2025 association runs from local economic activity to both light and revenue.

6. **We find no evidence that local capacity buffers the effect of exposure.**
   - Without fixed effects, the capacity × exposure interaction is positive (+{{int_baseline_coef}}, t = {{int_baseline_t}}).
   - With oblast fixed effects it is approximately zero for the annual ratio, the recent level, the worst quarter and the outage loss.
   - For the 2024–26 trend it is slightly negative ({{slope_int}}, t {{slope_int_t}}): capacity helps the trend less where exposure is high.
   - The apparent buffering in the pooled model reflects differences between oblasts.

7. **The Carpathian region is quieter and brighter, but not uniformly poorer or more trusting.**
   - A typical Carpathian hromada spent about {{carp_alert_hours_12m}} hours under alert in the last 12 months, against about {{nat_alert_hours_12m}} nationally.
   - Its recent light level is {{carp_level_recent}} of pre-war, against {{rest_level_recent}} elsewhere.
   - Fiscal capacity is below the national median in three of the four oblasts; Lviv is above it.
   - In the reSCORE 2024 survey (n = {{rescore_n}}), trust in local administration is far above the national average ({{trust_national}}) in Ivano-Frankivsk (+{{trust_diff_if}}) and Chernivtsi (+{{trust_diff_cv}}), but far below it in Zakarpattia ({{trust_diff_zk}}). Zakarpattia is the brightest of the four. [[PENDING: Lviv trust difference — request 15]]

8. **Money and people moved west, and are partly moving on.**
   - Civilian income tax in Carpathian hromadas, relative to 2021 and to the national median, peaked at {{pit_carp_peak}} in 2022 Q2–Q3 and has settled at {{pit_carp_recent}}.
   - Within oblasts, higher exposure goes with lower relative income tax ({{pit_exp_recent}}), consistent with taxpayers relocating away from exposed areas.
   - Registered IDPs in the Carpathian oblasts exceed those present by {{idp_west_gap}} (Zakarpattia: {{idp_reg_zk}} registered vs {{idp_present_zk}} present per 1,000 residents). Registrations there have fallen by {{idp_carp_decline}} since February 2023, while rising in Kherson (+{{idp_rise_ks}}), Sumy (+{{idp_rise_su}}) and Kyiv city (+{{idp_rise_kc}}).
   - Real own revenue of hromadas has been roughly flat since 2021.

**What this paper does not show.** It does not show that local fiscal capacity causes recovery. It says nothing about individuals, only about hromadas and oblasts. It does not describe conditions in occupied territory. It does not describe anything below the hromada level, or current power conditions in any hromada.

## 1. Introduction

### 1.1 Context

Since February 2022, Russian strikes have reached nearly every region of Ukraine. Since autumn 2022 they have repeatedly targeted the electricity system. The war arrived shortly after the 2015–2020 decentralisation reform. That reform consolidated local government into hromadas, which now keep a share of personal income tax and manage their own budgets, and which have carried much of the everyday response to the war: shelters, displaced people, utilities and local services.

That combination raises an obvious question for recovery planning. Do hromadas with stronger local finances cope better with the same level of attack? If they do, strengthening local fiscal capacity would be a recovery priority in its own right. If they do not, the reasons matter: perhaps recovery is governed by systems larger than any hromada, such as the national grid.

### 1.2 Questions

The paper asks four questions:

1. Is local fiscal capacity related to how exposed a hromada has been to strikes and air-raid alerts?
2. Does recovery, measured with night-time lights, vary with exposure and with capacity?
3. Does capacity moderate the association between exposure and recovery, so that stronger hromadas lose less for the same exposure?
4. How do oblast-level differences in trust, cohesion and displacement frame these results, particularly in the Carpathian region (Zakarpattia, Ivano-Frankivsk, Lviv and Chernivtsi oblasts)?

### 1.3 Approach and contribution

We assemble a hromada-level dataset for {{n_hromadas_total}} spatial units, of which {{n_hromadas_nonoccupied}} are in non-occupied territory, from open sources:
- strike events (VIINA) and air-raid alerts;
- local budget execution (openbudget.gov.ua);
- monthly night lights (NASA Black Marble);
- gridded population (JRC GHS-POP);
- reconstruction projects (DREAM).

From these we build three indices:
- a **fiscal capacity index** from own revenue, transfer dependency, capital spending and civilian income-tax growth;
- a **night-light recovery ratio**, comparing lit-pixel ratios for 2024 and winter 2024–25 against pre-war baselines;
- an **engagement measure**, DREAM reconstruction projects per 10,000 residents, kept separate because it responds to damage.

We relate these indices using pooled models, oblast fixed-effects models and spatial diagnostics, and set them against oblast-level survey (reSCORE 2024) and displacement (IOM DTM) data.

The contribution is threefold:
- An open, reproducible hromada-level dataset joining exposure, local finance and night-light data, released with its code, data dictionary and source catalogue.
- A transparent test of the "local capacity buffers exposure" hypothesis, including a clear negative result once oblast-level differences are controlled.
- A regional reading of the Carpathian oblasts that keeps survey, displacement and fiscal evidence at the levels where they are actually measured.

A note on terms: we use "resilience" only as a label for the research area. What we actually measure are proxies (fiscal indicators and night-time lights), and the text names them as such throughout.

### 1.4 Structure

- Section 2 defines the spatial units and coverage.
- Section 3 describes the data sources.
- Section 4 describes exposure.
- Section 5 constructs the indices.
- Sections 6 and 7 present the relationships and models.
- Section 8 covers monthly trajectories.
- Section 9 covers oblast social and displacement context.
- Section 10 focuses on the Carpathian region.
- Section 11 sets out limitations.
- Section 12 describes the rules applied to protect sensitive information.
- Section 13 documents reproducibility.

### 1.5 Author's position

The author lives in the Carpathian region of Ukraine and writes field dispatches from it (*Soil and Peace — Carpathian Dispatch 2026*). That proximity shaped the regional focus of section 10. All results are nevertheless computed nationally, with the same methods for every oblast.

## 2. Spatial units and coverage

### 2.1 The hromada frame

The unit of analysis is the hromada, identified by the hromada-level (k3) segment of the KATOTTH administrative codifier. The frame contains {{n_hromadas_total}} units:

- **Mainland Ukraine:** {{n_mainland_codab}} hromada polygons from the OCHA Common Operational Dataset of administrative boundaries (COD-AB, level 3).
- **Crimea and Sevastopol:** {{n_crimea_units}} units. Hromadas were never formed there, so COD-AB has no level-3 boundaries. We represent these territories with a tessellation built from settlement locations. These units exist so that strike and alert exposure can be mapped consistently. They do not enter any index or model.

All geometry is projected to a Lambert Azimuthal Equal Area projection centred on Ukraine (UA_LAEA; `+proj=laea +lat_0=48.5 +lon_0=31 +x_0=0 +y_0=0 +ellps=GRS80 +units=m +no_defs`), so that areas and densities are comparable across the country.

### 2.2 Occupation status

Each unit is classified as occupied or non-occupied from the VIINA territorial-control data, using the latest control status of each settlement on 19 September 2026. A hromada is classed as occupied when settlements holding at least half of its population are under Russian control or contested; Crimea and Sevastopol are classed as occupied throughout. {{n_hromadas_nonoccupied}} units are non-occupied. Indices and models are restricted to these, because budget execution, night-light comparisons and survey data are either unavailable or not comparable for occupied territory. Exposure maps (section 4) cover the whole frame.

### 2.3 Coverage by measure

Coverage falls from the full frame to each index, for different reasons (Table 1).

**Table 1. Coverage by measure**

| Measure | Level | Units covered | Reason for drop from the non-occupied frame |
|---|---|---|---|
| Spatial frame | Hromada | {{n_hromadas_total}} | none |
| Non-occupied frame | Hromada | {{n_hromadas_nonoccupied}} | none |
| Strike and alert exposure | Hromada | {{n_hromadas_total}} | none |
| Fiscal capacity index | Hromada | {{n_capacity}} | [[PENDING: request 1]] |
| Night-light recovery ratio | Hromada | {{n_recovery}} | [[PENDING: request 1]] |
| Engagement (DREAM projects) | Hromada | {{n_engagement}} | [[PENDING: request 1]] |
| reSCORE 2024 indicators | Oblast | {{n_rescore_oblasts}} oblasts | Donetsk, Luhansk and Crimea not surveyed |
| IOM DTM displacement | Oblast | {{n_dtm_oblasts}} oblasts | Only oblast level served for Ukraine |

The largest drop, from {{n_hromadas_nonoccupied}} to {{n_recovery}} hromadas for the recovery ratio, matters for interpretation: the excluded hromadas are not a random subset (section 11.5).

## 3. Data sources

All inputs are open, aggregated data. None contains personal data. Table 2 lists each source with its level, period and licence. The full source catalogue, with access dates and versions, is in Annex B.

**Table 2. Data sources**

| Source | Content used | Native level | Period | Licence / terms |
|---|---|---|---|---|
| VIINA 2.0 | Geocoded strike events | Point / settlement | {{period_viina}} | ODbL 1.0 |
| Air-raid alert records (Klimenko) | Alert start and end times | Oblast / raion / hromada | {{period_alerts}} | MIT |
| OCHA COD-AB (from SSPE Kartographia) | Administrative boundaries | ADM3 polygons | {{version_codab}} | CC BY-IGO |
| openbudget.gov.ua | Local budget execution: revenue by code, expenditure by economic classification | Hromada budget | 2021 Q1 – 2026 Q2, quarterly | Open data, CMU resolution 835 |
| NASA Black Marble VNP46A3 | Monthly night-time radiance | ~500 m raster | Jan 2020 – Aug 2026, monthly | Public domain |
| JRC GHS-POP R2023A | Population, 2020 epoch | 100 m raster | 2020 | EC reuse policy (attribution) |
| DREAM | Reconstruction projects | Project, geocoded to hromada | {{period_dream}} | [[PENDING: terms — request 23]] |
| reSCORE Ukraine 2021, 2024 (SeeD–UNDP) | Trust, cohesion, locality satisfaction, belonging | Oblast | 2021, 2024 | [[PENDING: terms — request 23]] |
| IOM DTM (API v3) | Registered IDPs by host and origin oblast; IDPs present (survey) | Oblast | Feb 2022 – Aug 2026; Aug 2024 – Mar 2026 | IOM terms of use |
| OpenStreetMap | Basemap tiles only (maps) | Vector | {{version_osm}} | ODbL 1.0 |
| Regional statistics offices | ЄДРПОУ enterprise tables: legal entities and sole proprietors by hromada; regional supplement for the Carpathian profile only (partial coverage), not used in the indices or models | [[PENDING]] | [[PENDING]] | Open data |

Three properties of the sources shape the analysis:

- **Level.** Exposure, finance, night lights, population and projects are available at hromada level. Survey and displacement data are available only at oblast level, so they appear only in the oblast context (section 9) and never as hromada-level predictors.
- **Timing.** Budget and night-light series start before February 2022, which allows pre-war baselines. Survey data has a 2021 wave but only oblast estimates. Displacement data starts with the invasion.
- **Reporting.** Strike events come from open-source reporting and are affected by reporting density (section 11.4). Alerts, budgets and night lights are recorded administratively or by instrument.

Attribution for every source is given in `ATTRIBUTION.md` of the data package and in the caption of every map.

## 4. Exposure

### 4.1 Strike events

Strike exposure is built from VIINA events of the following types: airstrikes and missile strikes, drone (UAV) strikes, artillery shelling and air-defence engagements, attributed to Russian forces and not initiated by Ukrainian forces. We use VIINA's `event_1pd` files, in which repeated reports of the same event are already merged (the number of reports is kept). Events in places under Russian control or contested are excluded. Hromada-level counts use only events geocoded to a settlement or street, and drop single-report events in places with fewer than 2,000 residents. Each event is assigned to the hromada containing its point location. Exposure is expressed as a count of events (in the models, the logarithm of one plus the count of all events since the invasion); maps also show events per 1,000 km² and per 100,000 residents (hromadas with at least 1,000 residents) over {{period_viina}}.

### 4.2 Air-raid alert hours

Alert exposure is the cumulative number of hours a hromada spent under an active air-raid alert over the 12 months from 1 September 2025 to 31 August 2026 (records cover {{period_alerts}}). Alerts have been declared at oblast, raion and, increasingly, hromada level. A hromada is treated as under alert whenever an alert covers the hromada itself, its raion or its oblast; overlapping alerts are merged so that no hour is counted twice. From September 2026 the single alert was replaced by yellow (drone) and red (massive or missile) threat levels under Cabinet Resolution No. 1092, with changed territorial and siren rules. Because the new records are not comparable, the series ends on 31 August 2026 and no later data are spliced in. Because alerts are recorded administratively, this measure does not depend on media reporting and covers frontline and rear areas on the same basis.

### 4.3 Composite risk index

Map 01 shows a recency-weighted strike index on H3 resolution-5 cells: each settlement-precision strike event is weighted by 0.5^(a/182.5), where a is its age in days (a six-month half-life); the weights are summed per cell and scaled to 0–100 relative to the most affected cell. Alert hours are not part of this index. It is used for mapping only. The models in section 7 enter strikes and alert hours separately.

### 4.4 Spatial pattern

<!-- begin table: figures/table03_exposure.md (resilience/26_publication_tables.py) -->
**Table 3. Exposure of non-occupied hromadas, by oblast**

| Oblast | Hromadas | With ≥ 1 strike, % | Strikes, median | Strikes, IQR | Strikes, max | Alert hours, median | Alert hours, IQR | Alert hours, max |
|---|---|---|---|---|---|---|---|---|
| Cherkasy | 66 | 11 | 0 | 0–0 | 105 | 985 | 721–985 | 994 |
| Chernihiv | 57 | 26 | 0 | 0–1 | 582 | 3,387 | 2,812–3,387 | 4,785 |
| Chernivtsi | 52 | 6 | 0 | 0–0 | 22 | 132 | 132–132 | 156 |
| Dnipropetrovsk | 82 | 33 | 0 | 0–1 | 2,546 | 2,100 | 1,934–3,002 | 7,315 |
| Donetsk | 11 | 73 | 11 | 0–88 | 403 | 7,718 | 7,718–7,718 | 7,721 |
| Ivano-Frankivsk | 62 | 5 | 0 | 0–0 | 50 | 113 | 113–115 | 115 |
| Kharkiv | 51 | 73 | 4 | 0–28 | 2,867 | 4,629 | 4,291–4,856 | 6,806 |
| Kherson | 16 | 81 | 14 | 2–35 | 2,431 | 1,800 | 1,606–1,800 | 1,800 |
| Khmelnytskyi | 60 | 13 | 0 | 0–0 | 71 | 205 | 198–214 | 214 |
| Kirovohrad | 49 | 16 | 0 | 0–0 | 261 | 1,129 | 822–1,129 | 1,183 |
| Kyiv | 70 | 43 | 0 | 0–5 | 71 | 747 | 649–949 | 1,218 |
| Kyiv City | 1 | 100 | 3,681 | 3,681–3,681 | 3,681 | 578 | 578–578 | 578 |
| Lviv | 73 | 15 | 0 | 0–0 | 453 | 113 | 109–117 | 119 |
| Mykolaiv | 52 | 31 | 0 | 0–1 | 1,154 | 1,283 | 835–1,536 | 1,536 |
| Odesa | 91 | 27 | 0 | 0–1 | 1,404 | 1,125 | 733–1,127 | 1,214 |
| Poltava | 60 | 17 | 0 | 0–0 | 278 | 1,807 | 1,328–2,462 | 2,462 |
| Rivne | 64 | 8 | 0 | 0–0 | 26 | 226 | 156–226 | 303 |
| Sumy | 51 | 61 | 2 | 0–10 | 327 | 4,624 | 3,507–5,900 | 5,900 |
| Ternopil | 55 | 7 | 0 | 0–0 | 106 | 147 | 146–147 | 147 |
| Vinnytsia | 63 | 6 | 0 | 0–0 | 219 | 327 | 314–361 | 366 |
| Volyn | 54 | 7 | 0 | 0–0 | 85 | 144 | 144–146 | 163 |
| Zakarpattia | 64 | 8 | 0 | 0–0 | 30 | 92 | 91–213 | 213 |
| Zaporizhzhia | 19 | 53 | 1 | 0–52 | 2,722 | 5,898 | 5,898–5,898 | 5,905 |
| Zhytomyr | 66 | 9 | 0 | 0–0 | 177 | 543 | 418–543 | 725 |
| Ukraine (non-occupied) | 1,289 | 23 | 0 | 0–0 | 3,681 | 674 | 147–1,536 | 7,721 |

Strikes: VIINA settlement-precision events attributed to Russian forces, 24 Feb 2022 – 19 Sep 2026, per hromada. Alert hours: hours under air-raid alert, 1 Sep 2025 – 31 Aug 2026 (hromada, raion or oblast alert; overlaps merged). IQR = interquartile range.
<!-- end table: figures/table03_exposure.md -->

Exposure has a clear east–west gradient, with concentrations along the front line, in the border oblasts and around major cities (Maps 01 and 04). Kernel density estimation (Map 07) and hot-spot analysis (Getis-Ord Gi*, Map 09) identify the same clusters. IDW and kriging surfaces (Annex D) are shown for comparison only. They interpolate between reported locations and should not be read as estimates for places without recorded events.

**Figures:** Map 01 — risk index by hromada. Map 04 — cumulative alert hours. Map 07 — strike density (KDE). Map 09 — Gi* hot and cold spots.

## 5. Indices

All indices are computed for non-occupied hromadas and expressed as percentile ranks (0–100), so they are comparable in scale but not in absolute level.

### 5.1 Fiscal capacity index

The capacity index combines four budget indicators:

| Component | Definition | Direction |
|---|---|---|
| Own revenue per capita | Own (non-transfer) revenue, 2025, per GHS-POP 2020 resident, log | + |
| Transfer dependency | Transfers as share of total revenue, 2025 | − |
| Capital spending share | Capital expenditure as share of total expenditure, 2023–2025 | + |
| Civilian income-tax growth | Growth of civilian personal income tax 2021–2025, relative to the national median | + |

Components are combined as the mean of their percentile ranks, after winsorising each at the 2nd and 98th percentiles and orienting it so that higher values mean more capacity; a hromada needs at least three of the four components. The first principal component explains {{cap_pc1_share}} of the variance of the four components. Dropping any one component leaves the index almost unchanged (leave-one-out ρ ≥ {{cap_loo_rho_min}}). [[PENDING: Table 4, loadings and leave-one-out correlations — request 3]]

Two points of interpretation:

- **Pre-war version.** Because civilian income-tax growth partly reflects recovery itself, we also compute capacity from 2021 data only. That version is the primary predictor in section 7 (see section 11.11).
- **Garrison hromadas.** {{n_garrison}} hromadas had military payroll above a quarter of their 2021 income tax. Their revenue reflects where units were paid rather than local economic activity. They stay in the index and are excluded only in a sensitivity check. The flag is not published at hromada level (section 12).

### 5.2 Night-light recovery ratio

The recovery ratio compares night-time light before and during the war, over the pixels of each hromada that were lit in 2021. A pixel counts as lit if its mean 2021 radiance is at least 1.0 nW/cm²/sr (VNP46A3 monthly composites, snow-free, with the snow-covered composite where no snow-free value exists). For each hromada we compute two ratios:

- **Annual:** light in 2024 relative to 2021.
- **Winter:** light in winter 2024–25 relative to winter 2020–21 (December to February).

The two ratios are closely correlated (ρ = {{rho_recovery_windows}}) and are combined as the mean of their percentile ranks; a hromada with only one valid ratio takes that ratio's rank. Hromadas with fewer than {{min_lit_pixels}} lit pixels are excluded, because ratios on very small counts are unstable. This rule accounts for most of the drop to {{n_recovery}} hromadas.

**Baseline.** 2021 was about {{nl_2021_vs_2020}} brighter than 2020 at the median, probably from LED retrofits and possibly from COVID-dimmed activity in 2020. The annual ratio uses a 2021-only baseline and therefore understates recovery by roughly {{nl_baseline_shift}}; the ranking of hromadas is unaffected. The monthly index in section 8 uses the more conservative mean of 2020 and 2021.

Using lit pixels rather than all pixels reduces the influence of newly lit or very bright isolated sources, such as industrial sites. It does not remove the effects of blackouts or reduced street lighting (section 11.1).

### 5.3 Engagement

Engagement is the number of valid DREAM reconstruction projects per 10,000 residents ([[PENDING: definition of "valid" — request 23]]). It is kept separate from capacity and recovery because projects are registered in response to damage. Combining it with the other indices would mix a response to exposure with the outcomes we want to compare against exposure.

**Figures and tables:** Map 16 — recovery ratio quintiles. Table 4 — capacity index loadings and robustness.

## 6. Capacity and exposure

### 6.1 Correlation

Fiscal capacity and exposure are nearly independent. Across the {{n_capacity}} hromadas with a capacity score, the rank correlation between capacity and exposure lies between ρ = {{rho_cap_exp_min}} and ρ = {{rho_cap_exp_max}}, depending on the exposure measure (Table 5).

**Table 5. Rank correlations between fiscal capacity and exposure**

| | Strike exposure | Alert hours |
|---|---|---|
| Capacity 2025 | {{rho_cap_strikes_2025}} [{{ci_cap_strikes_2025}}] | {{rho_cap_alerts_2025}} [{{ci_cap_alerts_2025}}] |
| Capacity 2021 (pre-war) | {{rho_cap_strikes_2021}} [{{ci_cap_strikes_2021}}] | {{rho_cap_alerts_2021}} [{{ci_cap_alerts_2021}}] |
| Capacity 2025, within oblasts | {{rho_cap_strikes_within}} | {{rho_cap_alerts_within}} |
| Capacity 2021 (pre-war), within oblasts | {{rho_cap_strikes_2021_within}} | {{rho_cap_alerts_2021_within}} |

*Spearman ρ with 95 % confidence intervals (Fisher z, Bonett–Wright standard error); n = 1,288. Within-oblast values are partial correlations after removing oblast means of the ranks.*

The small positive correlation is consistent with larger urban hromadas being both better resourced and more often targeted and reported (section 11.4). It is too weak to matter for the models that follow: capacity is not a stand-in for exposure, and both can enter the same model without collinearity problems. Pre-war capacity is different. It correlates with alert hours at ρ = {{rho_cap_alerts_2021}} and with strikes at ρ = {{rho_cap_strikes_2021}}. The alert association is regional: within oblasts it falls to ρ = {{rho_cap_alerts_2021_within}}. Hromadas in the east and centre had stronger own finances before 2022 and now spend the most hours under alert; the gap to the west has narrowed since (section 10.1). Within oblasts, pre-war capacity and strikes keep a small positive association (ρ = {{rho_cap_strikes_2021_within}}), the same urban pattern as above. Models with pre-war capacity therefore rely on oblast fixed effects to separate capacity from regional exposure.

### 6.2 Where low capacity meets high exposure

Maps 14 and 15 cross capacity terciles with exposure terciles. Each hromada falls into one of nine classes. The class of practical interest is high exposure with low capacity: hromadas that face the most sustained pressure with the weakest own finances.

<!-- begin table: figures/table06_terciles.md (resilience/26_publication_tables.py) -->
**Table 6. Hromadas by capacity and exposure class**

Classes as drawn on Maps 14, 15 and 17 (codes = exposure class + capacity class; 1 = low). Capacity and alert hours: terciles among non-occupied hromadas. Strikes: low = no strike since 24 Feb 2022; middle and high split the struck hromadas at their median. Carpathian panels on national classes are subsets of the national tables; the regional panel re-computes terciles within the four oblasts.

**Alert hours, national terciles, Ukraine (non-occupied)**

|  | Low capacity | Middle | High capacity |
|---|---|---|---|
| High exposure | 104 | 157 | 169 |
| Middle | 114 | 157 | 158 |
| Low exposure | 212 | 115 | 102 |

n = 1,288 classified; 1 without a class.

**Strike exposure, national classes, Ukraine (non-occupied)**

|  | Low capacity | Middle | High capacity |
|---|---|---|---|
| High exposure | 55 | 25 | 59 |
| Middle | 30 | 62 | 60 |
| Low exposure | 345 | 342 | 310 |

n = 1,288 classified; 1 without a class.

**Alert hours, national terciles, Carpathian oblasts**

|  | Low capacity | Middle | High capacity |
|---|---|---|---|
| High exposure | 0 | 0 | 0 |
| Middle | 0 | 0 | 0 |
| Low exposure | 126 | 58 | 67 |

n = 251 classified.

**Strike exposure, national classes, Carpathian oblasts**

|  | Low capacity | Middle | High capacity |
|---|---|---|---|
| High exposure | 0 | 1 | 6 |
| Middle | 2 | 5 | 8 |
| Low exposure | 124 | 52 | 53 |

n = 251 classified.

**Alert hours, regional terciles (Map 17), Carpathian oblasts**

|  | Low capacity | Middle | High capacity |
|---|---|---|---|
| High exposure | 36 | 30 | 18 |
| Middle | 23 | 27 | 33 |
| Low exposure | 25 | 26 | 33 |

n = 251 classified.
<!-- end table: figures/table06_terciles.md -->

Nationally, all nine cells are populated, but not evenly. Low alert exposure goes with low capacity in 212 hromadas, 126 of them in the four Carpathian oblasts, in line with ρ = {{rho_cap_alerts_2025}} (Table 5). The {{n_hilo_alerts}} hromadas with high alert exposure and low capacity lie in 11 oblasts in the north-east, east and south: Sumy (20), Kharkiv (18), Kherson (15), Dnipropetrovsk (11), and Chernihiv, Donetsk and Zaporizhzhia (9 each). On strikes the same cell holds {{n_hilo_strikes}} hromadas, led by Kharkiv, Sumy and Kherson. No Carpathian hromada reaches the national middle or top alert tercile, so Map 17 classifies the Carpathian oblasts on regional terciles; on that scale {{n_hilo_carp_regional}} hromadas combine relatively high exposure with low capacity.

**Figures:** Map 14 — alert hours × capacity (bivariate 3×3). Map 15 — strikes × capacity (bivariate 3×3).

## 7. Recovery models

### 7.1 Specification

The outcome is the night-light recovery ratio (section 5.2) for the {{n_model}} hromadas with both a recovery and a capacity score. The core model is

$$
R_i = \beta_1 C_i + \beta_2 E_i + \beta_3 (C_i \times E_i) + \alpha_{o(i)} + \varepsilon_i
$$

where $R_i$ is recovery, $C_i$ fiscal capacity, $E_i$ exposure and $\alpha_{o(i)}$ an oblast fixed effect. Variables are standardised. Standard errors are heteroskedasticity-robust (HC1); they do not account for residual spatial dependence (section 11.10). [[PENDING: wild-cluster bootstrap and spatially robust errors — requests 4, 5]]

- $\beta_3$ tests **buffering**. A positive value would mean that, for the same exposure, higher-capacity hromadas lose less.
- $\beta_1$ is the **main effect of capacity**: the difference in recovery between hromadas of different capacity at average exposure.
- The oblast fixed effects absorb everything shared by all hromadas in an oblast: grid conditions and outage schedules, distance to the front, regional economy and oblast-level administration.

**Table 7. Model specifications** [[PENDING: exact specifications M1–M7 — request 4]]

| Model | Oblast FE | Capacity measure | Exposure measure | Sample / other |
|---|---|---|---|---|
| M1 | No | 2025 | | All |
| M2 | Yes | 2025 | | All |
| M3–M7 | Yes | | | |

### 7.2 Pooled model: apparent buffering

Without fixed effects (M1), the interaction is positive and precisely estimated: β₃ = +{{int_baseline_coef}}, t = {{int_baseline_t}}. Taken alone, this would suggest that local capacity softens the loss of night-time light in heavily exposed hromadas. The model explains little of the variation in recovery (R² = {{r2_no_fe}}).

### 7.3 With oblast fixed effects: no buffering

Adding oblast fixed effects changes the picture in two ways.

- **The model fit changes sharply.** R² rises from {{r2_no_fe}} to {{r2_fe}}. Most of the variation in night-light recovery is between oblasts, not within them. [[PENDING: within-R² for each fixed-effects model — request 4]]
- **The interaction disappears.** In every fixed-effects specification (M2–M7), β₃ is approximately zero ({{int_fe_range}}). [[PENDING: estimates and bootstrap p-values — request 4]]

The buffering found in M1 is therefore a between-oblast pattern. Oblasts where hromadas have higher capacity on average also happen to recover better at a given exposure, most plausibly because of differences in grid conditions and distance from the front. Among hromadas within the same oblast, higher capacity does not go with a smaller loss at higher exposure.

We report this as the central result of the paper: **within oblasts, we find no evidence that local fiscal capacity buffers the association between exposure and night-light recovery.**

### 7.4 Main effect of capacity

Within oblasts, capacity is positively associated with recovery at average exposure. The coefficient is +{{cap_main_fe_min}} to +{{cap_main_fe_max}} (t {{cap_main_fe_t}}) across models using the 2025 index.

This estimate is inflated by construction. The 2025 index includes civilian income-tax growth from 2021 to 2025, which partly reflects the same recovery the outcome measures (section 11.11). Using pre-war (2021) capacity instead, the coefficient falls to +{{cap_main_fe_2021}} (t {{cap_main_fe_2021_t}}, HC1). Removing income-tax growth from the 2025 index, and keeping its other three components, gives +{{cap_main_fe_no_pitgrowth}} (t {{cap_main_fe_no_pitgrowth_t}}). The income-tax component thus accounts for about a sixth of the 2025 estimate. Most of the gap to the pre-war estimate lies elsewhere: own revenue, transfers and capital spending in 2025 also move with the wartime economy.

We treat the pre-war estimate as the primary result. It says that hromadas with stronger finances before the invasion show modestly better night-light recovery than others in the same oblast. It does not say why. Pre-war capacity is correlated with size, urbanisation and economic structure, any of which could drive the association. A clearer version of this association appears in the summer-2024 outage loss (section 8.5).

### 7.5 Spatial dependence

Recovery is strongly spatially dependent. A spatial lag model gives ρ = {{spatial_lag_rho}}. [[PENDING: which model the spatial lag refers to — request 5]] Even with oblast fixed effects, residuals remain clustered (Moran's I = {{resid_moran_fe}}). There is therefore spatial structure below the oblast level, plausibly grid districts and outage groups, that the models do not capture.

This has two consequences:
- Standard errors that ignore spatial dependence overstate precision.
- The capacity main effect could partly reflect neighbourhood patterns rather than anything specific to each hromada.

[[PENDING: capacity main effect and interaction in spatial lag and spatial error models with oblast FE — request 5]]

### 7.6 Sensitivity

<!-- begin table: figures/table08_sensitivity.md (resilience/27_sensitivity.py) -->
**Table 8. Sensitivity of the capacity estimates**

| Variant | n | β₁ capacity 2021 | β₃ interaction 2021 | β₁ capacity 2025 | β₃ interaction 2025 |
|---|---|---|---|---|---|
| Primary specification | 1,020 | +0.08 (2.3) | −0.01 (−0.2) | +0.18 (6.1) | −0.01 (−0.7) |
| Excluding garrison hromadas | 993 | +0.08 (2.4) | 0.00 (−0.2) | +0.18 (6.0) | −0.01 (−0.8) |
| Excluding frontline and Russian-border oblasts | 881 | +0.08 (2.0) | 0.00 (0.0) | +0.21 (5.8) | +0.01 (0.5) |
| Outcome: winter light ratio only | 1,006 | +0.08 (2.4) | −0.01 (−0.3) | +0.17 (5.5) | −0.01 (−0.4) |
| Outcome: annual light ratio only | 1,020 | +0.07 (1.9) | 0.00 (0.0) | +0.18 (6.0) | −0.01 (−0.7) |
| 2025 capacity without income-tax growth | 1,020 | — | — | +0.15 (4.6) | −0.01 (−0.5) |

Standardised coefficients with t-values (HC1) in brackets; all models with oblast fixed effects and controls (log population 2020, log lit pixels, log 2021 radiance). Outcome: night-light recovery index. Exposure: strikes since 24 Feb 2022. 2021 capacity: own revenue per capita and transfer dependency, 2021 budgets. Frontline and border oblasts: Donetsk, Zaporizhzhia, Kherson, Sumy, Kharkiv, Chernihiv. — = unchanged (the 2021 index does not include income-tax growth).
<!-- end table: figures/table08_sensitivity.md -->

The pre-war capacity coefficient stays between +0.07 and +0.08 in every variant. It is weakest when the outcome is the annual ratio alone (t 1.9), and the interaction is zero throughout. The 2025 index gives larger coefficients in every variant, including without income-tax growth.

### 7.7 What the models support

The models support three statements:
1. Exposure is associated with lower night-light recovery, more strongly for alert hours (ρ = {{rho_rec_alerts}}) than for recorded strikes (ρ = {{rho_rec_strikes}}).
2. Recovery is mostly an oblast-wide pattern, consistent with grid-level rather than local drivers.
3. Within oblasts, pre-war capacity has a small positive association with recovery, and there is no evidence of buffering. Section 8 finds a clearer capacity association for losses during the 2024 outages, and none in the acute phase of 2022.

They do not support the claim that strengthening local finances would, by itself, speed recovery from attacks. Section 8 tests whether monthly trajectories reveal local differences that the annual ratio hides.

**Figures and tables:** Table 7 — specifications. Table 8 — sensitivity. Figure 1 — β₃ with 95 % intervals across M1–M7 [[PENDING: request 4]]. Map 16 — recovery quintiles.

## 8. Trajectories, 2021–2026

The recovery ratio in sections 5–7 compares two periods. It cannot distinguish a hromada that lost light early and recovered from one that declined slowly, or one hit by a single deep outage from one with repeated winter dips. This section uses monthly night-light and quarterly budget panels to follow each hromada over time.

### 8.1 Monthly night-light index

The monthly panel covers January 2020 to {{nl_panel_end}} ({{nl_panel_months}} months) for the {{n_recovery}} hromadas with at least {{min_lit_pixels}} lit pixels.
- **Pixels:** those lit in 2021.
- **Index:** a hromada's radiance in a month divided by its mean radiance in the same calendar month of 2020 and 2021. An index of 1 means as bright as before the war; 0.5 means half as bright. {{nl_two_year_baseline_share}} of hromada-months have a two-year baseline.
- **Exclusion:** June 2025 is excluded as a retrieval artefact.

Comparing each month with the same month before the war removes ordinary seasonal differences, such as snow cover and day length.

**Noise.** Before the war, the index varied from month to month by {{nl_noise_median}} at the median hromada, from {{nl_noise_small}} in hromadas with 10–30 lit pixels to {{nl_noise_large}} in those with more than 1,000. Single months are therefore unreliable for small hromadas. The metrics below use windows and quarters, and a change counts only when it exceeds twice the hromada's own pre-war variation (|z| > 2).

### 8.2 The national trajectory

The median hromada's index traces the phases of the war:

| Period | Median index | Context |
|---|---|---|
| March 2022 | {{nl_march2022}} | Near-total dark-out: blackout orders, curfews |
| September 2022 | {{nl_sep2022}} | Partial return |
| October–November 2022 | {{nl_octnov2022}} | Energy-strike campaign |
| July–December 2023 | {{nl_h2_2023}} | Recovery |
| June–July 2024 | {{nl_trough_2024_median}} | Rolling outages after attacks on generation |
| September 2025 – {{nl_panel_end}} | {{nl_plateau}} | Plateau, no upward trend since late 2024 |

For {{nl_worstq_2022_share}} of hromadas the worst quarter fell in 2022. Measured against each hromada's own pre-war noise, light in the last 12 months compared with July–December 2023 has declined in {{nl_change_nat_decline}} of hromadas, stayed stable in {{nl_change_nat_stable}} and improved in {{nl_change_nat_improve}}.

**Figure 2.** National median monthly index, January 2021 – {{nl_panel_end}}, with interquartile band and major outage periods marked. [[PENDING: export — request 14]]

### 8.3 Carpathian oblasts and the rest

**Table 9. Night-light trajectory, Carpathian oblasts vs the rest of Ukraine (medians)**

| | Carpathian | Rest |
|---|---|---|
| Recent light level (last 12 months) | {{carp_level_recent}} | {{rest_level_recent}} |
| Light level, July–December 2023 | {{carp_level_h2_2023}} | {{rest_level_h2_2023}} |
| Worst quarter | {{carp_worstq}} | {{rest_worstq}} |
| Share of quarters below 0.5 | {{carp_share_q_below_half}} | {{rest_share_q_below_half}} |
| Summer-2024 light as share of H2 2023 level | {{carp_outage_retained}} | {{rest_outage_retained}} |
| Change since H2 2023: declined / stable / improved | {{nl_change_carp}} | {{nl_change_nat}} (national) |

Carpathian hromadas were brighter throughout, and lost a smaller share of their light in the 2024 outages. They were not spared: in July 2024 they too fell to well below their usual level. Section 10 describes differences between the four oblasts.

### 8.4 Trajectory metrics

For each hromada:

| Metric | Definition |
|---|---|
| Recent level | Mean index over the last 12 months |
| Worst quarter | Lowest quarterly mean index after February 2022 |
| Outage loss | Mean index in June–July 2024 divided by the hromada's own July–December 2023 mean |
| Recent slope | Linear trend of the monthly index, 2024–2026 |
| Change class | Last 12 months vs July–December 2023: declined, stable or improved (|z| > 2) |

Outage loss compares each hromada with itself shortly before the 2024 outages. It is therefore less affected by long-standing differences in lighting practice between hromadas than the level measures.

### 8.5 Do trajectories vary with capacity and exposure?

Each metric is modelled like the recovery ratio (section 7.1), with oblast fixed effects. Standard errors are HC1.

**Table 10. Trajectory models with oblast fixed effects (standardised coefficients, t in brackets)**

| Outcome | Capacity 2025 | Pre-war capacity (2021) | Capacity × exposure | Residual Moran's I |
|---|---|---|---|---|
| Outage loss, summer 2024 | +{{outage_cap_fe}} ({{outage_cap_fe_t}}); precision-weighted +{{outage_cap_w}} ({{outage_cap_w_t}}) | +{{outage_cap_prewar}} ({{outage_cap_prewar_t}}) | ≈ 0 | {{outage_moran}} |
| Recent level | +{{level_cap_fe}} ({{level_cap_fe_t}}) | +{{level_cap_prewar}} ({{level_cap_prewar_t}}) | ≈ 0 | {{level_trough_moran}} |
| Worst quarter | +{{worstq_cap_fe}} | {{worstq_cap_prewar}} | ≈ 0 | {{level_trough_moran}} |
| Recent slope, 2024–26 | [[PENDING: request 12]] | [[PENDING: request 12]] | {{slope_int}} ({{slope_int_t}}); R² {{slope_r2}} | [[PENDING: request 12]] |

[[PENDING: exact interaction estimates for the first three rows — request 12]]

**Exposure.** Alert hours are the dominant exposure measure. Their rank correlation with the recent light level is {{rho_level_alerts}} nationally. Within oblasts, the association is {{rho_level_alerts_within}} (t {{rho_level_alerts_within_t}}).

Four results follow.

1. **Outage loss is the clearest capacity result.** Within oblasts, hromadas with more fiscal capacity kept relatively more of their own light when the grid failed in summer 2024. The association holds with pre-war capacity, under precision weighting and with low residual spatial dependence. It is still an association between places. The mechanism may be backup generation, better-maintained local networks or a local economy with more users on priority supply; the data cannot distinguish these.
2. **In the acute phase, capacity did not protect.** The worst quarter, which for most hromadas fell in 2022, is an oblast-wide pattern. Within oblasts, 2025 capacity has a weak association (+{{worstq_cap_fe}}) and pre-war capacity none ({{worstq_cap_prewar}}).
3. **Level results are partly reverse-causal.** The recent light level is associated with 2025 capacity at +{{level_cap_fe}} but with pre-war capacity at only +{{level_cap_prewar}}. Local economic activity plausibly raises both light and income-tax revenue, so the 2025 association overstates any effect of capacity on light.
4. **No buffering, with one small exception.** The capacity × exposure interaction is about zero for level, worst quarter and outage loss, as for the annual ratio in section 7. For the 2024–26 slope it is slightly negative: capacity is associated with a better trend less where exposure is high. The effect is small and the model explains little (R² {{slope_r2}}).

Residual spatial dependence remains for level and worst quarter (Moran's I {{level_trough_moran}}), so HC1 t-values for these outcomes are optimistic.

**Figures:** Map 19 — recent light deficit × fiscal capacity (bivariate 3×3, national terciles). Map 20 — outage loss in quintiles (left) and change classes since H2 2023 (right). Both are subject to the rule in section 8.7.

### 8.6 Budget trajectories

The quarterly budget panel runs from 2021 Q1 to {{budget_panel_end}} ({{budget_panel_quarters}} quarters, {{n_capacity}} hromadas). Its four quarters of 2025 reproduce the annual values used in the capacity index.

- **Military income tax.** From 2022 Q2 to 2023 Q3, military personal income tax formed {{military_pit_share_range}} of local income-tax revenue. From 2023 Q4 it was redirected to the state budget. Civilian income tax stays comparable across that break because military payroll lines are identified by name. The capacity index uses civilian income tax only.
- **Real own revenue is roughly flat.** Nominal own revenue in 2025 was {{own_rev_2025_ratio}} times its 2021 level, about the same as cumulative inflation over the period. [[PENDING: basis of the 2026 H1 figure and CPI series — requests 11, 34]]
- **Relative civilian income tax.** We measure civilian income tax in each quarter relative to the same quarter of 2021, divided by the national median, which makes the measure inflation-neutral.
  - In the Carpathian oblasts it peaked at {{pit_carp_peak}} in 2022 Q2–Q3, consistent with firms and workers relocating westward, and has settled at {{pit_carp_recent}} since late 2023.
  - Within oblasts, higher exposure goes with lower relative income tax, both recently ({{pit_exp_recent}}) and in 2022 ({{pit_exp_2022}}). This fits taxpayers moving away from exposed areas.
  - The negative coefficient of pre-war capacity in these models is partly mechanical: the measure is a ratio to each hromada's own 2021 value, so regression to the mean pulls high 2021 values down. It should not be read as "stronger hromadas declined".

### 8.7 Publication rule for time series

Light levels in the last 12 months describe current power conditions. Under the rules in section 12:
- Hromada-level monthly values are released only for months at least 6 months before release.
- The most recent 12 months are shown at oblast level only.
- Hromadas within 30 km of the front line or border are aggregated to raion level.

Map 19 and the right panel of Map 20 use "recent" windows. For publication, their windows end at least 6 months before release, or they are shown at raion level. [[PENDING: re-windowed or aggregated versions — request 33]] Historical windows (2022–2024), including the outage-loss panel of Map 20, carry lower risk and are published at hromada level.

## 9. Oblast context: trust, cohesion and displacement

Survey and displacement data are available only by oblast. They cannot enter the hromada models: any oblast-level variable is absorbed completely by the oblast fixed effects. This section is therefore descriptive. It asks how oblasts differ in social conditions and displacement, not whether these conditions explain hromada recovery.

### 9.1 Trust, cohesion and satisfaction (reSCORE 2024)

reSCORE Ukraine 2024 surveyed {{rescore_n}} respondents in all oblasts except Donetsk, Luhansk and Crimea. We use four indicators, each on a 0–10 scale: trust in local administration, community cohesion, locality satisfaction and sense of belonging.

**Table 10. Selected reSCORE 2024 indicators by oblast** [[PENDING: full table with sample sizes and 95 % intervals — request 9]]

| Oblast | Trust in local admin. (diff. from national {{trust_national}}) | Community cohesion | Locality satisfaction | Belonging |
|---|---|---|---|---|
| Ivano-Frankivsk | +{{trust_diff_if}} | {{cohesion_if}} (highest) | {{locality_sat_if}} (highest) | |
| Chernivtsi | +{{trust_diff_cv}} | | | |
| Lviv | {{trust_diff_lv}} | | | |
| Zakarpattia | {{trust_diff_zk}} | | | |
| Ternopil | {{trust_diff_te}} | | | |
| Kherson | | | {{locality_sat_ks}} (lowest) | {{belonging_ks}} (highest) |

Two patterns stand out.

- **Western Ukraine is not uniform.** Trust in local administration is well above the national average in Ivano-Frankivsk and Chernivtsi, but below it in Zakarpattia and in neighbouring Ternopil. Regional labels such as "the west" hide differences as large as those between west and east.
- **Attachment is not satisfaction.** Kherson, heavily shelled and partly occupied until November 2022, records the lowest satisfaction with the locality but the strongest sense of belonging. Low ratings of local conditions do not imply weak attachment to the place.

[[PENDING: change 2021 → 2024 in trust and cohesion by oblast — request 28]]

### 9.2 Displacement (IOM DTM)

Two DTM series are available by oblast:
- **Registration:** monthly counts of registered IDPs by host and origin oblast, February 2022 – August 2026. Three months are missing (December 2024, January 2025, March 2025).
- **Presence:** survey estimates of IDPs actually present, from seven rounds between August 2024 and March 2026.

**Registered and present differ systematically, in opposite directions by region.**
- **West:** registered IDPs exceed those present.
  - Zakarpattia: {{idp_reg_zk}} registered vs {{idp_present_zk}} present per 1,000 residents.
  - Ivano-Frankivsk, Lviv and Chernivtsi: {{idp_reg_west_range}} vs {{idp_present_west_range}}.
- **Centre and east:** the relation reverses. Dnipropetrovsk: {{idp_reg_dp}} registered vs {{idp_present_dp}} present.

A plausible reading is that many people registered in the west early in the war, when it was the main destination, and later moved on or returned without deregistering. Meanwhile, many IDPs living in the centre and east are registered elsewhere or not at all. The data cannot confirm this. It does show that neither series alone is a reliable count of the displaced population in a given oblast.

**Registered numbers are shifting.** Since February 2023, registered IDPs have fallen by {{idp_carp_decline}} in the Carpathian oblasts, while rising in Kherson (+{{idp_rise_ks}}), Sumy (+{{idp_rise_su}}) and Kyiv city (+{{idp_rise_kc}}). [[PENDING: confirm that all changes use February 2023 as base — request 29]] The increases in Kherson and Sumy coincide with intensified attacks and evacuations near the front line.

[[PENDING: denominator used for "per 1,000 residents" — request 29]]

**Figures:** Map 18 — oblast context grid: reSCORE differences and IDPs per 1,000. Figure 3 — registered vs present IDPs per 1,000 by oblast [[PENDING: request 29]].

### 9.3 Why these data stay at oblast level

Displacement is the most obvious candidate explanation for the within-oblast capacity association in section 7.4. Hromadas that received many IDPs may have both higher income-tax growth and brighter nights. Testing this requires hromada-level displacement data, which has been requested from IOM. Removing income-tax growth from the capacity index lowers the within-oblast association only modestly (section 7.4), so displacement acting through income tax alone does not explain it. It could still act through other channels, such as own revenue or the demand for lighting. Until hromada-level data are available, the capacity association remains open to this interpretation.

## 10. The Carpathian region

This section applies the national results to the {{n_carp_hromadas}} non-occupied hromadas of four oblasts: {{carpathian_oblasts}}. All figures use the same methods and thresholds as the national analysis. Map 17 shows capacity and exposure as terciles computed within the region, so that differences between Carpathian hromadas are visible rather than lost in the national range.

### 10.1 Profile

**Exposure.**
- A typical Carpathian hromada spent about {{carp_alert_hours_12m}} hours under alert in the last 12 months, against about {{nat_alert_hours_12m}} nationally.
- Fewer than one in ten Carpathian hromadas has recorded a strike since 2022; nationally, more than one in five has.
- Lviv oblast is the most exposed of the four: about {{lviv_struck_share}} of its hromadas have recorded a strike.

**Fiscal capacity** is not uniformly low.
- The median Lviv hromada is above the national median on the capacity index, and Lviv depends least on transfers.
- In Ivano-Frankivsk and Zakarpattia, the median hromada raises about {{own_rev_pc_if_zk}} hryvnias of own revenue per resident, against about {{own_rev_pc_nat}} nationally. Transfers make up more than half its revenue.
- Chernivtsi is weaker still, at under {{own_rev_pc_cv}} hryvnias.

<!-- begin table: figures/table11_carpathian.md (resilience/26_publication_tables.py) -->
**Table 11. Carpathian oblasts and Ukraine, non-occupied hromadas**

| Measure | Zakarpattia | Ivano-Frankivsk | Lviv | Chernivtsi | Carpathian (4 oblasts) | Ukraine (non-occupied) |
|---|---|---|---|---|---|---|
| Hromadas with ≥ 1 strike since 24 Feb 2022, % | 8 (64) | 5 (62) | 15 (73) | 6 (52) | 9 (251) | 23 (1,289) |
| Alert hours, 1 Sep 2025 – 31 Aug 2026 (median) | 92 (64) | 113 (62) | 113 (73) | 132 (52) | 114 (251) | 674 (1,289) |
| Capacity 2021, mean percentile rank 0–100 (median) | 15.2 (64) | 12.9 (62) | 44.3 (73) | 9.9 (52) | 18.5 (251) | 51.3 (1,288) |
| Capacity 2025, mean percentile rank 0–100 (median) | 35.6 (64) | 35.3 (62) | 57.4 (73) | 28.9 (52) | 39.9 (251) | 49.3 (1,288) |
| Night-light recovery ratio 2024 / 2021 (median) | 0.84 (57) | 0.25 (48) | 0.44 (65) | 0.43 (39) | 0.46 (209) | 0.29 (1,021) |

Number of hromadas with a value in brackets. Capacity: mean percentile rank of the capacity components (2021 budgets for 2021; 2025 index). Recovery: mean radiance of pixels lit in 2021, 2024 relative to 2021.
<!-- end table: figures/table11_carpathian.md -->

**Night-time light** is higher than elsewhere (Table 9), but the four oblasts follow four different curves:
- **Zakarpattia** hardly went dark. Its median hromada was brighter in March 2022 than before the war, kept about half its light in the worst months of 2024, and has been near its pre-war level over the last year.
- **Lviv** sits in between, at about 60 % of pre-war light recently, with deep but shorter dips.
- **Chernivtsi** is a little darker. In more than a third of its hromadas light has declined since 2023, the national rate.
- **Ivano-Frankivsk** is as dark as the national median, and in the first war winter darker. Yet it is the least struck of the four.

In July 2024 all four fell together. Even Zakarpattia dropped to about half its usual light, which points to a cause shared across the grid. What drives the differences at other times is not visible in these data. Grid connection and supply in each part of the western network, and oblast and hromada decisions on street lighting, are the obvious candidates. In the Carpathian oblasts, darkness is not a measure of attack.

The national models apply here too. Most of the region's brightness is what oblast fixed effects capture: lower exposure and grid conditions shared across each oblast. It is not evidence that Carpathian hromadas manage recovery better than hromadas elsewhere.

### 10.2 Capacity and outage loss

Within the region, as nationally, hromadas with more fiscal capacity kept relatively more of their light in the 2024 outages. The pattern is also regional. Of the {{carp_weak_hit}} Carpathian hromadas with both low capacity and large outage loss, {{carp_weak_hit_if_cv}} are in Ivano-Frankivsk and Chernivtsi. At the other corner, Lviv (15) and Zakarpattia (12) hold most of the {{carp_strong_steady}} hromadas with high capacity and small losses. Both groups are corners of a regional classification: terciles, within the four oblasts, of the 2025 capacity index and of the light kept in June–July 2024 as a share of the second half of 2023. Low capacity is the bottom third (percentile rank below about 30), a large loss the bottom third of retention (at most 24 % of the 2023 level); the top thirds start at about 52 and 47 %. On the same rule with national terciles, {{nat_weak_hit}} hromadas are weak and hit. Much of what looks like a local story is the grid of the oblast.

### 10.3 Low fiscal capacity, high local trust, but not everywhere

The oblast pattern:
- **Ivano-Frankivsk** combines below-median fiscal capacity with trust in local administration of {{trust_if_abs}} on a 0–10 scale, the highest of the four oblasts. It also records the highest community cohesion and locality satisfaction in the country, and above-average economic security.
- **Chernivtsi** also combines weak finances with trust above the national average (+{{trust_diff_cv}}).
- **Zakarpattia**, the brightest of the four, reports one of the lowest levels of trust in local administration in the country: {{trust_zk_abs}}.
- **Lviv**, the fiscally strongest: [[PENDING: Lviv trust — request 15]]

This is a juxtaposition of two levels of measurement: hromada fiscal data and oblast survey means. It is not a relationship. We cannot say whether the hromadas with low capacity are the ones whose residents report high trust. The observation matters because fiscal indicators alone would rank much of the region as weak. Survey evidence suggests that, in at least two of its oblasts, local government holds a resource the budget data does not measure. Light, budgets and trust point in different directions here: a place can keep its lights on and distrust those who run it, or go dark and hold together.

### 10.4 A region of reception

The Carpathian oblasts gained income tax as firms and workers moved west.
- **2022.** In the third quarter of 2022, the median hromada in all four oblasts collected {{carp_pit_q3_2022_range}} more civilian income tax, relative to its own 2021 level, than the median hromada nationally. Ivano-Frankivsk gained most. The gain was unrelated to fiscal capacity: it followed people, not institutions.
- **Mid-2024.** The advantage had shrunk to a few per cent.
- **2025.** It returned strongly in Lviv and Ivano-Frankivsk (about {{carp_pit_2025_lv_if}} above the national median), and less so in Zakarpattia and Chernivtsi ({{carp_pit_2025_zk_cv}}).

Displaced people show the same movement:
- Registered IDPs range from {{idp_reg_carp_range}} per 1,000 pre-war residents across the four oblasts. IOM's estimate of those actually present is lower and strikingly even: {{idp_present_carp_range}} in all four.
- Registrations have fallen by {{idp_carp_decline}} since February 2023.

Per-capita figures based on pre-war population are therefore especially uncertain here (section 11.6), and in both directions.

### 10.5 What the region suggests for further work

Three questions follow, and none can be answered with current open data:
1. Does local trust or cohesion help hromadas with weak budgets sustain services under pressure? This needs hromada-level survey data.
2. Did hosting IDPs and relocated firms raise civilian income tax, and with it measured capacity, in western hromadas? This needs hromada-level displacement data.
3. What explains the four different light curves: grid topology, supply priorities or lighting policy? This needs grid and policy data by area, released with a security delay.

A fourth can be tested with the existing data: whether mountain and lowland hromadas differ within the region. [[PENDING: optional — request 30]]

## 11. Limitations

The limitations below are ordered by how much they constrain the paper's main claims.

### 11.1 Night lights are an indirect measure of recovery

Night-time light responds to physical damage and economic activity, but also to:
- blackout orders and curfews, as in March 2022;
- rolling outages scheduled across whole oblasts, as in summer 2024;
- deliberate reductions in street lighting since 2022, for security and energy saving.

The national plateau at about {{nl_plateau}} of pre-war light since late 2024 is therefore not "60 % destroyed". A large part of it is policy and grid conditions. We call the measures a *night-light recovery ratio* and a *night-light index*, and do not equate them with economic or social recovery.

Two further measurement issues apply:
- **Baseline choice.** The choice of baseline shifts levels by about {{nl_baseline_shift}} (section 5.2).
- **Monthly noise.** Monthly values are noisy, especially in small hromadas (section 8.1). Single-month values for individual hromadas should not be interpreted; publication of single-hromada values is limited to hromadas with at least [[CHECK: 30 lit pixels, as in the Carpathian dispatch — confirm as the general rule]] lit pixels.

### 11.2 Recovery is dominated by oblast-wide grid patterns

Oblast fixed effects explain most of the variation in the recovery ratio (R² {{r2_no_fe}} → {{r2_fe}}), and residuals remain spatially clustered (Moran's I = {{resid_moran_fe}} with fixed effects). This is consistent with recovery being governed by grid and supply decisions made above the hromada level. It follows that the within-oblast association between capacity and recovery is estimated from a limited share of the total variation, and that claims about the effect of local capacity must stay modest. We make no causal claim.

### 11.3 Ecological inference

All associations are measured between hromadas or between oblasts. They say nothing about individual households, businesses or officials. In particular, the oblast-level survey results (trust, cohesion, satisfaction) cannot be attributed to particular hromadas, and the juxtaposition of low fiscal capacity with high local trust in parts of the Carpathian region is a description at oblast level, not a hromada-level relationship.

### 11.4 Strike counts reflect reporting as well as attacks

VIINA records events reported in open sources. Reporting density is higher where media, local channels and population are denser, and lower near the front line and in occupied areas. Strike counts therefore partly measure visibility. Air-raid alert hours are recorded administratively and do not share this bias, which is one reason we report both. The stronger association of recovery with alert hours than with strike counts may partly reflect this difference in measurement quality.

### 11.5 Under-coverage of occupied and frontline areas

Indices are computed only for non-occupied hromadas ({{n_capacity}} for capacity, {{n_recovery}} for recovery). Budget, survey and displacement data are thin or absent for occupied and frontline areas. [[PENDING: breakdown of the {{n_hromadas_nonoccupied}} → {{n_recovery}} drop by reason and oblast — request 1]] The hromadas most affected by the war are the ones least represented in the models, which likely weakens the observed association between exposure and recovery.

### 11.6 Pre-war population denominators

Per-capita measures use JRC GHS-POP 2020 population. Displacement since 2022 has changed populations substantially, raising them in many western hromadas and lowering them near the front. Per-capita revenue and per-capita project counts are therefore biased: downward where population grew and upward where it fell. No reliable hromada-level wartime population series exists in open data.

### 11.7 Income tax is booked at the employer's address

Personal income tax is attributed to the hromada where the employer is registered, not where the employee lives. Hromadas hosting head offices, large enterprises or military units appear richer than their residents are. We flag {{n_garrison}} hromadas where military payroll made up at least a quarter of 2021 income tax. The flag is used only as a sensitivity check and is not published at hromada level (see section 12). In addition, from Q4 2023 military income tax was redirected from local budgets to the state budget; it had been {{military_pit_share_range}} of local income tax from Q2 2022. This creates a structural break in any budget series crossing that date.

### 11.8 Survey sampling and exclusions

reSCORE 2024 excludes Donetsk, Luhansk and Crimea, and its oblast estimates carry sampling error. [[PENDING: oblast sample sizes and confidence intervals for the trust differences — request 9]] Oblast differences smaller than their confidence intervals are not interpreted.

### 11.9 Registered vs present IDPs, and oblast-only data

IOM DTM data for Ukraine is available to us only at oblast level. Registration figures record where people registered, not where they currently live. The gap between registered and present IDPs (section 9) is itself a finding, but it means neither series is a reliable denominator. Because the displacement figures are oblast-level, they are collinear with oblast fixed effects and cannot enter the hromada models. [[PENDING: hromada-level DTM data requested from IOM]]

### 11.10 Inference: few oblast clusters and spatial dependence

The reported t-values use heteroskedasticity-robust (HC1) standard errors. These do not account for two features of the data:
- **Few clusters.** Hromadas in the same oblast share unobserved conditions, and there are only about two dozen oblasts.
- **Spatial dependence.** Residuals remain spatially clustered for several outcomes (Moran's I {{resid_moran_fe}} for the annual ratio, {{level_trough_moran}} for recent level and worst quarter).

The t-values for these outcomes are therefore optimistic. The outage-loss result, with low residual dependence (Moran's I {{outage_moran}}), is least affected. [[PENDING: wild-cluster bootstrap p-values and spatially robust errors — requests 4, 5]]

### 11.11 Composition of the capacity index

The 2025 capacity index includes civilian income-tax growth from 2021 to 2025, which is partly a consequence of the wartime economy and of recovery itself. This builds a degree of circularity into any model predicting recovery from 2025 capacity. We therefore report pre-war (2021) capacity as the primary specification, and the 2025 index as descriptive. Removing the income-tax component from the 2025 index lowers the within-oblast capacity coefficient to +{{cap_main_fe_no_pitgrowth}} and leaves the interaction at zero, so that component is not what drives the 2025 results.

### What would change the conclusions

The main conclusions would need revision in three cases:
- if hromada-level displacement data showed that population shifts account for the within-oblast capacity association;
- if the monthly trajectory metrics revealed local differences in recovery that the annual ratio hides;
- if a direct measure of grid restoration became available at hromada level.

The first two are in progress.


## 12. Protecting sensitive information

### 12.1 Principles

This study publishes analysis of an ongoing war. Four principles govern every map, table and file released:

1. **Aggregated open data only.** No personal data, and no names of officials, volunteers, contractors or residents.
2. **Nothing below the hromada level.** No output locates shelters, volunteers, military units or critical infrastructure at a finer scale than the hromada.
3. **No operational uplift.** Hromada-level outputs should not tell an attacker anything new, and in particular nothing about when and where the grid failed or recovered in the recent past.
4. **The raw inputs are already public.** VIINA events, Black Marble radiance and budget execution data can all be downloaded by anyone. The rules below therefore limit what this study *adds*: the joining, cleaning, timing and packaging that make patterns easier to read. They are not a claim that the underlying information is secret.

### 12.2 Rules

| Rule | Applies to | What is released | What is withheld |
|---|---|---|---|
| R1. Spatial floor | All outputs | Hromada, raion and oblast aggregates | Night-light rasters, DREAM project points, OSM infrastructure layers, interpolated surfaces as data |
| R2. Time lag | Monthly night-light index, trajectory metrics | Hromada monthly values up to 6 months before release | The most recent 12 months at hromada level; these are shown at oblast level only |
| R3. Frontline and border zone | Hromadas within 30 km of the front line or of the Russian or Belarusian border | Annual indices; time series aggregated to raion | Hromada-level monthly values and trajectory metrics |
| R4. Military finance | Budget tables, capacity index | Civilian income tax; the count of garrison hromadas and sensitivity results | The garrison flag and military income-tax share at hromada level |
| R5. Strike events | VIINA-derived outputs | Hromada counts; point maps at national extent only | Republished event points; point maps at regional or local zoom |
| R6. Personal data | DREAM and any record-level source | Project counts per hromada | Names, contractors, addresses, free-text fields |
| R7. Review | Every release | none | Release proceeds only after the checklist in Annex E is complete and one Ukrainian reader outside the project has reviewed all maps |

The front-line reference for R3 is [[PENDING: source and date of front-line geometry — request 31]].

KDE, IDW and kriging surfaces (Maps 07, 06, 05; Annex D) are published as national-extent images only. The underlying grids are not included in the data package.

### 12.3 Audit

**Table 12. Security audit of published outputs** [[PENDING: complete after request 13]]

| Output | Finest spatial level | Finest time step | Rules checked | Status |
|---|---|---|---|---|
| Maps 01–13 (exposure) | | | R1, R5 | |
| Map 14–15 (bivariate) | Hromada | Period total | R1, R4 | |
| Map 16 (recovery quintiles) | Hromada | Annual | R1 | |
| Map 17 (Carpathian terciles) | Hromada | Annual | R1 | |
| Map 18 (oblast context) | Oblast | Survey round / month | R1 | |
| Map 19 (recent light deficit × capacity) | Hromada | Last 12 months | R2, R3 | Re-window or aggregate (request 33) |
| Map 20 left (outage loss, summer 2024) | Hromada | 2024 window | R2, R3 | |
| Map 20 right (change classes since H2 2023) | Hromada | Last 12 months | R2, R3 | Re-window or aggregate (request 33) |
| Carpathian light chart (oblast medians) | Oblast | Month | R2 | |
| Data package tables | | | R1–R6 | |
| Data package GeoPackages | | | R1, R3, R5 | |

## 13. Reproducibility

### 13.1 Environment

The analysis runs in Python 3.13 in a virtual environment, with package versions pinned in `requirements.txt`. Maps are produced in QGIS 3.40 from the project `viina/qgis/ukraine_strikes.qgz`. [[PENDING: operating system and QGIS plugin versions — request 25]]

### 13.2 Pipeline

`./run_all.sh` rebuilds all tables, indices, models and figures from cached source downloads. A full run takes about {{run_time}}. The repository is organised as:

- `viina/` — strike events, alerts, exposure measures, QGIS project and map pages;
- `resilience/` — budget, night-light, population, survey and displacement processing; indices; tidy tables;
- `publication/` — this paper, the policy brief, the Dispatch essay, the data package documentation and the build script.

### 13.3 Data availability

The data package on Zenodo ({{zenodo_doi}}) contains:
- tidy tables for all indices and model inputs;
- GeoPackages of hromada and oblast boundaries with attributes;
- the data dictionary (Annex A) and source catalogue (Annex B).

It is subject to the rules in section 12.

Not every input can be redistributed:
- **Raw source downloads** are not included. Fetch scripts with recorded access dates retrieve them.
- **IOM DTM data** is retrieved through the IOM API under IOM's terms of use. The package contains the fetch script and, where the terms allow, oblast aggregates only. [[PENDING: confirm DTM redistribution terms — request 23]]
- **Night-light rasters** are withheld under rule R1 and can be downloaded directly from NASA.

### 13.4 Versions

This paper describes release {{release_version}} (commit {{commit_hash}}, {{release_date}}). Later releases will be listed with their changes on the Zenodo record.

### 13.5 Licences

- Text and figures: CC BY 4.0.
- Data package: ODbL 1.0. It contains databases derived from VIINA and OpenStreetMap, which are themselves licensed under ODbL.
- Code: MIT.

Every map and table credits its sources. Full attribution statements are in Annex F.

### 13.6 Suggested citation

Garand, M. ({{release_year}}). *Strikes, fiscal capacity and night-light recovery in Ukraine's hromadas, 2022–2026: A spatial analysis with open data* (Working paper {{release_version}}). SocArXiv. {{socarxiv_doi}}

Data: Garand, M. ({{release_year}}). *Ukraine hromada strikes and resilience dataset* ({{release_version}}) [Data set]. Zenodo. {{zenodo_doi}}

## References

[[CHECK: verify every entry and add methods references used in the pipeline]]

- Getis, A., & Ord, J. K. (1992). The analysis of spatial association by use of distance statistics. *Geographical Analysis*, 24(3), 189–206.
- Román, M. O., et al. (2018). NASA's Black Marble nighttime lights product suite. *Remote Sensing of Environment*, 210, 113–143.
- Schiavina, M., Freire, S., Carioli, A., & MacManus, K. (2023). *GHS-POP R2023A — GHS population grid multitemporal (1975–2030)*. European Commission, Joint Research Centre.
- Zhukov, Y. M. (2023). Near-real time analysis of war and economic activity during Russia's invasion of Ukraine. *Journal of Comparative Economics*, 51(4), 1232–1243.
- OCHA. *Ukraine — Subnational administrative boundaries (COD-AB)*. Humanitarian Data Exchange. {{version_codab}}
- IOM Displacement Tracking Matrix. *Ukraine data, API v3*. Accessed {{access_dtm}}.
- SeeD & UNDP. *SCORE / reSCORE Ukraine 2021 and 2024*. Accessed {{access_rescore}}.
- Ministry of Finance of Ukraine. *openbudget.gov.ua — local budget execution*. Accessed {{access_openbudget}}.
- DREAM — Digital Restoration Ecosystem for Accountable Management. Accessed {{access_dream}}.

## Annexes

| Annex | Content | Source file |
|---|---|---|
| A | Data dictionary | `resilience/tidy/data_dictionary.csv` |
| B | Source catalogue, with versions and access dates | `resilience/tidy/source_catalogue.md` |
| C | Full model output: M1–M7, sensitivity, spatial models, trajectory models | [[PENDING: requests 4, 5, 7, 12]] |
| D | Additional maps 02–13, after security review | `viina/` map pages |
| E | Security audit checklist, completed for this release | [[PENDING: request 13]] |
| F | Attribution statements for every source | `data_package/ATTRIBUTION.md` |
| G | Glossary | below |

### Annex G. Glossary

- **Hromada** — the basic unit of local self-government in Ukraine since the 2015–2020 decentralisation reform. A hromada may be urban, settlement or rural. It is the unit of analysis in this paper.
- **Raion** — the district level between hromada and oblast.
- **Oblast** — the region, the first-level administrative division.
- **KATOTTH** — Ukraine's codifier of administrative-territorial units. The hromada-level (k3) segment identifies each hromada.
- **COD-AB** — OCHA's Common Operational Dataset of administrative boundaries.
- **PIT** — personal income tax. A share is credited to the local budget of the hromada where the employer is registered.
- **Own revenue** — local budget revenue excluding transfers from the state budget.
- **Transfer dependency** — transfers as a share of total local revenue.
- **IDP** — internally displaced person.
- **Registered IDPs** — people recorded in the national IDP register by host oblast.
- **IDPs present** — IDPs estimated by IOM survey to be living in an oblast at the time of the survey round.
- **Night-light recovery ratio** — lit pixels during the war relative to the pre-war baseline, for the same hromada (section 5.2).
- **Oblast fixed effects** — model terms that absorb everything shared by all hromadas in the same oblast. Estimates with fixed effects compare hromadas only with others in the same oblast.
- **Buffering** — the hypothesis that higher local capacity reduces the loss associated with a given level of exposure. It is tested by the capacity × exposure interaction.
- **Night-light index** — monthly radiance of a hromada's lit pixels relative to the same calendar month in 2020–21 (section 8.1). 1 = pre-war level.
- **Outage loss** — a hromada's light in June–July 2024 relative to its own July–December 2023 level (section 8.4).
- **Relative civilian income tax** — civilian PIT in a quarter relative to the same quarter of 2021, divided by the national median.
- **Gi\*** — the Getis-Ord local statistic used to identify spatial clusters of high or low values (hot spots and cold spots).
