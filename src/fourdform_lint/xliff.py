from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree


def load_translation_catalog(form_paths: Iterable[Path]) -> dict[str, tuple[str, ...]]:
    catalog: dict[str, list[str]] = defaultdict(list)
    seen: dict[str, set[str]] = defaultdict(set)

    for search_root in translation_roots_for_forms(form_paths):
        for language_dir in sorted(search_root.iterdir()):
            if not language_dir.is_dir() or language_dir.suffix != ".lproj":
                continue
            for pattern in ("*.xlf", "*.xliff"):
                for path in sorted(language_dir.rglob(pattern)):
                    _collect_translations_from_file(path, catalog, seen)

    return {key: tuple(values) for key, values in catalog.items()}


def translation_roots_for_forms(form_paths: Iterable[Path]) -> tuple[Path, ...]:
    roots: list[Path] = []
    seen: set[Path] = set()

    for form_path in form_paths:
        resources_root = translation_root_for_form(form_path)
        if resources_root is None or not resources_root.exists():
            continue
        resolved = resources_root.resolve()
        if resolved in seen:
            continue
        roots.append(resolved)
        seen.add(resolved)

    return tuple(roots)


def translation_root_for_form(form_path: Path) -> Path | None:
    resolved = form_path.resolve()
    for candidate in (resolved.parent, *resolved.parent.parents):
        if candidate.name != "Forms":
            continue
        sources_dir = candidate.parent
        project_dir = sources_dir.parent
        if sources_dir.name != "Sources" or project_dir.name != "Project":
            continue
        return project_dir.parent / "Resources"
    return None


def _collect_translations_from_file(
    path: Path,
    catalog: dict[str, list[str]],
    seen: dict[str, set[str]],
) -> None:
    try:
        root = ElementTree.parse(path).getroot()
    except (ElementTree.ParseError, OSError):
        return

    for node in root.iter():
        if _local_name(node.tag) not in {"trans-unit", "unit"}:
            continue
        keys = [value for value in (node.get("id"), node.get("name"), node.get("resname")) if value]
        if not keys:
            continue
        texts = _translation_texts(node)
        if not texts:
            continue
        for key in keys:
            for text in texts:
                if text in seen[key]:
                    continue
                catalog[key].append(text)
                seen[key].add(text)


def _translation_texts(unit: ElementTree.Element) -> list[str]:
    texts: list[str] = []
    seen: set[str] = set()

    for candidate in unit.iter():
        if _local_name(candidate.tag) not in {"source", "target"}:
            continue
        normalized = _normalize_xml_text("".join(candidate.itertext()))
        if not normalized or normalized in seen:
            continue
        texts.append(normalized)
        seen.add(normalized)

    return texts


def _normalize_xml_text(value: str) -> str:
    return " ".join(value.split())


def _local_name(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag
