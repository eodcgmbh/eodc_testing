import os
import json
import time
import random
from datetime import datetime, timezone
import requests
from requests import RequestException
import jsonschema

STAC_URL = "https://stac.eodc.eu/api/v1"
ITEM_SCHEMA_URL = "https://schemas.stacspec.org/v1.1.0/item-spec/json-schema/item.json"
TIMEOUT = 20  # Sekunden

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def fetch_json(url: str, what: str):
    """GET JSON ohne raise_for_status; gibt (ok, data_or_msg, meta) zurück."""
    t0 = time.monotonic()
    try:
        resp = requests.get(url, timeout=TIMEOUT)
        latency_ms = int((time.monotonic() - t0) * 1000)
        meta = {"url": url, "what": what, "http_status": resp.status_code, "latency_ms": latency_ms}
        if resp.status_code != 200:
            return False, f"{what} failed: HTTP {resp.status_code}", meta
        return True, resp.json(), meta
    except RequestException as e:
        latency_ms = int((time.monotonic() - t0) * 1000)
        return False, f"{what} request exception: {e}", {"url": url, "what": what, "http_status": None, "latency_ms": latency_ms}
    except ValueError as e:
        latency_ms = int((time.monotonic() - t0) * 1000)
        return False, f"{what} JSON decode error: {e}", {"url": url, "what": what, "http_status": None, "latency_ms": latency_ms}

def get_stac_item_schema():
    ok, data, meta = fetch_json(ITEM_SCHEMA_URL, "Fetch STAC item schema")
    return ok, data, meta

def validate_item_schema(item, schema):
    try:
        jsonschema.validate(instance=item, schema=schema)
        return True, "Item is valid according to STAC 1.1.0 schema"
    except jsonschema.exceptions.ValidationError as e:
        return False, f"Item validation failed: {e.message} at {list(e.path)} (validator: {e.validator}, expected: {e.validator_value})"
    except jsonschema.exceptions.SchemaError as e:
        return False, f"Schema error: {e}"

def get_random_item_and_validate():
    # Collections
    ok, collections_payload, meta_col = fetch_json(f"{STAC_URL}/collections", "Fetch collections")
    if not ok:
        return False, ok, "N/A", "N/A", meta_col, "collections"

    collections = collections_payload.get("collections", [])
    if not collections:
        return False, "No collections found", "N/A", "N/A", meta_col, "collections"

    random_collection = random.choice(collections)
    collection_id = random_collection.get("id")
    if not collection_id:
        return False, "Collection has no 'id'", "N/A", "N/A", meta_col, "collections"

    # Items
    ok, items_payload, meta_items = fetch_json(f"{STAC_URL}/collections/{collection_id}/items", f"Fetch items from '{collection_id}'")
    if not ok:
        return False, items_payload, collection_id, "N/A", meta_items, "items"

    items = items_payload.get("features", [])
    if not items:
        return False, f"No items in collection {collection_id}", collection_id, "N/A", meta_items, "items"

    random_item = random.choice(items)
    item_id = random_item.get("id", "N/A")

    # Schema
    ok, schema_or_msg, meta_schema = get_stac_item_schema()
    if not ok:
        return False, schema_or_msg, collection_id, item_id, meta_schema, "schema"

    is_valid, validation_message = validate_item_schema(random_item, schema_or_msg)
    if not is_valid:
        return False, validation_message, collection_id, item_id, {"url": ITEM_SCHEMA_URL, "what": "validate item", "http_status": 200, "latency_ms": None}, "validation"

    return True, "STAC item is valid and conforms to 1.1.0 schema", collection_id, item_id, {"url": None, "what": "ok", "http_status": 200, "latency_ms": None}, "ok"

def write_logs(json_record, text_record):
    log_dir = "results/logs/"
    os.makedirs(log_dir, exist_ok=True)
    # JSONL (für Grafana/Loki)
    with open(os.path.join(log_dir, "test_stac_api.jsonl"), "a") as jf:
        jf.write(json.dumps(json_record, ensure_ascii=False) + "\n")
    # Optional: alte Textlog weiter pflegen
    with open(os.path.join(log_dir, "test_stac_api.log"), "a") as lf:
        lf.write(text_record + "\n")

if __name__ == "__main__":
    success, message, collection_id, item_id, meta, stage = get_random_item_and_validate()

    record = {
        "ts": now_iso(),
        "service": "stac",
        "stage": stage,  # "collections" | "items" | "schema" | "validation" | "ok"
        "status": "success" if success else "failed",
        "message": message,
        "url": meta.get("url"),
        "http_status": meta.get("http_status"),
        "latency_ms": meta.get("latency_ms"),
        "collection_id": collection_id or "N/A",
        "item_id": item_id or "N/A",
        "stac_base": STAC_URL,
        "schema_url": ITEM_SCHEMA_URL,
    }

    # menschenlesbare Kurzfassung (falls du sie magst)
    if success:
        text = f"{record['ts']}, success, collection: {record['collection_id']}, item: {record['item_id']}"
    else:
        # z.B.: failed: Fetch collections failed: HTTP 502 …
        text = (f"{record['ts']}, failed: {record['message']}, "
                f"stage: {record['stage']}, http_status: {record['http_status']}, "
                f"url: {record['url']}, collection: {record['collection_id']}, item: {record['item_id']}")

    write_logs(record, text)
    exit(0 if success else 1)
