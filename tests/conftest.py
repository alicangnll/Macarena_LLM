import sys
from pathlib import Path

# Make the repo root importable when running pytest without installing the package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
