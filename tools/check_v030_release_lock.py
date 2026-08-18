from __future__ import annotations

import argparse
import glob
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "docs" / "V030_RELEASE_LOCK.json"
RECEIPT_SCHEMA = "cmpct-v030-release-receipt-v1"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_repo_file(rel: str) -> Path:
    if not isinstance(rel, str) or not rel or "\\" in rel or "\x00" in rel:
        raise ValueError(f"unsafe evidence path: {rel!r}")
    parsed = PurePosixPath(rel)
    if parsed.is_absolute() or any(part in ("", ".", "..") for part in parsed.parts):
        raise ValueError(f"unsafe evidence path: {rel!r}")
    path = ROOT.joinpath(*parsed.parts)
    if not path.is_file():
        raise ValueError(f"evidence file does not exist: {rel}")
    return path


def load_manifest(path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "cmpct-v030-release-lock-manifest-v1":
        raise ValueError("unsupported v0.30 release-lock manifest schema")
    if data.get("release") != "0.30.0":
        raise ValueError("v0.30 release lock must target 0.30.0")
    if data.get("target_format_revision") != 25:
        raise ValueError("v0.30 release lock currently requires canonical format revision 25")
    if not isinstance(data.get("fingerprint_globs"), list) or not data["fingerprint_globs"]:
        raise ValueError("release lock has no fingerprint surface")
    if not isinstance(data.get("required_receipts"), list) or not data["required_receipts"]:
        raise ValueError("release lock has no required receipts")
    return data


def fingerprint(manifest: dict[str, Any]) -> tuple[str, list[str]]:
    """Hash the complete release-critical surface while excluding evidence receipts themselves.

    Footnote: receipts are committed *after* the code they attest, so a commit SHA would be self-referential.
    The stable solution is a content fingerprint over every implementation, native, benchmark, test, workflow
    and release-policy path that can affect the evidence.  Adding documentation/evidence later does not change
    this fingerprint, but changing tested behavior or the evidence harness invalidates every old receipt.
    """
    paths: set[Path] = set()
    for pattern in manifest["fingerprint_globs"]:
        if not isinstance(pattern, str) or not pattern:
            raise ValueError("invalid fingerprint glob")
        for match in glob.glob(str(ROOT / pattern), recursive=True):
            candidate = Path(match)
            if candidate.is_file():
                paths.add(candidate.resolve())
    if not paths:
        raise ValueError("release fingerprint matched no files")

    rows: list[str] = []
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda item: item.relative_to(ROOT).as_posix()):
        rel = path.relative_to(ROOT).as_posix()
        content_sha = _sha256(path)
        rows.append(rel)
        encoded = rel.encode("utf-8")
        digest.update(len(encoded).to_bytes(4, "little"))
        digest.update(encoded)
        digest.update(bytes.fromhex(content_sha))
    return digest.hexdigest(), rows


def _lookup(data: dict[str, Any], dotted: str) -> Any:
    current: Any = data
    for part in dotted.split("."):
        if not isinstance(current, dict) or part not in current:
            raise KeyError(dotted)
        current = current[part]
    return current


def _check_assertion(receipt: dict[str, Any], assertion: dict[str, Any]) -> str | None:
    path = assertion.get("path")
    if not isinstance(path, str) or not path:
        return "manifest assertion has no path"
    try:
        value = _lookup(receipt, path)
    except KeyError:
        return f"missing asserted field {path}"

    if "eq" in assertion and value != assertion["eq"]:
        return f"{path}={value!r}, expected exactly {assertion['eq']!r}"
    if "one_of" in assertion:
        allowed = assertion["one_of"]
        if not isinstance(allowed, list) or value not in allowed:
            return f"{path}={value!r}, expected one of {allowed!r}"
    for operator in ("min", "max"):
        if operator not in assertion:
            continue
        bound = assertion[operator]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return f"{path}={value!r} is not numeric for {operator} assertion"
        if operator == "min" and value < bound:
            return f"{path}={value!r}, expected >= {bound!r}"
        if operator == "max" and value > bound:
            return f"{path}={value!r}, expected <= {bound!r}"
    return None


