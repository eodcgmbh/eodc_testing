#!/usr/bin/env python3
import os, sys, time, requests
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from e2e_helpers.prom import push_e2e_result

ORBIT_URL = os.environ.get("ORBIT_URL", "https://orbit.discovery.eodc.eu").rstrip("/")
LOG = "results/logs/test_orbit.log"
SERVICE = "orbit"

def ok(resp, content_type):
    if not (200 <= resp.status_code < 300):
        return False, f"HTTP {resp.status_code}"
    ct = resp.headers.get("Content-Type", "").lower()
    if content_type not in ct:
        return False, f"bad content-type: {ct}"
    return True, "OK"

def main():
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    t0 = time.time()

    try:
        r = requests.get(f"{ORBIT_URL}/", timeout=15)
        ok0, msg0 = ok(r, "text/html")
        if not ok0:
            raise RuntimeError(f"landing page {msg0}")

        # the app cannot start without its config (STAC root, titiler, login)
        r = requests.get(f"{ORBIT_URL}/config.json", timeout=15)
        okc, msgc = ok(r, "json")
        if not okc:
            raise RuntimeError(f"/config.json {msgc}")
        try:
            config = r.json()
        except Exception as e:
            raise RuntimeError(f"/config.json invalid json: {e}")
        if not config.get("stacRoot"):
            raise RuntimeError("/config.json has no stacRoot")

        r = requests.get(f"{ORBIT_URL}/docs/", timeout=15)
        okd, msgd = ok(r, "text/html")
        if not okd:
            raise RuntimeError(f"/docs/ {msgd}")

        success, msg = True, "landing + config.json + docs OK (200)"
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
