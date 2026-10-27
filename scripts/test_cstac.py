#!/usr/bin/env python3
import os, sys, time, random, requests
from datetime import datetime
from getpass import getpass
from eodc_connect.auth import EODCConnection
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from e2e_helpers.prom import push_e2e_result

CSTAC_URL = os.environ.get("CSTAC_URL", "https://cstac.discovery.eodc.eu").rstrip("/")
LOG = "results/logs/test_cstac.log"
SERVICE = "cstac"

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

def get_headers():
    # CI uses env vars; locally fall back to an interactive prompt
    user = os.getenv("EODC_USERNAME")
    pwd = os.getenv("EODC_PASSWORD")
    if (not user or not pwd) and sys.stdin.isatty():
        user = user or input("Enter your eodc username: ")
        pwd = pwd or getpass("Enter your eodc password: ")
    if not user or not pwd:
        raise RuntimeError("missing EODC_USERNAME/EODC_PASSWORD")
    try:
        token = EODCConnection(username=user, password=pwd).get_access_token()
    except KeyError:
        # Keycloak returned no access_token, e.g. invalid_grant
        raise RuntimeError("login: no access_token from Keycloak")
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

def collections_url(landing):
    # Prefer the STAC landing page's rel="data" link over guessing the path
    for link in landing.get("links", []):
        if link.get("rel") == "data" and link.get("href"):
            return link["href"]
    return f"{CSTAC_URL}/collections"

def main():
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    t0 = time.time()
    col_id, item_id = "N/A", "N/A"

    try:
        headers = get_headers()
        s = requests.Session()
        s.headers.update(headers)

        r = s.get(f"{CSTAC_URL}/", timeout=15)
        ok0, msg0 = ok(r)
        if not ok0:
            raise RuntimeError(f"landing page {msg0}")

        url = collections_url(r.json())
        r = s.get(url, timeout=15)
        okc, msgc = ok(r)
        if not okc:
            raise RuntimeError(f"/collections {msgc}")

        ids = [c.get("id") for c in r.json().get("collections", []) if isinstance(c, dict) and c.get("id")]
        if not ids:
            success, msg = True, "collections=0 (200, OK JSON)"
        else:
            col_id = random.choice(ids)
            r2 = s.get(f"{url.rstrip('/')}/{col_id}", timeout=15)
            ok2, msg2 = ok(r2)
            if not ok2:
                raise RuntimeError(f"/collections/{col_id} {msg2}")

            r3 = s.get(f"{url.rstrip('/')}/{col_id}/items", params={"limit": 1}, timeout=30)
            ok3, msg3 = ok(r3)
            if not ok3:
                raise RuntimeError(f"/collections/{col_id}/items {msg3}")
            feats = r3.json().get("features", [])
            item_id = feats[0].get("id", "N/A") if feats else "N/A"
            success, msg = True, "collection + items OK (200, JSON)"
    except Exception as e:
        success, msg = False, str(e) if isinstance(e, RuntimeError) else f"exception: {e!r}"

    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    line = f"{ts}, {'SUCCESS' if success else 'FAILURE'}, collection: {col_id}, item: {item_id}, reason: {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")

    push_e2e_result(SERVICE, success, time.time() - t0)
    if not success:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
