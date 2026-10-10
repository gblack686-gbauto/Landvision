from __future__ import annotations

from pathlib import Path
import datetime as dt

import pandas as pd
from bokeh.layouts import column, layout
from bokeh.models import (
    Button,
    ColumnDataSource,
    DataTable,
    HoverTool,
    NumberFormatter,
    NumeralTickFormatter,
    RangeSlider,
    Select,
    Span,
    TabPanel,
    TableColumn,
)
from bokeh.models.widgets import TextInput
from bokeh.plotting import figure


AXIS_MAP = {
    "Home Size": "Square Footage (1)",
    "Base Price": "Price (1)",
    "Lot Size (sf)": "Typical Lot Size",
    "Latitude": "Lat",
    "Longitude": "Long",
    "Sales Rate": "Sales Rate",
}

REQUIRED_COLUMNS = {
    "Square Footage (1)",
    "Price (1)",
    "Typical Lot Size",
    "Project Name",
    "# of Floors (1)",
    "Builder Name",
    "City",
    "Sales Rate",
    "Total Units Planned",
    "Total Units Sold",
    "Total Remaining",
    "HOA1",
    "Assessments",
    "# of Beds (1)",
    "# of Baths (1)",
    "Lat",
    "Long",
}


def _rounded_limits(series: pd.Series, step: int) -> tuple[int, int]:
    clean = pd.to_numeric(series, errors="coerce").dropna()
    if clean.empty:
        return 0, step
    minimum = int(clean.min() // step * step)
    maximum = int(((clean.max() + step - 1) // step) * step)
    if minimum == maximum:
        maximum += step
    return minimum, maximum


def _validate_floorplans(df: pd.DataFrame) -> None:
    missing = sorted(REQUIRED_COLUMNS.difference(df.columns))
    if missing:
        raise ValueError(f"floorplans.csv is missing required columns: {', '.join(missing)}")


def scattergraph_tab(floorplans: pd.DataFrame) -> TabPanel:
    """Build the competitive market analysis tab for the Bokeh server app."""
    df = floorplans.copy()
    _validate_floorplans(df)

    # Normalize numeric columns used by filters and plots. Bad cells become NaN
    # and are naturally excluded by the slider predicates.
    numeric_columns = [
        "Square Footage (1)",
        "Price (1)",
        "Typical Lot Size",
        "Sales Rate",
        "Total Units Planned",
        "Total Units Sold",
        "Total Remaining",
        "HOA1",
        "Assessments",
        "# of Beds (1)",
        "# of Baths (1)",
        "Lat",
        "Long",
    ]
    for column_name in numeric_columns:
        df[column_name] = pd.to_numeric(df[column_name], errors="coerce")

    sf_min, sf_max = _rounded_limits(df["Square Footage (1)"], 500)
    price_min, price_max = _rounded_limits(df["Price (1)"], 50_000)
    lot_min, lot_max = _rounded_limits(df["Typical Lot Size"], 500)

    # Human-readable readouts sit next to sliders so the server app is usable
    # without editing source code.
    max_sf_widget = TextInput(title="Maximum Square Footage", value=str(sf_max), disabled=True)
    min_sf_widget = TextInput(title="Minimum Square Footage", value=str(sf_min), disabled=True)
    max_price_widget = TextInput(title="Maximum Base Price", value=str(price_max), disabled=True)
    min_price_widget = TextInput(title="Minimum Base Price", value=str(price_min), disabled=True)
    max_lot_size_widget = TextInput(title="Maximum Lot Size (sf)", value=str(lot_max), disabled=True)
    min_lot_size_widget = TextInput(title="Minimum Lot Size (sf)", value=str(lot_min), disabled=True)

    x_axis = Select(title="X Axis", options=sorted(AXIS_MAP.keys()), value="Home Size")
    y_axis = Select(title="Y Axis", options=sorted(AXIS_MAP.keys()), value="Base Price")

    fha_span = Span(location=403000, dimension="width", line_color="blue", line_dash="dashed", line_width=1)
    cll_span = Span(location=453100, dimension="width", line_color="green", line_dash="dashed", line_width=1)

    sf_slider = RangeSlider(title="Square Footage", start=sf_min, end=sf_max, value=(sf_min, sf_max), step=500)
    price_slider = RangeSlider(title="Base Price", start=price_min, end=price_max, value=(price_min, price_max), step=50_000)
    lot_slider = RangeSlider(title="Lot Size (SF)", start=lot_min, end=lot_max, value=(lot_min, lot_max), step=500)

    source = ColumnDataSource(data={})

    scatter = figure(height=500, width=800, title="Competitive Market Area", tools="pan,wheel_zoom,box_zoom,reset,save")
    scatter.scatter(x="x", y="y", source=source, size=15, line_color="black", fill_alpha=0.35)
    scatter.renderers.extend([fha_span, cll_span])
    scatter.yaxis.formatter = NumeralTickFormatter(format="$ 0,0")
    scatter.xaxis.formatter = NumeralTickFormatter(format="0,0")

    # Use a regular longitude/latitude plot instead of a Google Map. This keeps
    # the public app runnable without a hard-coded API key or secret.
    map_plot = figure(
        height=400,
        width=420,
        title="Community Locations",
        x_axis_label="Longitude",
        y_axis_label="Latitude",
        tools="pan,wheel_zoom,box_zoom,reset,save",
    )
    map_plot.scatter(x="Long", y="Lat", source=source, size=12, line_color="black", fill_alpha=0.35)

    def filter_df() -> pd.DataFrame:
        selected = df[
            (df["Square Footage (1)"] <= float(sf_slider.value[1]))
            & (df["Square Footage (1)"] >= float(sf_slider.value[0]))
            & (df["Price (1)"] <= float(price_slider.value[1]))
            & (df["Price (1)"] >= float(price_slider.value[0]))
            & (df["Typical Lot Size"] <= float(lot_slider.value[1]))
            & (df["Typical Lot Size"] >= float(lot_slider.value[0]))
        ]
        return selected.sort_values(by=["Project Name"])

    def update() -> None:
        selected = filter_df()
        x_column = AXIS_MAP[x_axis.value]
        y_column = AXIS_MAP[y_axis.value]

        scatter.xaxis.axis_label = x_axis.value
        scatter.yaxis.axis_label = y_axis.value
        scatter.title.text = f"Competitive Market Area — {len(selected)} floorplans selected"

        source.data = {
            "x": selected[x_column],
            "y": selected[y_column],
            "SF": selected["Square Footage (1)"],
            "Price": selected["Price (1)"],
            "Neighborhood": selected["Project Name"],
            "Floors": selected["# of Floors (1)"],
            "Builder": selected["Builder Name"],
            "Market": selected["City"],
            "Lot_Size": selected["Typical Lot Size"],
            "Sales_Rate": selected["Sales Rate"],
            "Total_Homes": selected["Total Units Planned"],
            "Homes_Sold": selected["Total Units Sold"],
            "Unsold_Homes": selected["Total Remaining"],
            "HOA": selected["HOA1"],
            "Tax_Rate": selected["Assessments"],
            "Beds": selected["# of Beds (1)"],
            "Baths": selected["# of Baths (1)"],
            "Lat": selected["Lat"],
            "Long": selected["Long"],
        }

    hover = HoverTool(
        tooltips=[
            ("Neighborhood", "@Neighborhood"),
            ("Builder", "@Builder"),
            ("Market", "@Market"),
            ("Lot Size", "@{Lot_Size}{0,0} SF"),
            ("Square Footage", "@{SF}{0,0} SF"),
            ("Base Price", "@{Price}{$0,0}"),
            ("Floors", "@Floors"),
            ("Sales Rate", "@{Sales_Rate}{0.0}/Mo"),
            ("Beds/Baths", "@Beds/@Baths"),
        ]
    )
    scatter.add_tools(hover)
    map_plot.add_tools(hover)

    table_columns = [
        TableColumn(field="Neighborhood", title="Neighborhood"),
        TableColumn(field="Market", title="Market"),
        TableColumn(field="Builder", title="Builder"),
        TableColumn(field="SF", title="Home Size", formatter=NumberFormatter(format="0,0")),
        TableColumn(field="Price", title="Base Price", formatter=NumberFormatter(format="$ 0,0[.]00")),
    ]
    table = DataTable(source=source, columns=table_columns, editable=False, height=600, width=1200, fit_columns=True)

    def download() -> None:
        downloads_dir = Path(__file__).resolve().parents[1] / "data" / "Downloads"
        downloads_dir.mkdir(parents=True, exist_ok=True)
        timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        filter_df().to_csv(downloads_dir / f"scattergraph_{timestamp}.csv", index=False)

    button_dl = Button(label="Export filtered CSV", button_type="success")
    button_dl.on_click(download)

    controls = [x_axis, y_axis, sf_slider, price_slider, lot_slider]
    for control in controls:
        control.on_change("value", lambda attr, old, new: update())

    readouts = [min_sf_widget, max_sf_widget, min_price_widget, max_price_widget, min_lot_size_widget, max_lot_size_widget]
    inputs = column([*controls, button_dl, *readouts], width=220, height=500)
    inputs.sizing_mode = "fixed"

    page = layout([[inputs, scatter], [map_plot], [table]], sizing_mode="fixed")
    update()
    return TabPanel(child=page, title="Scattergraph")
