S3_BUCKET = "my-climate-data-2024"
S3_REGION = "ap-northeast-1"

DATASETS = {
    # ── Wave Surge（有資料）────────────────────────────────
    "wave_surge": {
        "label":    "Wave Surge",
        "zarr_file": "return_water_levels",   # 對應 data/return_water_levels.zarr
        "has_time": False,                     # 這個檔案沒有 time
        "variables": [
            "flood100", "flood50", "flood25",
            "surge100", "surge50", "surge25",
            "topo"
        ],
        "color_group1": ["#0ea5e9","#0284c7","#0369a1"],  # flood
        "color_group2": ["#8b5cf6","#7c3aed","#6d28d9"],  # surge
        "ts_style": "bar",   # 沒有 time，只能用 bar
    },

    # ── Precipitation（留白）──────────────────────────────
    "precipitation": {
        "label":    "Precipitation",
        "zarr_file": None,   # 尚未有資料
        "has_time": True,
        "variables": [],
        "color_group1": ["#06b6d4","#0891b2","#0e7490"],
        "color_group2": ["#67e8f9","#a5f3fc","#cffafe"],
        "ts_style": "line",
    },

    # ── Fragility（留白）──────────────────────────────────
    "fragility": {
        "label":    "Fragility",
        "zarr_file": None,   # 尚未有資料
        "has_time": True,
        "variables": [],
        "color_group1": ["#ef4444","#dc2626","#b91c1c"],
        "color_group2": ["#f87171","#fca5a5","#fecaca"],
        "ts_style": "line",
    },



    # Tank return surge, flood, and winds
    "tank_surge": {
        "label":    "Tank Hazards",
        "zarr_file": "return_tank_levels",   # 對應 data/return_water_levels.zarr
        "has_time": False,                     # 這個檔案沒有 time
        "variables": [
            "flood100", "flood50", "flood25",
            "surge100", "surge50", "surge25",
            "mwspd100", "mwspd50", "mwspd25", 
        ],
        "color_group1": ["#0ea5e9","#0284c7","#0369a1"],  # flood
        "color_group2": ["#8b5cf6","#7c3aed","#6d28d9"],  # surge
        "ts_style": "bar",   # 沒有 time，只能用 bar
    },
}
