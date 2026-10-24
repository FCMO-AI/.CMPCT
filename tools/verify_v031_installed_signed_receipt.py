#!/usr/bin/env python3
"""Fail-closed *receipt* custody for actual installed-wheel symlink safety.

This independent proof consumer is intentionally not a second implementation
of Reader extraction. Its responsibility is to refuse partial, duplicated, or
misclassified platform observations before awarding aggregate CI credit.
"""
from __future__ import annotations

import re
from typing import Any

SCHEMA = "cmpct-v031-installed-wheel-signed-symlink-o3-v1"
CASES = frozenset({
    "parent_escape",
    "absolute_escape",
    "win_root_escape",
    "win_drive_escape",
    "safe_relative",
})
SHARED_NEGATIVES = frozenset({"parent_escape", "absolute_escape"})
WINDOWS_NEGATIVES = frozenset({"win_root_escape", "win_drive_escape"})
PLATFORMS = frozenset({"ubuntu-24.04", "macos-14", "windows-2025"})
HEX_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
HEX_SHA1 = re.compile(r"[0-9a-f]{40}\Z")


def validate_installed_signed_receipt(
    receipt: dict[str, Any], *, expected_head: str, platform: str
) -> str:
    """Return input-manifest SHA only if all five scoped outcomes are evidenced.

    Numeric counts or a bare boolean are *not* sufficient: they can silently
    certify two copies of one negative while omitting another critical case.
    """
    if platform not in PLATFORMS:
        raise ValueError(f"unknown O3 installed target platform: {platform!r}")
    if not isinstance(receipt, dict):
        raise ValueError("installed signed receipt must be an object")
    if (
        receipt.get("schema") != SCHEMA
        or not isinstance(expected_head, str)
        or not HEX_SHA1.fullmatch(expected_head)
        or receipt.get("source_sha") != expected_head
    ):
        raise ValueError("signed receipt schema/source identity mismatch")
    sha = receipt.get("fixture_manifest_sha256")
    if not isinstance(sha, str) or not HEX_SHA256.fullmatch(sha):
        raise ValueError("missing or malformed SHA-256 input custody")
    if not isinstance(receipt.get("host"), str) or not receipt["host"]:
        raise ValueError("missing source-executing host identity")
    if not isinstance(receipt.get("installed_module"), str) or not receipt["installed_module"]:
        raise ValueError("missing installed package module provenance")

    windows = platform == "windows-2025"
    negative_cases = SHARED_NEGATIVES | (WINDOWS_NEGATIVES if windows else frozenset())
    count = receipt.get("required_prewrite_negatives")
    if type(count) is not int or count != len(negative_cases):
        raise ValueError("incorrect required hostile-case count")
    physical = receipt.get("physical_safe_symlink_restored")
    if type(physical) is not bool or physical != (not windows):
        raise ValueError("missing or contradictory positive symlink evidence")

    raw = receipt.get("results")
    if not isinstance(raw, list) or len(raw) != len(CASES):
        raise ValueError("incomplete installed signed-case observation set")
    decisions: dict[str, str] = {}
    for entry in raw:
        if (
            not isinstance(entry, dict)
            or set(entry) != {"case", "result"}
            or not isinstance(entry["case"], str)
            or not isinstance(entry["result"], str)
        ):
            raise ValueError("malformed signed case entry")
        name = entry["case"]
        if name in decisions:
            raise ValueError(f"duplicate signed case in receipt: {name}")
        decisions[name] = entry["result"]
    if frozenset(decisions) != CASES:
        raise ValueError("missing/extra signed cases")
    for name in CASES:
        if name in negative_cases:
            expected = "prewrite_rejected"
        elif name == "safe_relative" and not windows:
            expected = "physical_relative_symlink_restored"
        else:
            expected = "logical_identity_verified"
        if decisions[name] != expected:
            raise ValueError(
                f"wrong O3 signed case result: {name}: {decisions[name]} != {expected}"
            )
    return sha
