import numpy as np
import pytest

from ndvi_processor import NdviThresholds, RasterBand, calculate_ndvi, classify_ndvi, summarize_ndvi


def band(values):
    data = np.asarray(values, dtype="float32")
    return RasterBand(data, np.isfinite(data), {}, "same-grid", "same-crs")


def test_ndvi_calculation_and_statistics():
    red = band([[1, 2], [4, 0]])
    nir = band([[3, 2], [0, 0]])
    ndvi, valid = calculate_ndvi(red, nir)
    np.testing.assert_allclose(ndvi[valid], [0.5, 0.0, -1.0])
    assert valid.sum() == 3
    stats = summarize_ndvi(ndvi, valid)
    assert stats["valid_pixels"] == 3
    assert round(stats["dense_pct"], 5) == round(100 / 3, 5)


def test_classification():
    values = np.array([[-0.2, 0.1, 0.3, 0.7, np.nan]], dtype="float32")
    valid = np.isfinite(values)
    assert classify_ndvi(values, valid).tolist() == [[1, 2, 3, 4, 0]]


def test_custom_thresholds():
    values = np.array([[0.1, 0.3, 0.7]], dtype="float32")
    valid = np.ones_like(values, dtype=bool)
    thresholds = NdviThresholds(sparse_upper=0.4, dense_lower=0.6)
    assert classify_ndvi(values, valid, thresholds).tolist() == [[2, 2, 4]]


def test_invalid_thresholds_are_rejected():
    with pytest.raises(ValueError):
        NdviThresholds(sparse_upper=0.6, dense_lower=0.5)


def test_misaligned_shapes_are_rejected():
    with pytest.raises(ValueError, match="dimensions differ"):
        calculate_ndvi(band([[1, 2]]), band([[1], [2]]))


def test_zero_denominator_pixels_become_invalid():
    ndvi, valid = calculate_ndvi(band([[0, 1]]), band([[0, 3]]))
    assert valid.tolist() == [[False, True]]
    assert np.isnan(ndvi[0, 0])

