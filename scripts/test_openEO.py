import os
import openeo
import random
from datetime import datetime
import time

OPENEO_BACKEND = "https://openeo.cloud"
TOKEN_PATH = os.path.expanduser("~/.openeo-refresh-token")

LOG_DIR = "results/logs/"
LOG_FILE = os.path.join(LOG_DIR, "test_openEO.log")

connection = openeo.connect(OPENEO_BACKEND)

def authenticate():
    """Authenticate with openEO using a stored or new refresh token."""

    refresh_token = os.getenv("OPENEO_REFRESH_TOKEN")
    
    if refresh_token:
        try:
            connection.authenticate_oidc_refresh_token(refresh_token)
            return
        except Exception as e:
            return

    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "r") as file:
            refresh_token = file.read().strip()
            if refresh_token:
                try:
                    connection.authenticate_oidc_refresh_token(refresh_token)
                    return
                except Exception as e:
                    return 

    try:
        connection.authenticate_oidc(client_id="openeo-platform-default-client")
    except Exception as e:
        return

authenticate()

def log_message(status, collection_id):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    log_entry = f"{timestamp}, {status}, collection: {collection_id}"
    
    os.makedirs(LOG_DIR, exist_ok=True)

    try:
        with open(LOG_FILE, "a") as log:
            log.write(log_entry + "\n")
    except Exception as e:
        print(f"Error writing to log file: {e}")

    print(log_entry)  


def get_random_collection():
    try:
        collections = connection.list_collections()

        if not collections:
            return None
        
        collection_ids = [c["id"] for c in collections]
        random_collection = random.choice(collection_ids)
        return random_collection
    except Exception as e:
        return None

def test_collection(collection_id):
    try:
        collection = connection.load_collection(collection_id)
        log_message("success", collection_id)
        return True
    except Exception as e:
        log_message("failure", collection_id)
        return False


from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
try:
    from prometheus_client.exposition import basic_auth_handler
except Exception:
    basic_auth_handler = None

def push_e2e_result(service: str, success: bool, duration_s: float):
    """Push ein paar schlanke E2E-Metriken direkt ins Pushgateway."""
    url = os.getenv("PUSHGATEWAY_URL")  # z.B. https://pushgw:9091
    if not url:
        return  
    env = "dev"
    user = os.getenv("PUSHGATEWAY_USERNAME")
    pwd  = os.getenv("PUSHGATEWAY_PASSWORD")

    reg = CollectorRegistry()
    g_last = Gauge("eodc_e2e_last_result", "1 success, 0 failure", ["service","env"], registry=reg)
    g_dur  = Gauge("eodc_e2e_test_duration_seconds", "total duration", ["service","env"], registry=reg)
    g_ts   = Gauge("eodc_e2e_last_success_timestamp", "Unix ts of last success", ["service","env"], registry=reg)

    g_last.labels(service, env).set(1 if success else 0)
    g_dur.labels(service, env).set(duration_s)
    if success:
        g_ts.labels(service, env).set(time.time())

    handler = None
    if user and pwd and basic_auth_handler:
        def handler(url, method, timeout, headers, data):
            return basic_auth_handler(url, method, timeout, headers, data, user, pwd)

    push_to_gateway(url, job="e2e_direct", registry=reg,
                    grouping_key={"env": env}, handler=handler, timeout=15)

if __name__ == "__main__":
    t0 = time.time()
    service = "openeo"
    success = False

    collection_id = get_random_collection()
    if collection_id:
        success = test_collection(collection_id)
    else:
        log_message("failure", "No collection found – test failed.")
        success = False
        
    push_e2e_result(service, success, time.time() - t0)
