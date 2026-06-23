"""Module 1 - Load.

Find the workbooks and read their day-sheets exactly as received, with no
interpretation yet. Every Excel file is one month; every sheet is one day.
"""
from pathlib import Path

import pandas as pd

SUPPORTED_SUFFIXES = {".csv", ".xls", ".xlsx"}


def list_tabular_files(raw_dir: str | Path) -> list[Path]:
    """Return the supported workbooks in the raw data directory."""
    raw_path = Path(raw_dir)
    return sorted(
        path
        for path in raw_path.glob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES
    )


def list_day_sheets(path: str | Path) -> list[str]:
    """Return the sheet names in one workbook (one sheet per day)."""
    return pd.ExcelFile(path).sheet_names


def load_raw_sheet(path: str | Path, sheet_name: str) -> pd.DataFrame:
    """Read one day-sheet untouched: no header, nothing dropped."""
    return pd.read_excel(path, sheet_name=sheet_name, header=None)


def iter_raw_sheets(raw_dir: str | Path):
    """Yield (file_path, sheet_name, raw_frame) for every day in every file."""
    for file_path in list_tabular_files(raw_dir):
        for sheet_name in list_day_sheets(file_path):
            yield file_path, sheet_name, load_raw_sheet(file_path, sheet_name)
