"""J24G53e hostile source/native loader custody controls; never timed product credit."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess

import pytest

from tools import j24g53e_native_runtime_custody as court


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def _commit(root: Path) -> str:
    _git(root, "add", "src")
    _git(root, "-c", "user.email=ci@example.invalid", "-c", "user.name=J24G53e Control", "commit", "-qm", "fixture")
    return _git(root, "rev-parse", "HEAD")


def _make_checkout(root: Path, number: int) -> tuple[str, str]:
    pkg = root / "src" / "cmpct"
    pkg.mkdir(parents=True)
    (root / "benchmarks").mkdir()
    for name in ("__init__.py", "builder.py", "reader.py", "codec.py"):
        (pkg / name).write_text(f"# fixture {name}: no real CMPCT imported\n")
    (pkg / "native_codec.py").write_text(
        "from pathlib import Path\nimport ctypes\n"
        "def _library_path():\n    return Path(__file__).parent / 'cmpct_core.so'\n"
        "_core = ctypes.CDLL(str(_library_path()))\n"
    )
    cc = root / "native.c"
    cc.write_text(f"int j24g53e_fixture(void) {{ return {number}; }}\n")
    subprocess.run(["gcc", "-shared", "-fPIC", "-o", str(pkg / "cmpct_core.so"), str(cc)], check=True)
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    head = _commit(root)
    digest = hashlib.sha256((pkg / "cmpct_core.so").read_bytes()).hexdigest()
    return head, digest


@pytest.fixture
def repos(tmp_path: Path):
    if not shutil.which("gcc") or not Path("/proc/self/maps").exists():
        pytest.skip("Linux ELF/gcc hostile controls only")
    base = tmp_path / "base"
    candidate = tmp_path / "candidate"
    bh, bd = _make_checkout(base, 101)
    ch, cd = _make_checkout(candidate, 202)
    receipt = tmp_path / "base-native.json"
    receipt.write_text(json.dumps({"source_commit": bh, "native_sha256": bd}))
    return base, candidate, bh, ch, bd, cd, receipt


def test_authentic_base_and_candidate_native_distinguished(repos):
    base, candidate, bh, ch, bd, cd, receipt = repos
    result = court.attest(candidate, base, ch, bh, receipt)
    assert result["schema"] == court.SCHEMA
    assert result["base"]["native"]["sha256"] == bd
    assert result["candidate"]["native"]["sha256"] == cd
    assert result["controls"]["base_matches_materialized_native_sha"] is True
    assert result["controls"]["same_native_binary_sha256"] is False
    assert result["base"]["native"]["mapped_regions"] > 0
    assert result["candidate"]["native"]["has_executable_mapping"]


def test_false_base_native_receipt_rejected(repos):
    base, candidate, bh, ch, _, _, receipt = repos
    receipt.write_text(json.dumps({"source_commit": bh, "native_sha256": "0" * 64}))
    with pytest.raises(ValueError, match="loaded binary disagrees"):
        court.attest(candidate, base, ch, bh, receipt)


def test_wrong_git_head_rejected_before_loading(repos):
    base, candidate, bh, ch, _, _, receipt = repos
    with pytest.raises(ValueError, match="wrong source HEAD"):
        court.attest(candidate, base, "e" * 40, bh, receipt)


def test_dirty_python_source_rejected(repos):
    base, candidate, bh, ch, _, _, receipt = repos
    (candidate / "src" / "cmpct" / "reader.py").write_text("# tampered uncommitted reader\n")
    with pytest.raises(RuntimeError, match="dirty source member"):
        court.attest(candidate, base, ch, bh, receipt)


def test_symlink_native_library_rejected(repos):
    base, candidate, bh, ch, _, _, receipt = repos
    lib = candidate / "src" / "cmpct" / "cmpct_core.so"
    target = candidate / "src" / "cmpct" / "surrogate.so"
    lib.rename(target)
    lib.symlink_to(target.name)
    with pytest.raises(RuntimeError, match="symlink native library"):
        court.attest(candidate, base, ch, bh, receipt)


def test_out_of_package_native_library_rejected(repos):
    base, candidate, bh, ch, _, _, receipt = repos
    lib = candidate / "src" / "cmpct" / "cmpct_core.so"
    moved = candidate / "external_native.so"
    lib.rename(moved)
    module = candidate / "src" / "cmpct" / "native_codec.py"
    module.write_text(
        "from pathlib import Path\nimport ctypes\n"
        f"def _library_path():\n    return Path({str(moved)!r})\n"
        "_core = ctypes.CDLL(str(_library_path()))\n"
    )
    ch = _commit(candidate)
    with pytest.raises(RuntimeError, match="native library escaped package"):
        court.attest(candidate, base, ch, bh, receipt)


def test_missing_native_library_rejected(repos):
    base, candidate, bh, ch, _, _, receipt = repos
    (candidate / "src" / "cmpct" / "cmpct_core.so").unlink()
    with pytest.raises(RuntimeError, match="native provenance probe failed"):
        court.attest(candidate, base, ch, bh, receipt)


def test_source_tree_alias_rejected(repos):
    base, candidate, bh, ch, _, _, receipt = repos
    with pytest.raises(ValueError, match="same source tree"):
        court.attest(candidate, candidate, ch, ch, receipt)


def test_original_abba_comparator_precedes_probe_and_receipt_upload():
    # Historical thresholds and all four timed phases remain ahead of the observer.
    # This is a custody/layout assertion, not a performance improvement claim.
    workflow = (Path(__file__).resolve().parents[1] / ".github" / "workflows" / "zip-parity.yml").read_text()
    phase_names = (
        "- name: Benchmark A — direct base",
        "- name: Benchmark B — candidate",
        "- name: Benchmark B — candidate repeat",
        "- name: Benchmark A — direct base repeat",
    )
    comparator = workflow.index("- name: Reject performance regressions")
    observer = workflow.index("- name: J24G53e post-ABBA native")
    upload = workflow.index("- name: Upload release benchmark evidence")
    assert all(workflow.index(name) < comparator for name in phase_names)
    assert comparator < observer < upload
    assert "--max-time-regression 0.05" in workflow
    assert "--max-size-regression 0.01" in workflow
    assert "if: always()" in workflow[observer:upload]


def test_same_name_different_inode_after_ctypes_load_rejected(repos):
    # Distinguishes a pathname that remains constant from a mapped inode
    # replaced after dlopen. A name-only check would incorrectly accept this.
    base, candidate, bh, ch, _, _, receipt = repos
    pkg = candidate / 'src' / 'cmpct'
    src = base / 'src' / 'cmpct' / 'cmpct_core.so'
    shutil.copyfile(src, pkg / 'surrogate.so')
    mod = pkg / 'native_codec.py'
    mod.write_text(
        'from pathlib import Path\nimport ctypes, shutil\n'
        '_lib = Path(__file__).parent / "cmpct_core.so"\n'
        '_core = ctypes.CDLL(str(_lib))\n'
        '_lib.rename(Path(__file__).parent / "old_loaded_inode.so")\n'
        'shutil.copyfile(Path(__file__).parent / "surrogate.so", _lib)\n'
        'def _library_path():\n    return _lib\n'
    )
    ch = _commit(candidate)
    with pytest.raises(RuntimeError, match='native binary not mapped'):
        court.attest(candidate, base, ch, bh, receipt)
