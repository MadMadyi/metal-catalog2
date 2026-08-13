"""Unified metal catalogue analyzer.

Pipeline:
1. Parse a raw metal-product description.
2. Detect product type and dimensions.
3. Select the most appropriate ГОСТ.
4. Return one structured result.

Place this file next to:
- metal_parser.py
- gost_finder.py
inside the src/ directory.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import Iterable, Optional

from metal_parser import parse_metal_name
from gost_finder import find_gost


@dataclass(frozen=True)
class MetalCatalogResult:
    original: str
    normalized: str
    metal_type: Optional[str]
    size_text: Optional[str]
    dimensions_mm: tuple[float, ...]
    profile: Optional[str]

    gost: Optional[str]
    gost_title: Optional[str]
    confidence: str
    reason: str
    gost_candidates: tuple[str, ...]

    future_replacement: Optional[str] = None
    future_effective_from: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


def analyze_metal(
    value: str,
    *,
    as_of: Optional[date] = None,
    allow_early_future: bool = False,
) -> MetalCatalogResult:
    """Analyze one metal-product description."""
    parsed = parse_metal_name(value)

    gost = find_gost(
        parsed.metal_type,
        normalized_text=parsed.normalized,
        dimensions_mm=parsed.dimensions_mm,
        as_of=as_of,
        allow_early_future=allow_early_future,
    )

    return MetalCatalogResult(
        original=parsed.original,
        normalized=parsed.normalized,
        metal_type=parsed.metal_type,
        size_text=parsed.size_text,
        dimensions_mm=parsed.dimensions_mm,
        profile=parsed.profile,
        gost=gost.standard,
        gost_title=gost.title,
        confidence=gost.confidence,
        reason=gost.reason,
        gost_candidates=gost.candidates,
        future_replacement=gost.future_replacement,
        future_effective_from=gost.future_effective_from,
    )


def analyze_many(
    values: Iterable[str],
    *,
    as_of: Optional[date] = None,
    allow_early_future: bool = False,
) -> list[MetalCatalogResult]:
    """Analyze several metal-product descriptions."""
    return [
        analyze_metal(
            value,
            as_of=as_of,
            allow_early_future=allow_early_future,
        )
        for value in values
    ]


def format_result(result: MetalCatalogResult) -> str:
    """Human-readable summary for quick manual checking."""
    size = result.size_text or "не определён"
    gost = result.gost or "требует проверки"

    lines = [
        f"Исходное наименование: {result.original}",
        f"Тип: {result.metal_type or 'не определён'}",
        f"Размер: {size}",
        f"ГОСТ: {gost}",
        f"Уверенность: {result.confidence}",
    ]

    if result.gost_candidates:
        lines.append(
            "Возможные ГОСТ: " + ", ".join(result.gost_candidates)
        )

    if result.future_replacement:
        lines.append(
            f"Будущая замена: {result.future_replacement}"
            + (
                f" с {result.future_effective_from}"
                if result.future_effective_from
                else ""
            )
        )

    lines.append(f"Комментарий: {result.reason}")
    return "\n".join(lines)


if __name__ == "__main__":
    examples = [
        "Швеллер 14П",
        "Уголок 50х50х5",
        "Уголок 75х50х6",
        "Труба 108х4",
        "Лист г/к 10х1500х6000",
        "Лист 10х1500х6000",
        "Круг 20",
    ]

    for item in examples:
        result = analyze_metal(
            item,
            as_of=date(2026, 8, 14),
        )
        print("=" * 60)
        print(format_result(result))
