"""Adversarial evidence-custody court for O3 installed-wheel receipts.

The original count-only aggregate falsely accepted duplicate parent-escape
negatives in place of an absent absolute-escape check. The product/Reader is
not mocked here: this tests only what CI may infer from hosted host receipts.
"""
from __future__ import annotations

from copy import deepcopy

import pytest

from tools.verify_v031_installed_signed_receipt import (
    validate_installed_signed_receipt,
)

HEAD = "1810a144d3432d630381d4c3f4a52ad103dd604b"
SHA = "5bf0a721d837ba07997020e89395083d8342ed71423249fca4dce0f47fa03f6d"
CASES = (
    "parent_escape",
    "absolute_escape",
    "win_root_escape",
    "win_drive_escape",
    "safe_relative",
)


def valid_receipt(platform: str) -> dict:
    windows = platform == "windows-2025"
    negatives = {"parent_escape", "absolute_escape"}
    if windows:
        negatives |= {"win_root_escape", "win_drive_escape"}
    cases = [
        {
            "case": name,
            "result": (
                "prewrite_rejected" if name in negatives
                else "physical_relative_symlink_restored"
                if name == "safe_relative" and not windows
                else "logical_identity_verified"
            ),
        }
        for name in CASES
    ]
    return {
        "schema": "cmpct-v031-installed-wheel-signed-symlink-o3-v1",
        "source_sha": HEAD,
        "host": platform,
        "installed_module": "/isolated/site-packages/cmpct/__init__.py",
        "required_prewrite_negatives": len(negatives),
        "physical_safe_symlink_restored": not windows,
        "fixture_manifest_sha256": SHA,
        "results": cases,
    }


@pytest.mark.parametrize("platform", ["ubuntu-24.04", "macos-14", "windows-2025"])
def test_accepts_complete_real_shape(platform: str) -> None:
    receipt = valid_receipt(platform)
    assert validate_installed_signed_receipt(receipt, expected_head=HEAD, platform=platform) == SHA
    receipt["results"].reverse()
    assert validate_installed_signed_receipt(receipt, expected_head=HEAD, platform=platform) == SHA


@pytest.mark.parametrize("platform", ["ubuntu-24.04", "macos-14", "windows-2025"])
def test_original_count_only_false_green_is_rejected(platform: str) -> None:
    receipt = valid_receipt(platform)
    n = receipt["required_prewrite_negatives"]
    receipt["results"] = [
        {"case": "parent_escape", "result": "prewrite_rejected"} for _ in range(n)
    ]
    # The original workflow checked only this count and a boolean; both passed.
    assert sum(x["result"] == "prewrite_rejected" for x in receipt["results"]) == n
    with pytest.raises(ValueError):
        validate_installed_signed_receipt(receipt, expected_head=HEAD, platform=platform)


@pytest.mark.parametrize("platform", ["ubuntu-24.04", "windows-2025"])
@pytest.mark.parametrize("mutation", [
    "duplicate_case", "missing_case", "wrong_negative", "wrong_positive",
    "fake_bool", "wrong_head", "malformed_sha", "malformed_entry",
])
def test_fail_closed_on_host_receipt_mutation(platform: str, mutation: str) -> None:
    receipt = deepcopy(valid_receipt(platform))
    if mutation == "duplicate_case":
        receipt["results"][1]["case"] = receipt["results"][0]["case"]
    elif mutation == "missing_case":
        receipt["results"].pop()
    elif mutation == "wrong_negative":
        receipt["results"][0]["result"] = "logical_identity_verified"
    elif mutation == "wrong_positive":
        receipt["results"][-1]["result"] = "logical_identity_verified" if platform != "windows-2025" else "physical_relative_symlink_restored"
    elif mutation == "fake_bool":
        receipt["required_prewrite_negatives"] = True
    elif mutation == "wrong_head":
        receipt["source_sha"] = "0" * 40
    elif mutation == "malformed_sha":
        receipt["fixture_manifest_sha256"] = "z" * 64
    elif mutation == "malformed_entry":
        receipt["results"][0]["unexpected"] = "accepted"
    with pytest.raises(ValueError):
        validate_installed_signed_receipt(receipt, expected_head=HEAD, platform=platform)


def test_wrong_platform_and_missing_host_rejected() -> None:
    receipt = valid_receipt("ubuntu-24.04")
    with pytest.raises(ValueError):
        validate_installed_signed_receipt(receipt, expected_head=HEAD, platform="other-os")
    receipt["host"] = ""
    with pytest.raises(ValueError):
        validate_installed_signed_receipt(receipt, expected_head=HEAD, platform="ubuntu-24.04")
