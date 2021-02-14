# In our model, the elevation of each hexagonal area is considered equal to the
# elevation of its center of gravity, obtained through Google Maps API. This
# file is used to generate commands to access Google Maps API with curl. The
# Google Maps API limits the length of each request to no more than 1850 bytes
# and no more than 512 requested locations. To enable this API, you should
# register on https://developers.google.com/maps first and replace the variable
# `key` in the code with your own API key.

import h3
import pandas as pd

input_dir = "../output/"
output_dir = "../output/"
loc_per_req = 450


def req_header(total):
    """Determine the save name of the file and generate the common request header"""
    part_1 = "curl -o req"
    part_2 = ".json \"https://maps.googleapis.com/maps/api/elevation/json?locations="
    return part_1 + str(total // loc_per_req + 1).zfill(2) + part_2


if __name__ == '__main__':
    accuracy = 4
    resolution = 7
    key = "Register_with_Google_Map_Elevation_API"  # API key to replace

    hex_df = pd.read_csv(input_dir + "csv/hex.csv")

    # Obtain the barycenter coordinates of each hexagonal area through the h3 API
    hex_df["center"] = hex_df["hex_id"].apply(h3.h3_to_geo)
    hex_df["lat"] = hex_df["center"].apply(lambda x: round(x[0], accuracy))
    hex_df["lng"] = hex_df["center"].apply(lambda x: round(x[1], accuracy))

    # Check whether rounding will cause the barycenter to leave its h3 hexagon
    hex_df["check"] = hex_df.apply(lambda x: h3.geo_to_h3(lat=x["lat"], lng=x["lng"], resolution=resolution))
    if hex_df["hex_id"] != hex_df["check"]:
        print("Higher accuracy is needed !!!")
        exit(1)

    to_write = open(output_dir + "tmp/req_line.txt", "w")
    req_body = ""
    req_tail = "&key=" + key + "\"\n"
    count = 0
    for index, row in hex_df.iterrows():
        unit = str(row["lat"]) + "," + str(row["lng"])
        if count % loc_per_req == 0:
            if count:
                to_write.write(req_header(count) + req_body + req_tail)
                req_body = ""
        else:
            req_body += "|"
        req_body += unit
        count += 1
    to_write.write(req_header(count) + req_body + req_tail)
    to_write.close()
