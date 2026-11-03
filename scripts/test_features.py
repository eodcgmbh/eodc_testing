#!/usr/bin/env python3
import os, sys, time, requests
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from e2e_helpers.prom import push_e2e_result

FEATURES_URL = os.environ.get("FEATURES_URL", "https://features.services.eodc.eu").rstrip("/")
LOG = "results/logs/test_features.log"
SERVICE = "features"

def main():
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    t0 = time.time()

    try:
        r = requests.get(f"{FEATURES_URL}/", params={"f": "json"}, timeout=15)
        if not (200 <= r.status_code < 300):
            raise RuntimeError(f"landing page HTTP {r.status_code}")
        ct = r.headers.get("Content-Type", "").lower()
        if "json" not in ct:
            raise RuntimeError(f"landing page bad content-type: {ct}")
        try:
            links = r.json().get("links", [])
        except Exception as e:
            raise RuntimeError(f"landing page invalid json: {e}")
        if not links:
            raise RuntimeError("landing page has no links")
        success, msg = True, "landing page OK (200, JSON)"
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
