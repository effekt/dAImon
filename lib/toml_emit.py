"""Minimal TOML emitter for dAImon's daemon.toml shapes (scalars, inline tables,
arrays, plus [section] headers). Shared by config.py and the sync compiler."""
from __future__ import annotations


def emit_value(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, str):
        return f'"{v}"'
    if isinstance(v, dict):
        return "{ " + ", ".join(f"{k} = {emit_value(val)}" for k, val in v.items()) + " }"
    if isinstance(v, list):
        return "[" + ", ".join(emit_value(x) for x in v) + "]"
    raise TypeError(f"cannot emit {v!r}")


def _section_lines(name: str, table: dict) -> list[str]:
    return [f"[{name}]"] + [f"{k} = {emit_value(v)}" for k, v in table.items()]


def dump_sections(sections: dict[str, dict]) -> str:
    blocks = [_section_lines(name, table) for name, table in sections.items() if table]
    return "\n\n".join("\n".join(b) for b in blocks) + "\n"
