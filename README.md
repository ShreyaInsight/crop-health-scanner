# 🌿 Satellite Crop Health Scanner

[![Live App](https://img.shields.io/badge/Live_App-Streamlit-FF4B4B?logo=streamlit)](https://crop-health-scanner-ca54vhtxe6wnnbpje9ict2.streamlit.app/)
[![CI](https://github.com/ShreyaInsight/crop-health-scanner/actions/workflows/ci.yml/badge.svg)](https://github.com/ShreyaInsight/crop-health-scanner/actions/workflows/ci.yml)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](#license)

A deployed geospatial application that converts aligned Sentinel-2 multispectral imagery into a pixel-level NDVI matrix, vegetation-health classifications, summary analytics, and GIS-ready exports.

**[Open the live application](https://crop-health-scanner-ca54vhtxe6wnnbpje9ict2.streamlit.app/)**

## Why this project matters

Field inspection does not scale easily across large agricultural areas. Satellite imagery provides repeatable observations, while NDVI offers a fast, explainable measure of relative vegetation greenness and density. This project turns raw Sentinel-2 bands into an accessible analytical workflow without requiring a machine-learning model.

> NDVI is an indicator of vegetation greenness and density. It cannot independently diagnose a particular crop disease, and thresholds should be calibrated for crop type, growth stage, soil, weather, and season.

## Features

- Upload aligned Sentinel-2 Level-2A B04 and B08 GeoTIFF bands.
- Validate raster dimensions, CRS, transform, nodata values, and processing size.
- Calculate NDVI safely with masked division and invalid-pixel handling.
- Adjust vegetation-classification thresholds interactively.
- Preview both original satellite bands with contrast stretching.
- Explore an NDVI map, classified map, histogram, distribution chart, and statistics.
- Export a presentation-ready PNG, statistics CSV, and georeferenced NDVI GeoTIFF.
- Run automated unit tests and lint checks through GitHub Actions.
- Deploy locally, with Docker, or on Streamlit Community Cloud.

## Application workflow

```text
B04 Red GeoTIFF ─┐
                  ├─► Validate alignment ─► NDVI matrix ─► Classification ─► Maps + statistics
B08 NIR GeoTIFF ─┘                                              └─────────► PNG / CSV / GeoTIFF
```

NDVI is calculated for every shared valid pixel:

```math
NDVI = \frac{NIR - Red}{NIR + Red}
```

## Default interpretation

| NDVI range | General interpretation |
|---|---|
| Below 0 | Water, shadow, built surface, or non-vegetated area |
| 0–0.2 | Bare soil or sparse vegetation |
| 0.2–0.5 | Moderate vegetation |
| 0.5–1.0 | Comparatively dense/healthy-looking vegetation |

The interface allows the 0.2 and 0.5 boundaries to be adjusted.

## Technology stack

| Area | Technology |
|---|---|
| Application | Python, Streamlit |
| Matrix processing | NumPy |
| Geospatial rasters | Rasterio, GeoTIFF |
| Visualisation | Matplotlib |
| Testing | Pytest |
| Quality | Ruff, GitHub Actions |
| Packaging | Docker |
| Deployment | Streamlit Community Cloud |

## Interface design system

The interface uses an agricultural editorial visual language rather than a generic dashboard template:

- **Palette:** soil, leaf, moss, wheat, clay, and paper tokens used consistently across the app.
- **Typography:** Fraunces for expressive display headings and DM Sans for compact analytical text.
- **Composition:** asymmetric workflow sections and a custom NDVI colour motif replace repetitive card grids.
- **Motion:** restrained entrance, hover, and button feedback with reduced-motion accessibility support.
- **Spacing:** responsive `clamp()` sizing, balanced line lengths, and content-driven height instead of fixed cards.

## Input requirements

The two bands must:

- come from the same Sentinel-2 scene and acquisition date;
- cover the same area of interest;
- have identical width, height, CRS, resolution, transform, and pixel grid;
- preferably be Level-2A B04 and B08 at 10 m resolution;
- be clipped to a small study area before upload.

Download raw bands using the [Copernicus Browser](https://browser.dataspace.copernicus.eu/). Choose a cloud-free scene, draw an area of interest, then use **Analytical → GeoTIFF → Raw B04 and B08**.

## Run locally

Python 3.10–3.12 is recommended.

```powershell
git clone https://github.com/ShreyaInsight/crop-health-scanner.git
cd crop-health-scanner
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

Generate small synthetic test bands if you do not yet have Sentinel-2 data:

```powershell
python generate_demo_data.py
```

Then upload `sample_data/B04_demo.tif` and `sample_data/B08_demo.tif`.

## Run with Docker

```bash
docker build -t crop-health-scanner .
docker run --rm -p 8501:8501 crop-health-scanner
```

Open `http://localhost:8501`.

## Tests and quality checks

```powershell
pytest
ruff check .
python -m compileall -q .
```

GitHub Actions repeats these checks for every push and pull request.

## Project structure

```text
crop-health-scanner/
├── .github/workflows/ci.yml   Automated tests and linting
├── .streamlit/config.toml     Application theme and server settings
├── app.py                     Streamlit interface and workflow
├── ndvi_processor.py          Validation, NDVI, classification, exports
├── visualization.py           Maps, previews, histogram, distribution chart
├── generate_demo_data.py      Synthetic aligned GeoTIFF generator
├── tests/                     Unit tests for core processing
├── Dockerfile                 Reproducible container deployment
├── pyproject.toml             Ruff and Pytest configuration
└── requirements.txt           Runtime and test dependencies
```

## Engineering decisions

- **Explainable analysis:** NDVI is deterministic and auditable rather than a black-box prediction.
- **Geospatial integrity:** inputs must share their complete grid definition, not only array dimensions.
- **Safe arithmetic:** zero denominators, nodata, NaN, and infinite values are excluded.
- **Memory guard:** oversized rasters are rejected with guidance to clip the study area.
- **Reproducible output:** the NDVI export preserves the source GeoTIFF profile and georeferencing.
- **Configurable interpretation:** thresholds are explicit, validated, and adjustable in the interface.

## Roadmap

- Sentinel-2 SCL cloud and cloud-shadow masking
- Two-date NDVI change detection
- GeoJSON/KML farm-boundary clipping
- Interactive web map with pixel inspection
- Automated Copernicus Data Space retrieval
- Downloadable PDF field report

## Résumé description

> Developed and deployed a geospatial crop-health monitoring application using Python, Streamlit, Rasterio, NumPy, and Sentinel-2 imagery. Implemented pixel-level NDVI analysis, raster-grid validation, nodata-safe matrix processing, configurable vegetation classification, analytical dashboards, automated CI tests, and georeferenced GeoTIFF/CSV exports.

## License

This project is available under the [MIT License](LICENSE).

