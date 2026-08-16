"""Load Sigil Atlas manifests, sigils, cards, and mappings."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def repository_root() -> Path:
    """Return the repository root."""
    return Path(__file__).resolve().parent.parent


def atlas_root(repo_root: str | Path | None = None) -> Path:
    """Return the Sigil Atlas root."""
    return Path(repo_root or repository_root()) / "SigilAtlas"


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_manifest(atlas_dir: str | Path | None = None) -> dict[str, Any]:
    """Load the atlas manifest."""
    return _read_json(atlas_root(atlas_dir) / "registry" / "manifest.json")


def load_operator_classification(atlas_dir: str | Path | None = None) -> dict[str, Any]:
    """Load operator classes and taxonomy."""
    return _read_json(atlas_root(atlas_dir) / "registry" / "operator-classes.json")


def load_card(sigil_id: str, atlas_dir: str | Path | None = None) -> dict[str, Any]:
    """Load the card model for a sigil."""
    return _read_json(atlas_root(atlas_dir) / "cards" / f"{sigil_id}.json")


def load_mapping(sigil_id: str, atlas_dir: str | Path | None = None) -> dict[str, Any]:
    """Load the stellar-evolution mapping for a sigil."""
    return _read_json(atlas_root(atlas_dir) / "integration-maps" / f"{sigil_id}.json")


def load_sigil_record(sigil_id: str, atlas_dir: str | Path | None = None) -> dict[str, Any]:
    """Load the full sigil record."""
    root = atlas_root(atlas_dir)
    metadata_path = root / "registry" / "sigils" / sigil_id / "metadata.json"
    metadata = _read_json(metadata_path)
    svg_path = root / metadata["svg"]["file"]

    record = {
        "id": sigil_id,
        "metadata": metadata,
        "card": load_card(sigil_id, root.parent),
        "mapping": load_mapping(sigil_id, root.parent),
        "svgPath": svg_path,
    }
    return record


def load_registry(atlas_dir: str | Path | None = None) -> dict[str, Any]:
    """Load the atlas manifest, classes, and all sigils."""
    root = atlas_root(atlas_dir)
    manifest = load_manifest(root.parent)
    sigils = [load_sigil_record(entry["id"], root.parent) for entry in manifest["sigils"]]
    return {
        "manifest": manifest,
        "operatorClasses": load_operator_classification(root.parent),
        "sigils": sigils,
    }
