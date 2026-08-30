"""Core raster validation, NDVI calculation, classification, and exports."""

from __future__ import annotations

from dataclasses import dataclass
from typing import BinaryIO

import numpy as np
import rasterio
from rasterio.io import MemoryFile


MAX_PIXELS = 25_000_000


@dataclass(frozen=True)
class NdviThresholds:
    """Configurable, validated NDVI classification thresholds."""

    sparse_upper: float = 0.2
    dense_lower: float = 0.5

    def __post_init__(self) -> None:
        if not 0.0 < self.sparse_upper < self.dense_lower <= 1.0:
            raise ValueError("Thresholds must satisfy 0 < sparse < dense <= 1.")


@dataclass(frozen=True)
class RasterBand:
    data: np.ndarray
    valid_mask: np.ndarray
    profile: dict
    transform: object
    crs: object


def read_band(source: str | BinaryIO) -> RasterBand:
    """Read the first band of a raster and preserve its geospatial metadata."""
    if hasattr(source, "seek"):
        source.seek(0)
    try:
        with rasterio.open(source) as dataset:
            if dataset.count < 1 or dataset.width == 0 or dataset.height == 0:
                raise ValueError("The raster is empty or contains no readable band.")
            if dataset.width * dataset.height > MAX_PIXELS:
                raise ValueError(
                    f"Raster is too large for this demo ({dataset.width * dataset.height:,} pixels). "
                    f"Please clip it below {MAX_PIXELS:,} pixels."
                )
            masked = dataset.read(1, masked=True).astype("float32")
            data = masked.filled(np.nan)
            valid_mask = ~np.ma.getmaskarray(masked) & np.isfinite(data)
            return RasterBand(
                data=data,
                valid_mask=valid_mask,
                profile=dataset.profile.copy(),
                transform=dataset.transform,
                crs=dataset.crs,
            )
    except rasterio.errors.RasterioIOError as exc:
        raise ValueError("This file is not a readable TIFF/GeoTIFF raster.") from exc


def _validate_alignment(red: RasterBand, nir: RasterBand) -> None:
    if red.data.shape != nir.data.shape:
        raise ValueError(
            f"Band dimensions differ: Red is {red.data.shape}, NIR is {nir.data.shape}."
        )
    if red.transform != nir.transform:
        raise ValueError("Band pixel grids do not align (their transforms differ).")
    if red.crs != nir.crs:
        raise ValueError("Band coordinate systems differ. Reproject them to the same CRS.")


def calculate_ndvi(red: RasterBand, nir: RasterBand) -> tuple[np.ndarray, np.ndarray]:
    """Calculate NDVI and return it with the shared valid-pixel mask."""
    _validate_alignment(red, nir)
    valid = red.valid_mask & nir.valid_mask
    denominator = nir.data + red.data
    valid &= np.isfinite(denominator) & (denominator != 0)

    ndvi = np.full(red.data.shape, np.nan, dtype="float32")
    np.divide(nir.data - red.data, denominator, out=ndvi, where=valid)
    np.clip(ndvi, -1.0, 1.0, out=ndvi)
    valid &= np.isfinite(ndvi)
    if not valid.any():
        raise ValueError("The bands contain no pixels suitable for NDVI calculation.")
    return ndvi, valid


def classify_ndvi(
    ndvi: np.ndarray,
    valid: np.ndarray,
    thresholds: NdviThresholds | None = None,
) -> np.ndarray:
    """Classify NDVI: 0 invalid, 1 non-vegetated, 2 sparse, 3 moderate, 4 dense."""
    thresholds = thresholds or NdviThresholds()
    classes = np.zeros(ndvi.shape, dtype="uint8")
    classes[valid & (ndvi < 0.0)] = 1
    classes[valid & (ndvi >= 0.0) & (ndvi < thresholds.sparse_upper)] = 2
    classes[valid & (ndvi >= thresholds.sparse_upper) & (ndvi < thresholds.dense_lower)] = 3
    classes[valid & (ndvi >= thresholds.dense_lower)] = 4
    return classes


def summarize_ndvi(
    ndvi: np.ndarray,
    valid: np.ndarray,
    thresholds: NdviThresholds | None = None,
) -> dict[str, float | int]:
    thresholds = thresholds or NdviThresholds()
    values = ndvi[valid]
    total = values.size
    return {
        "valid_pixels": int(total),
        "minimum": float(values.min()),
        "maximum": float(values.max()),
        "average": float(values.mean()),
        "non_vegetated_pct": float(np.count_nonzero(values < 0.0) / total * 100),
        "sparse_pct": float(np.count_nonzero((values >= 0.0) & (values < thresholds.sparse_upper)) / total * 100),
        "moderate_pct": float(np.count_nonzero((values >= thresholds.sparse_upper) & (values < thresholds.dense_lower)) / total * 100),
        "dense_pct": float(np.count_nonzero(values >= thresholds.dense_lower) / total * 100),
    }


def ndvi_geotiff_bytes(ndvi: np.ndarray, valid: np.ndarray, profile: dict) -> bytes:
    """Create a float32, georeferenced, single-band NDVI GeoTIFF in memory."""
    output_profile = profile.copy()
    output_profile.update(dtype="float32", count=1, nodata=-9999.0, compress="deflate")
    data = np.where(valid, ndvi, -9999.0).astype("float32")
    with MemoryFile() as memfile:
        with memfile.open(**output_profile) as dataset:
            dataset.write(data, 1)
            dataset.set_band_description(1, "NDVI")
        return memfile.read()


def statistics_csv(stats: dict[str, float | int]) -> bytes:
    rows = ["metric,value"]
    rows.extend(f"{key},{value}" for key, value in stats.items())
    return ("\n".join(rows) + "\n").encode("utf-8")

