"""Write qgis/meta.json with the data dates used in the map captions (read by build_qgis_project.py).
Run after build_unit_stats.py and build_surfaces.py (needs qgis/control_latest.pkl)."""
import json
from pathlib import Path
import pandas as pd

OUT = Path("qgis")
fmt = lambda t: f"{pd.Timestamp(t).day} {pd.Timestamp(t).strftime('%b %Y')}"

st = pd.read_pickle(OUT / "strike_events_filtered.pkl")
END = pd.Timestamp(st["date"].max())
START12 = END - pd.Timedelta(days=365)

a = pd.read_csv("../air_raid/official_data_en.csv", usecols=["started_at", "finished_at"])
s = pd.to_datetime(a["started_at"], utc=True); e = pd.to_datetime(a["finished_at"], utc=True)
ok = e > s
A_END = min(e[ok].max(), (END + pd.Timedelta(days=1)).tz_localize("UTC"))
A_START12 = A_END - pd.Timedelta(days=365)

ctrl = pd.read_pickle(OUT / "control_latest.pkl")
CDATE = pd.to_datetime(str(int(ctrl["date"].max())), format="%Y%m%d")

meta = {"event_first": fmt(st["date"].min()), "event_end": fmt(END), "event_w12_start": fmt(START12),
        "alert_start": fmt(s[ok].min()), "alert_end": fmt(A_END - pd.Timedelta(seconds=1)), "alert_w12_start": fmt(A_START12),
        "control_date": fmt(CDATE)}
(OUT / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
print(json.dumps(meta, indent=2, ensure_ascii=False))
