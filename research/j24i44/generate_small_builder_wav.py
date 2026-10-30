#!/usr/bin/env python3
"""J24I44: genuine Builder admission for small PCM16 WAV; never force a codec.

The generated sources contain no private material. This is a matched-input,
source-controlled research workload, not a published release benchmark.
"""
import argparse
import hashlib
import json
import wave
from pathlib import Path

import numpy as np
from cmpct.builder import Builder
from cmpct.reader import CMPCT

PCM_KIB = (64, 256, 1024, 2048, 4096, 8192)
SEED = 24144


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_pcm16(path: Path, pcm_kib: int) -> None:
    rng = np.random.default_rng(SEED)
    remaining = pcm_kib * 1024 // 2
    previous = 0
    with wave.open(str(path), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(44100)
        while remaining:
            take = min(65536, remaining)
            steps = rng.integers(-64, 65, size=take, dtype=np.int16).astype(np.int32)
            sums = np.cumsum(steps, dtype=np.int64)
            samples = ((sums + previous) & 65535).astype("<u2").view("<i2")
            out.writeframesraw(samples.tobytes())
            previous = (previous + int(sums[-1])) & 65535
            remaining -= take


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.output
    root.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema": "j24i44-small-builder-direct-wav-v1",
        "seed": SEED,
        "pcm_kib": list(PCM_KIB),
        "selection_unmodified": True,
        "records": {},
    }
    selected = 0
    for kib in PCM_KIB:
        tree = root / f"source-{kib}k"
        tree.mkdir(exist_ok=True)
        source = tree / "capture.wav"
        write_pcm16(source, kib)
        original = source.read_bytes()
        assert len(original) == kib * 1024 + 44
        archive = root / f"builder-wav-{kib}k.cmpct"
        details = Builder(tree, workers=1, reproducible=True).build(archive)
        physical = archive.read_bytes()
        with CMPCT(archive) as ar:
            assert len(ar.files) == 1, "expected one original file"
            row = ar.by["capture.wav"]
            assert row[4] == len(original), "logical size mismatch"
            assert ar.read_range("capture.wav", 0, len(original)) == original
            assert ar.verify() == 1
            is_direct = (row[6] == [0, 0] and len(ar.blobs) == 1)
            codec = int(ar.blobs[0][3]) if is_direct else None
        chosen = is_direct and codec == 2
        selected += int(chosen)
        manifest["records"][str(kib)] = {
            "pcm_kib": kib,
            "logical_bytes": len(original),
            "logical_sha256": digest(original),
            "archive_bytes": len(physical),
            "archive_sha256": digest(physical),
            "direct": is_direct,
            "codec": codec,
            "selected_flac": chosen,
            "builder_summary": details,
        }
        print("J24I44_ADMISSION", kib, "codec", codec, "flac", chosen, flush=True)
    (root / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    print("J24I44_ADMISSION_TOTAL", selected, "/", len(PCM_KIB))
    assert selected > 0, "NO_SELECTED_CODEC2: do not force codec or fake a crossover"


if __name__ == "__main__":
    main()
