#!/usr/bin/env python3
import os, sys, time, random, requests
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from e2e_helpers.prom import push_e2e_result

STAC_URL = os.environ.get("STAC_URL", "https://stac.eodc.eu/api/v1")
LOG = "results/logs/test_stac_api.log"
SERVICE = "stac"

def ok(resp, expect_json=True):
    if not (200 <= resp.status_code < 300):
        return False, f"HTTP {resp.status_code}"
    if expect_json:
        ct = resp.headers.get("Content-Type", "").lower()
        if ("application/json" not in ct) and ("+json" not in ct):
            return False, f"bad content-type: {ct}"
        try:
            resp.json()
        except Exception as e:
            return False, f"invalid json: {e}"
    return True, "OK"

def main():
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    t0 = time.time()
    service = SERVICE

    try:
        r = requests.get(f"{STAC_URL}/collections", timeout=15)
        okc, msgc = ok(r)
        if not okc:
            success, msg, col_id = False, f"/collections {msgc}", "N/A"
        else:
            cols = r.json().get("collections", [])
            if not cols:
                success, msg, col_id = True, "collections=0 (200, OK JSON)", "N/A"
            else:
                col_id = random.choice([c.get("id") for c in cols if isinstance(c, dict) and c.get("id")]) or "N/A"
                if col_id == "N/A":
                    success, msg = True, "no collection id (200, OK JSON)"
                else:
                    r2 = requests.get(f"{STAC_URL}/collections/{col_id}", timeout=15)
                    ok2, msg2 = ok(r2)
                    success, msg = (True, "collection OK (200, JSON)") if ok2 else (False, f"/collections/{col_id} {msg2}")
    except Exception as e:
        success, msg, col_id = False, f"exception: {e}", "N/A"

    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    line = f"{ts}, {'SUCCESS' if success else 'FAILURE'}, collection: {col_id}, item: N/A, reason: {msg}"
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")

    push_e2e_result(service, success, time.time() - t0)
    if not success:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
