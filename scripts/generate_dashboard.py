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
    try:
        with open(json_file, "r") as file:
            status_data = json.load(file)
    except json.JSONDecodeError:
        print("⚠ Fehler beim Laden von status_data.json, erstelle neues JSON.")
        status_data = {}
else:
    status_data = {}

def parse_log(file_path, service_name):
    """Liest die letzten 100 Einträge für Dask Gateway & openEO API, 
       STAC API & Notebooks speichern nur den letzten Eintrag."""
    try:
        with open(file_path, "r") as file:
            lines = file.readlines()
            if not lines:
                return [], "Never Tested", "UNKNOWN", None  

            entries = []
            last_status = "UNKNOWN"
            last_timestamp = "Never Tested"
            last_extra_info = None

            for line in lines[-100:]:  
                line = line.strip()

                if service_name == "Dask Gateway":
                    parts = line.split(" - ")
                    if len(parts) == 2:
                        timestamp, status = parts
                        status_numeric = 1 if status.upper() == "SUCCESS" else 0
                        entries.append({
                            "timestamp": timestamp,
                            "status": status_numeric,
                            "extra_info": None
                        })
                        last_timestamp, last_status = timestamp, status

                elif service_name == "openEO API":
                    parts = line.split(", ")
                    if len(parts) >= 3:
                        timestamp, status, collection = parts[:3]
                        status_numeric = 1 if status.upper() == "SUCCESS" else 0
                        entries.append({
                            "timestamp": timestamp,
                            "status": status_numeric,
                            "extra_info": collection.replace("collection: ", "")
                        })
                        last_timestamp, last_status = timestamp, status 

                elif service_name == "STAC API":
                    parts = line.split(", ")
                    if len(parts) >= 4:
                        timestamp, status, collection, item = parts[:4]
                        last_timestamp, last_status = timestamp, status 
                        last_extra_info = f"Collection: {collection}, Item: {item}"

                elif service_name == "Notebooks":
                    parts = line.split(" - ")
                    if len(parts) >= 4:
                        timestamp = parts[0]
                        status = parts[1]
                        notebook_name = parts[-1]
                        last_timestamp, last_status = timestamp, status 
                        last_extra_info = f"Notebook: {notebook_name}"

            return entries, last_timestamp, last_status, last_extra_info

    except FileNotFoundError:
        return [], "Never Tested", "UNKNOWN", None

for service_name, log_file in services.items():
    log_path = os.path.join(log_dir, log_file)
    entries, last_timestamp, last_status, last_extra_info = parse_log(log_path, service_name)

    if service_name in ["Dask Gateway", "openEO API"]:
        if service_name in status_data:
            old_history = status_data[service_name].get("history", [])
            new_history = old_history + entries
            status_data[service_name]["history"] = new_history[-100:]  
        else:
            status_data[service_name] = {
                "timestamp": last_timestamp,
                "status": last_status,  # SUCCESS oder FAILURE
                "extra_info": last_extra_info,
                "history": entries[-100:]  
            }
    else:
        status_data[service_name] = {
            "timestamp": last_timestamp,
            "status": last_status,  
            "extra_info": last_extra_info
        }

os.makedirs(docs_dir, exist_ok=True)

with open(json_file, "w") as file:
    json.dump(status_data, file, indent=4)
