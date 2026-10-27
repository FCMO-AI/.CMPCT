"""J24D04: source-exact installed-reader POSIX umask/overwrite ownership falsifier.

Research-only. See immutable prospective preregistration. Never alters Reader, fixtures,
metadata policy, or historical benchmark thresholds.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile


def digest(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def worker(args):
    from cmpct.reader import CMPCT
    import cmpct.reader as reader_module

    source_path = Path(reader_module.__file__).resolve()
    source_sha = digest(source_path.read_bytes().replace(b"\r\n", b"\n"))
    assert source_sha == args.expected_source_sha, (
        "installed source identity mismatch", source_sha, args.expected_source_sha
    )
    record = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
    archive_bytes = base64.b64decode(record["archive_base64"], validate=True)
    assert len(archive_bytes) == record["archive_bytes"]
    assert digest(archive_bytes) == record["archive_sha256"]
    sentinel = b"KEEP_PREVIOUS_CONTENT_UNCHANGED" * 3
    with tempfile.TemporaryDirectory(prefix="j24d04-real-") as td:
        root = Path(td)
        archive = root / "original-r24.cmpct"
        archive.write_bytes(archive_bytes)
        dest = root / "out"
        dest.mkdir()
        leaf = dest / record["name"]
        other = root / "outside-physical-alias"
        original_umask = os.umask(0o077)
        try:
            if args.case in ("existing", "alias"):
                leaf.write_bytes(sentinel)
                os.chmod(leaf, 0o600)
                if args.case == "alias":
                    os.link(leaf, other)
            prior_inode = leaf.stat().st_ino if leaf.exists() else None
            with CMPCT(archive) as reader:
                row = reader.by[record["name"]]
                assert row[6][0] == 0, "not an authentic S_BLOB golden"
                archive_mode = stat.S_IMODE(row[2])
                raw = reader.read(record["name"])
                assert digest(raw) == record["logical_sha256"]
                reader.extractall(dest, metadata=args.case == "metadata_true")
            actual = leaf.read_bytes()
            assert digest(actual) == record["logical_sha256"]
            after_mode = stat.S_IMODE(os.stat(leaf).st_mode)
            after_inode = leaf.stat().st_ino
            stage_files = [
                x.name for x in dest.iterdir() if ".cmpct-part-" in x.name
            ]
            assert not stage_files, stage_files
            if args.case == "alias":
                alias_sha = digest(other.read_bytes())
                alias_inode = other.stat().st_ino
            else:
                alias_sha = None
                alias_inode = None
        finally:
            os.umask(original_umask)
    return {
        "source": args.source, "case": args.case, "codec": record["codec"],
        "member": record["name"], "source_sha256": source_sha,
        "source_path": str(source_path), "archive_sha256": record["archive_sha256"],
        "logical_sha256": digest(actual), "expected_sha256": record["logical_sha256"],
        "archive_mode": archive_mode, "umask": 0o077,
        "output_mode": after_mode, "prior_mode": 0o600 if prior_inode is not None else None,
        "prior_inode": prior_inode, "output_inode": after_inode,
        "alias_sha256": alias_sha, "alias_inode": alias_inode,
        "original_sentinel_sha256": digest(sentinel),
        "inode_preserved": prior_inode is not None and prior_inode == after_inode,
        "alias_is_output_inode": alias_inode is not None and alias_inode == after_inode,
        "stage_leftovers": stage_files,
        "metadata": args.case == "metadata_true",
        "os_name": os.name,
    }


def orchestrate(args):
    repo = Path(args.repo).resolve()
    root = json.loads((repo / "tests/conformance/v24-direct-codecs.json").read_text())
    assert root["schema"] == "cmpct-v24-golden-direct-codecs-v1"
    assert root["format_revision"] == 24
    records = root["vectors"]
    assert {r["codec"] for r in records} == {0, 1, 4}
    results = []
    with tempfile.TemporaryDirectory(prefix="j24d04-orchestrate-") as td:
        tmp = Path(td)
        instrument = tmp / "j24d04_worker.py"
        instrument.write_bytes(Path(__file__).read_bytes())
        for source in ("original", "candidate"):
            site = Path(getattr(args, f"{source}_site")).resolve()
            source_tree = Path(getattr(args, f"{source}_tree")).resolve()
            expected_sha = digest((source_tree/"src/cmpct/reader.py").read_bytes().replace(b"\r\n", b"\n"))
            for record in records:
                fixture = tmp / f"golden-{record['codec']}.json"
                fixture.write_text(json.dumps(record))
                for case in ("new", "existing", "alias", "metadata_true"):
                    env = dict(os.environ)
                    env["PYTHONPATH"] = str(site)
                    cmd = [sys.executable, str(instrument), "--worker",
                           "--fixture", str(fixture), "--source", source,
                           "--case", case, "--expected-source-sha", expected_sha]
                    cp = subprocess.run(cmd, cwd=tmp, env=env, text=True,
                                        capture_output=True, timeout=100)
                    if cp.returncode != 0:
                        raise RuntimeError(f"{source}/{record['name']}/{case}: {cp.stdout}\n{cp.stderr}")
                    results.append(json.loads(cp.stdout))
    result = {
        "schema":"j24d04-direct-stage-mode-v1", "original_git":"80c358f8824ec1b20d349c92ed94c898090969b0",
        "candidate_parent_git":"1778085a1ff5278fadf5f3a12b5f950008a8d939",
        "observations":results, "expected_observations":24,
        "boundaries":["source-authenticated r24 only", "metadata and inode semantics only",
                      "external alias is a semantic difference, not a proven preferred behavior",
                      "not a whole-file transaction, same-UID race proof, release or performance gate"],
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, sort_keys=True, indent=2)+"\n", encoding="utf-8")
    print(f"J24D04_OBSERVATIONS={len(results)}")
    for r in results:
        print(f"J24D04_RESULT={r['source']} {r['member']} {r['case']}"
              f" archive_mode={oct(r['archive_mode'])} output_mode={oct(r['output_mode'])}"
              f" preserved_inode={r['inode_preserved']}")
    assert len(results) == 24


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--worker", action="store_true")
    p.add_argument("--fixture")
    p.add_argument("--source", choices=("original", "candidate"))
    p.add_argument("--case", choices=("new", "existing", "alias", "metadata_true"))
    p.add_argument("--expected-source-sha")
    p.add_argument("--original-tree")
    p.add_argument("--candidate-tree")
    p.add_argument("--original-site")
    p.add_argument("--candidate-site")
    p.add_argument("--repo")
    p.add_argument("--out")
    args = p.parse_args()
    if args.worker:
        print(json.dumps(worker(args), sort_keys=True))
    else:
        orchestrate(args)


if __name__ == "__main__":
    main()
