"""Bonus: the same pipeline, orchestrated by Apache Airflow.

This DAG does not reinvent the pipeline - it *wraps the exact functions* from
`src/` as tasks. Each task materialises its output to disk and passes the next
task a file path (never a 1.1M-row DataFrame through XCom).

Run it as a demo (see 04_Bonus_Airflow.md). It is NOT part of the core 3-hour
workshop and is not needed to complete the notebook or `src/run_pipeline.py`.

    raw sheets  ->  reshape  ->  clean  ->  validate  ->  insights

A failed `validate` task automatically stops everything downstream and the
Airflow UI shows the run as a graph - that is orchestration and lineage for free.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pendulum
from airflow.decorators import dag, task

# Make the project's own src/ importable, and locate its data folders.
# Default assumes this DAG lives in <project>/dags/; override with AGRI_PROJECT.
PROJECT = Path(os.environ.get("AGRI_PROJECT", Path(__file__).resolve().parents[1]))
SRC = str(PROJECT / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

PROCESSED = PROJECT / "data" / "processed"
REPORTS = PROJECT / "outputs" / "reports"


@dag(
    schedule="@monthly",  # a fresh workbook arrives each month
    start_date=pendulum.datetime(2024, 5, 1, tz="UTC"),
    catchup=False,
    tags=["agrivoltaics", "bonus"],
    doc_md=__doc__,
)
def agrivoltaics_pipeline():

    @task
    def reshape() -> str:
        """Module 2: wide two-header grid -> one tidy long table."""
        from reshape import build_long_table

        PROCESSED.mkdir(parents=True, exist_ok=True)
        out = PROCESSED / "long.parquet"
        df = build_long_table(PROJECT / "data" / "raw")
        # raw_time mixes time objects with junk strings, and value mixes numbers
        # with junk. Cast to string so the intermediate is parquet-serialisable -
        # the clean stage re-parses both with errors="coerce".
        for col in ("raw_time", "value"):
            df[col] = df[col].astype(str)
        df.to_parquet(out)
        return str(out)

    @task
    def clean(long_path: str) -> str:
        """Modules 3 & 4: apply the contract, then clean timestamps + values."""
        import pandas as pd
        from contract import apply_contract
        from transform import clean_long_table

        cleaned = clean_long_table(apply_contract(pd.read_parquet(long_path)))
        out = PROCESSED / "clean.parquet"
        cleaned.to_parquet(out)
        return str(out)

    @task
    def validate(clean_path: str) -> str:
        """Module 5: structural failure stops the run; quality issues warn."""
        import pandas as pd
        from validate_data import (
            validate_known_plots,
            validate_ranges,
            validate_timestamps,
        )

        cleaned = pd.read_parquet(clean_path)
        hard_errors = validate_known_plots(cleaned)
        warnings = validate_ranges(cleaned) + validate_timestamps(cleaned)

        REPORTS.mkdir(parents=True, exist_ok=True)
        report = pd.DataFrame(
            [{"status": "error", "message": m} for m in hard_errors]
            + [{"status": "warning", "message": m} for m in warnings]
            or [{"status": "ok", "message": "Validation passed"}]
        )
        report.to_csv(REPORTS / "validation_report.csv", index=False)

        if hard_errors:
            # Raising fails this task -> downstream tasks never run.
            raise ValueError(f"Validation failed: {hard_errors}")
        return clean_path

    @task
    def insights(clean_path: str) -> None:
        """Module 6: quarantine impossible readings, summarise, compare."""
        import pandas as pd
        from contract import ALLOWED_RANGES
        from transform import daily_plot_summary, midday_microclimate

        trusted = pd.read_parquet(clean_path)
        for measurement, (low, high) in ALLOWED_RANGES.items():
            mask = trusted["measurement"] == measurement
            bad = mask & ((trusted["value"] < low) | (trusted["value"] > high))
            trusted.loc[bad, "value"] = float("nan")

        daily_plot_summary(trusted).to_csv(
            PROCESSED / "daily_plot_summary.csv", index=False
        )
        midday_microclimate(trusted).to_csv(
            PROCESSED / "midday_microclimate.csv", index=False
        )

    # Wire the stages. The arrows are the lineage.
    insights(validate(clean(reshape())))


agrivoltaics_pipeline()
