#!/usr/bin/env python3
import os, sys, time, requests
from datetime import datetime, timedelta
import zarr
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from e2e_helpers.prom import push_e2e_result

SERVICE = "hda"
# one metric series per environment
paths = {"prod": "https://data.eodc.eu/collections", "dev": "https://dev.hda.eodchosting.eu/collections"}
files = [
    "SENTINEL1_SIG0_20M/V1M2R3/EQUI7_EU020M/E048N015T3/SIG0_20260412T171426__VV_A015_E048N015T3_EU020M_V1M2R3_S1CIWGRDH_TUWIEN.tif",
    "EOPF_ZARR/products/cpm_v300/S02MSIL2A/2026/09/06/S2B_MSIL2A_20260906T100019_N0512_R122_T35WNU_20260906T134813.zarr/zarr.json",
]

def ok(resp):
    if not (200 <= resp.status_code < 300):
        return False, f"HTTP {resp.status_code}"
    return True, "OK"

def check(env, path):
    t0 = time.time()

    try:
        msg = ""
        success = True
        for file in files:
            filepath = f"{path}/{file}"
            r = requests.get(filepath, timeout=15)
            okc, msgc = ok(r)
            if not okc:
                success, msg = False, f"Check hda: {filepath} {msgc}"
                break
            print(f"{r.status_code} - {filepath}")

    except Exception as e:
        success, msg = False, f"Exception: {e}"

    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    line = f"{ts} - {env} - {'SUCCESS' if success else 'FAILURE:'} {msg}"
    print(line)

    push_e2e_result(SERVICE, success, time.time() - t0, env=env)
    return success

def main():
    results = [check(env, path) for env, path in paths.items()]
    if not all(results):
        raise SystemExit(1)

if __name__ == "__main__":
    main()
