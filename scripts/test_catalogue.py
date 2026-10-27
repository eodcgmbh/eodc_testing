#!/usr/bin/env python3
import os, sys, time, requests
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from e2e_helpers.prom import push_e2e_result

CATALOGUE_URL = os.environ.get("CATALOGUE_URL", "https://catalogue.services.eodc.eu").rstrip("/")
LOG = "results/logs/test_catalogue.log"
SERVICE = "catalogue"

def ok(resp):
    if not (200 <= resp.status_code < 300):
        return False, f"HTTP {resp.status_code}"
    ct = resp.headers.get("Content-Type", "").lower()
    if ("application/json" not in ct) and ("+json" not in ct):
        return False, f"bad content-type: {ct}"
    try:
        resp.json()
    except Exception as e:
        return False, f"invalid json: {e}"
    return True, "OK"

def collections_url(landing):
    # Prefer the STAC landing page's rel="data" link over guessing the path
    for link in landing.get("links", []):
        if link.get("rel") == "data" and link.get("href"):
            return link["href"]
    return f"{CATALOGUE_URL}/collections"

def main():
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    t0 = time.time()
    n_cols = 0

    try:
        r = requests.get(f"{CATALOGUE_URL}/", headers={"Accept": "application/json"}, timeout=15)
        ok0, msg0 = ok(r)
        if not ok0:
            raise RuntimeError(f"landing page {msg0}")

        r = requests.get(collections_url(r.json()), headers={"Accept": "application/json"}, timeout=30)
        okc, msgc = ok(r)
        if not okc:
            raise RuntimeError(f"/collections {msgc}")

        n_cols = len(r.json().get("collections", []))
        if n_cols == 0:
            raise RuntimeError("/collections returned 0 collections")
        success, msg = True, "landing + collections OK (200, JSON)"
    except Exception as e:
        success, msg = False, str(e) if isinstance(e, RuntimeError) else f"exception: {e!r}"

    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    line = f"{ts}, {'SUCCESS' if success else 'FAILURE'}, collections: {n_cols}, reason: {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")

    push_e2e_result(SERVICE, success, time.time() - t0)
    if not success:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
