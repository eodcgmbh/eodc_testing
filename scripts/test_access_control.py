#!/usr/bin/env python3
# Restricted data and metadata must stay restricted for anonymous users.
# Every check is an anonymous request with an expected set of status codes;
# a public asset is the control that the host itself is reachable.
import os, sys, time, logging, requests
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from e2e_helpers.prom import push_e2e_result
from e2e_helpers.otel_push import record, flush

HDA_URL = os.environ.get("HDA_URL", "https://data.eodc.eu").rstrip("/")
# no cSTAC on dev: leave CSTAC_URL empty to skip the cSTAC checks
CSTAC_URL = os.environ.get("CSTAC_URL", "https://cstac.discovery.eodc.eu").rstrip("/")
LOG = "results/logs/test_access_control.log"
SERVICE = "access-control"
TIMEOUT = 20
DENIED = {401, 403}

# item ids are made up on purpose: the gate (APISIX/OPA) must answer before the
# request reaches the backend, so nothing is fetched or staged
CHECKS = [
    ("maap_asset", "get", f"{HDA_URL}/collections/data/maap/BiomassLevel2a/access-check/data", DENIED),
    ("cdse_asset", "get", f"{HDA_URL}/collections/data/cop_dataspace_s3/S2_MSI_L2A/access-check/B04", DENIED),
    ("bfw_asset", "get", f"{HDA_URL}/collections/TOP4EO/BFW/anomalies/FDL_M3/THUMB/anomalies_fdl_m3_04_2026_32TNS.png", DENIED),
    ("public_control", "get", f"{HDA_URL}/collections/TOP4EO/BFW/forest_mask/THUMB/UTM32_10_10.png", {200}),
]
# TOPO4EO/BFW collections on cSTAC (ACM26-337): only forest_mask is public,
# the others are visible only to users on the BFW access list
CSTAC_PUBLIC = "topo-dc-austria-forest_mask_utm"
CSTAC_RESTRICTED = [
    "topo-dc-austria-anomalies-utm",
    "topo-dc-austria-tree-species-14-utm",
    "topo-dc-austria-tree-species-26-utm",
    "topo-dc-austria-dsm-bfw",
    "topo-dc-austria-ndsm-bfw",
]
if CSTAC_URL:
    CHECKS += [
        # empty body: even if the write gate were open, nothing valid gets created
        ("cstac_post_collection", "post", f"{CSTAC_URL}/collections", DENIED),
        ("cstac_public_collection", "get", f"{CSTAC_URL}/collections/{CSTAC_PUBLIC}", {200}),
    ]
    # restricted collections are hidden from anonymous users
    CHECKS += [(f"cstac_hidden_{cid}", "get", f"{CSTAC_URL}/collections/{cid}", {404} | DENIED)
               for cid in CSTAC_RESTRICTED]

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s")
log = logging.getLogger(__name__)


def check(name, method, url, expected):
    kwargs = {"json": {}} if method == "post" else {}
    try:
        status = requests.request(method, url, timeout=TIMEOUT, allow_redirects=False, **kwargs).status_code
    except Exception as e:
        log.info("%-28s ERROR  %r", name, e)
        status = 0
    result = status in expected
    log.info("%-28s %s  http=%d  expected=%s", name, "OK" if result else "FAIL", status, sorted(expected))
    record({"eodc_e2e_access_check_ok": int(result), "eodc_e2e_access_check_http_status": status},
           {"check": name}, service=SERVICE)
    return result


def main():
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    t0 = time.time()

    failed = [name for name, method, url, expected in CHECKS if not check(name, method, url, expected)]
    flush()
    success = not failed
    msg = "all checks OK" if success else f"failed: {', '.join(failed)}"

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
