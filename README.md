# Satellite Crop Health Scanner

A Streamlit application that reads aligned Sentinel-2 B04 (red) and B08 (near-infrared) GeoTIFF bands, calculates an NDVI matrix, visualizes vegetation health classes, reports summary statistics, and exports PNG, CSV, and GeoTIFF results.

## Run locally

Python 3.10–3.12 is recommended.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python generate_demo_data.py
streamlit run app.py
```

Upload `sample_data/B04_demo.tif` and `sample_data/B08_demo.tif`, or use your own aligned GeoTIFFs.

## Input rules

- Both bands must come from the same Sentinel-2 scene and date.
- They must have identical dimensions, CRS, resolution, extent, and pixel alignment.
- Sentinel-2 Level-2A B04 and B08 are both available at 10 m resolution.
- Clip large scenes to the farm/study area before upload.

## Interpretation

| NDVI | General interpretation |
|---|---|
| Below 0 | Water, shadow, or non-vegetated surface |
| 0–0.2 | Bare soil or sparse vegetation |
| 0.2–0.5 | Moderate vegetation |
| 0.5–1.0 | Comparatively dense/healthy-looking vegetation |

These are general-purpose thresholds. NDVI measures vegetation greenness/density and cannot independently diagnose a crop disease. Adjust interpretation for crop type, growth stage, soil, weather, and season.

## Test

```powershell
pytest -q
```

## Project structure

```text
app.py                  Streamlit user interface
ndvi_processor.py       Raster reading, validation, NDVI, statistics, exports
visualization.py        NDVI and classified-map rendering
generate_demo_data.py   Synthetic aligned GeoTIFF generator
tests/                  Automated core calculation tests
sample_data/            Generated demo bands (after running the generator)
```

