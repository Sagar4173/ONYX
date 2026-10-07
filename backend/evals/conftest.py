"""Make the backend package importable when running `pytest evals/`."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
