"""Module 2 - Reshape.

The raw sheets are a wide sensor grid with two header rows: a plot code
(spread across merged cells) and a measurement type. We turn each sheet into
tidy long rows - one observation per row - which every later stage can rely on.
"""
import re

import pandas as pd

from ingest import iter_raw_sheets

# The measurement labels that mark the second header row.
MEASUREMENT_LABELS = {"Irr (W/m2)", "T (oC)", "RH (%)", "P (mm)"}


def detect_header_rows(raw: pd.DataFrame) -> tuple[int, int]:
    """Find the (plot-code row, measurement row).

    Some sheets have a blank top row, so we locate the measurement row by its
    labels instead of assuming a fixed position.
    """
    for i in range(min(6, len(raw))):
        labels = {str(v).strip() for v in raw.iloc[i] if isinstance(v, str)}
        if labels & MEASUREMENT_LABELS:
            return i - 1, i
    raise ValueError("No measurement header row found in sheet")


def parse_sheet_date(sheet_name: str) -> pd.Timestamp | None:
    """Turn a sheet name like '1 08 24' or '1_07_24' into a date."""
    tokens = [t for t in re.split(r"[ _]+", sheet_name.strip()) if t]
    if len(tokens) < 3 or not all(t.isdigit() for t in tokens[:3]):
        return None
    day, month, year = (int(t) for t in tokens[:3])
    year += 2000 if year < 100 else 0
    try:
        return pd.Timestamp(year=year, month=month, day=day)
    except ValueError:
        return None


def tidy_sheet(raw: pd.DataFrame, sheet_date: pd.Timestamp) -> pd.DataFrame:
    """Reshape one wide day-sheet into long rows.

    Returns columns: date, raw_time, plot_code, measurement, value.
    """
    plot_row, measurement_row = detect_header_rows(raw)
    plot_codes = raw.iloc[plot_row].ffill()          # carry codes across merges
    measurements = raw.iloc[measurement_row]
    body = raw.iloc[measurement_row + 1:].reset_index(drop=True)
    raw_time = body.iloc[:, 0]

    columns = []
    for col in range(1, raw.shape[1]):
        plot, measurement = plot_codes.iloc[col], measurements.iloc[col]
        if not (isinstance(plot, str) and isinstance(measurement, str)):
            continue
        if measurement.strip() not in MEASUREMENT_LABELS:
            continue
        columns.append(
            pd.DataFrame(
                {
                    "date": sheet_date,
                    "raw_time": raw_time.values,
                    "plot_code": plot.strip(),
                    "measurement": measurement.strip(),
                    "value": body.iloc[:, col].values,
                }
            )
        )

    if not columns:
        return pd.DataFrame(
            columns=["date", "raw_time", "plot_code", "measurement", "value"]
        )
    return pd.concat(columns, ignore_index=True)


def build_long_table(raw_dir) -> pd.DataFrame:
    """Reshape every day-sheet in every workbook into one tidy long table."""
    frames = []
    for _file_path, sheet_name, raw in iter_raw_sheets(raw_dir):
        sheet_date = parse_sheet_date(sheet_name)
        if sheet_date is None:
            continue
        frames.append(tidy_sheet(raw, sheet_date))

    return pd.concat(frames, ignore_index=True)
