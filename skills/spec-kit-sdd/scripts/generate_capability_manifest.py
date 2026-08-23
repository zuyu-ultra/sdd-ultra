#!/usr/bin/env python3
"""从固定 Spec Kit Typer 应用生成完整 CLI 能力清单。"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

from typer.main import get_command

import specify_cli
from specify_runtime import SKILL_ROOT, lock, risk_for


OUTPUT = SKILL_ROOT / "references" / "capability-map.json"


def parameter_record(parameter: object) -> dict[str, object]:
    record: dict[str, object] = {
        "name": getattr(parameter, "name", None),
        "required": bool(getattr(parameter, "required", False)),
    }
    if hasattr(parameter, "opts"):
        record["kind"] = "option"
        record["opts"] = list(getattr(parameter, "opts", [])) + list(
            getattr(parameter, "secondary_opts", [])
        )
        record["multiple"] = bool(getattr(parameter, "multiple", False))
    else:
        record["kind"] = "argument"
        record["nargs"] = getattr(parameter, "nargs", 1)
    if getattr(parameter, "help", None):
        record["help"] = getattr(parameter, "help")
    return record


def collect() -> list[dict[str, object]]:
    root = get_command(specify_cli.app)
    commands: list[dict[str, object]] = []

    def visit(command: object, parts: list[str]) -> None:
        children = getattr(command, "commands", None)
        if isinstance(children, dict) and children:
            for name in sorted(children):
                visit(children[name], [*parts, name])
            return
        commands.append(
            {
                "path": "specify " + " ".join(parts),
                "help": getattr(command, "help", "") or "",
                "risks": sorted(risk_for(parts)),
                "parameters": [
                    parameter_record(item)
                    for item in getattr(command, "params", [])
                ],
            }
        )

    visit(root, [])
    return commands


def render() -> str:
    commands = collect()
    metadata = lock()
    payload = {
        "schema_version": 1,
        "repository": metadata["repository"],
        "commit": metadata["commit"],
        "version": metadata["version"],
        "leaf_command_count": len(commands),
        "commands": commands,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    content = render()
    if args.check:
        if not args.output.is_file() or args.output.read_text(encoding="utf-8") != content:
            print("capability manifest is stale")
            return 1
        print(f"verified {len(collect())} CLI leaf commands")
        return 0
    atomic_write(args.output, content)
    print(f"wrote {args.output} with {len(collect())} CLI leaf commands")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
