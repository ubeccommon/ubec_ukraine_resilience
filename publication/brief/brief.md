---
title: "Local finances help in outages, not against heavier attacks"
subtitle: "What open data show about strikes, local capacity and night-time light in Ukraine's hromadas, 2022–2026"
author: "Michel Garand, UBEC Platform"
version: "Policy brief v0.2 — internal draft (trajectory results added)"
date: "September 2026"
licence: "CC BY 4.0"
---

<!--
Conventions as in paper.md: {{key}} from numbers.yaml; [[PENDING: …]] blocks release.
Target: 3 pages A4 with two figures. Audience: hromada practitioners, donors, recovery programmes.
-->

## In brief

- **Local fiscal strength and exposure to attacks are almost unrelated.** Hromadas with strong and weak budgets have been attacked at similar levels.
- **Night-time light has plateaued at about {{nl_plateau}} of pre-war levels, and follows the regional grid.** Oblast differences account for most of the variation.
- **When the grid failed in 2024, hromadas with stronger finances kept relatively more of their light.** But this advantage does not grow where attacks are heavier, and it was absent in the acute phase of 2022.

## Why this matters

Recovery programmes increasingly work through hromadas. A common assumption is that hromadas with stronger own revenue and lower dependence on transfers are better able to absorb shocks. If that were true, strengthening local finances would double as protection against attacks.

This brief tests that assumption with open data for {{n_hromadas_nonoccupied}} non-occupied hromadas, from 2021 to {{nl_panel_end}}. It combines:
- recorded strikes and air-raid alert hours;
- local budgets, quarterly;
- satellite night-time light, monthly, as a proxy for power supply and activity;
- oblast-level survey and displacement data.

## What we found

**1. Capacity and exposure are nearly independent.**
The correlation between the fiscal capacity index and exposure is only ρ = {{rho_cap_exp_min}} to {{rho_cap_exp_max}}. In every oblast there are hromadas with weak finances under heavy pressure, and strong ones that have been spared. Budget indicators alone say little about where attacks have hit hardest.

**2. Light is lowest where alerts have lasted longest.**
Alert hours are the strongest predictor of a hromada's recent light level (ρ = {{rho_level_alerts}}), stronger than recorded strike counts.

**3. Light has stopped recovering, and the pattern is regional.**
- The median hromada fell to {{nl_march2022}} of its pre-war light in March 2022 and recovered to {{nl_h2_2023}} by late 2023.
- It dropped to {{nl_trough_2024_median}} in the outages of summer 2024.
- Since late 2024 it has stayed at about {{nl_plateau}} with no upward trend.
- Knowing a hromada's oblast explains most of the variation in its light.

This is consistent with light being driven by the electricity grid, outage schedules and street-lighting policy, all decided above the hromada level. The plateau does not mean that 60 % of the country is destroyed.

**4. Stronger finances went with smaller losses when the grid failed.**
During the summer-2024 outages, hromadas with higher pre-war capacity kept relatively more of their own light than others in the same oblast (+{{outage_cap_prewar}} on a standardised scale). This is the most robust capacity result. The data cannot say why: backup power, better-maintained networks or a different local economy are all possible.

**5. But stronger finances did not offset heavier attacks, and did not help in 2022.**
- Within an oblast, the capacity advantage is the same whether a hromada was heavily or lightly exposed.
- For the recent trend it is even slightly smaller where exposure is high.
- In the acute phase of 2022, the dark came to strong and weak hromadas alike.

**6. Social context differs sharply, even between neighbouring oblasts.**
- Trust in local administration is well above the national average in Ivano-Frankivsk (+{{trust_diff_if}} on a 0–10 scale) and Chernivtsi (+{{trust_diff_cv}}), but far below it in Zakarpattia ({{trust_diff_zk}}), the brightest oblast of the region.
- Ivano-Frankivsk combines low fiscal capacity with the country's highest community cohesion.

