import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import xarray as xr
import numpy as np
from functools import lru_cache
from data_sets import DATASETS




app = FastAPI(openapi_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
    max_age=600,
)

USE_S3 = os.environ.get("USE_S3", "false").lower() == "true"

# ── 開啟 Zarr 檔案 ────────────────────────────────────────────
@lru_cache(maxsize=10)
def open_zarr(zarr_name: str) -> xr.Dataset:
    if USE_S3:
        import s3fs
        S3_BUCKET = os.environ.get("S3_BUCKET", "my-climate-data-2024")
        S3_REGION = os.environ.get("S3_REGION", "ap-northeast-1")
        fs    = s3fs.S3FileSystem(
            anon=False,
            client_kwargs={"region_name": S3_REGION}
        )
        store = s3fs.S3Map(root=f"{S3_BUCKET}/data/{zarr_name}.zarr", s3=fs)
        return xr.open_dataset(store, engine="zarr")
    else:
        return xr.open_dataset(f"data/{zarr_name}.zarr", engine="zarr")

# ── Health Check ──────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok"}

# ── 列出資料集（給前端知道哪些有資料）────────────────────────
@app.get("/datasets")
async def get_datasets():
    result = {}
    for key, ds in DATASETS.items():
        result[key] = {
            "label":        ds["label"],
            "available":    ds["zarr_file"] is not None,  # 是否有資料
            "has_time":     ds["has_time"],
            "variables":    ds["variables"],
            "color_group1": ds["color_group1"],
            "color_group2": ds["color_group2"],
            "ts_style":     ds["ts_style"],
        }
    return result

# ── 點查詢（無 time）→ Bar Plot ───────────────────────────────
@app.get("/query/{dataset_id}/point")
async def query_point(
    dataset_id: str,
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
):
    if dataset_id not in DATASETS:
        raise HTTPException(404, "Dataset not found")

    ds_config = DATASETS[dataset_id]

    if ds_config["zarr_file"] is None:
        raise HTTPException(503, f"{ds_config['label']} data not available yet")

    if ds_config["has_time"]:
        raise HTTPException(400, "This dataset has time dimension")

    ds     = open_zarr(ds_config["zarr_file"])
    result = {}

    for var in ds_config["variables"]:
        val = float(
            ds[var].sel(lat=lat, lon=lon, method="nearest").values
        )
        # ← 處理 NaN / inf
        if np.isnan(val) or np.isinf(val) or val <= -999:
            result[var] = None
        else:
            result[var] = round(val, 4)

    return {
        "mode":      "point",
        "dataset":   dataset_id,
        "label":     ds_config["label"],
        "lat":       lat,
        "lon":       lon,
        "values":    result,
        "colors_g1": ds_config["color_group1"],
        "colors_g2": ds_config["color_group2"],
    }
    

# ── 單年查詢（有 time）→ Bar Plot ────────────────────────────
@app.get("/query/{dataset_id}/year")
async def query_year(
    dataset_id: str,
    lat:  float = Query(..., ge=-90, le=90),
    lon:  float = Query(..., ge=-180, le=180),
    year: int   = Query(...),
):
    if dataset_id not in DATASETS:
        raise HTTPException(404, "Dataset not found")

    ds_config = DATASETS[dataset_id]

    if ds_config["zarr_file"] is None:
        raise HTTPException(503, f"{ds_config['label']} data not available yet")

    ds     = open_zarr(ds_config["zarr_file"])
    result = {}

    for var in ds_config["variables"]:
        val = float(
            ds[var].sel(lat=lat, lon=lon, method="nearest")
                   .sel(time=year, method="nearest").values
        )
        result[var] = round(val, 4)

    return {
        "mode":      "single_year",
        "dataset":   dataset_id,
        "label":     ds_config["label"],
        "lat":       lat,
        "lon":       lon,
        "year":      year,
        "values":    result,
        "colors_g1": ds_config["color_group1"],
        "colors_g2": ds_config["color_group2"],
    }

# ── 時間序列（有 time）→ Line Chart ──────────────────────────
@app.get("/query/{dataset_id}/timeseries")
async def query_timeseries(
    dataset_id:  str,
    lat:         float = Query(..., ge=-90, le=90),
    lon:         float = Query(..., ge=-180, le=180),
    start_year:  int   = Query(...),
    end_year:    int   = Query(...),
):
    if dataset_id not in DATASETS:
        raise HTTPException(404, "Dataset not found")

    if start_year >= end_year:
        raise HTTPException(400, "start_year must be less than end_year")

    ds_config = DATASETS[dataset_id]

    if ds_config["zarr_file"] is None:
        raise HTTPException(503, f"{ds_config['label']} data not available yet")

    ds     = open_zarr(ds_config["zarr_file"])
    result = {}

    for var in ds_config["variables"]:
        data = (
            ds[var].sel(lat=lat, lon=lon, method="nearest")
                   .sel(time=slice(start_year, end_year))
        )
        result[var] = {
            "times":  [int(t) for t in data["time"].values],
            "values": [round(float(v), 4) for v in data.values],
            "min":    round(float(data.min()), 4),
            "max":    round(float(data.max()), 4),
        }

    return {
        "mode":       "timeseries",
        "dataset":    dataset_id,
        "label":      ds_config["label"],
        "lat":        lat,
        "lon":        lon,
        "start_year": start_year,
        "end_year":   end_year,
        "ts_style":   ds_config["ts_style"],
        "variables":  result,
        "colors":     ds_config["color_group1"] + ds_config["color_group2"],
    }

