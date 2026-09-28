---
title: "Hromada resilience under strikes in Ukraine, 2022–2026"
subtitle: "Economic, rights and cultural life of Ukraine's hromadas — capacity, recovery, the three spheres, trust and reception: an associational analysis with open data"
short-title: "Hromada resilience under strikes, 2022–2026"
author: "Michel Garand, Ubuntu Bioregional Economic Commons"
version: "v0.5 — internal draft (three parts; the three spheres measured at hromada level)"
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

This working paper is about the resilience of Ukraine's hromadas (municipal communities) under Russian strikes, from 2021 to {{nl_panel_end}}. It reads resilience through the three spheres of social threefolding — economic, rights and cultural life (section 1.4) — and asks how they relate to one another and to the pressure of attack. It has three parts.

- **Part I — local capacity, recovery and exposure** works at hromada level. It relates fiscal capacity and night-time light (a proxy for continued activity and services, the functional side of resilience) to strike and air-raid-alert exposure.
- **Part II — the three spheres at hromada level** measures economic, rights and cultural life for each hromada in 2021 and 2025 from open budget, election and school data, maps them, relates them to exposure, to functional resilience and to each other, and asks why the patterns fall where they do.
- **Part III — trust, cohesion and reception** turns to the relational side: trust in local administration, community cohesion, belonging, and the movement of displaced people and taxpayers. These data exist only by oblast, so Part III describes and compares, with a regional reading of the Carpathian oblasts.

All results are associations. The paper estimates no causal effects, and it does not measure resilience directly: it measures proxies and names them as such.

### Part I — local capacity, recovery and exposure

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

### Part II — the three spheres at hromada level

