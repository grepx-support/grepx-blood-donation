# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""donor-service — wiring comes from config/config.yaml (request table, subscriptions); see grepx_service.serve."""
from grepx_service.serve import serve

if __name__ == "__main__":
    serve(__file__)
