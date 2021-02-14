# This file is used to calculate the value of s. Only fires with a confidence level higher than 0.8
# will be counted. Finally, the total number of fires in each h3 hexagonal area in Australia per year
# is obtained, and the s value of each h3 hexagonal area is calculated in turn

import h3
import pandas as pd
import math

input_dir = "../dataset/fire/"
output_dir = "../output/csv/"


def calculate_s(a1, a2, a3, a4, a5):
    """Calculate the value of s basing on the fire data from the past five years"""
    epsilon = 1.5
    w_sum = (math.pow(epsilon, 1.0 / 5.0) * a5 + math.pow(epsilon, 1.0 / 4.0) * a4 + math.pow(epsilon,
                                                                                              1.0 / 3.0) * a3 + math.pow(
        epsilon, 1.0 / 2.0) * a2 + epsilon * a1) / 23.0
    value = math.log(w_sum + 1) / 3.0 + 1
    return value


def select_reliable_fire(year):
    """Load the fire data of a single year and reserve rows with confidence higher than 0.8 .
    Calculate the h3 hexagon where the remaining fire occurred based on the latitude and longitude,
    and return it after merging."""
    raw_file = input_dir + "modis_" + year + "_Australia.csv"
    df_raw = pd.read_csv(raw_file, sep=',')
    df_sel = df_raw[df_raw["confidence"] >= 80].reset_index(drop=True)
    df_sel = df_sel[["latitude", "longitude"]]
    df_sel["hex_id"] = df_sel.apply(
        lambda row: h3.geo_to_h3(
            lat=row["latitude"],
            lng=row["longitude"],
            resolution=7),
        axis=1)
    print("A total of {} fire data are counted".format(df_sel.shape[0]))
    df_count = pd.DataFrame(df_sel["hex_id"].value_counts())
    df_count = df_count.reset_index()
    fire_column = "fire_" + year
    df_count.columns = ["hex_id", fire_column]
    return df_count


if __name__ == '__main__':
    year_set = ['2015', '2016', '2017', '2018', '2019']
    df = pd.DataFrame(columns=["hex_id"])
    for year in year_set:
        df = pd.merge(df, select_reliable_fire(year), how="outer", on="hex_id")
    df.fillna(0, inplace=True)
    df["S_value"] = df.apply(
        lambda x: calculate_s(x["fire_2019"], x["fire_2018"], x["fire_2017"], x["fire_2016"], x["fire_2015"], ), axis=1)
    df[["hex_id", "S_value"]].to_csv(output_dir + "s_value.csv", index=False)
