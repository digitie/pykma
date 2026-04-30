"""KMA category and code mappings."""

from __future__ import annotations

import re
from typing import Optional

SKY_LABELS = {
    "1": "맑음",
    "3": "구름많음",
    "4": "흐림",
}

PTY_NCST_LABELS = {
    "0": "없음",
    "1": "비",
    "2": "비/눈",
    "3": "눈",
    "5": "빗방울",
    "6": "빗방울눈날림",
    "7": "눈날림",
}

PTY_FCST_LABELS = {
    "0": "없음",
    "1": "비",
    "2": "비/눈",
    "3": "눈",
    "4": "소나기",
}

CATEGORY_UNITS = {
    "T1H": "C",
    "TMP": "C",
    "TMN": "C",
    "TMX": "C",
    "RN1": "mm",
    "PCP": "mm",
    "SNO": "cm",
    "REH": "%",
    "UUU": "m/s",
    "VVV": "m/s",
    "VEC": "deg",
    "WSD": "m/s",
    "POP": "%",
    "WAV": "m",
}

_NUMERIC_CATEGORIES = {
    "T1H",
    "TMP",
    "TMN",
    "TMX",
    "RN1",
    "REH",
    "UUU",
    "VVV",
    "VEC",
    "WSD",
    "POP",
    "WAV",
}


def label_for(category: str, value: object, *, endpoint: str = "") -> Optional[str]:
    code = str(value)
    if category == "SKY":
        return SKY_LABELS.get(code)
    if category == "PTY":
        if endpoint == "getUltraSrtNcst":
            return PTY_NCST_LABELS.get(code)
        return PTY_FCST_LABELS.get(code)
    return None


def normalize_value(category: str, value: object) -> str | float:
    raw = "" if value is None else str(value).strip()
    if category in {"PCP", "SNO"}:
        return raw
    if category in _NUMERIC_CATEGORIES:
        try:
            number = float(raw)
        except ValueError:
            return raw
        return number
    return raw


def parse_amount(value: object) -> Optional[float]:
    """Parse KMA precipitation or snowfall amount labels into a representative float.

    Range labels are represented by their midpoint. Open-ended labels use the boundary.
    Unrecognized non-empty values return None instead of raising.
    """

    if value is None:
        return None
    text = str(value).strip()
    if not text or text in {"강수없음", "적설없음", "없음", "0", "0.0"}:
        return 0.0

    number_pattern = r"[-+]?\d+(?:\.\d+)?"
    numbers = [float(match) for match in re.findall(number_pattern, text)]
    if not numbers:
        return None
    if "미만" in text or "<" in text:
        return numbers[0] / 2.0
    if "~" in text and len(numbers) >= 2:
        return (numbers[0] + numbers[1]) / 2.0
    return numbers[0]

