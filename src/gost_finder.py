"""ГОСТ finder for common metal products.

Initial reference date: 2026-08-14.
"""

from dataclasses import asdict, dataclass
from datetime import date
from typing import Optional, Sequence


@dataclass(frozen=True)
class GostResult:
    standard: Optional[str]
    title: Optional[str]
    confidence: str
    reason: str
    candidates: tuple[str, ...] = ()
    future_replacement: Optional[str] = None
    future_effective_from: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


CATALOG = {
    "швеллер": {
        "standard": "ГОСТ 8240-97",
        "title": "Швеллеры стальные горячекатаные. Сортамент",
        "future_replacement": "ГОСТ 8240-2026",
        "future_effective_from": date(2027, 4, 1),
    },
    "двутавр": {
        "standard": "ГОСТ 35087-2024",
        "title": "Двутавры стальные горячекатаные. Технические условия",
    },
    "арматура": {
        "standard": "ГОСТ 34028-2016",
        "title": "Прокат арматурный для железобетонных конструкций. Технические условия",
    },
    "круг": {
        "standard": "ГОСТ 2590-2006",
        "title": "Прокат сортовой стальной горячекатаный круглый. Сортамент",
    },
    "полоса": {
        "standard": "ГОСТ 103-2006",
        "title": "Прокат сортовой стальной горячекатаный полосовой. Сортамент",
    },
    "шестигранник": {
        "standard": "ГОСТ 2879-2006",
        "title": "Прокат сортовой стальной горячекатаный шестигранный. Сортамент",
    },
    "профлист": {
        "standard": "ГОСТ 24045-2016",
        "title": "Профили стальные листовые гнутые с трапециевидными гофрами для строительства. Технические условия",
    },
    "сетка": {
        "standard": "ГОСТ 23279-2012",
        "title": "Сетки арматурные сварные для железобетонных конструкций и изделий. Общие технические условия",
    },
    "труба": {
        "standard": "ГОСТ 10704-91",
        "title": "Трубы стальные электросварные прямошовные. Сортамент",
    },
}

SHEET_HOT = (
    "ГОСТ 19903-2015",
    "Прокат листовой горячекатаный. Сортамент",
)

SHEET_COLD = (
    "ГОСТ 19904-90",
    "Прокат листовой холоднокатаный. Сортамент",
)

ANGLE_EQUAL = {
    "standard": "ГОСТ 8509-93",
    "title": "Уголки стальные горячекатаные равнополочные. Сортамент",
    "future_replacement": "ГОСТ 8509-2026",
    "future_effective_from": date(2027, 4, 1),
}

ANGLE_UNEQUAL = {
    "standard": "ГОСТ 8510-86",
    "title": "Уголки стальные горячекатаные неравнополочные. Сортамент",
}


def _norm(value: str) -> str:
    return (
        value.lower()
        .replace("ё", "е")
        .replace("×", "x")
        .replace("х", "x")
        .strip()
    )


def _dated_standard(item: dict, *, as_of: date, allow_early_future: bool = False):
    future = item.get("future_replacement")
    future_from = item.get("future_effective_from")

    if future and future_from and (as_of >= future_from or allow_early_future):
        return future, item["title"], None, None

    return (
        item["standard"],
        item["title"],
        future,
        future_from.isoformat() if future_from else None,
    )


def _angle_is_equal(dimensions_mm: Sequence[float]) -> Optional[bool]:
    if len(dimensions_mm) < 2:
        return None
    return abs(float(dimensions_mm[0]) - float(dimensions_mm[1])) < 1e-9


def find_gost(
    metal_type: Optional[str],
    *,
    normalized_text: str = "",
    dimensions_mm: Sequence[float] = (),
    as_of: Optional[date] = None,
    allow_early_future: bool = False,
) -> GostResult:
    as_of = as_of or date.today()
    text = _norm(normalized_text or "")
    metal_type = _norm(metal_type or "") or None

    if metal_type == "лист":
        if "холоднокатан" in text or "х/к" in text or "хк" in text:
            return GostResult(
                standard=SHEET_COLD[0],
                title=SHEET_COLD[1],
                confidence="high",
                reason="В описании указан холоднокатаный лист.",
            )

        if "горячекатан" in text or "г/к" in text or "гк" in text:
            return GostResult(
                standard=SHEET_HOT[0],
                title=SHEET_HOT[1],
                confidence="high",
                reason="В описании указан горячекатаный лист.",
            )

        return GostResult(
            standard=None,
            title=None,
            confidence="needs_review",
            reason="Для листа не указан способ прокатки.",
            candidates=(SHEET_HOT[0], SHEET_COLD[0]),
        )

    if metal_type == "уголок":
        equal = _angle_is_equal(dimensions_mm)

        if equal is True:
            standard, title, future, future_from = _dated_standard(
                ANGLE_EQUAL,
                as_of=as_of,
                allow_early_future=allow_early_future,
            )
            return GostResult(
                standard=standard,
                title=title,
                confidence="high",
                reason="Полки уголка равны.",
                future_replacement=future,
                future_effective_from=future_from,
            )

        if equal is False:
            return GostResult(
                standard=ANGLE_UNEQUAL["standard"],
                title=ANGLE_UNEQUAL["title"],
                confidence="high",
                reason="Полки уголка различаются.",
            )

        return GostResult(
            standard=None,
            title=None,
            confidence="needs_review",
            reason="Недостаточно размеров для определения типа уголка.",
            candidates=(ANGLE_EQUAL["standard"], ANGLE_UNEQUAL["standard"]),
            future_replacement=ANGLE_EQUAL["future_replacement"],
            future_effective_from=ANGLE_EQUAL["future_effective_from"].isoformat(),
        )

    if metal_type in CATALOG:
        item = CATALOG[metal_type]
        standard, title, future, future_from = _dated_standard(
            item,
            as_of=as_of,
            allow_early_future=allow_early_future,
        )

        confidence = "medium" if metal_type == "труба" else "high"
        reason = (
            "Использован базовый ГОСТ для электросварной прямошовной трубы; "
            "для бесшовной, водогазопроводной или профильной трубы нужно отдельное правило."
            if metal_type == "труба"
            else "Тип металлопроката сопоставлен со справочником."
        )

        return GostResult(
            standard=standard,
            title=title,
            confidence=confidence,
            reason=reason,
            future_replacement=future,
            future_effective_from=future_from,
        )

    return GostResult(
        standard=None,
        title=None,
        confidence="needs_review",
        reason="Для этого типа правило ГОСТ пока не задано.",
    )


def find_gost_for_parsed(parsed) -> GostResult:
    return find_gost(
        parsed.metal_type,
        normalized_text=parsed.normalized,
        dimensions_mm=parsed.dimensions_mm,
    )


if __name__ == "__main__":
    examples = [
        ("швеллер", "швеллер 14п", (14.0,)),
        ("уголок", "уголок 50x50x5", (50.0, 50.0, 5.0)),
        ("уголок", "уголок 75x50x6", (75.0, 50.0, 6.0)),
        ("труба", "труба 108x4", (108.0, 4.0)),
        ("лист", "лист г/к 10x1500x6000", (10.0, 1500.0, 6000.0)),
        ("лист", "лист 10x1500x6000", (10.0, 1500.0, 6000.0)),
        ("круг", "круг 20", (20.0,)),
    ]

    for metal_type, text, dims in examples:
        result = find_gost(
            metal_type,
            normalized_text=text,
            dimensions_mm=dims,
            as_of=date(2026, 8, 14),
        )
        print(text, "->", result.to_dict())
