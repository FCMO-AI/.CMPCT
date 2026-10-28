from __future__ import annotations

import hashlib
from pathlib import Path
import platform
import struct
import subprocess

import pytest

from benchmarks import neutral_hostile_determinism_repair_v6 as R


def _elf_header(raw: bytes) -> tuple:
    return struct.unpack_from("<16sHHIQQQIHHHHHH", raw, 0)


def _program_header(raw: bytes) -> tuple:
    return struct.unpack_from("<IIQQQQQQ", raw, R.ELF_HEADER_BYTES)


def test_canonical_developer_elf_is_exact_deterministic_and_variant_specific() -> None:
    first = R.canonical_elf64(0)
    again = R.canonical_elf64(0)
    second = R.canonical_elf64(1)

    assert first == again
    assert first != second
    assert len(first) == len(second) == R.CANONICAL_ELF_BYTES == 112_776
    assert hashlib.sha256(first).digest() == hashlib.sha256(again).digest()

    # Footnote: exact file size is part of the repair contract because source-substrate repair must not make the
    # workload easier by simply shrinking the two historical 112,776-byte executable members.
    assert first[:4] == second[:4] == b"\x7fELF"
    assert b".note.gnu.build-id" not in first
    assert b".comment" not in first
    assert b"GCC:" not in first


def test_canonical_developer_elf_has_one_bounded_real_x86_64_load_image() -> None:
    raw = R.canonical_elf64(0)
    (
        ident,
        e_type,
        e_machine,
        e_version,
        e_entry,
        e_phoff,
        e_shoff,
        _e_flags,
        e_ehsize,
        e_phentsize,
        e_phnum,
        e_shentsize,
        e_shnum,
        e_shstrndx,
    ) = _elf_header(raw)

    assert ident[:4] == b"\x7fELF"
    assert ident[4:8] == bytes((2, 1, 1, 0))
    assert e_type == 2  # ET_EXEC
    assert e_machine == 62  # EM_X86_64
    assert e_version == 1
    assert e_entry == R.ELF_BASE_VADDR + R.ELF_CODE_OFFSET
    assert e_phoff == R.ELF_HEADER_BYTES
    assert e_shoff == 0
    assert e_ehsize == R.ELF_HEADER_BYTES
    assert e_phentsize == R.ELF_PROGRAM_HEADER_BYTES
    assert e_phnum == 1
    assert e_shentsize == e_shnum == e_shstrndx == 0

    p_type, p_flags, p_offset, p_vaddr, p_paddr, p_filesz, p_memsz, p_align = _program_header(raw)
    assert p_type == 1  # PT_LOAD
    assert p_flags == 5  # PF_R | PF_X
    assert p_offset == 0
    assert p_vaddr == p_paddr == R.ELF_BASE_VADDR
    assert p_filesz == p_memsz == R.CANONICAL_ELF_BYTES
    assert p_align == 0x1000


def test_canonical_developer_elf_embeds_exact_historical_static_table() -> None:
    for variant in range(R.ELF_VARIANTS):
        raw = R.canonical_elf64(variant)
        message = f"{sum(R._table_values(variant))}\n".encode("ascii")
        table_offset = R.ELF_CODE_OFFSET + 33 + len(message)
        values = list(struct.unpack_from("<25000I", raw, table_offset))

        # Footnote: the original corpus writes exactly this 25,000-entry C table and the executable sums it.
        # Keeping the complete table bytes prevents repair-v6 from replacing a realistic static-data workload
        # with a tiny launcher whose compression behavior would be materially easier and no longer comparable.
        assert values == R._table_values(variant)
        assert raw[R.ELF_CODE_OFFSET + 33 : table_offset] == message
        assert set(raw[table_offset + 25_000 * 4 :]) <= {0}


def test_developer_normalizer_changes_only_generated_executables(tmp_path: Path) -> None:
    workload = tmp_path / R.DEVELOPER_NAME
    build = workload / "build"
    build.mkdir(parents=True)
    marker = workload / "keep.txt"
    marker.write_bytes(b"unchanged benchmark source")
    (build / "app0").write_bytes(b"host-app-0")
    (build / "app1").write_bytes(b"host-app-1")
    before = marker.read_bytes()

    R.normalize_workload(workload)

    assert marker.read_bytes() == before
    assert (build / "app0").read_bytes() == R.canonical_elf64(0)
    assert (build / "app1").read_bytes() == R.canonical_elf64(1)
    assert (build / "app0").stat().st_mode & 0o111
    assert (build / "app1").stat().st_mode & 0o111


@pytest.mark.skipif(
    platform.system() != "Linux" or platform.machine().lower() not in {"x86_64", "amd64"},
    reason="canonical fixture executable targets Linux x86-64; byte-format tests remain cross-platform",
)
def test_canonical_developer_elf_preserves_original_program_output(tmp_path: Path) -> None:
    for variant in range(R.ELF_VARIANTS):
        path = tmp_path / f"app{variant}"
        path.write_bytes(R.canonical_elf64(variant))
        path.chmod(0o755)
        proc = subprocess.run([str(path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)

        # Footnote: the historical C program computes the sum of its static table and prints one decimal line.
        # The compiler-independent fixture must preserve that externally observable behavior, not merely parse as
        # ELF, otherwise benchmark repair would silently change the workload it claims to stabilize.
        assert proc.returncode == 0
        assert proc.stdout == f"{sum(R._table_values(variant))}\n"
        assert proc.stderr == ""
