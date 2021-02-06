#!/usr/bin/python
# -*- coding:utf-8 -*-
# author: zheng
# datetime: 2021/2/6 16:31
# software: PyCharm

import geojson
import numpy as np
import pygeohash as pgh
from matplotlib.path import Path
import matplotlib.pyplot as plt


# 单块 polygon 地图画布 (board)
def div_board(lat_list, lon_list):
    # 获取最值
    lat_max = np.max(lat_list)
    lat_min = np.min(lat_list)
    lon_max = np.max(lon_list)
    lon_min = np.min(lon_list)
    # 枚举划分/步长：
    accu = 0.1
    board_lat = []
    board_lon = []
    board_idx = []
    # 存储所有划分的出来的区域的编码
    for lat_i in np.arange(lat_min, lat_max, accu):
        for lon_i in np.arange(lon_min, lon_max, accu):
            c = pgh.encode(lat_i, lon_i)
            a, b = pgh.decode(c)
            board_lat.append(a)
            board_lon.append(b)
            board_idx.append(c)
    return board_lon, board_lat, board_idx


# 以适中精度处理 get division of certain level
def get_lonlat_zt(total):
    new_total = []  # 全部的多级编码
    for bit in total:  # 得到的前 n 位全部的编码
        new_total.append(bit[:5])  # n=para-1 => (para-1)级分区
    new_total = list(set(new_total))  # 编码去重
    new_total_lonlat = []
    for block in new_total:
        lat_zt, lon_zt = pgh.decode(block)
        new_total_lonlat.append([lon_zt, lat_zt])
    return new_total_lonlat


# 输入 board_idx
# 输出精度处理后的 [lon, lat] lon lat
def match_zt(total):
    new_total_lonlat = get_lonlat_zt(total)
    all_central_point = new_total_lonlat
    new_total_lon = []
    new_total_lat = []
    for point in all_central_point:
        new_total_lon.append(point[0])
        new_total_lat.append(point[1])
    return all_central_point, new_total_lon, new_total_lat


# 输入line_t
# 输出以且仅以它的每个元素为中点的序列 list
# 0, 1, 2, 3
# => -0.5, .5, 1.5, 2.5, 3.5
def avg_acquire(line_t):
    avg = []
    for l_i in range(len(line_t) - 1):
        avg.append((line_t[l_i] + line_t[l_i + 1]) / 2)
    sub_t = abs(line_t[0] - line_t[1]) / 2
    avg.insert(0, line_t[0] - sub_t)
    avg.append(line_t[len(line_t) - 1] + sub_t)
    return avg


# 输入 lon/lat list
# 输出经过 avg_acquire 毒打的 lon, lat
def border_point_zt(lon, lat):
    line_lon = list(set(lon[:]))  # 画出分区点的经度
    line_lat = list(set(lat[:]))  # 画出分区点的纬度
    line_lon.sort()
    line_lat.sort()
    avg_lon = avg_acquire(line_lon)
    avg_lat = avg_acquire(line_lat)
    avg_lat.sort()
    avg_lon.sort()
    return avg_lon, avg_lat


# 获得分域信息 dict
# 输入中心点、avg 的 lon/lat 序列
# 输出分域信息 dict: key 为中心点坐标，value 为方形区域 4 顶点
def get_dict(central_points, avg_lon, avg_lat):
    point_dict = {}
    # 区域的长、宽到中心点的最短距离，由于误差值相同，故该最短距离相同。
    lon_var = (avg_lon[1] - avg_lon[0]) / 2
    lat_var = (avg_lat[1] - avg_lat[0]) / 2
    # 构建字典
    for central_point in central_points:
        border_points = []
        lon = [central_point[0] + lon_var, central_point[0] - lon_var]
        lat = [central_point[1] + lat_var, central_point[1] - lat_var]
        for lon in lon:
            for lat in lat:
                border_points.append([lon, lat])
        point_dict[str(central_point)] = border_points
    return point_dict


# 得到边界
# 输入 polygon [[]]
# 输出 Path
def get_edge(graph):
    a = []
    for point in graph:
        a.append(tuple(point))
    p = Path(a)
    return p


# 筛选在 Path 内的中心点
# 输入 分域 dict， 边点 list
# 输出 新分域 dict， 边点 list， 满足条件的中心点集合
"""
def match(dict_p, graph_p):
    p = get_edge(graph_p)
    match_point1 = []
    match_point2 = []
    new_dict = {}
    # 遍历每一个键
    for key in dict_p.keys():
        flag = 0
        # 遍历该 key 存储的每一个坐标
        for item in dict_p[key]:
            if p.contains_point(item):
                flag = 1
        # 该 key 中存储的坐标中存在 Path 内的点
        if flag == 1:
            a = key[1:-1].split(",")
            for k in range(len(a)):
                a[k] = float(a[k])
            match_point1.append(a)
            for key_j in dict_p[key]:
                match_point2.append(key_j)
            new_dict[str(a)] = dict_p[key]
    return match_point1, match_point2, new_dict
"""

if __name__ == "__main__":
    # json => multipolygon[]
    vbList = []
    with open('../data/victoria.geojson') as vbJson:
        vbList.append(geojson.load(vbJson).geometries[0].coordinates)

    # multipolygon => polygons
    polygon_cdnts = []
    for i in range(len(vbList)):
        polygon_cdnts.append(vbList[i][0])

    # polygons => polygons' lon, lat, idx
    polygon_lon = []
    polygon_lat = []
    polygon_idx = []
    for i in range(len(polygon_cdnts)):
        xList = []
        yList = []
        pList = []
        for j in range(len(polygon_cdnts[i])):
            xList.append(polygon_cdnts[i][j][0])
            yList.append(polygon_cdnts[i][j][1])
            pList.append(pgh.encode(xList[j], yList[j]))
        polygon_lon.append(xList)
        polygon_lat.append(yList)
        polygon_idx.append(pList)

    plg_board_lon = []
    plg_board_lat = []
    plg_board_idx = []

    for i in range(len(polygon_cdnts)):
        t_lon, t_lat, t_idx = div_board(polygon_lat[i], polygon_lon[i])
        plg_board_lon.append(t_lon)
        plg_board_lat.append(t_lat)
        plg_board_idx.append(t_idx)

# mat.figure(dpi=200)
# plt.plot(x, y, lw=0.1)
# plt.show()
