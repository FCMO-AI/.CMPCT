#!/usr/bin/env python3
"""J24I40 decision court: preserve actual outcomes, never enforce predicted divergence."""
import argparse
import hashlib
import json
import re
from pathlib import Path

ROW = re.compile(r"^variant=(valid|md5_flip|md5_zero) reference_exit=(\d+) claxon_exit=(\d+)$")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--case-dir", type=Path, required=True)
    p.add_argument("--raw", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    base = args.case_dir
    manifest = json.loads((base / "md5-manifest.json").read_text())
    assert manifest["schema"] == "j24i40-streaminfo-md5-v1"
    observed = {}
    for raw_line in args.raw.read_text().splitlines():
        match = ROW.fullmatch(raw_line)
        assert match is not None, f"unexpected raw result: {raw_line!r}"
        name, ref_rc, claxon_rc = match.groups()
        assert name not in observed, f"duplicate result: {name}"
        observed[name] = {"reference_exit": int(ref_rc), "claxon_exit": int(claxon_rc)}
    assert set(observed) == {"valid", "md5_flip", "md5_zero"}
    assert observed["valid"] == {"reference_exit": 0, "claxon_exit": 0}, "original must pass both"

    fingerprints = {}
    for name, item in manifest["cases"].items():
        path = base / item["file"]
        physical = path.read_bytes()
        assert sha(physical) == item["sha256"], f"bad byte custody: {name}"
        assert len(physical) == item["encoded_bytes"]
        fingerprints[name] = {
            "sha256": sha(physical),
            "bytes": len(physical),
            "changed_offsets": item["changed_offsets"],
            **observed[name],
        }
    flip = observed["md5_flip"]
    if flip["reference_exit"] != 0 and flip["claxon_exit"] == 0:
        decision = "DIVERGENCE_FLAC_INTERNAL_MD5_NOT_CHECKED_BY_CLAXON_ITERATOR"
    elif flip["reference_exit"] != 0 and flip["claxon_exit"] != 0:
        decision = "NO_DIVERGENCE_BOTH_REJECT_MD5_BITFLIP"
    elif flip["reference_exit"] == 0 and flip["claxon_exit"] == 0:
        decision = "NO_REFERENCE_DETECTION_OF_MD5_BITFLIP"
    else:
        decision = "UNEXPECTED_CLAXON_ONLY_REJECTION"
    results = {
        "schema": "j24i40-md5-court-result-v1",
        "classification": decision,
        "primary_prediction_supported": decision.startswith("DIVERGENCE_"),
        "product_correctness_claim": "NONE: decoded SHA-256/CRC32 are independently checked by Claxon research probe",
        "source_archive_sha256": manifest["original_archive_sha256"],
        "source_flac_sha256": manifest["original_flac_sha256"],
        "original_md5": manifest["original_streaminfo_md5_hex"],
        "cases": fingerprints,
        "encoded_audio_frames_unchanged": manifest["audio_frames_byte_identical"],
        "reference": "Xiph flac -t (test checks decoded PCM against nonzero STREAMINFO MD5)",
        "scope": "independent split-file scientific test; not full archive-reader source custody",
    }
    args.output.write_text(json.dumps(results, sort_keys=True, indent=2) + "\n")
    print(json.dumps(results, sort_keys=True))
    assert results["encoded_audio_frames_unchanged"] is True


if __name__ == "__main__":
    main()
