#!/usr/bin/env python3
import os, sys, time, requests
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from e2e_helpers.prom import push_e2e_result

TITILER_URL = os.environ.get("TITILER_URL", "https://titiler.services.eodc.eu").rstrip("/")
# public COG on data.eodc.eu (TOP4EO/BFW forest_mask, CC-BY) and one tile inside it
COG_URL = os.environ.get("TITILER_COG_URL", "https://data.eodc.eu/collections/TOP4EO/BFW/forest_mask/COG/UTM32_10_10.tif")
TILE = os.environ.get("TITILER_TILE", "12/2158/1434")
LOG = "results/logs/test_titiler.log"
SERVICE = "titiler"

def main():
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    t0 = time.time()

    try:
        r = requests.get(f"{TITILER_URL}/cog/tiles/WebMercatorQuad/{TILE}.png", params={"url": COG_URL}, timeout=30)
        if not (200 <= r.status_code < 300):
            raise RuntimeError(f"tile {TILE} HTTP {r.status_code}: {r.text[:200]}")
        ct = r.headers.get("Content-Type", "").lower()
        if "image/png" not in ct:
            raise RuntimeError(f"tile {TILE} bad content-type: {ct}")
        if not r.content.startswith(b"\x89PNG"):
            raise RuntimeError(f"tile {TILE} is not a PNG")
        success, msg = True, f"tile {TILE} OK (200, PNG, {len(r.content)} bytes)"
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
