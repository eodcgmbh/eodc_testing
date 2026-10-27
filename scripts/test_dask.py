#!/usr/bin/env python3
import os, sys, time, traceback
from datetime import datetime
from getpass import getpass
from unittest.mock import patch
from dask.distributed import Client
from eodc_connect.dask import EODCDaskGateway
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from e2e_helpers.prom import push_e2e_result

LOG_PATH = "results/logs/test_DaskGateway.log"
SERVICE = "dask_gateway"

def log_result(success: bool, msg: str = ""):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{ts} - {'SUCCESS' if success else 'FAILURE'}{(' - '+msg) if msg else ''}"
    print(line, flush=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def get_credentials():
    # CI uses env vars; locally fall back to an interactive prompt
    user = os.getenv("EODC_USERNAME")
    pwd = os.getenv("EODC_PASSWORD")
    if (not user or not pwd) and sys.stdin.isatty():
        user = user or input("Enter your eodc username: ")
        pwd = pwd or getpass("Enter your eodc password: ")
    return user, pwd

def create_gateway(user, pwd):
    # The gateway only accepts tokens from the 'dedl-dask-gateway' client, which
    # EODCDaskGateway(username=...) requests via getpass, so we feed it the password
    try:
        with patch("getpass.getpass", return_value=pwd):
            return EODCDaskGateway(username=user)
    except KeyError:
        # Keycloak returned no access_token, e.g. invalid_grant
        log_result(False, "login: no access_token from Keycloak (wrong credentials or no access to client 'dedl-dask-gateway')")
    except Exception as e:
        log_result(False, f"login: {e!r}")
    return None

def create_and_connect_cluster(gateway):
    try:
        cluster = gateway.new_cluster()
        client = Client(cluster)
        cluster.scale(2)
        return cluster, client
    except Exception as e:
        log_result(False, f"connect: {e!r}")
        traceback.print_exc()
        return None, None

def test_simple_computation(client) -> bool:
    try:
        res = client.submit(lambda x, y: x + y, 5, 10).result()
        return res == 15
    except Exception as e:
        log_result(False, f"compute: {e!r}")
        traceback.print_exc()
        return False

def main():
    t0 = time.time()
    success = False
    cluster = client = None
    user, pwd = get_credentials()
    if not user or not pwd:
        log_result(False, "missing EODC_USERNAME/EODC_PASSWORD")
        raise SystemExit(1)
    try:
        gw = create_gateway(user, pwd)
        if gw:
            cluster, client = create_and_connect_cluster(gw)
            success = test_simple_computation(client) if client else False
    except Exception as e:
        log_result(False, f"unexpected: {e!r}")
        print(traceback.format_exc(), flush=True)
        success = False
    finally:
        try:
            if client: client.close()
        except: pass
        try:
            if cluster: cluster.close()
        except: pass
        log_result(success)
        try:
            push_e2e_result(SERVICE, success, time.time() - t0)
        except Exception:
            pass
    if not success:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
