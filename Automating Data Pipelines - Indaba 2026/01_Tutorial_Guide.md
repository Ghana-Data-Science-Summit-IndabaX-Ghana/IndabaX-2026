# 01 Tutorial Guide

# Automating a Ghana Agrivoltaics Data Pipeline

## Workshop Style

This is a 3-hour code-along tutorial. We build the pipeline in stages, inspect
what breaks, fix it, and end with real outputs.

The goal is not to memorize pandas. The goal is to learn the working rhythm of a
data engineer:

```text
look at the raw data
make the messy structure explicit
reshape it into something tidy
state your assumptions as a contract
clean carefully and validate before trusting
transform into useful outputs
communicate limits honestly
```

Raw data often looks calm until you ask it one serious question. So we will not
start with charts. We will start by inspecting the files.

## The Problem

**Do raised solar panels keep the crops cooler - while still generating power?**

We use a Ghana agrivoltaics dataset from the FAIR Forward Open Data catalog.
Agrivoltaics means using the same land for crop production and solar energy
generation, usually by placing raised solar PV panels above crops.

The practical question:

> Do crops under raised solar panels experience a gentler microclimate (less
> light and heat) than crops grown in open sun?

The pipeline question is just as important:

> Can we turn raw, messy field sensor logs into trusted outputs without doing
> manual spreadsheet magic every time?

## Dataset

- FAIR Forward catalog: https://fair-forward.github.io/datasets/
- Kaggle dataset: https://www.kaggle.com/datasets/responsibleailab/agrivoltaic-dataset-ghana
- Country: Ghana
- Provider: Responsible AI Lab, KNUST
- License: CC-BY 4.0

**What the data actually is.** This is *environmental sensor telemetry*, not a
tidy table of crop yields:

- 5 Excel workbooks, **one per month** (May, June, July, August, October 2024).
- **~30 sheets per workbook - one sheet per day** (e.g. `1 08 24`).
- Each day-sheet is a **wide grid**: a **plot code** row sits above a
  **measurement type** row, with **time** down the left, logged every 5 minutes
  (about 1.1 million readings in total).

**The experiment has three plots** (plus a weather station):

- **`AO` - Open control field (Plot 1):** open sun, no panels.
- **`AG` - Agrivoltaic system (Plot 2):** raised PV panels with crops underneath.
- **`PO` - Ground-mounted PV (Plot 3):** bare-land panels, energy only.
- **`WS` - Weather station:** site-wide ambient reference.

Plot codes look like `AG-PV P3`: prefix (`AG`) = treatment, suffix (`PV`, `TI`,
`SS`) = sensor station, `P3` = replicate. Measurements are irradiance (W/m2),
temperature (C), relative humidity (%), and rainfall (mm).

> **Note on the question.** This dataset contains no crop-yield numbers - only
> microclimate sensors. So we answer the question the data *can* answer:
> microclimate (light and heat), comparing the agrivoltaic plot against the
> open control field.

## 3-Hour Workshop Flow

| Time | Module | What We Build |
| --- | --- | --- |
| 0:00-0:25 | Opening | Problem, dataset, mental model |
| 0:25-0:45 | Module 1 | Load the raw day-sheets |
| 0:45-1:10 | Module 2 | Reshape to tidy rows and profile |
| 1:10-1:30 | Module 3 | Define the data contract (decode the codes) |
| 1:30-1:40 | Break | Quick reset |
| 1:40-2:05 | Module 4 | Clean timestamps and numeric values |
| 2:05-2:30 | Module 5 | Validate before trusting |
| 2:30-2:55 | Module 6 | Transform into the microclimate answer |
| 2:55-3:00 | Wrap | Save outputs, discuss responsible use |

Each module follows this pattern: **Big idea -> Instructor demo -> Your turn ->
Checkpoint -> Recap.**

## Project Structure

```text
Automating Data Pipelines - Indaba 2026/
  README.md
  01_Tutorial_Guide.md
  02_Facilitator_Guide.md
  03_Exercises.md
  requirements.txt
  data/
    raw/          # the 5 monthly Excel workbooks (untouched)
    processed/    # pipeline-generated tables
  notebooks/
    ghana_agrivoltaics_pipeline.ipynb
  src/
    ingest.py     # find files + read raw sheets
    reshape.py    # wide two-header grid -> tidy long rows
    contract.py   # decode plot codes, units, allowed ranges
    transform.py  # clean + summarise + compare
    validate_data.py
    profile_data.py
    run_pipeline.py
  outputs/
    charts/
    reports/
```

Do not manually edit raw files. If raw data needs fixing, write code that fixes
it.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

The 5 Excel workbooks ship in `data/raw/`. To re-download from Kaggle:

```bash
kaggle datasets download responsibleailab/agrivoltaic-dataset-ghana -p data/raw --unzip
```

You can run the finished pipeline at any point with:

```bash
python src/run_pipeline.py
```

The code-along itself lives in `notebooks/ghana_agrivoltaics_pipeline.ipynb`.

## Module 1: Load the Raw Sheets

