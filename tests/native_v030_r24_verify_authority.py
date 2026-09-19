from __future__ import annotations

"""Adversarial receipt for revision-24 complete verification in the shared native surface."""

import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile

from cmpct import codec
from cmpct.builder import Builder
from cmpct.reader import CMPCT


def _incompressible_bytes(blocks: int = 4096) -> bytes:
    return b"".join(hashlib.sha256(i.to_bytes(8, "little")).digest() for i in range(blocks))


def run(binary: Path) -> None:
    binary = Path(binary)
    if not binary.is_file():
        raise RuntimeError(f"native portable binary missing: {binary}")
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-native-r24-") as td:
        root = Path(td)
        source = root / "source"
        source.mkdir()
        payload = _incompressible_bytes()
        (source / "payload.bin").write_bytes(payload)
        archive = root / "clean.cmpct"
        Builder(source).build(archive)

        clean = subprocess.run([str(binary), "verify", str(archive)], capture_output=True, text=True)
        if clean.returncode != 0:
            raise RuntimeError(f"native verifier rejected clean r24 archive: {clean.stderr}")

        corrupted = root / "corrupted.cmpct"
        shutil.copyfile(archive, corrupted)
        with CMPCT(corrupted) as reader:
            row = reader.by["payload.bin"]
            storage = row[6]
            if storage[0] != codec.S_BLOB:
                raise RuntimeError(f"adversarial fixture did not produce direct storage: {storage!r}")
            blob_index = int(storage[1])
            offset, usize, csize, blob_codec, meta_len = reader.blobs[blob_index]
            if blob_codec != codec.CODEC_RAW or usize != len(payload) or csize != len(payload):
                raise RuntimeError(
                    f"adversarial fixture did not produce a direct RAW blob: codec={blob_codec} usize={usize} csize={csize}"
                )
            payload_offset = reader.record_base + offset + codec.BHDR.size + meta_len

        with corrupted.open("r+b") as stream:
            stream.seek(payload_offset + len(payload) // 2)
            original = stream.read(1)
            if len(original) != 1:
                raise RuntimeError("failed to locate adversarial RAW payload byte")
            stream.seek(-1, 1)
            stream.write(bytes([original[0] ^ 0x5A]))

        bad = subprocess.run([str(binary), "verify", str(corrupted)], capture_output=True, text=True)
        if bad.returncode == 0:
            raise RuntimeError(
                "native portable verify accepted a mutated direct RAW payload; touched-byte range success is not complete verification"
            )

        stats = subprocess.run(
            [str(binary), "member-stats", str(archive), "payload.bin"],
            capture_output=True,
            text=True,
        )
        if stats.returncode == 0:
            raise RuntimeError(
                "r24 native member-stats emitted a precise locality number even though cmpct-core does not expose operation-derived decoded context"
            )

        print("native-r24-strong-verify=PASS")
        print("native-r24-locality-unavailable=PASS")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, required=True)
    args = parser.parse_args()
    run(args.binary)

# Footnote: this deliberately mutates payload bytes while leaving framing/index metadata untouched. The older
# portable verifier only performed a full RAW range read and therefore returned success. The release contract
# requires the native core to authenticate complete logical identity instead of inferring verification from read
# success. r24 locality remains inherited evidence until cmpct-core exposes truthful touched/decoded accounting.
