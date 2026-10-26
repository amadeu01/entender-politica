"""Compilador: the Entender Política data pipeline."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"

# First year collected. Five years before 1980 so 1980 changes have a baseline.
START_YEAR = 1975
