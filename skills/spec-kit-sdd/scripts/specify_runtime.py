#!/usr/bin/env python3
"""运行固定版本的完整 Spec Kit CLI，并执行显式风险授权。"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import venv
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
VENDOR_ROOT = SKILL_ROOT / "vendor" / "spec-kit"
LOCK_PATH = SKILL_ROOT / "vendor" / "upstream-lock.json"
MANIFEST_PATH = SKILL_ROOT / "vendor" / "MANIFEST.sha256"
WHEELHOUSE_ROOT = SKILL_ROOT / "vendor" / "wheelhouse"
WHEELHOUSE_MANIFEST = SKILL_ROOT / "vendor" / "WHEELHOUSE.sha256"
CREDENTIAL_KEYS = {
    "GH_TOKEN",
    "GITHUB_TOKEN",
    "AZURE_DEVOPS_PAT",
    "AZURE_CLIENT_SECRET",
}


def sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def lock() -> dict[str, object]:
    return json.loads(LOCK_PATH.read_text(encoding="utf-8"))


def runtime_base() -> Path:
    override = os.environ.get("SPEC_KIT_SDD_RUNTIME_DIR")
    if override:
        return Path(override).expanduser().resolve()
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Caches" / "spec-kit-sdd"
    if os.name == "nt":
        local = os.environ.get("LOCALAPPDATA")
        return (
            Path(local) if local else Path.home() / "AppData" / "Local"
        ) / "spec-kit-sdd"
    cache = os.environ.get("XDG_CACHE_HOME")
    return (Path(cache) if cache else Path.home() / ".cache") / "spec-kit-sdd"


def runtime_dir() -> Path:
    data = lock()
    fingerprint = sha256(MANIFEST_PATH)
    if WHEELHOUSE_MANIFEST.is_file():
        fingerprint += sha256(WHEELHOUSE_MANIFEST)
    manifest_id = hashlib.sha256(fingerprint.encode("ascii")).hexdigest()[:16]
    commit = str(data["commit"])[:12]
    return runtime_base() / "runtimes" / f"{commit}-{manifest_id}"


def runtime_python(directory: Path | None = None) -> Path:
    root = directory or runtime_dir()
    return root / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def runtime_specify(directory: Path | None = None) -> Path:
    root = directory or runtime_dir()
    return root / ("Scripts/specify.exe" if os.name == "nt" else "bin/specify")


def verify_vendor() -> None:
    command = [sys.executable, str(SKILL_ROOT / "scripts/build_vendored_manifest.py")]
    result = subprocess.run(command, check=False)
    if result.returncode != 0:
        raise RuntimeError("vendored Spec Kit snapshot failed integrity verification")


def verify_runtime(directory: Path | None = None) -> bool:
    executable = runtime_specify(directory)
    marker = (directory or runtime_dir()) / "spec-kit-sdd-runtime.json"
    if not executable.is_file() or not marker.is_file():
        return False
    try:
        metadata = json.loads(marker.read_text(encoding="utf-8"))
        expected = lock()
        if metadata.get("commit") != expected.get("commit"):
            return False
        if metadata.get("manifest_sha256") != sha256(MANIFEST_PATH):
            return False
        expected_wheelhouse = (
            sha256(WHEELHOUSE_MANIFEST) if WHEELHOUSE_MANIFEST.is_file() else None
        )
        if metadata.get("wheelhouse_manifest_sha256") != expected_wheelhouse:
            return False
        result = subprocess.run(
            [str(executable), "--version"],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except (OSError, ValueError, subprocess.SubprocessError):
        return False
    return result.returncode == 0 and str(expected["version"]) in result.stdout


def ensure_runtime(allow_network: bool) -> Path:
    verify_vendor()
    destination = runtime_dir()
    if verify_runtime(destination):
        return destination
    if destination.exists():
        raise RuntimeError(
            f"runtime exists but failed verification; preserve it for inspection: {destination}"
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    builder = venv.EnvBuilder(with_pip=True, clear=False, symlinks=False)
    builder.create(destination)
    python = runtime_python(destination)
    bundled_wheels = sorted(WHEELHOUSE_ROOT.glob("specify_cli-*.whl"))
    result: subprocess.CompletedProcess[bytes] | subprocess.CompletedProcess[str]
    if len(bundled_wheels) == 1 and WHEELHOUSE_MANIFEST.is_file():
        command = [
            str(python),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--no-input",
            "--no-index",
            "--find-links",
            str(WHEELHOUSE_ROOT),
            str(bundled_wheels[0]),
        ]
        result = subprocess.run(command, check=False)
    else:
        result = subprocess.CompletedProcess([], 1)
    if result.returncode != 0 and allow_network:
        command = [
            str(python),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--no-input",
            str(VENDOR_ROOT),
        ]
        result = subprocess.run(command, check=False)
    if result.returncode != 0:
        raise RuntimeError(
            "runtime bootstrap failed from the bundled wheelhouse; this platform "
            f"may require --allow-network. Incomplete runtime preserved at {destination}"
        )
    metadata = {
        "commit": lock()["commit"],
        "version": lock()["version"],
        "manifest_sha256": sha256(MANIFEST_PATH),
        "wheelhouse_manifest_sha256": (
            sha256(WHEELHOUSE_MANIFEST) if WHEELHOUSE_MANIFEST.is_file() else None
        ),
    }
    marker = destination / "spec-kit-sdd-runtime.json"
    marker.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if not verify_runtime(destination):
        raise RuntimeError(
            f"new runtime failed verification; runtime preserved at {destination}"
        )
    return destination


def command_path(argv: list[str]) -> tuple[str, ...]:
    return tuple(arg for arg in argv if not arg.startswith("-"))


def risk_for(argv: list[str]) -> set[str]:
    if not argv or any(arg in {"--help", "-h", "--version", "-V"} for arg in argv):
        return set()
    path = command_path(argv)
    if not path:
        return set()
    if path[:2] == ("self", "upgrade"):
        return {"network", "runtime-write", "destructive"}
    if path[:2] == ("self", "check"):
        return {"network"}
    if path[:2] == ("event", "run"):
        return {"project-write", "code-execution"}

    group = path[0]
    action = path[1] if len(path) > 1 else ""
    nested_action = path[2] if len(path) > 2 else ""

    risks: set[str] = set()
    if group == "init":
        risks.add("project-write")
        if any(value.startswith(("http://", "https://")) for value in argv):
            risks.update({"network", "code-execution"})
    if group in {"integration", "extension", "preset", "workflow", "bundle"}:
        if action in {"search", "info"}:
            risks.add("network")
        if action in {
            "install",
            "uninstall",
            "switch",
            "upgrade",
            "use",
            "scaffold",
            "add",
            "remove",
            "update",
            "enable",
            "disable",
            "set-priority",
            "run",
            "resume",
            "build",
            "init",
        }:
            risks.add("project-write")
        if action in {"remove", "uninstall", "switch", "upgrade", "update"}:
            risks.add("destructive")
        if group == "workflow" and action in {"run", "resume"}:
            risks.add("code-execution")
        if group in {"extension", "preset", "workflow", "bundle"} and action in {
            "add",
            "install",
            "update",
        }:
            risks.update({"network", "code-execution"})
        if group == "integration" and action in {"install", "upgrade"}:
            risks.update({"network", "code-execution"})
        if group == "bundle" and action == "init":
            risks.update({"network", "code-execution"})
        if action in {"catalog", "step", "overlay"}:
            leaf = nested_action
            if leaf in {"add", "remove", "enable", "disable", "set-priority"}:
                risks.add("project-write")
            if leaf in {"add", "search", "info"}:
                risks.add("network")
            if action == "step" and leaf in {"add", "remove"}:
                risks.add("code-execution")
            if leaf == "remove":
                risks.add("destructive")
    if any(arg in {"--force", "--all"} for arg in argv):
        risks.add("destructive")
    return risks


def validate_target(path: Path) -> Path:
    expanded = path.expanduser()
    if expanded.is_symlink():
        raise RuntimeError(f"refusing symlink target: {expanded}")
    resolved = expanded.resolve()
    if resolved == Path(resolved.anchor) or resolved == Path.home().resolve():
        raise RuntimeError(f"refusing broad target: {resolved}")
    if not resolved.is_dir():
        raise RuntimeError(f"target must be an existing directory: {resolved}")
    return resolved


def run_cli(args: argparse.Namespace) -> int:
    verify_vendor()
    if not verify_runtime():
        raise RuntimeError(
            "verified runtime is not installed; run `specify_runtime.py ensure --allow-network`"
        )
    argv = list(args.specify_args)
    if argv and argv[0] == "--":
        argv = argv[1:]
    risks = risk_for(argv)
    approvals = {
        "network": args.allow_network,
        "project-write": args.allow_project_write,
        "code-execution": args.allow_code_execution,
        "runtime-write": args.allow_runtime_write,
        "destructive": args.allow_destructive,
    }
    denied = sorted(risk for risk in risks if not approvals[risk])
    if denied:
        print(
            json.dumps(
                {
                    "status": "authorization_required",
                    "risks": sorted(risks),
                    "missing_approvals": denied,
                    "argv": argv,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 3

    target = validate_target(args.target)
    environment = os.environ.copy()
    if not args.allow_credentials:
        for key in CREDENTIAL_KEYS:
            environment.pop(key, None)
    command = [str(runtime_specify()), *argv]
    result = subprocess.run(
        command,
        cwd=target,
        env=environment,
        stdin=None if args.interactive else subprocess.DEVNULL,
        check=False,
    )
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    ensure_parser = subparsers.add_parser("ensure")
    ensure_parser.add_argument("--allow-network", action="store_true")

    subparsers.add_parser("status")

    classify_parser = subparsers.add_parser("classify")
    classify_parser.add_argument("specify_args", nargs=argparse.REMAINDER)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--target", type=Path, default=Path.cwd())
    run_parser.add_argument("--allow-network", action="store_true")
    run_parser.add_argument("--allow-project-write", action="store_true")
    run_parser.add_argument("--allow-code-execution", action="store_true")
    run_parser.add_argument("--allow-runtime-write", action="store_true")
    run_parser.add_argument("--allow-destructive", action="store_true")
    run_parser.add_argument("--allow-credentials", action="store_true")
    run_parser.add_argument("--interactive", action="store_true")
    run_parser.add_argument("specify_args", nargs=argparse.REMAINDER)

    args = parser.parse_args()
    try:
        if args.command == "ensure":
            directory = ensure_runtime(args.allow_network)
            print(json.dumps({"status": "ready", "runtime": str(directory)}))
            return 0
        if args.command == "status":
            verify_vendor()
            print(
                json.dumps(
                    {
                        "vendor": "verified",
                        "runtime": "ready" if verify_runtime() else "missing",
                        "runtime_dir": str(runtime_dir()),
                        "version": lock()["version"],
                        "commit": lock()["commit"],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0 if verify_runtime() else 1
        if args.command == "classify":
            argv = args.specify_args[1:] if args.specify_args[:1] == ["--"] else args.specify_args
            print(json.dumps({"argv": argv, "risks": sorted(risk_for(argv))}, ensure_ascii=False, indent=2))
            return 0
        if args.command == "run":
            return run_cli(args)
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False))
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
