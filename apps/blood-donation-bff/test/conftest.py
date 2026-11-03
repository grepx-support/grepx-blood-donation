import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import os

os.environ["AUTH_DB_PATH"] = ":memory:"  # credentials stay in memory during tests