7. **Before the war, economic and rights life were strongest in the centre and east, weakest in the west; cultural life varies more locally.** In 2021 the median Carpathian hromada ranked {{sph_med_econ_2021_carp}} on economic life and {{sph_med_rights_2021_carp}} on rights life (national median 50), but {{sph_med_cult_2021_carp}} on cultural life. Economic and rights life form regional clusters (Moran's I {{lisa_nat_econ_2021_I}} and {{lisa_nat_rights_2021_I}}); cultural life, measured by what hromadas spend on culture and education per resident, does not ({{lisa_nat_cult_2021_I}}).

8. **Strikes fell on stronger places, and the relative fall since 2021 is concentrated in the zone near the front line and the border.**
   - Within oblasts, hromadas later struck more had stronger spheres before the war (economic {{a1_econ_b}}, rights {{a1_rights_b}}, cultural {{a1_cult_b}}; standardised). This describes where strikes fell, not what they did.
   - From 2021 to 2025, more-exposed hromadas fell back in economic ({{a3_econ_b}}) and cultural life ({{a3_cult_b}}) relative to others in their oblast. Both associations disappear without the {{n_zone}} hromadas within 30 km of the front line or the Russian or Belarusian border.
   - On the indicators measured in both years, zone hromadas fell {{q1zone_ll_econ_b}} (economic), {{q1zone_ll_rights_b}} (rights) and {{q1zone_ll_cult_b}} (cultural) standard deviations behind the rest of their oblast: income and property tax, rising dependence on transfers, and every cultural spending line.
   - Hromada profiles became more balanced across the three spheres from 2021 to 2025, except in the zone, where the median distance from the national balance rose from {{q2_imbalance_2021_zone}} to {{q2_imbalance_2025_zone}}. The zone leans to rights life because economic life collapsed while transfers and capital programmes held the rights index up.

9. **Outside the zone, struck hromadas spent more on capital works, social protection and education.** More-exposed hromadas raised their capital-expenditure share ({{q1expnz_capex_share_b}}), social protection spending ({{q1expnz_social_pc_b}}) and education spending per resident ({{q1expnz_education_pc_b}}), with no fall in economic or cultural life.

10. **Fiscal autonomy before the war goes with keeping light when the grid failed.** Within oblasts, hromadas less dependent on transfers in 2021 lost less light in the summer-2024 outages ({{q3_transfer_dep_civ_b}}, 95 % interval {{q3_transfer_dep_civ_ci}}), with the tax base and cultural life held constant. The association holds on reliable light data and without the zone. In threefold terms, the outage result of Part I belongs to the rights sphere: the autonomy of local self-government. No sphere buffers exposure.

11. **Economic and cultural life move together; rights life stands apart.** Economic and cultural life correlate at {{c_econ_cult_2025_rho}} (2025), within every oblast, and their changes since 2021 go together ({{c_econ_cult_change_b}}). Part of this is budget arithmetic: own revenue pays for culture. Rights and cultural life are only weakly related ({{c_rights_cult_2025_rho}}).

12. **The Carpathian economic rise is mostly faster income-tax growth, catch-up and Lviv.** The region's economic index rose by a median {{q5_d_econ_carp}} from 2021 to 2025 (elsewhere outside the zone {{q5_d_econ_restnz}}), but on the tax bases measured in both years only {{q5_d_ll_econ_carp}} (Lviv {{q5_d_ll_econ_lv}}). Given the 2021 level, the Carpathian lead is {{q5lvl_ll_b}} (p = {{q5lvl_ll_p}}), and {{q5lvl_nolviv_b}} without Lviv. Civilian income tax did grow faster in the west ({{q5_pdfo_civ_growth_rel_2125_carp}} times the national median). Whether that follows relocated firms and people cannot be tested with open hromada-level data.

### Part III — trust, cohesion and reception

13. **Relational resilience varies as much within the west as between west and east.** In the reSCORE 2024 survey (n = {{rescore_n}}), trust in local administration is far above the national average ({{trust_national}}) in Ivano-Frankivsk (+{{trust_diff_if}}) and Chernivtsi (+{{trust_diff_cv}}), close to it in Lviv (+{{trust_diff_lv}}), and far below it in Zakarpattia ({{trust_diff_zk}}) and neighbouring Ternopil ({{trust_diff_te}}).
   - Attachment is not satisfaction: Kherson records the lowest satisfaction with the locality ({{locality_sat_ks}}) but the strongest sense of belonging ({{belonging_ks}}).

14. **Relational and fiscal resilience do not line up.** Ivano-Frankivsk and Chernivtsi combine below-median fiscal capacity with trust well above the national average. Zakarpattia, the brightest of the four Carpathian oblasts, reports one of the lowest levels of trust. This sets hromada finances beside oblast survey means; it is a juxtaposition of two levels of measurement, not a measured relationship between them.

15. **Money and people moved west, and are partly moving on.**
   - Civilian income tax in Carpathian hromadas, relative to 2021 and to the national median, peaked at {{pit_carp_peak}} in 2022 Q2–Q3 and has settled at {{pit_carp_recent}}.
   - Within oblasts, higher exposure goes with lower relative income tax ({{pit_exp_recent}}), consistent with taxpayers relocating away from exposed areas.
   - Registered IDPs in the Carpathian oblasts exceed those present by {{idp_west_gap}} (Zakarpattia: {{idp_reg_zk}} registered vs {{idp_present_zk}} present per 1,000 residents). Registrations there have fallen by {{idp_carp_decline}} since February 2023, while rising in Kherson (+{{idp_rise_ks}}), Sumy (+{{idp_rise_su}}) and Kyiv city (+{{idp_rise_kc}}).
   - Real own revenue of hromadas has been roughly flat since 2021.

16. **The Carpathian region is quieter and brighter, but its four oblasts differ.**
    - A typical Carpathian hromada spent about {{carp_alert_hours_12m}} hours under alert in the last 12 months, against about {{nat_alert_hours_12m}} nationally.
    - Its recent light level is {{carp_level_recent}} of pre-war, against {{rest_level_recent}} elsewhere.
    - Fiscal capacity is below the national median in three of the four oblasts; Lviv is above it.
    - In the three spheres, the four oblasts were the weakest in economic life before the war and weak in rights life except Lviv. Their economic rise by 2025 is mostly faster income-tax growth, catch-up from a low start and Lviv (finding 12).

### How the three parts relate

Part I finds that fiscal capacity goes with keeping light when the grid fails, but does not buffer exposure. Part II splits that capacity into its economic and rights parts and adds cultural life. The outage association belongs to the rights sphere (fiscal autonomy), not to the tax base; exposure matters for the spheres mainly in the zone near the front line and the border. Part III finds that trust and cohesion, measured by oblast, follow neither the fiscal map nor the sphere indices. Because the relational data exist only by oblast, they cannot enter the hromada models, and the paper cannot test whether trust or cohesion helps hromadas with weak budgets hold together under pressure. That test needs hromada-level survey and displacement data (section 15.6).

**What this paper does not show.** It does not show that local fiscal capacity or any sphere causes recovery. It says nothing about individuals, only about hromadas and oblasts. It does not describe conditions in occupied territory. It does not describe anything below the hromada level, or current power conditions in any hromada. The sphere indices measure what budgets, elections and the school register record; cultural and civic life outside them is not measured.

## 1. Introduction

### 1.1 Context

Since February 2022, Russian strikes have reached nearly every region of Ukraine. Since autumn 2022 they have repeatedly targeted the electricity system. The war arrived shortly after the 2015–2020 decentralisation reform. That reform consolidated local government into hromadas, which now keep a share of personal income tax and manage their own budgets, and which have carried much of the everyday response to the war: shelters, displaced people, utilities and local services.

That combination raises an obvious question for recovery planning. Do hromadas with stronger local finances cope better with the same level of attack? If they do, strengthening local fiscal capacity would be a recovery priority in its own right. If they do not, the reasons matter: perhaps recovery is governed by systems larger than any hromada, such as the national grid.

Resilience also has more than one side. Budgets and infrastructure describe what a hromada can pay for and keep running. Its economic, political and cultural life describe what it is: a tax base and work, a self-governing community that allocates public funds, and schools and cultural institutions. Trust, cohesion and the reception of displaced people describe the relationships through which communities hold together. This paper looks at all of these, ordered by the three spheres of social threefolding, and at how each relates to exposure and to the others.

### 1.2 Questions

The paper asks eight questions, in three parts.

**Part I — local capacity, recovery and exposure (hromada level)**

1. Is local fiscal capacity related to how exposed a hromada has been to strikes and air-raid alerts?
2. Does recovery, measured with night-time lights, vary with exposure and with capacity?
3. Does capacity moderate the association between exposure and recovery, so that stronger hromadas lose less for the same exposure?

**Part II — the three spheres at hromada level**

4. How do economic, rights and cultural life vary between hromadas, and how did they change from 2021 to 2025?
5. How do the spheres relate to exposure, to functional resilience (night-time light) and to each other?
6. Why are the clearest patterns where they are: which candidate explanations can open data tell apart, and which not?

**Part III — trust, cohesion and reception (oblast level)**

7. How do oblasts differ in trust in local administration, community cohesion and belonging, and do these relational indicators follow the fiscal ones?
8. Where have displaced people and taxpayers moved, and what does that mean for the Carpathian region (Zakarpattia, Ivano-Frankivsk, Lviv and Chernivtsi oblasts) as a region of reception?

### 1.3 Approach and contribution

We assemble a hromada-level dataset for {{n_hromadas_total}} spatial units, of which {{n_hromadas_nonoccupied}} are in non-occupied territory, from open sources:
- strike events (VIINA) and air-raid alerts;
- local budget execution (openbudget.gov.ua);
- monthly night lights (NASA Black Marble);
- gridded population (JRC GHS-POP);
- reconstruction projects (DREAM);
- local budget spending by function, local taxes, the 2020 local elections (Central Election Commission) and the register of schools (Ministry of Education and Science).

From these we build three indices:
- a **fiscal capacity index** from own revenue, transfer dependency, capital spending and civilian income-tax growth;
- a **night-light recovery ratio**, comparing lit-pixel ratios for 2024 and winter 2024–25 against pre-war baselines;
- an **engagement measure**, DREAM reconstruction projects per 10,000 residents, kept separate because it responds to damage;
- three **sphere indices**, for economic, rights and cultural life, in 2021 and 2025 (Part II).

We relate these indices using pooled models, oblast fixed-effects models, a wild-cluster bootstrap by oblast, spatially robust errors and local cluster statistics, and set them against oblast-level survey (reSCORE 2024) and displacement (IOM DTM) data.

The contribution is threefold:
- An open, reproducible hromada-level dataset joining exposure, local finance and night-light data, released with its code, data dictionary and source catalogue.
- A transparent test of the "local capacity buffers exposure" hypothesis, including a clear negative result once oblast-level differences are controlled.
- A first measurement of the three spheres of social threefolding for every non-occupied hromada, with maps of each sphere and of their balance, their associations with exposure and functional resilience, and a structured inquiry into why the patterns fall where they do.
- A relational reading, by oblast, of trust, cohesion and displacement, with the Carpathian oblasts as a regional case, keeping survey, displacement and fiscal evidence at the levels where they are actually measured.

**Terms.** We use "resilience" for the ability of hromadas to keep functioning and to hold together under attack, and distinguish three sides: *institutional* (fiscal capacity), *functional* (night-time light, a proxy for activity and services) and *relational* (trust, cohesion, belonging and the reception of displaced people). None is measured directly; the text names the proxy each time. Section 1.4 places these sides within the three spheres of social threefolding, which Part II measures directly. "Relationship" and "association" mean statistical association, not cause.

### 1.4 Frame: social threefolding

We read resilience through social threefolding (Steiner 1919), which distinguishes three spheres of social life, each with its own principle.

**The three spheres**

| Sphere | Principle | Domain |
|---|---|---|
| Rights (political) life | Equality and democracy | Law, public administration, representation, the allocation of public funds |
| Cultural life | Freedom | Art, science, religion, education, the media |
| Economic life | Uncoerced cooperation in freely contractual relations | Production, trade, work, the tax base |

Read this way, a hromada is resilient when each sphere keeps its own principle working under attack — equal access and democratic self-government, free cultural and educational life, cooperative economic life — and when no sphere takes over the tasks of another. The theory is normative. Here it orders the measures and the reading of the results; it is not tested.

The measures used in this paper fall into the spheres as follows.

**Measures by sphere**

| Measure | Level | Sphere |
|---|---|---|
| Civilian income tax, single tax, property and land payments per resident; civilian income-tax growth | Hromada | Economic: the tax base (economic sphere index, Part II) |
| Transfer dependency; capital-expenditure share; social protection spending per resident | Hromada | Rights: autonomy and spending choices of local self-government (rights sphere index) |
| Deputy candidates per council seat, 2020 local elections | Hromada | Rights: democratic contestation (rights index 2021) |
| DREAM reconstruction projects | Hromada | Rights: public investment planning (rights index 2025; engagement in Part I) |
| Culture and arts, education and extracurricular spending per resident; schools per 10,000 residents | Hromada | Cultural (cultural sphere index) |
| Fiscal capacity index (Part I) | Hromada | Economic and rights components combined |
| Night-time light | Hromada | Functional outcome; economic activity and infrastructure shared across the grid; in no sphere index |
| Trust in local administration, civic engagement, locality satisfaction (reSCORE) | Oblast | Rights |
| Belonging, mental wellbeing (reSCORE) | Oblast | Cultural |
| Economic security (reSCORE) | Oblast | Economic |
| Community cohesion (reSCORE); displacement (IOM DTM) | Oblast | Across spheres |

Version 0.4 of this paper read the existing measures through the frame and noted two gaps: the fiscal capacity index mixed economic and rights components, and the cultural sphere had no hromada-level measure. Part II closes both, within the limits of open data. It splits the budget between the spheres and measures cultural life by what hromadas spend on culture and education and by the school network (`resilience/docs/threefolding_framework.md`). Cultural life outside the budget — associations, religious communities, the media — remains unmeasured, partly by design (rule R7, section 17).

### 1.5 Structure

- Sections 2 and 3 define the spatial units, coverage and data sources shared by all parts.
- **Part I** (sections 4–8): exposure (4), the capacity, recovery and engagement indices (5), how capacity and exposure relate (6), recovery models (7) and monthly trajectories (8).
- **Part II** (sections 9–13): measuring the three spheres and their balance (9), the spheres and exposure (10), the spheres and functional resilience (11), how the spheres relate (12), and "why there?" (13).
- **Part III** (sections 14–15): trust, cohesion and displacement by oblast (14), and the Carpathian region, where all three parts are read together (15).
- **Synthesis:** resilience in the three spheres.
- **Methods, limits and sources** (sections 16–18): limitations, the rules applied to protect sensitive information, and reproducibility, followed by references and annexes.

### 1.6 Author's position

The author lives in the Carpathian region of Ukraine and writes field dispatches from it (*Soil and Peace — Carpathian Dispatch 2026*). That proximity shaped the regional focus of section 15. All results are nevertheless computed nationally, with the same methods for every oblast.

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
| Sphere indices (economic, rights, cultural; 2021 and 2025) | Hromada | {{n_spheres}} | Fewer than three indicators (budget not served) |
| reSCORE 2024 indicators | Oblast | {{n_rescore_oblasts}} (22 oblasts and Kyiv city) | Donetsk, Luhansk and Crimea not surveyed |
| IOM DTM displacement | Oblast | {{n_dtm_oblasts}} | Only oblast level served for Ukraine |

The largest drop, from {{n_hromadas_nonoccupied}} to {{n_recovery}} hromadas for the recovery ratio, matters for interpretation: the excluded hromadas are not a random subset (section 16.5).

## 3. Data sources

All inputs are open, aggregated data. None contains personal data. Table 2 lists each source with its level, period and licence. The full source catalogue, with access dates and versions, is in Annex B.

**Table 2. Data sources**

| Source | Content used | Native level | Period | Licence / terms |
|---|---|---|---|---|
| VIINA 2.0 | Geocoded strike events | Point / settlement | {{period_viina}} | ODbL 1.0 |
| Air-raid alert records (Klimenko) | Alert start and end times | Oblast / raion / hromada | {{period_alerts}} | MIT |
| OCHA COD-AB (from SSPE Kartographia) | Administrative boundaries | ADM3 polygons | {{version_codab}} | CC BY 3.0 IGO |
| openbudget.gov.ua | Local budget execution: revenue by code (incl. single tax, property and land payments); expenditure by economic classification and by programme with functional codes | Hromada budget | 2021 Q1 – 2026 Q2, quarterly | Open data, CMU resolution 835 |
| NASA Black Marble VNP46A3 | Monthly night-time radiance | ~500 m raster | Jan 2020 – Aug 2026, monthly | Public domain |
| JRC GHS-POP R2023A | Population, 2020 epoch | 100 m raster | 2020 | EC reuse policy (attribution) |
| DREAM | Reconstruction projects | Project, geocoded to hromada | {{period_dream}} | [[PENDING: terms — request 23]] |
| Central Election Commission | Local elections of 25 Oct 2020: deputy candidates and seats per council (counts only) | Council (hromada) | 2020 | Open data, reuse with attribution; data.gov.ua copy CC BY |
| Ministry of Education and Science, ЄДЕБО register | General secondary schools in operation, placed in hromadas through the KATOTTG codifier (counts only) | School → hromada | 2026 | [[CHECK: licence statement of the register]] |
| Ministry of Education and Science, form ЗНЗ-1 | Pupils and classes per school, pre-war (context only) | School → hromada | 2021 | CC BY 4.0 (data.gov.ua) |
| reSCORE Ukraine 2021, 2024 (SeeD–UNDP) | Trust, cohesion, locality satisfaction, belonging | Oblast | 2021, 2024 | [[PENDING: terms — request 23]] |
| IOM DTM (API v3) | Registered IDPs by host and origin oblast; IDPs present (survey) | Oblast | Feb 2022 – Aug 2026; Aug 2024 – Mar 2026 | IOM terms of use |
| OpenStreetMap | Basemap tiles only (maps) | Raster tiles | {{version_osm}} | ODbL 1.0 |
| Regional statistics offices | ЄДРПОУ enterprise tables: legal entities and sole proprietors by hromada; regional supplement for the Carpathian profile only (partial coverage), not used in the indices or models | [[PENDING]] | [[PENDING]] | Open data |

Three properties of the sources shape the analysis:

- **Level.** Exposure, finance, night lights, population and projects are available at hromada level. Survey and displacement data are available only at oblast level, so they appear only in the oblast context (section 14) and never as hromada-level predictors.
- **Timing.** Budget and night-light series start before February 2022, which allows pre-war baselines. Survey data has a 2021 wave but only oblast estimates. Displacement data starts with the invasion.
- **Reporting.** Strike events come from open-source reporting and are affected by reporting density (section 16.4). Alerts, budgets and night lights are recorded administratively or by instrument.

Attribution for every source is given in `ATTRIBUTION.md` of the data package and in the caption of every map.

# Part I — Local capacity, recovery and exposure

Part I works at the level of the hromada. It asks whether local fiscal capacity, the institutional side of resilience, is related to exposure, and whether it goes with keeping or recovering night-time light, the functional side. All models are associational. Part II splits the capacity index into its economic and rights parts and tests the spheres against the same light outcomes.

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

Exposure has a clear east–west gradient, with concentrations along the front line, in the border oblasts and around major cities (Maps 01 and 04). Kernel density estimation (Map 10) and hot-spot analysis (Getis-Ord Gi*, Map 11) identify the same clusters. IDW and kriging surfaces (Annex D) are shown for comparison only. They interpolate between reported locations and should not be read as estimates for places without recorded events.

**Figures:** Map 01 — risk index by hromada. Map 04 — cumulative alert hours. Map 10 — strike density (KDE). Map 11 — Gi* hot and cold spots.

::: {.withheld}
Maps 01, 10 and 11 are withheld from publication under rules R1, R3 and R5 (section 17) and are not reproduced here; Map 04 follows.
:::

::: {.plate}
![Map 04 — alert hours per hromada, last 12 months](viina/qgis/maps/preview/04_alert_hours.png)
:::


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

- **Pre-war version.** Because civilian income-tax growth partly reflects recovery itself, we also compute capacity from 2021 data only. That version is the primary predictor in section 7 (see section 16.11).
- **Garrison hromadas.** {{n_garrison}} hromadas had military payroll above a quarter of their 2021 income tax. Their revenue reflects where units were paid rather than local economic activity. They stay in the index and are excluded only in a sensitivity check. The flag is not published at hromada level (section 17).

### 5.2 Night-light recovery ratio

The recovery ratio compares night-time light before and during the war, over the pixels of each hromada that were lit in 2021. A pixel counts as lit if its mean 2021 radiance is at least 1.0 nW/cm²/sr (VNP46A3 monthly composites, snow-free, with the snow-covered composite where no snow-free value exists). For each hromada we compute two ratios:

- **Annual:** light in 2024 relative to 2021.
- **Winter:** light in winter 2024–25 relative to winter 2020–21 (December to February).

The two ratios are closely correlated (ρ = {{rho_recovery_windows}}) and are combined as the mean of their percentile ranks; a hromada with only one valid ratio takes that ratio's rank. Hromadas with fewer than {{min_lit_pixels}} lit pixels are excluded, because ratios on very small counts are unstable. This rule accounts for most of the drop to {{n_recovery}} hromadas.

**Baseline.** 2021 was about {{nl_2021_vs_2020}} brighter than 2020 at the median, probably from LED retrofits and possibly from COVID-dimmed activity in 2020. The annual ratio uses a 2021-only baseline and therefore understates recovery by roughly {{nl_baseline_shift}}; the ranking of hromadas is unaffected. The monthly index in section 8 uses the more conservative mean of 2020 and 2021.

Using lit pixels rather than all pixels reduces the influence of newly lit or very bright isolated sources, such as industrial sites. It does not remove the effects of blackouts or reduced street lighting (section 16.1).

### 5.3 Engagement

Engagement is the number of valid DREAM reconstruction projects per 10,000 residents ([[PENDING: definition of "valid" — request 23]]). It is kept separate from capacity and recovery because projects are registered in response to damage. Combining it with the other indices would mix a response to exposure with the outcomes we want to compare against exposure.

**Figures and tables:** Map 16 — recovery ratio quintiles. Table 4 — capacity index loadings and robustness.

::: {.plate}
![Map 16 — night-light recovery ratio, quintiles](viina/qgis/maps/preview/16_resilience_recovery.png)
:::


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

The small positive correlation is consistent with larger urban hromadas being both better resourced and more often targeted and reported (section 16.4). It is too weak to matter for the models that follow: capacity is not a stand-in for exposure, and both can enter the same model without collinearity problems. Pre-war capacity is different. It correlates with alert hours at ρ = {{rho_cap_alerts_2021}} and with strikes at ρ = {{rho_cap_strikes_2021}}. The alert association is regional: within oblasts it falls to ρ = {{rho_cap_alerts_2021_within}}. Hromadas in the east and centre had stronger own finances before 2022 and now spend the most hours under alert; the gap to the west has narrowed since (section 15.1). Within oblasts, pre-war capacity and strikes keep a small positive association (ρ = {{rho_cap_strikes_2021_within}}), the same urban pattern as above. Models with pre-war capacity therefore rely on oblast fixed effects to separate capacity from regional exposure.

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

::: {.plate}
![Map 14 — alert hours × fiscal capacity](viina/qgis/maps/preview/14_resilience_alerts_capacity.png)
:::


::: {.plate}
![Map 15 — strikes × fiscal capacity](viina/qgis/maps/preview/15_resilience_strikes_capacity.png)
:::


## 7. Recovery models

### 7.1 Specification

The outcome is the night-light recovery ratio (section 5.2) for the {{n_model}} hromadas with both a recovery and a capacity score. The core model is

$$
R_i = \beta_1 C_i + \beta_2 E_i + \beta_3 (C_i \times E_i) + \alpha_{o(i)} + \varepsilon_i
$$

where $R_i$ is recovery, $C_i$ fiscal capacity, $E_i$ exposure and $\alpha_{o(i)}$ an oblast fixed effect. Variables are standardised. Standard errors are heteroskedasticity-robust (HC1); they do not account for residual spatial dependence (section 16.10). [[PENDING: wild-cluster bootstrap and spatially robust errors — requests 4, 5]]

- $\beta_3$ tests **buffering**. A positive value would mean that, for the same exposure, higher-capacity hromadas lose less.
- $\beta_1$ is the **main effect of capacity**: the difference in recovery between hromadas of different capacity at average exposure.
- The oblast fixed effects absorb everything shared by all hromadas in an oblast: grid conditions and outage schedules, distance to the front, regional economy and oblast-level administration.

<!-- begin table: figures/table07_models.md (resilience/27_sensitivity.py) -->
**Table 7. Recovery models M1–M7**

| Model | Oblast FE | Controls | Capacity | Exposure | Sample / method | n | R² | Within-R² | β₁ capacity (t) | p β₁ | β₃ interaction (t) | p β₃ | β₃ 95 % interval |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| M1 | No | No | 2025 | Strikes | All | 1,020 | 0.11 | — | +0.08 (2.5) | 0.271 | +0.15 (6.3) | < 0.001 | +0.09 to +0.22 |
| M2 | Yes | No | 2025 | Strikes | All | 1,020 | 0.57 | 0.05 | +0.16 (6.5) | < 0.001 | −0.01 (−0.5) | 0.639 | −0.04 to +0.03 |
| M3 | Yes | Yes | 2025 | Strikes | All | 1,020 | 0.57 | 0.05 | +0.18 (6.1) | < 0.001 | −0.01 (−0.7) | 0.529 | −0.05 to +0.03 |
| M4 | Yes | Yes | 2025 | Alert hours | All | 1,020 | 0.58 | 0.09 | +0.16 (5.4) | < 0.001 | −0.03 (−1.6) | 0.294 | −0.09 to +0.02 |
| M5 | Yes | Yes | 2021 (pre-war) | Strikes | All | 1,020 | 0.55 | 0.02 | +0.08 (2.3) | 0.058 | −0.01 (−0.2) | 0.824 | −0.06 to +0.04 |
| M6 | Yes | Yes | 2025 | Strikes | Without Donetsk, Zaporizhzhia, Kherson | 980 | 0.53 | 0.05 | +0.19 (6.1) | < 0.001 | 0.00 (−0.2) | 0.890 | −0.05 to +0.06 |
| M7 | Yes | Yes | 2025 | Strikes | All; spatial lag (S2SLS, KNN 6) | 1,020 | — | — | +0.14 (5.3) | — | −0.02 (−1.2) | — | −0.06 to +0.01 |

Outcome: night-light recovery index; all variables standardised. Controls: log population 2020, log lit pixels, log 2021 radiance. t-values with HC1 standard errors; p-values from a restricted wild-cluster bootstrap by oblast (24 clusters, Webb weights, 9,999 draws). β₃ intervals invert that test (M1–M6); for M7 (spatial lag, ρ = 0.845) they use the S2SLS standard error. R² is not defined for M7. Within-R²: share of the variation around oblast means explained.
<!-- end table: figures/table07_models.md -->

### 7.2 Pooled model: apparent buffering

Without fixed effects (M1), the interaction is positive and precisely estimated: β₃ = +{{int_baseline_coef}}, t = {{int_baseline_t}}. Taken alone, this would suggest that local capacity softens the loss of night-time light in heavily exposed hromadas. The model explains little of the variation in recovery (R² = {{r2_no_fe}}).

### 7.3 With oblast fixed effects: no buffering

Adding oblast fixed effects changes the picture in two ways.

- **The model fit changes sharply.** R² rises from {{r2_no_fe}} to {{r2_fe}}. Most of the variation in night-light recovery is between oblasts, not within them. Within oblasts, capacity, exposure and the controls explain little: the within-R² is {{r2_within_range}} (Table 7).
- **The interaction disappears.** In every fixed-effects specification (M2–M7), β₃ is approximately zero ({{int_fe_range}}). A wild-cluster bootstrap by oblast gives p = {{int_fe_p_range}} (M2–M6). The pooled M1 interaction stays significant under the same method (p < 0.001), so the contrast does not come from the standard errors.

The buffering found in M1 is therefore a between-oblast pattern. Oblasts where hromadas have higher capacity on average also happen to recover better at a given exposure, most plausibly because of differences in grid conditions and distance from the front. Among hromadas within the same oblast, higher capacity does not go with a smaller loss at higher exposure.

We report this as the central result of the paper: **within oblasts, we find no evidence that local fiscal capacity buffers the association between exposure and night-light recovery.**

### 7.4 Main effect of capacity

Within oblasts, capacity is positively associated with recovery at average exposure. The coefficient is +{{cap_main_fe_min}} to +{{cap_main_fe_max}} (t {{cap_main_fe_t}}) across models using the 2025 index.

This estimate is inflated by construction. The 2025 index includes civilian income-tax growth from 2021 to 2025, which partly reflects the same recovery the outcome measures (section 16.11). Using pre-war (2021) capacity instead, the coefficient falls to +{{cap_main_fe_2021}} (t {{cap_main_fe_2021_t}}, HC1; Conley t {{cap_main_fe_2021_conley}}). Removing income-tax growth from the 2025 index, and keeping its other three components, gives +{{cap_main_fe_no_pitgrowth}} (t {{cap_main_fe_no_pitgrowth_t}}). The income-tax component thus accounts for about a sixth of the 2025 estimate. Most of the gap to the pre-war estimate lies elsewhere: own revenue, transfers and capital spending in 2025 also move with the wartime economy.

We treat the pre-war estimate as the primary result. It is modest: with only 24 oblasts as clusters, the wild-cluster bootstrap gives p = {{cap_main_fe_2021_p}}, significant at the 10 % level but not at 5 %. The outage-loss result in section 8.5 is the stronger evidence. It says that hromadas with stronger finances before the invasion show modestly better night-light recovery than others in the same oblast. It does not say why. Pre-war capacity is correlated with size, urbanisation and economic structure, any of which could drive the association. A clearer version of this association appears in the summer-2024 outage loss (section 8.5).

### 7.5 Spatial dependence

Recovery is strongly spatially dependent. A spatial lag model on the M3 specification, with oblast fixed effects and six nearest neighbours (M7, S2SLS), gives ρ = {{spatial_lag_rho}}. Even with oblast fixed effects, residuals remain clustered (Moran's I = {{resid_moran_fe}}). There is therefore spatial structure below the oblast level, plausibly grid districts and outage groups, that the models do not capture.

This has two consequences:
- Standard errors that ignore spatial dependence overstate precision.
- The capacity main effect could partly reflect neighbourhood patterns rather than anything specific to each hromada.

We therefore re-estimate the M3 and M5 specifications, with oblast fixed effects and controls, as spatial models. In a spatial error model (GMM, robust to heteroskedasticity), λ = {{sem_lambda}}, and the filtered residuals show no remaining dependence (Moran's I = {{sem_moran}}). The capacity estimates barely move: +{{sem_cap_2025}} for 2025 capacity (z {{sem_cap_2025_z}}) and +{{sem_cap_2021}} for pre-war capacity (z {{sem_cap_2021_z}}), against +0.18 and +0.08 without the spatial term. The interaction stays at zero (z {{sem_int_z_range}}). The spatial lag model gives similar capacity coefficients, but its ρ approaches one with pre-war capacity ({{spatial_lag_rho_prewar}}) and its residuals are negatively autocorrelated (Moran's I {{lag_resid_moran}}), a sign that the lag term over-corrects. We therefore rely on the error model. Spatially correlated errors do not account for the capacity association.

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

**Figures and tables:** Table 7 — specifications. Table 8 — sensitivity. Figure 1 — β₃ with 95 % intervals across M1–M7. Map 16 — recovery quintiles (section 5.2).

![Figure 1 — Interaction coefficient β₃ (exposure × capacity) with 95 % intervals across models M1–M7.](publication/figures/fig01_interaction.png){width=100%}

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

Carpathian hromadas were brighter throughout, and lost a smaller share of their light in the 2024 outages. They were not spared: in July 2024 they too fell to well below their usual level. Section 15 describes differences between the four oblasts.

![Carpathian oblasts: monthly night-light index, oblast medians (Figure 1 of the Carpathian brief).](resilience/docs/fig1_carpathian_light.png){width=100%}

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

1. **Outage loss is the clearest capacity result.** Within oblasts, hromadas with more fiscal capacity kept relatively more of their own light when the grid failed in summer 2024. The association holds with pre-war capacity, under precision weighting and with low residual spatial dependence, and survives inference clustered by oblast (wild-cluster p = {{outage_cap_prewar_p}}) and spatial-HAC errors (Conley t 3.5–3.7). It is still an association between places. The mechanism may be backup generation, better-maintained local networks or a local economy with more users on priority supply; the data cannot distinguish these.
2. **In the acute phase, capacity did not protect.** The worst quarter, which for most hromadas fell in 2022, is an oblast-wide pattern. Within oblasts, 2025 capacity has a weak association (+{{worstq_cap_fe}}) and pre-war capacity none ({{worstq_cap_prewar}}).
3. **Level results are partly reverse-causal.** The recent light level is associated with 2025 capacity at +{{level_cap_fe}} but with pre-war capacity at only +{{level_cap_prewar}}. Local economic activity plausibly raises both light and income-tax revenue, so the 2025 association overstates any effect of capacity on light.
4. **No buffering.** The capacity × exposure interaction is about zero for level, worst quarter and outage loss, as for the annual ratio in section 7. For the 2024–26 slope it is slightly negative with HC1 errors, but not once errors are clustered by oblast (wild-cluster p = {{slope_int_p_wcb}}), and not with pre-war capacity. The slope model also explains little (R² {{slope_r2}}). We do not read it as a finding.

Residual spatial dependence remains for level and worst quarter (Moran's I {{level_trough_moran}}), so HC1 t-values for these outcomes are optimistic. With Conley spatial-HAC errors (50 and 100 km) and a wild-cluster bootstrap by oblast, the capacity estimates for level and outage loss and the 2025 estimate for the worst quarter remain clearly different from zero (p ≤ 0.004).

**Figures:** Map 19 — recent light deficit × fiscal capacity (bivariate 3×3, national terciles). Map 20 — outage loss in quintiles (left) and change classes since H2 2023 (right). Both are subject to the rule in section 8.7.

::: {.plate}
![Map 19 — recent light deficit × fiscal capacity](viina/qgis/maps/preview/19_trajectory_level_capacity.png)
:::


::: {.plate}
![Map 20 — summer-2024 outage loss and change since H2 2023](viina/qgis/maps/preview/20_trajectory_outage.png)
:::


### 8.6 Budget trajectories

The quarterly budget panel runs from 2021 Q1 to {{budget_panel_end}} ({{budget_panel_quarters}} quarters, {{n_capacity}} hromadas). Its four quarters of 2025 reproduce the annual values used in the capacity index.

- **Military income tax.** From 2022 Q2 to 2023 Q3, military personal income tax formed {{military_pit_share_range}} of local income-tax revenue. From 2023 Q4 it was redirected to the state budget. Civilian income tax stays comparable across that break because military payroll lines are identified by name. The capacity index uses civilian income tax only.
- **Real own revenue is roughly flat.** Nominal own revenue in 2025 was {{own_rev_2025_ratio}} times its 2021 level, about the same as cumulative inflation over the period. [[PENDING: basis of the 2026 H1 figure and CPI series — requests 11, 34]]
- **Relative civilian income tax.** We measure civilian income tax in each quarter relative to the same quarter of 2021, divided by the national median, which makes the measure inflation-neutral.
  - In the Carpathian oblasts it peaked at {{pit_carp_peak}} in 2022 Q2–Q3, consistent with firms and workers relocating westward, and has settled at {{pit_carp_recent}} since late 2023.
  - Within oblasts, higher exposure goes with lower relative income tax, both recently ({{pit_exp_recent}}) and in 2022 ({{pit_exp_2022}}). This fits taxpayers moving away from exposed areas.
  - The negative coefficient of pre-war capacity in these models is partly mechanical: the measure is a ratio to each hromada's own 2021 value, so regression to the mean pulls high 2021 values down. It should not be read as "stronger hromadas declined".

### 8.7 Publication rule for time series

Light levels in the last 12 months describe current power conditions. Under the rules in section 17:
- Hromada-level monthly values are released only for months at least 6 months before release.
- The most recent 12 months are shown at oblast level only.
- Hromadas within 30 km of the front line or border are aggregated to raion level.

Map 19 and the right panel of Map 20 use "recent" windows. For publication, their windows end at least 6 months before release, or they are shown at raion level. [[PENDING: re-windowed or aggregated versions — request 33]] Historical windows (2022–2024), including the outage-loss panel of Map 20, carry lower risk and are published at hromada level.

# Part II — The three spheres at hromada level

Part II measures the three spheres of social threefolding (section 1.4) for each non-occupied hromada, before the war (2021) and during it (2025). It asks where each sphere is strong, how the spheres relate to exposure, to the functional resilience measured in Part I and to each other, and why the patterns fall where they do. Everything here is associational. Night-time light is not part of any sphere index: it is the outcome against which the spheres are tested, and using it as an input would make the test circular.

## 9. Measuring the three spheres

### 9.1 Indicators

Each sphere is measured with at least three hromada-level indicators in each year; otherwise the index is not computed (Table S1).

**Table S1. Sphere indicators**

| Sphere | Indicator | Direction | 2021 | 2025 | Source |
|---|---|---|---|---|---|
| Economic | Civilian income tax per resident | + | ✓ | ✓ | openbudget.gov.ua |
| Economic | Single tax per resident (sole proprietors, small farms) | + | ✓ | ✓ | openbudget.gov.ua |
| Economic | Property and land payments per resident | + | ✓ | ✓ | openbudget.gov.ua |
| Economic | Civilian income-tax growth 2021–2025, relative to the national median | + | — | ✓ | openbudget.gov.ua |
| Rights | Transfer dependency (transfers as share of revenue) | − | ✓ | ✓ | openbudget.gov.ua |
| Rights | Capital-expenditure share | + | ✓ | ✓ (2023–25) | openbudget.gov.ua |
| Rights | Social protection spending per resident | + | ✓ | ✓ | openbudget.gov.ua (functional code 10) |
| Rights | Deputy candidates per council seat, local elections 2020, relative to the median of the same electoral system | + | ✓ | — | Central Election Commission |
| Rights | DREAM reconstruction projects per 10,000 residents | + | — | ✓ | DREAM |
| Cultural | Culture and arts spending per resident | + | ✓ | ✓ | openbudget.gov.ua (0820–0829) |
| Cultural | Education spending per resident | + | ✓ | ✓ | openbudget.gov.ua (09) |
| Cultural | Extracurricular education spending per resident (art and music schools, clubs) | + | ✓ | ✓ | openbudget.gov.ua (0960–0969) |
| Cultural | General secondary schools in operation per 10,000 residents | + | — | ✓ | Ministry of Education and Science, ЄДЕБО register |

Per-resident values use the 2020 population (GHS-POP). Spending is actual civilian spending by functional code; military finance is excluded throughout (rule R4).

Four design choices shape the indices:

- **Budget lines are split between spheres.** The tax base (income tax, single tax, property and land payments) is economic life. How far a hromada governs its own budget (transfer dependency), invests (capital share) and provides for its residents (social protection) is rights life, together with electoral contestation. What it spends on culture, education and extracurricular education is cultural life, measured here by its budget.
- **Per resident, not shares.** Shares of one budget sum to one: a high education share lowers every other share. As shares, the cultural and rights spheres were built to oppose each other. Per-resident amounts avoid that, but they rise with the size of the budget, so the economic sphere partly supplies the means of the cultural one. Section 12 examines this.
- **Property and land payments, not total own revenue.** Income tax is the largest part of own revenue, so total own revenue would count it twice.
- **Electoral contestation, not turnout.** The Central Election Commission publishes no structured turnout for the 2020 local elections, and the protocols cannot be linked to the open-data council codes. Candidates per seat depend on the electoral system (party lists in hromadas above 10,000 voters, multi-member districts below), so each council is compared with the median of its own system. Only counts are kept; no candidate is named (rule R6).

The oblast-level survey indicators of Part III (trust, cohesion, belonging) are read beside the sphere indices, never inside them. Schools, libraries, places of worship and media offices are never mapped as points, and no hromada-level table of religious affiliation, ethnicity or language is produced (rule R7, section 17).

### 9.2 Construction and robustness

Each indicator is transformed where it is a per-resident amount (logarithm), oriented so that higher means more, winsorised at the 2nd and 98th percentiles and turned into a percentile rank among non-occupied hromadas. A sphere index is the mean of its ranks, as for the capacity index (section 5.1). All six indices (three spheres, two years) are available for {{n_spheres}} hromadas.

- **Within spheres,** the three tax bases agree well, while income-tax growth stands apart; the rights and cultural indicators agree loosely. Rank correlations between indicators range from {{sph_within_econ_min}} to {{sph_within_econ_max}} (economic; the lowest involve income-tax growth), {{sph_within_rights_min}} to {{sph_within_rights_max}} (rights) and {{sph_within_cult_min}} to {{sph_within_cult_max}} (cultural). In the cultural sphere, dense village school networks and town art schools pull in different directions. The rights and cultural indices are therefore composites of distinct things, not measures of one latent trait.
- **Leave-one-out.** Dropping any one indicator leaves each index nearly unchanged (rank correlation at least {{sph_loo_econ}}, {{sph_loo_rights}} and {{sph_loo_cult}}).
- **Stability.** Rank correlations between 2021 and 2025 are {{sph_stab_econ}} (economic), {{sph_stab_rights}} (rights) and {{sph_stab_cult}} (cultural).
- **Budget sub-indices.** The economic and rights parts of the fiscal capacity index of Part I correlate at {{sph_rho_budget_sub}} (2025); they are related but not the same.

**Change and like-for-like.** The 2025 indices contain indicators the 2021 indices lack: civilian income-tax growth (economic), DREAM projects instead of candidates per seat (rights) and schools (cultural). A change of index from 2021 to 2025 is therefore partly a change of measure. We also report a like-for-like index, the mean rank of the indicators measured in both years. Its change correlates with the change of the full index at {{ll_corr_econ}} (economic), {{ll_corr_rights}} (rights) and {{ll_corr_cult}} (cultural). Where the two diverge, as in the Carpathian oblasts (section 13), the text says which one it uses. All changes are changes of relative position among hromadas, not of absolute levels.

### 9.3 Where each sphere is strong

<!-- begin table: figures/tableS2_spheres_oblast.md (resilience/38_sphere_tables.py) -->
**Table S2. Sphere indices by oblast, medians (0–100)**

| Oblast | Hromadas | Economic 2021 | Rights 2021 | Cultural 2021 | Economic 2025 | Rights 2025 | Cultural 2025 |
|---|---|---|---|---|---|---|---|
| Cherkasy | 66 | 69 | 54 | 47 | 61 | 53 | 51 |
| Chernihiv | 57 | 58 | 61 | 54 | 55 | 66 | 55 |
| Chernivtsi | 52 | 13 | 27 | 38 | 29 | 26 | 42 |
| Dnipropetrovsk | 82 | 63 | 52 | 57 | 63 | 62 | 53 |
| Donetsk | 11 | 56 | 65 | 54 | 16 | 48 | 20 |
| Ivano-Frankivsk | 62 | 16 | 32 | 43 | 31 | 28 | 45 |
| Kharkiv | 51 | 57 | 62 | 51 | 40 | 65 | 38 |
| Kherson | 16 | 61 | 44 | 50 | 15 | 61 | 42 |
| Khmelnytskyi | 60 | 45 | 46 | 50 | 48 | 42 | 47 |
| Kirovohrad | 49 | 73 | 57 | 63 | 71 | 60 | 66 |
| Kyiv | 69 | 73 | 72 | 60 | 72 | 76 | 59 |
| Kyiv City | 1 | 95 | 98 | 81 | 80 | 79 | 63 |
| Lviv | 73 | 40 | 52 | 49 | 53 | 50 | 53 |
| Mykolaiv | 52 | 59 | 44 | 48 | 58 | 60 | 51 |
| Odesa | 91 | 55 | 49 | 50 | 59 | 45 | 49 |
| Poltava | 60 | 74 | 71 | 60 | 61 | 61 | 56 |
| Rivne | 64 | 32 | 33 | 48 | 37 | 28 | 53 |
| Sumy | 51 | 62 | 57 | 56 | 46 | 57 | 39 |
| Ternopil | 55 | 28 | 41 | 42 | 38 | 37 | 42 |
| Vinnytsia | 63 | 45 | 47 | 43 | 51 | 43 | 44 |
| Volyn | 54 | 34 | 35 | 55 | 49 | 36 | 58 |
| Zakarpattia | 64 | 15 | 33 | 41 | 32 | 33 | 43 |
| Zaporizhzhia | 19 | 54 | 51 | 51 | 35 | 53 | 42 |
| Zhytomyr | 66 | 46 | 52 | 46 | 46 | 48 | 47 |
| Carpathian (4 oblasts) | 251 | 20 | 38 | 43 | 37 | 35 | 46 |
| Ukraine (non-occupied) | 1,288 | 50 | 50 | 50 | 50 | 50 | 49 |

Mean percentile rank of the sphere's indicators among non-occupied hromadas (0–100; national median about 50). Zone hromadas are included in the oblast medians. Indicators: Table S1.
<!-- end table: figures/tableS2_spheres_oblast.md -->

- **Economic life** was strongest before the war in the centre and east: the median hromada ranked {{sph_med_econ_2021_32}} in Kyiv oblast, {{sph_med_econ_2021_53}} in Poltava and {{sph_med_econ_2021_35}} in Kirovohrad. The west was weakest: {{sph_med_econ_2021_21}} in Zakarpattia, {{sph_med_econ_2021_26}} in Ivano-Frankivsk and {{sph_med_econ_2021_73}} in Chernivtsi, with Lviv at {{sph_med_econ_2021_46}}. By 2025 the zone oblasts had fallen (Donetsk {{sph_med_econ_2021_14}} → {{sph_med_econ_2025_14}}, Kherson {{sph_med_econ_2021_65}} → {{sph_med_econ_2025_65}}, Kharkiv {{sph_med_econ_2021_63}} → {{sph_med_econ_2025_63}}) and the west had risen, largely through the growth indicator (section 13).
- **Rights life** is low in the west in both years (Chernivtsi {{sph_med_rights_2021_73}}, Ivano-Frankivsk {{sph_med_rights_2021_26}}, Zakarpattia {{sph_med_rights_2021_21}}, Rivne {{sph_med_rights_2021_56}}) and highest around Kyiv ({{sph_med_rights_2021_32}}) and in Poltava ({{sph_med_rights_2021_53}}). In 2025 it stays high in Kharkiv ({{sph_med_rights_2025_63}}) and Kherson ({{sph_med_rights_2025_65}}), where capital programmes and reconstruction projects hold it up (section 10.3).
- **Cultural life** varies less between oblasts. It is highest in a band through the centre (Kirovohrad {{sph_med_cult_2021_35}}) and lowest in the far west in 2021. By 2025 it had fallen in the oblasts along the front and the Russian border (Donetsk {{sph_med_cult_2021_14}} → {{sph_med_cult_2025_14}}, Sumy {{sph_med_cult_2021_59}} → {{sph_med_cult_2025_59}}, Kharkiv {{sph_med_cult_2021_63}} → {{sph_med_cult_2025_63}}) and risen slightly in the north-west (Rivne {{sph_med_cult_2021_56}} → {{sph_med_cult_2025_56}}).

The economic and rights spheres are regional; the cultural sphere is local. Global Moran's I is {{lisa_nat_econ_2021_I}} for economic life and {{lisa_nat_rights_2021_I}} for rights life in 2021, but {{lisa_nat_cult_2021_I}} for cultural life (Table S8): what a hromada spends on culture and education per resident depends more on the hromada than on its region.

**Figures:** Maps 21–23 — the three sphere indices, 2021 and 2025, national quintiles. In the 30 km zone, maps show population-weighted raion values (rule R3).

::: {.plate}
![Map 21 — economic sphere, 2021 and 2025](viina/qgis/maps/preview/21_sphere_economic.png)
:::


::: {.plate}
![Map 22 — rights sphere, 2021 and 2025](viina/qgis/maps/preview/22_sphere_rights.png)
:::


::: {.plate}
![Map 23 — cultural sphere, 2021 and 2025](viina/qgis/maps/preview/23_sphere_cultural.png)
:::


### 9.4 The threefold balance

The balance map (Map 24) shows, for each hromada, how its three sphere indices weigh against each other rather than how high they are. Each index is divided by the sum of the three; the three weights form a composition. Following the centred ternary balance scheme of Schöley (2021), colours are centred on the national average composition ({{bal_centre_2021}} for economic : rights : cultural in 2021, {{bal_centre_2025}} in 2025). Hue shows which sphere weighs more than on national average; colour strength shows how far the hromada departs from that average. One scale is used for both years.

For the analysis, the composition is expressed in isometric log-ratio coordinates (Egozcue et al. 2003), which give three measures:
- **imbalance:** the distance from the national centre (the strength of colour on Map 24);
- **lean to cultural:** the cultural weight against the other two;
- **lean to economic (vs rights):** the economic weight against the rights weight.

The median imbalance fell from {{bal_imb_med_2021}} in 2021 to {{bal_imb_med_2025}} in 2025: hromada profiles became more balanced overall, but not everywhere (section 10.3). In 2021 the Carpathian arc leaned to cultural and to rights over economic life: in the national cluster analysis, {{lisa_nat_lean_cult_2021_21_HH}}, {{lisa_nat_lean_cult_2021_26_HH}}, {{lisa_nat_lean_cult_2021_46_HH}} and {{lisa_nat_lean_cult_2021_73_HH}} hromadas of Zakarpattia, Ivano-Frankivsk, Lviv and Chernivtsi lie in high–high clusters of the cultural lean. By 2025 its clusters of imbalance had largely gone (from {{lisa_nat_imbalance_2021_21_HH}}, {{lisa_nat_imbalance_2021_26_HH}} and {{lisa_nat_imbalance_2021_73_HH}} to {{lisa_nat_imbalance_2025_21_HH}}, {{lisa_nat_imbalance_2025_26_HH}} and {{lisa_nat_imbalance_2025_73_HH}} in Zakarpattia, Ivano-Frankivsk and Chernivtsi), and the arc leaned to cultural and, slightly, to economic life.

::: {.plate}
![Map 24 — threefold balance, 2021 and 2025](viina/qgis/maps/preview/24_threefold_balance.png)
:::


## 10. The spheres and war exposure

The models follow Part I: standardised variables, oblast fixed effects, log population as control. p-values come from a restricted wild-cluster bootstrap by oblast (24 clusters, Webb weights, 9,999 draws; Cameron et al. 2008, Webb 2023); every result called robust below also holds with Conley spatial-HAC errors at 50 and 100 km (Conley 1999). Exposure is the logarithm of one plus the strikes recorded since 24 February 2022; alert hours are a check.

### 10.1 Where strikes fell

Before the war, hromadas that were later struck more had stronger spheres, within oblasts as well as between them (Table S3, first column): economic {{a1_econ_b}} (p {{a1_econ_p}}), rights {{a1_rights_b}} (p {{a1_rights_p}}), cultural {{a1_cult_b}} (p {{a1_cult_p}}). Strikes come after 2021, so this row describes where strikes fell, not what they did. Larger and better-equipped places are both more often targeted and more often reported (section 16.4); log population does not remove the pattern, which also reflects the concentration of industry and infrastructure.

### 10.2 From 2021 to 2025: the fall is concentrated in the zone

<!-- begin table: figures/tableS3_spheres_exposure.md (resilience/38_sphere_tables.py) -->
**Table S3. The spheres and war exposure**

| Outcome | 2021 level (pre-war) | 2025 given 2021 [95 % interval] | 2025 given 2021, without zone | 2025 given 2021, alert hours |
|---|---|---|---|---|
| Economic sphere | +0.24 (< 0.001) | −0.15 (0.013) [−0.27 to −0.03] | 0.00 (0.974) | −0.27 (0.087) |
| Rights sphere | +0.12 (0.009) | +0.01 (0.859) [−0.08 to +0.10] | +0.08 (0.013) | −0.11 (0.284) |
| Cultural sphere | +0.13 (< 0.001) | −0.11 (0.044) [−0.22 to 0.00] | +0.02 (0.147) | −0.27 (0.079) |
| Imbalance (distance from the national centre) | — | +0.30 (< 0.001) | +0.13 (< 0.001) | +0.04 (0.310) (without zone) |
| Lean to cultural | — | 0.00 (0.956) | −0.03 (0.208) | 0.00 (0.995) (without zone) |
| Lean to economic (vs rights) | — | −0.20 (0.028) | +0.01 (0.787) | −0.07 (0.135) (without zone) |

Standardised coefficient of exposure (log strikes since 24 Feb 2022; last column: alert hours, 12 months), with p from a restricted wild-cluster bootstrap by oblast (24 clusters, 9,999 draws) in brackets and the 95 % interval from inverting that test. All models with oblast fixed effects and log population 2020; "given 2021" adds the 2021 value of the same outcome. Zone: the 196 hromadas within 30 km of the front line or the Russian or Belarusian border. The 2021 row describes where strikes later fell; strikes cannot affect the 2021 values.
<!-- end table: figures/tableS3_spheres_exposure.md -->

Given their own 2021 values, more-exposed hromadas fell back in economic life ({{a3_econ_b}}, 95 % interval {{a3_econ_ci}}) and in cultural life ({{a3_cult_b}}, {{a3_cult_ci}}) relative to other hromadas of the same oblast. Rights life did not change with exposure ({{a3_rights_b}}).

**Both falls disappear without the {{n_zone}} hromadas within 30 km of the front line or the Russian or Belarusian border** (economic {{a3nz_econ_b}}, p {{a3nz_econ_p}}; cultural {{a3nz_cult_b}}, p {{a3nz_cult_p}}). Leaving out only the three frontline oblasts weakens but does not remove them (economic {{a3nf_econ_b}}, p {{a3nf_econ_p}}): the fall is carried by zone hromadas in the oblasts along the Russian border as well. The relative loss is a matter of the zone, not a general cost of being struck. Alert hours point the same way, but they are mostly an oblast-level signal and the fixed effects absorb them (p {{a3alert_econ_p}} for economic life).

Outside the zone, more-exposed hromadas gained in rights life ({{a3nz_rights_b}}, p {{a3nz_rights_p}}).

<!-- begin table: figures/tableS4_zone_gap.md (resilience/38_sphere_tables.py) -->
**Table S4. The zone: change 2021–2025 by indicator**

| Indicator | Median rank change, zone | Median rank change, rest of the same oblasts | Zone gap, 2025 given 2021 (p) [95 % interval] | Exposure outside the zone (p) |
|---|---|---|---|---|
| **Economic sphere, like-for-like** | −0.08 | +0.01 | −0.38 (0.009) [−0.62 to −0.14] | 0.00 (0.840) |
| Civilian income tax per resident | −0.10 | +0.01 | −0.47 (0.004) | +0.02 (0.158) |
| Single tax per resident | −0.04 | +0.01 | −0.19 (0.124) | +0.02 (0.207) |
| Property and land payments per resident | −0.09 | 0.00 | −0.40 (0.004) | 0.00 (0.805) |
| **Rights sphere, like-for-like** | −0.03 | +0.02 | −0.26 (0.007) [−0.39 to −0.14] | +0.07 (0.003) |
| Transfer dependency (−) | −0.15 | +0.01 | −0.44 (0.005) | 0.00 (0.824) |
| Capital-expenditure share | +0.10 | +0.02 | +0.05 (0.672) | +0.09 (0.012) |
| Social protection spending per resident | −0.05 | 0.00 | −0.21 (0.009) | +0.12 (< 0.001) |
| **Cultural sphere, like-for-like** | −0.07 | +0.02 | −0.55 (0.001) [−0.83 to −0.24] | +0.01 (0.460) |
| Culture and arts spending per resident | −0.07 | +0.02 | −0.42 (0.005) | −0.02 (0.218) |
| Education spending per resident | −0.07 | +0.02 | −0.44 (< 0.001) | +0.05 (0.001) |
| Extracurricular education spending per resident | −0.01 | 0.00 | −0.22 (0.004) | 0.00 (0.824) |
| Civilian income-tax growth 2021–25 (2025 only) | — | — | −0.81 (< 0.001) (2025 level) | — |
| DREAM projects per 10,000 (2025 only) | — | — | −0.03 (0.800) (2025 level) | — |
| Schools per 10,000 (2025 only) | — | — | −0.17 (0.123) (2025 level) | — |

Rank change: percentile rank 2025 minus 2021 (0–1 scale) among non-occupied hromadas. Zone gap: difference between zone hromadas and other hromadas of the same oblast in the 2025 rank, given the 2021 rank and log population, in standard deviations. Exposure outside the zone: coefficient of log strikes in the same model without zone hromadas. Like-for-like: mean rank of the indicators measured in both years. Per-resident values use the 2020 population.
<!-- end table: figures/tableS4_zone_gap.md -->

Table S4 compares zone hromadas with the rest of their own oblast, indicator by indicator, on the like-for-like measure (section 9.2):

- **Economic life** in the zone fell {{q1zone_ll_econ_b}} standard deviations behind the rest of the oblast (interval {{q1zone_ll_econ_ci}}). Civilian income tax ({{q1zone_pdfo_civ_pc_b}}) and property and land payments ({{q1zone_property_tax_pc_b}}) carry the fall; the single tax of small entrepreneurs fell less ({{q1zone_single_tax_pc_b}}, p {{q1zone_single_tax_pc_p}}). About half of the fall of the full economic index in the zone (median change {{q1m_d_econ_zone}}, like-for-like {{q1m_d_ll_econ_zone}}) comes from the growth indicator: the median zone hromada ranks {{q1r25_zone_pdfo_civ_growth_rel_2125}} on income-tax growth, against {{q1r25_rest_pdfo_civ_growth_rel_2125}} in the oblasts without zone hromadas.
- **Rights life** fell too ({{q1zone_ll_rights_b}}, {{q1zone_ll_rights_ci}}), through rising transfer dependency ({{q1zone_transfer_dep_civ_b}} on the autonomy scale) and lower social spending per resident ({{q1zone_social_pc_b}}). Capital share and DREAM projects are no different from the rest of the oblast.
- **Cultural life** fell most ({{q1zone_ll_cult_b}}, {{q1zone_ll_cult_ci}}): culture and arts ({{q1zone_culture_arts_pc_b}}), education ({{q1zone_education_pc_b}}) and extracurricular education ({{q1zone_extracurricular_pc_b}}) all fell.

Per-resident values use the 2020 population. In the zone, where many people have left, the fall is also a fall in the number of people still paying taxes and using services; the data cannot separate the two.

Outside the zone, exposure goes with no fall in any economic or cultural indicator. Instead, more-exposed hromadas raised their capital-expenditure share ({{q1expnz_capex_share_b}}, p {{q1expnz_capex_share_p}}), social protection spending ({{q1expnz_social_pc_b}}, p {{q1expnz_social_pc_p}}) and education spending per resident ({{q1expnz_education_pc_b}}, p {{q1expnz_education_pc_p}}). The rights gain of struck hromadas outside the zone is spending, not transfers.

### 10.3 The balance

Exposure goes with a more one-sided profile: given 2021, imbalance rises with exposure ({{a3_imbalance_b}}, p {{a3_imbalance_p}}). This also holds without the zone ({{q2nz_imbalance_b}}, p {{q2nz_imbalance_p}}) and inside it ({{q2in_imbalance_b}}, p {{q2in_imbalance_p}}; only 12 oblast clusters). The median imbalance fell from 2021 to 2025 everywhere except the zone:

| | 2021 | 2025 |
|---|---|---|
| Zone hromadas | {{q2_imbalance_2021_zone}} | {{q2_imbalance_2025_zone}} |
| Rest of the same oblasts | {{q2_imbalance_2021_same}} | {{q2_imbalance_2025_same}} |
| Other oblasts | {{q2_imbalance_2021_other}} | {{q2_imbalance_2025_other}} |

*Median distance from the national centre (isometric log-ratio units).*

The direction of the shift is a matter of the zone. Given 2021, zone hromadas lean {{q2zone_lean_econ_rights_b}} standard deviations further to rights over economic life than the rest of their oblast (interval {{q2zone_lean_econ_rights_ci}}), and inside the zone the lean grows with exposure ({{q2in_lean_econ_rights_b}}, p {{q2in_lean_econ_rights_p}}). Without the zone there is none ({{q2nz_lean_econ_rights_b}}). The lean to cultural life does not change with exposure anywhere. The rights-leaning zone raions of Map 24 are therefore not places where rights life grew: like-for-like it fell (section 10.2). They are places where economic life collapsed while capital programmes (median capital-share rank {{q1m_capex_zone}} in the zone) and reconstruction projects held the rights index up.

## 11. The spheres and functional resilience

This section relates the pre-war (2021) spheres to the light outcomes of Part I. The 2025 spheres are contemporaneous with the outcomes and are not used here. All three spheres enter together, with exposure, the light controls of Part I (log population, log lit pixels, log 2021 radiance) and oblast fixed effects.

<!-- begin table: figures/tableS5_functional.md (resilience/38_sphere_tables.py) -->
**Table S5. Pre-war spheres (2021) and functional resilience**

| Outcome | Economic 2021 | Rights 2021 | Cultural 2021 |
|---|---|---|---|
| Recovery index (2024 / 2021) | +0.02 (0.698) [−0.07 to +0.11] | +0.09 (0.048) [0.00 to +0.18] | −0.06 (0.052) [−0.12 to 0.00] |
| Summer-2024 light vs H2 2023 | +0.06 (0.521) [−0.09 to +0.24] | +0.20 (0.002) [+0.08 to +0.32] | −0.11 (0.039) [−0.22 to −0.01] |
| Recent light level | +0.08 (0.064) [0.00 to +0.18] | +0.08 (0.028) [+0.01 to +0.14] | −0.08 (< 0.001) [−0.12 to −0.05] |

One model per outcome with all three 2021 sphere indices, log strikes, log population 2020, log lit pixels, log 2021 radiance and oblast fixed effects. Standardised coefficients, wild-cluster p in brackets, 95 % interval. Outcomes as in Part I (sections 5.2, 8.4); higher = more light kept.
<!-- end table: figures/tableS5_functional.md -->

**Outage loss.** Hromadas with a stronger pre-war rights sphere lost less light in the summer-2024 outages ({{b1_s24_rights_b}}, interval {{b1_s24_rights_ci}}; on hromadas with reliable light data {{b1r_s24_rights_b}}, p {{b1r_s24_rights_p}}). The economic sphere adds nothing once rights and cultural life are in the model ({{b1_s24_econ_b}}, p {{b1_s24_econ_p}}). This is the clearest link between a sphere and functional resilience in the study.

<!-- begin table: figures/tableS6_rights_outage.md (resilience/38_sphere_tables.py) -->
**Table S6. Which rights indicators go with the summer-2024 light loss**

| Rights indicator, 2021 rank | All (p) [95 % interval] | Reliable light data | Without zone |
|---|---|---|---|
| Transfer dependency (−) | +0.21 (< 0.001) [+0.11 to +0.30] | +0.15 (0.016) | +0.29 (< 0.001) |
| Capital-expenditure share | +0.08 (0.011) [+0.02 to +0.14] | +0.06 (0.097) | +0.09 (0.019) |
| Social spending per resident | +0.05 (0.303) [−0.05 to +0.13] | +0.04 (0.464) | +0.05 (0.271) |
| Candidates per seat 2020 | +0.04 (0.424) [−0.06 to +0.15] | +0.05 (0.465) | +0.03 (0.534) |

Outcome: log summer-2024 light relative to July–December 2023 (higher = smaller loss). The four rights indicators enter together, with economic and cultural 2021, log strikes, the light controls and oblast fixed effects. Reliable light: at least 30 lit pixels and pre-war noise at most 0.35.
<!-- end table: figures/tableS6_rights_outage.md -->

One indicator carries it (Table S6): **lower transfer dependency before the war goes with a smaller outage loss** ({{q3_transfer_dep_civ_b}}, interval {{q3_transfer_dep_civ_ci}}). It holds on reliable light data ({{q3r_transfer_dep_civ_b}}, p {{q3r_transfer_dep_civ_p}}) and more strongly without the zone ({{q3nz_transfer_dep_civ_b}}). Capital share adds a little ({{q3_capex_share_b}}, p {{q3_capex_share_p}}). Social spending and electoral contestation add nothing. In threefold terms, the pre-war capacity result of Part I (section 8.5) is a rights-sphere result: it belongs to the fiscal autonomy of local self-government, with the tax base held constant. Section 13 sets out what could explain it.

**Recovery and recent level.** For the annual recovery index the associations are weak (rights {{b1_rec_rights_b}}, p {{b1_rec_rights_p}}; cultural {{b1_rec_cult_b}}, p {{b1_rec_cult_p}}). For the recent light level, a stronger pre-war cultural sphere goes with less light ({{b1_recent_cult_b}}, interval {{b1_recent_cult_ci}}; reliable data {{b1r_recent_cult_b}}, p {{b1r_recent_cult_p}}). Section 13 finds no explanation for this and treats it as fragile.

**No buffering.** Adding a sphere × exposure interaction, one sphere at a time, gives no reliable evidence that any sphere softens the association between exposure and light. One of nine interactions is nominally significant (cultural × exposure on the recent level, {{b2int_recent_cult_b}}, p {{b2int_recent_cult_p}}), which is about what nine tests produce by chance. This matches Part I (section 7.3).

## 12. How the spheres relate

### 12.1 Together or apart

<!-- begin table: figures/tableS7_between.md (resilience/38_sphere_tables.py) -->
**Table S7. The spheres against each other**

| Pair | 2021: ρ \| within | 2021: b (p) [95 %] | 2025: ρ \| within | 2025: b (p) [95 %] | Change: ρ \| within | Change: b (p) [95 %] |
|---|---|---|---|---|---|---|
| Economic–rights | 0.55 \| 0.36 | +0.52 (< 0.001) [+0.43 to +0.61] | 0.58 \| 0.53 | +0.62 (< 0.001) [+0.54 to +0.70] | 0.09 \| 0.17 | +0.18 (< 0.001) [+0.11 to +0.24] |
| Economic–cultural | 0.58 \| 0.58 | +0.42 (< 0.001) [+0.38 to +0.47] | 0.63 \| 0.61 | +0.53 (< 0.001) [+0.48 to +0.59] | 0.38 \| 0.29 | +0.38 (< 0.001) [+0.29 to +0.47] |
| Rights–cultural | 0.22 \| 0.13 | +0.22 (< 0.001) [+0.19 to +0.25] | 0.27 \| 0.25 | +0.36 (< 0.001) [+0.31 to +0.40] | 0.14 \| 0.18 | +0.19 (< 0.001) [+0.14 to +0.25] |

ρ: Spearman rank correlation, plain and within oblasts (ranks demeaned by oblast). b: standardised coefficient of the second sphere in a model of the first with log population and oblast fixed effects, wild-cluster p and 95 % interval. Change: 2025 minus 2021 index (change of relative position).
<!-- end table: figures/tableS7_between.md -->

- **Economic and cultural life go together,** in every oblast (rank correlation {{c_econ_cult_2021_rho}} in 2021, {{c_econ_cult_2021_rhow}} within oblasts), and their changes from 2021 to 2025 go together too ({{c_econ_cult_change_b}}, interval {{c_econ_cult_change_ci}}). Part of this is budget arithmetic: own revenue pays for culture and part of education. It is the sense in which the economic sphere supplies the means of the cultural one (section 9.1).
- **Economic and rights life** were related in 2021 mainly between oblasts ({{c_econ_rights_2021_rho}} overall, {{c_econ_rights_2021_rhow}} within oblasts). By 2025 the relation holds within oblasts as well ({{c_econ_rights_2025_rhow}}): the tax base and budget autonomy have come closer inside each oblast.
- **Rights and cultural life** are only weakly related ({{c_rights_cult_2021_rho}} in 2021, {{c_rights_cult_2025_rho}} in 2025).

No pair moves in opposite directions. There is no sign that a weak sphere is compensated by a strong one; the picture is of two coupled spheres and one apart. Residual spatial dependence remains in these models (Moran's I {{c_moran_min}} to {{c_moran_max}}), so shared regional factors below the oblast level are not captured.

### 12.2 Clusters

<!-- begin table: figures/tableS8_lisa.md (resilience/38_sphere_tables.py) -->
**Table S8. Spatial clustering of the spheres and the balance**

| Variable | National: Moran's I | National: HH / LL clusters (after FDR) | Carpathian: Moran's I | Carpathian: HH / LL clusters (after FDR) |
|---|---|---|---|---|
| Economic 2021 | 0.48 | 200 / 255 (106 / 192) | 0.39 | 29 / 33 (17 / 6) |
| Economic 2025 | 0.42 | 186 / 225 (70 / 119) | 0.49 | 42 / 43 (27 / 18) |
| Economic change | 0.45 | 219 / 129 (81 / 71) | 0.01 | 7 / 3 (0 / 0) |
| Rights 2021 | 0.41 | 167 / 199 (97 / 117) | 0.30 | 41 / 23 (6 / 3) |
| Rights 2025 | 0.43 | 189 / 217 (80 / 120) | 0.31 | 41 / 24 (11 / 1) |
| Rights change | 0.11 | 79 / 66 (18 / 11) | 0.01 | 9 / 11 (0 / 0) |
| Cultural 2021 | 0.11 | 57 / 89 (4 / 9) | 0.15 | 17 / 26 (1 / 2) |
| Cultural 2025 | 0.16 | 72 / 111 (6 / 22) | 0.22 | 19 / 34 (3 / 10) |
| Cultural change | 0.24 | 70 / 82 (9 / 38) | 0.07 | 11 / 8 (0 / 0) |
| Imbalance 2021 | 0.29 | 122 / 77 (56 / 9) | 0.22 | 25 / 29 (0 / 5) |
| Imbalance 2025 | 0.21 | 81 / 82 (0 / 0) | 0.11 | 15 / 32 (0 / 0) |
| Lean to cultural 2021 | 0.41 | 173 / 133 (105 / 38) | 0.31 | 32 / 37 (6 / 13) |
| Lean to cultural 2025 | 0.32 | 142 / 132 (57 / 28) | 0.20 | 19 / 29 (0 / 0) |
| Lean to economic vs rights 2021 | 0.27 | 105 / 110 (22 / 54) | 0.13 | 19 / 16 (0 / 0) |
| Lean to economic vs rights 2025 | 0.30 | 81 / 101 (10 / 41) | 0.04 | 6 / 15 (0 / 4) |

Global Moran's I and local Moran (LISA) with six nearest neighbours (UA_LAEA representative points, row-standardised), 9,999 permutations; HH = high values among high neighbours, LL = low among low, at p < 0.05 and, in brackets, after a false-discovery-rate cut (Benjamini–Hochberg, 0.05). Carpathian: weights built within the four oblasts only. Counts of hromadas; no hromada is named or mapped (rule R3).
<!-- end table: figures/tableS8_lisa.md -->

Local indicators of spatial association (LISA; Anselin 1995) identify hromadas whose values resemble those of their neighbours.
- **Economic and rights life** form large regional clusters in both years; cultural life forms few.
- **The economic change** is strongly clustered (Moran's I {{lisa_nat_d_econ_I}}). High–high clusters of economic rise number {{lisa_nat_d_econ_HH}}; {{q5lisa_hh_carp}} of them lie in the Carpathian oblasts ({{lisa_nat_d_econ_21_HH}} in Zakarpattia, {{lisa_nat_d_econ_26_HH}} in Ivano-Frankivsk, {{lisa_nat_d_econ_46_HH}} in Lviv, {{lisa_nat_d_econ_73_HH}} in Chernivtsi) and they started low (median economic index {{q5lisa_hh_econ21}} in 2021). Low–low clusters of economic fall number {{lisa_nat_d_econ_LL}}, {{q5lisa_ll_zone}} of them in the zone and none in the Carpathian oblasts. Within the four Carpathian oblasts the rise is even (Moran's I {{lisa_carp_d_econ_I}}): the region moved as a whole.
- **Imbalance** clustered in 2021 ({{lisa_nat_imbalance_2021_HH}} high–high hromadas); in 2025 no cluster survives the false-discovery-rate cut.

Cluster counts after the false-discovery-rate cut (Benjamini and Hochberg 1995) are smaller, often by half. Hromada cluster membership is not published: it includes zone hromadas (rule R3).

## 13. Why there?

For each clear pattern, this section lists the candidate explanations, the data that would tell them apart, what the data show and what remains open. The tests are in `resilience/37_why_there.py`. "Against" means the data contradict the candidate as a main explanation, not that it plays no part.

**Table W1. The fall of economic and cultural life in the zone**

| Candidate explanation | Data that would distinguish | Result | Open |
|---|---|---|---|
| Strikes themselves | Exposure inside and outside the zone | Against as a general cause: outside the zone, exposure goes with no economic or cultural fall (like-for-like economic {{q1expnz_ll_econ_b}}, cultural {{q1expnz_ll_cult_b}}) | Whether damage or proximity to the front drives the zone gap |
| People left: fewer taxpayers and users per pre-war resident | Hromada-level population or displacement, 2025 | Not testable: only modelled population (GHS 2025) and oblast-level IOM data are available | Main open question |
| Firms left or closed | Registrations by hromada | Registration growth exists for five oblasts only (Vinnytsia, Zhytomyr, Rivne, Kharkiv, Khmelnytskyi); the single tax fell least ({{q1zone_single_tax_pc_b}}, p {{q1zone_single_tax_pc_p}}) | Needs registration data for all oblasts |
| Military administrations replaced council budget decisions | Status by hromada | Not assembled | Candidate for the next version |
| A change of measure | Like-for-like index | Partly: about half of the full index fall is the 2025-only growth indicator; like-for-like the gap is still {{q1zone_ll_econ_b}} | — |

**Table W2. Profiles more one-sided with exposure, and rights-leaning in the zone**

| Candidate explanation | Data that would distinguish | Result | Open |
|---|---|---|---|
| State transfers replaced own revenue | Transfer dependency | Supported for the zone: transfer dependency rose ({{q1zone_transfer_dep_civ_b}} on the autonomy scale) | — |
| Reconstruction and capital programmes | Capital share, DREAM projects | Capital share high in the zone (median rank {{q1m_capex_zone}}) but not above the rest of its oblasts ({{q1zone_capex_share_b}}); DREAM no different ({{q1zone25_dream_per10k_b}}) | Oblast-wide capital programmes |
| Economic collapse, rights held up | Like-for-like indices | Supported: economic {{q1zone_ll_econ_b}}, rights {{q1zone_ll_rights_b}} against the rest of the oblast | — |
| General war pressure outside the zone | Imbalance and leans without the zone | Imbalance rises with exposure outside the zone ({{q2nz_imbalance_b}}), but in no common direction (leans {{q2nz_lean_cult_b}} and {{q2nz_lean_econ_rights_b}}) | Which spheres move in struck hromadas outside the zone |

**Table W3. Fiscal autonomy and a smaller loss of light in the summer-2024 outages**

| Candidate explanation | Data that would distinguish | Result | Open |
|---|---|---|---|
| A stronger local economy (more users on priority supply) | Economic sphere in the same model | Against as the main explanation: the economic sphere adds nothing ({{b1_s24_econ_b}}); transfer dependency carries the result | — |
| Budgets with room to act: generators, backup power, network repairs | Municipal procurement of generators and repairs (Prozorro), by hromada | Not tested | First candidate for further work; procurement data are public, but must be screened under rules R1 and R3 |
| Local network condition and grid topology | Grid and outage-group data by area | Not available in open data (security) | Open |
| An artefact of the frontline zone | Model without zone hromadas | Against: the association is stronger without the zone ({{q3nz_transfer_dep_civ_b}}) | — |
| Noise in small light counts | Reliable light data only | Against: holds ({{q3r_transfer_dep_civ_b}}, p {{q3r_transfer_dep_civ_p}}) | — |

<!-- begin table: figures/tableS9_carpathian_econ.md (resilience/38_sphere_tables.py) -->
**Table S9. The Carpathian economic change, medians**

| Measure | Zakarpattia | Ivano-Frankivsk | Lviv | Chernivtsi | Carpathian | Rest, outside zone |
|---|---|---|---|---|---|---|
| Economic index 2021 | 0.15 | 0.16 | 0.40 | 0.13 | 0.20 | 0.57 |
| Economic index 2025 | 0.32 | 0.31 | 0.53 | 0.29 | 0.37 | 0.57 |
| Change, index | +0.14 | +0.14 | +0.17 | +0.14 | +0.15 | −0.01 |
| Change, like-for-like | +0.02 | +0.02 | +0.09 | +0.03 | +0.04 | 0.00 |
| … civilian income tax | +0.02 | +0.01 | +0.07 | +0.01 | +0.03 | +0.01 |
| … single tax | 0.00 | +0.02 | +0.05 | +0.03 | +0.02 | 0.00 |
| … property and land | +0.04 | +0.02 | +0.11 | +0.03 | +0.04 | 0.00 |
| Income-tax growth, rank 2025 | 0.68 | 0.68 | 0.79 | 0.65 | 0.70 | 0.52 |
| Income-tax growth 2021–25 / national median | 1.08 | 1.08 | 1.15 | 1.07 | 1.09 | 1.01 |

Index values 0–1 (percentile-rank means); changes 2025 minus 2021. Like-for-like: the three tax bases measured in both years; the 2025 index adds civilian income-tax growth. Income-tax growth: civilian PIT 2025 / 2021 relative to the national median (1 = national median).
<!-- end table: figures/tableS9_carpathian_econ.md -->

**Table W4. The Carpathian economic rise**

| Candidate explanation | Data that would distinguish | Result | Open |
|---|---|---|---|
| A change of measure (income-tax growth added in 2025) | Like-for-like index | Supported: the index rose {{q5_d_econ_carp}}, like-for-like only {{q5_d_ll_econ_carp}} (Lviv {{q5_d_ll_econ_lv}}); about three quarters of the rise is the growth indicator | — |
| Catch-up from a low start (regression to the mean) | Gap given the 2021 level | Supported: given 2021, the Carpathian lead is {{q5lvl_ll_b}} (interval {{q5lvl_ll_ci}}) | — |
| Lviv alone | Gap without Lviv | Largely: {{q5lvl_nolviv_b}} (p {{q5lvl_nolviv_p}}) | — |
| Relocation of firms and people | Registrations and displacement by hromada | Not testable: registration growth covers no Carpathian oblast; displacement data are oblast-level. The single tax, the nearest small-business signal, rose little ({{q5_dr_single_tax_pc_carp}}) | Main open question |
| Faster earnings growth in the west | Civilian income-tax growth | Real: {{q5_pdfo_civ_growth_rel_2125_carp}} times the national median (Lviv {{q5_pdfo_civ_growth_rel_2125_lv}}) | Whether it follows relocated employers (tax is booked at the employer's address, section 16.7) |

**Table W5. Economic and cultural life move together**

| Candidate explanation | Data that would distinguish | Result | Open |
|---|---|---|---|
| Budget arithmetic: own revenue pays for culture | Spending as shares instead of per resident | Consistent: as shares the cultural sphere did not cohere and opposed the rights sphere (section 9.1) | — |
| Shared population denominator | Population control, within-oblast models | Against as the whole story: holds with log population and within oblasts ({{c_econ_cult_2025_b}}) | — |
| Economic life supplies the means of cultural life (threefold reading) | Non-budget cultural life (associations, media, religious communities) | Not distinguishable from the arithmetic with budget data | Cultural life outside the budget is not measured (rule R7 limits what may be) |

**Table W6. A stronger pre-war cultural sphere and less light now (fragile)**

| Candidate explanation | Data that would distinguish | Result | Open |
|---|---|---|---|
| Education spending marks dense rural school networks in shrinking places | Class size, rural school share, pupils per 1,000, population change | Against: the coefficient does not move ({{q4_school_b}} with school network, {{q4_pop_b}} with population change) | — |
| One cultural indicator | Indicators separately | No single indicator holds on reliable light data (culture and arts {{q4r_culture_arts_pc_b}}, p {{q4r_culture_arts_pc_p}}) | — |
| Small, well-funded rural hromadas | Hromada type; profile by quintile | Present in settlement ({{q4_settlement_b}}) and village ({{q4_village_b}}) hromadas, absent in cities ({{q4_city_b}}); the top cultural quintile is small (median population {{q4_pop_q5}}, against {{q4_pop_q1}} in the bottom one) and economically strong (economic index {{q4_econ_q5}}) | Unexplained; not a finding |

The two remaining patterns named in the plan for this version, the four Carpathian light curves and high trust with weak finances, concern oblast-level data and are discussed in section 15.5.

# Part III — Trust, cohesion and reception

Part III turns to the relational side of resilience: trust in local administration, community cohesion, belonging, and the movement of displaced people and taxpayers. These data are published only by oblast, so this part describes and compares; it does not model. Section 15 reads all three parts together for the Carpathian oblasts.

## 14. Relational resilience by oblast: trust, cohesion and displacement

Survey and displacement data are available only by oblast. They cannot enter the hromada models: any oblast-level variable is absorbed completely by the oblast fixed effects. This section is therefore descriptive. It asks how oblasts differ in social conditions and displacement, not whether these conditions explain hromada recovery.

### 14.1 Trust, cohesion and satisfaction (reSCORE 2024)

reSCORE Ukraine 2024 surveyed {{rescore_n}} respondents in all oblasts except Donetsk, Luhansk and Crimea. We use four indicators, each on a 0–10 scale: trust in local administration, community cohesion, locality satisfaction and sense of belonging.

**Table 11. Selected reSCORE 2024 indicators by oblast** [[PENDING: full table with sample sizes and 95 % intervals — request 9]]

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

### 14.2 Displacement (IOM DTM)

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

**Figures:** Map 18 — oblast context grid: reSCORE 2024 differences from the national score (the IOM DTM panel is left empty; IOM terms do not allow redistribution). Figure 3 — registered vs present IDPs per 1,000 by oblast [[PENDING: request 29]].

::: {.plate}
![Map 18 — reSCORE 2024 by oblast, difference from national](viina/qgis/maps/preview/18_oblast_context.png)
:::


### 14.3 Why these data stay at oblast level

Displacement is the most obvious candidate explanation for the within-oblast capacity association in section 7.4. Hromadas that received many IDPs may have both higher income-tax growth and brighter nights. Testing this requires hromada-level displacement data, which has been requested from IOM. Removing income-tax growth from the capacity index lowers the within-oblast association only modestly (section 7.4), so displacement acting through income tax alone does not explain it. It could still act through other channels, such as own revenue or the demand for lighting. Until hromada-level data are available, the capacity association remains open to this interpretation.

## 15. The Carpathian region

This section applies the national results to the {{n_carp_hromadas}} non-occupied hromadas of four oblasts: {{carpathian_oblasts}}. All figures use the same methods and thresholds as the national analysis. Map 17 shows capacity and exposure as terciles computed within the region, so that differences between Carpathian hromadas are visible rather than lost in the national range.

::: {.plate}
![Map 17 — Carpathian region, alert hours × capacity (regional terciles)](viina/qgis/maps/preview/17_carpathian_resilience.png)
:::


::: {.plate}
![Map 13 — Carpathian region, strike hot and cold spots](viina/qgis/maps/preview/13_carpathian_hotspots.png)
:::


### 15.1 Profile

**Exposure.**
- A typical Carpathian hromada spent about {{carp_alert_hours_12m}} hours under alert in the last 12 months, against about {{nat_alert_hours_12m}} nationally.
- Fewer than one in ten Carpathian hromadas has recorded a strike since 2022; nationally, more than one in five has.
- Lviv oblast is the most exposed of the four: about {{lviv_struck_share}} of its hromadas have recorded a strike.

**Fiscal capacity** is not uniformly low.
- The median Lviv hromada is above the national median on the capacity index, and Lviv depends least on transfers.
- In Ivano-Frankivsk and Zakarpattia, the median hromada raises about {{own_rev_pc_if_zk}} hryvnias of own revenue per resident, against about {{own_rev_pc_nat}} nationally. Transfers make up more than half its revenue.
- Chernivtsi is weaker still, at under {{own_rev_pc_cv}} hryvnias.

<!-- begin table: figures/table11_carpathian.md (resilience/26_publication_tables.py) -->
**Table 12. Carpathian oblasts and Ukraine, non-occupied hromadas**

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

**The three spheres** (Table S2). Before the war the four oblasts were the weakest in the country in economic life (median {{sph_med_econ_2021_21}} in Zakarpattia, {{sph_med_econ_2021_26}} in Ivano-Frankivsk, {{sph_med_econ_2021_46}} in Lviv and {{sph_med_econ_2021_73}} in Chernivtsi, on a scale where the national median is 50) and weak in rights life except Lviv; cultural life was closer to the national median. Their profile leaned to cultural life and to rights over economic life, and it was one of the most unbalanced in the country; by 2025 much of that imbalance had gone (section 9.4).

The national models apply here too. Most of the region's brightness is what oblast fixed effects capture: lower exposure and grid conditions shared across each oblast. It is not evidence that Carpathian hromadas manage recovery better than hromadas elsewhere.

### 15.2 Capacity and outage loss

Within the region, as nationally, hromadas with more fiscal capacity kept relatively more of their light in the 2024 outages. The pattern is also regional. Of the {{carp_weak_hit}} Carpathian hromadas with both low capacity and large outage loss, {{carp_weak_hit_if_cv}} are in Ivano-Frankivsk and Chernivtsi. At the other corner, Lviv (15) and Zakarpattia (12) hold most of the {{carp_strong_steady}} hromadas with high capacity and small losses. Both groups are corners of a regional classification: terciles, within the four oblasts, of the 2025 capacity index and of the light kept in June–July 2024 as a share of the second half of 2023. Low capacity is the bottom third (percentile rank below about 30), a large loss the bottom third of retention (at most 24 % of the 2023 level); the top thirds start at about 52 and 47 %. On the same rule with national terciles, {{nat_weak_hit}} hromadas are weak and hit. Much of what looks like a local story is the grid of the oblast.

### 15.3 Low fiscal capacity, high local trust, but not everywhere

The oblast pattern:
- **Ivano-Frankivsk** combines below-median fiscal capacity with trust in local administration of {{trust_if_abs}} on a 0–10 scale, the highest of the four oblasts. It also records the highest community cohesion and locality satisfaction in the country, and above-average economic security.
- **Chernivtsi** also combines weak finances with trust above the national average (+{{trust_diff_cv}}).
- **Zakarpattia**, the brightest of the four, reports one of the lowest levels of trust in local administration in the country: {{trust_zk_abs}}.
- **Lviv**, the fiscally strongest, is close to the national average (+{{trust_diff_lv}}).

This is a juxtaposition of two levels of measurement: hromada fiscal data and oblast survey means. It is not a relationship. We cannot say whether the hromadas with low capacity are the ones whose residents report high trust. The observation matters because fiscal indicators alone would rank much of the region as weak. Survey evidence suggests that, in at least two of its oblasts, local government holds a resource the budget data does not measure. Light, budgets and trust point in different directions here: a place can keep its lights on and distrust those who run it, or go dark and hold together.

### 15.4 A region of reception

The Carpathian oblasts gained income tax as firms and workers moved west.
- **2022.** In the third quarter of 2022, the median hromada in all four oblasts collected {{carp_pit_q3_2022_range}} more civilian income tax, relative to its own 2021 level, than the median hromada nationally. Ivano-Frankivsk gained most. The gain was unrelated to fiscal capacity: it followed people, not institutions.
- **Mid-2024.** The advantage had shrunk to a few per cent.
- **2025.** It returned strongly in Lviv and Ivano-Frankivsk (about {{carp_pit_2025_lv_if}} above the national median), and less so in Zakarpattia and Chernivtsi ({{carp_pit_2025_zk_cv}}).

Displaced people show the same movement:
- Registered IDPs range from {{idp_reg_carp_range}} per 1,000 pre-war residents across the four oblasts. IOM's estimate of those actually present is lower and strikingly even: {{idp_present_carp_range}} in all four.
- Registrations have fallen by {{idp_carp_decline}} since February 2023.

Per-capita figures based on pre-war population are therefore especially uncertain here (section 16.6), and in both directions.

Part II adds a caution to the income-tax story. Measured on the tax bases available in both years, the region's economic position rose only a little from 2021 to 2025 (median {{q5_d_ll_econ_carp}}; Lviv {{q5_d_ll_econ_lv}}), and given its low starting point the Carpathian lead is not robust ({{q5lvl_ll_b}}, p = {{q5lvl_ll_p}}). The faster growth of civilian income tax ({{q5_pdfo_civ_growth_rel_2125_carp}} times the national median) is real, but in level the west has caught up only slightly, mostly in Lviv (section 13, Table W4).

### 15.5 Why there? The four light curves and trust with weak finances

**Table W7. Four different light curves in four neighbouring oblasts**

| Candidate explanation | Data that would distinguish | Result | Open |
|---|---|---|---|
| Exposure | Strikes and alert hours by oblast | Against: Ivano-Frankivsk, the least struck of the four, is the darkest; alert hours are similar in all four (Table 12) | — |
| Fiscal capacity or the spheres | Oblast medians; within-oblast models | Against as the explanation between oblasts: Zakarpattia, the brightest, is among the weakest in economic life ({{sph_med_econ_2021_21}}). Within oblasts, pre-war fiscal autonomy goes with a smaller outage loss (section 11) | — |
| Grid topology and supply priorities in the western network | Outage groups and supply schedules by area | Not available in open data. All four fell together in July 2024, which points to a shared grid cause | Needs grid data released with a security delay |
| Street-lighting decisions of oblasts and hromadas | Lighting policy by hromada | Not collected | Open |
| Terrain: mountain and lowland | A mountain indicator; comparison within the region | Not yet tested (request 30) | Next version |

**Table W8. High trust in local administration with weak finances (Ivano-Frankivsk, Chernivtsi)**

| Candidate explanation | Data that would distinguish | Result | Open |
|---|---|---|---|
| Trust mirrors the rights sphere measured from budgets and elections | Rights sphere by oblast | Against: rights life is low in Ivano-Frankivsk ({{sph_med_rights_2021_26}}) and Chernivtsi ({{sph_med_rights_2021_73}}), where trust is high | The survey and the budget measure different things |
| Trust mirrors cultural life | Cultural sphere by oblast | Not supported: cultural life in both is below the national median ({{sph_med_cult_2021_26}}, {{sph_med_cult_2021_73}}) | — |
| Small, close-knit communities | Hromada-level survey | Not testable: the survey is published by oblast | Needs hromada-level survey data |
| Regional history of institutions | Comparison across regions with similar finances | Not tested | Open |

Neither pattern can be explained with the open data available. Both are regional, both concern systems or relationships above the budget, and both need data that exist but are not published at the needed level.

### 15.6 What the region suggests for further work

Three questions follow, and none can be answered with current open data:
1. Does local trust or cohesion help hromadas with weak budgets sustain services under pressure? This needs hromada-level survey data.
2. Did hosting IDPs and relocated firms raise civilian income tax, and with it measured capacity, in western hromadas? Part II finds faster income-tax growth but little change in relative level (section 13, Table W4). Telling relocation apart needs hromada-level displacement and registration data.
3. What explains the four different light curves: grid topology, supply priorities or lighting policy? This needs grid and policy data by area, released with a security delay.

A fourth can be tested with the existing data: whether mountain and lowland hromadas differ within the region. The school register flags mountain schools and could supply a mountain indicator. [[PENDING: optional — request 30]]

# Synthesis: resilience in three spheres

Read together, the three parts suggest five points. Each is an association, not a cause.

1. **Exposure and local capacity are largely separate, and capacity does not buffer exposure.** Fiscal capacity is nearly unrelated to how exposed a hromada has been (section 6). Within oblasts, neither fiscal capacity nor any sphere softens the association between exposure and light (sections 7 and 11). Light recovery is largely shared at oblast level: grid conditions and oblast-wide decisions weigh more than any one hromada's budget (sections 7 and 8).
2. **Economic life: stronger where strikes later fell, hit hardest in the zone.** The pre-war tax base was stronger in the centre and east, where strikes concentrated. The relative economic fall since 2021 is concentrated in the zone near the front line and the border; elsewhere, being struck goes with no economic fall (section 10). Western hromadas gained income tax faster, but caught up in level only a little, mostly in Lviv (section 13).
3. **Rights life: autonomy goes with keeping light, and struck hromadas outside the zone spent more.** Hromadas less dependent on transfers before the war lost less light when the grid failed in summer 2024 — the clearest link between a sphere and functional resilience (section 11). Outside the zone, struck hromadas raised capital, social and education spending; inside it, transfers replaced own revenue (section 10). Trust in local administration, measured by oblast, follows neither the fiscal nor the rights measures (sections 14 and 15).
4. **Cultural life: local, tied to the budget, and hit in the zone.** What hromadas spend on culture and education varies from hromada to hromada more than between regions, moves with the economic sphere, and fell most in the zone (sections 9, 10 and 12). No robust link between cultural life and functional resilience was found (section 11).
5. **The balance: more even everywhere except the zone.** Hromada profiles across the three spheres became more balanced from 2021 to 2025. In the zone they became more one-sided: economic life collapsed, and transfers and capital programmes kept the rights index up (section 10.3). The Carpathian arc, the most unbalanced region in 2021, moved towards the national balance (section 9.4).

**Through the threefold frame.** The frame expects a hromada to be resilient when each sphere keeps its own principle working and none takes over the tasks of another. The data show where that fails most visibly: in the zone near the front line, where economic life and cultural provision fall and the state's transfers and programmes carry what local economic life no longer can. They also suggest where it holds: fiscal autonomy — a hromada governing its own budget rather than administering transfers — goes with keeping light when shared systems fail. The frame is normative and is not tested here; it orders the measures and the reading.

Two questions remain beyond what open data can answer. Whether relational resilience — trust, cohesion, belonging — helps hromadas with weak budgets hold together under pressure needs trust, cohesion and displacement data at hromada level (section 15.6). Whether cultural life outside the budget — associations, religious communities, the media — does so needs measures this study does not collect, partly by design (rule R7).

# Methods, limits and sources

The remaining sections set out the limitations of both parts, the rules applied to protect sensitive information and how to reproduce the results, followed by references and annexes.

## 16. Limitations

The limitations below are ordered by how much they constrain the paper's main claims.

### 16.1 Night lights are an indirect measure of recovery

Night-time light responds to physical damage and economic activity, but also to:
- blackout orders and curfews, as in March 2022;
- rolling outages scheduled across whole oblasts, as in summer 2024;
- deliberate reductions in street lighting since 2022, for security and energy saving.

The national plateau at about {{nl_plateau}} of pre-war light since late 2024 is therefore not "60 % destroyed". A large part of it is policy and grid conditions. We call the measures a *night-light recovery ratio* and a *night-light index*, and do not equate them with economic or social recovery.

Two further measurement issues apply:
- **Baseline choice.** The choice of baseline shifts levels by about {{nl_baseline_shift}} (section 5.2).
- **Monthly noise.** Monthly values are noisy, especially in small hromadas (section 8.1). Single-month values for individual hromadas should not be interpreted; publication of single-hromada values is limited to hromadas with at least [[CHECK: 30 lit pixels, as in the Carpathian dispatch — confirm as the general rule]] lit pixels.

### 16.2 Recovery is dominated by oblast-wide grid patterns

Oblast fixed effects explain most of the variation in the recovery ratio (R² {{r2_no_fe}} → {{r2_fe}}), and residuals remain spatially clustered (Moran's I = {{resid_moran_fe}} with fixed effects). This is consistent with recovery being governed by grid and supply decisions made above the hromada level. It follows that the within-oblast association between capacity and recovery is estimated from a limited share of the total variation, and that claims about the effect of local capacity must stay modest. We make no causal claim.

### 16.3 Ecological inference

All associations are measured between hromadas or between oblasts. They say nothing about individual households, businesses or officials. In particular, the oblast-level survey results (trust, cohesion, satisfaction) cannot be attributed to particular hromadas, and the juxtaposition of low fiscal capacity with high local trust in parts of the Carpathian region is a description at oblast level, not a hromada-level relationship.

### 16.4 Strike counts reflect reporting as well as attacks

VIINA records events reported in open sources. Reporting density is higher where media, local channels and population are denser, and lower near the front line and in occupied areas. Strike counts therefore partly measure visibility. Air-raid alert hours are recorded administratively and do not share this bias, which is one reason we report both. The stronger association of recovery with alert hours than with strike counts may partly reflect this difference in measurement quality.

### 16.5 Under-coverage of occupied and frontline areas

Indices are computed only for non-occupied hromadas ({{n_capacity}} for capacity, {{n_recovery}} for recovery). Budget, survey and displacement data are thin or absent for occupied and frontline areas. [[PENDING: breakdown of the {{n_hromadas_nonoccupied}} → {{n_recovery}} drop by reason and oblast — request 1]] The hromadas most affected by the war are the ones least represented in the models, which likely weakens the observed association between exposure and recovery.

### 16.6 Pre-war population denominators

Per-capita measures use JRC GHS-POP 2020 population. Displacement since 2022 has changed populations substantially, raising them in many western hromadas and lowering them near the front. Per-capita revenue and per-capita project counts are therefore biased: downward where population grew and upward where it fell. No reliable hromada-level wartime population series exists in open data.

### 16.7 Income tax is booked at the employer's address

Personal income tax is attributed to the hromada where the employer is registered, not where the employee lives. Hromadas hosting head offices, large enterprises or military units appear richer than their residents are. We flag {{n_garrison}} hromadas where military payroll made up at least a quarter of 2021 income tax. The flag is used only as a sensitivity check and is not published at hromada level (see section 17). In addition, from Q4 2023 military income tax was redirected from local budgets to the state budget; it had been {{military_pit_share_range}} of local income tax from Q2 2022. This creates a structural break in any budget series crossing that date.

### 16.8 Survey sampling and exclusions

reSCORE 2024 excludes Donetsk, Luhansk and Crimea, and its oblast estimates carry sampling error. [[PENDING: oblast sample sizes and confidence intervals for the trust differences — request 9]] Oblast differences smaller than their confidence intervals are not interpreted.

### 16.9 Registered vs present IDPs, and oblast-only data

IOM DTM data for Ukraine is available to us only at oblast level. Registration figures record where people registered, not where they currently live. The gap between registered and present IDPs (section 14) is itself a finding, but it means neither series is a reliable denominator. Because the displacement figures are oblast-level, they are collinear with oblast fixed effects and cannot enter the hromada models. [[PENDING: hromada-level DTM data requested from IOM]]

### 16.10 Inference: few oblast clusters and spatial dependence

The reported t-values use heteroskedasticity-robust (HC1) standard errors. These do not account for two features of the data:
- **Few clusters.** Hromadas in the same oblast share unobserved conditions, and there are only about two dozen oblasts.
- **Spatial dependence.** Residuals remain spatially clustered for several outcomes (Moran's I {{resid_moran_fe}} for the annual ratio, {{level_trough_moran}} for recent level and worst quarter).

The t-values for these outcomes are therefore optimistic. The outage-loss result, with low residual dependence (Moran's I {{outage_moran}}), is least affected. [[PENDING: wild-cluster bootstrap p-values and spatially robust errors — requests 4, 5]]

### 16.11 Composition of the capacity index

The 2025 capacity index includes civilian income-tax growth from 2021 to 2025, which is partly a consequence of the wartime economy and of recovery itself. This builds a degree of circularity into any model predicting recovery from 2025 capacity. We therefore report pre-war (2021) capacity as the primary specification, and the 2025 index as descriptive. Removing the income-tax component from the 2025 index lowers the within-oblast capacity coefficient to +{{cap_main_fe_no_pitgrowth}} and leaves the interaction at zero, so that component is not what drives the 2025 results. Part II separates the economic and rights components (section 9).

### 16.12 The sphere indices measure budgets and registers more than lives

Most sphere indicators are budget lines. They record what a hromada collects and spends, not the quality of its economic, political or cultural life. Education spending is largely the state education subvention and partly measures pupil numbers. Electoral contestation rests on one election, in 2020, before the invasion. Schools per 10,000 residents are higher where settlement is dispersed. Cultural life outside the budget — associations, religious communities, the media — is not measured; rule R7 limits what may be. The rights and cultural indices combine indicators that are only loosely correlated (section 9.2): they summarise several things, not one latent trait.

### 16.13 Index composition and change

The 2025 indices contain indicators that the 2021 indices lack. The economic 2025 index includes civilian income-tax growth, kept as agreed because it measures wartime dynamism; its change from 2021 is therefore partly a change of measure, most visibly in the Carpathian oblasts (section 13). Like-for-like indices are reported beside the full indices. All indices are percentile ranks: a change is a change of position among hromadas, not of absolute level, and one hromada's rise is another's fall.

### 16.14 Many tests

Part II rests on about two hundred models. Among so many, some p-values below 0.05 arise by chance. The findings reported in section 0 hold under the wild-cluster bootstrap by oblast and Conley spatial errors, and under at least one check (reliable light data, without the zone, or given the 2021 level). Single results near p = 0.05, such as the one nominal sphere × exposure interaction, are not treated as findings. The negative link between cultural life and recent light (section 11) is reported but treated as fragile.

### What would change the conclusions

The main conclusions would need revision in five cases:
- if hromada-level displacement data showed that population shifts account for the within-oblast capacity association, or for the fall of economic and cultural life in the zone;
- if hromada-level registration data showed a relocation of firms to the Carpathian oblasts that the income-tax measures miss;
- if the monthly trajectory metrics revealed local differences in recovery that the annual ratio hides;
- if a direct measure of grid restoration became available at hromada level.

The first is in progress (a request to IOM). The monthly trajectory metrics are done (section 8).


## 17. Protecting sensitive information

### 17.1 Principles

This study publishes analysis of an ongoing war. Four principles govern every map, table and file released:

1. **Aggregated open data only.** No personal data, and no names of officials, volunteers, contractors or residents.
2. **Nothing below the hromada level.** No output locates shelters, volunteers, military units or critical infrastructure at a finer scale than the hromada.
3. **No operational uplift.** Hromada-level outputs should not tell an attacker anything new, and in particular nothing about when and where the grid failed or recovered in the recent past.
4. **The raw inputs are already public.** VIINA events, Black Marble radiance and budget execution data can all be downloaded by anyone. The rules below therefore limit what this study *adds*: the joining, cleaning, timing and packaging that make patterns easier to read. They are not a claim that the underlying information is secret.

### 17.2 Rules

| Rule | Applies to | What is released | What is withheld |
|---|---|---|---|
| R1. Spatial floor | All outputs | Hromada, raion and oblast aggregates | Night-light rasters, DREAM project points, OSM infrastructure layers, interpolated surfaces as data |
| R2. Time lag | Monthly night-light index, trajectory metrics | Hromada monthly values up to 6 months before release | The most recent 12 months at hromada level; these are shown at oblast level only |
| R3. Frontline and border zone | Hromadas within 30 km of the front line or of the Russian or Belarusian border | Annual indices; time series aggregated to raion | Hromada-level monthly values and trajectory metrics |
| R4. Military finance | Budget tables, capacity index | Civilian income tax; the count of garrison hromadas and sensitivity results | The garrison flag and military income-tax share at hromada level |
| R5. Strike events | VIINA-derived outputs | Hromada counts; point maps at national extent only | Republished event points; point maps at regional or local zoom |
| R6. Personal data | DREAM and any record-level source | Project counts per hromada | Names, contractors, addresses, free-text fields |
| R7. Sensitive cultural data | Sphere indices, cultural and rights sources | Counts of institutions per hromada (schools); spending by function | Hromada-level maps or tables of religious affiliation, ethnicity or language; anything that could single out a community; locations of schools, libraries, places of worship and media offices |
| R8. Review | Every release | none | Release proceeds only after the checklist in Annex E is complete and one Ukrainian reader outside the project has reviewed all maps |

The front-line reference for R3 is [[PENDING: source and date of front-line geometry — request 31]].

KDE, IDW and kriging surfaces (Maps 07, 06, 05; Annex D) are published as national-extent images only. The underlying grids are not included in the data package.

### 17.3 Audit

**Table 13. Security audit of published outputs** [[PENDING: complete after request 13]]

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
| Maps 21–23 (sphere indices) | Hromada; raion in the 30 km zone | 2021, 2025 | R1, R3, R4, R7 | Published |
| Map 24 (threefold balance) | Hromada; raion in the 30 km zone | 2021, 2025 | R1, R3, R7 | Published |
| Tables S2–S9, W1–W8 | Oblast, group or national aggregates | Year | R1–R7 | Hromada cluster classes not published (R3) |
| Data package tables | | | R1–R6 | |
| Data package GeoPackages | | | R1, R3, R5 | |

## 18. Reproducibility

### 18.1 Environment

The analysis runs in Python 3.13 in a virtual environment, with package versions pinned in `requirements.txt`. Maps are produced in QGIS 3.40 from the project `viina/qgis/ukraine_strikes.qgz`. [[PENDING: operating system and QGIS plugin versions — request 25]]

### 18.2 Pipeline

`./run_all.sh` rebuilds all tables, indices, models and figures from cached source downloads. A full run takes about {{run_time}}. The repository is organised as:

- `viina/` — strike events, alerts, exposure measures, QGIS project and map pages;
- `resilience/` — budget, night-light, population, survey and displacement processing; indices; tidy tables;
- `publication/` — this paper, the policy brief, the Dispatch essay, the data package documentation and the build script.

The three-sphere analysis of Part II runs in `resilience/`: functional spending (`31_`), elections (`33_`), schools (`34_`), sphere indices (`32_`), map layers (`35_`), associations and clusters (`36_`), the "why there?" tests (`37_`) and the paper tables S2–S9 with their quoted numbers (`38_`, which writes `publication/numbers_spheres.yaml`). Tables S2–S9 are built from published tables only and can be reproduced without the local data.

### 18.3 Data availability

The data package on Zenodo ({{zenodo_doi}}) contains:
- tidy tables for all indices and model inputs;
- GeoPackages of hromada and oblast boundaries with attributes;
- the data dictionary (Annex A) and source catalogue (Annex B).

It is subject to the rules in section 17.

Not every input can be redistributed:
- **Raw source downloads** are not included. Fetch scripts with recorded access dates retrieve them.
- **IOM DTM data** is retrieved through the IOM API under IOM's terms of use. The package contains the fetch script and, where the terms allow, oblast aggregates only. [[PENDING: confirm DTM redistribution terms — request 23]]
- **Night-light rasters** are withheld under rule R1 and can be downloaded directly from NASA.

### 18.4 Versions

This paper describes release {{release_version}} (commit {{commit_hash}}, {{release_date}}). Later releases will be listed with their changes on the Zenodo record.

### 18.5 Licences

- Text and figures: CC BY 4.0.
- Data package: ODbL 1.0. It contains databases derived from VIINA and OpenStreetMap, which are themselves licensed under ODbL.
- Code: MIT.

Every map and table credits its sources. Full attribution statements are in Annex F.

### 18.6 Suggested citation

Garand, M. ({{release_year}}). *Hromada resilience under strikes in Ukraine, 2022–2026: An associational analysis with open data* (Working paper {{release_version}}). SocArXiv. {{socarxiv_doi}}

Data: Garand, M. ({{release_year}}). *Ukraine hromada strikes and resilience dataset* ({{release_version}}) [Data set]. Zenodo. {{zenodo_doi}}

## References

[[CHECK: verify every entry and add methods references used in the pipeline]]

- Anselin, L. (1995). Local indicators of spatial association — LISA. *Geographical Analysis*, 27(2), 93–115.
- Benjamini, Y., & Hochberg, Y. (1995). Controlling the false discovery rate: A practical and powerful approach to multiple testing. *Journal of the Royal Statistical Society, Series B*, 57(1), 289–300.
- Cameron, A. C., Gelbach, J. B., & Miller, D. L. (2008). Bootstrap-based improvements for inference with clustered errors. *Review of Economics and Statistics*, 90(3), 414–427.
- Conley, T. G. (1999). GMM estimation with cross sectional dependence. *Journal of Econometrics*, 92(1), 1–45.
- Egozcue, J. J., Pawlowsky-Glahn, V., Mateu-Figueras, G., & Barceló-Vidal, C. (2003). Isometric logratio transformations for compositional data analysis. *Mathematical Geology*, 35(3), 279–300.
- Schöley, J. (2021). The centered ternary balance scheme: A technique to visualize surfaces of unbalanced three-part compositions. *Demographic Research*, 44(19), 443–458.
- Webb, M. D. (2023). Reworking wild bootstrap-based inference for clustered errors. *Canadian Journal of Economics*, 56(3), 839–858.
- Steiner, R. (1919). *Die Kernpunkte der sozialen Frage in den Lebensnotwendigkeiten der Gegenwart und Zukunft*. Stuttgart: Greifenverlag. English: *Towards Social Renewal*.
- Getis, A., & Ord, J. K. (1992). The analysis of spatial association by use of distance statistics. *Geographical Analysis*, 24(3), 189–206.
- Román, M. O., et al. (2018). NASA's Black Marble nighttime lights product suite. *Remote Sensing of Environment*, 210, 113–143.
- Schiavina, M., Freire, S., Carioli, A., & MacManus, K. (2023). *GHS-POP R2023A — GHS population grid multitemporal (1975–2030)*. European Commission, Joint Research Centre.
- Zhukov, Y. M. (2023). Near-real time analysis of war and economic activity during Russia's invasion of Ukraine. *Journal of Comparative Economics*, 51(4), 1232–1243.
- OCHA. *Ukraine — Subnational administrative boundaries (COD-AB)*. Humanitarian Data Exchange. {{version_codab}}
- IOM Displacement Tracking Matrix. *Ukraine data, API v3*. Accessed {{access_dtm}}.
- SeeD & UNDP. *SCORE / reSCORE Ukraine 2021 and 2024*. Accessed {{access_rescore}}.
- Ministry of Finance of Ukraine. *openbudget.gov.ua — local budget execution*. Accessed {{access_openbudget}}.
- DREAM — Digital Restoration Ecosystem for Accountable Management. Accessed {{access_dream}}.
- Central Election Commission of Ukraine. *Місцеві вибори 2020* (election 695), open data. [[CHECK: access date]]
- Ministry of Education and Science of Ukraine. *ЄДЕБО — Реєстр суб'єктів освітньої діяльності*; form ЗНЗ-1, data.gov.ua. [[CHECK: access dates]]

## Annexes

| Annex | Content | Source file |
|---|---|---|
| A | Data dictionary | `resilience/tidy/data_dictionary.csv` |
| B | Source catalogue, with versions and access dates | `resilience/tidy/source_catalogue.md` |
| C | Full model output: M1–M7, sensitivity, spatial models, trajectory models; sphere models and "why there?" tests | [[PENDING: requests 4, 5, 7, 12]]; `resilience/tidy/sphere_associations.csv`, `why_there_models.csv`, `why_there_profiles.csv`, `sphere_lisa_summary.csv` |
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
- **Sphere index** — the mean percentile rank of a sphere's indicators among non-occupied hromadas, for economic, rights or cultural life, in 2021 or 2025 (section 9).
- **Like-for-like index** — a sphere index built only from the indicators measured in both 2021 and 2025, used to compare the two years (section 9.2).
- **Zone** — the hromadas within 30 km of the front line or of the Russian or Belarusian border (rule R3); {{n_zone}} non-occupied hromadas.
- **Threefold balance, imbalance, lean** — how a hromada's three sphere indices weigh against each other; imbalance is the distance from the national average composition, a lean the direction of the departure (section 9.4).
- **LISA** — local indicators of spatial association: hromadas whose values resemble those of their neighbours (high–high, low–low) or differ from them.
- **Wild-cluster bootstrap** — a resampling test that allows for errors shared within oblasts when there are few oblasts; used for all p-values in Parts I and II.
- **Conley errors** — standard errors that allow for correlation between nearby hromadas, up to a distance cut-off (50 and 100 km).
- **Gi\*** — the Getis-Ord local statistic used to identify spatial clusters of high or low values (hot spots and cold spots).
