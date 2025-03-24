import openstack
from datetime import datetime
import base64
import os

LOGFILE = "results/logs/test_openstack.log"

def log_result(status, message=""):
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    with open(LOGFILE, "a") as log:
        log.write(f"{timestamp}, {status}, {message}\n")

try:
    conn = openstack.connect(cloud="eodc-appcred")

    IMAGE_ID = os.getenv("OPENSTACK_IMAGE_ID")
    FLAVOR_ID = os.getenv("OPENSTACK_FLAVOR_ID")
    NETWORK_ID = os.getenv("OPENSTACK_NETWORK_ID")
    SECURITY_GROUP = "default"

    vm_name = "vm-test-" + datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    print(f"🚀 Erstelle Test-VM: {vm_name}")

    cloud_init = """#!/bin/bash
echo $((17 * 3)) > /tmp/result.txt
"""

    cloud_init_encoded = base64.b64encode(cloud_init.encode("utf-8")).decode("utf-8")

    server = conn.compute.create_server(
        name=vm_name,
        image_id=IMAGE_ID,
        flavor_id=FLAVOR_ID,
        networks=[{"uuid": NETWORK_ID}],
        security_groups=[{"name": SECURITY_GROUP}],
        user_data=cloud_init_encoded
    )

    server = conn.compute.wait_for_server(server, status="ACTIVE", failures=["ERROR"], interval=5, wait=300)

    log_result("SUCCESS", f"{server.name}")

    conn.compute.delete_server(server.id)

except Exception as e:
    log_result("FAILURE", str(e))