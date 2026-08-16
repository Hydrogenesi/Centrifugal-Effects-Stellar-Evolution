"""Validation helpers for Sigil Atlas assets."""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from .loader import atlas_root, load_manifest, load_operator_classification, load_sigil_record


class SigilAtlasValidationError(ValueError):
    """Raised when Sigil Atlas assets fail validation."""


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _schema_root(atlas_dir: str | Path | None = None) -> Path:
    return atlas_root(atlas_dir) / "schemas"


def load_schema(name: str, atlas_dir: str | Path | None = None) -> dict[str, Any]:
    """Load a JSON schema file."""
    return _read_json(_schema_root(atlas_dir) / name)


def _json_type_name(value: Any) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    if value is None:
        return "null"
    return type(value).__name__


def _matches_type(value: Any, expected: str) -> bool:
    actual = _json_type_name(value)
    if expected == "number":
        return actual in {"number", "integer"}
    return actual == expected


def validate_json_document(document: Any, schema: dict[str, Any], path: str = "$") -> None:
    """Validate a JSON document against the supported subset of JSON Schema."""
    if "type" in schema and not _matches_type(document, schema["type"]):
        raise SigilAtlasValidationError(
            f"{path}: expected {schema['type']}, found {_json_type_name(document)}"
        )

    if "const" in schema and document != schema["const"]:
        raise SigilAtlasValidationError(f"{path}: expected constant {schema['const']!r}")

    if "enum" in schema and document not in schema["enum"]:
        raise SigilAtlasValidationError(f"{path}: expected one of {schema['enum']!r}")

    if "minimum" in schema and document < schema["minimum"]:
        raise SigilAtlasValidationError(f"{path}: expected value >= {schema['minimum']}")

    if "maximum" in schema and document > schema["maximum"]:
        raise SigilAtlasValidationError(f"{path}: expected value <= {schema['maximum']}")

    if "pattern" in schema and isinstance(document, str) and not re.fullmatch(
        schema["pattern"], document
    ):
        raise SigilAtlasValidationError(f"{path}: value {document!r} does not match pattern")

    expected_type = schema.get("type")
    if expected_type == "object":
        required = schema.get("required", [])
        for key in required:
            if key not in document:
                raise SigilAtlasValidationError(f"{path}: missing required property {key!r}")

        properties = schema.get("properties", {})
        additional = schema.get("additionalProperties", True)
        for key, value in document.items():
            if key in properties:
                validate_json_document(value, properties[key], f"{path}.{key}")
            elif additional is False:
                raise SigilAtlasValidationError(f"{path}: unexpected property {key!r}")

    if expected_type == "array":
        if len(document) < schema.get("minItems", 0):
            raise SigilAtlasValidationError(
                f"{path}: expected at least {schema['minItems']} items"
            )
        if "maxItems" in schema and len(document) > schema["maxItems"]:
            raise SigilAtlasValidationError(
                f"{path}: expected at most {schema['maxItems']} items"
            )
        if schema.get("uniqueItems"):
            seen = set()
            for item in document:
                serialized = json.dumps(item, sort_keys=True)
                if serialized in seen:
                    raise SigilAtlasValidationError(f"{path}: duplicate array item {item!r}")
                seen.add(serialized)
        if "items" in schema:
            for index, item in enumerate(document):
                validate_json_document(item, schema["items"], f"{path}[{index}]")


def extract_svg_metadata(svg_path: str | Path) -> dict[str, Any]:
    """Extract embedded JSON metadata from an SVG."""
    root = ET.parse(svg_path).getroot()
    for element in root.iter():
        if element.tag.endswith("metadata") and element.text and element.text.strip():
            return json.loads(element.text)
    raise SigilAtlasValidationError(f"{svg_path}: missing embedded metadata block")


def validate_directory_structure(atlas_dir: str | Path | None = None) -> None:
    """Validate required Sigil Atlas directories."""
    root = atlas_root(atlas_dir)
    expected = [
        root / "schemas",
        root / "registry",
        root / "registry" / "sigils",
        root / "cards",
        root / "integration-maps",
        root / "ui",
    ]
    missing = [str(path) for path in expected if not path.exists()]
    if missing:
        raise SigilAtlasValidationError(f"Missing required directories: {missing}")


def validate_operator_classification(atlas_dir: str | Path | None = None) -> None:
    """Validate operator taxonomy."""
    schema = load_schema("operator_classification.schema.json", atlas_dir)
    document = load_operator_classification(atlas_dir)
    validate_json_document(document, schema, "$")


