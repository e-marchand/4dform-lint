from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree


def load_translation_catalog(search_root: Path) -> dict[str, tuple[str, ...]]:
    catalog: dict[str, list[str]] = defaultdict(list)
    seen: dict[str, set[str]] = defaultdict(set)

    if not search_root.exists():
        return {}

    for pattern in ("*.xlf", "*.xliff"):
        for path in sorted(search_root.rglob(pattern)):
            _collect_translations_from_file(path, catalog, seen)

    return {key: tuple(values) for key, values in catalog.items()}


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
