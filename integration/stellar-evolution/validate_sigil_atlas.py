"""Validate Sigil Atlas assets from the command line."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from SigilAtlas.validators import validate_atlas_directory


def main() -> int:
    issues = validate_atlas_directory(REPO_ROOT)
    if issues:
        for issue in issues:
            print(issue)
        return 1
    print("Sigil Atlas validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
