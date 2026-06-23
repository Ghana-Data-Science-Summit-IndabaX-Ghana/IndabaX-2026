# 02 Facilitator Guide

# 3-Hour Code-Along Workshop

## Workshop Title

**Automating a Ghana Agrivoltaics Data Pipeline**

## Teaching Style

Run this like a practical code-along workshop:

- move quickly but pause at checkpoints
- demo first, then make learners do the thing
- explain concepts through the code they are writing
- let learners inspect real, messy data instead of hiding it
- keep the energy high, but keep the claims careful

The room should be building for most of the session. The vibe:

> We are going to take raw, messy sensor logs, make them behave, and produce an
> answer we can actually defend.

## Core Story

The sponsors want the tutorial to use agricultural data from the FAIR Forward
catalog. We selected the Ghana agrivoltaics dataset because it is practical,
real, Ghana-specific, and connected to food security and clean energy.

Main question:

> Do raised solar panels keep the crops cooler - while still generating power?

Pipeline question:

> What has to happen before raw field sensor logs become trustworthy evidence?

**Important:** this dataset is **environmental sensor telemetry**, not crop
yields. It records irradiance, temperature, humidity, and rainfall every 5
minutes across three plots. So the analysis answers a **microclimate** question,
not a yield question. Be explicit about that with learners - it is itself a good
lesson in matching the question to the data you actually have.

## Audience Assumptions

Learners should know basic Python (run cells, read simple pandas, inspect
DataFrames, understand grouping). They do **not** need data engineering or ML
experience.

Be aware: **Module 2 (reshape) is the hardest part.** The wide two-header grid
with a drifting header row is genuinely tricky. Budget the most time and patience
here. For a beginner-heavy room, consider walking the room through `tidy_sheet`
line by line, or handing it out as starter code and focusing energy on
contract -> validate -> insights.

## Pre-Workshop Prep

1. `pip install -r requirements.txt` and confirm the environment works.
2. Run `python src/run_pipeline.py` once - it should finish with the midday
   microclimate table and write all outputs.
3. Open `notebooks/ghana_agrivoltaics_pipeline.ipynb` and run it top to bottom.
4. Re-read the plot-code legend (`AG/AO/PO/WS`, `PV/TI/SS`) so you can answer
   questions confidently.
5. Keep a local copy of `data/raw/` in case internet access fails (the workbooks
   already ship in the repo).

Dataset: https://www.kaggle.com/datasets/responsibleailab/agrivoltaic-dataset-ghana
Catalog: https://fair-forward.github.io/datasets/

## 3-Hour Run of Show

| Time | Segment | Format | Outcome |
| --- | --- | --- | --- |
| 0:00-0:25 | Cold open + mental model | Story + discussion | Learners understand the problem and what a pipeline is |
| 0:25-0:45 | Module 1 | Demo + code-along | Raw day-sheets are loaded |
| 0:45-1:10 | Module 2 | Demo + exercise | Data is reshaped to tidy rows and profiled |
| 1:10-1:30 | Module 3 | Guided mapping | Plot codes are decoded into a contract |
| 1:30-1:40 | Break | Reset | Everyone catches up |
| 1:40-2:05 | Module 4 | Demo + code-along | Timestamps and values are cleaned |
| 2:05-2:30 | Module 5 | Demo + exercise | Validation report is produced |
| 2:30-2:55 | Module 6 | Demo + code-along | Midday microclimate comparison and chart |
| 2:55-3:00 | Wrap | Discussion | Learners interpret outputs responsibly |

## Opening: 0:00-0:25

### Goal

Make the problem feel real, and give learners the mental model of a pipeline
before any code.

### Suggested Opening

> Today we are not starting with a clean sales CSV. We have a year of agrivoltaics
> sensor logs from Ghana - five messy Excel files, a sheet for every day, sensor
> codes buried in the headers. The question is whether raised panels keep crops
> cooler while still making power. But before we can answer anything, we need a
> pipeline that turns this mess into something trustworthy.

### Ask the Room

- What could go wrong if this data is messy and we don't notice?
- Who might use the output of this analysis?
- What would make the output trustworthy?

### Teaching Note

Keep it short. The code is the workshop; the story gives the code stakes.

## Module 1: Load the Raw Sheets, 0:25-0:45

### Big Idea

The first job of a pipeline is to reliably find and open inputs - and here that
means files **and** the day-sheets inside them.

### Demo

Show `Path`, listing workbooks, `pd.ExcelFile(...).sheet_names`, and reading one
sheet with `header=None` so the two header rows survive.

### Checkpoint

Who has all five workbooks listed? Who can read one raw sheet and point to the
plot-code row, the measurement row, and the time column?

### Common Issues

| Issue | Fix |
| --- | --- |
| No files found | Confirm the workbooks are in `data/raw/` |
| Excel fails to load | Confirm `openpyxl` is installed |
| Sheet looks empty up top | Some sheets have a blank first row - that's expected |

## Module 2: Reshape and Profile, 0:45-1:10

### Big Idea

