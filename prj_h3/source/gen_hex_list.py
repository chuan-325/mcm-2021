import h3
import geopandas as gpd
from shapely import geometry, ops
import pandas as pd
import sys

input_dir = "../dataset/"
output_dir = "../output/csv"


def load_and_prepare_gdf(filepath):
    """Loads a geojson files of polygon geometries and features,
    swaps the latitude and longitude andstores geojson"""
    gdf = gpd.read_file(filepath, driver="GeoJSON")
    gdf.head()
    gdf["geom_geojson"] = gdf["geometry"].apply(lambda x: geometry.mapping(x))
    gdf["geom_swap"] = gdf["geometry"].map(
        lambda polygon: ops.transform(lambda x, y: (y, x), polygon))
    gdf["geom_swap_geojson"] = gdf["geom_swap"].apply(lambda x: geometry.mapping(x))
    return gdf


def fill_hexagons(geom_geojson, res, flag_swap=False, flag_return_df=False):
    set_hexagons = h3.polyfill(geojson=geom_geojson,
                               res=res,
                               geo_json_conformant=flag_swap)
    list_hexagons_filling = list(set_hexagons)

    if flag_return_df is True:
        df_fill_hex = pd.DataFrame({"hex_id": list_hexagons_filling})
        df_fill_hex["value"] = 0
        df_fill_hex['geometry'] = df_fill_hex.hex_id.apply(
            lambda x:
            {"type": "Polygon",
             "coordinates": [
                 h3.h3_to_geo_boundary(h=x,
                                       geo_json=True)
             ]
             })
        assert (df_fill_hex.shape[0] == len(list_hexagons_filling))
        return df_fill_hex
    else:
        return list_hexagons_filling


def convert_to_hex_df(gdf, col):
    hex_id = []
    for index, row in gdf.iterrows():
        hex_id.extend(row[col])
    hex_dict = {"hex_id": hex_id}
    hex_df_res = pd.DataFrame(hex_dict)
    return hex_df_res


if __name__ == '__main__':
    input_file = ""
    output_file = ""
    if sys.argv[1] == "forest":
        input_file = "forest.geojson"
        output_file = "forest.csv"
    elif sys.argv[1] == "victoria":
        input_file = "victoria.geojson"
        output_file = "hex.csv"
    else:
        print("Unsupported input !!!")
        exit(1)
    resolution = 7
    gdf = load_and_prepare_gdf(filepath=input_dir + input_file)
    gdf["hex_fill"] = gdf["geom_swap_geojson"].apply(
        lambda x: list(fill_hexagons(geom_geojson=x,
                                     res=resolution))
    )
    gdf["num_hex_fill"] = gdf["hex_fill"].apply(len)
    gdf = gdf[gdf["num_hex_fill"] > 0].reset_index(drop=True)
    total_num_hex = gdf["num_hex_fill"].sum()
    print("A total of {} hexagons are used to cover the map".format(total_num_hex))
    hex_df = convert_to_hex_df(gdf=gdf, col="hex_fill")
    hex_df.to_csv(output_dir + output_file, index=False)
