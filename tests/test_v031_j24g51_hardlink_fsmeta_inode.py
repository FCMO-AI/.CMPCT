"""J24G51 independent physical falsifier: signed inode-incompatible xattrs on hardlink aliases.

Research-only. An authenticated r24 metadata record may be logically valid as a
per-path table while impossible as a physical hardlink inode. Do not weaken
Reader/validator to make this adversarial specimen pass.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import msgpack
import pytest
import zstandard as zstd

from cmpct.builder import Builder
from cmpct.codec import FMAGIC, FTR, HDR, K_FILE, K_HARDLINK, MAGIC, VERSION
from cmpct.reader import CMPCT
from cmpct.validation import preflight_archive

HOST_KEY = "com.fcmo.cmpct.j24g51" if sys.platform == "darwin" else "user.cmpct_j24g51"
OWNER = "a-owner.bin"
ALIAS = "z-alias.bin"
PLAIN_B = "b-copy.bin"
PLAIN_C = "c-copy.bin"
VALUES = {OWNER: b"owner\x00\xff", ALIAS: b"alias\x00\xfe",
          PLAIN_B: b"independent-B", PLAIN_C: b"independent-C"}


def _sha(v: bytes) -> bytes:
    return hashlib.sha256(v).digest()


def _set_os_xattr(path: Path, value: bytes) -> None:
    if sys.platform == "darwin":
        subprocess.run(["/usr/bin/xattr", "-wx", HOST_KEY, value.hex(), str(path)],
                       check=True, capture_output=True, text=True)
    else:
        os.setxattr(path, HOST_KEY, value, follow_symlinks=False)


def _get_os_xattr(path: Path) -> bytes:
    if sys.platform == "darwin":
        p = subprocess.run(["/usr/bin/xattr", "-px", HOST_KEY, str(path)],
                           check=True, capture_output=True, text=True)
        return bytes.fromhex("".join(p.stdout.split()))
    return os.getxattr(path, HOST_KEY, follow_symlinks=False)


def _resign_fsmeta(archive: bytes, values: dict[str, bytes]) -> bytes:
    magic, ver, flags, cs, us, span, old_hash = HDR.unpack_from(archive)
    assert magic == MAGIC and ver == VERSION and flags == 0
    idxraw = zstd.ZstdDecompressor().decompress(
        archive[HDR.size:HDR.size + cs], max_output_size=us + 1)
    assert len(idxraw) == us and _sha(idxraw) == old_hash
    idx = msgpack.unpackb(idxraw, raw=False)
    by = {row[0]: (i, row) for i, row in enumerate(idx["files"])}
    assert set(by) == {OWNER, ALIAS, PLAIN_B, PLAIN_C}
    assert by[OWNER][1][1] == K_FILE
    assert by[ALIAS][1][1] == K_HARDLINK
    assert by[ALIAS][1][6] == [OWNER]
    assert by[PLAIN_B][1][1] == by[PLAIN_C][1][1] == K_FILE
    idx["fsmeta"] = {
        "owner": [0, 0],
        "owner_overrides": [],
        "xattrs": [[by[name][0], [[HOST_KEY, value]]]
                   for name, value in sorted(values.items(), key=lambda kv: by[kv[0]][0])],
    }
    raw = msgpack.packb(idx, use_bin_type=True)
    encoded = zstd.ZstdCompressor(level=3).compress(raw)
    records = archive[HDR.size + cs:HDR.size + cs + span]
    assert len(records) == span
    head = HDR.pack(MAGIC, VERSION, flags, len(encoded), len(raw), span, _sha(raw))
    footer = FTR.pack(FMAGIC, 0, 1, 0, 0, len(encoded), len(raw), 0, _sha(raw))
    return head + encoded + records + encoded + footer


@pytest.mark.skipif(sys.platform not in ("darwin", "linux"),
                    reason="native POSIX xattr inode semantics only")
def test_signed_hardlink_xattr_inode_contradiction(tmp_path: Path) -> None:
    probe = tmp_path / "probe.bin"
    probe.write_bytes(b"probe")
    _set_os_xattr(probe, b"control\x00")
    assert _get_os_xattr(probe) == b"control\x00"

    root = tmp_path / "source"
    root.mkdir()
    payload = b"shared-payload-J24G51\x00" * 100
    (root / OWNER).write_bytes(payload)
    os.link(root / OWNER, root / ALIAS)
    assert os.stat(root / OWNER).st_ino == os.stat(root / ALIAS).st_ino
    (root / PLAIN_B).write_bytes(payload)
    (root / PLAIN_C).write_bytes(payload)
    assert os.stat(root / PLAIN_B).st_ino != os.stat(root / PLAIN_C).st_ino

    original_path = tmp_path / "builder.cmpct"
    Builder(root, workers=1, reproducible=True).build(original_path)
    original = original_path.read_bytes()

    # Positive: alias metadata equal, distinct-content-independent inodes differ.
    equal_values = {**VALUES, ALIAS: VALUES[OWNER]}
    compatible = _resign_fsmeta(original, equal_values)
    good = tmp_path / "compatible.cmpct"
    good.write_bytes(compatible)
    assert preflight_archive(good)["files"] == 4
    with CMPCT(good) as ar:
        assert ar.verify() == 4
        dest = tmp_path / "compatible-out"
        ar.extractall(dest, metadata=True, require_xattrs=True)
    assert os.stat(dest / OWNER).st_ino == os.stat(dest / ALIAS).st_ino
    assert _get_os_xattr(dest / OWNER) == VALUES[OWNER]
    assert _get_os_xattr(dest / ALIAS) == VALUES[OWNER]
    assert _get_os_xattr(dest / PLAIN_B) == VALUES[PLAIN_B]
    assert _get_os_xattr(dest / PLAIN_C) == VALUES[PLAIN_C]
    assert os.stat(dest / PLAIN_B).st_ino != os.stat(dest / PLAIN_C).st_ino

    # Adversarial: signed per-path xattrs demand impossible values on one inode.
    contradictory = _resign_fsmeta(original, VALUES)
    bad = tmp_path / "contradictory.cmpct"
    bad.write_bytes(contradictory)
    preflight_accepted = True
    try:
        preflight_archive(bad)
    except Exception:
        preflight_accepted = False
    verify_accepted = False
    if preflight_accepted:
        with CMPCT(bad) as ar:
            try:
                verify_accepted = (ar.verify() == 4)
            except Exception:
                verify_accepted = False

    extract_accepted = False
    inode_equal = None
    observed = {}
    if preflight_accepted and verify_accepted:
        with CMPCT(bad) as ar:
            dest = tmp_path / "contradictory-out"
            try:
                ar.extractall(dest, metadata=True, require_xattrs=True)
                extract_accepted = True
            except Exception:
                pass
            if (dest / OWNER).exists() and (dest / ALIAS).exists():
                inode_equal = os.stat(dest / OWNER).st_ino == os.stat(dest / ALIAS).st_ino
                for name in VALUES:
                    if (dest / name).exists():
                        try:
                            observed[name] = _get_os_xattr(dest / name).hex()
                        except OSError:
                            observed[name] = None
    discrepancy = any(observed.get(n) != value.hex() for n, value in VALUES.items())
    result = {
        "question": "signed distinct xattrs on two hardlink paths",
        "platform": sys.platform,
        "source_sha256": _sha(original).hex(),
        "compatible_sha256": _sha(compatible).hex(),
        "contradictory_sha256": _sha(contradictory).hex(),
        "preflight_accepted": preflight_accepted,
        "verify_accepted": verify_accepted,
        "strict_extract_accepted": extract_accepted,
        "same_inode": inode_equal,
        "observed_hex": observed,
        "expected_hex": {k: v.hex() for k, v in VALUES.items()},
        "at_least_one_metadata_mismatch": discrepancy,
        "classification": ("ACCEPTED_WITH_INODE_CONTRADICTION"
                           if extract_accepted and discrepancy and inode_equal
                           else "REJECTED_OR_NOT_REPRODUCED"),
    }
    evidence_dir = os.environ.get("J24G51_EVIDENCE_DIR")
    if evidence_dir:
        out = Path(evidence_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "builder.cmpct").write_bytes(original)
        (out / "compatible.cmpct").write_bytes(compatible)
        (out / "contradictory.cmpct").write_bytes(contradictory)
        (out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("J24G51_RESULT", json.dumps(result, sort_keys=True))
    # Explicit source-exact negative claim: do not pass for a product that already rejects.
    assert preflight_accepted and verify_accepted and extract_accepted, result
    assert inode_equal and discrepancy, result
    assert _get_os_xattr((tmp_path / "contradictory-out") / OWNER) == VALUES[ALIAS]
    assert _get_os_xattr((tmp_path / "contradictory-out") / ALIAS) == VALUES[ALIAS]
    assert _get_os_xattr((tmp_path / "contradictory-out") / PLAIN_B) == VALUES[PLAIN_B]
    assert _get_os_xattr((tmp_path / "contradictory-out") / PLAIN_C) == VALUES[PLAIN_C]
