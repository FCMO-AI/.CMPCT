from __future__ import annotations

"""R4 Office falsifier: route valid OOXML containers through the existing r24 S_VZIP primitive.

The canonical r24 Builder already has a native/readable/recovery-gated virtual ZIP representation, but encoder
container discovery currently defers only `.zip` and `.whl`.  Office documents are ZIP containers too.  This
oracle does NOT propose suffix dispatch and does not change the product.  It creates two path-length-matched copies
of the frozen Office workload: a non-virtual control and a probe whose valid OOXML members are renamed so the
unchanged Builder exercises S_VZIP.  Both outputs are extracted, names restored and compared byte-for-byte to the
original source tree.  A positive result authorizes only a later content-signature-driven admission experiment.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import time

from benchmarks import v030_release_generalization as GENERAL
from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.codec import S_VZIP

TARGET = "02_office_workspace"
OOXML = {".docx", ".xlsx", ".pptx"}


def _content_tree(root: Path) -> str:
    h = hashlib.sha256(); root = Path(root)
    for p in sorted(q for q in root.rglob("*") if q.is_file()):
        rel = p.relative_to(root).as_posix().encode(); raw = p.read_bytes()
        h.update(len(rel).to_bytes(4, "little")); h.update(rel); h.update(len(raw).to_bytes(8, "little")); h.update(raw)
    return h.hexdigest()


def _copy_variant(src: Path, dst: Path, mode: str) -> dict[str, str]:
    shutil.rmtree(dst, ignore_errors=True); shutil.copytree(src, dst)
    reverse: dict[str, str] = {}
    for p in sorted(dst.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in OOXML:
            continue
        original_rel = p.relative_to(dst).as_posix()
        if mode == "control":
            q = p.with_suffix(".ooxx")  # five chars incl dot, same as docx/xlsx/pptx
        elif mode == "probe":
            q = p.with_name(p.stem + "_.zip")  # underscore compensates for .zip being one byte shorter
        else:
            raise ValueError(mode)
        if len(q.relative_to(dst).as_posix().encode()) != len(original_rel.encode()):
            raise RuntimeError("path-length matching failed")
        p.rename(q); reverse[q.relative_to(dst).as_posix()] = original_rel
    return reverse


def _restore_names(root: Path, reverse: dict[str, str]) -> None:
    for changed, original in sorted(reverse.items(), key=lambda x: x[0], reverse=True):
        src = root.joinpath(*Path(changed).parts); dst = root.joinpath(*Path(original).parts)
        dst.parent.mkdir(parents=True, exist_ok=True); src.rename(dst)


def _build_and_verify(root: Path, reverse: dict[str, str], work: Path, name: str, expected_tree: str) -> dict:
    archive = work / f"{name}.cmpct"
    started = time.perf_counter(); stats = dict(Builder(root).build(archive)); create_s = time.perf_counter() - started
    with CMPCT(archive) as ar:
        vzip_files = [row[0] for row in ar.files if row[1] == 0 and row[6] and row[6][0] == S_VZIP]
        recipes = len(ar.recipes)
        out = work / f"{name}-out"; shutil.rmtree(out, ignore_errors=True)
        started = time.perf_counter(); ar.extractall(out, metadata=True); extract_s = time.perf_counter() - started
    _restore_names(out, reverse)
    actual = _content_tree(out)
    if actual != expected_tree:
        raise RuntimeError(f"{name} reconstructed content tree mismatch: {actual} != {expected_tree}")
    return {
        "archive_bytes": archive.stat().st_size,
        "create_wall_s": create_s,
        "extract_wall_s": extract_s,
        "vzip_file_count": len(vzip_files),
        "vzip_files": vzip_files,
        "recipe_count": recipes,
        "builder_stats": stats,
        "restored_content_tree_sha256": actual,
    }


def run(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True); work.mkdir(parents=True)
    neutral = GENERAL.V029._load(GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "cmpct_v030_ooxml_neutral")
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_v030_ooxml_repair"); repair.install_generation_hooks(neutral)
    corpus = work / "neutral"; neutral.build(corpus); repair.normalize_root(corpus)
    source = corpus / TARGET; expected = _content_tree(source)

    control_root = work / "control"; probe_root = work / "probe"
    control_reverse = _copy_variant(source, control_root, "control")
    probe_reverse = _copy_variant(source, probe_root, "probe")
    if sorted(control_reverse.values()) != sorted(probe_reverse.values()) or not probe_reverse:
        raise RuntimeError("OOXML variant mapping mismatch")

    control = _build_and_verify(control_root, control_reverse, work, "control", expected)
    probe = _build_and_verify(probe_root, probe_reverse, work, "probe", expected)
    saving = control["archive_bytes"] - probe["archive_bytes"]

    # False-positive control: extension/suffix alone cannot make arbitrary bytes a valid virtual ZIP recipe.
    fake_root = work / "fake"; fake_root.mkdir(); fake = fake_root / "not-a-container.zip"; fake.write_bytes(b"PK\x03\x04" + b"not-a-valid-zip" * 32)
    fake_archive = work / "fake.cmpct"; Builder(fake_root).build(fake_archive)
    with CMPCT(fake_archive) as ar:
        fake_vzip = any(row[1] == 0 and row[6] and row[6][0] == S_VZIP for row in ar.files)
    if fake_vzip:
        raise RuntimeError("malformed ZIP-like hostile control was virtualized")

    return {
        "schema": "cmpct-v030-r4-ooxml-vzip-oracle-v1",
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "workload": TARGET,
        "original_ooxml_files": sorted(probe_reverse.values()),
        "ooxml_file_count": len(probe_reverse),
        "original_content_tree_sha256": expected,
        "control": control,
        "probe_existing_s_vzip": probe,
        "saving_bytes": saving,
        "saving_fraction_of_control": saving / max(1, control["archive_bytes"]),
        "probe_to_control_ratio": probe["archive_bytes"] / max(1, control["archive_bytes"]),
        "hostile_fake_zip_fell_back": not fake_vzip,
        "hypothesis": {
            "existing_s_vzip_is_exact_for_ooxml": probe["restored_content_tree_sha256"] == expected,
            "probe_virtualized_ooxml": probe["vzip_file_count"] >= len(probe_reverse),
            "control_did_not_virtualize_ooxml": control["vzip_file_count"] == 0,
            "material_size_win": saving >= 1024 * 1024,
            "hostile_malformed_container_rejected": not fake_vzip,
            "supported_for_content_signature_admission_oracle": probe["vzip_file_count"] >= len(probe_reverse) and saving >= 1024 * 1024 and not fake_vzip,
        },
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "production_builder_changed": False,
            "suffix_dispatch_proposed": False,
            "path_lengths_matched_between_control_and_probe": True,
            "exact_original_content_tree_required_after_name_restore": True,
        },
        "next_if_supported": "replace suffix routing with bounded ZIP-signature/central-directory discovery, admit only when the existing S_VZIP recipe is exact and economically wins, then measure complete r24 product size/create/selective/recovery/native behavior on Office plus hostile non-Office ZIP controls",
        "next_if_falsified": "do not widen r24 virtual-container discovery for Office; return to a different stream-federation/derived-view primitive",
    }


def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-ooxml-vzip-work")); p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-ooxml-vzip.json")); a=p.parse_args()
    r=run(a.work_root); a.output.parent.mkdir(parents=True, exist_ok=True); a.output.write_text(json.dumps(r, indent=2)+"\n")
    print(json.dumps({"control_bytes":r["control"]["archive_bytes"],"probe_bytes":r["probe_existing_s_vzip"]["archive_bytes"],"saving_bytes":r["saving_bytes"],"probe_vzip_files":r["probe_existing_s_vzip"]["vzip_file_count"],"hypothesis":r["hypothesis"]}, indent=2))

if __name__ == "__main__": main()