### Big Idea

The first job of a pipeline is to reliably find and open its inputs. Here every
workbook is a month and every sheet is a day, so we list the files **and** the
sheets inside them.

### Instructor Demo

```python
from pathlib import Path
import pandas as pd

ROOT = Path("..").resolve()
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
REPORTS_DIR = ROOT / "outputs" / "reports"
CHARTS_DIR = ROOT / "outputs" / "charts"

for directory in [PROCESSED_DIR, REPORTS_DIR, CHARTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
```

```python
SUPPORTED = {".csv", ".xls", ".xlsx"}
workbooks = sorted(p for p in RAW_DIR.glob("*") if p.suffix.lower() in SUPPORTED)

for path in workbooks:
    print(path.name)

sheets = pd.ExcelFile(workbooks[0]).sheet_names
print(workbooks[0].name, "->", len(sheets), "sheets, e.g.", sheets[:5])
```

Read one day-sheet exactly as recorded - `header=None` keeps every messy row:

```python
raw = pd.read_excel(workbooks[0], sheet_name=sheets[0], header=None)
print(raw.shape)
raw.iloc[:5, :8]
```

### Your Turn

- How many workbooks did you load, and how many sheets are in each?
- In the raw sheet, which row holds the plot codes? Which holds the measurements?
- Where is the time column?

### Checkpoint

You can list every workbook, enumerate the day-sheets inside one, and read a
single raw sheet without cleaning anything yet.

### Recap

We did not transform anything. First we locate, open, and look.

## Module 2: Reshape and Profile

### Big Idea

The wide two-header grid is hard to work with. We reshape every sheet into
**tidy long rows** (one reading per row), then profile what we have. Because the
header row sometimes drifts, we *detect* it rather than assume its position.

### Instructor Demo

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
```

```python
def tidy_sheet(raw, sheet_date):
    plot_row, meas_row = detect_header_rows(raw)
    plot_codes = raw.iloc[plot_row].ffill()        # carry codes across merges
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
            "date": sheet_date,
            "raw_time": raw_time.values,
            "plot_code": plot.strip(),
            "measurement": meas.strip(),
            "value": body.iloc[:, col].values,
        }))
    return pd.concat(columns, ignore_index=True)
```

Build the full long table (this is the slow cell - ~150 sheets, ~30 seconds):

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
print(f"{len(long_table):,} readings")
```

Profile it:

```python
def profile_table(df):
    return pd.DataFrame({
        "column": df.columns,
        "dtype": [str(df[c].dtype) for c in df.columns],
        "missing_pct": [round(df[c].isna().mean() * 100, 2) for c in df.columns],
        "unique_values": [df[c].nunique(dropna=True) for c in df.columns],
    })

profile = profile_table(long_table)
profile.to_csv(REPORTS_DIR / "profile_readings.csv", index=False)
profile
```

### Your Turn

- What percentage of `value` is missing? (Hint: sensor gaps, not errors.)
- How many distinct `plot_code`s are there? How many `measurement`s?
- Pick one column whose cardinality surprises you and explain why.

### Checkpoint

Every day-sheet reshapes into tidy rows, the full table holds ~1.1M readings,
and a `profile_readings.csv` is saved in `outputs/reports/`.

### Recap

The reshape is the hardest and most valuable move. Once data is tidy, every
later stage becomes simple grouping and filtering.

## Module 3: Define the Data Contract

### Big Idea

A data contract is a small agreement between the raw source and your pipeline.
The cryptic plot codes carry the whole experiment, so we encode their meaning
once - prefix to treatment, label to unit - and the rest of the pipeline speaks
`agrivoltaic`, not `AG`.

### Instructor Demo

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
```

```python
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

### Your Turn

- Run `parse_plot_code("AG-PV P3")`. What does each part mean?
- Confirm every prefix in the data maps to a known treatment.
- Write a one-line note for any code you are unsure about.

### Checkpoint

You can choose a plot code and explain its treatment, station, and replicate,
and every reading now carries a `treatment` and `unit`.

### Recap

The contract is where the pipeline becomes intentional. We never let raw codes
leak into the analysis.

## Break: 10 Minutes

When you come back, we stop describing the data and start making it trustworthy.

## Module 4: Clean and Standardize

### Big Idea

Make times real and values numeric - without erasing evidence. Junk such as
`11:34 - Need network restart` becomes `NaT`; un-parseable numbers become `NaN`.
We expose failure instead of hiding it.

### Instructor Demo

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
```

### Your Turn

- How many timestamps became `NaT`? How many values became `NaN`?
- Confirm `cleaned` is a copy and `long_table` is unchanged.

### Checkpoint

`timestamp` is a real datetime or a visible `NaT`; `value` is numeric or a
visible `NaN`.

### Recap

Cleaning is not deleting bad rows. It is making messy cells trustworthy while
keeping the evidence of what was wrong.

## Module 5: Validate Before Trusting

### Big Idea

Validation decides what may be published. We separate **structural failures**
(an unknown plot code -> STOP) from **data-quality issues** (a few out-of-range
sensor spikes -> quarantine and warn). A pipeline that halts on every glitch
never ships; one that ignores structure cannot be trusted.

### Instructor Demo

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
```

