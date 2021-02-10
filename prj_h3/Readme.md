# H3 Project for MCM-2021

## Directory Guide

- `backup/` : Backup of original results
- `dataset/` : Raw data used in this project
    - `dataset/fire/` : 2015 - 2019 fire statistics in Australia, download from NASA
    - `dataset/json/` : Elevation `json` files, via Google Map Elevation API
    - `dataset/forest.tiff` : Boundary of forests in Australia, download from `https://data.gov.au/`
    - `dataset/vitoria.geojson` : Boundary of Victoria, from download from `http://polygons.openstreetmap.fr/`
- `env/` : Environment configuration file exported from conda
- `output/` : All results will be saved here
- `source/` : Source code of this project

## Environment Setup

Make sure you have installed `Conda` first.

When you're currently under the directory `prj_h3`, you can setup the necessary environment easily with the command below:
``` shell script
conda env create -f env/environment.yaml
```

## Execution Tips

Remain to complete ...
