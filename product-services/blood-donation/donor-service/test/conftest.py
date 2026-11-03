"""Put this service's src/ first on sys.path (each service is tested in its own process)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
