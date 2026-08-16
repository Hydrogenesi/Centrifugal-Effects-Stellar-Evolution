"""Generate an overview plot for mapped Sigil Atlas parameters."""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from SigilAtlas.loader import load_registry


def main() -> int:
    registry = load_registry(REPO_ROOT)
    output_path = REPO_ROOT / "SigilAtlas" / "ui" / "mapping-distribution.png"

    fig, axes = plt.subplots(len(registry["sigils"]), 1, figsize=(9, 4 * len(registry["sigils"])))
    if len(registry["sigils"]) == 1:
        axes = [axes]

    for axis, record in zip(axes, registry["sigils"]):
        overrides = record["mapping"]["parameterOverrides"]
        axis.bar(
            [item["parameter"] for item in overrides],
            [item["value"] for item in overrides],
            color=record["card"]["accent"],
        )
        axis.set_title(record["metadata"]["name"])
        axis.tick_params(axis="x", rotation=35)

    fig.tight_layout()
    fig.savefig(output_path)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
