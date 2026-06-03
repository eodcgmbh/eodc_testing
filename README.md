# eodc_testing

Automated end-to-end tests for EODC services, running via GitHub Actions.

## Tests

| Workflow | What it tests | Schedule |
|---|---|---|
| `test_stac_api` | STAC API endpoints and spec compliance | every 30 min |
| `test_openEO` | openEO API | every 10 min |
| `test_openstack` | OpenStack VM provisioning | every hour |
| `test_DaskGateway` | Dask Gateway | on push |
| `test_s2_datacube` | S2 datacube access | daily 07:00 UTC |
| `test_notebooks` | EODC example notebooks | on push |
| `test_jupyterhub_eodc` | EODC JupyterHub | every 30 min |
| `test_jupyterhub_eopf` | EOPF JupyterHub | every 30 min |

## Running locally

```bash
pip install -r requirements.txt
python scripts/<test_script>.py
```

## Results

Results can be found as Dashboards in Grafana.