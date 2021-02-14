# In our project, beta represents the difference of maximum elevation difference (that is:
# the second-order norm of elevation), which is calculated by this file. More generally, this
# script supports the calculation of any order norm of the specified attribute value of the
# h3 hexagon.

import h3
import pandas as pd
import numpy as np

input_dir = "../output/csv/"
output_dir = "../output/csv/"
df_hex = pd.read_csv(input_dir + "elevation.csv")


def calculate_gradient(center, base):
    """Calculate the maximum difference between the central
    hexagon and its six adjacent hexagons in the `base` value"""
    neighbor = list(h3.k_ring_distances(center, 1)[1])
    max_beta = 0
    for hex in neighbor:
        gradient = np.array(df_hex[df_hex["hex_id"] == hex]).tolist()
        if len(gradient):
            difference = abs(base - gradient[0][1])
            if difference > max_beta:
                max_beta = difference
    return max_beta


if __name__ == '__main__':
    df_hex["slope"] = df_hex.apply(lambda x: calculate_gradient(x["hex_id"], x["elevation"]), axis=1)
    df_hex = df_hex[["hex_id", "slope"]]
    df_hex["B_value"] = df_hex.apply(lambda x: calculate_gradient(x["hex_id"], x["slope"]), axis=1)
    df_hex = df_hex[["hex_id", "B_value"]]
    df_hex.to_csv(output_dir + "beta.csv", index=False)
