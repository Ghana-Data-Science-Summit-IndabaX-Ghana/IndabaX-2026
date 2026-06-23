# Automating Data Pipelines - Indaba 2026

## Workshop Theme

**Automating a Ghana Agrivoltaics Data Pipeline**

This is a 3-hour, code-along workshop that teaches participants how to build a
repeatable data pipeline from **real, messy field data** from Ghana. The dataset
comes from an agrivoltaics pilot: farming under or near raised solar photovoltaic
panels so the same land supports both crop production and clean energy.

The teaching rhythm is practical:

```text
load
reshape
contract
clean
validate
insights
```

## Main Problem

**Do raised solar panels keep the crops cooler - while still generating power?**

Participants use environmental sensor data to compare the **midday microclimate**
under the agrivoltaic panels against an open-sun control field. The goal is not
only to analyze the data, but to learn how a raw, messy dataset becomes trusted,
validated, analysis-ready output through an automated pipeline.

## Dataset

- Catalog: https://fair-forward.github.io/datasets/
- Dataset: https://www.kaggle.com/datasets/responsibleailab/agrivoltaic-dataset-ghana
- Country: Ghana
- Provider: Responsible AI Lab, KNUST
- License: CC-BY 4.0

**The data is environmental sensor telemetry, not crop yields:**

- 5 Excel workbooks, one per month (May-Oct 2024).
- ~30 sheets per workbook - one sheet per day.
- Each day-sheet is a wide grid: a plot-code row over a measurement row, with
  time down the side, logged every 5 minutes (~1.1M readings total).
- Measurements: irradiance (W/m2), temperature (C), humidity (%), rainfall (mm).

The experiment has three plots plus a weather station:

- **`AO` - Open control field:** open sun, no panels.
- **`AG` - Agrivoltaic system:** raised PV panels with crops underneath.
- **`PO` - Ground-mounted PV:** bare land, energy only.
- **`WS` - Weather station:** ambient site reference.

> Because the dataset has no yield numbers, the workshop answers the question the
> data can answer: **microclimate** (light and heat), agrivoltaic vs open control.

## What Learners Will Build

A pipeline that:

1. Lists the monthly workbooks and their daily sheets.
2. Reads each raw sheet untouched.
3. Reshapes the wide two-header grid into one tidy long table.
4. Profiles columns, missingness, and cardinality.
5. Decodes the plot codes into a data contract (treatments, stations, units).
6. Cleans timestamps and numeric values without erasing evidence.
7. Validates structure (stop) and data quality (quarantine + warn).
8. Summarises to a daily, per-plot grain.
9. Compares the agrivoltaic plot against its open reference at midday.
10. Saves processed tables and a chart, runnable as one command.

## Folder Structure

```text
Automating Data Pipelines - Indaba 2026/
  README.md
  01_Tutorial_Guide.md
  02_Facilitator_Guide.md
  03_Exercises.md
  requirements.txt
  data/
    raw/          # the 5 monthly Excel workbooks (ship with the repo)
    processed/    # pipeline-generated tables
  notebooks/
    ghana_agrivoltaics_pipeline.ipynb
  src/
    ingest.py
    reshape.py
    contract.py
    transform.py
    validate_data.py
    profile_data.py
    run_pipeline.py
  outputs/
    charts/
    reports/
```

## Material Guide

- `01_Tutorial_Guide.md`: learner-facing step-by-step pipeline workflow.
- `02_Facilitator_Guide.md`: pacing, teaching notes, prompts, checkpoints, issues.
- `03_Exercises.md`: module-aligned live tasks, checkpoints, and stretch tasks.
- `requirements.txt`: Python packages for the workshop.
- `notebooks/ghana_agrivoltaics_pipeline.ipynb`: guided code-along notebook.
- `src/`: the finished, runnable pipeline (`python src/run_pipeline.py`).
- `data/raw/`: the monthly workbooks. `data/processed/`: generated tables.
- `outputs/charts/`, `outputs/reports/`: charts and diagnostics.

## 3-Hour Flow

| Time | Segment | Outcome |
| --- | --- | --- |
| 0:00-0:25 | Opening | Problem, dataset, pipeline mental model |
| 0:25-0:45 | Module 1 | Raw day-sheets loaded |
| 0:45-1:10 | Module 2 | Data reshaped to tidy rows and profiled |
| 1:10-1:30 | Module 3 | Plot codes decoded into a contract |
| 1:30-1:40 | Break | Reset and catch up |
| 1:40-2:05 | Module 4 | Timestamps and values cleaned |
| 2:05-2:30 | Module 5 | Validation report produced |
| 2:30-2:55 | Module 6 | Midday microclimate comparison and chart |
| 2:55-3:00 | Wrap | Responsible interpretation |

## Recommended Setup

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run the finished pipeline at any time:

```bash
python src/run_pipeline.py
```

The workbooks already ship in `data/raw/`. To re-download from Kaggle:

```bash
kaggle datasets download responsibleailab/agrivoltaic-dataset-ghana -p data/raw --unzip
```

## Responsible Data Use

This dataset comes from a single Ghanaian pilot site and measures microclimate,
not yield. It should not be treated as proof that agrivoltaics will work the same
way across all farms, regions, soils, crop varieties, or economic conditions.

Participants should:

- Credit the dataset provider and source catalog (CC-BY 4.0).
- Avoid overgeneralizing from one pilot dataset.
- Communicate uncertainty clearly (microclimate is not yield).
- Treat pipeline outputs as decision support, not final policy or farming advice.

## Workshop Outcome

By the end, participants should be able to turn a real, messy agriculture dataset
into a reliable, repeatable pipeline that produces a trustworthy, well-qualified
answer.
