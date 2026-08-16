"""Build stellar-evolution input dictionaries from Sigil Atlas mappings."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from SigilAtlas.loader import load_sigil_record
from SigilAtlas.validators import SigilAtlasValidationError, validate_sigil_record

try:
    from stellar_evolution import initial_conditions as _initial_conditions
except ModuleNotFoundError as error:
    if error.name not in {"stellar_evolution", "numpy", "scipy", "matplotlib"}:
        raise

    def _initial_conditions(_: float) -> list[float]:
        return [1.0e3, 1.0e26, 1.0e7]

SUPPORTED_PARAMETERS = {
    "mass",
    "initial_density",
    "initial_luminosity",
    "initial_temperature",
    "time_start",
    "time_stop",
    "num_steps",
    "rotation_factor",
    "centrifugal_enhancement",
    "evolution_track_variant",
}


def _apply_override(current: float, override: dict[str, Any]) -> float:
    if override["effect"] == "set":
        return override["value"]
    if override["effect"] == "scale":
        return current * override["value"]
    raise SigilAtlasValidationError(f"Unsupported override effect {override['effect']!r}")


def build_simulation_input(sigil_id: str, mass: float = 1.0e30) -> dict[str, Any]:
    """Build a stellar-evolution input payload for one sigil."""
    validate_sigil_record(sigil_id, REPO_ROOT)
    record = load_sigil_record(sigil_id, REPO_ROOT)

    overrides = {item["parameter"]: item for item in record["mapping"]["parameterOverrides"]}
    unknown_parameters = set(overrides) - SUPPORTED_PARAMETERS
    if unknown_parameters:
        raise SigilAtlasValidationError(f"Unknown parameters: {sorted(unknown_parameters)!r}")

    effective_mass = mass
    if "mass" in overrides:
        effective_mass = _apply_override(effective_mass, overrides["mass"])

    density, luminosity, temperature = _initial_conditions(effective_mass)
    config = {
        "format": "stellar-evolution:v1",
        "sigilId": sigil_id,
        "mass": effective_mass,
        "time_grid": {
            "start": 1.0e5,
            "stop": 1.0e10,
            "num_steps": 1000,
        },
        "initial_state": {
            "density": density,
            "luminosity": luminosity,
            "temperature": temperature,
        },
        "annotations": {
            "rotation_factor": 1.0,
            "centrifugal_enhancement": 0.0,
            "evolution_track_variant": 0,
        },
    }

    state_keys = {
        "initial_density": ("initial_state", "density"),
        "initial_luminosity": ("initial_state", "luminosity"),
        "initial_temperature": ("initial_state", "temperature"),
    }
    grid_keys = {
        "time_start": ("time_grid", "start"),
        "time_stop": ("time_grid", "stop"),
        "num_steps": ("time_grid", "num_steps"),
    }

    for parameter, override in overrides.items():
        if parameter in {"mass"}:
            continue
        if parameter in state_keys:
            section, key = state_keys[parameter]
            config[section][key] = _apply_override(config[section][key], override)
        elif parameter in grid_keys:
            section, key = grid_keys[parameter]
            config[section][key] = _apply_override(config[section][key], override)
        elif parameter in config["annotations"]:
            config["annotations"][parameter] = _apply_override(config["annotations"][parameter], override)

    config["time_grid"]["num_steps"] = int(round(config["time_grid"]["num_steps"]))
    config["annotations"]["evolution_track_variant"] = int(
        round(config["annotations"]["evolution_track_variant"])
    )
    return config


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: python integration/stellar-evolution/export_sigil_parameters.py <sigil-id> [mass]")
        return 1

    sigil_id = argv[1]
    mass = float(argv[2]) if len(argv) > 2 else 1.0e30
    config = build_simulation_input(sigil_id, mass)
    print(json.dumps(config, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
