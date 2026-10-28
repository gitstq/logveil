"""LogVeil redaction engine.

The core idea is *consistent pseudonymisation*, not deletion: the same
original value always becomes the same placeholder (``[EMAIL_1]``), so
a stack trace, a user report and a server log stay correlatable after
redaction -- and with the locally-kept mapping file the process is
fully reversible via :func:`restore_text`.
"""
from __future__ import annotations

import json
import os
import re
from typing import Iterable, Optional

from .detectors import CATEGORIES, DETECTORS, PRIVATE_KEY_RE


class Redactor:
    def __init__(
        self,
        categories: Optional[Iterable[str]] = None,
        mapping: Optional[dict[str, str]] = None,
        extra_patterns: Optional[list[tuple[str, str]]] = None,
    ) -> None:
        wanted = set(categories) if categories else set(CATEGORIES)
        unknown = wanted - set(CATEGORIES)
        if unknown and not extra_patterns:
            raise ValueError(f"unknown categories: {sorted(unknown)}")
        self.categories = wanted
        # original -> placeholder, plus reverse index and per-category counters
        self.mapping: dict[str, str] = dict(mapping or {})
        self._counters: dict[str, int] = {}
        for original, placeholder in self.mapping.items():
            m = re.match(r"\[([A-Z_]+)_(\d+)\]$", placeholder)
            if m:
                cat, num = m.group(1), int(m.group(2))
                self._counters[cat] = max(self._counters.get(cat, 0), num)
        self.counts: dict[str, int] = {}
        self._detectors = [d for d in DETECTORS if d.category in wanted]
        self._extra: list[tuple[str, re.Pattern]] = []
        for name, regex in extra_patterns or []:
            cat = name.upper()
            self._extra.append((cat, re.compile(regex)))
            self.categories.add(cat)

    # -- placeholder bookkeeping -------------------------------------------
    def _placeholder(self, category: str, original: str) -> str:
        if original in self.mapping:
            return self.mapping[original]
        self._counters[category] = self._counters.get(category, 0) + 1
        placeholder = f"[{category}_{self._counters[category]}]"
        self.mapping[original] = placeholder
        self.counts[category] = self.counts.get(category, 0) + 1
        return placeholder

    # -- redaction ----------------------------------------------------------
    def redact_text(self, text: str) -> str:
        lines = text.splitlines(keepends=True)
        return "".join(self.redact_line(line) for line in lines)

    def redact_line(self, line: str) -> str:
        if "PRIVATE_KEY" in self.categories and PRIVATE_KEY_RE.search(line):
            key_line = line.strip()
            placeholder = self._placeholder("PRIVATE_KEY", key_line)
            return line.replace(key_line, placeholder)
        out = line
        for det in self._detectors:
            out = self._apply(out, det.category, det.pattern, det.validator, det.group)
        for cat, pattern in self._extra:
            out = self._apply(out, cat, pattern, None, 0)
        return out

    def _apply(self, text, category, pattern, validator, group):
        def repl(match: re.Match) -> str:
            value = match.group(group)
            if validator is not None and not validator(value):
                return match.group(0)
            placeholder = self._placeholder(category, value)
            if group == 0:
                return placeholder
            start, end = match.span(group)
            whole = match.group(0)
            offset = match.start()
            return whole[: start - offset] + placeholder + whole[end - offset :]

        return pattern.sub(repl, text)

    # -- mapping persistence -------------------------------------------------
    def save_mapping(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.mapping, fh, ensure_ascii=False, indent=2)
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass  # best effort on platforms without POSIX modes

    @classmethod
    def load_mapping(cls, path: str, **kwargs) -> "Redactor":
        with open(path, encoding="utf-8") as fh:
            mapping = json.load(fh)
        return cls(mapping=mapping, **kwargs)


def restore_text(text: str, mapping: dict[str, str]) -> str:
    """Replace placeholders back with originals (longest first)."""
    reverse = sorted(mapping.items(), key=lambda kv: len(kv[1]), reverse=True)
    out = text
    for original, placeholder in reverse:
        out = out.replace(placeholder, original)
    return out
