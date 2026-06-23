# 03 Exercises

# Ghana Agrivoltaics Pipeline Exercises

These exercises are designed for a 3-hour code-along workshop.

You will build a pipeline around this question:

> Do raised solar panels keep the crops cooler - while still generating power?

Dataset: https://www.kaggle.com/datasets/responsibleailab/agrivoltaic-dataset-ghana
Catalog: https://fair-forward.github.io/datasets/

The data is **environmental sensor telemetry**: 5 monthly Excel workbooks, ~30
day-sheets each, a wide two-header grid logged every 5 minutes. There is no crop
yield - only irradiance, temperature, humidity, and rainfall across three plots
(`AO` open control, `AG` agrivoltaic, `PO` ground-mounted PV) and a weather
station (`WS`).

## Exercise Format

Each module has:

- **Live Task**: do this during the workshop.
- **Checkpoint**: prove the module worked.
- **Stretch**: optional if you move quickly.

By the end, you should produce:

```text
outputs/reports/profile_readings.csv
outputs/reports/validation_report.csv
data/processed/daily_plot_summary.csv
data/processed/midday_microclimate.csv
outputs/charts/midday_microclimate.png
```

## Opening Exercise: Frame the Problem

### Live Task

Write short answers:

1. What decision could this dataset help support?
2. Who might care about the answer?
3. What could go wrong if the data pipeline is wrong?

### Checkpoint

Explain the problem in one sentence, e.g.:

> We are building a pipeline to compare the midday microclimate under
> agrivoltaic panels against an open-sun control field in Ghana.

### Stretch

List two extra datasets that would strengthen the analysis (e.g. crop yield,
soil moisture, installation cost, farmer surveys).

## Module 1 Exercise: Load the Raw Sheets

### Live Task

The workbooks ship in `data/raw/`. List them and peek inside one:

```python
from pathlib import Path
import pandas as pd

RAW_DIR = Path("data/raw")
SUPPORTED = {".csv", ".xls", ".xlsx"}

workbooks = sorted(p for p in RAW_DIR.glob("*") if p.suffix.lower() in SUPPORTED)
for path in workbooks:
    print(path.name)

sheets = pd.ExcelFile(workbooks[0]).sheet_names
print(workbooks[0].name, "->", len(sheets), "sheets")

raw = pd.read_excel(workbooks[0], sheet_name=sheets[0], header=None)
raw.iloc[:5, :8]
```

### Checkpoint

- All five workbooks are listed.
- You can enumerate the day-sheets inside one workbook.
- You can read a single raw sheet with `header=None`.

### Stretch

Count the total number of day-sheets across all five workbooks.

## Module 2 Exercise: Reshape and Profile

### Live Task

Write the header detector and the reshape:

```python
import re

MEASUREMENT_LABELS = {"Irr (W/m2)", "T (oC)", "RH (%)", "P (mm)"}

def detect_header_rows(raw):
    for i in range(min(6, len(raw))):
        labels = {str(v).strip() for v in raw.iloc[i] if isinstance(v, str)}
        if labels & MEASUREMENT_LABELS:
            return i - 1, i
    raise ValueError("No measurement header row found")

def parse_sheet_date(sheet_name):
    tokens = [t for t in re.split(r"[ _]+", sheet_name.strip()) if t]
    if len(tokens) < 3 or not all(t.isdigit() for t in tokens[:3]):
        return None
    day, month, year = (int(t) for t in tokens[:3])
    year += 2000 if year < 100 else 0
    return pd.Timestamp(year=year, month=month, day=day)

def tidy_sheet(raw, sheet_date):
    plot_row, meas_row = detect_header_rows(raw)
    plot_codes = raw.iloc[plot_row].ffill()
    measurements = raw.iloc[meas_row]
    body = raw.iloc[meas_row + 1:].reset_index(drop=True)
    raw_time = body.iloc[:, 0]

    columns = []
    for col in range(1, raw.shape[1]):
        plot, meas = plot_codes.iloc[col], measurements.iloc[col]
        if not (isinstance(plot, str) and isinstance(meas, str)):
            continue
        if meas.strip() not in MEASUREMENT_LABELS:
            continue
        columns.append(pd.DataFrame({
            "date": sheet_date, "raw_time": raw_time.values,
            "plot_code": plot.strip(), "measurement": meas.strip(),
            "value": body.iloc[:, col].values,
        }))
    return pd.concat(columns, ignore_index=True)
```

Build the full table and profile it:

