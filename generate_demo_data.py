"""Generate two small, aligned GeoTIFF bands for trying the app."""

from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin


output = Path(__file__).parent / "sample_data"
output.mkdir(exist_ok=True)
rows, columns = 320, 420
y, x = np.mgrid[-1:1:complex(rows), -1:1:complex(columns)]
vegetation = np.clip(0.75 - 0.45 * (x**2 + y**2), 0.05, 0.8)
vegetation += 0.08 * np.sin(x * 18) * np.cos(y * 12)
vegetation = np.clip(vegetation, -0.05, 0.85)
brightness = 6000 + 500 * np.sin(x * 5)
red = brightness * (1 - vegetation)
nir = brightness * (1 + vegetation)

profile = {
    "driver": "GTiff", "height": rows, "width": columns, "count": 1,
    "dtype": "uint16", "crs": "EPSG:32643",
    "transform": from_origin(500000, 2000000, 10, 10), "compress": "deflate",
}
for filename, data in (("B04_demo.tif", red), ("B08_demo.tif", nir)):
    with rasterio.open(output / filename, "w", **profile) as dataset:
        dataset.write(np.clip(data, 0, 10000).astype("uint16"), 1)
print(f"Demo bands created in {output}")

