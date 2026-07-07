"""CLI output formatters."""

from __future__ import annotations

from typing import Any


def heading(text: str) -> str:
    return f"\n=== {text} ==="


def kv(key: str, value: Any, indent: int = 0) -> str:
    pad = "  " * indent
    return f"{pad}{key}: {value}"


def table(rows: list[list[str]], header: list[str]) -> str:
    if not rows:
        return ""

    col_widths = [
        max(len(str(row[i])) for row in [header] + rows)
        for i in range(len(header))
    ]

    lines: list[str] = []

    def _fmt(row: list[str]) -> str:
        return "  ".join(
            str(item).ljust(col_widths[i]) for i, item in enumerate(row)
        )

    sep = "  ".join("-" * w for w in col_widths)
    lines.append(_fmt(header))
    lines.append(sep)
    for row in rows:
        lines.append(_fmt(row))
    return "\n".join(lines)


def status_line(text: str) -> str:
    return f"  {text}"
