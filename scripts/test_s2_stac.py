#!/usr/bin/env python3
import os, sys, time, requests
from datetime import datetime, timedelta
from pystac_client import Client
import zarr
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from e2e_helpers.prom import push_e2e_result

LOG = "results/logs/test_s2_datacube.log"
SERVICE = "s2-datacube"
PATH = "https://data.eodc.eu/collections/S2-L2A-C1"

tiles = ['T32TNS', 'T32TNT', 'T32TPS', 'T32TPT', 'T32TQS', 'T32TQT', 'T32UQU', 
         'T33TUM', 'T33TUN', 'T33TVM', 'T33TVN', 'T33TWM', 'T33TWN', 'T33TXN', 
         'T33UUP', 'T33UVP', 'T33UVQ', 'T33UWP', 'T33UWQ', 'T33UXP', 'T33UXQ',        
        ]

def check_stac():
    bbox = [9.684, 46.072, 17.181, 49.205]
    te = datetime.now()
    ts = te - timedelta(5)
    time = str(ts.strftime("%Y-%m-%d")+"/"+te.strftime("%Y-%m-%d"))

    catalog_ref = 'https://earth-search.aws.element84.com/v1'
    collection_name = 'sentinel-2-c1-l2a'
    catalog = Client.open(catalog_ref)

    search = catalog.search(
        collections=[collection_name],
        bbox = bbox,
        datetime = time,
        max_items=100,
        sortby="properties.datetime"
    )
    items = list(search.items())
    valid_items = []
    for item in items: 
        if item.id.split("_")[1] in tiles:
            valid_items.append(item)
    if len(valid_items) < 1:
        catalog_ref = 'https://stac.dataspace.copernicus.eu/v1/'
        collection_name = 'sentinel-2-l2a'
        catalog = Client.open(catalog_ref)
        search = catalog.search(
            collections=[collection_name],
            bbox = bbox,
            datetime = time,
            max_items=100,
            sortby="properties.datetime"
        )
        items = list(search.items())
        for item in items:
            if items[0].id.split("_")[-2] in tiles:
                valid_items.append(item)
        if len(valid_items) > 0:
            return False, f"AWS missing items for {time}: CDSE: {valid_items}"
        else:
            return False, f"No stac items for {time}"
    else:
        for item in valid_items:
            tile = item.id.split("_")[1]
            path = f"{PATH}/{tile}"
            path_indices = f"{path}/indices"
            indices = zarr.open(path_indices)
            time_ind = indices.time[-1]
            latest = datetime.strptime(str(time_ind)[:19], "%Y-%m-%dT%H:%M:%S")
            if te - latest > timedelta(7):
                return False, f"ERROR: Latest timestep: {latest}"
    return True, "OK"

def ok(resp):
    if not (200 <= resp.status_code < 300):
        return False, f"HTTP {resp.status_code}"
    return True, "OK"

def main():
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    t0 = time.time()
    service = SERVICE

    try:
        msg = ""
        success = True
        r = requests.get(f"{PATH}/T33UWP/indices/.zmetadata", timeout=15)
        okc, msgc = ok(r)
        if not okc:
            success, msg = False, f"Check hda: {PATH}/T33UWP/indices/.zmetadata {msgc}"
        else:
            check, msgc = check_stac()
            if not check:
                success, msg = False, msgc

    except Exception as e:
        success, msg = False, f"Exception: {e}"

    if not success:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        line = f"{ts} - FAILURE - {msg}\n"
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line)

    push_e2e_result(service, success, time.time() - t0)
    if not success:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
