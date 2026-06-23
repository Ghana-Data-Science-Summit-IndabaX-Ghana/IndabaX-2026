"""End-to-end Ghana agrivoltaics microclimate pipeline.

One command rebuilds every trusted output: load -> reshape -> contract ->
clean -> validate -> insights. Run from the project root:

    python src/run_pipeline.py
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from reshape import build_long_table
from contract import apply_contract, ALLOWED_RANGES
from profile_data import profile_table, save_profile
from transform import (
    clean_long_table,
    daily_plot_summary,
    midday_microclimate,
)
from validate_data import (
    save_validation_report,
    validate_known_plots,
    validate_ranges,
    validate_timestamps,
)

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
REPORTS_DIR = ROOT / "outputs" / "reports"
CHARTS_DIR = ROOT / "outputs" / "charts"


def ensure_dirs() -> None:
    for directory in (PROCESSED_DIR, REPORTS_DIR, CHARTS_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def quarantine_out_of_range(cleaned):
    """Replace physically impossible readings with NaN, keeping the rows."""
    out = cleaned.copy()
    for measurement, (low, high) in ALLOWED_RANGES.items():
        mask = out["measurement"] == measurement
        bad = mask & ((out["value"] < low) | (out["value"] > high))
        out.loc[bad, "value"] = float("nan")
    return out


def save_microclimate_chart(comparison) -> None:
    fig, axes = plt.subplots(1, len(comparison), figsize=(11, 4))
    if len(comparison) == 1:
        axes = [axes]
    for ax, (_, row) in zip(axes, comparison.iterrows()):
        ax.bar(["Open reference", "Agrivoltaic"],
               [row["reference_value"], row["agrivoltaic"]],
               color=["#F7C948", "#54D17A"])
        ax.set_title(f"{row['measurement'].title()} ({row['difference_pct']:+}%)")
        ax.grid(axis="y", alpha=0.3)
    fig.suptitle("Midday microclimate: agrivoltaic vs open reference")
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "midday_microclimate.png", dpi=150)
    plt.close(fig)


def main() -> None:
    print("Starting Ghana agrivoltaics microclimate pipeline")
    ensure_dirs()

    long_table = build_long_table(RAW_DIR)
    if long_table.empty:
        raise RuntimeError(f"No readings reshaped from {RAW_DIR}")
    print(f"Reshaped {len(long_table):,} readings from raw sheets")

    contracted = apply_contract(long_table)
    cleaned = clean_long_table(contracted)

    profile = profile_table(cleaned)
    save_profile(profile, REPORTS_DIR)

    # Structural failure stops the run; data-quality issues are warnings.
    hard_errors = validate_known_plots(cleaned)
    warnings = validate_ranges(cleaned) + validate_timestamps(cleaned)
    rows = (
        [{"status": "error", "message": m} for m in hard_errors]
        + [{"status": "warning", "message": m} for m in warnings]
    )
    report = pd.DataFrame(
        rows or [{"status": "ok", "message": "Validation passed"}]
    )
    save_validation_report(report, REPORTS_DIR)

    if hard_errors:
        raise RuntimeError(
            "Validation failed. See outputs/reports/validation_report.csv"
        )
    print(f"Validation: {len(warnings)} data-quality warning(s) recorded")

    trusted = quarantine_out_of_range(cleaned)

    daily = daily_plot_summary(trusted)
    comparison = midday_microclimate(trusted)

    daily.to_csv(PROCESSED_DIR / "daily_plot_summary.csv", index=False)
    comparison.to_csv(PROCESSED_DIR / "midday_microclimate.csv", index=False)
    save_microclimate_chart(comparison)

    print("\nMidday microclimate (agrivoltaic vs open reference):")
    print(comparison.to_string(index=False))
    print("\nPipeline completed successfully")


if __name__ == "__main__":
    main()
