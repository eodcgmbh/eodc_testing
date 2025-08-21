from eodc.dask import EODCDaskGateway
from dask.distributed import Client
from unittest.mock import patch
import os, time
from datetime import datetime
from e2e_helpers.prom import push_e2e_result

class CustomEODCDaskGateway(EODCDaskGateway):
    def __init__(self, username, password):
        self._password = password
        super().__init__(username=username)
    def _authenticate(self):
        return self._password

def get_cluster_options(gateway):
    try:
        _ = gateway.cluster_options()
    except Exception as e:
        print(f"Error cluster options: {e}")

def log_result(success: bool):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    result = "SUCCESS" if success else "FAILURE"
    os.makedirs("results/logs", exist_ok=True)
    with open("results/logs/test_DaskGateway.log", "a") as f:
        f.write(f"{timestamp} - {result}\n")

def create_and_connect_cluster(gateway):
    try:
        cluster = gateway.new_cluster()
        client = Client(cluster)
        cluster.scale(2)
        return cluster, client
    except Exception as e:
        return None, None

def test_simple_computation(client) -> bool:
    try:
        def add(x, y): return x + y
        future = client.submit(add, 5, 10)
        return future.result() == 15
    except Exception as e:
        return False

def main():
    t0 = time.time()
    service = "dask_gateway"
    success = False
    cluster = client = None

    username = os.getenv("EODC_USERNAME")
    password = os.getenv("EODC_PASSWORD")
    if not username or not password:
        log_result(False)
        raise ValueError("Error EODC_USERNAME or EODC_PASSWORD")

    try:
        with patch("getpass.getpass", return_value=password):
            gateway = CustomEODCDaskGateway(username=username, password=password)
            get_cluster_options(gateway)
            cluster, client = create_and_connect_cluster(gateway)
            if client:
                success = test_simple_computation(client)
            else:
                success = False
    finally:
        try:
            if client: client.close()
        except Exception: pass
        try:
            if cluster: cluster.close()
        except Exception: pass
        log_result(success)
        push_e2e_result(service, success, time.time() - t0)

if __name__ == "__main__":
    main()
