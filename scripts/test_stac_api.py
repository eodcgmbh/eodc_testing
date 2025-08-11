import os
import requests
import random
from datetime import datetime
import jsonschema
from requests import RequestException

STAC_URL = "https://stac.eodc.eu/api/v1"
ITEM_SCHEMA_URL = "https://schemas.stacspec.org/v1.1.0/item-spec/json-schema/item.json"
TIMEOUT = 20 

def fetch_json(url: str, what: str):
    """GET JSON ohne raise_for_status; gibt (ok, data_or_message) zurück."""
    try:
        resp = requests.get(url, timeout=TIMEOUT)
        if resp.status_code != 200:
            return False, f"{what} failed: HTTP {resp.status_code} for url: {url}"
        return True, resp.json()
    except RequestException as e:
        return False, f"{what} request exception for url: {url}: {e}"
    except ValueError as e:
        return False, f"{what} JSON decode error for url: {url}: {e}"

def get_stac_item_schema():
    """Fetch the STAC 1.1.0 item JSON schema."""
    ok, data = fetch_json(ITEM_SCHEMA_URL, "Fetch STAC item schema")
    if not ok:
        return False, data
    return True, data

def validate_item_schema(item, schema):
    """Validate a STAC item against the 1.1.0 schema."""
    try:
        jsonschema.validate(instance=item, schema=schema)
        return True, "Item is valid according to STAC 1.1.0 schema"
    except jsonschema.exceptions.ValidationError as e:
        return False, f"Item validation failed: {e.message} at {list(e.path)} (validator: {e.validator}, expected: {e.validator_value})"
    except jsonschema.exceptions.SchemaError as e:
        return False, f"Schema error: {e}"

def get_random_item_and_validate():
    """Fetch a random item and validate against STAC schema."""
    try:
        ok, collections_payload = fetch_json(f"{STAC_URL}/collections", "Fetch collections")
        if not ok:
            return False, collections_payload, "N/A", "N/A"

        collections = collections_payload.get("collections", [])
        if not collections:
            return False, "No collections found", "N/A", "N/A"

        random_collection = random.choice(collections)
        collection_id = random_collection.get("id")
        if not collection_id:
            return False, "Collection has no 'id'", "N/A", "N/A"

        ok, items_payload = fetch_json(f"{STAC_URL}/collections/{collection_id}/items",
                                       f"Fetch items from '{collection_id}'")
        if not ok:
            return False, items_payload, collection_id, "N/A"

        items = items_payload.get("features", [])
        if not items:
            return False, f"No items in collection {collection_id}", collection_id, "N/A"

        random_item = random.choice(items)

        ok, schema_or_msg = get_stac_item_schema()
        if not ok:
            return False, schema_or_msg, collection_id, random_item.get("id", "N/A")
        schema = schema_or_msg

        is_valid, validation_message = validate_item_schema(random_item, schema)
        if not is_valid:
            return False, validation_message, collection_id, random_item.get("id", "N/A")

        return True, "STAC item is valid and conforms to 1.1.0 schema", collection_id, random_item.get("id", "N/A")

    except Exception as e:
        return False, f"Exception: {e}", "N/A", "N/A"

if __name__ == "__main__":
    success, message, collection_id, item_id = get_random_item_and_validate()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    collection_id = collection_id or "N/A"
    item_id = item_id or "N/A"

    if success:
        log_entry = f"{timestamp}, success, collection: {collection_id}, item: {item_id}"
    else:
        log_entry = f"{timestamp}, failure: {message or 'Unknown error'}, collection: {collection_id}, item: {item_id}"

    log_dir = "results/logs/"
    os.makedirs(log_dir, exist_ok=True)

    with open(os.path.join(log_dir, "test_stac_api.log"), "a") as log_file:
        log_file.write(log_entry + "\n")

    exit(0 if success else 1)
