from __future__ import annotations

from types import SimpleNamespace

from benchmarks import v030_r24_dictionary_skip_admission_oracle as ADMISSION


def test_pretraining_features_observe_release_bin_policy_and_restore_it(tmp_path, monkeypatch):
    source = tmp_path / "source"
    source.mkdir()
    (source / "shape.bin").write_bytes(b"x" * 128)

    observed = {"scan_bin_visible": False, "pack_bin_visible": False, "deflate_bin_visible": False}

    class FakeBuilder:
        def __init__(self, root, *, deflate_reuse_min):
            self.root = root
            self.micro_pack_target = 2 * 1024 * 1024
            self.micro_pack_max_file = 0
            self.cands = {"one": SimpleNamespace(raw=b"a" * 128, hints={".bin"})}

        def scan(self):
            observed["scan_bin_visible"] = ".bin" in ADMISSION.P.R24_BUILDER_MODULE.TEXT_EXT

        def _build_micro_packs(self):
            observed["pack_bin_visible"] = ".bin" in ADMISSION.P.R24_BUILDER_MODULE.TEXT_EXT

        def _prepare_deflate_reuse(self):
            observed["deflate_bin_visible"] = ".bin" in ADMISSION.P.R24_BUILDER_MODULE.TEXT_EXT

    monkeypatch.setattr(ADMISSION.P.C, "Builder", FakeBuilder)

    assert ".bin" not in ADMISSION.P.R24_BUILDER_MODULE.TEXT_EXT
    features = ADMISSION._pretraining_features(source)

    assert observed == {
        "scan_bin_visible": True,
        "pack_bin_visible": True,
        "deflate_bin_visible": True,
    }
    assert features["dictionary_sample_count"] == 1.0
    assert features["dictionary_sample_bytes"] == 128.0
    assert features["sample_mean_bytes"] == 128.0
    assert ".bin" not in ADMISSION.P.R24_BUILDER_MODULE.TEXT_EXT
