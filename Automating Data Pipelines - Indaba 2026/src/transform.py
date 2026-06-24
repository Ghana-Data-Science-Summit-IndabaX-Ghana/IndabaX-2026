"""Module 4 & 6 - Clean and Insights.

Cleaning turns messy cells into trustworthy values without erasing evidence.
The insight stage aggregates the tidy readings to answer the microclimate
question: do the raised panels soften the light and heat reaching the crops?
"""
import pandas as pd

MIDDAY_START = "11:00"
MIDDAY_END = "14:00"

# What "open" means depends on the sensor. The control field has no light
# sensor, so full-sun irradiance is referenced against the ground-mounted PV.
BASELINE_BY_MEASUREMENT = {
    "temperature": "open_sun_control",
    "humidity": "open_sun_control",
    "irradiance": "ground_mounted_pv",
}


def clean_long_table(long_table: pd.DataFrame) -> pd.DataFrame:
    """Build real timestamps and numeric values; failures become NaT / NaN."""
    cleaned = long_table.copy()
    cleaned["date"] = pd.to_datetime(cleaned["date"], errors="coerce")

    # Combine the sheet date with the row time. Junk like
    # '11:34 - Need network restart' simply coerces to NaT.
    stamp = (
        cleaned["date"].dt.strftime("%Y-%m-%d")
        + " "
        + cleaned["raw_time"].astype(str)
    )
    cleaned["timestamp"] = pd.to_datetime(stamp, errors="coerce")
    cleaned["value"] = pd.to_numeric(cleaned["value"], errors="coerce")
    return cleaned


def daily_plot_summary(cleaned: pd.DataFrame) -> pd.DataFrame:
    """Average each plot's readings per day and measurement."""
    return (
        cleaned.dropna(subset=["timestamp", "value"])
        .groupby(["date", "treatment", "station", "measurement"], dropna=False)
        .agg(
            observations=("value", "count"),
            mean_value=("value", "mean"),
            min_value=("value", "min"),
            max_value=("value", "max"),
        )
        .reset_index()
    )


def midday_microclimate(cleaned: pd.DataFrame) -> pd.DataFrame:
    """Compare the agrivoltaic plot against its open reference at midday.

    Each measurement is compared with the right baseline: temperature and
    humidity against the open-sun control field, irradiance against the
    full-sun ground-mounted panels.
    """
    midday = cleaned.dropna(subset=["timestamp", "value"]).set_index("timestamp")
    midday = midday.between_time(MIDDAY_START, MIDDAY_END).reset_index()

    means = midday.groupby(["measurement", "treatment"])["value"].mean().to_dict()

    rows = []
    for measurement, baseline in BASELINE_BY_MEASUREMENT.items():
        agrivoltaic = means.get((measurement, "agrivoltaic"))
        reference = means.get((measurement, baseline))
        if agrivoltaic is None or reference is None:
            continue
        difference = agrivoltaic - reference
        rows.append(
            {
                "measurement": measurement,
                "agrivoltaic": round(agrivoltaic, 2),
                "reference": baseline,
                "reference_value": round(reference, 2),
                "difference": round(difference, 2),
                "difference_pct": round(difference / reference * 100, 2),
            }
        )

    return pd.DataFrame(rows)
