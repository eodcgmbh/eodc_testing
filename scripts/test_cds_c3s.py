#!/usr/bin/env python3
import os, sys, time, requests
from datetime import datetime
from getpass import getpass
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from e2e_helpers.prom import push_e2e_result

CDS_URL = os.environ.get("CDS_URL", "https://cds.c3s.eodc.eu").rstrip("/")
LOG = "results/logs/test_cds_c3s.log"
SERVICE = "cds-c3s"

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

def main():
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    t0 = time.time()

    try:
        auth = get_auth()

        # Gateway (APISIX) must reject anonymous requests with 401
        r = requests.get(f"{CDS_URL}/", timeout=15)
        if r.status_code != 401:
            raise RuntimeError(f"anonymous request: expected 401, got HTTP {r.status_code}")

        # With Basic Auth the service itself must answer
        r = requests.get(f"{CDS_URL}/", auth=auth, timeout=30)
        if r.status_code in (401, 403):
            raise RuntimeError(f"login rejected: HTTP {r.status_code}")
        if not (200 <= r.status_code < 300):
            raise RuntimeError(f"landing page HTTP {r.status_code}")
        if not r.content:
            raise RuntimeError("landing page empty response")
        success, msg = True, f"landing page OK ({r.status_code}, {r.headers.get('Content-Type', '?')})"
    except Exception as e:
        success, msg = False, str(e) if isinstance(e, RuntimeError) else f"exception: {e!r}"

    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    line = f"{ts}, {'SUCCESS' if success else 'FAILURE'}, reason: {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")

    # cds.c3s.eodc.eu is a prod-only service: always report as prod, also for local runs
    push_e2e_result(SERVICE, success, time.time() - t0, env="prod")
    if not success:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
