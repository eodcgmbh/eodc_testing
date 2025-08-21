import os, time
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
from prometheus_client.exposition import basic_auth_handler as _bah

def push_e2e_result(service: str, success: bool, duration_s: float):
    url  = os.getenv("PUSHGATEWAY_URL")
    if not url: return
    env  = os.getenv("E2E_ENV", "dev")
    user = os.getenv("PUSHGATEWAY_USERNAME"); pwd = os.getenv("PUSHGATEWAY_PASSWORD")

    reg = CollectorRegistry()

    g_last = Gauge("eodc_e2e_last_result", "1 success, 0 failure", registry=reg)
    g_dur  = Gauge("eodc_e2e_test_duration_seconds", "total duration", registry=reg)
    g_ts   = Gauge("eodc_e2e_last_success_timestamp", "unix ts last success", registry=reg)

    g_last.set(1 if success else 0)
    g_dur.set(duration_s)
    if success:
        g_ts.set(time.time())

    handler = None
    if user and pwd:
        def handler(url, method, timeout, headers, data):
            return _bah(url, method, timeout, headers, data, user, pwd)

    push_to_gateway(
        url,
        job="e2e_direct",
        registry=reg,
        grouping_key={"env": env, "service": service},
        handler=handler,
        timeout=15,
    )
