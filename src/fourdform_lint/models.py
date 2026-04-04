from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Frame:
    top: int
    left: int
    width: int
    height: int

    @property
    def right(self) -> int:
        return self.left + self.width

    @property
    def bottom(self) -> int:
        return self.top + self.height


@dataclass
class ElementContext:
    element_id: str
    element_type: str
    frame: Frame
    native_object: dict[str, object] = field(default_factory=dict)
    ignores: set[str] = field(default_factory=set)
    placement: str | None = None


@dataclass
class PageContext:
    index: int
    elements: list[ElementContext]


@dataclass(frozen=True)
class TranslationText:
    language: str
    text: str
    is_source: bool = False


@dataclass
class FormContext:
    source_path: Path
    display_path: str
    width: int | None
    height: int | None
    pages: list[PageContext]
    form_events: set[str] = field(default_factory=set)
    translations: dict[str, tuple[TranslationText, ...]] = field(default_factory=dict)


@dataclass(frozen=True)
class Finding:
    file_path: str
    rule_id: str
    severity: str
    message: str
    page_index: int | None = None
    element_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "path": self.file_path,
            "rule_id": self.rule_id,
            "severity": self.severity,
            "message": self.message,
        }
        if self.page_index is not None:
            payload["page_index"] = self.page_index
        if self.element_ids:
            payload["element_ids"] = list(self.element_ids)
        return payload