def validate_sigil_record(sigil_id: str, atlas_dir: str | Path | None = None) -> None:
    """Validate metadata, card, mapping, and SVG metadata for one sigil."""
    root = atlas_root(atlas_dir)
    record = load_sigil_record(sigil_id, root.parent)

    metadata_schema = load_schema("sigil_metadata.schema.json", root.parent)
    card_schema = load_schema("sigil_card.schema.json", root.parent)
    mapping_schema = load_schema("stellar_mapping.schema.json", root.parent)
    svg_schema = load_schema("sigil_svg_metadata.schema.json", root.parent)

    svg_metadata = extract_svg_metadata(record["svgPath"])

    validate_json_document(record["metadata"], metadata_schema, "$")
    validate_json_document(record["card"], card_schema, "$")
    validate_json_document(record["mapping"], mapping_schema, "$")
    validate_json_document(svg_metadata, svg_schema, "$")

    metadata = record["metadata"]
    mapping = record["mapping"]
    card = record["card"]

    if metadata["id"] != sigil_id or card["sigilId"] != sigil_id or mapping["sigilId"] != sigil_id:
        raise SigilAtlasValidationError(f"Sigil identifiers are inconsistent for {sigil_id}")

    if svg_metadata["sigilId"] != sigil_id:
        raise SigilAtlasValidationError(f"Embedded SVG metadata does not match {sigil_id}")

    if metadata["stellarIntegration"]["mappingFile"] != f"integration-maps/{sigil_id}.json":
        raise SigilAtlasValidationError(f"Unexpected mapping file reference for {sigil_id}")

    allowed_parameters = set(metadata["stellarIntegration"]["compatibility"]["supportedParameters"])
    for override in mapping["parameterOverrides"]:
        if override["parameter"] not in allowed_parameters:
            raise SigilAtlasValidationError(
                f"{sigil_id}: unsupported mapped parameter {override['parameter']!r}"
            )
        expected_semantics = "multiplier" if override["effect"] == "scale" else "absolute"
        if override["valueSemantics"] != expected_semantics:
            raise SigilAtlasValidationError(
                f"{sigil_id}: {override['parameter']} has inconsistent value semantics"
            )
        if override["minValue"] > override["maxValue"]:
            raise SigilAtlasValidationError(
                f"{sigil_id}: {override['parameter']} has an invalid range declaration"
            )
        if not override["minValue"] <= override["value"] <= override["maxValue"]:
            raise SigilAtlasValidationError(
                f"{sigil_id}: {override['parameter']} is outside declared range"
            )


def validate_manifest(atlas_dir: str | Path | None = None) -> None:
    """Validate the registry manifest and its file references."""
    root = atlas_root(atlas_dir)
    schema = load_schema("manifest.schema.json", root.parent)
    manifest = load_manifest(root.parent)
    validate_json_document(manifest, schema, "$")

    for entry in manifest["sigils"]:
        sigil_root = root / "registry" / "sigils" / entry["id"]
        expected_files = [
            sigil_root / "metadata.json",
            sigil_root / "sigil.svg",
            root / "cards" / f"{entry['id']}.json",
            root / "integration-maps" / f"{entry['id']}.json",
        ]
        for path in expected_files:
            if not path.exists():
                raise SigilAtlasValidationError(f"Manifest entry {entry['id']} is missing {path}")


def validate_atlas_directory(atlas_dir: str | Path | None = None) -> list[str]:
    """Run full Sigil Atlas validation and return a list of issues."""
    root = atlas_root(atlas_dir)
    issues: list[str] = []
    manifest: dict[str, Any] | None = None

    try:
        validate_directory_structure(root.parent)
    except (SigilAtlasValidationError, FileNotFoundError, json.JSONDecodeError) as error:
        issues.append(str(error))

    try:
        validate_operator_classification(root.parent)
    except (SigilAtlasValidationError, FileNotFoundError, json.JSONDecodeError) as error:
        issues.append(str(error))

    try:
        validate_manifest(root.parent)
        manifest = load_manifest(root.parent)
    except (SigilAtlasValidationError, FileNotFoundError, json.JSONDecodeError) as error:
        issues.append(str(error))
        return issues

    for entry in manifest["sigils"]:
        try:
            validate_sigil_record(entry["id"], root.parent)
        except SigilAtlasValidationError as error:
            issues.append(str(error))
    return issues
