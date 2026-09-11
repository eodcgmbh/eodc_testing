#!/usr/bin/env python3
import os, sys, time, requests
from datetime import datetime, timedelta
import zarr
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

paths = ["https://data.eodc.eu/collections", "https://dev.hda.eodchosting.eu/collections"]
sig0 = f"{paths[0]}/SENTINEL1_SIG0_20M/V1M2R3/EQUI7_EU020M/E048N015T3/SIG0_20260412T171426__VV_A015_E048N015T3_EU020M_V1M2R3_S1CIWGRDH_TUWIEN.tif"
eopf = f"{paths[0]}/EOPF_ZARR/products/cpm_v300/S02MSIL2A/2026/09/06/S2B_MSIL2A_20260906T100019_N0512_R122_T35WNU_20260906T134813.zarr/zarr.json"
sig0_dev = f"{paths[1]}/SENTINEL1_SIG0_20M/V1M2R3/EQUI7_EU020M/E048N015T3/SIG0_20260412T171426__VV_A015_E048N015T3_EU020M_V1M2R3_S1CIWGRDH_TUWIEN.tif"
eopf_dev = f"{paths[1]}/EOPF_ZARR/products/cpm_v300/S02MSIL2A/2026/09/06/S2B_MSIL2A_20260906T100019_N0512_R122_T35WNU_20260906T134813.zarr/zarr.json"

def ok(resp):
    if not (200 <= resp.status_code < 300):
        return False, f"HTTP {resp.status_code}"
    return True, "OK"

def main():
    t0 = time.time()

    try:
        msg = ""
        success = True
        for filepath in [sig0, eopf, sig0_dev, eopf_dev]:
            if success:
                r = requests.get(filepath, timeout=15)
                okc, msgc = ok(r)
                if not okc:
                    success, msg = False, f"Check hda: {sig0} {msgc}"
            else:
                break

    except Exception as e:
        success, msg = False, f"Exception: {e}"

    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    line = f"{ts} - {'SUCCESS' if success else 'FAILURE:'} {msg}"
    print(line)

    if not success:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
