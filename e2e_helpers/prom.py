import os, time
from urllib.error import HTTPError
from prometheus_client import CollectorRegistry, Gauge, pushadd_to_gateway
from prometheus_client.exposition import basic_auth_handler as _bah

def push_e2e_result(service: str, success: bool, duration_s: float) -> None:
    url = os.getenv("PUSHGATEWAY_URL")
    if not url:
        return
    env  = os.getenv("E2E_ENV", "dev").strip().lower()
    user = os.getenv("PUSHGATEWAY_USERNAME")
    pwd  = os.getenv("PUSHGATEWAY_PASSWORD")

    reg = CollectorRegistry()
    Gauge("eodc_e2e_last_result", "1 success, 0 failure", registry=reg).set(1 if success else 0)
    Gauge("eodc_e2e_test_duration_seconds", "total duration", registry=reg).set(float(duration_s))
    if success:
        Gauge("eodc_e2e_last_success_timestamp", "unix ts last success", registry=reg).set(time.time())

    handler = None
    if user and pwd:
        def handler(url, method=None, timeout=None, headers=None, data=None, **kwargs):
            return _bah(url, method, timeout, headers, data, user, pwd)

    try:
        pushadd_to_gateway(
            url,
            job="e2e_direct",
            registry=reg,
            grouping_key={"env": env, "service": service.strip().lower()},
            handler=handler,
            timeout=15,
        )
    except HTTPError as e:
        try:
            print("Pushgateway error body:", e.read().decode("utf-8", "ignore"))
        finally:
            raise
