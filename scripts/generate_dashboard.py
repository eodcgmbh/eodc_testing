import os
import json

log_dir = "results/logs"
json_file = "results/status_data.json"

services = {
    "Dask Gateway": "test_DaskGateway.log",
    "openEO API": "test_openEO.log",
    "STAC API": "latest_test.log",
    "Notebooks": "test_notebooks.log"
}

status_data = {}


stac_collections = {}

def parse_log_entry(file_path, service_name):
    try:
        with open(file_path, "r") as file:
            lines = file.readlines()
            if not lines:
                return "Never Tested", "UNKNOWN", None

            if service_name == "Dask Gateway":
                last_line = lines[-1].strip()
                parts = last_line.split(" - ")
                return parts[0], parts[1], None

            elif service_name == "openEO API":
                last_line = lines[-1].strip()
                parts = last_line.split(", ")
                return parts[0], parts[1].upper(), parts[2].replace("collection: ", "")

            elif service_name == "STAC API":
                for line in lines:
                    try:
                        parts = line.strip().split(", ")
                        timestamp = parts[0]
                        status = parts[1].upper()
                        collection = parts[2].replace("collection: ", "")
                        item = parts[3].replace("item: ", "")

                        # Save details for each collection
                        stac_collections[collection] = {
                            "timestamp": timestamp,
                            "status": status,
                            "item": item
                        }
                    except IndexError:
                       return

                return "Multiple Collections", "Multiple Results", stac_collections

            elif service_name == "Notebooks":
                last_timestamp = None
                notebook_results = []
                for line in lines:
                    parts = line.strip().split(" - ")
                    if len(parts) >= 3:
                        last_timestamp = parts[0]
                        notebook_results.append({
                            "notebook": parts[2],
                            "status": parts[1]
                        })
                return last_timestamp, "Notebook Results", notebook_results

    except Exception as e:
        return "Never Tested", "ERROR", None


for service_name, log_file in services.items():
    log_path = os.path.join(log_dir, log_file)
    timestamp, status, extra_info = parse_log_entry(log_path, service_name)
    status_data[service_name] = {
        "timestamp": timestamp,
        "status": status,
        "extra_info": extra_info
    }

os.makedirs("results", exist_ok=True)
with open(json_file, "w") as file:
    json.dump(status_data, file, indent=4)


