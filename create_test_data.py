import xarray as xr
import numpy as np
import os

os.makedirs("data", exist_ok=True)

times = np.arange(1900, 2010)
lats  = np.arange(-90, 91, 2.0)
lons  = np.arange(-180, 181, 2.0)

names = [
    "precip_var1","precip_var2","precip_var3",
    "wave_var1","wave_var2","wave_var3",
    "frag_var1","frag_var2","frag_var3",
]

for name in names:
    ds = xr.Dataset(
        {name: (["time","lat","lon"],
                np.random.rand(len(times), len(lats), len(lons)).astype("float32"))},
        coords={"time": times, "lat": lats, "lon": lons}
    )
    ds.to_zarr(f"data/{name}.zarr", mode="w")
    print(f"✓ {name}.zarr")

print("完成！")
