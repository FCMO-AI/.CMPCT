#!/usr/bin/env python3
"""O204: actual CMPCT CLI/Reader without optional NumPy or SoundFile.

Source-exact comparison against historical v0.31 codec blob, not a mocked function.
See docs/v031-research/2026-10-26-o204-audio-optional-prereg.md.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
import struct
import subprocess
import sys
import tempfile
import traceback
import wave

BASE_COMMIT = "4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b"
BASE_CODEC_BLOB = "29526db4203723d83523fc95d074c346b63d7587"
CAND_CODEC_BLOB = "6e116ee1fc348b78d81a541fcaf5cf3d6912d3c4"
ROOT = Path(__file__).resolve().parents[1]


def blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def command(argv: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, check=False)


def expected_success(run: subprocess.CompletedProcess[bytes], case: str) -> bytes:
    if run.returncode:
        raise AssertionError(f"{case}: rc={run.returncode}; stderr={run.stderr.decode(errors='replace')[-2400:]}")
    return run.stdout


def make_wav(bits: int, channels: int = 1, frames: int = 271) -> bytes:
    from io import BytesIO
    out = BytesIO()
    width = bits // 8
    with wave.open(out, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(width)
        wf.setframerate(22050)
        if bits == 8:
            payload = bytes((i * 37 + 19) % 256 for i in range(frames * channels))
        elif bits == 16:
            payload = b"".join(struct.pack("<h", (i * 503) % 65536 - 32768)
                               for i in range(frames * channels))
        else:
            payload = b"".join(struct.pack("<i", (i * 1234567) % (1 << 32) - (1 << 31))
                               for i in range(frames * channels))
        wf.writeframes(payload)
    return out.getvalue()


def cli(py: str, source: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(source)
    env.pop("PYTHONHOME", None)
    return command([py, "-m", "cmpct", *map(str, args)], env)


def assert_archive(py: str, package: Path, source_bytes: dict[str, bytes],
                   corpus: Path, archive: Path) -> dict:
    out = expected_success(
        cli(py, package, "create", str(corpus), str(archive), "--workers", "1", "--reproducible"),
        "create")
    assert archive.is_file() and archive.stat().st_size > 0
    info = json.loads(expected_success(cli(py, package, "info", str(archive)), "info"))
    assert info["version"] == 24, info
    verify = expected_success(cli(py, package, "verify", str(archive)), "verify").decode().strip()
    expected_success(cli(py, package, "preflight", str(archive)), "preflight")
    hashes = {}
    for name, expected in source_bytes.items():
        data = expected_success(cli(py, package, "cat", str(archive), name), "cat " + name)
        assert hashlib.sha256(data).digest() == hashlib.sha256(expected).digest(), name
        assert data == expected, name
        start = min(len(data), 3)
        length = min(len(data) - start, 17)
        got = expected_success(
            cli(py, package, "range", str(archive), name, str(start), str(length)),
            "range " + name)
        assert got == expected[start:start + length], name
        hashes[name] = hashlib.sha256(data).hexdigest()
    return {"archive_bytes": archive.stat().st_size,
            "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
            "logical_sha256": hashes, "verify": verify,
            "create_summary": json.loads(out)}


def execute(py: str) -> dict:
    if importlib.util.find_spec("numpy") is not None:
        raise AssertionError("Not a minimal runtime: numpy is importable")
    if importlib.util.find_spec("soundfile") is not None:
        raise AssertionError("Not a minimal runtime: soundfile is importable")
    candidate_codec = (ROOT / "src/cmpct/codec.py").read_bytes()
    assert blob_sha(candidate_codec) == CAND_CODEC_BLOB, "candidate codec source changed"
    base_codec = expected_success(
        command(["git", "show", BASE_COMMIT + ":src/cmpct/codec.py"]), "git-show-base-codec")
    assert blob_sha(base_codec) == BASE_CODEC_BLOB, "historical codec source changed"

    head = expected_success(command(["git", "rev-parse", "HEAD"]), "head").decode().strip()
    freeze = expected_success(command([py, "-m", "pip", "freeze"]), "pip freeze").decode()
    result = {"schema": "cmpct-o204-installed-minimal-audio-v1",
              "head": head, "base_commit": BASE_COMMIT,
              "base_codec_blob": blob_sha(base_codec),
              "candidate_codec_blob": blob_sha(candidate_codec),
              "runtime": sys.version, "platform": platform.platform(),
              "pip_freeze": freeze.splitlines(),
              "optional_modules_absent": ["numpy", "soundfile"]}

    with tempfile.TemporaryDirectory(prefix="cmpct-o204-") as temp:
        t = Path(temp)
        candidate = t / "candidate"
        baseline = t / "historical"
        for dst in (candidate, baseline):
            shutil.copytree(ROOT / "src/cmpct", dst / "cmpct")
        (baseline / "cmpct/codec.py").write_bytes(base_codec)

        corpus = t / "mixed"
        corpus.mkdir()
        expected = {
            "pcm16.wav": make_wav(16, 2),
            "pcm32.wav": make_wav(32),
            "pcm8.wav": make_wav(8),
            "invalid.wav": b"RIFF\x0c\x00\x00\x00WAVEmalformed-payload",
            "ordinary.bin": bytes(range(256)) * 11,
        }
        for name, payload in expected.items():
            (corpus / name).write_bytes(payload)

        plain = t / "plain"
        plain.mkdir()
        (plain / "ordinary.bin").write_bytes(expected["ordinary.bin"])
        plain_expect = {"ordinary.bin": expected["ordinary.bin"]}
        control_old = assert_archive(py, baseline, plain_expect, plain, t / "base-plain.cmpct")
        control_new = assert_archive(py, candidate, plain_expect, plain, t / "candidate-plain.cmpct")
        assert control_old["archive_sha256"] == control_new["archive_sha256"], "plain archive changed"
        result["ordinary_control"] = {
            "archive_bytes": control_old["archive_bytes"],
            "byte_identical": True, "sha256": control_old["archive_sha256"]}

        historical = cli(py, baseline, "create", str(corpus), str(t / "historical.cmpct"),
                         "--workers", "1", "--reproducible")
        stderr = historical.stderr.decode(errors="replace")
        result["historical_mixed"] = {
            "returncode": historical.returncode, "error_tail": stderr[-1500:]}
        if historical.returncode == 0 or not (
            "ModuleNotFoundError" in stderr and
            ("No module named 'numpy'" in stderr or "No module named 'soundfile'" in stderr)
        ):
            raise AssertionError("Historical control did not fail specifically on missing optional audio")

        result["candidate_mixed"] = assert_archive(
            py, candidate, expected, corpus, t / "candidate.cmpct")
        for name in ("pcm16.wav", "pcm32.wav", "pcm8.wav"):
            probe = command([py, "-c",
                "from cmpct.codec import wavflac_compress; import pathlib,sys; "
                "assert wavflac_compress(pathlib.Path(sys.argv[1]).read_bytes()) is None",
                str(corpus / name)], env={**os.environ, "PYTHONPATH": str(candidate)})
            expected_success(probe, "fallback-probe " + name)
        result["direct_fallback_cases"] = ["pcm16.wav", "pcm32.wav", "pcm8.wav"]
    result["decision"] = "CANDIDATE_PASS_HISTORICAL_MISSING_AUDIO_FAIL"
    return result


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--result", type=Path, required=True)
    args = p.parse_args()
    report = {}
    try:
        report = execute(sys.executable)
        success = True
    except Exception as exc:
        report = {"schema": "cmpct-o204-installed-minimal-audio-v1",
                  "decision": "FAIL_OR_AMBIGUOUS",
                  "error": repr(exc), "traceback": traceback.format_exc(),
                  "python": sys.version, "platform": platform.platform()}
        success = False
    args.result.parent.mkdir(parents=True, exist_ok=True)
    args.result.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