```python
frames = []
for workbook in workbooks:
    for sheet in pd.ExcelFile(workbook).sheet_names:
        sheet_date = parse_sheet_date(sheet)
        if sheet_date is None:
            continue
        raw_sheet = pd.read_excel(workbook, sheet_name=sheet, header=None)
        frames.append(tidy_sheet(raw_sheet, sheet_date))

long_table = pd.concat(frames, ignore_index=True)

def profile_table(df):
    return pd.DataFrame({
        "column": df.columns,
        "dtype": [str(df[c].dtype) for c in df.columns],
        "missing_pct": [round(df[c].isna().mean() * 100, 2) for c in df.columns],
        "unique_values": [df[c].nunique(dropna=True) for c in df.columns],
    })

REPORTS_DIR = Path("outputs/reports")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
profile = profile_table(long_table)
profile.to_csv(REPORTS_DIR / "profile_readings.csv", index=False)
profile
```

### Checkpoint

Answer:

1. How many readings are in `long_table`?
2. What percentage of `value` is missing?
3. How many distinct `plot_code`s and `measurement`s are there?

### Stretch

One sheet in July uses underscores (`1_07_24`) and some sheets have a blank top
row. Confirm your `detect_header_rows` and `parse_sheet_date` handle both.

## Module 3 Exercise: Define the Data Contract

### Live Task

Encode the legend and decode the codes:

```python
MEASUREMENT_NAMES = {"Irr (W/m2)": "irradiance", "T (oC)": "temperature",
                     "RH (%)": "humidity", "P (mm)": "rainfall"}
MEASUREMENT_UNITS = {"irradiance": "W/m2", "temperature": "C",
                     "humidity": "%", "rainfall": "mm"}
TREATMENT_BY_PREFIX = {"AG": "agrivoltaic", "AO": "open_sun_control",
                       "PO": "ground_mounted_pv", "WS": "ambient"}
ALLOWED_PREFIXES = set(TREATMENT_BY_PREFIX)
ALLOWED_RANGES = {"irradiance": (0, 1500), "temperature": (5, 60),
                  "humidity": (0, 100), "rainfall": (0, 300)}

def parse_plot_code(code):
    base, _, replicate = code.strip().partition(" ")
    prefix, _, station = base.partition("-")
    return {"prefix": prefix, "station": station or None,
            "replicate": replicate or None,
            "treatment": TREATMENT_BY_PREFIX.get(prefix, "unknown")}

def apply_contract(long_table):
    out = long_table.copy()
    parts = out["plot_code"].map(parse_plot_code)
    out["treatment"] = [p["treatment"] for p in parts]
    out["station"] = [p["station"] for p in parts]
    out["replicate"] = [p["replicate"] for p in parts]
    out["measurement"] = out["measurement"].map(MEASUREMENT_NAMES).fillna(
        out["measurement"])
    out["unit"] = out["measurement"].map(MEASUREMENT_UNITS)
    return out

contracted = apply_contract(long_table)
```

### Checkpoint

- `parse_plot_code("AG-PV P3")` returns treatment `agrivoltaic`, station `PV`,
  replicate `P3`.
- Every prefix in the data maps to a known treatment (none are `unknown`).

### Stretch

Write a short note: what do the `TI` and `SS` stations measure, and how would you
confirm it from the data?

## Module 4 Exercise: Clean and Standardize

### Live Task

```python
def clean_long_table(long_table):
    cleaned = long_table.copy()
    cleaned["date"] = pd.to_datetime(cleaned["date"], errors="coerce")
    stamp = (cleaned["date"].dt.strftime("%Y-%m-%d")
             + " " + cleaned["raw_time"].astype(str))
    cleaned["timestamp"] = pd.to_datetime(stamp, errors="coerce")
    cleaned["value"] = pd.to_numeric(cleaned["value"], errors="coerce")
    return cleaned

cleaned = clean_long_table(contracted)
print("unparseable timestamps:", int(cleaned["timestamp"].isna().sum()))
print("missing / non-numeric values:", int(cleaned["value"].isna().sum()))
```

### Checkpoint

`timestamp` is datetime (or visible `NaT`) and `value` is numeric (or visible
`NaN`). The original `long_table` is unchanged.

### Stretch

Find an example of a `raw_time` cell that became `NaT` and explain why.

## Module 5 Exercise: Validate

### Live Task

