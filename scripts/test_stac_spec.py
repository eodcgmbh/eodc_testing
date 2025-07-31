import requests
import json
import os
from jsonschema import validate, ValidationError
from datetime import datetime
from jinja2 import Template

# Konfiguration
API_URL = "https://dev.stac.eodc.eu/api/v1"
HISTORY_FILE = "stac_validation_log_history.json"
HTML_FILE = "docs/stac_report.html"

COLLECTION_SCHEMA_URL = "https://schemas.stacspec.org/v1.0.0/collection-spec/json-schema/collection.json"
ITEM_SCHEMA_URL = "https://schemas.stacspec.org/v1.0.0/item-spec/json-schema/item.json"

TEMPLATE_HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>STAC Validation Report</title>
  <style>
    body { font-family: sans-serif; padding: 2em; }
    table { border-collapse: collapse; width: 100%; }
    td, th { border: 1px solid #ccc; padding: 0.5em; }
    .success { color: green; font-weight: bold; }
    .error { color: red; font-weight: bold; }
  </style>
</head>
<body>
  <h1>STAC API Validation Report</h1>
  <p><strong>API:</strong> {{ api_url }}</p>
  <p><strong>Last Teset:</strong> {{ timestamp }}</p>

  <table>
    <tr>
      <th>Collection</th>
      <th>Item</th>
      <th>Collection Validation</th>
      <th>Item Validation</th>
      <th>Timestamp</th>
    </tr>
    {% for entry in entries %}
    <tr>
      <td>{{ entry.collection }}</td>
      <td>{{ entry.item }}</td>
      <td class="{{ 'success' if entry.collection_validation == 'success' else 'error' }}">
        {{ entry.collection_validation }}
      </td>
      <td class="{{ 'success' if entry.item_validation == 'success' else 'error' }}">
        {{ entry.item_validation }}
      </td>
      <td>{{ entry.timestamp }}</td>
    </tr>
    {% endfor %}
  </table>
</body>
</html>
"""

def load_schema(url):
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

def validate_json(obj, schema):
    try:
        validate(instance=obj, schema=schema)
        return "success"
    except ValidationError as e:
        return f"error: {str(e).splitlines()[0]}"

collection_schema = load_schema(COLLECTION_SCHEMA_URL)
item_schema = load_schema(ITEM_SCHEMA_URL)


collections_resp = requests.get(f"{API_URL}/collections")
collections_resp.raise_for_status()
collections = collections_resp.json().get("collections", [])

if not collections:
    print("❌ Keine Collections gefunden.")
    exit(1)

if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE) as f:
        history = json.load(f)
else:
    history = []

history_dict = {entry["collection"]: entry for entry in history}


for col in collections:
    col_id = col["id"]
    col_val = validate_json(col, collection_schema)

    items_url = f"{API_URL}/collections/{col_id}/items"
    try:
        items_resp = requests.get(items_url)
        items_resp.raise_for_status()
        items = items_resp.json().get("features", [])
        if items:
            item = items[0]
            item_id = item.get("id", "unknown")
            item_val = validate_json(item, item_schema)
        else:
            item_id = "-"
            item_val = "no items"
    except Exception as e:
        item_id = "-"
        item_val = f"error: {str(e)}"

    # Neue Version speichern
    history_dict[col_id] = {
        "timestamp": datetime.utcnow().isoformat(),
        "collection": col_id,
        "collection_validation": col_val,
        "item": item_id,
        "item_validation": item_val
    }

final_history = sorted(history_dict.values(), key=lambda x: x["collection"])

with open(HISTORY_FILE, "w") as f:
    json.dump(final_history, f, indent=2)

html = Template(TEMPLATE_HTML).render(
    api_url=API_URL,
    timestamp=datetime.utcnow().isoformat(),
    entries=final_history
)

with open(HTML_FILE, "w") as f:
    f.write(html)

print(f"{len(final_history)} Collections checked")
print(f"Report saved in: {HTML_FILE}")


