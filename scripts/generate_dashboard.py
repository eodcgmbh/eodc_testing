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

                        stac_collections[collection] = {
                            "timestamp": timestamp,
                            "status": status,
                            "item": item
                        }
                    except IndexError:
                        continue  

                return stac_collections

            elif service_name == "Notebooks":
                last_timestamp = None
                notebook_results = []
                for line in lines:
                    # Check if the line is formatted correctly
                    parts = line.strip().split(" - ")
                    if len(parts) >= 4:
                        last_timestamp = parts[0]
                        notebook_results.append({
                            "notebook": parts[-1],
                            "status": parts[1],
                            "message": parts[-2]
                        })
                    else:
                        print(f"Skipping line due to format issue: {line.strip()}")
        
                if notebook_results:
                    return last_timestamp, notebook_results
                else:
                    return "Never Tested", "UNKNOWN", None  # In case no valid notebook data is found

    except Exception as e:
        print(f"Error parsing log for {service_name}: {e}")
        return "Never Tested", "ERROR", None


for service_name, log_file in services.items():
    log_path = os.path.join(log_dir, log_file)
    result = parse_log_entry(log_path, service_name)

    if isinstance(result, dict):  # STAC API returns a dictionary (collections)
        status_data[service_name] = {
            "timestamp": "Multiple Collections",
            "status": "Multiple Results",
            "extra_info": result 
        }
    elif isinstance(result, tuple) and len(result) == 3:  # Other services return a tuple of 3 values
        timestamp, status, extra_info = result
        status_data[service_name] = {
            "timestamp": timestamp,
            "status": status,
            "extra_info": extra_info
        }
    else:
        # In case of unexpected results
        status_data[service_name] = {
            "timestamp": "Never Tested",
            "status": "ERROR",
            "extra_info": None
        }

os.makedirs("results", exist_ok=True)
with open(json_file, "w") as file:
    json.dump(status_data, file, indent=4)

