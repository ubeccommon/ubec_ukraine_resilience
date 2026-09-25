import pandas as pd, zipfile, glob

frames = []
for z in sorted(glob.glob("event_1pd_latest_*.zip")):
    with zipfile.ZipFile(z) as zf:
        name = [n for n in zf.namelist() if n.endswith(".csv")][0]
        frames.append(pd.read_csv(zf.open(name), low_memory=False))
ev = pd.concat(frames, ignore_index=True)

print(ev.shape)
print(ev.columns.tolist())
print(ev.head(3).T)
