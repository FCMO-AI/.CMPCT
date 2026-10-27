"""J24D03 independent source-bound referee over J24D02 + J24D03 raw decisions.

Does not import CMPCT or the old J24D02 referee; no release-credit inference.
"""
from __future__ import annotations

import base64
import copy
import errno
import hashlib
import json
from pathlib import Path
import sys


EXPECTED_READER_BLOB = "1273708b42d2164ac806eea9297ac6fc098104b4"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def vectors(repo: Path):
    out = []
    for family, name in (("direct", "v24-direct-codecs.json"), ("chunked", "v24-chunk-maps.json")):
        root = json.loads((repo / "tests/conformance" / name).read_text())
        assert root["format_revision"] == 24
        for v in root["vectors"]:
            data = base64.b64decode(v["archive_base64"], validate=True)
            assert sha(data) == v["archive_sha256"]
            out.append((family, v))
    assert len(out) == 5 and sum(f == "direct" for f, _ in out) == 3
    return out


def audit(direct: dict, mode: dict, repo: Path, head: str):
    expected = vectors(repo)
    assert direct["schema"] == "cmpct-j24d02-r1"
    assert direct["head_sha"] == head
    assert direct["reader_blob"] == EXPECTED_READER_BLOB
    assert direct["cases_total"] == len(direct["cases"]) == 10
    assert (direct["clean_exact"], direct["direct_preserved"], direct["chunk_preserved"]) == (5, 3, 2)
    checks = 8
    for i, (family, v) in enumerate(expected):
        for mode_ix, action in enumerate(("clean", "fault")):
            j = 2*i+mode_ix
            case = direct["cases"][j]
            assert (case["family"], case["member"], case["mode"]) == (family, v["name"], action)
            assert case["archive_sha256"] == v["archive_sha256"]
            assert case["expected_member_sha256"] == v["logical_sha256"]
            old = b"preexisting-destination-J24D02-" * 7 + bytes([j])
            assert case["before_sha256"] == sha(old)
            assert case["before_inode"] >= 0 and case["after_inode"] >= 0
            assert case["stage_remainders"] == []
            if case["external_alias_created"]:
                assert case["external_alias_preserved"] is True
                assert case["external_alias_sha256"] == sha(old)
            else:
                assert case["external_alias_preserved"] is None
                assert case["external_alias_sha256"] is None
            if action == "clean":
                assert case["decision"] == "CLEAN_EXACT_RECONSTRUCTION"
                assert case["after_sha256"] == v["logical_sha256"]
                assert case["after_size"] == v["logical_size"]
                assert case["fault_calls"] == 0
                assert case["real_short_write_hex"] == ""
                assert case["error"] is None and case["error_errno"] is None
            else:
                assert case["decision"] == ("STAGED_DIRECT_DESTINATION_PRESERVED" if family == "direct" else "STAGED_CHUNK_DESTINATION_PRESERVED")
                assert case["after_sha256"] == sha(old)
                assert case["after_size"] == len(old)
                assert case["after_inode"] == case["before_inode"]
                assert case["fault_calls"] == 2
                assert case["error"] == "OSError" and case["error_errno"] == errno.ENOSPC
                assert 1 <= len(bytes.fromhex(case["real_short_write_hex"])) <= 7
            checks += 19

    chunks = [v for f, v in expected if f == "chunked"]
    assert mode["schema"] == "cmpct-j24d03-mode-r1"
    assert mode["cases_total"] == len(mode["cases"]) == 8
    assert mode["os_name"] in ("posix", "nt")
    if mode["os_name"] == "nt":
        assert mode["native_fchmod_available"] is False
    else:
        assert mode["native_fchmod_available"] is True
    for i, v in enumerate(chunks):
        for mode_ix, variant in enumerate(("native", "absent", "oserror", "valueerror")):
            row = mode["cases"][i*4+mode_ix]
            assert (row["member"], row["storage_kind"], row["variant"]) == (v["name"], v["storage_kind"], variant)
            assert row["archive_sha256"] == v["archive_sha256"]
            assert row["expected_sha256"] == v["logical_sha256"]
            assert row["remainders"] == []
            old = b"J24D03-OLD-OUTPUT-" + bytes([i])
            assert row["old_sha256"] == sha(old)
            if variant == "valueerror":
                assert row["outcome"] == "REJECT_AND_PRESERVE"
                assert row["error"] == "ValueError"
                assert row["actual_sha256"] == sha(old)
                assert row["after_inode"] == row["previous_inode"]
            else:
                assert row["outcome"] == "EXACT_OUTPUT"
                assert row["error"] is None
                assert row["actual_sha256"] == v["logical_sha256"]
            checks += 11
    return checks


def hostile_receipt_checks(d: dict, m: dict, repo: Path, head: str):
    mutations = [
        ("direct:blob", lambda a, b: a.update(reader_blob="f"*40)),
        ("direct:head", lambda a, b: a.update(head_sha="a"*40)),
        ("direct:sha", lambda a, b: a["cases"][0].update(after_sha256="0"*64)),
        ("direct:errno", lambda a, b: a["cases"][1].update(error_errno=errno.EIO)),
        ("direct:shortwrite", lambda a, b: a["cases"][1].update(fault_calls=1)),
        ("direct:leak", lambda a, b: a["cases"][7].update(stage_remainders=["fake"])),
        ("direct:missing", lambda a, b: a["cases"].pop()),
        ("mode:false-success", lambda a, b: b["cases"][3].update(outcome="EXACT_OUTPUT")),
        ("mode:false-error", lambda a, b: b["cases"][3].update(error=None)),
        ("mode:wrong-image", lambda a, b: b["cases"][4].update(archive_sha256="f"*64)),
        ("mode:missing", lambda a, b: b["cases"].pop()),
        ("mode:api", lambda a, b: b.update(native_fchmod_available=not b["native_fchmod_available"])),
    ]
    rejected = []
    for label, mutate in mutations:
        a = copy.deepcopy(d)
        b = copy.deepcopy(m)
        mutate(a, b)
        try:
            audit(a, b, repo, head)
        except (AssertionError, KeyError, IndexError, TypeError, ValueError):
            rejected.append(label)
    assert len(rejected) == len(mutations), (len(rejected), len(mutations))
    return rejected


if __name__ == "__main__":
    if len(sys.argv) != 5:
        raise SystemExit("usage: j24d03_receipt_referee.py J24D02_JSON J24D03_JSON REPO_ROOT HEAD")
    direct = json.loads(Path(sys.argv[1]).read_text())
    mode = json.loads(Path(sys.argv[2]).read_text())
    repo = Path(sys.argv[3])
    head = sys.argv[4]
    n = audit(direct, mode, repo, head)
    rejected = hostile_receipt_checks(direct, mode, repo, head)
    print(json.dumps({"decision":"J24D03_COMPOSED_COURT_PASS", "head":head, "checks":n, "mutants_rejected":len(rejected), "mutant_labels":rejected},sort_keys=True))
