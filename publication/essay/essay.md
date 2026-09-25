---
title: "The Grid Is Not the Village"
subtitle: "What satellite light, budgets and air-raid sirens say, and don't say, about recovery in Ukraine's hromadas"
author: "Michel Garand"
series: "Soil and Peace — Carpathian Dispatch 2026"
version: "Essay v0.2 — draft for style review (trajectory results added)"
date: "September 2026"
licence: "CC BY 4.0"
---

<!--
Conventions as in paper.md: {{key}} from numbers.yaml; [[PENDING: …]] blocks release.
[[FIELD NOTE: …]] = your own observation, to be written by you. Nothing personal has been invented here.
Security for field notes: no place below hromada level, no dates or times of recent outages,
no shelters, units, volunteers or infrastructure.
Voice: first-person frame (opening, closing), plain explanatory voice for the data sections.
Target ~2,500 words, 4 maps + 1 chart.
-->

[[FIELD NOTE: Opening scene, 150–200 words. An evening in the mountains when the power goes, or comes back: what you hear, what people do, how the village adjusts. Keep it at the level of "the village", "the valley" or the hromada name, with no date.]]

Moments like that raise a question I have carried since arriving in the Carpathians. When the lights come back, whose doing is it? Is it the village, the hromada with its small budget and its council, or something much larger and further away?

Over the past year I have tried to answer that question with numbers. This dispatch reports what I found. The honest answer is less comforting than I hoped, and more useful.

## A country of hromadas

Ukraine went into this war only a few years after one of the largest local-government reforms in Europe. Between 2015 and 2020, thousands of village and town councils were merged into hromadas: communities with their own elected councils, their own budgets and a share of the income tax paid by those who work there. When the full-scale invasion came, these hromadas became the front desk of the state. They opened shelters, housed displaced families, kept water and heating running, and organised the thousand small tasks that let life continue.

It is natural to think that a hromada with more money of its own copes better. A hromada that raises more of its own revenue, depends less on transfers from Kyiv and invests in its own infrastructure ought to be more resilient. It ought to lose less when it is hit and recover faster afterwards. Many recovery programmes are built on that intuition.

I wanted to know whether the evidence supports it.

## Seeing a war from orbit

No one can visit {{n_hromadas_total}} communities, so I used open data. Everything below comes from sources anyone can download:

- **Strikes.** A research database of attacks reported in open sources (VIINA), assigned to the hromada where they were recorded.
- **Air-raid alerts.** The official record of how many hours each hromada has spent under alert. Unlike strike reports, this does not depend on whether a journalist was nearby.
- **Local budgets.** Published revenue and spending of every hromada from 2021, the last full year before the invasion, to 2025.
- **Night-time light.** NASA's Black Marble satellite product, which measures how much light each patch of the country gives off at night, month by month.

Night light is the key to what follows, and also its weakest point. Where towns are damaged, power is cut or businesses close, the lights go down. Where life returns, they come back. By comparing how many places were lit in 2024 and in winter 2024–25 with the same periods before the war, I built a simple measure: a *night-light recovery ratio* for each hromada.

A dark window, though, is not always a broken one. Since 2022, Ukrainians have switched off street lights for safety, saved power during rolling blackouts, and lived through curfews. Some of the lost light is caution, not damage. I come back to this below, because it shapes everything the data can say.

**Map 1.** Strike and alert exposure by hromada, 2022–{{nl_panel_end_year}}. [[PENDING: Map 01 at essay size]]

## Money and missiles do not line up

The first result surprised me. I expected wealthier hromadas, the cities and industrial towns, to be hit more often, and poorer rural ones to be spared. There is a slight tendency in that direction, but it is very weak. The correlation between a hromada's fiscal capacity and its exposure to strikes or alerts is between {{rho_cap_exp_min}} and {{rho_cap_exp_max}}. In statistical terms, that is close to nothing.

Put simply, the war does not choose its targets by the size of the local budget. In every oblast there are hromadas with thin finances that have endured months of sirens, and well-off hromadas that have been largely spared.

This matters for anyone deciding where help should go. A list of "weak" hromadas drawn from budget data alone will miss many of the places under the heaviest pressure. The map below crosses the two measures. The hromadas that deserve the most attention are those that are both heavily exposed and financially weak.

