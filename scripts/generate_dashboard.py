import os
import json

log_dir = "results/logs"
docs_dir = "docs"
json_file = os.path.join(docs_dir, "status_data.json")

services = {
    "Dask Gateway": "test_DaskGateway.log",
    "openEO API": "test_openEO.log",
    "STAC API": "latest_test.log",
    "Notebooks": "test_notebooks.log"
}

if os.path.exists(json_file):
    with open(json_file, "r") as file:
        status_data = json.load(file)
else:
    status_data = {}

def parse_log_entry(file_path, service_name):
    try:
        with open(file_path, "r") as file:
            lines = file.readlines()
            if not lines:
                return "Never Tested", "UNKNOWN", None

            last_line = lines[-1].strip()
            parts = last_line.split(" - ")

            timestamp = parts[0]
            status = parts[1].upper()

            if service_name == "Dask Gateway":
                if service_name not in status_data:
                    status_data[service_name] = {"history": []}
                status_data[service_name]["history"].append({"timestamp": timestamp, "status": status})

            return timestamp, status, None

    except Exception as e:
        return "Never Tested", "ERROR", None


for service_name, log_file in services.items():
    log_path = os.path.join(log_dir, log_file)
    result = parse_log_entry(log_path, service_name)

    if result is not None:
        timestamp, status, extra_info = result
        status_data[service_name] = {
            "timestamp": timestamp,
            "status": status,
            "extra_info": extra_info
        }

os.makedirs(docs_dir, exist_ok=True)
with open(json_file, "w") as file:
    json.dump(status_data, file, indent=4)
