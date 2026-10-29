#!/usr/bin/env python3
"""J24I41: independently hosted, same-source WAV capability admission court.

Research-only. The candidate codec belongs to existing PR #225; this file never
rewrites encoder policy. Its output is not release/benchmark evidence.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

import numpy as np

CASES = (
    "pcm16_mono", "pcm16_stereo", "pcm16_stereo_suffix",
    "pcm32_stereo", "pcm24_mono", "pcm8_mono",
    "pcm16_zero", "pcm16_partial", "pcm16_9ch", "pcm16_highrate",
)
CONTROL = ("pcm16_mono", "pcm16_stereo", "pcm16_stereo_suffix")
FALLBACK = set(CASES) - set(CONTROL)
SEED = 24141


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def wav(pcm: bytes, *, channels: int, rate: int, bits: int, suffix: bytes = b"") -> bytes:
    width = bits // 8
    align = channels * width
    fmt = struct.pack("<HHIIHH", 1, channels, rate, rate * align, align, bits)
    body = b"fmt " + struct.pack("<I", len(fmt)) + fmt
    body += b"data" + struct.pack("<I", len(pcm)) + pcm
    # A deliberately malformed partial frame can still have a valid RIFF envelope.
    body += suffix
    return b"RIFF" + struct.pack("<I", len(body) + 4) + b"WAVE" + body


def steps(nframes: int, channels: int, bits: int, seed: int) -> bytes:
    rng = np.random.default_rng(seed)
    draws = rng.integers(-64, 65, size=nframes * channels, dtype=np.int16).astype(np.int32)
    accum = np.cumsum(draws, dtype=np.int64)
    if bits == 16:
        return (accum & 0xffff).astype("<u2").tobytes()
    if bits == 32:
        return (accum & 0xffffffff).astype("<u4").tobytes()
    raise ValueError(bits)


def prepare(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    data = {}
    for case in CASES:
        if case.startswith("pcm16"):
            ch = 9 if case == "pcm16_9ch" else (2 if "stereo" in case else 1)
            rate = 655351 if case == "pcm16_highrate" else 44100
            frame_count = 0 if case == "pcm16_zero" else max(1, (512 * 1024) // (ch * 2))
            pcm = steps(frame_count, ch, 16, SEED + len(case))
            if case == "pcm16_partial":
                pcm += b"\x81"
            tail = (b"LIST" + struct.pack("<I", 8) + b"J24I41!!") if case == "pcm16_stereo_suffix" else b""
            raw = wav(pcm, channels=ch, rate=rate, bits=16, suffix=tail)
        elif case == "pcm32_stereo":
            raw = wav(steps(65536, 2, 32, SEED), channels=2, rate=44100, bits=32)
        elif case == "pcm24_mono":
            rng = np.random.default_rng(SEED)
            pcm = rng.integers(0, 256, size=((512*1024)//3)*3, dtype=np.uint8).tobytes()
            raw = wav(pcm, channels=1, rate=44100, bits=24)
        elif case == "pcm8_mono":
            rng = np.random.default_rng(SEED)
            pcm = rng.integers(0, 256, size=512*1024, dtype=np.uint8).tobytes()
            raw = wav(pcm, channels=1, rate=44100, bits=8)
        else:
            raise AssertionError(case)
        target = root / case
        target.mkdir(exist_ok=True)
        (target / "capture.wav").write_bytes(raw)
        data[case] = {"sha256": digest(raw), "bytes": len(raw)}
    (root / "fixtures.json").write_text(json.dumps({"schema":"j24i41-fixtures-v1","seed":SEED,"cases":data}, sort_keys=True,indent=2) + "\n")


def evaluate(root: Path, out: Path, side: str) -> None:
    # Import from the explicitly pinned PYTHONPATH worktree, never from a
    # cached installed interpreter's implicit working-directory package.
    import cmpct
    from cmpct.builder import Builder
    from cmpct.reader import CMPCT
    from cmpct import codec
    import soundfile as sf
    import unittest.mock as mock
    import types

    expected_source = Path(__import__("os").environ["J24I41_SOURCE_ROOT"]).resolve()
    actual_source = Path(codec.__file__).resolve()
    assert expected_source in actual_source.parents, (expected_source, actual_source)
    files = json.loads((root / "fixtures.json").read_text())
    assert files["schema"] == "j24i41-fixtures-v1"
    out.mkdir(parents=True, exist_ok=True)
    selected = CONTROL if side == "control" else CASES
    records = {}
    for name in selected:
        tree = root / name
        raw = (tree / "capture.wav").read_bytes()
        assert digest(raw) == files["cases"][name]["sha256"]
        archive = out / (name + ".cmpct")
        Builder(tree, workers=1, reproducible=True).build(archive)
        with CMPCT(archive) as ar:
            assert list(ar.by) == ["capture.wav"], (name, ar.by)
            assert ar.verify() == 1, name
            got = ar.read_range("capture.wav", 0, len(raw))
            assert got == raw, "lossy or incomplete reconstructed data: " + name
            assert ar.by["capture.wav"][4] == len(raw)
            codecs = sorted(set(int(row[3]) for row in ar.blobs))
            if side == "candidate" and name in FALLBACK:
                assert 2 not in codecs, (name, codecs)
        complete = archive.read_bytes()
        records[name] = {
            "input_sha256": digest(raw), "input_bytes":len(raw),
            "archive_sha256":digest(complete),"archive_bytes":len(complete),
            "codecs":codecs, "verified":True, "exact":True
        }
    diag = {"libsndfile":str(sf.__libsndfile_version__), "soundfile":str(sf.__version__),
            "codec_source":str(actual_source), "python":sys.version.split()[0]}
    if side == "candidate":
        pcm = (root/"pcm16_mono"/"capture.wav").read_bytes()
        class FaultingBackend:
            @staticmethod
            def write(*args, **kwargs): raise ValueError("injected unsupported backend")
        with mock.patch.object(codec,"_audio_modules",return_value=(np,FaultingBackend)):
            assert codec.wavflac_compress(pcm) is None
        class OomBackend:
            @staticmethod
            def write(*args, **kwargs): raise MemoryError("injected real allocation failure")
        with mock.patch.object(codec,"_audio_modules",return_value=(np,OomBackend)):
            try: codec.wavflac_compress(pcm)
            except MemoryError: pass
            else: raise AssertionError("MemoryError must not be swallowed")
        for failure in (ImportError("missing optional audio"), OSError("unloadable optional audio")):
            with mock.patch.object(codec, "_audio_modules", side_effect=failure):
                assert codec.wavflac_compress(pcm) is None, type(failure).__name__
        diag["injected_backend_refusal"]="fallback"
        diag["injected_optional_import_error"]="fallback"
        diag["injected_MemoryError"]="propagated"
    else:
        pcm = (root/"pcm32_stereo"/"capture.wav").read_bytes()
        try:
            result = codec.wavflac_compress(pcm)
            diag["parent_pcm32_probe"] = "returned_none" if result is None else "encoded"
        except Exception as exc:
            diag["parent_pcm32_probe"] = "exception:" + type(exc).__name__
            diag["parent_pcm32_message"] = str(exc)[:160]
    output={"schema":"j24i41-admission-court-v1","side":side,"cases":records,"diagnostics":diag}
    (out / "result.json").write_text(json.dumps(output,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"side":side,"records":records,"diagnostics":diag},sort_keys=True))


def compare(parent: Path, candidate: Path, output: Path) -> None:
    a=json.loads((parent/"result.json").read_text())
    b=json.loads((candidate/"result.json").read_text())
    assert a["schema"] == b["schema"] == "j24i41-admission-court-v1"
    assert a["side"] == "control" and b["side"] == "candidate"
    for name in CONTROL:
        pa=a["cases"][name]; ca=b["cases"][name]
        assert pa["archive_sha256"] == ca["archive_sha256"], (
            "admitted PCM16 archive byte regression",name,pa,ca)
        assert pa["codecs"] == ca["codecs"], ("codec selection changed",name)
    assert all(b["cases"][name]["exact"] for name in CASES)
    result={"schema":"j24i41-decision-v1","decision":"PASS",
            "control_archive_identity":True,
            "candidate_exact_cases":len(CASES),
            "candidate_fallback_cases":len(FALLBACK),
            "candidate_codec2_admitted_cases":sum(2 in b["cases"][n]["codecs"] for n in CONTROL),
            "parent_pcm32_probe":a["diagnostics"]["parent_pcm32_probe"],
            "parent_libsndfile":a["diagnostics"]["libsndfile"],
            "candidate_libsndfile":b["diagnostics"]["libsndfile"]}
    output.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps(result,sort_keys=True))


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("mode",choices=["prepare","evaluate","compare"])
    p.add_argument("--root",type=Path)
    p.add_argument("--out",type=Path)
    p.add_argument("--side",choices=["candidate","control"])
    p.add_argument("--parent",type=Path)
    p.add_argument("--candidate",type=Path)
    a=p.parse_args()
    if a.mode=="prepare":prepare(a.root)
    elif a.mode=="evaluate":evaluate(a.root,a.out,a.side)
    else: compare(a.parent,a.candidate,a.out)
