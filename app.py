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

st.set_page_config(page_title="Crop Health Scanner", page_icon="C", layout="wide")
st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=Fraunces:opsz,wght@9..144,600;9..144,700&display=swap');

      :root {
        --soil-950: #16251f;
        --soil-800: #253b32;
        --leaf-700: #356348;
        --leaf-500: #5f8a64;
        --moss-300: #a9b78b;
        --wheat-200: #ddd0a5;
        --clay-500: #b96747;
        --paper-100: #f4f1e8;
        --paper-50: #fbfaf6;
        --line: #d9d5c8;
      }

      html, body, [class*="css"], .stApp {font-family: 'DM Sans', sans-serif;}
      .stApp {background: var(--paper-50); color: var(--soil-950);}
      h1, h2, h3, .hero-title {font-family: 'Fraunces', serif !important; letter-spacing: -.025em;}
      .block-container {max-width: 1180px; padding-top: 2.2rem; padding-bottom: 4rem;}

      .hero {
        position: relative; overflow: hidden; padding: clamp(2rem, 5vw, 4.5rem);
        min-height: 330px; display: flex; align-items: flex-end;
        border: 1px solid var(--soil-950); border-radius: 3px;
        color: var(--paper-50); background: var(--soil-950); margin-bottom: 2.3rem;
        animation: rise-in .55s ease-out both;
      }
      .hero-copy {max-width: 720px; position: relative; z-index: 2;}
      .eyebrow {font-size: .74rem; font-weight: 600; letter-spacing: .17em; text-transform: uppercase;
                color: var(--moss-300); margin-bottom: 1.2rem;}
      .hero-title {font-size: clamp(2.6rem, 6vw, 5.3rem); line-height: .97; margin: 0; text-wrap: balance;}
      .hero-text {max-width: 610px; margin: 1.35rem 0 0; font-size: clamp(1rem, 1.8vw, 1.18rem);
                  line-height: 1.65; color: #dfe5dd; text-wrap: pretty;}
      .ndvi-mark {position: absolute; top: 0; right: 0; width: min(34%, 340px); height: 100%;
                  display: flex; opacity: .9; transform: skewX(-8deg) translateX(35px);}
      .ndvi-mark span {flex: 1; transition: flex .35s ease;}
      .ndvi-mark span:hover {flex: 1.7;}
      .ndvi-mark .n1 {background: var(--clay-500);}
      .ndvi-mark .n2 {background: var(--wheat-200);}
      .ndvi-mark .n3 {background: var(--moss-300);}
      .ndvi-mark .n4 {background: var(--leaf-500);}

      .workflow {display: grid; grid-template-columns: minmax(240px, .72fr) minmax(0, 1.55fr);
                 gap: clamp(2rem, 6vw, 5.5rem); margin: 1.5rem 0 3rem; align-items: start;}
      .workflow-intro {position: sticky; top: 2rem; padding-top: .5rem;}
      .workflow-intro h2 {font-size: clamp(2rem, 4vw, 3.25rem); line-height: 1.04; margin: 0 0 1rem; text-wrap: balance;}
      .workflow-intro p {color: #56645d; line-height: 1.7; max-width: 34ch;}
      .steps {border-top: 1px solid var(--soil-950);}
      .step {display: grid; grid-template-columns: 3rem 1fr; gap: 1rem; padding: 1.7rem .4rem;
             border-bottom: 1px solid var(--line); transition: transform .2s ease, background .2s ease;}
      .step:hover {transform: translateX(8px); background: var(--paper-100);}
      .step-number {font-family: 'Fraunces', serif; font-size: 1.35rem; color: var(--clay-500);}
      .step h3 {font-size: 1.35rem; margin: 0 0 .45rem;}
      .step p {margin: 0; line-height: 1.65; color: #56645d; max-width: 58ch; text-wrap: pretty;}

      [data-testid="stMetric"] {background: var(--paper-100); border: 1px solid var(--line);
             padding: 1rem; border-radius: 3px; transition: border-color .2s ease, transform .2s ease;}
      [data-testid="stMetric"]:hover {border-color: var(--leaf-500); transform: translateY(-2px);}
      .stButton > button, .stDownloadButton > button, .stLinkButton > a {
        border-radius: 2px !important; border: 1px solid var(--soil-800) !important;
        transition: transform .18s ease, box-shadow .18s ease !important;
      }
      .stButton > button:hover, .stDownloadButton > button:hover, .stLinkButton > a:hover {
        transform: translateY(-2px); box-shadow: 4px 4px 0 var(--moss-300) !important;
      }
      [data-baseweb="tab-list"] {gap: .35rem; border-bottom: 1px solid var(--line);}
      [data-baseweb="tab"] {font-family: 'DM Sans', sans-serif; padding-inline: 1rem;}

      @keyframes rise-in {from {opacity: 0; transform: translateY(14px);} to {opacity: 1; transform: translateY(0);}}
      @media (prefers-reduced-motion: reduce) {*, *::before, *::after {animation: none !important; transition: none !important;}}
      @media (max-width: 760px) {
        .block-container {padding-inline: 1rem; padding-top: 1rem;}
        .hero {min-height: 410px; align-items: flex-start;}
        .hero-copy {max-width: 100%;}
        .ndvi-mark {width: 100%; height: 85px; top: auto; bottom: 0; transform: none;}
        .workflow {grid-template-columns: 1fr; gap: 1rem;}
        .workflow-intro {position: static;}
      }
    </style>
    <div class="hero">
      <div class="hero-copy">
        <div class="eyebrow">Sentinel-2 field intelligence</div>
        <div class="hero-title">Read the field<br>from above.</div>
        <p class="hero-text">Transform aligned red and near-infrared satellite bands into an explainable crop-health map, pixel by pixel.</p>
      </div>
      <div class="ndvi-mark" aria-label="NDVI colour scale"><span class="n1"></span><span class="n2"></span><span class="n3"></span><span class="n4"></span></div>
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
    st.markdown(
        """
        <section class="workflow">
          <div class="workflow-intro">
            <div class="eyebrow" style="color: var(--leaf-700)">A focused workflow</div>
            <h2>From raw bands to a field signal.</h2>
            <p>No black-box prediction. Every result traces back to aligned raster values and an explicit NDVI calculation.</p>
          </div>
          <div class="steps">
            <article class="step"><div class="step-number">01</div><div><h3>Bring two aligned bands</h3><p>Select Sentinel-2 Level-2A B04 and B08 GeoTIFFs captured on the same date and clipped to one area.</p></div></article>
            <article class="step"><div class="step-number">02</div><div><h3>Inspect the matrix</h3><p>The scanner validates the geospatial grid, handles invalid pixels, and calculates NDVI without hiding the arithmetic.</p></div></article>
            <article class="step"><div class="step-number">03</div><div><h3>Carry the result forward</h3><p>Explore health classes and export a map, a statistics table, or a georeferenced raster for GIS work.</p></div></article>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
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
    ["NDVI map", "Input bands", "Health classes", "Statistics", "Export"]
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

