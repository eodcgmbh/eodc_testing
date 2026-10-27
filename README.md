# eodc_testing

Automated end-to-end tests for EODC services, running via GitHub Actions.

## Tests

| Workflow | Script | What it tests | Schedule |
|---|---|---|---|
| `test_stac_api` | `test_stac_api.py` | STAC API endpoints and spec compliance | every 30 min |
| `test_cstac` | `test_cstac.py` | Customer-managed STAC ([cstac.discovery.eodc.eu](https://cstac.discovery.eodc.eu)): landing page, collections, items | every 30 min |
| `test_catalogue` | `test_catalogue.py` | eodc Catalogue ([catalogue.services.eodc.eu](https://catalogue.services.eodc.eu)): up check of landing page and collections | every 30 min |
| `test_DaskGateway` | `test_dask.py` | Dask Gateway: login via `eodc-connect`, cluster creation, simple computation | every 2 h |
| `test_hda_go` | `test_hda_go.py` | HDA go data access | hourly |
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
