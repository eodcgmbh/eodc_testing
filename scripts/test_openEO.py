import os
import openeo
import random
from datetime import datetime
import time
from e2e_helpers.prom import push_e2e_result

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