**Map 2.** Alert hours and fiscal capacity combined (3×3 classes). [[PENDING: Map 14 at essay size]]

## The grid decides

The second result is the one that changed how I think about recovery.

Hromadas that have endured more alerts and strikes have recovered less of their night-time light. That is expected. The association is stronger for alert hours than for recorded strikes, probably because alerts are measured more completely.

What I did not expect was how much of the recovery is decided above the hromada level. If you know only which oblast a hromada is in, you can explain most of the variation in its night-light recovery. The share of variation explained rises from {{r2_no_fe}} to {{r2_fe}} once the oblast is known. Recovery also clusters strongly on the map: neighbouring hromadas rise and fall together.

The most likely explanation is the electricity system. When attacks destroy power stations and substations, the resulting outages are scheduled across whole regions. When repairs come, they restore whole regions. A hromada council can buy generators and keep a boiler house running. It cannot rebuild a transmission line or decide the outage schedule for the oblast.

The monthly data make this visible. In March 2022, under blackout orders and curfews, the typical hromada gave off only {{nl_march2022}} of its pre-war light. By late 2023 it had climbed back to about {{nl_h2_2023}}. Then, in June and July 2024, during the rolling blackouts that followed attacks on generating capacity, it fell to {{nl_trough_2024_median}}. Since late 2024 it has stayed at about {{nl_plateau}}, with no sign of rising. That plateau does not mean that 60 % of the country is destroyed. It is as much about darkened streets, saved power and a strained grid as about damage.

**Chart 1.** Monthly night-time light, national median, 2021–{{nl_panel_end_year}}. [[PENDING: export — request 14]]

## The buffer that wasn't

The central question was whether stronger hromadas lose less when they are hit harder. At first, the data seemed to say yes. Across the whole country, higher-capacity hromadas lost less light at high exposure than lower-capacity ones did. On its own, that result would have made a hopeful headline.

It does not survive a fair comparison.

Think of two farmers in different valleys, one with better soil and more rain. If the first harvests more, you learn little about whether their methods are better. The weather and the soil did most of the work. To judge the farmers, you have to compare each one with the neighbours who share their valley.

The same applies here. Oblasts differ in their distance from the front, the state of their grid and their economy. When each hromada is compared only with others in the same oblast, the apparent buffering disappears. In every version of the model I tested, the effect was approximately zero. Within an oblast, stronger local finances do not soften the loss associated with heavier attacks.

What remains is more specific. When the grid failed in the summer of 2024, hromadas with stronger finances *before* the invasion kept relatively more of their own light than their neighbours in the same oblast. That is the most solid result in the study. It may reflect backup generators, better-kept local networks or simply a different local economy; the data cannot say which. And the advantage does not grow where attacks are heavier. In the first, worst months of 2022, it did not exist at all: the dark came to strong and weak hromadas alike.

I want to state this plainly, because it is easy to lose in a hopeful story. **The data do not show that local financial strength offsets heavier attacks.** That is not an argument against strengthening hromadas. Good local government matters for many reasons: services, accountability, the long work of rebuilding. But it should not be promised as a shield.

## What the budget cannot see

Here in the Carpathians, the numbers tell a particular story.

The region has been further from the front than most of the country. Over the last year a typical Carpathian hromada spent about {{carp_alert_hours_12m}} hours under air-raid alert, against about {{nat_alert_hours_12m}} nationally, and fewer than one in ten has recorded a strike since 2022. Apart from Lviv oblast, many of its hromadas have small budgets and depend on transfers for more than half their income. By fiscal measures alone, much of the region looks weak.

A national survey, reSCORE 2024, run by SeeD and UNDP with {{rescore_n}} respondents, tells a different story, at least in part. In Ivano-Frankivsk oblast, trust in local administration is {{trust_diff_if}} points above the national average on a 0–10 scale. The oblast also records the highest community cohesion and the highest satisfaction with local life anywhere in the country. Chernivtsi is not far behind (+{{trust_diff_cv}}).

[[FIELD NOTE: 100–150 words. What you see of this locally: how people speak of the hromada, the council, mutual help. Keep it general, with no names of officials or volunteers.]]

