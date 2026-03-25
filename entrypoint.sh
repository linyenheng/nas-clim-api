#!/bin/bash
set -e

mkdir -p data

# Wave Surge data
if [ ! -d "data/return_water_levels.zarr" ]; then
    echo "==> Extracting wave surge data..."
    tar -xzf return_water_levels.tar.gz -C data/
    rm return_water_levels.tar.gz
fi

# Fragility data
if [ ! -d "data/fragility_1942.zarr" ]; then
    echo "==> Extracting fragility data..."
    tar -xzf fragility_1942.tar.gz -C data/
    rm fragility_1942.tar.gz
fi

# check and start 
echo "==> Starting API..."
ls -la data/

uvicorn main:app --host 0.0.0.0 --port 8080
