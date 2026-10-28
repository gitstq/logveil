"""Detection patterns for LogVeil.

Every detector yields candidate matches; validators (Luhn for bank
cards, the MOD 11-2 checksum for Chinese resident IDs) reject the
look-alike numbers that plain regex scanners happily destroy --
timestamps, order numbers and build IDs are not secrets.

Only the Python standard library is used.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass(frozen=True)
class Detector:
    """One category of sensitive text.

    ``pattern`` finds candidates. ``validator`` (optional) receives the
    matched text and returns True only for a genuine hit. ``group``
    selects which regex group is the sensitive value when the match
    carries context that must be preserved (e.g. ``api_key=`` keeps the
    key name, replaces only the value).
    """

    category: str
    pattern: re.Pattern
    validator: Optional[Callable[[str], bool]] = None
    group: int = 0


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------

def _luhn_ok(text: str) -> bool:
    digits = [int(ch) for ch in text if ch.isdigit()]
    if not 13 <= len(digits) <= 19:
        return False
    total = 0
    parity = len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


_ID_WEIGHTS = (7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2)
_ID_CHECK = "10X98765432"


def _cn_id_ok(text: str) -> bool:
    if len(text) != 18 or not text[:17].isdigit():
        return False
    total = sum(int(text[i]) * _ID_WEIGHTS[i] for i in range(17))
    return _ID_CHECK[total % 11] == text[17].upper()


def _ipv4_ok(text: str) -> bool:
    parts = text.split(".")
    return len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts)


# ---------------------------------------------------------------------------
# Detectors, in application order (most specific first)
# ---------------------------------------------------------------------------

def _c(regex: str) -> re.Pattern:
    return re.compile(regex)


DETECTORS: list[Detector] = [
    # PEM private-key blocks are handled line-wise in redactor.py.
    Detector("TOKEN", _c(r"\bghp_[A-Za-z0-9]{30,}\b")),
    Detector("TOKEN", _c(r"\bgithub_pat_[A-Za-z0-9_]{30,}\b")),
    Detector("TOKEN", _c(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b")),
    Detector("TOKEN", _c(r"\bAKIA[0-9A-Z]{16}\b")),
    Detector("TOKEN", _c(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    Detector("TOKEN", _c(r"\bAIza[0-9A-Za-z_-]{30,}\b")),
    Detector("TOKEN", _c(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b")),  # JWT
    Detector(
        "TOKEN",
        _c(r"(?i)\b(authorization\s*:\s*bearer\s+)([A-Za-z0-9._~+/=-]{8,})"),
        group=2,
    ),
    Detector(
        "SECRET",
        _c(r"(?i)\b(api[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret|password|passwd|pwd|secret)\b(\s*[:=]\s*)([\"']?)([^\s\"',;]{4,})"),
        group=4,
    ),
    Detector("EMAIL", _c(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    Detector(
        "URL_SECRET",
        _c(r"(?i)\b([a-z][a-z0-9+.-]*://[^\s:/@]+:)([^\s/@]+)(@)"),
        group=2,
    ),
    Detector("ID_CARD", _c(r"\b\d{17}[\dXx]\b"), validator=_cn_id_ok),
    Detector("BANK_CARD", _c(r"\b(?:\d[ -]?){12,18}\d\b"), validator=_luhn_ok),
    Detector("PHONE", _c(r"(?<!\d)(?:\+?86[ -]?)?1[3-9]\d{9}(?!\d)")),
    Detector("PHONE", _c(r"\+\d{1,3}[ -]\d{3,4}[ -]\d{4,8}\b")),
    # MAC before IPv6: both use colons, but a MAC is exactly six pairs.
    Detector("MAC", _c(r"\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b")),
    Detector("IP", _c(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), validator=_ipv4_ok),
    # IPv6: at least 3 colons (full/compressed forms) so HH:MM:SS times survive.
    Detector("IP", _c(r"\b(?:[0-9A-Fa-f]{1,4}:){3,7}[0-9A-Fa-f]{1,4}\b|\b[0-9A-Fa-f]{1,4}(?::[0-9A-Fa-f]{0,4})*::(?:[0-9A-Fa-f]{1,4}:)*[0-9A-Fa-f]{1,4}\b")),
    Detector(
        "USER_PATH",
        _c(r"(?i)(/(?:users|home)/)([^/\s]+)(/)"),
        group=2,
    ),
    Detector(
        "USER_PATH",
        _c(r"(?i)([A-Za-z]:\\users\\)([^\\\s]+)(\\)"),
        group=2,
    ),
    Detector(
        "GPS",
        _c(r"(?i)\blat(?:itude)?\s*[:=]\s*-?\d{1,2}\.\d{4,}\s*[, ]\s*(?:lon|lng|longitude)\s*[:=]\s*-?\d{1,3}\.\d{4,}"),
    ),
]

CATEGORIES = sorted({d.category for d in DETECTORS} | {"PRIVATE_KEY"})

PRIVATE_KEY_RE = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")
