#!/usr/bin/env python3
"""J24F02: independent post-SHA chunked-extraction namespace swap falsifier.

This test deliberately makes a second process rebind only the private staging
pathname between verification and publication. It never patches CMPCT source.
PASS means a vulnerability was REPRODUCED, not that CMPCT is safe.
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

READER_BLOB = "e716233403dabd0966863c45635e18fa5ac6afb8"
FIXTURE_BLOB = "91141405bb10b2e1226b0652e3aa0a13ba41846c"
ROOT = Path(__file__).resolve().parents[1]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def git_blob(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\x00" + data).hexdigest()


def actor(stage, quarantine, foreign_base64):
    """Only mutate one disposable stage directory entry, in a new process."""
    payload = base64.b64decode(foreign_base64, validate=True)
    before = stage.stat()
    os.rename(stage, quarantine)  # keep original inode live; prevent reuse
    with open(stage, "xb") as out:
        out.write(payload)
        out.flush()
        os.fsync(out.fileno())
    after = stage.stat()
    if before.st_ino == after.st_ino or before.st_dev != after.st_dev:
        raise AssertionError("stage inode failed to change")
    return dict(
        actor_pid=os.getpid(), uid=os.getuid() if hasattr(os, "getuid") else None,
        original_inode=before.st_ino, replacement_inode=after.st_ino,
        original_sha256=digest(quarantine.read_bytes()),
        replacement_sha256=digest(stage.read_bytes()),
        quarantine=str(quarantine),
    )


def trial(vector, destination):
    import cmpct.reader as source_mod
    from cmpct.reader import CMPCT
    name = vector["name"]
    archive_bytes = base64.b64decode(vector["archive_base64"], validate=True)
    assert len(archive_bytes) == vector["archive_bytes"]
    assert digest(archive_bytes) == vector["archive_sha256"]
    archive = destination / ("source-" + name + ".cmpct")
    archive.write_bytes(archive_bytes)
    pristine_sha = digest(archive.read_bytes())
    assert pristine_sha == vector["archive_sha256"]

    with CMPCT(archive) as reader:
        assert len(reader.files) == 1
        row = reader.by[name]
        assert row[6][0] == vector["storage_kind"]
        assert row[4] == vector["logical_size"]
        expected = reader.read(name)
        assert len(expected) == vector["logical_size"]
        assert digest(expected) == vector["logical_sha256"]

        # Strong ordinary control: same authentic archive, same Reader, no injection.
        control = destination / ("ordinary-" + name)
        reader.extractall(control, metadata=False)
        ordinary_bytes = (control / name).read_bytes()
        assert ordinary_bytes == expected

        foreign = bytes((byte ^ 0xA5) for byte in expected)
        assert len(foreign) == len(expected) and digest(foreign) != digest(expected)
        attacked = destination / ("swapped-" + name)
        attacked.mkdir()
        old_replace = os.replace
        evidence = []
        caught = None

        def interposed_replace(src, dst, *args, **kwargs):
            src = Path(src)
            dst = Path(dst)
            if dst == attacked / name and ".cmpct-part-" in src.name:
                if evidence:
                    raise AssertionError("multiple publication seam events")
                before = src.stat()
                stage_sha = digest(src.read_bytes())
                assert stage_sha == digest(expected), "source not verified before seam"
                assert src.stat().st_size == len(expected)
                quarantine = src.with_name(src.name + ".original-quarantine")
                assert not quarantine.exists()
                command = [sys.executable, str(Path(__file__).resolve()), "--actor",
                           str(src), str(quarantine), base64.b64encode(foreign).decode("ascii")]
                proc = subprocess.run(command, text=True, stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE, timeout=10, check=True)
                child = json.loads(proc.stdout)
                assert child["actor_pid"] != os.getpid()
                assert child["original_inode"] == before.st_ino
                assert child["replacement_inode"] != before.st_ino
                assert child["original_sha256"] == stage_sha
                assert child["replacement_sha256"] == digest(foreign)
                assert quarantine.stat().st_ino == before.st_ino
                evidence.append(dict(
                    seam="after_verified_fd_closed_before_os_replace",
                    original_stage_sha256=stage_sha,
                    original_stage_inode=before.st_ino,
                    child=child, destination=str(dst)))
            return old_replace(src, dst, *args, **kwargs)

        # Injection is a deterministic rendezvous, not an alteration of Reader.
        try:
            os.replace = interposed_replace
            try:
                reader.extractall(attacked, metadata=False)
            except Exception as exc:
                caught = repr(exc)
        finally:
            os.replace = old_replace

        if len(evidence) != 1:
            raise AssertionError("instrument never reached expected publication seam")
        published = attacked / name
        data = published.read_bytes() if published.exists() else None
        wrong_sha = digest(data) if data is not None else None
        result = {
            "vector": name, "storage_kind": vector["storage_kind"],
            "archive_sha256": pristine_sha, "original_member_sha256": digest(expected),
            "control_sha256": digest(ordinary_bytes),
            "attempted_sha256": digest(foreign),
            "published_sha256": wrong_sha,
            "published_length": len(data) if data is not None else None,
            "reader_exception": caught,
            "stage": evidence[0],
            "source_preserved": digest(archive.read_bytes()) == pristine_sha,
        }
        # Scope: a genuine deterministic adversarial success if all hold.
        reproduced = (
            caught is None and data == foreign and len(data) == len(expected)
            and result["source_preserved"]
        )
        result["decision"] = "VULNERABILITY_REPRODUCED" if reproduced else "NOT_REPRODUCED"
        quarantine = Path(evidence[0]["child"]["quarantine"])
        assert quarantine.read_bytes() == expected
        quarantine.unlink()
        assert not any(".cmpct-part-" in p.name for p in attacked.iterdir())
        return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--actor", nargs=3, metavar=("STAGE", "QUARANTINE", "PAYLOAD"))
    parser.add_argument("--output", default="j24f02-result.json")
    args = parser.parse_args()
    if args.actor:
        print(json.dumps(actor(Path(args.actor[0]), Path(args.actor[1]), args.actor[2]), sort_keys=True))
        return
    import cmpct.reader as mod
    reader_path = Path(mod.__file__).resolve()
    assert not reader_path.is_relative_to(ROOT), "Reader imported from checkout"
    reader_sha = git_blob(reader_path.read_bytes())
    assert reader_sha == READER_BLOB, (reader_path, reader_sha)
    fixtures_path = ROOT / "tests/conformance/v24-chunk-maps.json"
    assert git_blob(fixtures_path.read_bytes()) == FIXTURE_BLOB
    fixtures = json.loads(fixtures_path.read_text())
    assert len(fixtures["vectors"]) == 2
    with tempfile.TemporaryDirectory(prefix="j24f02-") as temp:
        rows = [trial(vector, Path(temp)) for vector in fixtures["vectors"]]
    result = dict(schema="cmpct-j24f02-v1", reader_blob=reader_sha,
                  reader_path=str(reader_path), fixture_blob=FIXTURE_BLOB,
                  platform=sys.platform, pid=os.getpid(), cases=rows,
                  scope="deterministic writable-stage-directory race, not arbitrary adversary",
                  decision=("VULNERABILITY_REPRODUCED" if all(
                      row["decision"] == "VULNERABILITY_REPRODUCED" for row in rows
                  ) else "PARTIAL_OR_NOT_REPRODUCED"))
    with open(args.output, "w", encoding="utf8") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
    print("J24F02_DECISION=" + result["decision"], flush=True)
    for row in rows:
        print("J24F02_CASE=" + json.dumps(row, sort_keys=True), flush=True)
    if result["decision"] != "VULNERABILITY_REPRODUCED":
        raise AssertionError("preregistered exact two-vector reproducer did not hold")


if __name__ == "__main__":
    main()
