#!/usr/bin/env python3
"""O206: exact-source installed-package positive WAVFLAC/optional-extras court.

Research-only; no Reader/Builder/codec modifications, no changes to frozen vectors.
Prereg: docs/v031-research/2026-10-26-o206-wavflac-extras-prereg.md
"""
from __future__ import annotations

import base64
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import random
import shutil
import struct
import subprocess
import sys
import tempfile
import traceback
import wave
from io import BytesIO

ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b"
BASE_CODEC_BLOB = "29526db4203723d83523fc95d074c346b63d7587"
CAND_CODEC_BLOB = "6e116ee1fc348b78d81a541fcaf5cf3d6912d3c4"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def git_blob(b: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest()


def command(argv: list[str], *, source: Path | None = None) -> subprocess.CompletedProcess[bytes]:
    env = dict(os.environ)
    if source is not None:
        env["PYTHONPATH"] = str(source)
        env.pop("PYTHONHOME", None)
    return subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, check=False)


def ok(run: subprocess.CompletedProcess[bytes], title: str) -> bytes:
    if run.returncode:
        raise AssertionError(
            f"{title}: returncode={run.returncode}, stderr={run.stderr.decode(errors='replace')[-1600:]}"
        )
    return run.stdout


def make_wav(*, channels: int, frames: int, seed: int, bits: int = 16) -> bytes:
    rng = random.Random(seed)
    width = bits // 8
    pcm = bytearray()
    for i in range(frames * channels):
        if bits == 16:
            # Unequal channel/sample observations, mixed predictability, always aligned.
            val = ((i * (93 + seed) + (i // 37) * 4093 + rng.randrange(-500, 501)) % 65536) - 32768
            pcm.extend(struct.pack("<h", val))
        elif bits == 32:
            val = (i * 1234567 + rng.randrange(0, 65536)) % (1 << 32) - (1 << 31)
            pcm.extend(struct.pack("<i", val))
        else:
            raise ValueError(bits)
    out = BytesIO()
    with wave.open(out, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(width)
        wf.setframerate(22050)
        wf.writeframes(bytes(pcm))
    return out.getvalue()


def codec_trial(py: str, source: Path, wav_path: Path) -> dict:
    # The subprocess loads the authentic codec from each separate source tree.
    code = (
        "import hashlib,json,sys,pathlib;"
        "from cmpct.codec import wavflac_compress,wavflac_decompress;"
        "raw=pathlib.Path(sys.argv[1]).read_bytes();"
        "v=wavflac_compress(raw);"
        "assert v is not None,'eligible PCM16 must produce FLAC with installed extras';"
        "data,meta=v;"
        "out=wavflac_decompress(data,meta);"
        "assert out==raw,'WAVFLAC exact round trip failed';"
        "print(json.dumps({'flac_bytes':len(data),'flac_sha256':hashlib.sha256(data).hexdigest(),"
        "'meta_sha256':hashlib.sha256(meta).hexdigest(),"
        "'decoded_sha256':hashlib.sha256(out).hexdigest(),"
        "'prefix':data[:4].hex()}))"
    )
    res = ok(command([py, "-c", code, str(wav_path)], source=source), "supported codec trial")
    return json.loads(res.decode())


def codec_reject(py: str, source: Path, wav_path: Path) -> None:
    code = (
        "import pathlib,sys;"
        "from cmpct.codec import wavflac_compress;"
        "assert wavflac_compress(pathlib.Path(sys.argv[1]).read_bytes()) is None"
    )
    ok(command([py, "-c", code, str(wav_path)], source=source), "unsupported PCM32 fallback")


def cli(py: str, source: Path, *args: str) -> bytes:
    return ok(command([py, "-m", "cmpct", *map(str, args)], source=source), "CLI " + " ".join(args[:2]))


def verify_archive(py: str, source: Path, archive: Path, expected: dict[str, bytes]) -> dict:
    cli(py, source, "verify", str(archive))
    cli(py, source, "preflight", str(archive))
    observed = {}
    for name, contents in expected.items():
        whole = cli(py, source, "cat", str(archive), name)
        assert whole == contents, "cat mismatch: " + name
        offset = min(41, len(contents))
        length = min(31, len(contents) - offset)
        part = cli(py, source, "range", str(archive), name, str(offset), str(length))
        assert part == contents[offset:offset + length], "range mismatch: " + name
        observed[name] = sha(whole)
    # Read the real physical codec list, but do not require a specific winner.
    pycode = (
        "import json,sys;"
        "from cmpct.reader import CMPCT;"
        "ar=CMPCT(sys.argv[1]);"
        "print(json.dumps({'codecs':[v[3] for v in ar.blobs],"
        "'files':[[v[0],v[2],v[3],v[4]] for v in ar.files]}));"
        "ar.close()"
    )
    fields = json.loads(ok(command([py, "-c", pycode, str(archive)], source=source), "physical-index").decode())
    return {"bytes": archive.stat().st_size, "sha256": sha(archive.read_bytes()),
            "logical_sha256": observed, **fields}


def frozen_vector(py: str, candidate: Path, root: Path) -> dict:
    from cmpct.reader import CMPCT
    vector = json.loads((ROOT / "tests/conformance/v24-wavflac.json").read_text())["vector"]
    raw = base64.b64decode(vector["archive_base64"])
    assert len(raw) == vector["archive_bytes"]
    assert sha(raw) == vector["archive_sha256"]
    target = root / "frozen-wavflac.cmpct"
    target.write_bytes(raw)
    # CLI is the actual package under test (same candidate source tree).
    cli(py, candidate, "preflight", str(target))
    cli(py, candidate, "verify", str(target))
    contents = cli(py, candidate, "cat", str(target), vector["name"])
    assert len(contents) == vector["logical_size"]
    assert sha(contents) == vector["logical_sha256"]
    range_spec = vector["range"]
    got = cli(py, candidate, "range", str(target), vector["name"],
              str(range_spec["offset"]), str(range_spec["length"]))
    assert got == bytes.fromhex(range_spec["hex"])
    # Independent physical-header corruption probe. A wrongly signed FLAC body
    # must not become successful logical read on the Python installed product.
    with CMPCT(target) as ar:
        row = ar.by[vector["name"]]
        assert ar.blobs[row[6][1]][3] == 2
        blob_pos = ar.record_base + ar.blobs[row[6][1]][0]
    corrupt = bytearray(raw)
    corrupt[blob_pos + 32] ^= 1
    bad = root / "frozen-corrupt-hash.cmpct"
    bad.write_bytes(corrupt)
    wrong = command([py, "-m", "cmpct", "verify", str(bad)], source=candidate)
    assert wrong.returncode != 0, "corrupted physical hash silently accepted"
    return {"vector_archive_sha256": sha(raw), "logical_sha256": sha(contents),
            "codec": 2, "corruption_rejected": True, "range_sha256": sha(got)}


def main() -> int:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--result", required=True)
    args = p.parse_args()
    try:
        import numpy, soundfile
        result = {"schema": "cmpct-o206-enabled-wavflac-v1",
                  "git_head": ok(command(["git", "rev-parse", "HEAD"]), "git HEAD").decode().strip(),
                  "platform": platform.platform(),
                  "python": sys.version,
                  "numpy_version": numpy.__version__,
                  "soundfile_version": soundfile.__version__,
                  "libsndfile_version": getattr(soundfile, "__libsndfile_version__", None)}
        old = ok(command(["git", "show", BASE_COMMIT + ":src/cmpct/codec.py"]), "git base codec")
        new = ok(command(["git", "show", "HEAD:src/cmpct/codec.py"]), "git candidate codec")
        assert git_blob(old) == BASE_CODEC_BLOB
        assert git_blob(new) == CAND_CODEC_BLOB
        result["historical_codec_blob"] = git_blob(old)
        result["candidate_codec_blob"] = git_blob(new)
        native_path = Path(ok(
            command([sys.executable, "-c",
                     "from cmpct.native_codec import _library_path; print(_library_path())"],
                    source=ROOT / "src"), "installed native core").decode().strip())
        assert native_path.is_file()
        result["native_sha256"] = sha(native_path.read_bytes())
        with tempfile.TemporaryDirectory(prefix="cmpct-o206-") as tmp:
            root = Path(tmp)
            oldpkg, newpkg = root / "old", root / "candidate"
            for dst, contents in ((oldpkg, old), (newpkg, new)):
                shutil.copytree(ROOT / "src/cmpct", dst / "cmpct")
                shutil.copy2(native_path, dst / "cmpct" / native_path.name)
                (dst / "cmpct/codec.py").write_bytes(contents)
            result["frozen"] = frozen_vector(sys.executable, newpkg, root)
            source = root / "supported"
            source.mkdir()
            expected = {
                "mono.wav": make_wav(channels=1, frames=2048, seed=7),
                "stereo.wav": make_wav(channels=2, frames=4096, seed=17),
                "other.bin": bytes(range(256)) * 2,
            }
            for name, payload in expected.items():
                (source / name).write_bytes(payload)
            cmp = {}
            for name in ("mono.wav", "stereo.wav"):
                historical = codec_trial(sys.executable, oldpkg, source / name)
                candidate = codec_trial(sys.executable, newpkg, source / name)
                assert historical == candidate, f"supported WAVFLAC codec bytes changed: {name}"
                assert candidate["prefix"] == b"fLaC".hex()
                assert candidate["decoded_sha256"] == sha(expected[name])
                cmp[name] = candidate
            result["supported_codec_trials"] = cmp
            oldarc, newarc = root / "historical.cmpct", root / "candidate.cmpct"
            cli(sys.executable, oldpkg, "create", str(source), str(oldarc),
                "--workers", "1", "--reproducible")
            cli(sys.executable, newpkg, "create", str(source), str(newarc),
                "--workers", "1", "--reproducible")
            oldreport = verify_archive(sys.executable, oldpkg, oldarc, expected)
            newreport = verify_archive(sys.executable, newpkg, newarc, expected)
            assert oldarc.read_bytes() == newarc.read_bytes(), "same-host historic/candidate physical mismatch"
            result["supported_corpus"] = newreport
            result["same_host_historical_candidate_archive_identical"] = True
            # Capability refusal must not prevent ordinary exact archiving.
            unsupported = root / "unsupported"
            unsupported.mkdir()
            bad = make_wav(channels=1, frames=383, seed=23, bits=32)
            (unsupported / "pcm32.wav").write_bytes(bad)
            codec_reject(sys.executable, newpkg, unsupported / "pcm32.wav")
            extra = root / "unsupported.cmpct"
            cli(sys.executable, newpkg, "create", str(unsupported), str(extra),
                "--workers", "1", "--reproducible")
            result["unsupported_fallback"] = verify_archive(
                sys.executable, newpkg, extra, {"pcm32.wav": bad})
        result["decision"] = "O206_SUPPORTED_WAVFLAC_EXTRAS_COMPATIBLE"
        success = True
    except Exception as e:
        result = {"schema": "cmpct-o206-enabled-wavflac-v1", "decision": "FAIL_OR_AMBIGUOUS",
                  "error": repr(e), "traceback": traceback.format_exc(),
                  "platform": platform.platform(), "python": sys.version}
        success = False
    out = Path(args.result)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
