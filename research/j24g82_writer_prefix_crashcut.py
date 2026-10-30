#!/usr/bin/env python3
"""J24G82: every-prefix physical crash-cut recovery court for J24G80. Research only."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import tempfile
import traceback
from pathlib import Path

from cmpct import transactions as tx
from cmpct.reader import CMPCT
from cmpct.validation import preflight_archive
import j24g80_owned_writer_session as parent

PARENT = "d29c8b6b64017ab912cfd219d598501e00b62a72"
PREREG = "767c8ba713b5826de1028fa71f0f644c3148b88c"
WRITER_BLOB = "71bbc8a989d1da79d0f0dbe44f7f5c39f3304854"
SOURCE_BLOB = "4b29db0e5818faedc77ea9ff2c32b63c8b6ad2da"
N = 192
WHERE = "middle"
CUT_TYPES = ("first_uncommitted_byte", "last_payload_byte",
             "footer_start", "footer_mid", "footer_last_byte", "flipped_sha")


def attest():
    repo = Path(__file__).resolve().parents[1]
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()
    head = git("rev-parse", "HEAD")
    for ancestor in (PARENT, PREREG):
        subprocess.run(["git", "merge-base", "--is-ancestor", ancestor, head],
                       cwd=repo, check=True)
    assert git("rev-parse", "HEAD:src/cmpct/transactions.py") == WRITER_BLOB
    assert git("rev-parse", "HEAD:research/j24g80_owned_writer_session.py") == SOURCE_BLOB
    return dict(head=head, parent=PARENT, prereg=PREREG,
                writer_blob=WRITER_BLOB, source_blob=SOURCE_BLOB)


def sha(data: bytes):
    return hashlib.sha256(data).hexdigest()


def check_state(path: Path, generation: int, deleted: list[str], base_names: set[str]):
    expected = base_names - set(deleted[:generation])
    expected_depth = 0 if generation == 64 else generation
    with CMPCT(path) as ar:
        got = set(ar.by)
        assert got == expected, ("member names", generation, len(got), len(expected),
                                 sorted(got ^ expected)[:5])
        assert ar.delta_depth == expected_depth, ("delta_depth", generation, ar.delta_depth)
        assert ar.verify() == len(expected), ("strong verify", generation)
        for name in ("f00000.dat", "f00048.dat", "f00190.dat"):
            if name in expected:
                index = int(name[1:6])
                truth = hashlib.sha256(f"j24g80-{N}-{index}".encode()).digest()
                assert ar.read(name) == truth, ("content", generation, name)
    pre = preflight_archive(path)
    assert pre["files"] == len(expected), ("preflight count", generation, pre)
    assert pre["delta_depth"] == expected_depth, ("preflight depth", generation, pre)
    return sha(",".join(sorted(expected)).encode())


def run_case(root: Path, receipt: dict):
    base, builder_ns = parent.make_base(root, N, WHERE)
    names = parent.select(N, WHERE)
    base_bytes = base.read_bytes()
    base_names = {f"f{i:05d}.dat" for i in range(N)}
    receipt["base"] = dict(bytes=len(base_bytes), sha256=sha(base_bytes),
                           builder_ns=builder_ns, delete_names=names)
    receipt["cases"] = {}
    parent_rows = {}
    full = {}
    # Test exactly the existing source, not a separately reimplemented Writer.
    for variant, trial_number in (("public", 0), ("owned", 1)):
        row = parent.trial(root, base, N, WHERE, names, variant, trial_number)
        image = (root / f"{N}-{WHERE}-{variant}-{trial_number}.cmpct").read_bytes()
        assert len(row["physical"]) == 64
        assert len(image) == row["physical"][-1]["bytes"]
        parent_rows[variant] = row
        full[variant] = image
        receipt["cases"][variant] = dict(
            final_sha256=sha(image), final_bytes=len(image),
            physical_generations=row["physical"], checks=[], status="RUNNING")
        save(receipt)

    assert parent_rows["public"]["physical"] == parent_rows["owned"]["physical"], \
        "all 64 SHA/length witnesses must be identical"
    assert full["public"] == full["owned"], "final physical bytes diverge"
    receipt["physical_exact_prefix_parity_64_of_64"] = True
    save(receipt)

    scratch = root / "recovery-cut.cmpct"
    for variant in ("public", "owned"):
        image = full[variant]
        lengths = [len(base_bytes)] + [x["bytes"] for x in parent_rows[variant]["physical"]]
        assert lengths == sorted(set(lengths)), "every physical generation must add bytes"
        for g in range(1, 65):
            start, end = lengths[g-1:g+1]
            footer_begin = end - tx.FTR.size
            assert footer_begin > start + 2, ("payload too small", g, start, end)
            assert image[:start] == (base_bytes if g == 1 else image[:start])
            assert sha(image[:end]) == parent_rows[variant]["physical"][g-1]["sha256"], \
                ("bad original generation witness", variant, g)
            # Completed generation: current state must be fully visible.
            scratch.write_bytes(image[:end])
            digest = check_state(scratch, g, names, base_names)
            receipt["cases"][variant]["checks"].append(
                dict(generation=g, cut="fully_committed", bytes=end,
                     recovered_generation=g, state_sha256=digest, outcome="PASS"))

            # Model cuts inside the appended generation's payload and footer.
            offsets = {
                "first_uncommitted_byte": start + 1,
                "last_payload_byte": footer_begin - 1,
                "footer_start": footer_begin,
                "footer_mid": footer_begin + (tx.FTR.size // 2),
                "footer_last_byte": end - 1,
            }
            assert start < offsets["first_uncommitted_byte"] < footer_begin
            assert len(set(offsets.values())) == len(offsets), (g, offsets)
            assert all(start < cut < end for cut in offsets.values())
            for cut_kind, cut in offsets.items():
                scratch.write_bytes(image[:cut])
                digest = check_state(scratch, g-1, names, base_names)
                receipt["cases"][variant]["checks"].append(
                    dict(generation=g, cut=cut_kind, bytes=cut,
                         recovered_generation=g-1, state_sha256=digest,
                         prefix_sha256=sha(image[:cut]), outcome="PASS"))

            damaged = bytearray(image[:end])
            damaged[-1] ^= 0xA5
            assert damaged[-1] != image[end-1]
            scratch.write_bytes(damaged)
            digest = check_state(scratch, g-1, names, base_names)
            receipt["cases"][variant]["checks"].append(
                dict(generation=g, cut="flipped_sha", bytes=end,
                     recovered_generation=g-1, state_sha256=digest,
                     prefix_sha256=sha(damaged), outcome="PASS"))
            save(receipt)

        receipt["cases"][variant]["status"] = "PASS"
        save(receipt)

    # Every logical result of the same physical cut must also agree between variants.
    pub, own = (receipt["cases"][v]["checks"] for v in ("public", "owned"))
    assert [(x["generation"], x["cut"], x["bytes"], x["state_sha256"],
             x["recovered_generation"]) for x in pub] == [
               (x["generation"], x["cut"], x["bytes"], x["state_sha256"],
                x["recovered_generation"]) for x in own]
    receipt["checked_cases_per_variant"] = len(pub)
    assert len(pub) == 64 * (1 + len(CUT_TYPES)), len(pub)
    receipt["status"] = "PASS"
    receipt["decision"] = "PREFIX_AND_CRASHCUT_EQUIVALENCE_SURVIVED_RESTRICTED_COURT"
    save(receipt)


def save(receipt: dict):
    dest = Path(os.environ.get("J24G82_EVIDENCE_DIR", "evidence"))
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "j24g82-result.json").write_text(
        json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def main():
    receipt = dict(schema="cmpct-j24g82-prefix-crashcut-v1",
                   scope="single-owner sequential; simulated torn writes; research only",
                   product_credit=0, status="STARTED",
                   host=platform.platform(), source=attest())
    save(receipt)
    try:
        with tempfile.TemporaryDirectory(prefix="cmpct-j24g82-") as tmp:
            run_case(Path(tmp), receipt)
    except BaseException as exc:
        receipt["status"] = "FAIL"
        receipt["error"] = repr(exc)
        receipt["traceback"] = traceback.format_exc()
        save(receipt)
        raise
    print(json.dumps({k: receipt[k] for k in
                      ("status", "decision", "checked_cases_per_variant",
                       "physical_exact_prefix_parity_64_of_64")}, sort_keys=True))


if __name__ == "__main__":
    main()