```python
hard_errors = validate_known_plots(cleaned)
warnings = validate_ranges(cleaned) + validate_timestamps(cleaned)

report = pd.DataFrame(
    [{"status": "error", "message": m} for m in hard_errors]
    + [{"status": "warning", "message": m} for m in warnings]
    or [{"status": "ok", "message": "Validation passed"}]
)
report.to_csv(REPORTS_DIR / "validation_report.csv", index=False)

def quarantine_out_of_range(cleaned):
    out = cleaned.copy()
    for name, (low, high) in ALLOWED_RANGES.items():
        mask = out["measurement"] == name
        bad = mask & ((out["value"] < low) | (out["value"] > high))
        out.loc[bad, "value"] = float("nan")
    return out

trusted = quarantine_out_of_range(cleaned)
```

### Your Turn

Break it on purpose:

- Rename one plot to `ZZ-XX` and confirm `validate_known_plots` flags it.
- Inject a 350 temperature reading and watch it get quarantined, not published.
- Add one more check (duplicate timestamps, or a station that should not appear).

### Checkpoint

You have `outputs/reports/validation_report.csv` listing every issue, and an
unknown plot code stops the run.

### Recap

Validation is where the pipeline earns trust. Bad data fails loudly; expected
sensor noise is quarantined and recorded.

## Module 6: Transform Into Insights

### Big Idea

1.1M readings cannot be read directly. We summarise to a meaningful **grain**,
then compare the agrivoltaic plot against the right open reference at **midday** -
when sun, heat, and the panels' effect all peak.

### Instructor Demo

```python
daily = (
    trusted.dropna(subset=["timestamp", "value"])
    .groupby(["date", "treatment", "station", "measurement"], dropna=False)
    .agg(observations=("value", "count"),
         mean_value=("value", "mean"),
         min_value=("value", "min"),
         max_value=("value", "max"))
    .reset_index()
)
daily.to_csv(PROCESSED_DIR / "daily_plot_summary.csv", index=False)
```

Each measurement is compared with the baseline that actually exists - temperature
and humidity against the open control field, irradiance against the full-sun
ground-mounted PV (the control field has no light sensor):

```python
BASELINE_BY_MEASUREMENT = {"temperature": "open_sun_control",
                           "humidity": "open_sun_control",
                           "irradiance": "ground_mounted_pv"}

midday = trusted.dropna(subset=["timestamp", "value"]).set_index("timestamp")
midday = midday.between_time("11:00", "14:00").reset_index()
means = midday.groupby(["measurement", "treatment"])["value"].mean().to_dict()

rows = []
for measurement, baseline in BASELINE_BY_MEASUREMENT.items():
    agrivoltaic = means.get((measurement, "agrivoltaic"))
    reference = means.get((measurement, baseline))
    if agrivoltaic is None or reference is None:
        continue
    diff = agrivoltaic - reference
    rows.append({"measurement": measurement, "agrivoltaic": round(agrivoltaic, 2),
                 "reference": baseline, "reference_value": round(reference, 2),
                 "difference": round(diff, 2),
                 "difference_pct": round(diff / reference * 100, 2)})

comparison = pd.DataFrame(rows)
comparison.to_csv(PROCESSED_DIR / "midday_microclimate.csv", index=False)
comparison
```

Chart it:

```python
import matplotlib.pyplot as plt

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

### Your Turn

- How much cooler is the agrivoltaic plot at midday?
- What happens to humidity under the panels?
- Why is irradiance compared against the ground-mounted PV instead of the
  control field?

### Checkpoint

You have processed summaries in `data/processed/`, a chart in `outputs/charts/`,
and a clear, reproducible answer to Ama's question.

### Recap

We started with five messy workbooks. We now have tidy tables, a validation
report, and a chart - rebuildable any time with `python src/run_pipeline.py`.

## Wrap-Up: Responsible Interpretation

A clean pipeline does not make the dataset bigger than it is.

- This is a single Ghana pilot site, one growing window in 2024.
- The data measures **microclimate**, not yield - a cooler microclimate is
  promising for crops but does not by itself prove higher harvests.
- Irradiance here is panel-plane solar resource (energy), not under-canopy light.
- The dataset requires attribution under CC-BY 4.0.

Good conclusion style:

> In this pilot dataset, the midday microclimate under the agrivoltaic panels is
> markedly cooler and drier than the open control field, while the panels still
> receive strong irradiance. This supports further study of agrivoltaics for
> heat-stressed crops, but field yield trials and economic data are needed before
> any farmer or policy recommendation.

## Final Deliverables

- raw workbooks in `data/raw/`
- `outputs/reports/profile_readings.csv`
- `outputs/reports/validation_report.csv`
- `data/processed/daily_plot_summary.csv`
- `data/processed/midday_microclimate.csv`
- `outputs/charts/midday_microclimate.png`
- clear notes on what the data can and cannot support
