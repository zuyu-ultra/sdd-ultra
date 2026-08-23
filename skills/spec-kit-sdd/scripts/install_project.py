#!/usr/bin/env python3
"""安全安装或检查 Spec Kit 中文项目叠加层。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import sys
import tempfile
from pathlib import Path, PurePosixPath


SKILL_ROOT = Path(__file__).resolve().parent.parent
SOURCE_ROOT = SKILL_ROOT / "assets" / "project"
VENDORED_UPSTREAM_ROOT = SKILL_ROOT / "vendor" / "spec-kit"
UPSTREAM_VERSION = "0.16.4.dev0"
UPSTREAM_COMMIT = "83883a2ebad7e7de667fd00381b100d597faf846"
BUNDLE_REVISION = 4
MANAGED_PREDECESSORS_PATH = SKILL_ROOT / "manifests" / "managed-predecessors.json"
LOCALE_METADATA_PATH = Path(".specify/spec-kit-sdd-locale.json")
PROTECTED_PATHS = {Path(".specify/memory/constitution.md")}
OFFICIAL_MANIFESTS = (
    Path(".specify/integrations/speckit.manifest.json"),
    Path(".specify/integrations/codex.manifest.json"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="把中文版 Spec Kit 资产安全叠加到代码仓库。"
    )
    parser.add_argument(
        "--target",
        type=Path,
        default=Path.cwd(),
        help="需要初始化或本地化的仓库根目录（默认：当前目录）。",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="刷新冲突的托管文件；不会覆盖项目自定义 constitution。",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="只检查目标目录，不做修改。",
    )
    return parser.parse_args()


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def source_assets() -> list[Path]:
    assets = sorted(path for path in SOURCE_ROOT.rglob("*") if path.is_file())
    for source in assets:
        if source.is_symlink():
            raise ValueError(f"refusing symlink source asset: {source}")
    return assets


def _json_object_without_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate key in managed predecessor manifest: {key}")
        result[key] = value
    return result


def _validate_predecessor_hashes(
    value: object,
    *,
    label: str,
    expected_paths: set[str],
) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ValueError(f"managed predecessor {label} must be an object")

    validated: dict[str, str] = {}
    for raw_path, raw_hash in value.items():
        if not isinstance(raw_path, str):
            raise ValueError(f"managed predecessor {label} contains a non-string path")
        relative = PurePosixPath(raw_path)
        if (
            not raw_path
            or relative.is_absolute()
            or raw_path != relative.as_posix()
            or any(part in {"", ".", ".."} for part in relative.parts)
            or raw_path not in expected_paths
        ):
            raise ValueError(
                f"managed predecessor {label} contains an unsafe or unknown path: {raw_path}"
            )
        if not isinstance(raw_hash, str) or re.fullmatch(r"[0-9a-f]{64}", raw_hash) is None:
            raise ValueError(
                f"managed predecessor {label} contains an invalid SHA-256 for {raw_path}"
            )
        validated[raw_path] = raw_hash

    if set(validated) != expected_paths:
        missing = sorted(expected_paths - set(validated))
        extra = sorted(set(validated) - expected_paths)
        raise ValueError(
            f"managed predecessor {label} is incomplete: missing={missing}, extra={extra}"
        )
    return validated


def load_managed_predecessors(
    path: Path = MANAGED_PREDECESSORS_PATH,
) -> dict[str, object]:
    """Load the Skill-owned predecessor allowlist and fail closed on drift.

    Project-local integration manifests are intentionally excluded: they are
    writable project state and may only be refreshed after a trusted update.
    """
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"managed predecessor manifest is missing or unsafe: {path}")
    try:
        payload = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_json_object_without_duplicates,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid managed predecessor manifest {path}: {exc}") from exc

    if not isinstance(payload, dict):
        raise ValueError("managed predecessor manifest root must be an object")
    required_keys = {
        "schema_version",
        "repository",
        "upstream_version",
        "upstream_commit",
        "official_init",
        "bundle_revisions",
    }
    if set(payload) != required_keys:
        raise ValueError(
            "managed predecessor manifest keys do not match the supported schema"
        )
    if payload.get("schema_version") != 1:
        raise ValueError("unsupported managed predecessor manifest schema_version")
    if payload.get("repository") != "https://github.com/github/spec-kit":
        raise ValueError("managed predecessor manifest repository mismatch")
    if payload.get("upstream_version") != UPSTREAM_VERSION:
        raise ValueError("managed predecessor manifest upstream version mismatch")
    if payload.get("upstream_commit") != UPSTREAM_COMMIT:
        raise ValueError("managed predecessor manifest upstream commit mismatch")

    expected_paths = {
        source.relative_to(SOURCE_ROOT).as_posix()
        for source in source_assets()
        if source.relative_to(SOURCE_ROOT) not in PROTECTED_PATHS
    }
    official_init = _validate_predecessor_hashes(
        payload.get("official_init"),
        label="official_init",
        expected_paths=expected_paths,
    )

    raw_revisions = payload.get("bundle_revisions")
    if not isinstance(raw_revisions, dict):
        raise ValueError("managed predecessor bundle_revisions must be an object")
    revisions: dict[int, dict[str, str]] = {}
    for raw_revision, raw_hashes in raw_revisions.items():
        if (
            not isinstance(raw_revision, str)
            or not raw_revision.isdigit()
            or str(int(raw_revision)) != raw_revision
        ):
            raise ValueError(
                f"invalid managed predecessor bundle revision: {raw_revision!r}"
            )
        revision = int(raw_revision)
        if revision >= BUNDLE_REVISION:
            raise ValueError(
                f"managed predecessor revision must be older than {BUNDLE_REVISION}: {revision}"
            )
        revisions[revision] = _validate_predecessor_hashes(
            raw_hashes,
            label=f"bundle revision {revision}",
            expected_paths=expected_paths,
        )

    return {
        "official_init": official_init,
        "bundle_revisions": revisions,
    }


def expected_metadata(bundle_revision: int = BUNDLE_REVISION) -> dict[Path, str]:
    locale = {
        "language": "zh-CN",
        "bundle": "spec-kit-sdd",
        "bundle_revision": bundle_revision,
        "upstream_version": UPSTREAM_VERSION,
        "upstream_commit": UPSTREAM_COMMIT,
    }
    upstream = {
        "repository": "https://github.com/github/spec-kit",
        "version": UPSTREAM_VERSION,
        "commit": UPSTREAM_COMMIT,
        "localization": "zh-CN",
    }
    return {
        Path(".specify/spec-kit-sdd-locale.json"): json.dumps(
            locale, ensure_ascii=False, indent=2, sort_keys=True
        )
        + "\n",
        Path(".specify/spec-kit-sdd-upstream.json"): json.dumps(
            upstream, ensure_ascii=False, indent=2, sort_keys=True
        )
        + "\n",
    }


def known_previous_metadata(
    relative: Path,
    actual: str,
    predecessor_revisions: set[int],
) -> bool:
    """Allow exact managed metadata from a known predecessor to migrate safely."""
    return any(
        expected_metadata(revision).get(relative) == actual
        for revision in predecessor_revisions
    )


def validate_target(target: Path) -> Path:
    expanded = target.expanduser()
    if expanded.is_symlink():
        raise ValueError(f"refusing symlink target: {expanded}")
    resolved = expanded.resolve()
    if resolved == Path(resolved.anchor) or resolved == Path.home().resolve():
        raise ValueError(f"refusing broad target: {resolved}")
    if resolved.exists() and not resolved.is_dir():
        raise ValueError(f"target is not a directory: {resolved}")
    return resolved


def validate_codex_overlay_target(target: Path) -> None:
    """Reject applying Codex-specific skill files to a different integration."""
    state_path = target / ".specify/integration.json"
    if not state_path.exists():
        return
    if state_path.is_symlink():
        raise ValueError(f"refusing symlink integration state: {state_path}")
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid integration state: {state_path}: {exc}") from exc
    default = state.get("default_integration") or state.get("integration")
    if default != "codex":
        raise ValueError(
            "the Chinese project overlay targets the Codex skills layout; "
            f"project default integration is {default!r}"
        )
    settings = state.get("integration_settings", {}).get("codex", {})
    parsed = settings.get("parsed_options", {})
    if isinstance(parsed, dict) and parsed.get("skills") is False:
        raise ValueError("Codex integration is not using the required skills layout")


def lexists(path: Path) -> bool:
    return os.path.lexists(path)


def unsafe_component(target: Path, relative: Path) -> Path | None:
    """Return the first unsafe child path without following target symlinks."""
    current = target
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            return current
        if lexists(current) and not current.exists():
            return current
    return None


def ensure_safe_parent(target: Path, destination: Path) -> None:
    relative = destination.relative_to(target)
    current = target
    if target.exists() and not target.is_dir():
        raise ValueError(f"unsafe target directory: {target}")
    target.mkdir(parents=True, exist_ok=True)
    for part in relative.parent.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"refusing symlink path component: {current}")
        if lexists(current):
            if not current.is_dir():
                raise ValueError(f"expected directory but found file: {current}")
        else:
            current.mkdir()
    if destination.is_symlink():
        raise ValueError(f"refusing symlink destination: {destination}")
    if lexists(destination) and destination.is_dir():
        raise ValueError(f"expected file but found directory: {destination}")


def atomic_copy(source: Path, destination: Path, target: Path) -> None:
    ensure_safe_parent(target, destination)
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as output, source.open("rb") as input_file:
            shutil.copyfileobj(input_file, output)
            output.flush()
            os.fsync(output.fileno())
        os.chmod(temporary, stat.S_IMODE(source.stat().st_mode))
        if destination.is_symlink():
            raise ValueError(f"refusing symlink destination: {destination}")
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            temporary.unlink()


def atomic_write(content: str, destination: Path, target: Path) -> None:
    ensure_safe_parent(target, destination)
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as output:
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
        if destination.is_symlink():
            raise ValueError(f"refusing symlink destination: {destination}")
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            temporary.unlink()


def known_placeholder_constitution(path: Path) -> bool:
    if not path.is_file() or path.is_symlink():
        return False
    candidates = [
        SOURCE_ROOT / ".specify/memory/constitution.md",
        VENDORED_UPSTREAM_ROOT / "templates/constitution-template.md",
    ]
    current_digest = digest(path)
    return any(
        candidate.is_file() and digest(candidate) == current_digest
        for candidate in candidates
    )


def load_official_manifests(target: Path) -> list[tuple[Path, dict[str, object]]]:
    manifests: list[tuple[Path, dict[str, object]]] = []
    for relative in OFFICIAL_MANIFESTS:
        path = target / relative
        if not path.exists():
            continue
        if unsafe_component(target, relative) is not None:
            raise ValueError(f"refusing unsafe official manifest: {relative}")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        files = data.get("files")
        if data.get("version") != UPSTREAM_VERSION or not isinstance(files, dict):
            continue
        manifests.append((relative, data))
    return manifests


def upstream_source_for(relative: Path) -> Path | None:
    parts = relative.parts
    if parts[:2] == (".specify", "templates") and len(parts) == 3:
        return VENDORED_UPSTREAM_ROOT / "templates" / relative.name
    if parts[:3] == (".specify", "scripts", "python") and len(parts) == 4:
        return VENDORED_UPSTREAM_ROOT / "scripts/python" / relative.name
    if relative == Path(".specify/workflows/speckit/workflow.yml"):
        return VENDORED_UPSTREAM_ROOT / "workflows/speckit/workflow.yml"
    return None


def known_current_upstream_unchanged(destination: Path, relative: Path) -> bool:
    if not destination.is_file() or destination.is_symlink():
        return False
    upstream = upstream_source_for(relative)
    return bool(
        upstream is not None
        and upstream.is_file()
        and not upstream.is_symlink()
        and digest(upstream) == digest(destination)
    )


def known_project_bundle_revision(
    target: Path,
    predecessors: dict[str, object],
) -> int | None:
    """Return a predecessor revision only for byte-exact Skill metadata."""
    locale_path = target / LOCALE_METADATA_PATH
    if locale_path.is_symlink() or not locale_path.is_file():
        return None
    try:
        actual = locale_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    revisions = predecessors.get("bundle_revisions", {})
    if not isinstance(revisions, dict):
        return None
    for revision in revisions:
        if (
            isinstance(revision, int)
            and expected_metadata(revision).get(LOCALE_METADATA_PATH) == actual
        ):
            return revision
    return None


def known_managed_predecessor(
    destination: Path,
    relative: Path,
    predecessors: dict[str, object],
    project_revision: int | None,
) -> bool:
    """Authorize overwrite only for a path/hash pair shipped by this Skill."""
    if not destination.is_file() or destination.is_symlink():
        return False
    key = relative.as_posix()
    current = digest(destination)

    official_init = predecessors.get("official_init", {})
    if isinstance(official_init, dict) and official_init.get(key) == current:
        return True

    revisions = predecessors.get("bundle_revisions", {})
    if project_revision is not None and isinstance(revisions, dict):
        revision_hashes = revisions.get(project_revision, {})
        if isinstance(revision_hashes, dict) and revision_hashes.get(key) == current:
            return True
    return False


def trusted_refresh_source(
    destination: Path,
    relative: Path,
    predecessors: dict[str, object],
    project_revision: int | None,
) -> bool:
    return known_current_upstream_unchanged(
        destination, relative
    ) or known_managed_predecessor(
        destination,
        relative,
        predecessors,
        project_revision,
    )


def refresh_official_manifest_hashes(
    target: Path,
    manifests: list[tuple[Path, dict[str, object]]],
) -> list[str]:
    refreshed: list[str] = []
    localized_hashes: dict[str, str] = {}
    for source in source_assets():
        relative = source.relative_to(SOURCE_ROOT)
        destination = target / relative
        if destination.is_file() and not destination.is_symlink() and digest(destination) == digest(source):
            localized_hashes[relative.as_posix()] = digest(source)
    for relative, data in manifests:
        files = data.get("files")
        if not isinstance(files, dict):
            continue
        changed = False
        for key, expected in localized_hashes.items():
            if key in files and files[key] != expected:
                files[key] = expected
                changed = True
        if changed:
            atomic_write(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                target / relative,
                target,
            )
            refreshed.append(str(relative))
    return refreshed


def preflight_write_paths(target: Path) -> None:
    """Reject every known unsafe destination before the first managed write."""
    for source in source_assets():
        relative = source.relative_to(SOURCE_ROOT)
        unsafe = unsafe_component(target, relative)
        if unsafe is not None:
            raise ValueError(f"refusing unsafe managed path {relative}: {unsafe}")
    for relative in expected_metadata():
        unsafe = unsafe_component(target, relative)
        if unsafe is not None:
            raise ValueError(f"refusing unsafe metadata path {relative}: {unsafe}")


def inspect_assets(target: Path) -> dict[str, object]:
    missing: list[str] = []
    modified: list[str] = []
    protected: list[str] = []
    unsafe: list[str] = []
    invalid_metadata: list[str] = []
    upgradable_metadata: list[str] = []
    localizable_constitution = False
    localizable_official: list[str] = []
    unchanged = 0
    predecessors = load_managed_predecessors()
    project_revision = known_project_bundle_revision(target, predecessors)
    revision_maps = predecessors.get("bundle_revisions", {})
    predecessor_revisions = (
        set(revision_maps) if isinstance(revision_maps, dict) else set()
    )

    for source in source_assets():
        relative = source.relative_to(SOURCE_ROOT)
        destination = target / relative
        unsafe_path = unsafe_component(target, relative)
        if unsafe_path is not None:
            unsafe.append(str(relative))
        elif not destination.exists():
            missing.append(str(relative))
        elif digest(source) == digest(destination):
            unchanged += 1
        elif relative in PROTECTED_PATHS:
            if known_placeholder_constitution(destination):
                localizable_constitution = True
            else:
                protected.append(str(relative))
        elif trusted_refresh_source(
            destination,
            relative,
            predecessors,
            project_revision,
        ):
            localizable_official.append(str(relative))
        else:
            modified.append(str(relative))

    for relative, expected in expected_metadata().items():
        destination = target / relative
        unsafe_path = unsafe_component(target, relative)
        if unsafe_path is not None:
            unsafe.append(str(relative))
        elif not destination.exists():
            missing.append(str(relative))
        else:
            try:
                actual = destination.read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                invalid_metadata.append(str(relative))
            else:
                if actual == expected:
                    unchanged += 1
                elif known_previous_metadata(
                    relative,
                    actual,
                    predecessor_revisions,
                ):
                    upgradable_metadata.append(str(relative))
                else:
                    invalid_metadata.append(str(relative))

    changes_required = bool(
        missing
        or modified
        or unsafe
        or invalid_metadata
        or upgradable_metadata
        or localizable_constitution
        or localizable_official
    )
    return {
        "status": "changes_required" if changes_required else "ready",
        "target": str(target),
        "missing": missing,
        "modified": modified,
        "protected_customizations": protected,
        "unsafe_paths": sorted(set(unsafe)),
        "invalid_metadata": invalid_metadata,
        "upgradable_metadata": upgradable_metadata,
        "placeholder_constitution_needs_localization": localizable_constitution,
        "official_assets_need_localization": localizable_official,
        "recognized_predecessor_revision": project_revision,
        "unchanged_count": unchanged,
        "upstream_version": UPSTREAM_VERSION,
        "upstream_commit": UPSTREAM_COMMIT,
    }


def install(target: Path, force: bool) -> dict[str, object]:
    copied: list[str] = []
    updated: list[str] = []
    preserved: list[str] = []
    unchanged = 0
    predecessors = load_managed_predecessors()
    project_revision = known_project_bundle_revision(target, predecessors)
    revision_maps = predecessors.get("bundle_revisions", {})
    predecessor_revisions = (
        set(revision_maps) if isinstance(revision_maps, dict) else set()
    )
    manifests = load_official_manifests(target)
    blocking_asset_conflict = False

    preflight_write_paths(target)
    target.mkdir(parents=True, exist_ok=True)
    for source in source_assets():
        relative = source.relative_to(SOURCE_ROOT)
        destination = target / relative
        unsafe_path = unsafe_component(target, relative)
        if unsafe_path is not None:
            raise ValueError(
                f"refusing unsafe managed path {relative}: {unsafe_path}"
            )
        if destination.exists():
            if digest(source) == digest(destination):
                unchanged += 1
                continue
            if relative in PROTECTED_PATHS:
                if known_placeholder_constitution(destination):
                    atomic_copy(source, destination, target)
                    updated.append(str(relative))
                else:
                    preserved.append(str(relative))
                continue
            if not force and not trusted_refresh_source(
                destination,
                relative,
                predecessors,
                project_revision,
            ):
                preserved.append(str(relative))
                blocking_asset_conflict = True
                continue
            atomic_copy(source, destination, target)
            updated.append(str(relative))
        else:
            atomic_copy(source, destination, target)
            copied.append(str(relative))

    for relative, content in expected_metadata().items():
        destination = target / relative
        unsafe_path = unsafe_component(target, relative)
        if unsafe_path is not None:
            raise ValueError(
                f"refusing unsafe metadata path {relative}: {unsafe_path}"
            )
        existed = destination.exists()
        current = ""
        if existed:
            try:
                current = destination.read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                current = ""
            if current == content:
                unchanged += 1
                continue
        if relative == LOCALE_METADATA_PATH and blocking_asset_conflict and not force:
            preserved.append(str(relative))
            continue
        if existed:
            if not force and not known_previous_metadata(
                relative,
                current,
                predecessor_revisions,
            ):
                preserved.append(str(relative))
                continue
        atomic_write(content, destination, target)
        (updated if existed else copied).append(str(relative))

    refreshed_manifests = refresh_official_manifest_hashes(target, manifests)
    updated.extend(refreshed_manifests)

    scripts_root = target / ".specify/scripts/python"
    unsafe_scripts_root = unsafe_component(target, scripts_root.relative_to(target))
    if unsafe_scripts_root is not None:
        raise ValueError(f"refusing unsafe scripts directory: {unsafe_scripts_root}")
    for script in scripts_root.glob("*.py"):
        relative = script.relative_to(target)
        if unsafe_component(target, relative) is not None:
            raise ValueError(f"refusing unsafe script path: {relative}")
        script.chmod(script.stat().st_mode | 0o111)

    status = "attention_required" if preserved else "ready"
    return {
        "status": status,
        "target": str(target),
        "copied": copied,
        "updated": updated,
        "preserved": preserved,
        "unchanged_count": unchanged,
        "refreshed_official_manifests": refreshed_manifests,
        "upstream_version": UPSTREAM_VERSION,
        "upstream_commit": UPSTREAM_COMMIT,
    }


def main() -> int:
    args = parse_args()
    try:
        target = validate_target(args.target)
        validate_codex_overlay_target(target)
        if args.check:
            result = inspect_assets(target)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result["status"] == "ready" else 1
        result = install(target, args.force)
    except (OSError, ValueError) as exc:
        print(
            json.dumps(
                {"status": "error", "message": str(exc)}, ensure_ascii=False
            )
        )
        return 2

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "ready" else 1


if __name__ == "__main__":
    sys.exit(main())
