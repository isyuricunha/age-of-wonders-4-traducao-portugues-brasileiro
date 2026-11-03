"""Legacy CLI compatibility; no positional translation writes. AGPL-3.0-only."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / "translation-work"))
from toolkit import main
if __name__ == "__main__":
    mapping = {"validate": "check", "build-po": "build", "build-mo": "build"}
    if len(sys.argv) == 2 and sys.argv[1] in mapping:
        raise SystemExit(main([mapping[sys.argv[1]]]))
    print("Use python translation-work/toolkit.py status|apply|check|build. Positional merge is retired to protect stable IDs.", file=sys.stderr)
    raise SystemExit(2)
