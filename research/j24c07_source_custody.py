#!/usr/bin/env python3
"""J24C07: source-exact, read-only auditor for two independent VZIP guard transfers.

Compare against both frozen source owners, never only the mutable candidate branch.
This instrument is scientific source custody, not a substitute for behavioral tests.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess


PARENT_SHA = "0a128ff55c7ae0f14c6bdf019a81b40f0d894eff"
OWNER_SHA = "a4b54266f7cb09e03f9d8704155774b10d6351ab"
PARENT_READER_BLOB = "b37b786966ac1506a0439567d4a58eea472d85f8"
PARENT_VALIDATOR_BLOB = "fbcf6e9c108799dc8b6f5c19e95bcb0618cf41e8"
PARENT_CODEC_BLOB = "29526db4203723d83523fc95d074c346b63d7587"
OWNER_VALIDATOR_BLOB = "7f436b0fc1cab82dcf7eb12e061385af764877c4"
OWNER_CODEC_BLOB = "05fa46ee3cad6116c3579d14a3d86e234b9d92a0"
OWNER_TEST_BLOB = "32da46fde7f531b28de6ef9f5c2770b03a2da276"


def source(path: Path) -> str:
    return path.read_bytes().replace(b"\r\n", b"\n").decode("utf-8")


def git_blob(path: Path) -> str:
    return subprocess.check_output(["git", "hash-object", str(path)], text=True).strip()


def section(contents: str, begin: str, end: str) -> str:
    assert contents.count(begin) == 1, (begin, "source boundary count")
    start = contents.index(begin)
    stop = contents.find(end, start + len(begin))
    assert stop > start, (begin, end, "missing end boundary")
    return contents[start:stop]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, default=Path("."))
    parser.add_argument("--parent", type=Path, required=True)
    parser.add_argument("--owner", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    ns = parser.parse_args()
    candidate, parent, owner = ns.candidate, ns.parent, ns.owner

    for path, expected in (
        (parent / "src/cmpct/reader.py", PARENT_READER_BLOB),
        (parent / "src/cmpct/validation.py", PARENT_VALIDATOR_BLOB),
        (parent / "src/cmpct/codec.py", PARENT_CODEC_BLOB),
        (owner / "src/cmpct/validation.py", OWNER_VALIDATOR_BLOB),
        (owner / "src/cmpct/codec.py", OWNER_CODEC_BLOB),
        (owner / "tests/test_j24k05_vzip_projection_contract.py", OWNER_TEST_BLOB),
    ):
        assert git_blob(path) == expected, (path, "frozen-owner drift")

    assert source(candidate / "src/cmpct/reader.py") == source(parent / "src/cmpct/reader.py"), "Reader owner drift"
    assert source(candidate / "tests/test_j24c07_vzip_guard_composition.py") == source(
        owner / "tests/test_j24k05_vzip_projection_contract.py"
    ), "candidate test altered historical J24K05 assertions"

    base_validator = source(parent / "src/cmpct/validation.py")
    fix_validator = source(owner / "src/cmpct/validation.py")
    candidate_validator = source(candidate / "src/cmpct/validation.py")
    recipe_begin, recipe_end = "\ndef _validate_recipe(", "\ndef _validate_storage("
    old_recipe = section(base_validator, recipe_begin, recipe_end)
    fixed_recipe = section(fix_validator, recipe_begin, recipe_end)
    old_call = "_validate_recipe(recipe, len(blobs), limits, rid)"
    new_call = "_validate_recipe(recipe, blobs, limits, rid)"
    assert base_validator.count(old_call) == 1
    assert fix_validator.count(new_call) == 1
    assert candidate_validator == base_validator.replace(old_recipe, fixed_recipe).replace(
        old_call, new_call
    ), "validator differs from exact two bounded owner changes"

    base_codec = source(parent / "src/cmpct/codec.py")
    fix_codec = source(owner / "src/cmpct/codec.py")
    candidate_codec = source(candidate / "src/cmpct/codec.py")
    range_begin, range_end = "\ndef range_vzip(", "\ndef _sparse_data_extents("
    old_range = section(base_codec, range_begin, range_end)
    fixed_range = section(fix_codec, range_begin, range_end)
    assert candidate_codec == base_codec.replace(old_range, fixed_range), "codec unexpected edit"
    assert fixed_range.count("len(result) != length") == 2
    assert "skeleton_bytes != blobs[skeleton][1]" in fixed_recipe
    assert "if projected_bytes != total:" in fixed_recipe
    assert "_validate_storage" in candidate_validator
    assert "S_CHUNKS" in candidate_validator and "S_CDC" in candidate_validator and "S_SPARSE" in candidate_validator

    receipt = {
        "question": "J24C07 signed VZIP guard onto guarded Reader",
        "decision": "SOURCE_EXACT_TWO_OWNER_COMPOSITION_PASS",
        "parent_commit": PARENT_SHA,
        "owner_commit": OWNER_SHA,
        "reader_blob": git_blob(candidate / "src/cmpct/reader.py"),
        "validator_blob": git_blob(candidate / "src/cmpct/validation.py"),
        "codec_blob": git_blob(candidate / "src/cmpct/codec.py"),
        "test_blob": git_blob(candidate / "tests/test_j24c07_vzip_guard_composition.py"),
        "source_sha256": {
            "reader": hashlib.sha256(source(candidate / "src/cmpct/reader.py").encode()).hexdigest(),
            "validation": hashlib.sha256(candidate_validator.encode()).hexdigest(),
            "codec": hashlib.sha256(candidate_codec.encode()).hexdigest(),
        },
        "changed_surfaces": ["validation._validate_recipe", "validation._validate_index.recipe_call", "codec.range_vzip"],
        "product_release_claim": False,
    }
    ns.out.parent.mkdir(parents=True, exist_ok=True)
    ns.out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("J24C07_SOURCE_EXACT_TWO_OWNER_COMPOSITION_PASS")


if __name__ == "__main__":
    main()
