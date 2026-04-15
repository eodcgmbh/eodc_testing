#!/usr/bin/env python3
import os, sys, time, requests
from datetime import datetime, timedelta
import zarr
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from e2e_helpers.prom import push_e2e_result

LOG = "results/logs/test_s2_datacube.log"
SERVICE = "s2-datacube"
PATH = "https://data.eodc.eu/collections/S2-L2A-C1"

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
            r = requests.get(f"https://data.eodc.eu/collections/SENTINEL1_SIG0_20M/V1M2R3/EQUI7_EU020M/E048N015T3/SIG0_20260412T171426__VV_A015_E048N015T3_EU020M_V1M2R3_S1CIWGRDH_TUWIEN.tif", timeout=15)
            okc, msgc = ok(r)
            if not okc:
                success, msg = False, f"Check hda: https://data.eodc.eu/collections/SENTINEL1_SIG0_20M/V1M2R3/EQUI7_EU020M/E048N015T3/SIG0_20260412T171426__VV_A015_E048N015T3_EU020M_V1M2R3_S1CIWGRDH_TUWIEN.tif {msgc}"

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
