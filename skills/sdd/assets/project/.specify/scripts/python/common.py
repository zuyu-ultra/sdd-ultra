"""Shared helpers for Spec Kit Python scripts."""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path


STORAGE_CONFIG_PATH = Path(".specify/sdd-storage.json")
FEATURE_METADATA_NAME = ".sdd-feature.json"


def _trim_trailing_separators(value: Path) -> str:
    text = str(value)
    while len(text) > 1 and text.endswith((os.sep, "/")):
        text = text[:-1]
    return text


def find_specify_root(start_dir: Path | None = None) -> Path | None:
    current = (start_dir or Path.cwd()).resolve()
    while True:
        if (current / ".specify").is_dir():
            return current
        parent = current.parent
        if parent == current:
            return None
        current = parent


def resolve_specify_init_dir() -> Path:
    raw = os.environ.get("SPECIFY_INIT_DIR", "")
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    try:
        init_root = candidate.resolve(strict=True)
    except OSError:
        print(
            f"ERROR: SPECIFY_INIT_DIR does not point to an existing directory: {raw}",
            file=sys.stderr,
        )
        raise SystemExit(1)
    if not init_root.is_dir():
        print(
            f"ERROR: SPECIFY_INIT_DIR does not point to an existing directory: {raw}",
            file=sys.stderr,
        )
        raise SystemExit(1)
    if not (init_root / ".specify").is_dir():
        print(
            "ERROR: SPECIFY_INIT_DIR is not a Spec Kit project "
            f"(no .specify/ directory): {init_root}",
            file=sys.stderr,
        )
        raise SystemExit(1)
    return init_root


def get_repo_root(script_file: Path | None = None) -> Path:
    if os.environ.get("SPECIFY_INIT_DIR"):
        return resolve_specify_init_dir()

    specify_root = find_specify_root()
    if specify_root is not None:
        return specify_root

    if script_file is not None:
        script_root = find_specify_root(script_file.resolve().parent)
        if script_root is not None:
            return script_root

        # Installed scripts live at .specify/scripts/python/<script>.py.
        return script_file.resolve().parents[3]
    return Path.cwd().resolve()


def get_current_branch() -> str:
    return os.environ.get("SPECIFY_FEATURE", "")


