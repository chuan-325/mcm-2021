import h3
from geojson.feature import *
import geopandas as gpd
from shapely import geometry
from folium import Map, GeoJson
import folium
import branca.colormap as cm
import json
import pandas as pd

input_dir = "../dataset/"
output_dir = "../output/"


def load_and_prepare_gdf(filepath):
    gdf = gpd.read_file(filepath, driver="GeoJSON")
    gdf.head()
    gdf["geom_geojson"] = gdf["geometry"].apply(lambda x: geometry.mapping(x))
    return gdf


def calculate_u(h):
    if h <= 800.0:
        return 0.0
    else:
        res = (h - 800.0) * 0.00000868
        return res


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
                'opacity': 0.5,
                'weight': 3,
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


def generate_s_value():
    df_s = pd.read_csv(output_dir + "csv/s_value.csv")
    return df_s


def generate_f_value():
    gdf_raw = pd.read_csv(output_dir + "csv/forest.csv")
    gdf_raw["F_value"] = 0.58
    return gdf_raw


def generate_value(df_hex, mode):
    df_ele = pd.read_csv(output_dir + "csv/elevation.csv")
    df_hex = pd.merge(df_hex, df_ele, on="hex_id")
    if mode == "heat-1" or mode == "heat-3":
        s_value = generate_s_value()
        df_hex = pd.merge(df_hex, s_value, on="hex_id", how="left")
        f_value = generate_f_value()
        df_hex = pd.merge(df_hex, f_value, on="hex_id", how="left")
        df_hex.fillna(0, inplace=True)
        if mode == "heat-1":
            df_hex["value"] = df_hex.apply(lambda x: x["S_value"] * x["F_value"], axis=1)
        else:
            df_hex["H_value"] = df_hex["elevation"].apply(calculate_u)
            # print(df_hex)
            df_beta = pd.read_csv("beta.csv")
            df_hex = pd.merge(df_hex, df_beta, on="hex_id", how="left")
            df_hex["value"] = df_hex.apply(lambda x: (x["S_value"] + x["H_value"] * x["B_value"]) * x["F_value"],
                                           axis=1)
    elif mode == "elevation":
        df_ele.columns = ["hex_id", "value"]
        df_hex = pd.merge(df_hex, df_ele, on="hex_id")
    else:
        df_hex["value"] = 1
    df_valued = df_hex[["hex_id", "value"]]
    # print(df_hex)
    return df_valued


def choropleth_map(df_aggreg, hex_id_field, geometry_field, value_field,
                   layer_name, initial_map=None, kind="filled_nulls",
                   border_color='#ffffff', fill_opacity=0.4,
                   border_opacity=0.3, with_legend=False):
    """Plots a choropleth map with folium"""

    if initial_map is None:
        initial_map = base_empty_map()

    # the custom colormap depends on the map kind
    if kind == "linear":
        min_value = df_aggreg[value_field].min()
        max_value = df_aggreg[value_field].max()
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
        # m = round((min_value + max_value) / 2, 0)
        m = (min_value + max_value) / 2.0
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
            'opacity': border_opacity,
            'weight': 0.2,
            'fillOpacity': fill_opacity
        },
        name=layer_name
    ).add_to(initial_map)

    # add legend (not recommended if multiple layers)
    if with_legend is True:
        custom_cm.add_to(initial_map)

    return initial_map


def set_range_plain(original_map, color):
    center_list = [(-37.362157, 148.579852), (-37.190834, 148.232456), (-37.458542, 148.190546),
                   (-37.382846, 147.752364), (-37.640824, 148.026425)]
    for center in center_list:
        folium.Circle(location=center,
                      color=color,
                      radius=20000,
                      fill_color=color,
                      fillOpacity=0.2).add_to(original_map)
    return original_map


def set_range_forest(original_map, color):
    center_list = [(-36.722421, 146.777949), (-36.888024, 147.523976), (-36.892515, 147.124482),
                   (-36.910543, 147.316754), (-36.759834, 147.259824), (-37.044143, 147.202352),
                   (-36.783415, 147.400954), (-37.041345, 147.025425), (-37.173534, 147.159656),
                   (-37.172845, 147.345787), (-37.043256, 147.426565), (-36.873454, 146.903554)]
    for center in center_list:
        folium.Circle(location=center,
                      color=color,
                      radius=10000,
                      fill_color=color,
                      fillOpacity=0.2).add_to(original_map)
    return original_map


def set_range_urban(original_map, color):
    center_list = [(-37.730532, 145.096356), (-37.664546, 145.089435)]
    for center in center_list:
        folium.Circle(location=center,
                      color=color,
                      radius=5000,
                      fill_color=color,
                      fillOpacity=0.2).add_to(original_map)
    return original_map


if __name__ == '__main__':
    map_type = "heat-3"
    output_file = output_dir + "html/" + map_type + ".html"
    color_plain = "c295ff"
    color_forest = "a464fc"
    color_urban = "8936fb"

    gdf = load_and_prepare_gdf(input_dir + "victoria.geojson")
    map_boundary = plot_basemap_region_fill(gdf)

    hex_df = pd.read_csv(output_dir + "csv/hex.csv")
    hex_df = generate_value(df_hex=hex_df, mode=map_type)
    sorted_df = hex_df.sort_values(by="value", ascending=False).reset_index(drop=True)
    sorted_df.to_csv(output_dir + "csv/valued.csv", index=False)
    print(sorted_df["value"].sum())
    hex_df["geometry"] = hex_df["hex_id"].apply(
        lambda x: {"type": "Polygon",
                   "coordinates":
                       [h3.h3_to_geo_boundary(
                           h=x, geo_json=True)]
                   }
    )
    m_hex = choropleth_map(initial_map=map_boundary,
                           df_aggreg=hex_df,
                           hex_id_field="hex_id",
                           geometry_field="geometry",
                           value_field="value",
                           layer_name="Choropleth",
                           with_legend=True)
    # m_hex = set_range_plain(m_hex, color_plain)
    # m_hex = set_range_forest(m_hex, color_forest)
    # m_hex = set_range_urban(m_hex, color_urban)
    m_hex.save(output_file)
