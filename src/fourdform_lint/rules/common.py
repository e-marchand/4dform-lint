from __future__ import annotations

from pathlib import Path, PurePosixPath

from ..models import Frame
from ..native import native_event_names


def element_ignores_rule(element_ignores: set[str], rule_id: str) -> bool:
    return rule_id in element_ignores


def frames_intersect(first: Frame, second: Frame) -> bool:
    return (
        first.left < second.right
        and first.right > second.left
        and first.top < second.bottom
        and first.bottom > second.top
    )


def object_method_name(native_object: dict[str, object]) -> str | None:
    value = native_object.get("method")
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def method_value_looks_like_file_reference(method_name: str) -> bool:
    return "/" in method_name or "\\" in method_name or method_name.lower().endswith(".4dm")


def resolve_form_local_method_path(form_path: Path, method_name: str) -> Path:
    return (form_path.parent / _method_reference_path(method_name)).resolve(strict=False)


def method_path_is_within_form_folder(form_path: Path, method_name: str) -> bool:
    form_dir = form_path.parent.resolve(strict=False)
    resolved_path = resolve_form_local_method_path(form_path, method_name)
    try:
        resolved_path.relative_to(form_dir)
    except ValueError:
        return False
    return True


def project_methods_dir_for_form(form_path: Path) -> Path | None:
    current = form_path.parent
    while True:
        if (
            current.name == "Forms"
            and current.parent.name == "Sources"
            and current.parent.parent.name == "Project"
        ):
            return current.parent / "Methods"
        if current.parent == current:
            return None
        current = current.parent


def _method_reference_path(method_name: str) -> Path:
    normalized = method_name.replace("\\", "/")
    return Path(*PurePosixPath(normalized).parts)
