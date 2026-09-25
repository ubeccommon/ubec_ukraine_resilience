import pandas as pd, zipfile, glob
frames=[]
for z in sorted(glob.glob("event_1pd_latest_*.zip")):
    with zipfile.ZipFile(z) as zf:
        frames.append(pd.read_csv(zf.open([n for n in zf.namelist() if n.endswith(".csv")][0]), low_memory=False))
ev = pd.concat(frames, ignore_index=True)
cols = ["t_airstrike_b","t_uav_b","t_artillery_b","t_aad_b"]
any_strike = ev[cols].fillna(0).sum(axis=1) > 0
print("strike-type events total:", any_strike.sum())
print("a_rus_init_b values among them:\n", ev.loc[any_strike,"a_rus_init_b"].value_counts(dropna=False))
print("a_rus_b values among them:\n", ev.loc[any_strike,"a_rus_b"].value_counts(dropna=False))