Turn the wide two-header grid into tidy long rows, then profile. Detect the
header row instead of assuming its position.

### Demo

Show `detect_header_rows` (matching the measurement labels), `parse_sheet_date`,
and `tidy_sheet` (forward-fill the merged plot codes, then melt column by column).
Then build the full table and profile it.

### Learner Task

Learners build `long_table` and read the profile: how much of `value` is missing,
how many plot codes and measurements exist.

### Checkpoint

Everyone saves `outputs/reports/profile_readings.csv` and can state the missing
percentage of `value`.

### Teaching Line

> The reshape is the hard part of real data work. Once it's tidy, everything
> after this is just grouping and filtering.

### Common Issue

The build cell is slow (~150 sheets). Tell learners it's meant to take ~30
seconds; it is not frozen.

## Module 3: Data Contract, 1:10-1:30

### Big Idea

The plot codes carry the experiment. Decode them once into treatments, stations,
and units so the rest of the pipeline speaks meaning, not codes.

### Demo

Show `TREATMENT_BY_PREFIX`, `parse_plot_code`, and `apply_contract`. Walk through
`AG-PV P3` -> agrivoltaic / PV / P3.

### Learner Task

Learners confirm every prefix maps to a known treatment and decode a few codes.

### Common Issue

Learners may want the legend handed to them. Show them the three-plot design
(`AO` open control, `AG` agrivoltaic, `PO` ground-mounted PV) and let them
connect codes to it.

## Break: 1:30-1:40

Help anyone behind on file paths, the reshape, or the build cell.

## Module 4: Clean and Standardize, 1:40-2:05

### Big Idea

Make times real and values numeric without erasing evidence. Junk becomes `NaT` /
`NaN`, visibly.

### Demo

Show `clean_long_table`: combine the sheet date with the row time, coerce to
datetime, coerce values to numeric. Highlight that `errors="coerce"` exposes
failure rather than crashing.

### Learner Task

Learners clean the table and count how many timestamps became `NaT`.

### Checkpoint

`timestamp` is datetime or visible `NaT`; `value` is numeric or visible `NaN`;
the original table is unchanged.

## Module 5: Validate Data, 2:05-2:30

### Big Idea

Validation decides what may be published. Separate **structural** failures
(unknown plot code -> STOP) from **data-quality** issues (out-of-range spikes ->
quarantine and warn).

### Demo

Show `validate_known_plots`, `validate_ranges`, `validate_timestamps`, the
combined report, and `quarantine_out_of_range`.

### Learner Task

Learners run validation, then **break it on purpose**: rename a plot to `ZZ-XX`
and confirm the structural check fires.

### Checkpoint

Everyone has `outputs/reports/validation_report.csv`.

### Discussion Prompt

> If this pipeline ran automatically every month, should a single out-of-range
> sensor reading stop the whole run?

Expected answer: no - quarantine and warn for noise, but stop hard when the data
violates the contract (unknown plot, missing column).

## Module 6: Transform and Visualize, 2:30-2:55

### Big Idea

Summarise to a meaningful grain, then compare the agrivoltaic plot against the
right baseline at midday.

### Demo

Show `daily_plot_summary`, then the midday comparison with
`BASELINE_BY_MEASUREMENT`. Emphasise **why** irradiance uses the ground-mounted
PV as baseline (the control field has no light sensor). Save CSVs and the chart.

### Learner Task

Learners produce the comparison and chart.

### Checkpoint

Ask:

- How much cooler is the agrivoltaic plot at midday? (~7C)
- What happens to humidity?
- Why is irradiance compared against the ground-mounted PV?

## Wrap: 2:55-3:00

### Goal

Help learners interpret responsibly.

### Ask

- What does the data suggest, and what does it not prove?
- Why does cooler air not automatically mean higher yield?
- What extra data would strengthen the decision?

### Key Responsible Data Points

- This is a single pilot site, one 2024 window.
- It measures microclimate, not yield.
- Irradiance here is panel-plane solar resource, not under-canopy light.
- Attribution is required under CC-BY 4.0.

### Closing Line

> The win today is not just the chart. The win is the workflow: load, reshape,
> contract, clean, validate, transform, and communicate the limits.

## Instructor Energy Notes

- "Trust the file only after it has earned it."
- "The reshape is where real data work actually happens."
- "If the labels are inconsistent, your groupby will happily lie to your face."
- "A chart is not an argument unless the pipeline behind it is defensible."

Keep humor pointed at the workflow, not at learners.

## What Not to Do

- Do not spend 45 minutes lecturing before code.
- Do not hide the messy headers - the mess is the lesson.
- Do not claim the data proves a yield benefit. It measures microclimate.
- Do not turn the session into advanced ML.
- Do not manually fix the raw workbooks.

## Success Criteria

By the end, learners should have:

- loaded the raw day-sheets
- reshaped the data into a tidy table and profiled it
- decoded the plot codes into a contract
- cleaned timestamps and values
- generated a validation report
- produced the daily summary and midday microclimate comparison
- created at least one chart
- written a careful interpretation
