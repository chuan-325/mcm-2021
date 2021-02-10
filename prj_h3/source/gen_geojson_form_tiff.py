import rasterio.features
import rasterio.warp
import sys

input_dir = "../dataset/"
output_dir = "../dataset/"

to_write = open(output_dir + "forest.geojson", 'w')
sys.stdout = to_write
sys.stderr = to_write

with rasterio.open(input_dir + "forest.tiff") as dataset:
    mask = dataset.dataset_mask()
    for geom, val in rasterio.features.shapes(
            mask, transform=dataset.transform):
        geom = rasterio.warp.transform_geom(
            dataset.crs, 'EPSG:4326', geom, precision=6)
        print(geom)

to_write.close()
