"""Streamlit interface for the Satellite Crop Health Scanner."""

import matplotlib.pyplot as plt
import streamlit as st

from ndvi_processor import (
    calculate_ndvi,
    classify_ndvi,
    ndvi_geotiff_bytes,
    read_band,
    statistics_csv,
    summarize_ndvi,
)
from visualization import class_figure, figure_png_bytes, ndvi_figure


st.set_page_config(page_title="Crop Health Scanner", page_icon="🌿", layout="wide")
st.title("🌿 Satellite Crop Health Scanner")
st.caption("Sentinel-2 B04 + B08 • pixel-by-pixel NDVI matrix analysis")

with st.sidebar:
    st.header("Upload aligned bands")
    red_file = st.file_uploader("Red band (B04)", type=["tif", "tiff"])
    nir_file = st.file_uploader("Near-infrared band (B08)", type=["tif", "tiff"])
    st.info("Use bands from the same scene, date, crop area, CRS, resolution, and pixel grid.")

st.markdown(
    "This tool measures vegetation greenness and density. It does **not** diagnose a "
    "specific crop disease; thresholds vary with crop, growth stage, soil, and season."
)

if not (red_file and nir_file):
    st.subheader("How it works")
    st.latex(r"NDVI = \frac{NIR - Red}{NIR + Red}")
    st.write("Upload both GeoTIFF bands in the sidebar to generate the analysis.")
    st.stop()

if red_file.getvalue() == nir_file.getvalue():
    st.warning("The two uploaded files are identical. Check that one is B04 and the other is B08.")

try:
    with st.spinner("Reading bands and calculating NDVI…"):
        red = read_band(red_file)
        nir = read_band(nir_file)
        ndvi, valid = calculate_ndvi(red, nir)
        classes = classify_ndvi(ndvi, valid)
        stats = summarize_ndvi(ndvi, valid)
except ValueError as exc:
    st.error(str(exc))
    st.stop()
except Exception as exc:
    st.error(f"Unexpected processing error: {exc}")
    st.stop()

st.success(f"Processed {stats['valid_pixels']:,} valid pixels successfully.")
metric_cols = st.columns(4)
metric_cols[0].metric("Average NDVI", f"{stats['average']:.3f}")
metric_cols[1].metric("Minimum", f"{stats['minimum']:.3f}")
metric_cols[2].metric("Maximum", f"{stats['maximum']:.3f}")
metric_cols[3].metric("Dense / healthy-looking", f"{stats['dense_pct']:.1f}%")

map_tab, class_tab, stats_tab = st.tabs(["NDVI map", "Health classes", "Statistics"])
with map_tab:
    figure = ndvi_figure(ndvi)
    st.pyplot(figure, use_container_width=True)
    png_data = figure_png_bytes(figure)
    plt.close(figure)
with class_tab:
    class_plot = class_figure(classes)
    st.pyplot(class_plot, use_container_width=True)
    plt.close(class_plot)
    st.markdown("🟩 **Dense ≥ 0.5** · 🟨 **Moderate 0.2–0.5** · 🟥 **Sparse 0–0.2** · ⬛ **Non-vegetated < 0** · ⬜ **No data**")
with stats_tab:
    st.dataframe(
        {
            "Class": ["Non-vegetated", "Sparse", "Moderate", "Dense / healthy-looking"],
            "NDVI range": ["< 0", "0–0.2", "0.2–0.5", "≥ 0.5"],
            "Area (% of valid pixels)": [
                stats["non_vegetated_pct"], stats["sparse_pct"],
                stats["moderate_pct"], stats["dense_pct"],
            ],
        },
        hide_index=True,
        use_container_width=True,
    )

st.subheader("Download results")
download_cols = st.columns(3)
download_cols[0].download_button("NDVI map (PNG)", png_data, "ndvi_map.png", "image/png")
download_cols[1].download_button(
    "NDVI raster (GeoTIFF)",
    ndvi_geotiff_bytes(ndvi, valid, red.profile),
    "ndvi.tif",
    "image/tiff",
)
download_cols[2].download_button(
    "Statistics (CSV)", statistics_csv(stats), "ndvi_statistics.csv", "text/csv"
)

