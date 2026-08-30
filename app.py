"""Streamlit interface for the Satellite Crop Health Scanner."""

from __future__ import annotations

import logging

import matplotlib.pyplot as plt
import streamlit as st

from ndvi_processor import (
    NdviThresholds,
    calculate_ndvi,
    classify_ndvi,
    ndvi_geotiff_bytes,
    read_band,
    statistics_csv,
    summarize_ndvi,
)
from visualization import (
    band_preview_figure,
    class_distribution_figure,
    class_figure,
    figure_png_bytes,
    ndvi_figure,
    ndvi_histogram_figure,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
LOGGER = logging.getLogger(__name__)

st.set_page_config(page_title="Crop Health Scanner", page_icon="🌿", layout="wide")
st.markdown(
    """
    <style>
      .stApp {background: linear-gradient(180deg, #f7fbf7 0%, #ffffff 42%);}
      .hero {padding: 1.6rem 1.8rem; border-radius: 18px; color: white;
             background: linear-gradient(120deg, #123d2a, #20834f); margin-bottom: 1rem;}
      .hero h1 {margin: 0; font-size: 2.15rem;}
      .hero p {margin: .45rem 0 0; opacity: .9;}
      .step {padding: 1rem; border: 1px solid #dce8df; border-radius: 14px;
             background: rgba(255,255,255,.82); min-height: 128px;}
      [data-testid="stMetric"] {background: white; border: 1px solid #e0ebe3;
             padding: 1rem; border-radius: 14px; box-shadow: 0 4px 16px rgba(18,61,42,.06);}
    </style>
    <div class="hero">
      <h1>🌿 Satellite Crop Health Scanner</h1>
      <p>Sentinel-2 B04 + B08 · pixel-level NDVI analysis · georeferenced exports</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Analysis setup")
    st.caption("Step 1 of 2 · Upload aligned Sentinel-2 bands")
    red_file = st.file_uploader("Red band (B04)", type=["tif", "tiff"], help="Sentinel-2 red band at 10 m")
    nir_file = st.file_uploader("Near-infrared band (B08)", type=["tif", "tiff"], help="NIR band from the same scene")
    with st.expander("Classification thresholds"):
        sparse_upper = st.slider("Sparse → moderate", 0.05, 0.40, 0.20, 0.05)
        dense_lower = st.slider("Moderate → dense", 0.30, 0.80, 0.50, 0.05)
        if sparse_upper >= dense_lower:
            st.error("Dense threshold must be greater than the sparse threshold.")
    st.info("Both files must share the same scene, date, CRS, resolution, extent, and pixel grid.")
    st.markdown("[View source code](https://github.com/ShreyaInsight/crop-health-scanner)")

if not (red_file and nir_file):
    st.subheader("From satellite bands to an actionable map")
    columns = st.columns(3)
    cards = [
        ("1 · Upload", "Select aligned Sentinel-2 Level-2A B04 and B08 GeoTIFF files."),
        ("2 · Analyse", "The app validates both grids and calculates NDVI for every valid pixel."),
        ("3 · Export", "Explore health classes and download PNG, CSV, or GeoTIFF results."),
    ]
    for column, (title, body) in zip(columns, cards, strict=True):
        column.markdown(f'<div class="step"><h3>{title}</h3><p>{body}</p></div>', unsafe_allow_html=True)
    st.markdown("### NDVI calculation")
    formula_col, meaning_col = st.columns([1, 2])
    formula_col.latex(r"NDVI = \frac{NIR - Red}{NIR + Red}")
    meaning_col.info(
        "Higher NDVI generally indicates greener, denser vegetation. NDVI does not independently "
        "diagnose a disease, and interpretation varies by crop, season, soil, and growth stage."
    )
    with st.expander("Where do I get B04 and B08?"):
        st.write("Use a cloud-free Sentinel-2 Level-2A scene. Download raw B04 and B08 as 10 m GeoTIFFs cropped to one area.")
        st.link_button("Open Copernicus Browser", "https://browser.dataspace.copernicus.eu/")
    st.stop()

if sparse_upper >= dense_lower:
    st.error("Correct the classification thresholds in the sidebar to continue.")
    st.stop()
if red_file.getvalue() == nir_file.getvalue():
    st.warning("The uploaded files are identical. Confirm that one is B04 and the other is B08.")

thresholds = NdviThresholds(sparse_upper=sparse_upper, dense_lower=dense_lower)
try:
    with st.status("Processing satellite bands…", expanded=True) as status:
        st.write("Reading GeoTIFF matrices and metadata")
        red, nir = read_band(red_file), read_band(nir_file)
        st.write("Validating CRS, dimensions, and pixel alignment")
        ndvi, valid = calculate_ndvi(red, nir)
        st.write("Calculating classifications and statistics")
        classes = classify_ndvi(ndvi, valid, thresholds)
        stats = summarize_ndvi(ndvi, valid, thresholds)
        status.update(label="Analysis complete", state="complete", expanded=False)
        LOGGER.info("Processed %s valid pixels", stats["valid_pixels"])
except ValueError as exc:
    LOGGER.warning("Input validation failed: %s", exc)
    st.error(str(exc))
    st.stop()
except Exception:
    LOGGER.exception("Unexpected NDVI processing error")
    st.error("Unexpected processing error. Check that both inputs are valid GeoTIFF bands.")
    st.stop()

st.subheader("Analysis summary")
metric_cols = st.columns(5)
for column, label, value in zip(
    metric_cols,
    ["Average NDVI", "Minimum", "Maximum", "Dense vegetation", "Valid pixels"],
    [f"{stats['average']:.3f}", f"{stats['minimum']:.3f}", f"{stats['maximum']:.3f}", f"{stats['dense_pct']:.1f}%", f"{stats['valid_pixels']:,}"],
    strict=True,
):
    column.metric(label, value)

overview_tab, bands_tab, classes_tab, statistics_tab, export_tab = st.tabs(
    ["🗺️ NDVI map", "🛰️ Input bands", "🌱 Health classes", "📊 Statistics", "⬇️ Export"]
)
with overview_tab:
    figure = ndvi_figure(ndvi)
    st.pyplot(figure, use_container_width=True)
    png_data = figure_png_bytes(figure)
    plt.close(figure)
    st.caption("Red indicates low NDVI; yellow indicates moderate NDVI; green indicates high NDVI.")

with bands_tab:
    preview_cols = st.columns(2)
    red_preview = band_preview_figure(red.data, "B04 · Red band", "Reds")
    preview_cols[0].pyplot(red_preview, use_container_width=True)
    plt.close(red_preview)
    nir_preview = band_preview_figure(nir.data, "B08 · Near-infrared band", "Greens")
    preview_cols[1].pyplot(nir_preview, use_container_width=True)
    metadata_cols = st.columns(4)
    metadata_cols[0].metric("Width", f"{red.data.shape[1]:,} px")
    metadata_cols[1].metric("Height", f"{red.data.shape[0]:,} px")
    metadata_cols[2].metric("CRS", str(red.crs or "Not provided"))
    metadata_cols[3].metric("Valid coverage", f"{valid.mean() * 100:.1f}%")

with classes_tab:
    class_cols = st.columns([3, 2])
    class_plot = class_figure(classes)
    class_cols[0].pyplot(class_plot, use_container_width=True)
    plt.close(class_plot)
    distribution = class_distribution_figure(stats)
    class_cols[1].pyplot(distribution, use_container_width=True)
    plt.close(distribution)
    st.markdown(
        f"🟩 **Dense ≥ {dense_lower:.2f}** · 🟨 **Moderate {sparse_upper:.2f}–{dense_lower:.2f}** · "
        f"🟥 **Sparse 0–{sparse_upper:.2f}** · ⬛ **Non-vegetated < 0** · ⬜ **No data**"
    )

with statistics_tab:
    stats_cols = st.columns([3, 2])
    histogram = ndvi_histogram_figure(ndvi, valid)
    stats_cols[0].pyplot(histogram, use_container_width=True)
    plt.close(histogram)
    stats_cols[1].dataframe(
        {"Class": ["Non-vegetated", "Sparse", "Moderate", "Dense"],
         "Area (%)": [stats["non_vegetated_pct"], stats["sparse_pct"], stats["moderate_pct"], stats["dense_pct"]]},
        hide_index=True,
        use_container_width=True,
    )
    st.warning("These categories are comparative indicators, not a diagnosis of crop disease.")

with export_tab:
    st.write("Download reproducible outputs for GIS, reporting, or further analysis.")
    download_cols = st.columns(3)
    download_cols[0].download_button("Download map (PNG)", png_data, "ndvi_map.png", "image/png", use_container_width=True)
    download_cols[1].download_button("Download raster (GeoTIFF)", ndvi_geotiff_bytes(ndvi, valid, red.profile), "ndvi.tif", "image/tiff", use_container_width=True)
    download_cols[2].download_button("Download statistics (CSV)", statistics_csv(stats), "ndvi_statistics.csv", "text/csv", use_container_width=True)

st.divider()
st.caption("Built with Python, Streamlit, NumPy, Rasterio, and Matplotlib · Sentinel-2 Level-2A NDVI analysis")

