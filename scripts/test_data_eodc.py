#!/usr/bin/env python3
import os, sys, time, requests
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from e2e_helpers.prom import push_e2e_result

# one public asset on data.eodc.eu (TOP4EO/BFW forest_mask, CC-BY), no login needed
ASSET_URL = os.environ.get("DATA_ASSET_URL", "https://data.eodc.eu/collections/TOP4EO/BFW/forest_mask/THUMB/UTM32_10_10.png")
LOG = "results/logs/test_data_eodc.log"
SERVICE = "data-eodc"

def main():
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    t0 = time.time()

    try:
        r = requests.get(ASSET_URL, timeout=30)
        if r.status_code != 200:
            raise RuntimeError(f"{ASSET_URL} HTTP {r.status_code}")
        if not r.content:
            raise RuntimeError(f"{ASSET_URL} empty response")
        success, msg = True, f"public asset OK (200, {len(r.content)} bytes)"
    except Exception as e:
        success, msg = False, str(e) if isinstance(e, RuntimeError) else f"exception: {e!r}"

    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    line = f"{ts}, {'SUCCESS' if success else 'FAILURE'}, reason: {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")

    push_e2e_result(SERVICE, success, time.time() - t0)
    if not success:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
