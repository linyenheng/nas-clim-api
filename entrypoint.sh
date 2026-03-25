#!/bin/bash
set -e

mkdir -p data

# Wave Surge 資料
if [ ! -d "data/return_water_levels.zarr" ]; then
    echo "==> Extracting wave surge data..."
    tar -xzf return_water_levels.tar.gz -C data/
    rm return_water_levels.tar.gz
fi


# Fragility 資料
if [ ! -d "data/fragility_1942.zarr" ]; then
    echo "==> Downloading fragility data from Google Drive..."

    # 用 wget 下載（比 gdown 更穩定處理大檔案）
    wget --load-cookies /tmp/cookies.txt \
      "https://drive.google.com/uc?export=download&id=1sAjUQBmdwELxSWuwmVcKg1dvrC_FjS5q&confirm=$(
        wget --quiet --save-cookies /tmp/cookies.txt --keep-session-cookies \
          --no-check-certificate \
          'https://drive.google.com/uc?export=download&id=1sAjUQBmdwELxSWuwmVcKg1dvrC_FjS5q' \
          -O- | sed -rn 's/.*confirm=([0-9A-Za-z_]+).*/\1/p'
      )" \
      -O data/fragility_1942.tar.gz

    echo "==> Download size:"
    du -sh data/fragility_1942.tar.gz

    echo "==> Extracting fragility data..."
    tar -xzf data/fragility_1942.tar.gz -C data/
    rm data/fragility_1942.tar.gz
    echo "==> Fragility data ready!"
fi

echo "==> Starting API..."
uvicorn main:app --host 0.0.0.0 --port 8080
