"""Compatibility entry point; maintained implementation lives under translation-work/."""
import runpy
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / "translation-work"))
from toolkit import main
if __name__ == "__main__":
    raise SystemExit(main(['status']))
