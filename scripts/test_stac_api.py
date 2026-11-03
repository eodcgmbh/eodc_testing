#!/usr/bin/env python3
# STAC availability: root, collections and per collection detail, items and search.
# Pushes eodc_e2e_probe_* per probe/collection (STAC dashboard) and
# eodc_e2e_last_result for the whole run (service overview + alerts).
import os, sys, time, logging, requests
from datetime import datetime, timezone, timedelta
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from e2e_helpers.prom import push_e2e_result
from e2e_helpers.otel_push import record, flush

STAC_URL = os.environ.get("STAC_URL", "https://stac.eodc.eu/api/v1").rstrip("/")
LOG = "results/logs/test_stac_api.log"
SERVICE = "stac"
TIMEOUT = 20

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s")
log = logging.getLogger(__name__)


def request(method, url, **kwargs):
    t0 = time.perf_counter()
    try:
        r = getattr(requests, method)(url, timeout=TIMEOUT, allow_redirects=True, **kwargs)
        return r.status_code, time.perf_counter() - t0, r
    except Exception:
        return 0, time.perf_counter() - t0, None


def ok(status):
    return 200 <= status < 300


def probe(name, collection, method, url, **kwargs):
    status, dur, resp = request(method, url, **kwargs)
    result = ok(status)
    log.info("%-24s %-18s %s  http=%d  %.0fms", collection, name, "OK" if result else "FAIL", status, dur * 1000)
    record(
        {"eodc_e2e_probe_success":            int(result),
         "eodc_e2e_probe_duration_seconds":   dur,
         "eodc_e2e_probe_http_status":        status,
         "eodc_e2e_probe_last_run_timestamp": time.time()},
        {"probe": name, "collection": collection},
        service=SERVICE,
    )
    return result, resp


def run():
    failed = []

    result, _ = probe("root", "_", "get", f"{STAC_URL}/")
    if not result:
        failed.append("root")

    result, resp = probe("collections_list", "_", "get", f"{STAC_URL}/collections")
    if not result:
        failed.append("collections_list")
        return failed

    col_ids = [c["id"] for c in resp.json().get("collections", []) if isinstance(c, dict) and "id" in c]
    log.info("Found %d collections", len(col_ids))

    now = datetime.now(timezone.utc)
    window = f"{(now - timedelta(days=90)).strftime('%Y-%m-%dT%H:%M:%SZ')}/{now.strftime('%Y-%m-%dT%H:%M:%SZ')}"
    for col_id in col_ids:
        checks = [
            ("collection_detail", "get", f"{STAC_URL}/collections/{col_id}", {}),
            ("items_list", "get", f"{STAC_URL}/collections/{col_id}/items", {"params": {"limit": 5}}),
            ("search_post", "post", f"{STAC_URL}/search", {"json": {"limit": 5, "collections": [col_id], "datetime": window}}),
        ]
        for name, method, url, kwargs in checks:
            result, _ = probe(name, col_id, method, url, **kwargs)
            if not result:
                failed.append(f"{col_id}/{name}")
    return failed


def main():
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    t0 = time.time()

    try:
        failed = run()
        success = not failed
        msg = "all probes OK" if success else f"{len(failed)} failed: {', '.join(failed[:10])}"
    except Exception as e:
        success, msg = False, f"exception: {e!r}"
    flush()

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