```python
def validate_known_plots(cleaned):
    prefixes = cleaned["plot_code"].str.split("-").str[0].str.split(" ").str[0]
    unknown = sorted(set(prefixes.dropna()) - ALLOWED_PREFIXES)
    return [f"Unknown plot prefixes: {unknown}"] if unknown else []

def validate_ranges(cleaned):
    errors = []
    for name, (low, high) in ALLOWED_RANGES.items():
        values = cleaned.loc[cleaned["measurement"] == name, "value"]
        bad = values[(values < low) | (values > high)]
        if not bad.empty:
            errors.append(f"{name}: {len(bad)} values outside [{low}, {high}]")
    return errors

def validate_timestamps(cleaned):
    missing = int(cleaned["timestamp"].isna().sum())
    return [f"{missing} rows have an unparseable timestamp"] if missing else []

hard_errors = validate_known_plots(cleaned)
warnings = validate_ranges(cleaned) + validate_timestamps(cleaned)

report = pd.DataFrame(
    [{"status": "error", "message": m} for m in hard_errors]
    + [{"status": "warning", "message": m} for m in warnings]
    or [{"status": "ok", "message": "Validation passed"}]
)
report.to_csv(REPORTS_DIR / "validation_report.csv", index=False)
report
```

### Checkpoint

You have `outputs/reports/validation_report.csv`.

### Stretch

Break it on purpose: set one `plot_code` to `"ZZ-XX"` and confirm
`validate_known_plots` now returns a structural error.

## Module 6 Exercise: Transform and Visualize

### Live Task

Quarantine impossible readings, then summarise and compare:

```python
def quarantine_out_of_range(cleaned):
    out = cleaned.copy()
    for name, (low, high) in ALLOWED_RANGES.items():
        mask = out["measurement"] == name
        bad = mask & ((out["value"] < low) | (out["value"] > high))
        out.loc[bad, "value"] = float("nan")
    return out

trusted = quarantine_out_of_range(cleaned)

PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

daily = (
    trusted.dropna(subset=["timestamp", "value"])
    .groupby(["date", "treatment", "station", "measurement"], dropna=False)
    .agg(observations=("value", "count"), mean_value=("value", "mean"),
         min_value=("value", "min"), max_value=("value", "max"))
    .reset_index()
)
daily.to_csv(PROCESSED_DIR / "daily_plot_summary.csv", index=False)

BASELINE_BY_MEASUREMENT = {"temperature": "open_sun_control",
                           "humidity": "open_sun_control",
                           "irradiance": "ground_mounted_pv"}

midday = trusted.dropna(subset=["timestamp", "value"]).set_index("timestamp")
midday = midday.between_time("11:00", "14:00").reset_index()
means = midday.groupby(["measurement", "treatment"])["value"].mean().to_dict()

rows = []
for measurement, baseline in BASELINE_BY_MEASUREMENT.items():
    ag = means.get((measurement, "agrivoltaic"))
    ref = means.get((measurement, baseline))
    if ag is None or ref is None:
        continue
    diff = ag - ref
    rows.append({"measurement": measurement, "agrivoltaic": round(ag, 2),
                 "reference": baseline, "reference_value": round(ref, 2),
                 "difference": round(diff, 2),
                 "difference_pct": round(diff / ref * 100, 2)})

comparison = pd.DataFrame(rows)
comparison.to_csv(PROCESSED_DIR / "midday_microclimate.csv", index=False)
comparison
```

Chart it:

```python
import matplotlib.pyplot as plt

CHARTS_DIR = Path("outputs/charts")
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

fig, axes = plt.subplots(1, len(comparison), figsize=(11, 4))
for ax, (_, row) in zip(axes, comparison.iterrows()):
    ax.bar(["Open reference", "Agrivoltaic"],
           [row["reference_value"], row["agrivoltaic"]],
           color=["#F7C948", "#54D17A"])
    ax.set_title(f"{row['measurement'].title()} ({row['difference_pct']:+}%)")
    ax.grid(axis="y", alpha=0.3)
fig.suptitle("Midday microclimate: agrivoltaic vs open reference")
fig.tight_layout()
fig.savefig(CHARTS_DIR / "midday_microclimate.png", dpi=150)
```

### Checkpoint

You should have:

```text
data/processed/daily_plot_summary.csv
data/processed/midday_microclimate.csv
outputs/charts/midday_microclimate.png
```

### Stretch

Recompute the comparison for a different time window (e.g. `09:00`-`11:00`). Does
the temperature gap shrink or grow away from peak sun?

## Closing Exercise: Responsible Interpretation

Write 5-7 sentences:

1. What does the comparison actually show?
2. Why is a cooler, drier midday microclimate interesting for crops?
3. What does it *not* prove (e.g. yield)?
4. Why is irradiance referenced against the ground-mounted PV, not the control field?
5. What limitations should be communicated, and what extra data would help?

This is a single pilot site, not a universal answer for all Ghanaian farms.

## Final Checklist

- [ ] workbooks present in `data/raw/`
- [ ] `outputs/reports/profile_readings.csv`
- [ ] `outputs/reports/validation_report.csv`
- [ ] `data/processed/daily_plot_summary.csv`
- [ ] `data/processed/midday_microclimate.csv`
- [ ] `outputs/charts/midday_microclimate.png`
- [ ] short written interpretation
