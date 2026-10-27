"""Independent fixture-bound referee for J24D05 direct-stage experiments."""
import base64
import copy
import errno
import hashlib
import json
from pathlib import Path
import subprocess
import sys

MODES = ("native", "absent", "absent-fault", "oserror", "valueerror", "native-fault")

def sha(data):
    return hashlib.sha256(data).hexdigest()

def gitblob(data):
    prefix = b"blob " + str(len(data)).encode() + bytes([0])
    return hashlib.sha1(prefix + data).hexdigest()

def check(report, root, head):
    fixture = json.loads((root / "tests/conformance/v24-direct-codecs.json").read_text())
    assert fixture["format_revision"] == 24 and len(fixture["vectors"]) == 3
    assert report["schema"] == "cmpct-j24d05-r1"
    assert report["head_sha"] == head
    # Git stores canonical LF blob bytes even when Windows autocrlf materializes
    # CRLF in checkout. Bind to the exact immutable Git object, then separately
    # require that checkout bytes normalize to that object (no weaker SHA gate).
    canonical = subprocess.check_output(
        ["git", "show", f"{head}:src/cmpct/reader.py"], cwd=root)
    checkout = (root / "src/cmpct/reader.py").read_bytes()
    assert checkout.replace(b"\r\n", b"\n") == canonical
    assert report["reader_blob"] == gitblob(canonical)
    rows = report["cases"]
    assert len(rows) == 18
    score = 4
    for index, record in enumerate(rows):
        vector = fixture["vectors"][index // 6]
        mode = MODES[index % 6]
        assert (record["vector"], record["variant"]) == (vector["name"], mode)
        wire = base64.b64decode(vector["archive_base64"], validate=True)
        assert len(wire) == vector["archive_bytes"]
        assert sha(wire) == record["archive_sha256"] == vector["archive_sha256"]
        assert record["logical_sha256"] == vector["logical_sha256"]
        old = b"J24D05-PRIOR-DIRECT-OUTPUT-" * 4 + index.to_bytes(2, "little")
        assert record["before_sha256"] == sha(old)
        assert record["remaining_stages"] == [] and record["path_chmod_attempts"] == []
        score += 8
        if mode.endswith("-fault"):
            assert record["outcome"] == "SHORT_WRITE_ENOSPC_OLD_DEST_PRESERVED"
            assert record["error_type"] == "OSError" and record["error_errno"] == errno.ENOSPC
            assert record["after_sha256"] == record["before_sha256"]
            assert record["new_inode"] == record["old_inode"]
            assert record["write_calls"] == 2
            assert 1 <= len(bytes.fromhex(record["actual_kernel_short_write_hex"])) <= 7
            score += 6
        elif mode == "valueerror":
            assert record["outcome"] == "UNEXPECTED_FD_MODE_ERROR_PROPAGATED"
            assert record["error_type"] == "ValueError"
            assert record["after_sha256"] == record["before_sha256"]
            assert record["new_inode"] == record["old_inode"]
            assert record["write_calls"] == 0
            score += 5
        else:
            assert record["outcome"] == "CLEAN_SHA_EXACT"
            assert record["error_type"] is None
            assert record["after_sha256"] == vector["logical_sha256"]
            assert record["write_calls"] == 0
            score += 4
    return score

def mutation_checks(report, root, head):
    changes = [
        lambda x: x.update(reader_blob="missing"),
        lambda x: x["cases"][1].update(path_chmod_attempts=["unexpected"]),
        lambda x: x["cases"][2].update(write_calls=1),
        lambda x: x["cases"][2].update(error_errno=errno.EIO),
        lambda x: x["cases"][3].update(after_sha256="wrong"),
        lambda x: x["cases"][4].update(remaining_stages=["leftover"]),
        lambda x: x["cases"].pop(),
    ]
    rejected = 0
    for alter in changes:
        trial = copy.deepcopy(report)
        alter(trial)
        try:
            check(trial, root, head)
        except (AssertionError, KeyError, ValueError, IndexError):
            rejected += 1
    assert rejected == len(changes)
    return rejected

if __name__ == "__main__":
    assert len(sys.argv) == 4
    report = json.loads(Path(sys.argv[1]).read_text())
    repo = Path(sys.argv[2])
    head = sys.argv[3]
    checks = check(report, repo, head)
    rejections = mutation_checks(report, repo, head)
    print(json.dumps({"decision": "J24D05_PASS", "checks": checks,
                      "altered_receipts_rejected": rejections}, sort_keys=True))
