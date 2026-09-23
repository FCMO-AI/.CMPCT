from __future__ import annotations

import copy
import unittest

from tools import proof_spine_v030_receipt as adapter


MANIFEST = {
    "schema": "cmpct-v030-release-lock-manifest-v1",
    "release": "0.30.0",
    "target_format_revision": 25,
    "required_receipts": [
        {"id": "canonical-architecture"},
        {"id": "compression-generalization"},
        {"id": "native-r25"},
    ],
}


def report(*, passed: list[str], failures: dict[str, list[str]], strict: list[str] | None = None,
           task: list[str] | None = None, unlocked: bool = False) -> dict:
    return {
        "schema": "cmpct-v030-release-lock-report-v1",
        "release": "0.30.0",
        "target_format_revision": 25,
        "candidate_fingerprint": "a" * 64,
        "fingerprinted_files": 123,
        "required_receipts": 3,
        "passed_receipts": passed,
        "failures": failures,
        "task_states": {},
        "task_state_failures": task or [],
        "strict_input_failures": strict or [],
        "strict_input_green": not strict,
        "release_unlocked": unlocked,
    }


class ProofSpineV030ReceiptTests(unittest.TestCase):
    def test_locked_release_exports_unknown_not_fabricated_product_failure(self) -> None:
        local = report(
            passed=["canonical-architecture"],
            failures={
                "compression-generalization": ["missing receipt"],
                "native-r25": ["missing receipt"],
            },
        )
        receipt = adapter.build_project_receipt(MANIFEST, local, observed_at="2026-09-15T22:00:00Z")
        states = {item["id"]: item["status"] for item in receipt["evidence"]}
        self.assertEqual(states["release_receipt_canonical-architecture"], "PASS")
        self.assertEqual(states["release_receipt_compression-generalization"], "UNKNOWN")
        self.assertEqual(states["release_receipt_native-r25"], "UNKNOWN")
        self.assertEqual(receipt["local_decisions"][0]["state"], "LOCKED")

    def test_unlocked_release_exports_all_required_proof_as_pass(self) -> None:
        local = report(
            passed=["canonical-architecture", "compression-generalization", "native-r25"],
            failures={},
            unlocked=True,
        )
        receipt = adapter.build_project_receipt(MANIFEST, local, observed_at="2026-09-15T22:00:00Z")
        self.assertTrue(all(item["status"] == "PASS" for item in receipt["evidence"]))
        self.assertEqual(receipt["local_decisions"][0]["state"], "UNLOCKED")

    def test_strict_input_failure_is_unknown_proof_not_release_authority(self) -> None:
        local = report(
            passed=[],
            failures={
                "canonical-architecture": ["stale fingerprint"],
                "compression-generalization": ["missing receipt"],
                "native-r25": ["missing receipt"],
            },
            strict=["unsafe evidence path"],
        )
        receipt = adapter.build_project_receipt(MANIFEST, local, observed_at="2026-09-15T22:00:00Z")
        strict = next(item for item in receipt["evidence"] if item["id"] == "strict_input_integrity")
        self.assertEqual(strict["status"], "UNKNOWN")
        self.assertEqual(receipt["local_decisions"][0]["state"], "LOCKED")

    def test_receipt_contains_evidence_only_boundary_and_no_contract_fields(self) -> None:
        local = report(
            passed=["canonical-architecture"],
            failures={"compression-generalization": ["missing"], "native-r25": ["missing"]},
        )
        receipt = adapter.build_project_receipt(MANIFEST, local, observed_at="2026-09-15T22:00:00Z")
        self.assertEqual(receipt["kind"], "FCMO_PROOF_SPINE_PROJECT_RECEIPT")
        self.assertEqual(receipt["authority"], "EVIDENCE_ONLY")
        self.assertEqual(receipt["project"], {"id": "cmpct", "repository": "FCMO-AI/.CMPCT"})
        self.assertNotIn("mission", receipt)
        self.assertNotIn("claims", receipt)
        self.assertNotIn("gates", receipt)

    def test_candidate_fingerprint_is_first_class_scope(self) -> None:
        local = report(
            passed=["canonical-architecture"],
            failures={"compression-generalization": ["missing"], "native-r25": ["missing"]},
        )
        receipt = adapter.build_project_receipt(MANIFEST, local, observed_at="2026-09-15T22:00:00Z")
        self.assertEqual(receipt["scope"]["candidate_fingerprint"], "a" * 64)
        self.assertEqual(receipt["scope"]["release"], "0.30.0")
        self.assertEqual(receipt["scope"]["format_revision"], 25)

    def test_inconsistent_unlock_flag_is_rejected(self) -> None:
        local = report(
            passed=["canonical-architecture", "compression-generalization", "native-r25"],
            failures={},
            unlocked=False,
        )
        with self.assertRaises(ValueError):
            adapter.build_project_receipt(MANIFEST, local, observed_at="2026-09-15T22:00:00Z")

    def test_unknown_passed_receipt_is_rejected(self) -> None:
        local = report(
            passed=["canonical-architecture", "not-in-manifest"],
            failures={"compression-generalization": ["missing"], "native-r25": ["missing"]},
        )
        with self.assertRaises(ValueError):
            adapter.build_project_receipt(MANIFEST, local, observed_at="2026-09-15T22:00:00Z")

    def test_source_report_digest_changes_when_local_report_changes(self) -> None:
        base = report(
            passed=["canonical-architecture"],
            failures={"compression-generalization": ["missing"], "native-r25": ["missing"]},
        )
        first = adapter.build_project_receipt(MANIFEST, base, observed_at="2026-09-15T22:00:00Z")
        changed = copy.deepcopy(base)
        changed["failures"]["native-r25"] = ["different evidence problem"]
        second = adapter.build_project_receipt(MANIFEST, changed, observed_at="2026-09-15T22:00:00Z")
        self.assertNotEqual(first["source_report_digest"], second["source_report_digest"])


if __name__ == "__main__":
    unittest.main()
