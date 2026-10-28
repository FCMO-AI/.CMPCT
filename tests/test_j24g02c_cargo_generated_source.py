"""Cargo-generated target/ paths are not prospective Git-source custody."""
from __future__ import annotations

from pathlib import Path

from tools import check_v031_candidate_fingerprint as source

ROOT = Path(__file__).resolve().parents[1]


def test_generated_cargo_target_sources_never_change_candidate_fingerprint(tmp_path: Path) -> None:
    product = tmp_path / "src"
    product.mkdir()
    (product / "entry.py").write_text("answer = 42\n", encoding="utf-8")
    rust = tmp_path / "native" / "crate" / "src"
    rust.mkdir(parents=True)
    main = rust / "lib.rs"
    main.write_text("pub fn original() {}\n", encoding="utf-8")
    manifest = {
        "fingerprint_globs": [
            "src/**/*.py", "native/**/*.rs", "native/**/*.c", "native/**/*.h"
        ],
        "required_paths": [],
    }
    before, rows = source.fingerprint(manifest, root=tmp_path)
    assert set(rows) == {"src/entry.py", "native/crate/src/lib.rs"}

    generated = tmp_path / "native" / "crate" / "target" / "release" / "build" / "serde" / "out"
    generated.mkdir(parents=True)
    for name in ("private.rs", "flag_check.c", "zstd.h"):
        (generated / name).write_text("generated = local environment\n", encoding="utf-8")
    after, rows = source.fingerprint(manifest, root=tmp_path)
    assert after == before and set(rows) == {"src/entry.py", "native/crate/src/lib.rs"}

    for name in ("private.rs", "flag_check.c", "zstd.h"):
        (generated / name).write_text("generated = changed machine\n", encoding="utf-8")
    regenerated, _ = source.fingerprint(manifest, root=tmp_path)
    assert regenerated == before

    main.write_text("pub fn changed() {}\n", encoding="utf-8")
    source_changed, paths = source.fingerprint(manifest, root=tmp_path)
    assert source_changed != before
    assert "native/crate/src/lib.rs" in paths


def test_real_native_source_is_charged_without_cargo_target_artifacts() -> None:
    digest, files = source.fingerprint(source.load_manifest())
    assert len(digest) == 64
    assert "native/cmpct-core/src/lib.rs" in files
    assert "native/cmpct-core/target/release/build/serde-fb811f44da2e6fa8/out/private.rs" not in files
    assert not any("/target/" in f for f in files if f.startswith("native/"))
