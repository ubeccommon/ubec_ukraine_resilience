"""Fixed end of the air-raid alert series, shared by build_unit_stats.py and write_meta.py.

Ukraine replaced the single air-raid alert with two levels, yellow (drone threat) and red (massive
drone, missile or combined threat), under Cabinet Resolution No. 1092 of 4 Sep 2026, rolled out
region by region from 6 Sep 2026. Alert territory and siren rules changed at the same time, so the
old single-alert series is not comparable after the switch, and yellow + red is not a substitute.

All alert windows therefore end at ALERT_CUTOFF: alert_h_12m = 1 Sep 2025 .. 31 Aug 2026 (UTC),
alert_h_all = 15 Mar 2022 .. 31 Aug 2026. Post-break data go into a separate series, never spliced."""
import pandas as pd

ALERT_CUTOFF = pd.Timestamp("2026-09-01 00:00", tz="UTC")
