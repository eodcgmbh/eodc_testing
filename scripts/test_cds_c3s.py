#!/usr/bin/env python3
# C3S CDS (cds.c3s.eodc.eu): APISIX basic-auth in front of nginx-static, which serves
# directory listings (autoindex) of /eodc/products/c3s_cds/{c3s_manifest_https,service}
# under /manifest/ and /service/ - ECMWF's CDS fetches its files from there.
#
# Probes (each pushed as eodc_e2e_probe_* with label probe=..., service.name=cds-c3s):
#   anonymous_401   anonymous request must be rejected by APISIX
#   root_listing    landing page (listing of manifest + service)
#   manifest_list   /manifest/ listing (real data directory on EODC storage)
#   service_list    /service/ listing
#   manifest_file   first 1 MB of one real file under /manifest/ (Range request)
#   service_file    first 1 MB of one real file under /service/
# Overall result (eodc_e2e_last_result) = all probes OK.
import os, sys, time, re, requests
from datetime import datetime
from getpass import getpass
from urllib.parse import urljoin, unquote
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ["E2E_ENV"] = "prod"  # prod-only service: always report as prod, also for local runs
from e2e_helpers.prom import push_e2e_result
from e2e_helpers.otel_push import record, flush

CDS_URL = os.environ.get("CDS_URL", "https://cds.c3s.eodc.eu").rstrip("/")
LOG = "results/logs/test_cds_c3s.log"
SERVICE = "cds-c3s"
READ_BYTES = 1024 * 1024
MAX_DEPTH = 4  # how deep to descend into the listing to find a file


def get_auth():
    # CI uses env vars (Bitwarden "CDS C3S EODC"); locally fall back to an interactive prompt
    user = os.getenv("CDS_USERNAME")
    pwd = os.getenv("CDS_PASSWORD")
    if (not user or not pwd) and sys.stdin.isatty():
        user = user or input("Enter the CDS C3S username: ")
        pwd = pwd or getpass("Enter the CDS C3S password: ")
    if not user or not pwd:
        raise RuntimeError("missing CDS_USERNAME/CDS_PASSWORD")
    return user, pwd


def listing_links(html):
    # nginx autoindex: <a href="name">, directories end with "/"
    return [h for h in re.findall(r'<a href="([^"?#]+)"', html) if h not in ("../", "/") and not h.startswith(("http", "/"))]


def find_file(s, url, depth=0):
    """Descend into the first directory entries until a file is found; returns its URL or None."""
    r = s.get(url, timeout=30)
    r.raise_for_status()
    links = listing_links(r.text)
    files = [l for l in links if not l.endswith("/")]
    if files:
        return urljoin(url, files[0])
    if depth >= MAX_DEPTH:
        return None
    for d in [l for l in links if l.endswith("/")][:3]:
        found = find_file(s, urljoin(url, d), depth + 1)
        if found:
            return found
    return None


results = {}


def probe(name, fn):
    t0 = time.perf_counter()
    status, ok, msg = 0, False, ""
    try:
        status, ok, msg = fn()
    except Exception as e:
        msg = f"{type(e).__name__}: {e}"
    dur = time.perf_counter() - t0
    results[name] = (ok, status, msg)
    print(f"  {name:15} {'OK  ' if ok else 'FAIL'} http={status} {dur * 1000:.0f}ms {msg}", flush=True)
    record({"eodc_e2e_probe_success": int(ok),
            "eodc_e2e_probe_duration_seconds": dur,
            "eodc_e2e_probe_http_status": status,
            "eodc_e2e_probe_last_run_timestamp": time.time()},
           {"probe": name}, service=SERVICE)
    return ok


def main():
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    t0 = time.time()
    s = requests.Session()

    def anonymous():
        r = requests.get(f"{CDS_URL}/", timeout=15)
        return r.status_code, r.status_code == 401, "expected 401"

    def listing(path):
        def f():
            r = s.get(f"{CDS_URL}{path}", timeout=30)
            n = len(listing_links(r.text)) if r.ok else 0
            return r.status_code, r.ok and n > 0, f"{n} entries"
        return f

    def file_read(path):
        def f():
            url = find_file(s, f"{CDS_URL}{path}")
            if not url:
                return 0, False, "no file found in listing"
            r = s.get(url, headers={"Range": f"bytes=0-{READ_BYTES - 1}"}, timeout=60)
            got = len(r.content)
            name = unquote(url[len(CDS_URL):])
            return r.status_code, r.status_code in (200, 206) and got > 0, f"{got} bytes of {name}"
        return f

    try:
        s.auth = get_auth()
        probe("anonymous_401", anonymous)
        probe("root_listing", listing("/"))
        probe("manifest_list", listing("/manifest/"))
        probe("service_list", listing("/service/"))
        probe("manifest_file", file_read("/manifest/"))
        probe("service_file", file_read("/service/"))
        failed = [k for k, (ok, _, _) in results.items() if not ok]
        success = not failed
        msg = "all probes OK" if success else "failed: " + ", ".join(f"{k} ({results[k][1]} {results[k][2]})" for k in failed)
    except Exception as e:
        success, msg = False, str(e) if isinstance(e, RuntimeError) else f"exception: {e!r}"

    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    line = f"{ts}, {'SUCCESS' if success else 'FAILURE'}, reason: {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")

    flush()
    push_e2e_result(SERVICE, success, time.time() - t0, env="prod")
    if not success:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
