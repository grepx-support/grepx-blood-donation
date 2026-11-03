"""blood-donation-bff — the product's API (web + mobile) on the shared grepx_bff core. Wiring only."""
from __future__ import annotations

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))

from grepx_bff import Gateway, create_app as build  # noqa: E402
from nexus_api import NexusClient  # noqa: E402
from grepx_config import load_config

from routers import ROUTERS  # noqa: E402

cfg = load_config(SRC.parent / "config")
WEB = SRC.parent / "web"                     # the original LifeFlow site (Flask pages), on the microservices


def create_app(gw: Gateway):
    """JSON API at /api/v1 (mobile app and integrations); the original web site everywhere else."""
    from product_copy import COPY
    from grepx_bff import register_copy, register_hidden
    register_copy(COPY)
    register_hidden("cal_token")
    api = build(gw, ROUTERS, cfg.get("api_title") or f"{cfg.get('product', '')} API".strip(), web_dir=None, product=cfg.get("product", "blood-donation"))
    sys.path.insert(0, str(WEB))
    from a2wsgi import WSGIMiddleware
    from web_app import create_web_app
    api.mount("/", WSGIMiddleware(create_web_app(gw)))
    return api


if __name__ == "__main__":
    from grepx_web_bootstrap import run_server
    from nexus_api import Heartbeat
    client = NexusClient(cfg.service_name, host=cfg.nexus.host, port=cfg.nexus.port)
    Heartbeat(NexusClient(f"{cfg.service_name}-heartbeat", host=cfg.nexus.host, port=cfg.nexus.port), cfg.service_name).start()
    run_server(create_app(Gateway(client, cfg)), service=cfg.service_name, host=(cfg.get("web") or {}).get("bind", "0.0.0.0"))