The pattern is not regional destiny, though. Next door, in Zakarpattia, trust in local administration is {{trust_diff_zk}} points *below* the national average. [[PENDING: Lviv — request 15]] Whatever produces high trust in some Carpathian communities, it is not simply mountains, culture or distance from the war.

I should be careful here, because the two kinds of data sit at different levels. Budgets are measured for each hromada, while the survey gives averages for each oblast. I cannot say that the hromadas with the smallest budgets are the ones whose residents trust their councils most. What I can say is that a region which looks weak on paper appears, in at least two of its oblasts, to hold something that budgets do not record. Anyone judging where local institutions can carry the work of recovery should look at both.

The survey offers one more lesson from the other end of the country. In Kherson, which lived through occupation and still lives under constant fire, people rate their local conditions the lowest in Ukraine and their sense of belonging the highest. Hard conditions do not loosen people's attachment to their place.

**Map 3.** Carpathian hromadas: capacity, recovery and exposure within the region. [[PENDING: Map 17 at essay size]]

## Where the people are

The Carpathians have been a place of refuge since 2022, and here too the official numbers mislead.

Ukraine keeps a register of internally displaced people, and the International Organization for Migration also surveys how many are actually living in each oblast. In the west, the register shows far more people than the survey finds. In Zakarpattia, the gap is {{idp_reg_zk}} registered against {{idp_present_zk}} present per 1,000 residents. In the centre and east it runs the other way: in Dnipropetrovsk, {{idp_reg_dp}} registered against {{idp_present_dp}} present.

A likely reading is that many people registered in the west in the first months of the war, when it was the safest destination, then moved on or went home without deregistering. Meanwhile many people now living in the centre and east are registered somewhere else. The data cannot prove this. But anyone planning housing, schools or clinics should know that the register is a poor map of where displaced people actually are.

The register is also shifting. Since early 2023, registered IDPs in the Carpathian oblasts have fallen by {{idp_carp_decline}}. In Kherson they have nearly doubled, and in Sumy they have risen by {{idp_rise_su}}, as attacks and evacuations near the front have intensified. The movement is now towards the edges of the war, not away from it.

**Map 4.** Oblast context: trust, cohesion and displaced people per 1,000 residents. [[PENDING: Map 18 at essay size]]

## What the data cannot say

A few cautions belong in any honest account of this work.

- **Night light is a proxy.** It measures electricity and activity, not wellbeing, and it falls with caution as well as with damage.
- **Strike records depend on reporting.** They are thinner near the front line, where the war is hardest, than in cities with active local media.
- **The analysis covers only non-occupied hromadas.** The worst-affected places are the least represented.
- **Everything here compares places, not people.** Nothing in it describes any individual's experience of the war.
- **These are associations, not proof of cause.**

I also made deliberate choices about what not to publish:
- Nothing is shown below the level of the hromada.
- Recent month-by-month patterns of light are released only for whole oblasts and only after a delay.
- Data on military payrolls is left out entirely.

The raw sources are public, but a clean, joined, mapped dataset makes patterns easier to read, and some patterns should not be made easier to read while the war goes on.

## Back to the village

[[FIELD NOTE: Closing scene, 150–200 words. Return to the opening image. What the finding means from where you sit: the lights come back because of people and systems far beyond the valley, and what the village does in the dark still matters.]]

If the data teach one thing, it is humility about scale. The light that returns to a mountain village at night is mostly the work of a system far larger than the village: engineers, substations, transmission lines, and decisions made in regional control rooms. No hromada budget can buy that.

But the numbers also point at something they cannot measure: the trust, cohesion and belonging that let a community hold together while it waits. That, too, is part of the soil in which peace has to grow.

---

*This essay draws on a working paper and an open dataset published alongside it.*
**Working paper:** {{socarxiv_doi}} · **Data and code:** {{zenodo_doi}}

*Data: VIINA (ODbL); air-raid alert records (MIT); OCHA COD-AB (CC BY-IGO); openbudget.gov.ua; NASA Black Marble; JRC GHS-POP; SeeD–UNDP reSCORE; IOM DTM. Text and maps CC BY 4.0.*
