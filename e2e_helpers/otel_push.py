# e2e_helpers/otel_push.py
# Detailed per-probe metrics (several values per run, extra attributes like probe/collection).
# environment and service.name are resource attributes, the same labels push_e2e_result uses.
import os, logging
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import Resource

OTEL_ENDPOINT = os.environ.get("OTEL_ENDPOINT", "https://otel.observability.eodc.eu/v1/metrics")
OTEL_API_KEY  = os.environ.get("OTEL_API_KEY")

log = logging.getLogger(__name__)

_provider = None
_meter    = None
_gauges: dict = {}


def _init(service: str):
    global _provider, _meter
    if _provider is None:
        resource = Resource(attributes={
            "environment":  os.environ.get("E2E_ENV", "dev"),
            "service.name": service,
            "datacenter":   "vienna",
            "team":         "access",
        })
        headers   = {"Authorization": f"Bearer {OTEL_API_KEY}"} if OTEL_API_KEY else {}
        exporter  = OTLPMetricExporter(endpoint=OTEL_ENDPOINT, headers=headers)
        reader    = PeriodicExportingMetricReader(exporter, export_interval_millis=3_600_000)
        _provider = MeterProvider(metric_readers=[reader], resource=resource)
        _meter    = _provider.get_meter("eodc.e2e")


def record(metrics: dict, attributes: dict, service: str = "stac"):
    """Stage metric values for the given attribute set. Buffered until flush()."""
    _init(service)
    for name, value in metrics.items():
        if name not in _gauges:
            _gauges[name] = _meter.create_gauge(name)
        _gauges[name].set(float(value), attributes)
    log.info("recorded  attrs=%s  metrics=%s", attributes,
             {k: round(v, 4) if isinstance(v, float) else v for k, v in metrics.items()})


def flush():
    """Export all recorded metrics to the OTel collector. Call once at script end."""
    if _provider:
        ok = _provider.force_flush(timeout_millis=10_000)
        _provider.shutdown()
        if ok:
            log.info("otel metrics flushed to %s", OTEL_ENDPOINT)
        else:
            log.error("otel export FAILED — metrics not delivered to %s", OTEL_ENDPOINT)
