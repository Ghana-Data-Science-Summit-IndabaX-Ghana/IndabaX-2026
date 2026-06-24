"""Module 3 - Contract.

The plot codes carry the whole experiment design. This module makes that design
explicit: what each code means, what units we expect, and what ranges are valid.
"""
import pandas as pd

# Short, stable names for the raw measurement labels.
MEASUREMENT_NAMES = {
    "Irr (W/m2)": "irradiance",
    "T (oC)": "temperature",
    "RH (%)": "humidity",
    "P (mm)": "rainfall",
}

MEASUREMENT_UNITS = {
    "irradiance": "W/m2",
    "temperature": "C",
    "humidity": "%",
    "rainfall": "mm",
}

# Plot prefix -> treatment (the three experimental plots + the weather station).
TREATMENT_BY_PREFIX = {
    "AG": "agrivoltaic",        # Plot 2: raised PV panels, crops underneath
    "AO": "open_sun_control",   # Plot 1: open field, no panels
    "PO": "ground_mounted_pv",  # Plot 3: bare-land panels, energy only
    "WS": "ambient",            # Weather station: site-wide reference
}

ALLOWED_PREFIXES = set(TREATMENT_BY_PREFIX)

# Physically plausible ranges; anything outside is a sensor fault, not data.
ALLOWED_RANGES = {
    "irradiance": (0, 1500),
    "temperature": (5, 60),
    "humidity": (0, 100),
    "rainfall": (0, 300),
}


def parse_plot_code(code: str) -> dict:
    """Split a plot code like 'AG-PV P3' into its parts.

    'AG-PV P3' -> prefix AG, station PV, replicate P3
    'WS'       -> prefix WS, station None, replicate None
    """
    base, _, replicate = code.strip().partition(" ")
    prefix, _, station = base.partition("-")
    return {
        "prefix": prefix,
        "station": station or None,
        "replicate": replicate or None,
        "treatment": TREATMENT_BY_PREFIX.get(prefix, "unknown"),
    }


def apply_contract(long_table: pd.DataFrame) -> pd.DataFrame:
    """Attach treatment, station, replicate, measurement name, and unit."""
    out = long_table.copy()
    parts = out["plot_code"].map(parse_plot_code)
    out["treatment"] = [p["treatment"] for p in parts]
    out["station"] = [p["station"] for p in parts]
    out["replicate"] = [p["replicate"] for p in parts]
    out["measurement"] = out["measurement"].map(MEASUREMENT_NAMES).fillna(
        out["measurement"]
    )
    out["unit"] = out["measurement"].map(MEASUREMENT_UNITS)
    return out
