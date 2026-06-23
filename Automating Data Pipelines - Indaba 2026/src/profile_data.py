"""Module 2 - Profile.

A profile turns a million readings into one readable row-per-column diagnostic:
what each column is, how much is missing, and how many distinct values it holds.
"""
from pathlib import Path

import pandas as pd


def profile_table(df: pd.DataFrame) -> pd.DataFrame:
    """Create a compact data profile for one DataFrame."""
    return pd.DataFrame(
        {
            "column": df.columns,
            "dtype": [str(df[column].dtype) for column in df.columns],
            "missing_count": [int(df[column].isna().sum()) for column in df.columns],
            "missing_pct": [
                round(float(df[column].isna().mean() * 100), 2)
                for column in df.columns
            ],
            "unique_values": [
                int(df[column].nunique(dropna=True)) for column in df.columns
            ],
        }
    )


def save_profile(
    profile: pd.DataFrame,
    reports_dir: str | Path,
    filename: str = "profile_readings.csv",
) -> None:
    """Save a profile report as a CSV file."""
    output_dir = Path(reports_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    profile.to_csv(output_dir / filename, index=False)
