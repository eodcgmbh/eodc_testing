import logging, sys
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
sys.path.insert(0, ".")
from e2e_helpers.prom import push_e2e_result
push_e2e_result("stac", True, 1.23)