# ── 格點覆蓋層（給地圖顯示有資料的區域）─────────────────────
@app.get("/query/{dataset_id}/grid")
async def query_grid(
    dataset_id: str,
    downsample: int = Query(15),
):
    if dataset_id not in DATASETS:
        raise HTTPException(404, "Dataset not found")

    ds_config = DATASETS[dataset_id]

    if ds_config["zarr_file"] is None:
        raise HTTPException(503, "Data not available yet")

    ds = open_zarr(ds_config["zarr_file"])

    # topo 不參與判斷
    check_vars = ["flood100","flood50","flood25",
                  "surge100","surge50","surge25"]

    sample   = ds[check_vars[0]][::downsample, ::downsample]
    lons     = [round(float(v), 4) for v in sample.lon.values]
    lats     = [round(float(v), 4) for v in sample.lat.values]

    has_data = np.zeros((len(lons), len(lats)), dtype=bool)

    for var in check_vars:
        data = ds[var][::downsample, ::downsample].values
        # 任何一個變數 > 0 才算有資料
        valid    = ~np.isnan(data) & ~np.isinf(data) & (data > 0)
        has_data = has_data | valid

    result = []
    for i in range(len(lons)):
        row = []
        for j in range(len(lats)):
            row.append(bool(has_data[i, j]))
        result.append(row)

    return {
        "lons":     lons,
        "lats":     lats,
        "has_data": result,
    }


# ── Fragility: 所有 AST 點位 ──────────────────────────────────
@app.get("/fragility/points")
async def get_fragility_points():
    if _ast_points_cache is None:
        raise HTTPException(503, "Fragility data not ready yet")
    return _ast_points_cache

    ds = open_zarr(ds_config["zarr_file"])

    lats    = ds.Latitude.values
    lons    = ds.Longitude.values
    ids     = ds.AST_ID.values
    types   = ds.Type.values
    heights = ds.Height.values

    points = []
    for i in range(len(ids)):
        pf = ds.Pf_System_[i].values
        sv = ds.Spill_Volume_[i].values
        points.append({
            "ast_id":  int(ids[i]),
            "lat":     round(float(lats[i]), 6),
            "lon":     round(float(lons[i]), 6),
            "type":    str(types[i]),
            "height":  round(float(heights[i]), 2),
            "pf_mean": round(float(np.mean(pf)), 6),
            "pf_std":  round(float(np.std(pf)),  6),
            "sv_mean": round(float(np.mean(sv)), 4),
            "sv_std":  round(float(np.std(sv)),  4),
        })

    return {"points": points, "count": len(points)}

# ── Fragility: 單一 AST 詳細（點擊圓點）──────────────────────
@app.get("/fragility/ast/{ast_id}")
async def get_ast_detail(ast_id: int):
    ds_config = DATASETS["fragility"]
    if ds_config["zarr_file"] is None:
        raise HTTPException(503, "Fragility data not available yet")

    ds  = open_zarr(ds_config["zarr_file"])
    ids = ds.AST_ID.values
    idx = np.where(ids == ast_id)[0]

    if len(idx) == 0:
        raise HTTPException(404, f"AST_ID {ast_id} not found")

    i  = idx[0]
    pf = ds.Pf_System_[i].values
    sv = ds.Spill_Volume_[i].values

    return {
        "ast_id": ast_id,
        "lat":    round(float(ds.Latitude[i].values),  6),
        "lon":    round(float(ds.Longitude[i].values), 6),
        "type":   str(ds.Type[i].values),
        "height": round(float(ds.Height[i].values), 2),
        "pf": {
            "mean": round(float(np.mean(pf)), 6),
            "std":  round(float(np.std(pf)),  6),
        },
        "sv": {
            "mean": round(float(np.mean(sv)), 4),
            "std":  round(float(np.std(sv)),  4),
        },
    }


# ── 啟動時預建 AST 快取 ───────────────────────────────────────
_ast_points_cache = None

def build_ast_cache():
    global _ast_points_cache
    try:
        ds      = open_zarr("fragility_1942")
        lats    = ds.Latitude.values
        lons    = ds.Longitude.values
        ids     = ds.AST_ID.values
        types   = ds.Type.values
        heights = ds.Height.values

        pf_all  = ds.Pf_System_.values    # (5979, 1000)
        sv_all  = ds.Spill_Volume_.values # (5979, 1000)

        pf_mean = np.mean(pf_all, axis=1)
        pf_std  = np.std(pf_all,  axis=1)
        sv_mean = np.mean(sv_all, axis=1)
        sv_std  = np.std(sv_all,  axis=1)

        points = []
        for i in range(len(ids)):
            points.append({
                "ast_id":  int(ids[i]),
                "lat":     round(float(lats[i]), 6),
                "lon":     round(float(lons[i]), 6),
                "type":    str(types[i]),
                "height":  round(float(heights[i]), 2),
                "pf_mean": round(float(pf_mean[i]), 6),
                "pf_std":  round(float(pf_std[i]),  6),
                "sv_mean": round(float(sv_mean[i]), 4),
                "sv_std":  round(float(sv_std[i]),  4),
            })

        _ast_points_cache = {"points": points, "count": len(points)}
        print(f"✓ AST cache built: {len(points)} points")

    except Exception as e:
        print(f"⚠ AST cache failed: {e}")

# 程式啟動時執行
build_ast_cache()
