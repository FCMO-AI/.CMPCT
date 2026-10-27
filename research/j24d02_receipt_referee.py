"""Independent J24D02 structured-evidence referee; does not import CMPCT."""
from __future__ import annotations
import copy
import errno
import hashlib
import json
from pathlib import Path
import sys


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def check(receipt: dict, repo: Path, *, expected_head: str | None = None) -> int:
    assert receipt["schema"] == "cmpct-j24d02-r1"
    if expected_head is not None:
        assert receipt["head_sha"] == expected_head
    assert receipt["reader_blob"] == "8b74c3994b59af63528acff960cd7f59f535bf8f"
    expected = []
    for family, filename in [
        ("direct", "tests/conformance/v24-direct-codecs.json"),
        ("chunked", "tests/conformance/v24-chunk-maps.json"),
    ]:
        fixture = json.loads((repo / filename).read_text())
        assert fixture["format_revision"] == 24
        for v in fixture["vectors"]:
            for mode in ("clean", "fault"):
                expected.append((family, v, mode))
    assert receipt["cases_total"] == len(expected) == 10
    assert len(receipt["cases"]) == 10
    seen = set()
    assertions = 8
    for ordinal, (row, (family, v, mode)) in enumerate(zip(receipt["cases"], expected)):
        ident = (row["family"], row["member"], row["mode"])
        assert ident not in seen
        seen.add(ident)
        assert ident == (family, v["name"], mode)
        assert row["archive_sha256"] == v["archive_sha256"]
        assert row["expected_member_sha256"] == v["logical_sha256"]
        sentinel = b"preexisting-destination-J24D02-" * 7 + bytes([ordinal])
        assert row["before_sha256"] == sha(sentinel)
        assert row["before_inode"] >= 0 and row["after_inode"] >= 0
        assert not row["stage_remainders"]
        if row["external_alias_created"]:
            assert row["external_alias_preserved"] is True
            assert row["external_alias_sha256"] == row["before_sha256"]
        else:
            assert row["external_alias_preserved"] is None
            assert row["external_alias_sha256"] is None
        assertions += 9

        if mode == "clean":
            assert row["decision"] == "CLEAN_EXACT_RECONSTRUCTION"
            assert row["after_sha256"] == v["logical_sha256"]
            assert row["after_size"] == v["logical_size"]
            assert row["fault_calls"] == 0
            assert row["real_short_write_hex"] == ""
            assert row["error"] is None and row["error_errno"] is None
            assertions += 6
        else:
            bits = bytes.fromhex(row["real_short_write_hex"])
            assert 1 <= len(bits) <= 7
            assert row["fault_calls"] == 2
            assert row["error_errno"] == errno.ENOSPC
            assert row["error"] in ("OSError",)
            assert row["after_inode"] == row["before_inode"]
            assertions += 5
            if family == "direct":
                assert row["decision"] == "STAGED_DIRECT_DESTINATION_PRESERVED"
                assert row["after_sha256"] == row["before_sha256"]
                assert row["after_size"] == len(sentinel)
                assertions += 3
            else:
                assert row["decision"] == "STAGED_CHUNK_DESTINATION_PRESERVED"
                assert row["after_sha256"] == row["before_sha256"]
                assert row["after_size"] == len(sentinel)
                assertions += 3
    assert receipt["clean_exact"] == 5
    assert receipt["direct_preserved"] == 3
    assert receipt["chunk_preserved"] == 2
    return assertions + 3


def adversarial_controls(original: dict, repo: Path) -> int:
    mutations = [
        lambda r: r.update(reader_blob="0000000000000000000000000000000000000000"),
        lambda r: r["cases"][1].update(after_sha256="00"*32),
        lambda r: r["cases"][1].update(error_errno=errno.EIO),
        lambda r: r["cases"][1].update(fault_calls=1),
        lambda r: r["cases"][1].update(after_inode=r["cases"][1]["before_inode"]+1),
        lambda r: r["cases"][7].update(stage_remainders=["leaked-stage"]),
        lambda r: r["cases"][0].update(expected_member_sha256="11"*32),
        lambda r: r["cases"].pop(),
        lambda r: r["cases"][1].update(external_alias_sha256="ff"*32) if r["cases"][1]["external_alias_created"] else r["cases"][1].update(external_alias_preserved=True),
    ]
    rejected = 0
    for mutate in mutations:
        item = copy.deepcopy(original)
        mutate(item)
        try:
            check(item, repo)
        except (AssertionError, ValueError, KeyError, IndexError):
            rejected += 1
    assert rejected == len(mutations)
    return rejected


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4):
        raise SystemExit("usage: referee RECEIPT_JSON REPO_ROOT [EXPECTED_HEAD]")
    receipt = json.loads(Path(sys.argv[1]).read_text())
    n = check(receipt, Path(sys.argv[2]), expected_head=sys.argv[3] if len(sys.argv) == 4 else None)
    negative = adversarial_controls(receipt, Path(sys.argv[2]))
    print(json.dumps({"checks_pass": n, "mutant_receipts_rejected": negative,
                      "result": "PASS", "head": receipt["head_sha"]}, sort_keys=True))
