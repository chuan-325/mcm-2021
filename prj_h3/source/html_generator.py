import h3
import geopandas as gpd
from shapely import geometry, ops
from geojson.feature import *
from folium import Map, GeoJson
import folium
import json
import pandas as pd
import sys


def load_and_prepare_districts(filepath):
    """Loads a geojson files of polygon geometries and features,
    swaps the latitude and longitude andstores geojson"""
    gdf_districts = gpd.read_file(filepath, driver="GeoJSON")
    gdf_districts.head()
    gdf_districts["geom_geojson"] = gdf_districts["geometry"].apply(lambda x: geometry.mapping(x))
    gdf_districts["geom_swap"] = gdf_districts["geometry"].map(
        lambda polygon: ops.transform(lambda x, y: (y, x), polygon))
    gdf_districts["geom_swap_geojson"] = gdf_districts["geom_swap"].apply(lambda x: geometry.mapping(x))
    return gdf_districts


def fill_hexagons(geom_geojson, res, flag_swap=False, flag_return_df=False):
    """Fills a geometry given in geojson format with H3 hexagons at specified
    resolution. The flag_reverse_geojson allows to specify whether the geometry
    is lon/lat or swapped"""

    set_hexagons = h3.polyfill(geojson=geom_geojson,
                               res=res,
                               geo_json_conformant=flag_swap)
    list_hexagons_filling = list(set_hexagons)

    if flag_return_df is True:
        # make dataframe
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


def base_empty_map():
    """Prepares a folium map centered in a central GPS point of Victoria"""
    m = Map(location=[-37.813889, 144.963056],
            zoom_start=10,
            tiles="cartodbpositron",
            attr='''© <a href="http://www.openstreetmap.org/copyright">
                      OpenStreetMap</a>contributors ©
                      <a href="http://cartodb.com/attributions#basemaps">
                      CartoDB</a>'''
            )
    return m


def plot_basemap_region_fill(df_boundaries_zones, initial_map=None):
    """On a folium map, add the boundaries of the geometries in geojson formatted
       column of df_boundaries_zones"""

    if initial_map is None:
        initial_map = base_empty_map()

    feature_group = folium.FeatureGroup(name='Boundaries')

    for i, row in df_boundaries_zones.iterrows():
        feature_sel = Feature(geometry=row["geom_geojson"], id=str(i))
        feat_collection_sel = FeatureCollection([feature_sel])
        geojson_subzone = json.dumps(feat_collection_sel)

        GeoJson(
            geojson_subzone,
            style_function=lambda feature: {
                'fillColor': None,
                'color': 'blue',
                'weight': 5,
                'fillOpacity': 0
            }
        ).add_to(feature_group)

    feature_group.add_to(initial_map)
    return initial_map


def hexagons_dataframe_to_geojson(df_hex, hex_id_field,
                                  geometry_field, value_field,
                                  file_output=None):
    """Produce the GeoJSON representation containing all geometries in a dataframe
     based on a column in geojson format (geometry_field)"""

    list_features = []

    for i, row in df_hex.iterrows():
        feature = Feature(geometry=row[geometry_field],
                          id=row[hex_id_field],
                          properties={"value": row[value_field]})
        list_features.append(feature)

    feat_collection = FeatureCollection(list_features)

    geojson_result = json.dumps(feat_collection)

    # optionally write to file
    if file_output is not None:
        with open(file_output, "w") as f:
            json.dump(feat_collection, f)

    return geojson_result


def map_addlayer_filling(df_fill_hex, map_initial, fillcolor=None):
    """ On a folium map (likely created with plot_basemap_region_fill),
        add a layer of hexagons that filled the geometry at given H3 resolution
        (df_fill_hex returned by fill_hexagons method)"""
    geojson_hx = hexagons_dataframe_to_geojson(df_fill_hex,
                                               hex_id_field="hex_id",
                                               value_field="value",
                                               geometry_field="geometry")
    GeoJson(
        geojson_hx,
        style_function=lambda feature: {
            'fillColor': fillcolor,
            'color': 'red',
            'weight': 2,
            'fillOpacity': 0.1
        },
        # name='xxx'
    ).add_to(map_initial)
    return map_initial


def visualize_district_filled_compact(gdf_districts,
                                      fillcolor=None):
    overall_map = base_empty_map()
    map_district = plot_basemap_region_fill(gdf_districts,
                                            initial_map=overall_map)
    for i, row in gdf_districts.iterrows():
        # district_name = row["libelle_du_grand_quartier"]
        if len(row["uncompacted_novoids"]) > 0:
            list_hexagons_filling_uncompact = row["uncompacted_novoids"]
        else:
            list_hexagons_filling_uncompact = []
        list_hexagons_filling_uncompact.extend(row["hex_fill_initial"])
        list_hexagons_filling_uncompact = list(set(list_hexagons_filling_uncompact))
        # make dataframes
        df_fill_compact = pd.DataFrame({"hex_id": list_hexagons_filling_uncompact})
        df_fill_compact["value"] = 0
        df_fill_compact['geometry'] = df_fill_compact.hex_id.apply(
            lambda x:
            {"type": "Polygon",
             "coordinates": [
                 h3.h3_to_geo_boundary(h=x,
                                       geo_json=True)
             ]
             })
        map_fill_compact = map_addlayer_filling(df_fill_hex=df_fill_compact,
                                                map_initial=map_district,
                                                fillcolor=fillcolor)

    folium.map.LayerControl('bottomright', collapsed=True).add_to(map_fill_compact)
    return map_fill_compact


if __name__ == '__main__':
    input_file_districts = sys.argv[1]
    size = int(sys.argv[2])
    output_path = 'test-' + sys.argv[2] + '.html'
    gdf_districts = load_and_prepare_districts(filepath=input_file_districts)

    gdf_districts["hex_fill_initial"] = gdf_districts["geom_swap_geojson"].apply(
        lambda x: list(fill_hexagons(geom_geojson=x,
                                     res=size))
    )
    gdf_districts["num_hex_fill_initial"] = gdf_districts["hex_fill_initial"].apply(len)
    total_num_hex_initial = gdf_districts["num_hex_fill_initial"].sum()
    print("Until here, we'd have to search over {} hexagons".format(total_num_hex_initial))
    gdf_districts["uncompacted_novoids"] = [[] for _ in range(gdf_districts.shape[0])]

    visualize_district_filled_compact(gdf_districts=gdf_districts).save(output_path)
