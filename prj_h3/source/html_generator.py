import h3
import geopandas as gpd
from shapely import geometry, ops
from geojson.feature import *
from folium import Map, GeoJson
import folium
import branca.colormap as cm

import sys
import json
import pandas as pd


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


def convert_to_hex_df(gdf, col):
    hex_id = []
    for index, row in gdf.iterrows():
        hex_id.extend(row[col])
    hex_dict = {"hex_id": hex_id}
    hex_df_res = pd.DataFrame(hex_dict)
    return hex_df_res


def choropleth_map(df_aggreg, hex_id_field, geometry_field, value_field,
                   layer_name, initial_map=None, kind="linear",
                   border_color='black', fill_opacity=0.4,
                   with_legend=False):
    """Plots a choropleth map with folium"""

    if initial_map is None:
        initial_map = base_empty_map()

    # the custom colormap depends on the map kind
    if kind == "linear":
        min_value = df_aggreg[value_field].min()
        max_value = df_aggreg[value_field].max()
        m = round((min_value + max_value) / 2, 0)
        custom_cm = cm.LinearColormap(['green', 'yellow', 'red'],
                                      vmin=min_value,
                                      vmax=max_value)
    elif kind == "outlier":
        # for outliers, values would be -1,0,1
        custom_cm = cm.LinearColormap(['blue', 'white', 'red'],
                                      vmin=-1, vmax=1)
    elif kind == "filled_nulls":
        min_value = df_aggreg[df_aggreg[value_field] > 0][value_field].min()
        max_value = df_aggreg[df_aggreg[value_field] > 0][value_field].max()
        m = round((min_value + max_value) / 2, 0)
        custom_cm = cm.LinearColormap(['silver', 'green', 'yellow', 'red'],
                                      index=[0, min_value, m, max_value],
                                      vmin=min_value,
                                      vmax=max_value)
    else:
        custom_cm = None

    # create geojson data from dataframe
    geojson_data = hexagons_dataframe_to_geojson(df_aggreg, hex_id_field,
                                                 geometry_field, value_field)
    # plot on map
    GeoJson(
        geojson_data,
        style_function=lambda feature: {
            'fillColor': custom_cm(feature['properties']['value']),
            'color': border_color,
            'weight': 1,
            'fillOpacity': fill_opacity
        },
        name=layer_name
    ).add_to(initial_map)

    # add legend (not recommended if multiple layers)
    if with_legend is True:
        custom_cm.add_to(initial_map)

    return initial_map


def generate_heat_map(gdf):
    hex_df = convert_to_hex_df(gdf=gdf, col="hex_fill")
    hex_df["geometry"] = hex_df["hex_id"].apply(
        lambda x: {"type": "Polygon",
                   "coordinates":
                       [h3.h3_to_geo_boundary(
                           h=x, geo_json=True)]
                   }
    )
    hex_df["value"] = 0
    temp = 0
    for index, row in hex_df.iterrows():
        row["value"] = temp // 500
        hex_df.iloc[index] = row
        temp += 1
    print(hex_df.head())
    m_hex = choropleth_map(df_aggreg=hex_df,
                           hex_id_field="hex_id",
                           geometry_field="geometry",
                           value_field="value",
                           layer_name="Choropleth",
                           with_legend=True)
    return m_hex


if __name__ == '__main__':
    input_file = sys.argv[1]
    resolution = int(sys.argv[2])
    output_file = 'test-' + sys.argv[2] + '.html'
    gdf = load_and_prepare_gdf(filepath=input_file)

    gdf["hex_fill"] = gdf["geom_swap_geojson"].apply(
        lambda x: list(fill_hexagons(geom_geojson=x,
                                     res=resolution))
    )
    gdf["num_hex_fill"] = gdf["hex_fill"].apply(len)
    gdf = gdf[gdf["num_hex_fill"] > 0].reset_index(drop=True)
    total_num_hex = gdf["num_hex_fill"].sum()
    print("A total of {} hexagons are used to cover the map".format(total_num_hex))

    generate_heat_map(gdf).save(output_file)
