#!/usr/bin/env python3
import os, sys, time, requests
from datetime import datetime, timedelta
import zarr
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from e2e_helpers.prom import push_e2e_result

LOG = "results/logs/test_s2_datacube.log"
SERVICE = "s2-datacube"
PATH = "https://data.eodc.eu/collections/S2-L2A-C1"

tiles = ['T32TNS', 'T32TNT', 'T32TPS', 'T32TPT', 'T32TQS', 'T32TQT', 'T32UQU', 
         'T33TUM', 'T33TUN', 'T33TVM', 'T33TVN', 'T33TWM', 'T33TWN', 'T33TXN', 
         'T33UUP', 'T33UVP', 'T33UVQ', 'T33UWP', 'T33UWQ', 'T33UXP', 'T33UXQ',        
        ]

def check_tile(tile, t=-1):
    path = f"{PATH}/{tile}"

    path_10m = f"{path}/10"
    cube_10m = zarr.open(path_10m)
    if len(cube_10m.time[:]) < t:
        # while the ingest for new items is running, time for 10m, 20m and indices might not align, 
        # pick a timestep before the last one to check
        t = len(cube_10m.time[:]) - 10
    time_10 = cube_10m.time[t]
    if (cube_10m.red[t, 6000, 6000] == 0):
        check_red = (cube_10m.red[t, :, :] == 0).all()
        check_red_nan = np.isnan(cube_10m.red[t, :, :]).all()
        if check_red or check_red_nan:
            return False, f"ERROR: {tile}: RED at {time_10} "

    path_20m = f"{path}/20"
    cube_20m = zarr.open(path_20m)
    time_20 = cube_20m.time[t]
    if (cube_20m.scl[t, 3000, 3000] == 0):
        check_scl = np.isnan(cube_20m.scl[t, :, :]).all()
        if check_scl:
            return False, f"ERROR: {tile}: SCL at {time_20} "

    path_indices = f"{path}/indices"
    indices = zarr.open(path_indices)
    time_ind = indices.time[t]
    if np.isnan(indices.ndvi[t, 6000, 6000]):
        check_ndvi = np.isnan(indices.ndvi[t, :, :]).all()
        if check_ndvi:
            return False, f"ERROR: {tile}: NDVI at {time_ind} "
    if np.isnan(indices.lai[t, 6000, 6000]):
        check_lai = np.isnan(indices.lai[t, :, :]).all()
        if check_lai:
            return False, f"ERROR: {tile}: LAI at {time_ind} "

    if str(time_ind) != str(time_10):
        return False, f"ERROR: {tile}: Time mismatch: INDICES: {time_ind} != 10m: {time_10} "

    if str(time_20) != str(time_10):
        return False, f"ERROR: {tile}: Time mismatch: 20m: {time_20} != 10m: {time_10} "

    if t == -1:
        today = datetime.now()

        latest = datetime.strptime(str(time_ind)[:19], "%Y-%m-%dT%H:%M:%S")
        if today - latest > timedelta(8):
            return False, f"ERROR: {tile}: Latest timestep: {latest}"

    return True, "OK"

def ok(resp):
    if not (200 <= resp.status_code < 300):
        return False, f"HTTP {resp.status_code}"
    return True, "OK"

def main():
    t0 = time.time()
    service = SERVICE

    try:
        msg = ""
        success = True
        r = requests.get(f"{PATH}/T33UWP/indices/.zmetadata", timeout=15)
        okc, msgc = ok(r)
        if not okc:
            success, msg = False, f"Check hda: {PATH}/T33UWP/indices/.zmetadata {msgc}"
        else:
            today = datetime.now()
            t = 200
            if today.hour in [16, 17, 18, 19, 20]:
                t = 200
            for tile in tiles:
                check, msgc = check_tile(tile, t)
                if not check:
                    success = False
                    msg += msgc + "\n"

    except Exception as e:
        success, msg = False, f"Exception: {e}"

    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    line = f"{ts} - {'SUCCESS' if success else 'FAILURE:'} {msg}"
    print(line)

    push_e2e_result(service, success, time.time() - t0)
    if not success:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
