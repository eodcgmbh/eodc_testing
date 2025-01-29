import os
import openeo
import random
from datetime import datetime

OPENEO_BACKEND = "https://openeo.cloud"
TOKEN_PATH = os.path.expanduser("~/.openeo-refresh-token")

LOG_DIR = "results/logs/"
LOG_FILE = os.path.join(LOG_DIR, "test_openEO.log")

connection = openeo.connect(OPENEO_BACKEND)
if os.path.exists(TOKEN_PATH):
    with open(TOKEN_PATH, "r") as file:
        refresh_token = file.read().strip()
        if not refresh_token:
            print("❌ Fehler: Refresh Token Datei existiert, ist aber leer!")
            exit(1)
        print(f"🔑 Verwende Refresh Token: {refresh_token[:10]}********")

        connection.authenticate_oidc(client_id="openeo-platform-default-client", refresh_token=refresh_token)

        print("✅ Erfolgreich authentifiziert mit openEO!")
else:
    print("❌ Fehler: Kein Refresh Token gefunden!")
    exit(1)

if os.path.exists(TOKEN_PATH):
    with open(TOKEN_PATH, "r") as file:
        refresh_token = file.read().strip()
        connection.authenticate_oidc_refresh_token(refresh_token)
else:
    exit(1)

def log_message(status, message, collection_id="N/A"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    log_entry = f"{timestamp}, {status}, collection: {collection_id}, {message}"
    print(log_entry)
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(LOG_FILE, "a") as log:
        log.write(log_entry + "\n")

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
        return True
    except Exception as e:
        log_message("failure", f"Collection: {collection_id}: {str(e)}", collection_id)
        return False

if __name__ == "__main__":
    collection_id = get_random_collection()
    if collection_id:
        test_collection(collection_id)
