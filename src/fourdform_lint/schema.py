from __future__ import annotations

import json
from importlib import resources
from pathlib import Path

import jsonschema


def load_native_form(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_schema() -> dict:
    schema_text = resources.files("fourdform_lint.assets").joinpath("formsSchema.json").read_text(
        encoding="utf-8"
    )
    return json.loads(schema_text)


def validate_native_form(document: dict) -> list[str]:
    schema = load_schema()
    validator = jsonschema.Draft4Validator(schema)
    errors = sorted(validator.iter_errors(document), key=lambda err: list(err.absolute_path))
    messages: list[str] = []
    for error in errors:
        path = ".".join(str(part) for part in error.absolute_path) or "<root>"
        messages.append(f"{path}: {error.message}")
    return messages
