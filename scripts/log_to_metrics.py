import os
import glob
import time
import requests
from datetime import datetime, timedelta

PUSHGATEWAY_URL = os.environ.get("PUSHGATEWAY_URL")
ENV = os.environ.get("E2E_ENV", "dev")
SERVICE = os.environ.get("E2E_SERVICE", "default")

LOG_DIR = "results/logs"
LOG_PATTERN = "test_*.log"

def parse_logs():
    now = datetime.now()
    one_hour_ago = now - timedelta(hours=1)
    last_result = 0
    last_success_ts = 0
    success_count = 0
    failure_count = 0

    for log_file in glob.glob(os.path.join(LOG_DIR, LOG_PATTERN)):
        with open(log_file) as f:
            for line in f:
                # Beispiel: 2025-08-20 12:34:56 - SUCCESS - ... - notebook.ipynb
                parts = line.strip().split(" - ")
                if len(parts) < 3:
                    continue
                ts, status = parts[0], parts[1]
                dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                if dt > one_hour_ago:
                    if status == "SUCCESS":
                        success_count += 1
                        last_success_ts = int(dt.timestamp())
                    elif status == "FAILURE":
                        failure_count += 1
                # Letzter Lauf zählt für last_result
                if dt > now - timedelta(minutes=10):  # Annahme: aktueller Lauf
                    last_result = 1 if status == "SUCCESS" else 0

    total = success_count + failure_count
    availability = success_count / total if total > 0 else 0.0

    return {
        "eodc_e2e_last_result": last_result,
        "eodc_e2e_success_count_1h": success_count,
        "eodc_e2e_failure_count_1h": failure_count,
        "eodc_e2e_availability_ratio_1h": availability,
        "eodc_e2e_last_success_timestamp": last_success_ts,
    }

def push_metrics(metrics):
    labels = f'service="{SERVICE}",env="{ENV}"'
    lines = []
    for k, v in metrics.items():
        lines.append(f'{k}{{{labels}}} {v}')
    data = "\n".join(lines) + "\n"
    url = f"{PUSHGATEWAY_URL}/metrics/job/eodc_e2e"
    resp = requests.post(url, data=data)
    resp.raise_for_status()

if __name__ == "__main__":
    if not PUSHGATEWAY_URL:
        print("PUSHGATEWAY_URL not set")
        exit(1)
    metrics = parse_logs()
    push_metrics(metrics)