def validate_receipt(
    receipt_path: Path,
    spec: dict[str, Any],
    expected_fingerprint: str,
) -> list[str]:
    errors: list[str] = []
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"cannot parse receipt: {exc}"]

    expected_id = spec["id"]
    expected_owner = spec["owner_task"]
    if receipt.get("schema") != RECEIPT_SCHEMA:
        errors.append("unsupported receipt schema")
    if receipt.get("id") != expected_id:
        errors.append(f"receipt id {receipt.get('id')!r} != {expected_id!r}")
    if receipt.get("status") != "pass":
        errors.append(f"receipt status is {receipt.get('status')!r}, not 'pass'")
    if receipt.get("owner_task") != expected_owner:
        errors.append(f"owner_task {receipt.get('owner_task')!r} != {expected_owner!r}")
    if receipt.get("candidate_fingerprint") != expected_fingerprint:
        errors.append("candidate fingerprint does not match current release-critical surface")

    evidence = receipt.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        errors.append("receipt must reference at least one durable evidence file")
    else:
        for index, item in enumerate(evidence):
            if not isinstance(item, dict):
                errors.append(f"evidence[{index}] is not an object")
                continue
            rel = item.get("path")
            expected_sha = item.get("sha256")
            try:
                path = _safe_repo_file(rel)
            except Exception as exc:
                errors.append(f"evidence[{index}]: {exc}")
                continue
            if not isinstance(expected_sha, str) or len(expected_sha) != 64:
                errors.append(f"evidence[{index}] has invalid sha256 declaration")
                continue
            got = _sha256(path)
            if got != expected_sha.lower():
                errors.append(f"evidence[{index}] SHA-256 mismatch for {rel}")

    for assertion in spec.get("assertions", []):
        error = _check_assertion(receipt, assertion)
        if error:
            errors.append(error)
    return errors


def template_for(receipt_id: str, manifest: dict[str, Any], fp: str) -> dict[str, Any]:
    spec = next((item for item in manifest["required_receipts"] if item.get("id") == receipt_id), None)
    if spec is None:
        raise ValueError(f"unknown release receipt id: {receipt_id}")
    facts: dict[str, Any] = {}
    for assertion in spec.get("assertions", []):
        dotted = assertion["path"]
        if not dotted.startswith("facts."):
            continue
        key = dotted.split(".", 1)[1]
        if "eq" in assertion:
            facts[key] = assertion["eq"]
        elif "min" in assertion:
            facts[key] = f"REPLACE_WITH_VALUE_>=_{assertion['min']}"
        elif "max" in assertion:
            facts[key] = f"REPLACE_WITH_VALUE_<=_{assertion['max']}"
        else:
            facts[key] = "REPLACE_WITH_MEASURED_VALUE"
    return {
        "schema": RECEIPT_SCHEMA,
        "id": receipt_id,
        "status": "pass",
        "owner_task": spec["owner_task"],
        "candidate_fingerprint": fp,
        "evidence": [
            {"path": "REPLACE_WITH_DURABLE_REPOSITORY_EVIDENCE", "sha256": "REPLACE_WITH_SHA256"}
        ],
        "facts": facts,
    }


def check(manifest: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    fp, fingerprint_paths = fingerprint(manifest)
    receipt_dir = ROOT / manifest["receipt_directory"]
    failures: dict[str, list[str]] = {}
    passed: list[str] = []
    for spec in manifest["required_receipts"]:
        receipt_id = spec["id"]
        path = receipt_dir / f"{receipt_id}.json"
        if not path.is_file():
            failures[receipt_id] = [f"missing receipt {path.relative_to(ROOT).as_posix()}"]
            continue
        errors = validate_receipt(path, spec, fp)
        if errors:
            failures[receipt_id] = errors
        else:
            passed.append(receipt_id)
    report = {
        "schema": "cmpct-v030-release-lock-report-v1",
        "release": manifest["release"],
        "target_format_revision": manifest["target_format_revision"],
        "candidate_fingerprint": fp,
        "fingerprinted_files": len(fingerprint_paths),
        "required_receipts": len(manifest["required_receipts"]),
        "passed_receipts": passed,
        "failures": failures,
        "release_unlocked": not failures,
    }
    return not failures, report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fail closed unless every CMPCT v0.30 release receipt is current and durable")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--print-fingerprint", action="store_true")
    parser.add_argument("--template", metavar="RECEIPT_ID")
    parser.add_argument("--json", action="store_true", help="print machine-readable lock report")
    args = parser.parse_args(argv)

    manifest = load_manifest(args.manifest)
    fp, paths = fingerprint(manifest)
    if args.print_fingerprint:
        print(json.dumps({"candidate_fingerprint": fp, "files": paths}, indent=2))
        return 0
    if args.template:
        print(json.dumps(template_for(args.template, manifest, fp), indent=2))
        return 0

    ok, report = check(manifest)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        state = "UNLOCKED" if ok else "LOCKED"
        print(f"CMPCT v0.30 release lock: {state}")
        print(f"candidate fingerprint: {report['candidate_fingerprint']}")
        print(f"receipts: {len(report['passed_receipts'])}/{report['required_receipts']} passed")
        for receipt_id, errors in report["failures"].items():
            print(f"- {receipt_id}")
            for error in errors:
                print(f"    {error}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
