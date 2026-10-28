#!/usr/bin/env python3
"""J24B03-H3: exact-source RAW physical control-bit differential; original H untouched."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

from cmpct.codec import BHDR, CODEC_RAW, K_FILE, K_SYMLINK
from cmpct.reader import CMPCT
from cmpct.validation import preflight_archive
from j24b03_direct_blob_size_court import PAYLOAD, wire

KINDS = ((K_FILE, "file", "direct.bin"), (K_SYMLINK, "symlink", "link"))
FAULTS = (("flags-1", 2, 1), ("flags-128", 2, 128),
          ("reserved-1", 3, 1), ("reserved-65535", 3, 65535))
START, LENGTH = 7, 8


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def observation(fn):
    try:
        value = fn()
    except Exception as exc:
        return {"status": "REJECT", "error_type": type(exc).__name__}
    if isinstance(value, bytes):
        return {"status": "ACCEPT", "hex": value.hex(),
                "length": len(value), "sha256": digest(value)}
    return {"status": "ACCEPT"}


def generate(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    manifest = {"experiment": "J24B03-H3", "format": 24,
                "expected_selected_hex": PAYLOAD[START:START + LENGTH].hex(),
                "expected_payload_sha256": digest(PAYLOAD),
                "controls": [], "hostiles": []}
    for kind, label, member in KINDS:
        good, _, frame = wire(kind, CODEC_RAW, len(PAYLOAD))
        off = good.find(frame)
        assert off >= 0 and good.count(frame) == 1
        assert frame[BHDR.size:] == PAYLOAD
        base = f"valid-{label}.cmpct"
        (root / base).write_bytes(good)
        manifest["controls"].append({"kind": label, "member": member, "file": base,
                                      "sha256": digest(good), "offset": off})
        original = list(BHDR.unpack_from(frame))
        assert original[2] == original[3] == 0
        for fault, field, value in FAULTS:
            altered = list(original)
            altered[field] = value
            header = BHDR.pack(*altered)
            assert len(header) == BHDR.size and header != frame[:BHDR.size]
            image = good[:off] + header + good[off + BHDR.size:]
            assert len(image) == len(good)
            filename = f"bad-{label}-{fault}.cmpct"
            (root / filename).write_bytes(image)
            manifest["hostiles"].append({"kind": label, "member": member, "file": filename,
                                         "sha256": digest(image), "good_sha256": digest(good),
                                         "offset": off, "fault": fault, "field": field,
                                         "value": value})
    assert len(manifest["controls"]) == 2 and len(manifest["hostiles"]) == 8
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def run(root: Path, arm: str, result_path: Path):
    import cmpct.reader as reader_module
    raw_manifest = (root / "manifest.json").read_bytes()
    manifest = json.loads(raw_manifest)
    assert manifest["experiment"] == "J24B03-H3"
    records = {"experiment": "J24B03-H3", "arm": arm,
               "reader_file": str(Path(reader_module.__file__).resolve()),
               "reader_sha256": digest(Path(reader_module.__file__).read_bytes()),
               "manifest_sha256": digest(raw_manifest), "controls": [], "hostiles": []}
    for category in ("controls", "hostiles"):
        for spec in manifest[category]:
            path = root / spec["file"]
            assert digest(path.read_bytes()) == spec["sha256"]
            preflight = observation(lambda: preflight_archive(path))
            try:
                with CMPCT(path) as reader:
                    selected = observation(lambda: reader.read_range(spec["member"], START, LENGTH))
                    whole = observation(lambda: reader.read(spec["member"]))
                    verified = observation(lambda: reader.verify())
            except Exception as exc:
                error = {"status": "REJECT", "error_type": type(exc).__name__}
                selected = whole = verified = error
            records[category].append({
                "kind": spec["kind"], "file": spec["file"], "fault": spec.get("fault"),
                "sha256": spec["sha256"], "preflight": preflight, "selected": selected,
                "whole": whole, "verified": verified})
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps(records, indent=2, sort_keys=True) + "\n")
    # All records are persisted before verdict assertions, including a failing candidate.
    for row in records["controls"]:
        assert row["preflight"]["status"] == "ACCEPT", row
        assert row["selected"].get("hex") == manifest["expected_selected_hex"], row
        assert row["whole"].get("sha256") == manifest["expected_payload_sha256"], row
        assert row["verified"]["status"] == "ACCEPT", row
    for row in records["hostiles"]:
        assert row["preflight"]["status"] == "REJECT", row
        if arm == "candidate":
            assert row["selected"]["status"] == "REJECT", ("bad selected", row)
            assert row["whole"]["status"] == "REJECT", ("bad whole", row)
            assert row["verified"]["status"] == "REJECT", ("bad verify", row)
    print(json.dumps({"arm": arm, "controls": len(records["controls"]),
                      "hostiles": len(records["hostiles"]),
                      "selected_accepted": sum(v["selected"]["status"] == "ACCEPT"
                                               for v in records["hostiles"]),
                      "whole_accepted": sum(v["whole"]["status"] == "ACCEPT"
                                            for v in records["hostiles"])}, sort_keys=True))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--generate", action="store_true")
    g.add_argument("--arm", choices=("baseline", "candidate"))
    p.add_argument("--corpus", type=Path, required=True)
    p.add_argument("--receipt", type=Path)
    a = p.parse_args()
    if a.generate:
        generate(a.corpus)
    else:
        if a.receipt is None:
            p.error("--receipt required for --arm")
        run(a.corpus, a.arm, a.receipt)