**7. Registered displacement is a poor guide to where displaced people are.**
In the Carpathian oblasts, registered IDPs exceed those actually present by {{idp_west_gap}} (Zakarpattia: {{idp_reg_zk}} registered vs {{idp_present_zk}} present per 1,000 residents). In the centre and east the gap runs the other way (Dnipropetrovsk: {{idp_reg_dp}} vs {{idp_present_dp}}).

**Figure 1.** Alert hours × fiscal capacity, by hromada (Map 14, bivariate 3×3). [[PENDING: export at brief size — request 14]]

## What this means for recovery programmes

**Target on exposure and capacity together.**
The two are nearly independent, so a single ranking by budget strength misses many heavily exposed hromadas. The combined classes in Figure 1 identify hromadas with both high exposure and low capacity. There are {{n_hilo_alerts}} such hromadas nationally on alert hours, most of them in Sumy, Kharkiv and Kherson oblasts.

**Treat energy resilience first as a system-level task.**
Light tracks the regional grid far more than local finances. Local budgets cannot substitute for investment in generation, transmission and distribution.

**Close the outage gap for weaker hromadas.**
Hromadas with stronger finances lost less light when the grid failed. If the reason is backup power or better-kept local networks, weaker hromadas are the ones that most need support for these. Programmes that fund them should record what they install, so that the effect can be tested.

**Do not expect local capacity to offset heavier attacks.**
The capacity advantage does not grow with exposure, and it did not exist in the acute phase. Capacity-building is justified by service delivery, accountability and long-term recovery. For hromadas under the heaviest pressure, it is not a substitute for direct support.

**Plan services on where people are, not where they registered.**
In western oblasts, registration overstates the displaced population. In the centre and east it understates it. Service planning for IDPs should use presence estimates, or local counts, alongside the register.

**Add social data to capacity assessments.**
Fiscal indicators alone rank much of the Carpathian region as weak. Survey evidence suggests some of these communities have high trust and cohesion, which budgets do not measure. Zakarpattia shows the pattern cannot be assumed across a whole region.

**Publish the missing data.**
Three open datasets would sharpen all of these conclusions:
- hromada-level displacement figures;
- a current population estimate by hromada;
- a record of grid restoration and backup capacity by area, released with a security delay.

**Figure 2.** Oblast context: trust, cohesion and IDPs per 1,000 residents (Map 18). [[PENDING: export at brief size — request 14]]

## What this evidence cannot tell you

- **Night-time light is not the same as recovery.** It also falls with blackout orders, outage schedules and reduced street lighting.
- **Recorded strikes depend partly on reporting,** which is thinner near the front.
- **The analysis covers non-occupied hromadas only,** and frontline areas are under-represented.
- **All findings compare places, not people.** Oblast survey results cannot be applied to individual hromadas.
- **The findings are associations, not causes.** In particular, the outage result does not show what stronger hromadas did differently.

## Data, methods and security

The analysis uses only aggregated open data:
- VIINA 2.0 strike events;
- air-raid alert records;
- openbudget.gov.ua;
- NASA Black Marble night lights;
- JRC GHS-POP population;
- DREAM reconstruction projects;
- SeeD–UNDP reSCORE 2024;
- IOM DTM;
- OCHA administrative boundaries.

Models compare hromadas with and without accounting for their oblast (fixed effects).

No information is published below the hromada level. Recent monthly light is released only with a delay and at oblast level. Military finance data is not published by hromada.

**Full working paper:** {{socarxiv_doi}} · **Open data and code:** {{zenodo_doi}}
**Contact:** [[PENDING: contact address]]

*Data: VIINA 2.0 (ODbL); air-raid alert records, Klimenko (MIT); OCHA COD-AB (CC BY-IGO); openbudget.gov.ua; NASA Black Marble; JRC GHS-POP; DREAM; SeeD–UNDP reSCORE; IOM DTM. Text and figures CC BY 4.0.*
