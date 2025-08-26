import os
import time
import base64
import openstack
import sys
import time
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__))) 
from e2e_helpers.prom import push_e2e_result

LOGFILE = "results/logs/test_openstack.log"

def log_result(status, message=""):
    os.makedirs(os.path.dirname(LOGFILE), exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOGFILE, "a") as log:
        log.write(f"{timestamp}, {status}, {message}\n")

def main():
    t0 = time.time()
    service = "openstack"
    success = False
    server = None

    try:
        conn = openstack.connect(cloud="eodc-appcred")

        IMAGE_ID = os.getenv("OPENSTACK_IMAGE_ID")
        FLAVOR_ID = os.getenv("OPENSTACK_FLAVOR_ID")
        NETWORK_ID = os.getenv("OPENSTACK_NETWORK_ID")
        SECURITY_GROUP = "default"

        if not all([IMAGE_ID, FLAVOR_ID, NETWORK_ID]):
            raise RuntimeError("Missing OPENSTACK_* IDs")

        vm_name = "vm-test-" + datetime.utcnow().strftime("%Y%m%d-%H%M%S")

        cloud_init = """#!/bin/bash
echo $((17 * 3)) > /tmp/result.txt
"""
        user_data = base64.b64encode(cloud_init.encode("utf-8")).decode("utf-8")

        server = conn.compute.create_server(
            name=vm_name,
            image_id=IMAGE_ID,
            flavor_id=FLAVOR_ID,
            networks=[{"uuid": NETWORK_ID}],
            security_groups=[{"name": SECURITY_GROUP}],
            user_data=user_data,
        )

        server = conn.compute.wait_for_server(
            server, status="ACTIVE", failures=["ERROR"], interval=5, wait=300
        )

        success = True
        log_result("SUCCESS", server.name)

    except Exception as e:
        log_result("FAILURE", str(e))

    finally:
        try:
            if server:
                conn.compute.delete_server(server.id)
        except Exception:
            pass
        push_e2e_result(service, success, time.time() - t0)

if __name__ == "__main__":
    main()
