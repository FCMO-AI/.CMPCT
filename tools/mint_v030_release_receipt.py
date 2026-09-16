from __future__ import annotations

"""Fail-closed v0.30 release-receipt minting from durable JSON evidence.

This tool does not decide whether evidence is good enough. The release-lock manifest owns every
normative assertion. The mint only removes a dangerous clerical step: asserted facts are copied
verbatim from hashed durable JSON, bound to the current release-critical fingerprint, validated by
the canonical lock, and atomically published only if validation succeeds.
"""

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from tools import check_v030_release_lock as lock


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _repo_relative(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(lock.ROOT.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError(f"evidence must live inside the repository: {path}") from exc


def _parse_binding(raw: str) -> tuple[str, int, str]:
    """Parse facts.foo=0:json.path while keeping the accepted grammar deliberately small."""
    if "=" not in raw or ":" not in raw:
        raise ValueError(f"invalid binding {raw!r}; expected facts.NAME=INDEX:JSON.PATH")
    asserted_path, source = raw.split("=", 1)
    index_text, json_path = source.split(":", 1)
    if not asserted_path.startswith("facts.") or len(asserted_path) <= len("facts."):
        raise ValueError(f"invalid asserted path {asserted_path!r}")
    if not index_text.isdigit():
        raise ValueError(f"invalid evidence index in {raw!r}")
    if not json_path:
        raise ValueError(f"missing JSON path in {raw!r}")
    return asserted_path, int(index_text), json_path


def build_receipt(
    receipt_id: str,
    evidence_paths: list[Path],
    bindings: dict[str, tuple[int, str]],
    *,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    manifest = manifest or lock.load_manifest()
    spec = next((item for item in manifest["required_receipts"] if item.get("id") == receipt_id), None)
    if spec is None:
        raise ValueError(f"unknown release receipt id: {receipt_id}")
    if not evidence_paths:
        raise ValueError("at least one durable evidence JSON file is required")

    documents: list[Any] = []
    evidence: list[dict[str, str]] = []
    receipt_dir = manifest["receipt_directory"].rstrip("/") + "/"
    for path in evidence_paths:
        rel = _repo_relative(path)
        if rel == manifest["receipt_directory"].rstrip("/") or rel.startswith(receipt_dir):
            raise ValueError("receipt files may not be used as their own release evidence")
        safe_path = lock._safe_repo_file(rel)
        try:
            document = json.loads(safe_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"release fact evidence must be valid JSON: {rel}: {exc}") from exc
        documents.append(document)
        evidence.append({"path": rel, "sha256": _sha256(safe_path)})

    required_paths = {
        assertion["path"]
        for assertion in spec.get("assertions", [])
        if isinstance(assertion.get("path"), str) and assertion["path"].startswith("facts.")
    }
    if set(bindings) != required_paths:
        missing = sorted(required_paths - set(bindings))
        extra = sorted(set(bindings) - required_paths)
        raise ValueError(f"fact bindings must match manifest assertions exactly; missing={missing}, extra={extra}")

    facts: dict[str, Any] = {}
    fact_sources: dict[str, dict[str, Any]] = {}
    for asserted_path in sorted(required_paths):
        evidence_index, json_path = bindings[asserted_path]
        if evidence_index < 0 or evidence_index >= len(documents):
            raise ValueError(f"evidence index out of range for {asserted_path}")
        try:
            value = lock._lookup(documents[evidence_index], json_path)
        except KeyError as exc:
            raise ValueError(f"missing JSON path {json_path!r} for {asserted_path}") from exc
        facts[asserted_path.split(".", 1)[1]] = value
        fact_sources[asserted_path] = {"evidence_index": evidence_index, "json_path": json_path}

    fingerprint, _ = lock.fingerprint(manifest)
    # The strict release front door requires the fingerprint to be sourced from hashed durable JSON, not merely
    # copied into a receipt by the mint itself. Keep that source deterministic: evidence[0] is the custody witness.
    try:
        evidence_fingerprint = lock._lookup(documents[0], "candidate_fingerprint")
    except KeyError as exc:
        raise ValueError("evidence[0] must record candidate_fingerprint for strict release custody") from exc
    if evidence_fingerprint != fingerprint:
        raise ValueError(
            "evidence[0] candidate_fingerprint does not match the current release-critical fingerprint: "
            f"{evidence_fingerprint!r} != {fingerprint!r}"
        )

    return {
        "schema": lock.RECEIPT_SCHEMA,
        "id": receipt_id,
        "status": "pass",
        "owner_task": spec["owner_task"],
        "candidate_fingerprint": fingerprint,
        "candidate_fingerprint_source": {
            "evidence_index": 0,
            "json_path": "candidate_fingerprint",
        },
        "evidence": evidence,
        "facts": facts,
        "fact_sources": fact_sources,
    }


def write_validated_receipt(
    receipt: dict[str, Any],
    output: Path,
    *,
    manifest: dict[str, Any] | None = None,
) -> None:
    manifest = manifest or lock.load_manifest()
    spec = next(item for item in manifest["required_receipts"] if item.get("id") == receipt["id"])
    expected_fingerprint, _ = lock.fingerprint(manifest)
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_name(output.name + ".tmp")
    tmp.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    errors = lock.validate_receipt(tmp, spec, expected_fingerprint, manifest["receipt_directory"])
    if errors:
        tmp.unlink(missing_ok=True)
        raise ValueError("receipt failed canonical validation: " + "; ".join(errors))
    tmp.replace(output)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Mint one v0.30 release receipt by copying every normative fact from hashed durable JSON evidence."
    )
    parser.add_argument("--receipt-id", required=True)
    parser.add_argument("--evidence", action="append", type=Path, required=True)
    parser.add_argument(
        "--bind",
        action="append",
        required=True,
        metavar="FACT=INDEX:JSON_PATH",
        help="bind a manifest fact path, e.g. facts.tests_green=0:facts.tests_green",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    parsed: dict[str, tuple[int, str]] = {}
    for raw in args.bind:
        asserted_path, index, json_path = _parse_binding(raw)
        if asserted_path in parsed:
            raise SystemExit(f"duplicate binding for {asserted_path}")
        parsed[asserted_path] = (index, json_path)

    manifest = lock.load_manifest()
    receipt = build_receipt(args.receipt_id, args.evidence, parsed, manifest=manifest)
    output = args.output or (lock.ROOT / manifest["receipt_directory"] / f"{args.receipt_id}.json")
    try:
        output.resolve().relative_to(lock.ROOT.resolve())
    except ValueError as exc:
        raise SystemExit("receipt output must live inside the repository") from exc
    write_validated_receipt(receipt, output, manifest=manifest)
    print(json.dumps({"receipt": output.relative_to(lock.ROOT).as_posix(), "candidate_fingerprint": receipt["candidate_fingerprint"]}, indent=2))


if __name__ == "__main__":
    main()
