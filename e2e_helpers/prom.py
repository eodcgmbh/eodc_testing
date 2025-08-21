# e2e_helpers/prom.py
import os, time
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
try:
    from prometheus_client.exposition import basic_auth_handler
except Exception:
    basic_auth_handler = None

def push_e2e_result(service: str, success: bool, duration_s: float):
    url = os.getenv("PUSHGATEWAY_URL")
    if not url:
        return
    env  = os.getenv("E2E_ENV", "dev")
    user = os.getenv("PUSHGATEWAY_USERNAME")
    pwd  = os.getenv("PUSHGATEWAY_PASSWORD")

    reg = CollectorRegistry()
    g_last = Gauge("eodc_e2e_last_result", "1 success, 0 failure", ["service","env"], registry=reg)
    g_dur  = Gauge("eodc_e2e_test_duration_seconds", "total duration", ["service","env"], registry=reg)
    g_ts   = Gauge("eodc_e2e_last_success_timestamp", "unix ts last success", ["service","env"], registry=reg)

    g_last.labels(service, env).set(1 if success else 0)
    g_dur.labels(service, env).set(duration_s)
    if success:
        g_ts.labels(service, env).set(time.time())

    handler = None
    if user and pwd and basic_auth_handler:
        def handler(url, method, timeout, headers, data):
            return basic_auth_handler(url, method, timeout, headers, data, user, pwd)

    push_to_gateway(
        url,
        job="e2e_direct",
        registry=reg,
        grouping_key={"env": env, "service": service},
        handler=handler,
        timeout=15,
    )
