# Landvision

Landvision is a small Bokeh server app for exploring bundled residential floorplan data. The current app renders a competitive-market scattergraph, longitude/latitude location plot, filter controls, and a data table from `data/floorplans.csv`.

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Run

From the repository root:

```bash
bokeh serve --show .
```

If you do not want Bokeh to open a browser automatically:

```bash
bokeh serve . --address 127.0.0.1 --port 5006
```

Then open:

```text
http://127.0.0.1:5006/Landvision
```

## Data

The app expects:

```text
data/floorplans.csv
```

The CSV must include the columns used by `tabs/scattergraph_floorplans_tab.py`, including square footage, price, lot size, builder, market, sales-rate, latitude, and longitude fields.

## Security note

This repo no longer stores or prints cloud secrets. Keep API keys and provider credentials in an approved secret manager or environment-specific runtime configuration, not in source code.
