"""Module 5 - Validate.

Cleaning changed representation; validation judges acceptability. Each check
answers one question and returns evidence, so the pipeline can refuse to publish
data it cannot trust.
"""
from pathlib import Path

import pandas as pd

from contract import ALLOWED_PREFIXES, ALLOWED_RANGES


def validate_known_plots(cleaned: pd.DataFrame) -> list[str]:
    """Every plot code must belong to a known experimental plot."""
    prefixes = cleaned["plot_code"].str.split("-").str[0].str.split(" ").str[0]
    unknown = sorted(set(prefixes.dropna()) - ALLOWED_PREFIXES)
    if unknown:
        return [f"Unknown plot prefixes: {unknown}"]
    return []


def validate_ranges(cleaned: pd.DataFrame) -> list[str]:
    """Each measurement must fall inside its physically plausible range."""
    errors = []
    for measurement, (low, high) in ALLOWED_RANGES.items():
        values = cleaned.loc[cleaned["measurement"] == measurement, "value"]
        out_of_range = values[(values < low) | (values > high)]
        if not out_of_range.empty:
            errors.append(
                f"{measurement}: {len(out_of_range)} values outside "
                f"[{low}, {high}]"
            )
    return errors


def validate_timestamps(cleaned: pd.DataFrame) -> list[str]:
    """Flag readings whose time could not be parsed."""
    missing = int(cleaned["timestamp"].isna().sum())
    if missing:
        return [f"{missing} rows have an unparseable timestamp"]
    return []


def build_validation_report(errors: list[str]) -> pd.DataFrame:
    if not errors:
        return pd.DataFrame([{"status": "ok", "message": "Validation passed"}])
    return pd.DataFrame(
        {"status": "error", "message": message} for message in errors
    )


def save_validation_report(
    report: pd.DataFrame,
    reports_dir: str | Path,
    filename: str = "validation_report.csv",
) -> None:
    output_dir = Path(reports_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    report.to_csv(output_dir / filename, index=False)
