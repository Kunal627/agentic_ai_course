from pathlib import Path
import sys


PROJECTS_DIR = Path(__file__).resolve().parents[2]

if str(PROJECTS_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECTS_DIR))