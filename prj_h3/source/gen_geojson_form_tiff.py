# This is a script copied from StackOverflow, which converts a tiff file into a geojson file.
# Note: The output file cannot be used directly as the input of `gen_hex_list.py`. You should
# adjust it to a standard geojson file first

import rasterio.features
import rasterio.warp
import json

input_dir = "../dataset/"
output_dir = "../dataset/"

if __name__ == '__main__':
    to_write = open(output_dir + "forest_raw.geojson", 'w')
    with rasterio.open(input_dir + "forest.tiff") as dataset:
        mask = dataset.dataset_mask()
        for geom, val in rasterio.features.shapes(
                mask, transform=dataset.transform):
            geom = rasterio.warp.transform_geom(
                dataset.crs, 'EPSG:4326', geom, precision=6)
            json.dump(geom, to_write)
    to_write.close()
