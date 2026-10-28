#!/usr/bin/env python3
"""J24B03-H2: source-exact BHDR offset diagnostic, separate from frozen H negative.

Generate the corpus exactly once, run original and candidate separately, record
all observations before checking acceptance. Never modify J24B03-H's assertions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from cmpct.codec import BHDR, BMAGIC, CODEC_RAW, CODEC_ZSTD, K_FILE, K_SYMLINK
from cmpct.reader import CMPCT
from cmpct.validation import preflight_archive
from j24b03_direct_blob_size_court import PAYLOAD, wire

FAULTS = ("magic", "codec", "usize", "csize", "mlen")
KINDS = ((K_FILE, "file", "direct.bin"), (K_SYMLINK, "symlink", "link"))
START, LENGTH = 7, 8


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def observe(fn):
    try:
        result = fn()
    except Exception as exc:
        return {"status": "REJECT", "error_type": type(exc).__name__}
    if isinstance(result, bytes):
        return {"status": "ACCEPT", "length": len(result),
                "hex": result.hex(), "sha256": sha(result)}
    return {"status": "ACCEPT"}


def generate(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    manifest = {"experiment": "J24B03-H2", "format": 24,
                "expected_normal_hex": PAYLOAD[START:START + LENGTH].hex(),
                "predicted_shift_hex": PAYLOAD[START + 1:START + 1 + LENGTH].hex(),
                "controls": [], "faults": []}
    for kind, kind_label, member in KINDS:
        good, _, frame = wire(kind, CODEC_RAW, len(PAYLOAD))
        offset = good.find(frame)
        assert offset >= 0 and good.count(frame) == 1
        assert frame[BHDR.size:] == PAYLOAD
        good_filename = f"valid-{kind_label}.cmpct"
        (root / good_filename).write_bytes(good)
        manifest["controls"].append({"kind": kind_label, "name": member,
                                      "file": good_filename, "sha256": sha(good),
                                      "frame_offset": offset})
        header = list(BHDR.unpack_from(frame))
        for fault in FAULTS:
            altered = list(header)
            if fault == "magic":
                altered[0] = bytes((BMAGIC[0] ^ 1,)) + BMAGIC[1:]
            elif fault == "codec":
                altered[1] = CODEC_ZSTD
            elif fault == "usize":
                altered[4] = len(PAYLOAD) + 1
            elif fault == "csize":
                altered[5] = len(PAYLOAD) - 1
            else:
                altered[6] = 1
            new_header = BHDR.pack(*altered)
            assert new_header != frame[:BHDR.size]
            bad = good[:offset] + new_header + good[offset + BHDR.size:]
            assert bad[:offset] == good[:offset]
            assert bad[offset + BHDR.size:] == good[offset + BHDR.size:]
            filename = f"bad-{kind_label}-{fault}.cmpct"
            (root / filename).write_bytes(bad)
            manifest["faults"].append({
                "kind": kind_label, "name": member, "fault": fault, "file": filename,
                "sha256": sha(bad), "good_sha256": sha(good),
                "frame_offset": offset,
                "previous_header_hex": frame[:BHDR.size].hex(),
                "altered_header_hex": new_header.hex()
            })
    assert len(manifest["controls"]) == 2 and len(manifest["faults"]) == 10
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"generated": 12, "faults": 10, "manifest_sha256":
                      sha((root / "manifest.json").read_bytes())}, sort_keys=True))


def investigate(root: Path, arm: str, receipt_path: Path):
    import cmpct.reader as reader_module
    manifest_bytes = (root / "manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    assert manifest["experiment"] == "J24B03-H2"
    observations = {"experiment": "J24B03-H2", "arm": arm,
                    "manifest_sha256": sha(manifest_bytes),
                    "reader_file": str(Path(reader_module.__file__).resolve()),
                    "reader_sha256": sha(Path(reader_module.__file__).read_bytes()),
                    "valid": [], "faults": []}
    for category, key in (("controls", "valid"), ("faults", "faults")):
        for entry in manifest[category]:
            path = root / entry["file"]
            image = path.read_bytes()
            assert sha(image) == entry["sha256"]
            preflight = observe(lambda: preflight_archive(path))
            try:
                with CMPCT(path) as reader:
                    selected = observe(lambda: reader.read_range(entry["name"], START, LENGTH))
                    if key == "valid":
                        whole = observe(lambda: reader.read(entry["name"]))
                        verification = observe(lambda: reader.verify())
                    else:
                        whole = verification = None
            except Exception as exc:
                selected = {"status": "REJECT", "error_type": type(exc).__name__}
                whole = verification = None
            record = {k: entry[k] for k in ("kind", "name", "file", "sha256")}
            if key == "faults":
                record["fault"] = entry["fault"]
            record.update({"preflight": preflight, "selected": selected})
            if key == "valid":
                record["whole"] = whole
                record["verification"] = verification
            observations[key].append(record)

    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(observations, indent=2, sort_keys=True) + "\n")
    # Persist every observation *before* asserting anything; failures remain evidence.
    correct = manifest["expected_normal_hex"]
    for r in observations["valid"]:
        assert r["preflight"]["status"] == "ACCEPT", r
        assert r["selected"].get("hex") == correct, r
        assert r["whole"].get("sha256") == sha(PAYLOAD), r
        assert r["verification"]["status"] == "ACCEPT", r
    for r in observations["faults"]:
        assert r["preflight"]["status"] == "REJECT", r
        if arm == "candidate":
            assert r["selected"]["status"] == "REJECT", ("unrejected hostile BHDR", r)
    print(json.dumps({"arm": arm, "valid": len(observations["valid"]),
                      "hostile": len(observations["faults"]),
                      "baseline_accepted": sum(r["selected"]["status"] == "ACCEPT"
                                               for r in observations["faults"]),
                      "candidate_rejected": sum(r["selected"]["status"] == "REJECT"
                                                for r in observations["faults"])},
                     sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--generate", action="store_true")
    group.add_argument("--arm", choices=("baseline", "candidate"))
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    if args.generate:
        generate(args.corpus)
    else:
        if args.receipt is None:
            parser.error("--receipt required for --arm")
        investigate(args.corpus, args.arm, args.receipt)
