# eodc_testing

Automated end-to-end tests for EODC services, running via GitHub Actions.

## Tests

| Workflow | Script | What it tests | Schedule |
|---|---|---|---|
| `test_stac_api` | `test_stac_api.py` | STAC API availability: root, /collections and for every collection detail, items and search; prod (stac.eodc.eu) and dev (dev.stac.eodc.eu) | every 30 min |
| `test_stac_functional` | `stac_functional/test_stac_functional.py` | STAC functional tests on dev (pytest): known item, search filter, pagination, ingest → visible → delete, asset href format | daily 02:00 UTC |
| `test_stac_performance` | `test_stac_performance.py` | STAC load test with locust (10/25/50/100 users): p50/p95, RPS, error rate for POST /search and GET /items | daily 02:00 UTC (prod), manual for dev |
| `test_cstac` | `test_cstac.py` | Customer-managed STAC ([cstac.discovery.eodc.eu](https://cstac.discovery.eodc.eu)) with login: landing page, collections, items; the logged-in CI user (on the BFW access list) sees all 6 TOPO4EO/BFW collections | every 30 min |
| `test_catalogue` | `test_catalogue.py` | eodc Catalogue: landing page and collections, prod ([catalogue.services.eodc.eu](https://catalogue.services.eodc.eu)) and dev (eodag.development.eodc.eu) | every 30 min |
| `test_orbit` | `test_orbit.py` | Orbit: landing page, `config.json`, `/docs/`, prod ([orbit.discovery.eodc.eu](https://orbit.discovery.eodc.eu)) and dev (orbit.development.eodc.eu) | every 30 min |
| `test_titiler` | `test_titiler.py` | titiler ([titiler.services.eodc.eu](https://titiler.services.eodc.eu)): one PNG tile of a public COG on data.eodc.eu | every 30 min |
| `test_features` | `test_features.py` | Features API ([features.services.eodc.eu](https://features.services.eodc.eu)): landing page | every 30 min |
| `test_data_eodc` | `test_data_eodc.py` | data.eodc.eu: one public asset returns 200 | every 30 min |
| `test_cds_c3s` | `test_cds_c3s.py` | C3S CDS ([cds.c3s.eodc.eu](https://cds.c3s.eodc.eu)): anonymous request gets 401; with Basic Auth the landing page, the `/manifest/` and `/service/` listings and the first 1 MB of one real file in each return OK; pushes `eodc_e2e_probe_*` per probe | every 30 min |
| `test_DaskGateway` | `test_dask.py` | Dask Gateway: login via `eodc-connect`, cluster creation, simple computation | manual only |
| `test_access_control` | `test_access_control.py` | Restricted data stays restricted: anonymous requests to a MAAP, a CDSE and a BFW asset on data.eodc.eu and an anonymous POST /collections on cSTAC must get 401/403, the 5 restricted TOPO4EO/BFW cSTAC collections must be hidden, the public forest_mask collection and one public asset must return 200; prod (data.eodc.eu + cSTAC) and dev (dev.hda.eodchosting.eu) | every 30 min |
| `test_hda_go` | `test_hda_go.py` | HDA data access on [data.eodc.eu](https://data.eodc.eu) (prod) and dev.hda.eodchosting.eu (dev): S1 GeoTIFF and EOPF Zarr | hourly |
| `test_s2_datacube` | `test_hda.py`, `test_s2_stac.py`, `test_s2_datacube.py` | S2 datacube access | daily 07:00 UTC |
| `test_notebooks` | `test_notebooks.py` | EODC example notebooks | on push |
| `test_jupyterhub_eodc` | `test_jupyter.py` | EODC JupyterHub | every 30 min |
| `test_jupyterhub_eopf` | `test_jupyter.py` | EOPF JupyterHub | every 30 min |

All workflows also run on push of their script and can be triggered manually (`workflow_dispatch`).

## Secrets

| Secret | Used by |
|---|---|
| `EODC_USERNAME`, `EODC_PASSWORD` | `test_cstac`, `test_DaskGateway` |
| `EODC_USER`, `EODC_TOKEN` | `test_jupyterhub_eodc` |
| `EOPF_USER`, `EOPF_TOKEN` | `test_jupyterhub_eopf` |
| `INGEST_URL`, `INGEST_USER`, `INGEST_PASSWORD` | `test_stac_functional` (ingest test on dev) |
| `CDS_USERNAME`, `CDS_PASSWORD` | `test_cds_c3s` (Bitwarden: "CDS C3S EODC") |
| `OTEL_API_KEY` | all tests pushing metrics to Grafana |

## Running locally

Run from the repository root:

```bash
pip install -r requirements.txt
python scripts/<test_script>.py
```

Tests that need a login (`test_cstac.py`, `test_dask.py`) read `EODC_USERNAME` / `EODC_PASSWORD` from the environment and otherwise prompt for them:

```bash
export EODC_USERNAME=<user>
read -s EODC_PASSWORD && export EODC_PASSWORD
python scripts/test_cstac.py
```

The cSTAC URL can be overridden with `CSTAC_URL`.

## Results

Test results and durations are pushed as OTel metrics and can be found as dashboards in Grafana.

Every test except `test_notebooks` pushes `eodc_e2e_last_result` (1 = success, 0 = failure), `eodc_e2e_test_duration_seconds` and `eodc_e2e_last_success_timestamp` with the labels `service.name` (the service) and `environment`. The workflows set `E2E_ENV=prod`; `test_stac_api`, `test_catalogue`, `test_orbit` and `test_hda_go` also test the dev instance and report `prod` and `dev` separately.

| `service.name` | Test |
|---|---|
| `stac` | `test_stac_api` |
| `cstac` | `test_cstac` |
| `catalogue` | `test_catalogue` |
| `orbit` | `test_orbit` |
| `titiler` | `test_titiler` |
| `features` | `test_features` |
| `data-eodc` | `test_data_eodc` |
| `cds-c3s` | `test_cds_c3s` |
| `access-control` | `test_access_control` |
| `hda` | `test_hda_go` |
| `dask_gateway` | `test_DaskGateway` |
| `jupyterhub-eodc`, `jupyterhub-eopf` | `test_jupyterhub_eodc`, `test_jupyterhub_eopf` |
| `s2-datacube` | `test_s2_datacube` |

The STAC tests additionally push detailed metrics for the STAC dashboard: `eodc_e2e_probe_*` (labels `probe`, `collection`), `eodc_e2e_functional_*` (label `test`) and `eodc_e2e_perf_*` (labels `endpoint`, `vus`), with the same `environment` and `service.name` labels.

GitHub runs scheduled workflows irregularly (often hours apart instead of every 30 min).
