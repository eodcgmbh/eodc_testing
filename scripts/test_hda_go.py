#!/usr/bin/env python3
import os, sys, time, requests
from datetime import datetime, timedelta
import zarr
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

path = "https://data.eodc.eu/collections"
sig0 = f"{path}/SENTINEL1_SIG0_20M/V1M2R3/EQUI7_EU020M/E048N015T3/SIG0_20260412T171426__VV_A015_E048N015T3_EU020M_V1M2R3_S1CIWGRDH_TUWIEN.tif"
eopf = f"{path}/EOPF_ZARR/products/cpm_v300/S02MSIL2A/2026/09/06/S2B_MSIL2A_20260906T100019_N0512_R122_T35WNU_20260906T134813.zarr/zarr.json"

def ok(resp):
    if not (200 <= resp.status_code < 300):
        return False, f"HTTP {resp.status_code}"
    return True, "OK"

def main():
    t0 = time.time()

    try:
        msg = ""
        success = True
        r = requests.get(sig0, timeout=15)
        okc, msgc = ok(r)
        if not okc:
            success, msg = False, f"Check hda: {sig0} {msgc}"
        else:
            r = requests.get(eopf, timeout=15)
            okc, msgc = ok(r)
            if not okc:
                success, msg = False, f"Check hda: {eopf} {msgc}"

    except Exception as e:
        success, msg = False, f"Exception: {e}"

    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    line = f"{ts} - {'SUCCESS' if success else 'FAILURE:'} {msg}"
    print(line)

    if not success:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
