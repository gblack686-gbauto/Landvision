from pathlib import Path

import pandas as pd
from bokeh.models import Tabs
from bokeh.plotting import curdoc

from tabs.scattergraph_floorplans_tab import scattergraph_tab


APP_ROOT = Path(__file__).resolve().parent
DATA_PATH = APP_ROOT / "data" / "floorplans.csv"


def load_floorplans() -> pd.DataFrame:
    """Load the bundled floorplan data for the Bokeh application."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Missing floorplans CSV: {DATA_PATH}")
    return pd.read_csv(DATA_PATH)


floorplans = load_floorplans()
scatterplot_tab = scattergraph_tab(floorplans)

curdoc().title = "Landvision"
curdoc().add_root(Tabs(tabs=[scatterplot_tab], name="tabs"))
