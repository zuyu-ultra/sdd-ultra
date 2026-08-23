#!/usr/bin/env python3
"""生成或验证固定上游快照的 SHA-256 文件清单。"""

from __future__ import annotations

import argparse
import hashlib
import os
import tempfile
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
VENDOR_ROOT = SKILL_ROOT / "vendor" / "spec-kit"
MANIFEST = SKILL_ROOT / "vendor" / "MANIFEST.sha256"
WHEELHOUSE_ROOT = SKILL_ROOT / "vendor" / "wheelhouse"
WHEELHOUSE_MANIFEST = SKILL_ROOT / "vendor" / "WHEELHOUSE.sha256"
IGNORED_NAMES = {".DS_Store", "MANIFEST.sha256"}
IGNORED_PARTS = {"__pycache__", ".pytest_cache"}


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def entries(root: Path) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"vendored snapshot contains symlink: {path}")
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if path.name in IGNORED_NAMES or any(
            part in IGNORED_PARTS for part in relative.parts
        ):
            continue
        result.append((digest(path), relative.as_posix()))
    return result


def render(root: Path) -> str:
    return "".join(f"{sha}  {name}\n" for sha, name in entries(root))


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
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
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    source_expected = render(VENDOR_ROOT)
    wheel_expected = render(WHEELHOUSE_ROOT) if WHEELHOUSE_ROOT.is_dir() else ""
    if args.write:
        atomic_write(MANIFEST, source_expected)
        if WHEELHOUSE_ROOT.is_dir():
            atomic_write(WHEELHOUSE_MANIFEST, wheel_expected)
        print(
            f"wrote {MANIFEST} with {len(entries(VENDOR_ROOT))} files; "
            f"wheelhouse files={len(entries(WHEELHOUSE_ROOT)) if WHEELHOUSE_ROOT.is_dir() else 0}"
        )
        return 0
    if not MANIFEST.is_file():
        print(f"missing manifest: {MANIFEST}")
        return 1
    if MANIFEST.read_text(encoding="utf-8") != source_expected:
        print("vendored snapshot does not match MANIFEST.sha256")
        return 1
    if WHEELHOUSE_ROOT.is_dir():
        if not WHEELHOUSE_MANIFEST.is_file():
            print(f"missing manifest: {WHEELHOUSE_MANIFEST}")
            return 1
        if WHEELHOUSE_MANIFEST.read_text(encoding="utf-8") != wheel_expected:
            print("wheelhouse does not match WHEELHOUSE.sha256")
            return 1
    print(
        f"verified {len(entries(VENDOR_ROOT))} vendored files and "
        f"{len(entries(WHEELHOUSE_ROOT)) if WHEELHOUSE_ROOT.is_dir() else 0} wheels"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
