# pip install prometheus-client
import os, time
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
try:
    from prometheus_client.exposition import basic_auth_handler
except Exception:
    basic_auth_handler = None

def _pgw_handler():
    u, p = os.getenv("PUSHGATEWAY_USERNAME"), os.getenv("PUSHGATEWAY_PASSWORD")
    if u and p and basic_auth_handler:
        return lambda url, m, t, h, d: basic_auth_handler(url, m, t, h, d, u, p)
    return None

def push_e2e_result(service: str, success: bool, duration_s: float):
    url = os.getenv("PUSHGATEWAY_URL")
    env = os.getenv("E2E_ENV", "dev")
    if not url:
        return
    reg = CollectorRegistry()
    last = Gauge("eodc_e2e_last_result", "1 success, 0 failure", ["service","env"], registry=reg)
    dur  = Gauge("eodc_e2e_test_duration_seconds", "total duration", ["service","env"], registry=reg)
    ts   = Gauge("eodc_e2e_last_success_timestamp", "unix ts", ["service","env"], registry=reg)
    last.labels(service, env).set(1 if success else 0)
    dur.labels(service, env).set(duration_s)
    if success:
        ts.labels(service, env).set(time.time())
    push_to_gateway(url, job="e2e_direct", registry=reg,
                    grouping_key={"env": env}, handler=_pgw_handler(), timeout=15)

def e2e_test(service: str):
    """Decorator: misst Dauer & pushed Erfolg/Fehlschlag automatisch."""
    def deco(fn):
        def wrapper(*args, **kwargs):
            t0 = time.time(); ok = False
            try:
                res = fn(*args, **kwargs)
                ok = True
                return res
            finally:
                push_e2e_result(service, ok, time.time() - t0)
        return wrapper
    return deco

from contextlib import contextmanager
@contextmanager
def e2e_run(service: str):
    t0 = time.time(); ok = False
    try:
        yield
        ok = True
    finally:
        push_e2e_result(service, ok, time.time() - t0)
