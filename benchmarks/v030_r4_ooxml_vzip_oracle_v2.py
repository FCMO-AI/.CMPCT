from __future__ import annotations

"""Receipt-preserving rerun of the OOXML S_VZIP falsifier.

The first oracle placed a malformed-ZIP hostile control after the useful Office measurement.  The mature Builder
currently lets ``zipfile.BadZipFile`` escape from suffix-routed deferred ZIP discovery, so that control could erase
the valid size/reconstruction receipt.  This rerun records the hostile behavior separately instead of hiding it.
A malformed suffix-routed ZIP that aborts the build is recorded as fail-closed debt, not as clean opaque fallback.
"""

import argparse, json, os
from pathlib import Path
import shutil

from benchmarks import v030_release_generalization as GENERAL
from benchmarks import v030_r4_ooxml_vzip_oracle as V1
from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.codec import S_VZIP


def run(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True); work.mkdir(parents=True)
    neutral = GENERAL.V029._load(GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "cmpct_v030_ooxml_neutral_v2")
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_v030_ooxml_repair_v2"); repair.install_generation_hooks(neutral)
    corpus = work / "neutral"; neutral.build(corpus); repair.normalize_root(corpus)
    source = corpus / V1.TARGET; expected = V1._content_tree(source)
    control_root = work / "control"; probe_root = work / "probe"
    control_reverse = V1._copy_variant(source, control_root, "control")
    probe_reverse = V1._copy_variant(source, probe_root, "probe")
    if sorted(control_reverse.values()) != sorted(probe_reverse.values()) or not probe_reverse:
        raise RuntimeError("OOXML variant mapping mismatch")

    control = V1._build_and_verify(control_root, control_reverse, work, "control", expected)
    probe = V1._build_and_verify(probe_root, probe_reverse, work, "probe", expected)
    saving = control["archive_bytes"] - probe["archive_bytes"]

    fake_root = work / "fake"; fake_root.mkdir(); (fake_root / "not-a-container.zip").write_bytes(b"PK\x03\x04" + b"not-a-valid-zip" * 32)
    fake_archive = work / "fake.cmpct"; fake_vzip = False; fake_fell_back = False; fake_error = None
    try:
        Builder(fake_root).build(fake_archive)
        with CMPCT(fake_archive) as ar:
            fake_vzip = any(row[1] == 0 and row[6] and row[6][0] == S_VZIP for row in ar.files)
        fake_fell_back = not fake_vzip
    except Exception as exc:
        fake_error = f"{type(exc).__name__}: {exc}"

    safe_not_virtualized = not fake_vzip
    supported = probe["vzip_file_count"] >= len(probe_reverse) and saving >= 1024 * 1024 and safe_not_virtualized
    return {
        "schema": "cmpct-v030-r4-ooxml-vzip-oracle-v2",
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "workload": V1.TARGET,
        "original_ooxml_files": sorted(probe_reverse.values()),
        "ooxml_file_count": len(probe_reverse),
        "original_content_tree_sha256": expected,
        "control": control,
        "probe_existing_s_vzip": probe,
        "saving_bytes": saving,
        "saving_fraction_of_control": saving / max(1, control["archive_bytes"]),
        "probe_to_control_ratio": probe["archive_bytes"] / max(1, control["archive_bytes"]),
        "hostile_malformed_zip": {
            "virtualized": fake_vzip,
            "clean_opaque_fallback": fake_fell_back,
            "build_error": fake_error,
            "safe_not_virtualized": safe_not_virtualized,
            "debt": None if fake_fell_back else ("suffix-routed malformed ZIP aborts build; content-driven discovery must catch parse failure and delegate opaque" if fake_error else "unexpected hostile behavior"),
        },
        "hypothesis": {
            "existing_s_vzip_is_exact_for_ooxml": probe["restored_content_tree_sha256"] == expected,
            "probe_virtualized_ooxml": probe["vzip_file_count"] >= len(probe_reverse),
            "control_did_not_virtualize_ooxml": control["vzip_file_count"] == 0,
            "material_size_win": saving >= 1024 * 1024,
            "hostile_malformed_container_not_virtualized": safe_not_virtualized,
            "hostile_malformed_container_clean_fallback": fake_fell_back,
            "supported_for_content_signature_admission_oracle": supported,
        },
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "production_builder_changed": False,
            "suffix_dispatch_proposed": False,
            "path_lengths_matched_between_control_and_probe": True,
            "exact_original_content_tree_required_after_name_restore": True,
            "hostile_control_failure_does_not_erase_size_receipt": True,
        },
        "next_if_supported": "implement bounded content-signature/central-directory discovery in a research wrapper; parse failures must delegate to opaque storage, then measure actual Office r24 size/create/member-range/recovery/native behavior and unrelated ZIP controls",
        "next_if_falsified": "do not widen virtual-container discovery for Office; return to a different stream-federation/derived-view primitive",
    }


def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/v030-r4-ooxml-vzip-v2-work')); p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-r4-ooxml-vzip-v2.json')); a=p.parse_args()
    r=run(a.work_root); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps({'control_bytes':r['control']['archive_bytes'],'probe_bytes':r['probe_existing_s_vzip']['archive_bytes'],'saving_bytes':r['saving_bytes'],'probe_vzip_files':r['probe_existing_s_vzip']['vzip_file_count'],'hostile':r['hostile_malformed_zip'],'hypothesis':r['hypothesis']},indent=2))

if __name__=='__main__': main()
