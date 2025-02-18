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

# Lade bestehendes JSON, falls vorhanden
if os.path.exists(json_file):
    with open(json_file, "r") as file:
        try:
            status_data = json.load(file)
        except json.JSONDecodeError:
            status_data = {}
else:
    status_data = {}

def parse_dask_log(file_path):
    """ Liest die letzten 100 Einträge aus dem Dask Gateway Log und gibt den letzten Status zurück. """
    try:
        with open(file_path, "r") as file:
            lines = file.readlines()
            if not lines:
                return [], "Never Tested", 0, None  # Fehlerwert als 0

            entries = []
            for line in lines[-100:]:  # Nur die letzten 100 Einträge speichern
                line = line.strip()
                parts = line.split(" - ")
                if len(parts) == 2:
                    timestamp, status = parts
                    # Konvertiere "SUCCESS" zu 1, "FAILURE" zu 0
                    status_numeric = 1 if status.upper() == "SUCCESS" else 0
                    entries.append({
                        "timestamp": timestamp,
                        "status": status_numeric,
                        "extra_info": None
                    })
            
            # Der letzte Eintrag wird als aktueller Status genutzt
            last_entry = entries[-1] if entries else {"timestamp": "Never Tested", "status": 0, "extra_info": None}
            return entries, last_entry["timestamp"], last_entry["status"], last_entry["extra_info"]

    except FileNotFoundError:
        return [], "Never Tested", 0, None

# Dask Gateway Logs parsen
dask_entries, last_timestamp, last_status, last_extra_info = parse_dask_log(os.path.join(log_dir, services["Dask Gateway"]))

# JSON aktualisieren (nur Dask Gateway!)
status_data["Dask Gateway"] = {
    "timestamp": last_timestamp,
    "status": last_status,  # Jetzt als 1 oder 0 gespeichert
    "extra_info": last_extra_info,
    "history": dask_entries[-100:]  # Maximal 100 Einträge
}

def parse_log_entry(file_path, service_name):
    try:
        with open(file_path, "r") as file:
            lines = file.readlines()
            if not lines:
                return "Never Tested", "UNKNOWN", None

            if service_name == "openEO API":
                last_line = lines[-1].strip()
                parts = last_line.split(", ")
                return parts[0], parts[1].upper(), parts[2].replace("collection: ", "")

            elif service_name == "STAC API":
                stac_collections_dict = {}  

                for line in lines:
                    try:
                        parts = line.strip().split(", ")
                        timestamp = parts[0]
                        status = parts[1].upper()
                        collection = parts[2].replace("collection: ", "")
                        item = parts[3].replace("item: ", "")

                        if collection not in stac_collections_dict or timestamp > stac_collections_dict[collection]["timestamp"]:
                            stac_collections_dict[collection] = {
                                "collection": collection,
                                "timestamp": timestamp,
                                "status": status,
                                "item": item
                            }
                    except IndexError:
                        continue 

                return "Latest Collections", "Filtered Results", list(stac_collections_dict.values())

            elif service_name == "Notebooks":
                last_timestamp = None
                notebook_results = []

                for line in lines:
                    parts = line.strip().split(" - ")
                    if len(parts) >= 4:
                        last_timestamp = parts[0]
                        notebook_results.append({
                            "notebook": parts[-1],
                            "status": parts[1],
                            "message": parts[-2]
                        })
                return last_timestamp, "Notebook Results", notebook_results

    except Exception as e:
        return "Never Tested", "ERROR", None

# JSON für alle anderen Services aktualisieren (Dask bleibt erhalten!)
for service_name, log_file in services.items():
    if service_name == "Dask Gateway":
        continue  # Dask wurde oben verarbeitet

    log_path = os.path.join(log_dir, log_file)
    result = parse_log_entry(log_path, service_name)

    if result is None:
        timestamp, status, extra_info = "Never Tested", "ERROR", None
    else:
        timestamp, status, extra_info = result

    status_data[service_name] = {
        "timestamp": timestamp,
        "status": status,
        "extra_info": extra_info
    }

os.makedirs(docs_dir, exist_ok=True)

with open(json_file, "w") as file:
    json.dump(status_data, file, indent=4)