def read_feature_json_feature_directory(repo_root: Path) -> str:
    feature_json = repo_root / ".specify" / "feature.json"
    if not feature_json.is_file():
        return ""
    try:
        data = json.loads(feature_json.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return ""
    value = data.get("feature_directory") if isinstance(data, dict) else None
    return value if isinstance(value, str) else ""


def _json_dump(data: dict[str, object]) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n"


def read_storage_config(repo_root: Path) -> dict[str, object]:
    config_path = repo_root / STORAGE_CONFIG_PATH
    if not config_path.is_file() or config_path.is_symlink():
        return {}
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        return {}
    return data


def persist_storage_config(
    repo_root: Path,
    *,
    mode: str,
    artifact_root: Path,
    active_feature_directory: Path,
    naming: str,
) -> None:
    if mode not in {"project", "external"}:
        raise ValueError(f"unsupported SDD storage mode: {mode}")
    root_value = (
        artifact_root.relative_to(repo_root).as_posix()
        if mode == "project"
        else str(artifact_root)
    )
    active_value = (
        active_feature_directory.relative_to(repo_root).as_posix()
        if mode == "project"
        else str(active_feature_directory)
    )
    payload: dict[str, object] = {
        "schema_version": 1,
        "mode": mode,
        "artifact_root": root_value,
        "active_feature_directory": active_value,
        "naming": naming,
    }
    specify_dir = repo_root / ".specify"
    specify_dir.mkdir(parents=True, exist_ok=True)
    (repo_root / STORAGE_CONFIG_PATH).write_bytes(
        _json_dump(payload).encode("utf-8")
    )


def _absolute_lexical(path: Path, repo_root: Path) -> Path:
    candidate = path.expanduser()
    if not candidate.is_absolute():
        candidate = repo_root / candidate
    return Path(os.path.abspath(candidate))


def _require_within_external_root(
    repo_root: Path,
    feature_dir: Path,
    storage_config: dict[str, object],
) -> tuple[str, Path]:
    mode = storage_config.get("mode")
    root_value = storage_config.get("artifact_root")
    if mode != "external" or not isinstance(root_value, str):
        inferred_mode = (
            "project"
            if feature_dir == repo_root / "specs"
            or (repo_root / "specs") in feature_dir.parents
            else "external"
        )
        inferred_root = repo_root / "specs" if inferred_mode == "project" else feature_dir.parent
        return inferred_mode, inferred_root

    raw_root = Path(root_value).expanduser()
    if not raw_root.is_absolute():
        print(
            "ERROR: External SDD artifact_root must be an absolute path in "
            f"{repo_root / STORAGE_CONFIG_PATH}: {root_value}",
            file=sys.stderr,
        )
        raise SystemExit(1)
    try:
        artifact_root = raw_root.resolve(strict=True)
    except OSError:
        print(
            "ERROR: External SDD artifact_root does not exist or cannot be read: "
            f"{raw_root}",
            file=sys.stderr,
        )
        raise SystemExit(1)
    if not artifact_root.is_dir():
        print(
            f"ERROR: External SDD artifact_root is not a directory: {artifact_root}",
            file=sys.stderr,
        )
        raise SystemExit(1)
    # Resolve existing symlink components before the containment check. This
    # prevents a child symlink inside an approved Obsidian root from silently
    # redirecting an active requirement to an unrelated directory.
    feature_dir = feature_dir.resolve(strict=False)
    try:
        relative = feature_dir.relative_to(artifact_root)
    except ValueError:
        print(
            "ERROR: Active SDD feature directory is outside the approved external "
            f"artifact root: feature={feature_dir}, root={artifact_root}",
            file=sys.stderr,
        )
        raise SystemExit(1)
    if relative == Path("."):
        print(
            "ERROR: The external artifact root itself cannot be used as a feature "
            "directory; each requirement needs its own child folder.",
            file=sys.stderr,
        )
        raise SystemExit(1)
    return "external", artifact_root


def persist_feature_json(repo_root: Path, feature_dir_value: str) -> None:
    # Strip the repo root prefix lexically (no resolve()) to mirror the
    # Bash/PowerShell helpers: with a symlinked <repo>/specs, resolve() would
    # escape the repo and persist a machine-specific absolute path instead of
    # the relative "specs/NNN-name" the other variants store.
    value = feature_dir_value
    relative = Path(value)
    if relative.is_absolute():
        try:
            value = relative.relative_to(repo_root).as_posix()
        except ValueError:
            value = str(relative)

    current = read_feature_json_feature_directory(repo_root)
    if current == value:
        return

    specify_dir = repo_root / ".specify"
    specify_dir.mkdir(parents=True, exist_ok=True)
    (specify_dir / "feature.json").write_bytes(
        _json_dump({"feature_directory": value}).encode("utf-8")
    )


@dataclass(frozen=True)
class FeaturePaths:
    repo_root: Path
    current_branch: str
    feature_dir: Path
    feature_spec: Path
    impl_plan: Path
    tasks: Path
    research: Path
    data_model: Path
    quickstart: Path
    contracts_dir: Path
    storage_mode: str
    artifact_root: Path


def get_feature_paths(
    *, no_persist: bool = False, script_file: Path | None = None
) -> FeaturePaths:
    repo_root = get_repo_root(script_file)
    current_branch = get_current_branch()

    storage_config = read_storage_config(repo_root)
    feature_dir_raw = os.environ.get("SPECIFY_FEATURE_DIRECTORY", "")
    feature_pointer_value = ""
    if feature_dir_raw:
        feature_dir = _absolute_lexical(Path(feature_dir_raw), repo_root)
        feature_pointer_value = feature_dir_raw
    elif (repo_root / ".specify" / "feature.json").is_file():
        stored = read_feature_json_feature_directory(repo_root)
        if not stored:
            print(
                "ERROR: Feature directory not found. Set SPECIFY_FEATURE_DIRECTORY "
                "or ensure .specify/feature.json contains feature_directory.",
                file=sys.stderr,
            )
            raise SystemExit(1)
        feature_dir = _absolute_lexical(Path(stored), repo_root)
        feature_pointer_value = stored
    elif isinstance(storage_config.get("active_feature_directory"), str):
        stored = str(storage_config["active_feature_directory"])
        feature_dir = _absolute_lexical(Path(stored), repo_root)
        feature_pointer_value = stored
    else:
        print(
            "ERROR: Feature directory not found. Set SPECIFY_FEATURE_DIRECTORY "
            "or run the specify command to create .specify/feature.json.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    storage_mode, artifact_root = _require_within_external_root(
        repo_root, feature_dir, storage_config
    )

    metadata_path = feature_dir / FEATURE_METADATA_NAME
    if storage_mode == "external" and metadata_path.is_file():
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            metadata = {}
        recorded_project = metadata.get("project_root") if isinstance(metadata, dict) else None
        if (
            isinstance(recorded_project, str)
            and _absolute_lexical(Path(recorded_project), repo_root) != repo_root
        ):
            print(
                "ERROR: The selected external SDD requirement belongs to a different "
                f"project: recorded={recorded_project}, current={repo_root}",
                file=sys.stderr,
            )
            raise SystemExit(1)

    if not no_persist:
        persist_feature_json(repo_root, feature_pointer_value or str(feature_dir))
        naming = storage_config.get("naming")
        if not isinstance(naming, str) or not naming:
            naming = (
                "YYYY年MM月DD日-需求名"
                if storage_mode == "external"
                else "NNN-short-name"
            )
        persist_storage_config(
            repo_root,
            mode=storage_mode,
            artifact_root=artifact_root,
            active_feature_directory=feature_dir,
            naming=naming,
        )

    if not current_branch:
        current_branch = Path(_trim_trailing_separators(feature_dir)).name

    return FeaturePaths(
        repo_root=repo_root,
        current_branch=current_branch,
        feature_dir=feature_dir,
        feature_spec=feature_dir / "spec.md",
        impl_plan=feature_dir / "plan.md",
        tasks=feature_dir / "tasks.md",
        research=feature_dir / "research.md",
        data_model=feature_dir / "data-model.md",
        quickstart=feature_dir / "quickstart.md",
        contracts_dir=feature_dir / "contracts",
        storage_mode=storage_mode,
        artifact_root=artifact_root,
    )


_SAFE_COMPONENT_PATTERN = re.compile(r"[a-z0-9-]+")


def _is_safe_component(value: object) -> bool:
    return (
        isinstance(value, str)
        and _SAFE_COMPONENT_PATTERN.fullmatch(value) is not None
    )


def _normalize_priority(value: object) -> int:
    if isinstance(value, bool):
        return 10
    try:
        priority = int(value)
    except (TypeError, ValueError, OverflowError):
        return 10
    return priority if priority >= 1 else 10


def _sorted_preset_ids(presets_dir: Path) -> list[str]:
    registry = presets_dir / ".registry"
    if registry.is_file():
        # Invalid JSON or registry shapes fall back to the directory scan below.
        try:
            data = json.loads(registry.read_text(encoding="utf-8"))
            presets = data.get("presets", {})
            return [
                pid
                for pid, meta in sorted(
                    presets.items(),
                    key=lambda kv: (
                        _normalize_priority(kv[1].get("priority"))
                        if isinstance(kv[1], dict)
                        else 10,
                        kv[0],
                    ),
                )
                if (
                    _is_safe_component(pid)
                    and isinstance(meta, dict)
                    and bool(meta.get("enabled", True))
                )
            ]
        except Exception:
            pass
    try:
        return sorted(
            p.name
            for p in presets_dir.iterdir()
            if p.is_dir() and _is_safe_component(p.name)
        )
    except OSError:
        return []


def _sorted_extension_ids(extensions_dir: Path) -> list[str]:
    registry = extensions_dir / ".registry"
    registered_ids: set[str] = set()
    extensions: dict[object, object] = {}
    if os.path.lexists(registry):
        if not registry.is_file():
            raise TemplateResolutionError(
                f"Invalid extension registry {registry}: not a regular file"
            )
        try:
            data = json.loads(registry.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise TemplateResolutionError(
                f"Failed to parse extension registry {registry}: {exc}"
            ) from exc
        if not isinstance(data, dict):
            raise TemplateResolutionError(
                f"Invalid extension registry {registry}: root must be a mapping"
            )
        raw_extensions = data.get("extensions", {})
        if not isinstance(raw_extensions, dict):
            raise TemplateResolutionError(
                f"Invalid extension registry {registry}: "
                "'extensions' must be a mapping"
            )
        extensions = raw_extensions
        registered_ids = {
            ext_id for ext_id in extensions if isinstance(ext_id, str)
        }

    ranked: list[tuple[int, str]] = []
    for ext_id, metadata in extensions.items():
        if (
            _is_safe_component(ext_id)
            and isinstance(metadata, dict)
            and bool(metadata.get("enabled", True))
        ):
            ranked.append((_normalize_priority(metadata.get("priority")), ext_id))

    try:
        ranked.extend(
            (10, path.name)
            for path in extensions_dir.iterdir()
            if (
                path.is_dir()
                and _is_safe_component(path.name)
                and path.name not in registered_ids
            )
        )
    except OSError:
        pass
    return [ext_id for _, ext_id in sorted(ranked)]


def _conventional_template(
    base_dir: Path, template_name: str
) -> Path | None:
    for candidate in (
        base_dir / "templates" / f"{template_name}.md",
        base_dir / f"{template_name}.md",
    ):
        if candidate.is_file():
            return candidate
    return None


def resolve_template(template_name: str, repo_root: Path) -> Path | None:
    """Resolve a template name to a file path using the priority stack.

    Order (mirrors resolve_template in scripts/bash/common.sh):
      1. .specify/templates/overrides/
      2. .specify/presets/<preset-id>/templates/ (sorted by .registry priority)
      3. .specify/extensions/<ext-id>/templates/ (hidden directories skipped)
      4. .specify/templates/ (core)
    """
    if not _is_safe_component(template_name):
        return None

    base = repo_root / ".specify" / "templates"

    override = base / "overrides" / f"{template_name}.md"
    if override.is_file():
        return override

    presets_dir = repo_root / ".specify" / "presets"
    if presets_dir.is_dir():
        for preset_id in _sorted_preset_ids(presets_dir):
            candidate = _conventional_template(
                presets_dir / preset_id, template_name
            )
            if candidate is not None:
                return candidate

    ext_dir = repo_root / ".specify" / "extensions"
    if ext_dir.is_dir():
        for extension_id in _sorted_extension_ids(ext_dir):
            ext = ext_dir / extension_id
            candidate = _conventional_template(ext, template_name)
            if candidate is not None:
                return candidate

    core = base / f"{template_name}.md"
    if core.is_file():
        return core
    return None


class TemplateResolutionError(RuntimeError):
    """Raised when template layers exist but cannot be composed safely."""


# Mirror the canonical PresetManifest contract (see src/specify_cli/presets)
# so runtime resolution rejects the same structurally malformed manifests.
_VALID_TEMPLATE_TYPES = ("template", "command", "script")
_VALID_TEMPLATE_STRATEGIES = ("replace", "prepend", "append", "wrap")
_VALID_SCRIPT_STRATEGIES = ("replace", "wrap")


def _validate_manifest_template_entry(entry: object) -> None:
    """Validate a single manifest template entry against the canonical rules."""
    if not isinstance(entry, dict):
        raise ValueError("manifest template entries must be mappings")
    if "type" not in entry or "name" not in entry or "file" not in entry:
        raise ValueError("manifest template entry missing type, name, or file")
    for field in ("type", "name", "file"):
        if not isinstance(entry[field], str):
            raise ValueError(f"manifest template {field} must be a string")
    if entry["type"] not in _VALID_TEMPLATE_TYPES:
        raise ValueError(f"invalid manifest template type '{entry['type']}'")
    strategy = entry.get("strategy", "replace")
    if not isinstance(strategy, str):
        raise ValueError("manifest template strategy must be a string")
    strategy = strategy.lower()
    if strategy not in _VALID_TEMPLATE_STRATEGIES:
        raise ValueError(f"invalid manifest template strategy '{strategy}'")
    if entry["type"] == "script" and strategy not in _VALID_SCRIPT_STRATEGIES:
        raise ValueError(
            f"invalid manifest script strategy '{strategy}'"
        )


def _preset_template_layer(
    preset_dir: Path, template_name: str
) -> tuple[Path, str] | None:
    """Return the preset template path and composition strategy."""
    manifest_path = preset_dir / "preset.yml"
    conventional = _conventional_template(preset_dir, template_name)

    try:
        import yaml
    except ImportError as exc:
        if manifest_path.is_file():
            raise TemplateResolutionError(
                "PyYAML is required to resolve preset template composition"
            ) from exc
        return (conventional, "replace") if conventional is not None else None

    if manifest_path.is_file():
        try:
            manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
            if not isinstance(manifest, dict):
                raise ValueError("manifest root must be a mapping")
            if "provides" not in manifest:
                raise ValueError("manifest missing provides section")
            provides = manifest["provides"]
            if not isinstance(provides, dict):
                raise ValueError("manifest provides must be a mapping")
            if "templates" not in provides:
                raise ValueError("manifest provides missing templates")
            templates = provides["templates"]
            if not isinstance(templates, list):
                raise ValueError("manifest templates must be a list")
            if not templates:
                raise ValueError("manifest must provide at least one template")
            for entry in templates:
                _validate_manifest_template_entry(entry)
            for entry in templates:
                if (
                    entry.get("name") != template_name
                    or entry.get("type", "template") != "template"
                ):
                    continue
                file_value = entry.get("file", "")
                strategy = entry.get("strategy", "replace")
                relative = Path(file_value)
                if (
                    not relative
                    or relative.is_absolute()
                    or ".." in relative.parts
                ):
                    return None
                candidate = preset_dir / relative
                if not candidate.is_file():
                    return None
                return candidate, strategy.lower()
        except (OSError, UnicodeError, ValueError, yaml.YAMLError) as exc:
            raise TemplateResolutionError(
                f"Failed to parse preset manifest {manifest_path}: {exc}"
            ) from exc

    return (conventional, "replace") if conventional is not None else None


_BROWNFIELD_SAFETY_OVERLAYS: dict[str, tuple[tuple[str, ...], str]] = {
    "spec-template": (
        ("## 存量行为与兼容性", "PB-###", "本次不会改变", "BUG-###", "RC-###", "因果链", "检测缺口"),
        """
## 不可覆盖的存量安全约束

<!-- SDD_BROWNFIELD_SAFETY_V1:spec-template -->

- 为每项未被本需求明确改变的现有可观察行为分配 `PB-###`，写明调用方、输入、输出、错误语义和兼容边界。
- 明确区分“本次会改变”与“本次不会改变”；用户批准不能豁免旧功能回退，破坏性意图必须采用兼容适配、并行版本或完成迁移后的独立退役流程。
- Bug 修复必须在写 `spec.md` 前先调查根因；规格以 `BUG-###`/`RC-###` 记录事实时间线、复现证据、`触发条件 → 第一个错误状态/值 → 外部症状` 因果链、根因状态/置信度、影响与检测缺口。根因未确认时只允许诊断草稿并阻断规划。
""",
    ),
    "plan-template": (
        ("## 现有实现与项目惯例", "NM-###", "RC-###", "## 回归验证矩阵", "变更前基线"),
        """
## 不可覆盖的存量实施关卡

<!-- SDD_BROWNFIELD_SAFETY_V1:plan-template -->

- 证据顺序固定为同一个类/组件、同模块、同领域、同项目；列出真实符号、路径、调用方、相邻测试及本次沿用的项目惯例。
- 复用阶梯固定为：直接调用现有实现 > 兼容扩展现有实现 > 提炼共享实现 > 新建符号。任何新 method/class/module/helper/service/endpoint/schema/dependency 都必须有获批的 `NM-###`、检索范围、被拒候选和不可复用理由。
- Bug 每项方案必须追踪到已确认 `RC-###` 和具体因果链阻断点，并补强规格中的检测缺口；根因未确认或被推翻时返回规格阶段。
- 回归验证矩阵必须覆盖所有 `PB-###`、Bug 复现、目标/相邻测试，以及项目标准 lint/typecheck/build/test；先实际记录变更前基线，无法运行即阻塞。
""",
    ),
    "tasks-template": (
        ("## 阶段 1：存量基线与复用确认", "PB-###", "NM-###", "RC-###", "项目标准 lint/typecheck/build/test"),
        """
## 不可覆盖的任务安全关卡

<!-- SDD_BROWNFIELD_SAFETY_V1:tasks-template -->

- 第一组阻塞任务必须读取目标类/模块、调用方和相邻测试，实际运行变更前基线，并把每个实现任务绑定到既有符号或已批准的 `NM-###`。
- 新功能必须保护全部 `PB-###`；Bug 修复必须先复核已确认 `RC-###`，再运行能因该根因正确失败的复现测试、执行直接命中根因的最小修复，并补强检测缺口。根因被推翻时停止并返回规格阶段。
- 源码变更后必须运行目标测试、相邻测试、与基线相同的命令及项目标准 lint/typecheck/build/test。任何基线之外的新失败都立即停止，任务不得勾选完成。
""",
    ),
    "checklist-template": (
        ("兼容", "PB-###", "RC-###", "因果链"),
        """
## 不可覆盖的存量兼容性审查

<!-- SDD_BROWNFIELD_SAFETY_V1:checklist-template -->

- [ ] CHK-BF001 所有未明确改变的现有可观察行为均以 `PB-###` 追踪，并具有可衡量的兼容边界。
- [ ] CHK-BF002 新符号例外、变更前基线、Bug 复现和完整回归要求均明确且可验证。
- [ ] CHK-BF003 Bug 的 `BUG-###`/`RC-###`、事实时间线、复现证据、完整因果链、根因置信度、影响与检测缺口均已写清；未确认根因明确阻断规划。
""",
    ),
    "constitution-template": (
        ("复用", "回归"),
        """
## 不可覆盖原则：复用优先与零回归

<!-- SDD_BROWNFIELD_SAFETY_V1:constitution-template -->

实现必须沿用同一个类、同模块和同项目的既有惯例，优先复用或兼容扩展现有符号。新需求不得破坏老功能；Bug 修复不得引入新 Bug。任何批准、模板、override、preset、extension、workflow 或 hook 都不能豁免这两条原则。
""",
    ),
}


def _enforce_brownfield_safety(template_name: str, content: str) -> str:
    """Restore non-negotiable brownfield gates removed by a replace layer."""
    policy = _BROWNFIELD_SAFETY_OVERLAYS.get(template_name)
    if policy is None:
        return content
    markers, overlay = policy
    sentinel = f"<!-- SDD_BROWNFIELD_SAFETY_V1:{template_name} -->"
    if sentinel in content and all(marker in content for marker in markers):
        return content
    return f"{content.rstrip()}\n\n{overlay.strip()}\n"


def resolve_template_content(template_name: str, repo_root: Path) -> str | None:
    """Resolve and compose template content through the project layer stack."""
    if not _is_safe_component(template_name):
        return None

    layers: list[tuple[Path, str]] = []

    def compose_from_base() -> str:
        try:
            content = layers[-1][0].read_bytes().decode("utf-8")
            for path, strategy in reversed(layers[:-1]):
                layer_content = path.read_bytes().decode("utf-8")
                if strategy == "prepend":
                    content = f"{layer_content}\n\n{content}"
                elif strategy == "append":
                    content = f"{content}\n\n{layer_content}"
                elif strategy == "wrap":
                    placeholder = "{CORE_TEMPLATE}"
                    if placeholder not in layer_content:
                        raise TemplateResolutionError(
                            f"Wrap layer {path} is missing {placeholder}"
                        )
                    content = layer_content.replace(placeholder, content)
                else:
                    raise TemplateResolutionError(
                        f"Unknown template composition strategy '{strategy}' in {path}"
                    )
        except (OSError, UnicodeError) as exc:
            raise TemplateResolutionError(
                f"Failed to read template layer for '{template_name}': {exc}"
            ) from exc
        return _enforce_brownfield_safety(template_name, content)

    override = (
        repo_root
        / ".specify"
        / "templates"
        / "overrides"
        / f"{template_name}.md"
    )
    if override.is_file():
        layers.append((override, "replace"))
        return compose_from_base()

    presets_dir = repo_root / ".specify" / "presets"
    for preset_id in _sorted_preset_ids(presets_dir):
        layer = _preset_template_layer(presets_dir / preset_id, template_name)
        if layer is not None:
            layers.append(layer)
            if layer[1] == "replace":
                return compose_from_base()

    extensions_dir = repo_root / ".specify" / "extensions"
    for extension_id in _sorted_extension_ids(extensions_dir):
        extension_dir = extensions_dir / extension_id
        candidate = _conventional_template(extension_dir, template_name)
        if candidate is not None:
            layers.append((candidate, "replace"))
            return compose_from_base()

    core = repo_root / ".specify" / "templates" / f"{template_name}.md"
    if core.is_file():
        layers.append((core, "replace"))
        return compose_from_base()

    if not layers:
        return None

    raise TemplateResolutionError(
        f"Template '{template_name}' has composing layers but no replace base"
    )


def get_invoke_separator(repo_root: Path) -> str:
    integration_json = repo_root / ".specify" / "integration.json"
    if not integration_json.is_file():
        return "."
    # Split the parse out of the lookup and guard the top-level shape, matching
    # read_feature_json_feature_directory above and the bash/PowerShell twins,
    # which both fall back to "." for any unusable integration.json:
    #   * a non-mapping top level ([], "forge", 42, null) is valid JSON, so
    #     json.JSONDecodeError never fires and state.get(...) raised
    #     AttributeError;
    #   * a non-UTF-8 file raises UnicodeDecodeError, which is a ValueError --
    #     not an OSError -- so it escaped the except tuple. Realistic on
    #     Windows, where PowerShell 5.1's Out-File/`>` default to UTF-16.
    try:
        state = json.loads(integration_json.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return "."
    if not isinstance(state, dict):
        return "."
    key = state.get("default_integration") or state.get("integration") or ""
    settings = state.get("integration_settings")
    if isinstance(key, str) and isinstance(settings, dict):
        entry = settings.get(key)
        if isinstance(entry, dict) and entry.get("invoke_separator") in {".", "-"}:
            return entry["invoke_separator"]
    return "."


def format_speckit_command(command_name: str, repo_root: Path) -> str:
    separator = get_invoke_separator(repo_root)
    name = command_name.lstrip("/")
    if name.startswith("speckit."):
        name = name[len("speckit.") :]
    elif name.startswith("speckit-"):
        name = name[len("speckit-") :]
    name = name.replace(".", separator)
    return f"$speckit{separator}{name}"
