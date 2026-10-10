"""Legacy compatibility module.

The Landvision Bokeh app now loads its bundled CSV directly from `main.py`.
This file remains so old imports do not break, but it no longer depends on
Bokeh sample data.
"""

from pathlib import Path

import pandas as pd


DATA_PATH = Path(__file__).resolve().parent / "data" / "floorplans.csv"


def process_data() -> pd.DataFrame:
    """Return the bundled floorplan data."""
    return pd.read_csv(DATA_PATH)
