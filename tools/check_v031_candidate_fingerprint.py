#!/usr/bin/env python3
"""Prospective v0.31 source custody: complete candidate identity, not v0.30 release authority.

The v0.30 release lock and all published receipts remain immutable historical evidence.
Use this SHA-256 as an input to future exact-candidate gates; emitting a fingerprint alone
does not prove correctness, performance or release eligibility.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/V031_CANDIDATE_FINGERPRINT.json"
SCHEMA = "cmpct-v031-prospective-candidate-fingerprint-v1"


def load_manifest(path: Path = MANIFEST) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("schema") != SCHEMA or value.get("status") != "candidate-evidence-only-not-released":
        raise ValueError("unknown or falsely promoted candidate fingerprint manifest")
    patterns = value.get("fingerprint_globs")
    required = value.get("required_paths")
    if not isinstance(patterns, list) or not patterns or not isinstance(required, list) or not required:
        raise ValueError("candidate fingerprint must have glob coverage and required exact paths")
    for entry in patterns + required:
        if not isinstance(entry, str) or not entry or "\\" in entry or "\x00" in entry:
            raise ValueError("invalid candidate fingerprint path or pattern")
        parsed = PurePosixPath(entry)
        if parsed.is_absolute() or ".." in parsed.parts:
            raise ValueError("candidate fingerprint path escapes repository")
    if len(set(required)) != len(required) or len(set(patterns)) != len(patterns):
        raise ValueError("duplicate candidate fingerprint path or pattern")
    return value


def fingerprint(manifest: dict, *, root: Path = ROOT) -> tuple[str, list[str]]:
    """Hash exact path names and full source bytes using canonical globstar semantics.

    Include path identities so a rename/removal changes the result. Reject symlinks,
    external references, and generated Android artifacts instead of trusting a
    runner's mutable workspace as the source tree.
    """
    root = root.resolve()
    found: dict[str, Path] = {}
    for pattern in manifest["fingerprint_globs"]:
        if not isinstance(pattern, str) or "\\" in pattern or "\x00" in pattern:
            raise ValueError("unsafe fingerprint pattern")
        parsed = PurePosixPath(pattern)
        if parsed.is_absolute() or ".." in parsed.parts:
            raise ValueError("fingerprint pattern escapes source tree")
        for match in glob.glob(str(root / pattern), recursive=True):
            path = Path(match)
            if not path.is_file() and not path.is_symlink():
                continue
            relative = path.relative_to(root).as_posix()
            # Cargo generates Rust/C/header sources beneath target/ during package
            # installation. They are not canonical Git source and their build hashes
            # vary by runner; never let them contaminate candidate source identity.
            if relative.startswith("native/") and "target" in PurePosixPath(relative).parts:
                continue
            if relative.startswith("integrations/android/") and (
                "/build/" in relative or "/jniLibs/" in relative
            ):
                continue
            if path.is_symlink() or path.resolve() != path:
                raise ValueError(f"symlink or escaped candidate source: {relative}")
            found[relative] = path
    missing = set(manifest.get("required_paths", [])) - set(found)
    if missing:
        raise ValueError(f"candidate fingerprint missing mandatory custody sources: {sorted(missing)}")
    if not found:
        raise ValueError("empty candidate identity")
    digest = hashlib.sha256()
    rows = sorted(found)
    for relative in rows:
        encoded = relative.encode("utf-8")
        digest.update(len(encoded).to_bytes(4, "little"))
        digest.update(encoded)
        content = hashlib.sha256()
        with found[relative].open("rb") as stream:
            while block := stream.read(1024 * 1024):
                content.update(block)
        digest.update(content.digest())
    return digest.hexdigest(), rows



def assert_git_head_custody(
    rows: list[str], *, root: Path = ROOT, expected_head: str
) -> None:
    """Reject receipts whose scanned source cannot be attributed to exact Git HEAD.

    The source fingerprint measures worktree bytes. An untracked matching source
    could change that digest while the receipt's 'source_sha' stays unchanged;
    a dirty tracked source has the same problem. Git HEAD identity alone does
    not bind those bytes. Fail closed instead of silently excluding them.
    """

    root = root.resolve()

    def git_bytes(*args: str) -> bytes:
        try:
            return subprocess.run(
                ["git", *args],
                cwd=root,
                capture_output=True,
                check=True,
            ).stdout
        except (OSError, subprocess.CalledProcessError) as exc:
            raise ValueError("cannot establish Git HEAD custody for candidate source") from exc

    head = git_bytes("rev-parse", "HEAD").decode("ascii").strip()
    if head != expected_head:
        raise ValueError("candidate Git HEAD changed while source was being scanned")

    # NUL separation prevents quoted/escaped Git pathnames from passing the
    # membership check incorrectly. Only committed source may claim HEAD.
    tracked = {
        entry.decode("utf-8")
        for entry in git_bytes("ls-tree", "-r", "-z", "--name-only", expected_head).split(b"\0")
        if entry
    }
    untracked = sorted(set(rows) - tracked)
    if untracked:
        raise ValueError(
            "untracked source is not attributable to Git HEAD "
            f"({len(untracked)} paths; first: {untracked[:5]})"
        )

    # HEAD-vs-worktree includes both staged and unstaged tracked changes,
    # including removals that no longer appear in the filesystem glob scan.
    # Git's own filters preserve legitimate platform checkout line endings.
    dirty = [
        entry.decode("utf-8")
        for entry in git_bytes(
            "diff", "--no-ext-diff", "--no-textconv",
            "--name-only", "-z", expected_head, "--",
        ).split(b"\0")
        if entry
    ]
    if dirty:
        raise ValueError(
            "dirty tracked source cannot use a clean Git HEAD receipt "
            f"({len(dirty)} paths; first: {dirty[:5]})"
        )

    if git_bytes("rev-parse", "HEAD").decode("ascii").strip() != expected_head:
        raise ValueError("candidate Git HEAD changed during custody validation")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="JSON receipt location")
    args = parser.parse_args()
    manifest = load_manifest()
    digest, rows = fingerprint(manifest)
    git = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()
    expected = os.environ.get("EVIDENCE_HEAD")
    if expected and expected != git:
        raise SystemExit(f"candidate evidence SHA mismatch: {git} != {expected}")
    assert_git_head_custody(rows, root=ROOT, expected_head=git)
    payload = {
        "schema": "cmpct-v031-candidate-source-receipt-v1",
        "source_sha": git,
        "fingerprint": digest,
        "files": len(rows),
        "paths": rows,
        "historical_lock_unchanged_by_this_tool": True,
        "proof_scope": "source-identity-only; no product/release/performance credit",
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"source_sha": git, "fingerprint": digest, "files": len(rows)}))


if __name__ == "__main__":
    main()
