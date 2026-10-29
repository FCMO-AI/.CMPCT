#!/usr/bin/env python3
"""J24I38: authentic unmodified Builder WAV-FLAC admission. Scientific source generator."""
import argparse
import hashlib
import json
import wave
import zlib
from pathlib import Path

import numpy as np

from cmpct.builder import Builder
from cmpct.reader import CMPCT


def digest(b):
    return hashlib.sha256(b).hexdigest()


def generate_pcm(path, mib):
    # Bounded deterministic random walk; FLAC can model deltas while generic bytes compressors
    # cannot assume the signal's predictive structure. No post-hoc candidate tuning.
    nframes = (mib * 1024 * 1024) // 2
    rng = np.random.default_rng(24138)
    previous = 0
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(44100)
        remaining = nframes
        while remaining:
            take = min(1_048_576, remaining)
            steps = rng.integers(-64, 65, size=take, dtype=np.int16).astype(np.int32)
            sums = np.cumsum(steps, dtype=np.int64)
            pcm = ((sums + previous) & 65535).astype("<u2").view("<i2")
            w.writeframesraw(pcm.tobytes())
            previous = (previous + int(sums[-1])) & 65535
            remaining -= take


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema": "j24i38-builder-wav-flac-v1",
        "base_sha": "2d0dd4031b8c0fb2c42b715b6a4569199a2309a3",
        "seed": 24138,
        "pcm_format": "RIFF/WAVE PCM16 mono 44100 Hz random-walk steps [-64,64]",
        "records": {},
    }
    for mib in (8, 32):
        tree = a.output / ("source-%dm" % mib)
        tree.mkdir(exist_ok=True)
        source = tree / "capture.wav"
        generate_pcm(source, mib)
        raw = source.read_bytes()
        # The standard wave writer adds a 44-byte canonical RIFF header.
        assert len(raw) == mib * 1024 * 1024 + 44
        archive = a.output / ("builder-wav-%dm.cmpct" % mib)
        details = Builder(tree, workers=1, reproducible=True).build(archive)
        with CMPCT(archive) as ar:
            assert len(ar.files) == 1 and len(ar.blobs) == 1, "unexpected Builder layout"
            row = ar.by["capture.wav"]
            assert row[1] == 0 and row[4] == len(raw)
            assert row[6] == [0, 0], "Builder did not admit direct blob"
            assert ar.blobs[0][3] == 2, (
                "REAL ADMISSION NEGATIVE: Builder chose codec %r instead of WAV-FLAC"
                % (ar.blobs[0][3],)
            )
            assert ar.read_range("capture.wav", 0, 64) == raw[:64]
            assert ar.verify() == 1
            encoded_bytes = ar.blobs[0][2]
        physical = archive.read_bytes()
        manifest["records"][str(mib)] = {
            "logical_bytes": len(raw),
            "source_sha256": digest(raw),
            "payload_sha256": digest(raw),
            "archive_sha256": digest(physical),
            "archive_bytes": len(physical),
            "encoded_bytes": encoded_bytes,
            "crc32": zlib.crc32(raw) & 0xffffffff,
            "builder_summary": details,
            "codec": 2,
        }
    (a.output / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"schema": manifest["schema"], "records": {
        k: {x: y for x, y in v.items() if x != "builder_summary"}
        for k, v in manifest["records"].items()
    }}, sort_keys=True))


if __name__ == "__main__":
    main()
