#!/usr/bin/env python3
import os, sys, time, traceback
from datetime import datetime
from unittest.mock import patch
from dask.distributed import Client
from eodc.dask import EODCDaskGateway
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from e2e_helpers.prom import push_e2e_result

LOG_PATH = "results/logs/test_DaskGateway.log"
SERVICE = "dask_gateway"

def log_result(success: bool, msg: str = ""):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"{ts} - {'SUCCESS' if success else 'FAILURE'}{(' - '+msg) if msg else ''}\n")

class CustomEODCDaskGateway(EODCDaskGateway):
    def __init__(self, username, password):
        self._password = password
        super().__init__(username=username)
    def _authenticate(self):
        return self._password

def create_and_connect_cluster(gateway):
    try:
        cluster = gateway.new_cluster()
        client = Client(cluster)
        cluster.scale(2)
        return cluster, client
    except Exception as e:
        log_result(False, f"connect: {e}")
        return None, None

def test_simple_computation(client) -> bool:
    try:
        res = client.submit(lambda x, y: x + y, 5, 10).result()
        return res == 15
    except Exception as e:
        log_result(False, f"compute: {e}")
        return False

def main():
    t0 = time.time()
    success = False
    cluster = client = None
    user = os.getenv("EODC_USERNAME")
    pwd = os.getenv("EODC_PASSWORD")
    if not user or not pwd:
        log_result(False, "missing EODC_USERNAME/EODC_PASSWORD")
        raise SystemExit(1)
    try:
        with patch("getpass.getpass", return_value=pwd):
            gw = CustomEODCDaskGateway(username=user, password=pwd)
            cluster, client = create_and_connect_cluster(gw)
            success = test_simple_computation(client) if client else False
    except Exception as e:
        log_result(False, f"unexpected: {e}")
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
