import os, time, logging
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import Resource

OTEL_ENDPOINT = os.environ.get("OTEL_ENDPOINT", "https://otel.infra.eodc.eu/v1/metrics")
OTEL_API_KEY  = os.environ.get("OTEL_API_KEY")

log = logging.getLogger(__name__)


def push_e2e_result(service: str, success: bool, duration_s: float, *, team: str = "access", datacenter: str = "vienna"):
    env = os.environ.get("E2E_ENV", "dev")
    resource = Resource(attributes={
        "environment":  env,
        "service.name": service,
        "datacenter":   datacenter,
        "team":         team,
    })
    headers  = {"Authorization": f"Bearer {OTEL_API_KEY}"} if OTEL_API_KEY else {}
    exporter = OTLPMetricExporter(endpoint=OTEL_ENDPOINT, headers=headers)
    reader   = PeriodicExportingMetricReader(exporter, export_interval_millis=3_600_000)
    provider = MeterProvider(metric_readers=[reader], resource=resource)
    meter    = provider.get_meter("eodc.e2e")

    attrs = {}
    meter.create_gauge("eodc_e2e_last_result").set(1.0 if success else 0.0, attrs)
    meter.create_gauge("eodc_e2e_test_duration_seconds").set(float(duration_s), attrs)
    if success:
        meter.create_gauge("eodc_e2e_last_success_timestamp").set(time.time(), attrs)

    ok = provider.force_flush(timeout_millis=10_000)
    provider.shutdown()
    if ok:
        log.info("otel metrics flushed  service=%s  success=%s  duration=%.2fs", service, success, duration_s)
    else:
        log.error("otel export FAILED — metrics not delivered to %s", OTEL_ENDPOINT)
