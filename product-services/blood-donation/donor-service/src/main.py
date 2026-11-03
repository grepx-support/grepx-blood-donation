"""donor-service — wiring comes from config/config.yaml (request table, subscriptions); see grepx_service.serve."""
from grepx_service.serve import serve

if __name__ == "__main__":
    serve(__file__)
