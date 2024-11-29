import requests
import json
import random
from datetime import datetime

STAC_URL = "https://dev.stac.eodc.eu/api/v1"

def get_random_item():
    """Fetch a random item from the /collections endpoint and validate it."""
    try:
        # get collections
        collections_response = requests.get(f"{STAC_URL}/collections")
        if collections_response.status_code != 200:
            return False, f"Failed to fetch collections: {collections_response.status_code}"

        collections_data = collections_response.json()
        collections = collections_data.get("collections", [])
        if not collections:
            return False, "No collections found in the API"

        # random collection
        random_collection = random.choice(collections)
        collection_id = random_collection.get("id", None)
        if not collection_id:
            return False, "Random collection has no 'id' field"

        # fetch items from the collection
        items_response = requests.get(f"{STAC_URL}/collections/{collection_id}/items")
        if items_response.status_code != 200:
            return False, f"Failed to fetch items from collection {collection_id}: {items_response.status_code}"

        items_data = items_response.json()
        features = items_data.get("features", [])
        if not features:
            return False, f"No features found in collection {collection_id}"

        # random item
        random_item = random.choice(features)
        required_keys = ["id", "type", "geometry", "properties"]
        missing_keys = [key for key in required_keys if key not in random_item]
        if missing_keys:
            return False, f"Random item missing required keys: {missing_keys}", collection_id, random_item.get("id", None)

        return True, "Random item test passed", collection_id, random_item.get("id", None)
    
    # TODO: Defining Exceptions 

    except Exception as e:
        return False, f"Exception occurred: {str(e)}"

if __name__ == "__main__":
    success, message, collection_id, item_id = get_random_item()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    result = "success" if success else "failure"

    log_entry = f"{timestamp}, {result}, collection: {collection_id}, item: {item_id}"
    if not success:
        log_entry += f", reason: {message}"  

    with open("results/logs/latest_test.log", "a") as log_file:  
        log_file.write(log_entry + "\n")


    exit(0 if success else 1)
