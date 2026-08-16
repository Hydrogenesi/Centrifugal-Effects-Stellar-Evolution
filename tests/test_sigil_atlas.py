"""Tests for the Sigil Atlas module."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

from SigilAtlas.loader import load_registry, load_sigil_record
from SigilAtlas.validators import extract_svg_metadata, validate_atlas_directory

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_script_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class SigilAtlasTests(unittest.TestCase):
    def test_load_registry(self) -> None:
        registry = load_registry(REPO_ROOT)
        self.assertEqual(registry["manifest"]["atlas"], "Sigil Atlas")
        self.assertEqual(len(registry["sigils"]), 2)

    def test_validate_atlas_directory(self) -> None:
        self.assertEqual(validate_atlas_directory(REPO_ROOT), [])

    def test_svg_metadata_matches_metadata(self) -> None:
        record = load_sigil_record("aurora-spin", REPO_ROOT)
        svg_metadata = extract_svg_metadata(record["svgPath"])
        self.assertEqual(svg_metadata["sigilId"], record["metadata"]["id"])
        self.assertEqual(
            svg_metadata["operatorClass"], record["metadata"]["operatorClass"]
        )

    def test_build_simulation_input(self) -> None:
        module = _load_script_module(
            REPO_ROOT / "integration" / "stellar-evolution" / "export_sigil_parameters.py",
            "export_sigil_parameters",
        )
        config = module.build_simulation_input("kepler-lattice", 1.0e30)
        self.assertEqual(config["format"], "stellar-evolution:v1")
        self.assertGreater(config["initial_state"]["density"], 1.0e3)
        self.assertEqual(config["annotations"]["evolution_track_variant"], 2)


if __name__ == "__main__":
    unittest.main()
