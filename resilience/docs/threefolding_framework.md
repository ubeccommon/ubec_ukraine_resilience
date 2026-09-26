# Resilience in the light of social threefolding — framework proposal

Status: 26 Sep 2026. Decided: threefolding enters the paper now as its frame (Option A, paper v0.4, section 1.4);
the three-sphere analysis with new data follows as the next version (Option B). The municipal budget is split
between spheres (section 2). Nothing in section 3–4 is computed yet.

## 1. The frame

Social threefolding (Rudolf Steiner, *Die Kernpunkte der sozialen Frage*, 1919; English *Towards
Social Renewal*) distinguishes three spheres of social life, each with its own principle:

| Sphere | Principle | Domain |
|---|---|---|
| Rights (political) life | equality, democracy | law, public administration, public finance, representation |
| Cultural (spiritual) life | freedom | art, science, religion, education, the media |
| Economic life | uncoerced cooperation in freely contractual relations | production, trade, work, associations of producers and consumers |

**Resilience, read through this frame,** is the ability of each sphere to keep its own principle
working under attack — equal access and democratic self-government, free cultural and educational
life, cooperative economic life — and the balance between the three: no sphere taking over the
function of another.

The theory is normative. Here it serves as an **interpretive and organising frame**: it decides which
indicators are gathered and how results are grouped. The analysis stays associational, as in the
current paper. It does not test the theory.

## 2. Where the current measures sit

**The municipal budget is split between two spheres** (decision of 26 Sep 2026): the tax base belongs to
economic life, and the autonomy and spending choices of local self-government belong to rights life.
The four components of the current fiscal capacity index divide evenly:

| Capacity component | Sphere |
|---|---|
| Own revenue per resident | Economic (tax base) |
| Civilian income-tax growth | Economic (tax base) |
| Transfer dependency (inverse) | Rights (autonomy) |
| Capital-expenditure share | Rights (spending choices) |

Option B builds two sub-indices from these pairs and reports them separately.

| Measure (existing) | Level | Sphere | Note |
|---|---|---|---|
| Fiscal capacity index: own revenue, income-tax growth / transfer dependency, capital spending | hromada | Economic / Rights | split as above |
| Civilian income tax growth, relative income tax | hromada | Economic | where work and earnings are located |
| Night-time light (recovery, level, outage loss) | hromada | Economic (+ infrastructure) | activity and services; grid is shared infrastructure |
| ЄДРПОУ legal entities and sole proprietors per 1,000 | hromada, 10 oblasts | Economic | partial coverage |
| DREAM reconstruction projects per 10,000 | hromada | Rights | public investment planning and transparency |
| reSCORE: trust in local administration, civic engagement, locality satisfaction | oblast | Rights | |
| reSCORE: belonging, mental wellbeing | oblast | Cultural | |
| reSCORE: community cohesion | oblast | Cultural / economic | cohesion straddles spheres; decide |
| reSCORE: economic security | oblast | Economic | |
| IOM DTM displacement | oblast | across spheres | reception involves all three |

**Gap:** the cultural sphere has no hromada-level measure at all, and economic *cooperation* (as
distinct from activity) is not measured.

## 3. Candidate new data

Counts or shares per hromada only; no site locations (rule R1). Schools, libraries and religious
buildings are sensitive targets and are never mapped as points.

| Sphere | Indicator | Source | Level | Effort | To verify |
|---|---|---|---|---|---|
| Cultural | Education and culture spending, share of expenditure (functional classification 09 education, 08 culture and sport) | openbudget.gov.ua API, same source as `03_openbudget.py` (`classificationType=FUNCTIONAL`) | hromada, 2021–2026 | low | one test pull |
| Cultural | Schools and pupils per 1,000; schools operating in person / online | ІСУО / Ministry of Education open data | hromada | medium | licence, war-time updates |
| Cultural | Damaged or destroyed education facilities (count) | saveschools.in.ua (Ministry of Education) | hromada | medium | terms, R1 |
| Cultural | Religious communities per 10,000 | register of religious organisations (data.gov.ua) | hromada via address | medium | geocoding quality |
| Cultural | Libraries and cultural institutions per 10,000 | Ministry of Culture registers | hromada | medium | availability |
| Cultural | Local media outlets | National Council register of media entities | hromada via address | medium | availability |
| Rights | Local election turnout 2020; council composition (gender share) | Central Election Commission | hromada | low–medium | format |
| Rights | Social protection spending share (functional 10); administration share (01) | openbudget.gov.ua (functional) | hromada | low | with the cultural pull |
| Rights | Administrative service centres (ЦНАП) present | Ministry of Digital Transformation / Diia | hromada | low | availability |
| Economic | Cooperatives and associations (legal forms) per 10,000 | ЄДР bulk open data (data.gov.ua) | hromada via address | medium–high | file size, address to KATOTTG |
| Economic | Housing and communal economy spending share (functional 06) | openbudget.gov.ua | hromada | low | with the cultural pull |

The functional-classification pull is the natural first step: one source already in the pipeline
gives hromada-level measures for all three spheres.

## 4. Spatial analysis design

1. **Sphere indices per hromada** — mean percentile rank of the indicators in each sphere, built like
   the capacity index; oblast-level survey indicators kept separate.
2. **Maps** — one choropleth per sphere, and a **threefold balance map**: each hromada coloured by the
   relative weight of its three sphere indices (ternary colour scheme), under rules R1–R3.
3. **Associations** —
   - each sphere index against exposure (strikes, alert hours), with oblast fixed effects and spatial
     diagnostics, as in Part I;
   - each sphere index against functional resilience (outage loss, recovery), within oblasts;
   - between-sphere associations: do the spheres move together, or does one compensate for another?
4. **Clusters** — LISA on the sphere indices and on the balance, national and Carpathian.
5. **Carpathian reading** — the four oblasts by sphere, including the survey indicators.

## 5. What it means for the paper

- **Option A — lens now, data later.** Keep the two-part v0.3 structure and results; add threefolding
  to the introduction (framework, Table of spheres) and re-read the synthesis through it. Label
  existing measures by sphere. No new data; fits the v1.2 release.
- **Option B — three-sphere paper.** Restructure around the three spheres (rights, cultural,
  economic), with the new data. A larger piece of work: new pulls on the data machine, new scripts
  (`31_functional_spending.py`, …), new maps, and review of every indicator against R1–R6.
- **Recommended:** A for the v1.2 release, B as the next version, starting with the functional
  spending pull.
