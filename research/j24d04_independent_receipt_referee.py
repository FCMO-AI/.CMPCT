"""Independent referee for J24D04 raw installed-source evidence.

Consumes JSON receipts; does not import CMPCT or reuse court control flow.
"""
import argparse
import hashlib
import json
from pathlib import Path


def check(path: Path, report_path: Path):
    document = json.loads(path.read_text(encoding="utf-8"))
    assert document["schema"] == "j24d04-direct-stage-mode-v1"
    rows = document["observations"]
    os_names = {r["os_name"] for r in rows}
    assert len(os_names) == 1, os_names
    expected_count = 24 if next(iter(os_names)) == "posix" else 18
    assert len(rows) == document["expected_observations"] == expected_count
    indexed = {}
    for row in rows:
        key = (row["source"], row["codec"], row["case"])
        assert key not in indexed, key
        indexed[key] = row
        assert row["logical_sha256"] == row["expected_sha256"]
        assert not row["stage_leftovers"]
        assert row["source_sha256"] and row["archive_sha256"]
        assert row["umask"] == 0o077
    assert len(indexed) == 2*3*(4 if os_name == "posix" else 3)
    assert {x["codec"] for x in rows} == {0, 1, 4}
    operating_systems = {x["os_name"] for x in rows}
    assert len(operating_systems) == 1
    os_name = operating_systems.pop()
    conditions = []
    for codec in (0,1,4):
        for case in (("new", "existing", "alias", "metadata_true") if os_name == "posix" else ("new", "existing", "alias")):
            old = indexed["original",codec,case]
            new = indexed["candidate",codec,case]
            assert old["archive_sha256"] == new["archive_sha256"]
            assert old["logical_sha256"] == new["logical_sha256"]
            assert old["archive_mode"] == new["archive_mode"]
            assert old["metadata"] == new["metadata"] == (case == "metadata_true")
        if os_name == "posix":
            new_old = indexed["original",codec,"new"]
            new_new = indexed["candidate",codec,"new"]
            mode = new_old["archive_mode"]
            assert new_old["output_mode"] == (mode & ~0o077), (
                "historical umask control failed", codec, new_old
            )
            assert new_new["output_mode"] == (mode or 0o666), (
                "stage fchmod mechanism differs from prereg expectation", codec, new_new
            )
            before = indexed["original",codec,"existing"]
            after = indexed["candidate",codec,"existing"]
            assert before["output_mode"] == 0o600
            assert before["inode_preserved"]
            assert after["output_mode"] == (mode or 0o666)
            assert not after["inode_preserved"]
            for source in ("original", "candidate"):
                assert indexed[source,codec,"metadata_true"]["output_mode"] == mode
            alias_old = indexed["original",codec,"alias"]
            alias_new = indexed["candidate",codec,"alias"]
            assert alias_old["alias_is_output_inode"] and alias_old["inode_preserved"]
            assert alias_old["alias_sha256"] == alias_old["logical_sha256"]
            assert not alias_new["alias_is_output_inode"] and not alias_new["inode_preserved"]
            assert alias_new["alias_sha256"] == alias_new["original_sentinel_sha256"]
            conditions.append({"codec":codec,"mode":oct(mode),
                               "fresh_metadata_false_original":oct(new_old["output_mode"]),
                               "fresh_metadata_false_candidate":oct(new_new["output_mode"]),
                               "mode_widening":bool(new_new["output_mode"] & ~new_old["output_mode"])})
    decision = ("POSIX_METADATA_FALSE_UMASK_WIDENING_CONFIRMED"
                if os_name == "posix" and any(x["mode_widening"] for x in conditions)
                else ("POSIX_NO_MODE_WIDENING_ON_GOLDENS" if os_name == "posix"
                      else "WINDOWS_EXACTNESS_ONLY_NO_MODE_CLAIM"))
    audit = {
        "schema":"j24d04-independent-receipt-referee-v1",
        "decision":decision,
        "raw_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
        "verified_observations":len(rows),
        "platform":os_name,
        "conditions":conditions,
        "scope":["POSITVE: complete exact read/output SHA, no staged leftovers",
                 "POSIX: historical vs staged real mode and alias/inode controls",
                 "Windows released Reader metadata=True raises NotImplementedError (initial hosted result); not retested",
                 "NOT MEASURED: ACL, Windows mode equivalence, races, product performance"],
    }
    report_path.write_text(json.dumps(audit,sort_keys=True,indent=2)+"\n")
    print(f"J24D04_REFEREE={decision}")
    print("J24D04_RECEIPTS_VERIFIED=24")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("raw")
    p.add_argument("out")
    a = p.parse_args()
    check(Path(a.raw),Path(a.out))
