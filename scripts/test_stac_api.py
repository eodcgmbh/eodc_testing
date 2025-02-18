import os
import requests
import random
from datetime import datetime

STAC_URL = "https://dev.stac.eodc.eu/api/v1"

def get_random_item():
    """Fetch a random item from the /collections endpoint and validate it."""
    try:
        collections_response = requests.get(f"{STAC_URL}/collections")
        if collections_response.status_code != 200:
            return False, f"Failed to fetch collections: {collections_response.status_code}", "N/A", "N/A"

        collections_data = collections_response.json()
        collections = collections_data.get("collections", [])
        if not collections:
            return False, "No collections found in the API", "N/A", "N/A"

        random_collection = random.choice(collections)
        collection_id = random_collection.get("id", None)
        if not collection_id:
            return False, "Random collection has no 'id' field", "N/A", "N/A"

        items_response = requests.get(f"{STAC_URL}/collections/{collection_id}/items")
        if items_response.status_code != 200:
            return False, f"Failed to fetch items from collection {collection_id}: {items_response.status_code}", collection_id, "N/A"

        items_data = items_response.json()
        features = items_data.get("features", [])
        if not features:
            return False, f"No items found in collection {collection_id}", collection_id, "N/A"

        random_item = random.choice(features)
        required_keys = ["id", "type", "geometry", "properties"]
        missing_keys = [key for key in required_keys if key not in random_item]
        if missing_keys:
            return False, f"Random item missing required keys: {missing_keys}", collection_id, random_item.get("id", "N/A")

        return True, "Random item test passed", collection_id, random_item.get("id", "N/A")

    except Exception as e:
        return False, f"Exception occurred: {str(e)}", "N/A", "N/A"

if __name__ == "__main__":
    success, message, collection_id, item_id = get_random_item()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    result = "success" if success else "failure"
    collection_id = collection_id or "N/A"
    item_id = item_id or "N/A"

    log_entry = f"{timestamp}, {result}, collection: {collection_id}, item: {item_id}"
    if not success:
        log_entry += f", reason: {message or 'Unknown error'}"

    log_dir = "results/logs/"
    os.makedirs(log_dir, exist_ok=True)

    with open(os.path.join(log_dir, "latest_test.log"), "a") as log_file:
        log_file.write(log_entry + "\n")

    exit(0 if success else 1)
