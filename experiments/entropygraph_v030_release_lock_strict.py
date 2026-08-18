"""Strict hostile-input front door for the CMPCT v0.30 release lock.

The core release-lock engine deliberately focuses on evidence binding, threshold policy and coordination state.
This module adds the hostile-input grammar that must run *before* any receipt can influence promotion:

- JSON must be standards-compliant; Python's permissive NaN/Infinity extensions are rejected;
- every parsed float must be finite;
- evidence/task paths must remain ordinary repository files with no symlink component or root escape;
- JSON evidence used by receipts is pre-parsed under the same strict grammar before the core lock reads it.

Footnote: this file intentionally lives under ``experiments/entropygraph_v030_*`` because that surface is already
part of the release-critical fingerprint. Changing the strict gate therefore invalidates every prior receipt.
The underlying ``tools/check_v030_release_lock.py`` remains the single policy/evidence engine; this module is the
mandatory release CLI/front door, not a competing set of thresholds.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path, PurePosixPath
from typing import Any

from tools import check_v030_release_lock as CORE

ROOT = CORE.ROOT
DEFAULT_MANIFEST = CORE.DEFAULT_MANIFEST


class StrictReleaseInputError(ValueError):
    """Release metadata/evidence is non-canonical or unsafe to consume."""


def _reject_json_constant(token: str) -> None:
    raise StrictReleaseInputError(f"non-standard JSON numeric constant is forbidden: {token}")


def strict_json_loads(text: str, *, label: str) -> Any:
    try:
        value = json.loads(text, parse_constant=_reject_json_constant)
    except (json.JSONDecodeError, StrictReleaseInputError) as exc:
        raise StrictReleaseInputError(f"invalid strict JSON in {label}: {exc}") from exc
    _require_finite(value, label=label)
    return value


def _require_finite(value: Any, *, label: str, path: str = "$", nodes: int = 0) -> int:
    """Reject non-finite floats recursively with a bounded traversal counter.

    Footnote: JSON proper does not contain NaN/Infinity, but checking the parsed tree as well protects this gate
    if a future parser or programmatic caller supplies Python objects directly instead of text.
    """
    nodes += 1
    if nodes > 2_000_000:
        raise StrictReleaseInputError(f"{label} exceeds strict validation node budget")
    if isinstance(value, float) and not math.isfinite(value):
        raise StrictReleaseInputError(f"{label} contains non-finite number at {path}")
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str):
                raise StrictReleaseInputError(f"{label} contains non-string JSON object key at {path}")
            nodes = _require_finite(child, label=label, path=f"{path}.{key}", nodes=nodes)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            nodes = _require_finite(child, label=label, path=f"{path}[{index}]", nodes=nodes)
    return nodes


def strict_repo_file(rel: str) -> Path:
    """Resolve one ordinary repository file without following symlinked path components."""
    if not isinstance(rel, str) or not rel or "\\" in rel or "\x00" in rel:
        raise StrictReleaseInputError(f"unsafe repository evidence path: {rel!r}")
    parsed = PurePosixPath(rel)
    if parsed.is_absolute() or any(part in ("", ".", "..") for part in parsed.parts):
        raise StrictReleaseInputError(f"unsafe repository evidence path: {rel!r}")

    root = ROOT.resolve()
    cursor = ROOT
    for part in parsed.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise StrictReleaseInputError(f"release evidence path uses symlink component: {rel}")
    try:
        resolved = cursor.resolve(strict=True)
    except (FileNotFoundError, OSError) as exc:
        raise StrictReleaseInputError(f"release evidence file does not exist: {rel}") from exc
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise StrictReleaseInputError(f"release evidence path escapes repository root: {rel}") from exc
    if not resolved.is_file():
        raise StrictReleaseInputError(f"release evidence path is not a regular file: {rel}")
    return resolved


def load_manifest_strict(path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    manifest = strict_json_loads(path.read_text(encoding="utf-8"), label=path.relative_to(ROOT).as_posix())
    if not isinstance(manifest, dict):
        raise StrictReleaseInputError("release-lock manifest root must be an object")
    # Reuse the core semantic validator without letting it re-read permissive text.
    if manifest.get("schema") != "cmpct-v030-release-lock-manifest-v1":
        raise StrictReleaseInputError("unsupported v0.30 release-lock manifest schema")
    if manifest.get("release") != "0.30.0" or manifest.get("target_format_revision") != 25:
        raise StrictReleaseInputError("strict release lock targets only CMPCT 0.30.0 / format revision 25")
    if not isinstance(manifest.get("required_receipts"), list) or not manifest["required_receipts"]:
        raise StrictReleaseInputError("release-lock manifest has no required receipts")
    if not isinstance(manifest.get("fingerprint_globs"), list) or not manifest["fingerprint_globs"]:
        raise StrictReleaseInputError("release-lock manifest has no fingerprint surface")
    return manifest


def preflight(manifest: dict[str, Any]) -> list[str]:
    """Return strict-input failures without mutating core release state."""
    failures: list[str] = []

    for task in manifest.get("required_task_states", []):
        rel = task.get("path") if isinstance(task, dict) else None
        try:
            strict_repo_file(rel)
        except Exception as exc:
            failures.append(f"task path {rel!r}: {exc}")

    receipt_dir_value = manifest.get("receipt_directory")
    if not isinstance(receipt_dir_value, str) or not receipt_dir_value:
        return failures + ["manifest receipt_directory is missing or invalid"]
    receipt_dir = ROOT.joinpath(*PurePosixPath(receipt_dir_value).parts)

    for spec in manifest["required_receipts"]:
        if not isinstance(spec, dict) or not isinstance(spec.get("id"), str):
            failures.append("manifest contains malformed receipt specification")
            continue
        receipt_id = spec["id"]
        receipt_path = receipt_dir / f"{receipt_id}.json"
        if not receipt_path.exists():
            # Missing receipts are ordinary locked-state output owned by the core checker, not malformed input.
            continue
        try:
            rel_receipt = receipt_path.relative_to(ROOT).as_posix()
            strict_repo_file(rel_receipt)
            receipt = strict_json_loads(receipt_path.read_text(encoding="utf-8"), label=rel_receipt)
        except Exception as exc:
            failures.append(f"receipt {receipt_id}: {exc}")
            continue
        if not isinstance(receipt, dict):
            failures.append(f"receipt {receipt_id}: root must be an object")
            continue

        evidence = receipt.get("evidence")
        if not isinstance(evidence, list):
            continue
        for index, item in enumerate(evidence):
            if not isinstance(item, dict) or not isinstance(item.get("path"), str):
                continue
            rel = item["path"]
            try:
                evidence_path = strict_repo_file(rel)
            except Exception as exc:
                failures.append(f"receipt {receipt_id} evidence[{index}]: {exc}")
                continue
            if evidence_path.suffix.lower() == ".json":
                try:
                    strict_json_loads(evidence_path.read_text(encoding="utf-8"), label=rel)
                except Exception as exc:
                    failures.append(f"receipt {receipt_id} evidence[{index}]: {exc}")
    return failures


def check(manifest: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    strict_failures = preflight(manifest)
    core_ok, report = CORE.check(manifest)
    report = dict(report)
    report["strict_input_failures"] = strict_failures
    report["strict_input_green"] = not strict_failures
    report["release_unlocked"] = bool(core_ok and not strict_failures)
    report["strict_front_door"] = "experiments/entropygraph_v030_release_lock_strict.py"
    return report["release_unlocked"], report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Strict fail-closed front door for CMPCT v0.30 release evidence"
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--print-fingerprint", action="store_true")
    parser.add_argument("--template", metavar="RECEIPT_ID")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        manifest = load_manifest_strict(args.manifest)
    except Exception as exc:
        print(f"CMPCT v0.30 strict release lock: LOCKED\nstrict manifest failure: {exc}")
        return 1

    fingerprint, paths = CORE.fingerprint(manifest)
    if args.print_fingerprint:
        print(json.dumps({"candidate_fingerprint": fingerprint, "files": paths}, indent=2, allow_nan=False))
        return 0
    if args.template:
        print(json.dumps(CORE.template_for(args.template, manifest, fingerprint), indent=2, allow_nan=False))
        return 0

    ok, report = check(manifest)
    if args.json:
        print(json.dumps(report, indent=2, allow_nan=False))
    else:
        print(f"CMPCT v0.30 strict release lock: {'UNLOCKED' if ok else 'LOCKED'}")
        print(f"candidate fingerprint: {report['candidate_fingerprint']}")
        print(f"receipts: {len(report['passed_receipts'])}/{report['required_receipts']} passed")
        for error in report["strict_input_failures"]:
            print(f"- strict input: {error}")
        for receipt_id, errors in report["failures"].items():
            print(f"- {receipt_id}")
            for error in errors:
                print(f"    {error}")
        if report.get("task_state_failures"):
            print("- coordination task states")
            for error in report["task_state_failures"]:
                print(f"    {error}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
