#!/usr/bin/env python3
"""Export CMPCT v0.30 strict release-lock state as an evidence-only Proof Spine receipt.

This adapter does not reimplement CMPCT release law. It asks the repository's authoritative
strict v0.30 release-lock front door for its current report, then normalizes that report into
the FCMO_PROOF_SPINE_PROJECT_RECEIPT boundary used by the private/shared Proof Spine experiment.
A LOCKED release remains a successful observation and therefore does not make this adapter exit
non-zero; only failure to obtain a trustworthy local report is an adapter error.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from experiments import entropygraph_v030_release_lock_strict as STRICT

RECEIPT_KIND = "FCMO_PROOF_SPINE_PROJECT_RECEIPT"
PROJECT_ID = "cmpct"
REPOSITORY = "FCMO-AI/.CMPCT"
LOCAL_DECISION_ID = "cmpct_v030_strict_release_lock"


def _canonical_digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _iso_now(value: str | None = None) -> str:
    if value is None:
        dt = datetime.now(timezone.utc)
    else:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            raise ValueError("--now must include an explicit timezone")
        dt = dt.astimezone(timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


def _validate_local_report(manifest: dict[str, Any], report: dict[str, Any]) -> None:
    if report.get("schema") != "cmpct-v030-release-lock-report-v1":
        raise ValueError(f"unsupported strict release report schema: {report.get('schema')!r}")
    if report.get("release") != manifest.get("release"):
        raise ValueError("strict release report release does not match manifest")
    if report.get("target_format_revision") != manifest.get("target_format_revision"):
        raise ValueError("strict release report format revision does not match manifest")
    if not isinstance(report.get("candidate_fingerprint"), str) or len(report["candidate_fingerprint"]) != 64:
        raise ValueError("strict release report has no valid candidate fingerprint")
    if not isinstance(report.get("passed_receipts"), list):
        raise ValueError("strict release report passed_receipts is not a list")
    if not isinstance(report.get("failures"), dict):
        raise ValueError("strict release report failures is not an object")
    if not isinstance(report.get("task_state_failures"), list):
        raise ValueError("strict release report task_state_failures is not a list")
    if not isinstance(report.get("strict_input_failures"), list):
        raise ValueError("strict release report strict_input_failures is not a list")


def _evidence_id(receipt_id: str) -> str:
    # Footnote: the universal federation layer reserves ``::`` for cross-project
    # namespacing. CMPCT's local receipt IDs contain only ordinary release-lock names,
    # but keep the transformation explicit so a future manifest cannot accidentally
    # escape the local evidence namespace.
    if "::" in receipt_id:
        raise ValueError(f"release-lock receipt id uses reserved federation delimiter: {receipt_id!r}")
    return f"release_receipt_{receipt_id}"


def build_project_receipt(
    manifest: dict[str, Any],
    report: dict[str, Any],
    *,
    observed_at: str,
) -> dict[str, Any]:
    """Normalize one authoritative local lock report without inventing project truth."""
    _validate_local_report(manifest, report)
    required_specs = manifest.get("required_receipts")
    if not isinstance(required_specs, list) or not required_specs:
        raise ValueError("release-lock manifest has no required receipts")

    required_ids: list[str] = []
    for spec in required_specs:
        if not isinstance(spec, dict) or not isinstance(spec.get("id"), str) or not spec["id"]:
            raise ValueError("release-lock manifest contains malformed receipt specification")
        required_ids.append(spec["id"])

    passed = set(report["passed_receipts"])
    unknown_passed = sorted(passed - set(required_ids))
    if unknown_passed:
        raise ValueError(f"strict report claims unknown passed receipts: {unknown_passed}")

    fingerprint = report["candidate_fingerprint"]
    evidence: list[dict[str, Any]] = []

    # Footnote: LOCKED does not necessarily prove a product defect. A missing, stale,
    # malformed, or incomplete proof receipt means the promotion premise is unproven,
    # so the universal epistemic state is UNKNOWN rather than a fabricated FAIL.
    evidence.append(
        {
            "id": "strict_input_integrity",
            "status": "PASS" if not report["strict_input_failures"] else "UNKNOWN",
            "causal_root": f"cmpct-v030-strict-input:{fingerprint}",
            "observed_at": observed_at,
            "source": {"failure_count": len(report["strict_input_failures"])},
        }
    )
    evidence.append(
        {
            "id": "coordination_task_states",
            "status": "PASS" if not report["task_state_failures"] else "UNKNOWN",
            "causal_root": f"cmpct-v030-task-state:{fingerprint}",
            "observed_at": observed_at,
            "source": {"failure_count": len(report["task_state_failures"])},
        }
    )

    failures = report["failures"]
    for receipt_id in required_ids:
        accepted = receipt_id in passed
        receipt_failures = failures.get(receipt_id, [])
        evidence.append(
            {
                "id": _evidence_id(receipt_id),
                "status": "PASS" if accepted else "UNKNOWN",
                "causal_root": f"cmpct-v030-release-receipt:{receipt_id}:{fingerprint}",
                "observed_at": observed_at,
                "source": {
                    "local_receipt_id": receipt_id,
                    "accepted_by_strict_lock": accepted,
                    "failure_count": len(receipt_failures) if isinstance(receipt_failures, list) else 1,
                },
            }
        )

    locally_unlocked = bool(report.get("release_unlocked"))
    expected_unlock = (
        not report["strict_input_failures"]
        and not report["task_state_failures"]
        and len(passed) == len(required_ids)
        and not failures
    )
    if locally_unlocked != expected_unlock:
        raise ValueError("strict release report unlock state is inconsistent with its own evidence surface")

    return {
        "schema_version": 1,
        "kind": RECEIPT_KIND,
        "authority": "EVIDENCE_ONLY",
        "project": {"id": PROJECT_ID, "repository": REPOSITORY},
        "observed_at": observed_at,
        "scope": {
            "subject": "v0.30-strict-release-lock",
            "release": manifest["release"],
            "format_revision": manifest["target_format_revision"],
            "candidate_fingerprint": fingerprint,
        },
        "evidence": evidence,
        "local_decisions": [
            {
                "id": LOCAL_DECISION_ID,
                "state": "UNLOCKED" if locally_unlocked else "LOCKED",
                "required_receipts": len(required_ids),
                "passed_receipts": len(passed),
                "strict_input_green": not report["strict_input_failures"],
                "task_states_green": not report["task_state_failures"],
            }
        ],
        "source_report_digest": _canonical_digest(report),
        "claim_boundary": (
            "This receipt only exports CMPCT's own strict v0.30 release-lock evidence. It does not change "
            "release thresholds, unlock CMPCT, merge/tag/version/publish, or grant Proof Spine release authority. "
            "The authoritative local decision remains experiments/entropygraph_v030_release_lock_strict.py."
        ),
    }


def observe(*, now: str | None = None) -> dict[str, Any]:
    manifest = STRICT.load_manifest_strict(STRICT.DEFAULT_MANIFEST)
    _ok, report = STRICT.check(manifest)
    return build_project_receipt(manifest, report, observed_at=_iso_now(now))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--now")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        receipt = observe(now=args.now)
    except Exception as exc:
        print(f"CMPCT Proof Spine evidence adapter error: {exc}")
        return 2

    text = json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    if args.json or not args.output:
        print(text, end="")

    # Footnote: a trustworthy observation of LOCKED is still a successful adapter run.
    # Fail-closed promotion belongs to CMPCT's strict lock and the consuming proof
    # contract; this exporter must not turn ordinary incomplete evidence into CI noise.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
