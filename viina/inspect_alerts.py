import pandas as pd
pd.set_option("display.width", 200); pd.set_option("display.max_columns", 40); pd.set_option("display.max_colwidth", 60)
a = pd.read_csv("../air_raid/official_data_en.csv")
print(a.shape); print(a.dtypes); print()
print("nulls:", a.isna().sum().to_dict()); print()
print(a.head(5).to_string()); print()
for c in a.columns:
    if a[c].dtype == object and a[c].nunique() <= 40:
        print(f"value_counts[{c}]:"); print(a[c].value_counts(dropna=False).to_string()); print()
print("unique oblast:", sorted(a["oblast"].dropna().unique().tolist())); print()
for c in a.columns:
    if a[c].dtype == object and 40 < a[c].nunique() < 5000:
        print(f"{c}: {a[c].nunique()} unique, samples: {a[c].dropna().unique()[:15].tolist()}")
s = pd.to_datetime(a["started_at"], utc=True, errors="coerce"); f = pd.to_datetime(a["finished_at"], utc=True, errors="coerce")
print("\nstarted range:", s.min(), "->", s.max(), " unparsed:", s.isna().sum(), f.isna().sum())
dur = (f - s).dt.total_seconds() / 3600
print("duration h: ", dur.describe().round(2).to_dict())
print("rows with level per year:"); print(pd.crosstab(s.dt.year, a["level"]).to_string())
