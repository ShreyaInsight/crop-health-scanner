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


def figure_png_bytes(figure) -> bytes:
    buffer = BytesIO()
    figure.savefig(buffer, format="png", dpi=180, bbox_inches="tight")
    return buffer.getvalue()

