import os
import requests
import random
from datetime import datetime
import jsonschema


STAC_URL = "https://dev.stac.eodc.eu/api/v1"
ITEM_SCHEMA_URL = "https://schemas.stacspec.org/v1.1.0/item-spec/json-schema/item.json"


def get_stac_item_schema():
    """Fetch the STAC 1.1.0 item JSON schema."""
    response = requests.get(ITEM_SCHEMA_URL)
    response.raise_for_status()
    return response.json()

def validate_item_schema(item, schema):
    """Validate a STAC item against the 1.1.0 schema."""
    try:
        jsonschema.validate(instance=item, schema=schema)
        return True, "Item is valid according to STAC 1.1.0 schema"
    except jsonschema.exceptions.ValidationError as e:
        return False, f"Item validation failed: {e.message} at {list(e.path)} (validator: {e.validator}, expected: {e.validator_value})"


def get_random_item_and_validate():
    """Fetch a random item and validate against STAC schema."""
    try:
        collections_response = requests.get(f"{STAC_URL}/collections")
        if collections_response.status_code != 200:
            return False, f"Failed to fetch collections: {collections_response.status_code}", "N/A", "N/A"

        collections = collections_response.json().get("collections", [])
        if not collections:
            return False, "No collections found", "N/A", "N/A"

        random_collection = random.choice(collections)
        collection_id = random_collection.get("id", None)
        if not collection_id:
            return False, "Collection has no 'id'", "N/A", "N/A"

        items_response = requests.get(f"{STAC_URL}/collections/{collection_id}/items")
        if items_response.status_code != 200:
            return False, f"Failed to fetch items from {collection_id}: {items_response.status_code}", collection_id, "N/A"

        items = items_response.json().get("features", [])
        if not items:
            return False, f"No items in collection {collection_id}", collection_id, "N/A"

        random_item = random.choice(items)

        # STAC schema validation
        schema = get_stac_item_schema()
        is_valid, validation_message = validate_item_schema(random_item, schema)

        if not is_valid:
            return False, validation_message, collection_id, random_item.get("id", "N/A")

        return True, "STAC item is valid and conforms to 1.1.0 schema", collection_id, random_item.get("id", "N/A")

    except Exception as e:
        return False, f"Exception: {str(e)}", "N/A", "N/A"

if __name__ == "__main__":
    success, message, collection_id, item_id = get_random_item_and_validate()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    result = "success" if success else "failure"
    collection_id = collection_id or "N/A"
    item_id = item_id or "N/A"

    log_entry = f"{timestamp}, {result}, collection: {collection_id}, item: {item_id}"
    if not success:
        log_entry += f", reason: {message or 'Unknown error'}"

    log_dir = "results/logs/"
    os.makedirs(log_dir, exist_ok=True)

    with open(os.path.join(log_dir, "test_stac_api.log"), "a") as log_file:
        log_file.write(log_entry + "\n")

    exit(0 if success else 1)
