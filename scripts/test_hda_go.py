#!/usr/bin/env python3
import os, sys, time, requests
from datetime import datetime, timedelta, timezone
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from e2e_helpers.prom import push_e2e_result

SERVICE = "hda"
PROD_BASE = "https://data.eodc.eu/collections"
# one metric series per environment
paths = {"prod": PROD_BASE, "dev": "https://dev.hda.eodchosting.eu/collections"}

# Static files that are not subject to a retention window
static_files = [
    "SENTINEL1_SIG0_20M/V1M2R3/EQUI7_EU020M/E048N015T3/SIG0_20260412T171426__VV_A015_E048N015T3_EU020M_V1M2R3_S1CIWGRDH_TUWIEN.tif",
]

# EOPF Zarr products are deleted after a rolling window, so a fixed product
# eventually returns 404. Pick a current one from the EOPF STAC instead,
# a few days old so it is fully ingested and not about to roll out.
EOPF_STAC = "https://stac.core.eopf.eodc.eu"
EOPF_COLLECTION = "sentinel-2-l2a-zarr3"
EOPF_MIN_AGE_DAYS = 2


def ok(resp):
    if not (200 <= resp.status_code < 300):
        return False, f"HTTP {resp.status_code}"
    return True, "OK"


def latest_eopf_file():
    """Return the zarr.json path (relative to PROD_BASE) of a recent EOPF product, or None."""
    until = (datetime.now(timezone.utc) - timedelta(days=EOPF_MIN_AGE_DAYS)).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        r = requests.get(
            f"{EOPF_STAC}/collections/{EOPF_COLLECTION}/items",
            params={"limit": 1, "sortby": "-properties.datetime", "datetime": f"../{until}"},
            timeout=15,
        )
        r.raise_for_status()
        href = r.json()["features"][0]["assets"]["product"]["href"].rstrip("/")
    except Exception as e:
        print(f"WARNING: EOPF STAC lookup failed, skipping EOPF Zarr check: {e}")
        return None
    if not href.startswith(f"{PROD_BASE}/"):
        print(f"WARNING: unexpected EOPF product href, skipping EOPF Zarr check: {href}")
        return None
    return f"{href[len(PROD_BASE) + 1:]}/zarr.json"


def check(env, path, files):
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
    files = list(static_files)
    eopf_file = latest_eopf_file()
    if eopf_file:
        files.append(eopf_file)
    results = [check(env, path, files) for env, path in paths.items()]
    if not all(results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
