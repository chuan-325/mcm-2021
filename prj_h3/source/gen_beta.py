import h3
import pandas as pd
import numpy as np

input_dir = "../output/csv/"
output_dir = "../output/csv/"
df_hex = pd.read_csv(input_dir + "elevation.csv")


def calculate_gradient(center, base, idx):
    neighbor = list(h3.k_ring_distances(center, 1)[1])
    max_beta = 0
    for hex in neighbor:
        gradient = np.array(df_hex[df_hex["hex_id"] == hex]).tolist()
        # print(hex_ele)
        if len(gradient):
            difference = abs(base - gradient[0][idx])
            if difference > max_beta:
                max_beta = difference
    return max_beta


if __name__ == '__main__':
    df_hex["slope"] = df_hex.apply(lambda x: calculate_gradient(x["hex_id"], x["elevation"], 1), axis=1)
    df_hex["B_value"] = df_hex.apply(lambda x: calculate_gradient(x["hex_id"], x["slope"], 2), axis=1)
    df_hex = df_hex[["hex_id", "B_value"]]
    df_hex.to_csv(output_dir + "beta.csv", index=False)
