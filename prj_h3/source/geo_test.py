import rasterio
import rasterio.features
import rasterio.warp
import sys

f = open('test.geojson', 'w')
sys.stdout = f
sys.stderr = f

with rasterio.open('../dataset/aus_for18.tiff') as dataset:
    mask = dataset.dataset_mask()
    for geom, val in rasterio.features.shapes(
            mask, transform=dataset.transform):
        geom = rasterio.warp.transform_geom(
            dataset.crs, 'EPSG:4326', geom, precision=6)
        print(geom)

f.close()
