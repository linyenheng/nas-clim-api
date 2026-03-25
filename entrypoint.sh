#!/bin/bash
set -e

mkdir -p data

# Wave Surge 資料
if [ ! -d "data/return_water_levels.zarr" ]; then
    echo "==> Extracting wave surge data..."
    tar -xzf return_water_levels.tar.gz -C data/
    rm return_water_levels.tar.gz
fi

# Fragility 資料（從 Google Drive 下載）
if [ ! -d "data/fragility_1942.zarr" ]; then
    echo "==> Downloading fragility data from Google Drive..."
    gdown "1sAjUQBmdwELxSWuwmVcKg1dvrC_FjS5q" -O data/fragility_1942.tar.gz
    echo "==> Extracting fragility data..."
    tar -xzf data/fragility_1942.tar.gz -C data/
    rm data/fragility_1942.tar.gz
    echo "==> Fragility data ready!"
fi

echo "==> Starting API..."
uvicorn main:app --host 0.0.0.0 --port 8080
