import json
import pandas as pd
import os

input_dir = "../dataset/json/"
output_dir = "../output/csv/"

if __name__ == '__main__':
    files = os.listdir(input_dir)
    count = 0
    df_list = []
    for file in files:
        count += 1
        with open(input_dir + "req" + str(count).zfill(2) + ".json", 'r') as load_f:
            load_dict = json.load(load_f)
            elevation_list = []
            for item in load_dict["results"]:
                elevation_list.append(item["elevation"])
            ele_dict = {"elevation": elevation_list}
            df_unit = pd.DataFrame(ele_dict)
            df_list.append(df_unit)
    df_ele = pd.concat(df_list, ignore_index=True)
    df_hex = pd.read_csv(output_dir + "hex.csv")
    df_total = pd.concat([df_hex, df_ele], axis=1)
    df_total.to_csv(output_dir + "elevation.csv", index=False)