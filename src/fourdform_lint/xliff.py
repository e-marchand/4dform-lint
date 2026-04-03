from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree

from .models import TranslationText


def load_translation_catalog(form_paths: Iterable[Path]) -> dict[str, tuple[TranslationText, ...]]:
    catalog: dict[str, list[TranslationText]] = defaultdict(list)
    seen: dict[str, set[tuple[str, str, bool]]] = defaultdict(set)

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
    catalog: dict[str, list[TranslationText]],
    seen: dict[str, set[tuple[str, str, bool]]],
) -> None:
    try:
        root = ElementTree.parse(path).getroot()
    except (ElementTree.ParseError, OSError):
        return

    for node, source_language, target_language in _iter_translation_units(root):
        keys = [value for value in (node.get("id"), node.get("name"), node.get("resname")) if value]
        if not keys:
            continue
        texts = _translation_texts(
            node,
            source_language=source_language,
            target_language=target_language,
        )
        if not texts:
            continue
        for key in keys:
            for text in texts:
                signature = (text.language, text.text, text.is_source)
                if signature in seen[key]:
                    continue
                catalog[key].append(text)
                seen[key].add(signature)


def _iter_translation_units(
    root: ElementTree.Element,
) -> Iterable[tuple[ElementTree.Element, str | None, str | None]]:
    root_source_language = _language_attribute(root, "srcLang", "source-language")
    root_target_language = _language_attribute(root, "trgLang", "target-language")
    file_nodes = [node for node in root.iter() if _local_name(node.tag) == "file"]
    if file_nodes:
        for file_node in file_nodes:
            file_source_language = (
                _language_attribute(file_node, "srcLang", "source-language")
                or root_source_language
            )
            file_target_language = (
                _language_attribute(file_node, "trgLang", "target-language")
                or root_target_language
            )
            for node in file_node.iter():
                if _local_name(node.tag) in {"trans-unit", "unit"}:
                    yield node, file_source_language, file_target_language
        return

    for node in root.iter():
        if _local_name(node.tag) in {"trans-unit", "unit"}:
            yield node, root_source_language, root_target_language


def _translation_texts(
    unit: ElementTree.Element,
    *,
    source_language: str | None,
    target_language: str | None,
) -> list[TranslationText]:
    texts: list[TranslationText] = []
    seen: set[tuple[str, str, bool]] = set()

    for candidate in unit.iter():
        local_name = _local_name(candidate.tag)
        if local_name not in {"source", "target"}:
            continue
        normalized = _normalize_xml_text("".join(candidate.itertext()))
        if not normalized:
            continue
        if local_name == "source":
            entry = TranslationText(
                language=source_language or "source",
                text=normalized,
                is_source=True,
            )
        else:
            entry = TranslationText(
                language=target_language or "target",
                text=normalized,
                is_source=False,
            )
        signature = (entry.language, entry.text, entry.is_source)
        if signature in seen:
            continue
        texts.append(entry)
        seen.add(signature)

    return texts


def _language_attribute(node: ElementTree.Element, *names: str) -> str | None:
    for name in names:
        value = node.get(name)
        if isinstance(value, str):
            stripped = value.strip()
            if stripped:
                return stripped
    return None


def _normalize_xml_text(value: str) -> str:
    return " ".join(value.split())


def _local_name(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag
