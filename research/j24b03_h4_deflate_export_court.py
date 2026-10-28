#!/usr/bin/env python3
"""J24B03-H4: same signed r24 wires, direct-Deflate ZIP export header-custody A/B."""
from __future__ import annotations
import argparse
import hashlib
import json
import struct
import tempfile
import zipfile
from pathlib import Path

from cmpct.codec import BHDR, CODEC_DEFLATE, K_FILE, K_SYMLINK
from cmpct.reader import CMPCT
from cmpct.validation import preflight_archive
from j24b03_direct_blob_size_court import PAYLOAD, wire

KINDS = ((K_FILE, "regular", "direct.bin"), (K_SYMLINK, "symlink", "link"))
FAULTS = (("flags-1", 2, 1), ("flags-128", 2, 128),
          ("reserved-1", 3, 1), ("reserved-65535", 3, 65535))


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def observe(action):
    try:
        value = action()
        return {"status": "ACCEPT", "value": value}
    except Exception as exc:
        return {"status": "REJECT", "error": type(exc).__name__}


def build(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    manifest = {"experiment": "J24B03-H4", "control_source": "independent signed wire()",
                "payload_sha256": digest(PAYLOAD), "controls": [], "hostiles": []}
    for kind, label, member in KINDS:
        original, _, frame = wire(kind, CODEC_DEFLATE, len(PAYLOAD))
        offset = original.find(frame)
        assert offset >= 0 and original.count(frame) == 1
        header = list(BHDR.unpack_from(frame))
        assert header[2] == 0 and header[3] == 0
        assert header[1] == CODEC_DEFLATE
        original_name = f"good-{label}.cmpct"
        (root / original_name).write_bytes(original)
        manifest["controls"].append({"file": original_name, "member": member, "kind": label,
                                      "sha256": digest(original), "frame_offset": offset,
                                      "stream_sha256": digest(frame[BHDR.size:])})
        for fault, index, value in FAULTS:
            mutation = header.copy()
            mutation[index] = value
            image = original[:offset] + BHDR.pack(*mutation) + original[offset + BHDR.size:]
            assert len(image) == len(original)
            assert image[:offset] == original[:offset]
            assert image[offset + BHDR.size:] == original[offset + BHDR.size:]
            name = f"bad-{label}-{fault}.cmpct"
            (root / name).write_bytes(image)
            manifest["hostiles"].append({"file": name, "member": member, "kind": label,
                                         "fault": fault, "sha256": digest(image),
                                         "parent_sha256": digest(original), "frame_offset": offset})
        # Independent authenticated *index* contradiction, not a header-bit mutation.
        signed_mismatch, _, signed_frame = wire(kind, CODEC_DEFLATE, len(PAYLOAD) + 8)
        assert signed_frame == frame
        name = f"bad-{label}-signed-size-136.cmpct"
        (root / name).write_bytes(signed_mismatch)
        manifest["hostiles"].append({"file": name, "member": member, "kind": label,
                                     "fault": "signed-size-136", "sha256": digest(signed_mismatch),
                                     "parent_sha256": digest(original), "frame_offset": signed_mismatch.find(frame)})
    assert len(manifest["controls"]) == 2 and len(manifest["hostiles"]) == 10
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def export(reader: CMPCT, path: Path, member: str):
    reader.export_zip(path)
    data = path.read_bytes()
    with zipfile.ZipFile(path) as z:
        assert z.namelist() == [member], z.namelist()
        info = z.getinfo(member)
        logical = z.read(member)
        assert info.compress_type == zipfile.ZIP_DEFLATED
        pos = info.header_offset
        fields = struct.unpack_from("<IHHHHHIIIHH", data, pos)
        assert fields[0] == 0x04034B50
        stream_start = pos + 30 + fields[-2] + fields[-1]
        stream = data[stream_start:stream_start + info.compress_size]
    return {"zip_sha256": digest(data), "zip_bytes": len(data),
            "logical_sha256": digest(logical), "logical_bytes": len(logical),
            "stream_sha256": digest(stream), "stream_bytes": len(stream)}


def run(root: Path, arm: str, output: Path):
    import cmpct.reader as module
    manifest_bytes = (root / "manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    assert manifest["experiment"] == "J24B03-H4"
    receipt = {"experiment": "J24B03-H4", "arm": arm,
               "reader_sha256": digest(Path(module.__file__).read_bytes()),
               "reader_file": str(Path(module.__file__).resolve()),
               "manifest_sha256": digest(manifest_bytes), "controls": [], "hostiles": []}
    for category in ("controls", "hostiles"):
        for spec in manifest[category]:
            source = root / spec["file"]
            assert digest(source.read_bytes()) == spec["sha256"]
            p = observe(lambda: preflight_archive(source))
            with tempfile.TemporaryDirectory(prefix="cmpct-h4-export-") as td:
                try:
                    with CMPCT(source) as reader:
                        full = observe(lambda: reader.read(spec["member"]))
                        verify = observe(lambda: reader.verify())
                        zip_result = observe(lambda: export(reader, Path(td) / "out.zip", spec["member"]))
                except Exception as exc:
                    error = {"status": "REJECT", "error": type(exc).__name__}
                    full = verify = zip_result = error
            result = {"file": spec["file"], "kind": spec["kind"], "member": spec["member"],
                      "fault": spec.get("fault"), "sha256": spec["sha256"],
                      "preflight": p["status"], "read": full["status"],
                      "verify": verify["status"], "export": zip_result["status"],
                      "zip": zip_result.get("value")}
            receipt[category].append(result)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    for row in receipt["controls"]:
        assert (row["preflight"], row["read"], row["verify"], row["export"]) == ("ACCEPT",) * 4, row
        assert row["zip"]["logical_sha256"] == manifest["payload_sha256"], row
        spec = next(s for s in manifest["controls"] if s["file"] == row["file"])
        assert row["zip"]["stream_sha256"] == spec["stream_sha256"], row
    for row in receipt["hostiles"]:
        assert row["preflight"] == "REJECT", row
        if arm == "candidate":
            assert row["export"] == "REJECT", row
        elif arm == "baseline":
            assert row["export"] == "ACCEPT", row
            assert row["zip"]["logical_sha256"] == manifest["payload_sha256"], row
    print(json.dumps({"arm": arm, "reader_sha256": receipt["reader_sha256"],
                      "valid": len(receipt["controls"]), "invalid": len(receipt["hostiles"]),
                      "invalid_exports_accepted": sum(r["export"] == "ACCEPT" for r in receipt["hostiles"])},
                     sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    option = parser.add_mutually_exclusive_group(required=True)
    option.add_argument("--generate", action="store_true")
    option.add_argument("--arm", choices=("baseline", "candidate"))
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    if args.generate:
        build(args.corpus)
    else:
        if args.receipt is None:
            parser.error("--receipt is required with --arm")
        run(args.corpus, args.arm, args.receipt)
