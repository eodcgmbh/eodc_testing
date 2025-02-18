import os
import json

# Verzeichnisse für Logs und JSON-Output
log_dir = "results/logs"
docs_dir = "docs"
json_file = os.path.join(docs_dir, "status_data.json")

services = {
    "Dask Gateway": "test_DaskGateway.log",
    "openEO API": "test_openEO.log",
    "STAC API": "latest_test.log",
    "Notebooks": "test_notebooks.log"
}


status_data = {}

def parse_dask_log(file_path):
    """ Liest die letzten 100 Einträge aus dem Dask Gateway Log und konvertiert SUCCESS/FAILURE in 1/0 """
    try:
        with open(file_path, "r") as file:
            lines = file.readlines()
            if not lines:
                return [], "Never Tested", 0, None  # Falls keine Logs existieren

            entries = []
            for line in lines[-100:]:  # Nur die letzten 100 Einträge speichern
                line = line.strip()
                parts = line.split(" - ")
                if len(parts) == 2:
                    timestamp, status = parts
                    status_numeric = 1 if status.upper() == "SUCCESS" else 0
                    entries.append({
                        "timestamp": timestamp,
                        "status": status_numeric,
                        "extra_info": None
                    })
            
            # Letzten Eintrag als aktuellen Status nutzen
            last_entry = entries[-1] if entries else {"timestamp": "Never Tested", "status": 0, "extra_info": None}
            return entries, last_entry["timestamp"], last_entry["status"], last_entry["extra_info"]

    except FileNotFoundError:
        return [], "Never Tested", 0, None

# Dask Gateway Logs parsen
dask_entries, last_timestamp, last_status, last_extra_info = parse_dask_log(os.path.join(log_dir, services["Dask Gateway"]))

# Falls "Dask Gateway" schon existiert, nur die History aktualisieren
if "Dask Gateway" in status_data:
    old_history = status_data["Dask Gateway"].get("history", [])
    new_history = old_history + dask_entries
    status_data["Dask Gateway"]["history"] = new_history[-100:]  # Letzte 100 Einträge behalten
else:
    status_data["Dask Gateway"] = {
        "timestamp": last_timestamp,
        "status": last_status,  # 1 für SUCCESS, 0 für FAILURE
        "extra_info": last_extra_info,
        "history": dask_entries[-100:]  # Maximal 100 Einträge
    }

# JSON speichern
os.makedirs(docs_dir, exist_ok=True)

with open(json_file, "w") as file:
    json.dump(status_data, file, indent=4)

print("✅ JSON aktualisiert: Letzte 100 Logs für Dask Gateway gespeichert!")
