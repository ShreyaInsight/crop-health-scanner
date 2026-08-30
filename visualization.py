"""Rendering helpers for the NDVI application."""

from __future__ import annotations

from io import BytesIO

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import BoundaryNorm, ListedColormap


def ndvi_figure(ndvi: np.ndarray):
    figure, axis = plt.subplots(figsize=(9, 6), constrained_layout=True)
    image = axis.imshow(ndvi, cmap="RdYlGn", vmin=-1, vmax=1)
    figure.colorbar(image, ax=axis, label="NDVI", shrink=0.85)
    axis.set_title("NDVI Crop-Health Map")
    axis.set_axis_off()
    return figure


def class_figure(classes: np.ndarray):
    colors = ["#d1d5db", "#6b7280", "#ef4444", "#facc15", "#16a34a"]
    cmap = ListedColormap(colors)
    norm = BoundaryNorm([-0.5, 0.5, 1.5, 2.5, 3.5, 4.5], cmap.N)
    figure, axis = plt.subplots(figsize=(9, 6), constrained_layout=True)
    axis.imshow(classes, cmap=cmap, norm=norm)
    axis.set_title("Vegetation Classification")
    axis.set_axis_off()
    return figure


def band_preview_figure(data: np.ndarray, title: str, cmap: str):
    """Render a contrast-stretched preview without changing analytical values."""
    finite = data[np.isfinite(data)]
    low, high = np.percentile(finite, [2, 98]) if finite.size else (0, 1)
    figure, axis = plt.subplots(figsize=(7, 5), constrained_layout=True)
    axis.imshow(data, cmap=cmap, vmin=low, vmax=high)
    axis.set_title(title)
    axis.set_axis_off()
    return figure


def ndvi_histogram_figure(ndvi: np.ndarray, valid: np.ndarray):
    figure, axis = plt.subplots(figsize=(8, 4.5), constrained_layout=True)
    axis.hist(ndvi[valid], bins=50, range=(-1, 1), color="#20834f", alpha=0.88)
    axis.axvline(0, color="#6b7280", linewidth=1)
    axis.set(title="NDVI value distribution", xlabel="NDVI", ylabel="Pixel count", xlim=(-1, 1))
    axis.grid(axis="y", alpha=0.2)
    return figure


def class_distribution_figure(stats: dict[str, float | int]):
    labels = ["Non-vegetated", "Sparse", "Moderate", "Dense"]
    values = [stats["non_vegetated_pct"], stats["sparse_pct"], stats["moderate_pct"], stats["dense_pct"]]
    colors = ["#6b7280", "#ef4444", "#facc15", "#16a34a"]
    figure, axis = plt.subplots(figsize=(6, 5.6), constrained_layout=True)

    wedges, _ = axis.pie(
        values,
        labels=None,
        colors=colors,
        startangle=90,
        counterclock=False,
        wedgeprops={"width": 0.38, "edgecolor": "white", "linewidth": 2},
    )
    axis.text(
        0,
        0,
        "VALID\nPIXELS",
        ha="center",
        va="center",
        fontsize=10,
        fontweight="bold",
        color="#356348",
        linespacing=1.25,
    )
    axis.legend(
        wedges,
        [f"{label} · {value:.1f}%" for label, value in zip(labels, values, strict=True)],
        loc="upper center",
        bbox_to_anchor=(0.5, -0.02),
        ncol=2,
        frameon=False,
        fontsize=9,
        columnspacing=1.4,
        handlelength=1.0,
    )
    axis.set_title("Health-class composition", pad=16)
    return figure


def figure_png_bytes(figure) -> bytes:
    buffer = BytesIO()
    figure.savefig(buffer, format="png", dpi=180, bbox_inches="tight")
    return buffer.getvalue()

