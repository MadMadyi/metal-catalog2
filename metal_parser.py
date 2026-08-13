"""Basic parser for common Russian metal-product names."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Optional


TYPE_PATTERNS = (
    (r"\bшвеллер\w*\b", "швеллер"),
    (r"\bдвутавр\w*\b|\bбалк\w*\b", "двутавр"),
    (r"\bугол(?:ок|ка|ки|ков)?\b", "уголок"),
    (r"\bтруб\w*\b", "труба"),
    (r"\bлист\w*\b", "лист"),
    (r"\bкруг\w*\b", "круг"),
    (r"\bполос\w*\b", "полоса"),
    (r"\bшестигран\w*\b", "шестигранник"),
    (r"\bарматур\w*\b", "арматура"),
    (r"\bпрофнастил\w*\b|\bпрофлист\w*\b", "профлист"),
    (r"\bсетк\w*\b", "сетка"),
)


@dataclass(frozen=True)
class MetalParseResult:
    original: str
    normalized: str
    metal_type: Optional[str]
    size_text: Optional[str]
    dimensions_mm: tuple[float, ...]
    profile: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


def normalize_text(value: str) -> str:
    text = value.strip().lower().replace("×", "x").replace("х", "x").replace("*", "x")
    text = re.sub(r"\s*x\s*", "x", text)
    text = re.sub(r"\s+", " ", text)
    return text


def detect_type(text: str) -> Optional[str]:
    for pattern, metal_type in TYPE_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            return metal_type
    return None


def _to_number(token: str) -> float:
    return float(token.replace(",", "."))


def _extract_dimension_group(text: str):
    match = re.search(r"(?<!\d)(\d+(?:[.,]\d+)?(?:x\d+(?:[.,]\d+)?){1,3})(?!\d)", text)
    if not match:
        return None, ()
    size_text = match.group(1)
    return size_text, tuple(_to_number(part) for part in size_text.split("x"))


def _extract_single_size(text: str, metal_type: Optional[str]):
    if metal_type not in {"круг", "арматура", "шестигранник"}:
        return None, ()
    match = re.search(r"(?:ø|ф|d\s*)?(\d+(?:[.,]\d+)?)", text)
    if not match:
        return None, ()
    raw = match.group(1)
    return raw, (_to_number(raw),)


def _extract_channel_profile(text: str, metal_type: Optional[str]):
    if metal_type != "швеллер":
        return None, (), None
    match = re.search(r"(?<!\d)(\d+(?:[.,]\d+)?)\s*([пуэс])?\b", text, flags=re.IGNORECASE)
    if not match:
        return None, (), None
    number = match.group(1)
    profile = match.group(2).upper() if match.group(2) else None
    return f"{number}{profile or ''}", (_to_number(number),), profile


def parse_metal_name(value: str) -> MetalParseResult:
    normalized = normalize_text(value)
    metal_type = detect_type(normalized)

    size_text = None
    dimensions = ()
    profile = None

    if metal_type == "швеллер":
        size_text, dimensions, profile = _extract_channel_profile(normalized, metal_type)

    if not dimensions:
        size_text, dimensions = _extract_dimension_group(normalized)

    if not dimensions:
        size_text, dimensions = _extract_single_size(normalized, metal_type)

    return MetalParseResult(
        original=value,
        normalized=normalized,
        metal_type=metal_type,
        size_text=size_text,
        dimensions_mm=dimensions,
        profile=profile,
    )


if __name__ == "__main__":
    examples = (
        "Швеллер 14П",
        "Уголок 50х50х5",
        "Труба 108х4",
        "Лист 10х1500х6000",
        "Круг 20",
    )
    for example in examples:
        print(parse_metal_name(example).to_dict())
