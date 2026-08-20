from __future__ import annotations

"""Neutral/hostile benchmark substrate repair-v6 — compiler-independent developer ELF fixtures.

Repair-v5 made the office/log/backup/media subset portable, but the developer-repository workload still
contained two stripped executables produced by the host ``gcc``/linker. Those files carry toolchain provenance
such as GNU build IDs and compiler comments, so a synthetic source tree advertised as frozen could change even
when every source byte, RNG seed, workload size and recorded high-level compiler version stayed the same.

Repair-v6 composes repair-v5 unchanged and canonicalizes only ``build/app0`` and ``build/app1`` after the
historical generator has produced the developer workload. Each replacement is a real runnable ELF64 x86-64
executable with one deterministic PT_LOAD segment, a tiny Linux syscall program, and the exact 25,000-entry
integer table represented by the corresponding C source. The file is padded to the historical 112,776-byte
shape so the workload keeps its file count and logical-byte envelope while eliminating compiler/linker metadata.

Footnote: this is benchmark-substrate repair, not candidate preprocessing. v0.28/v0.29/v0.30 and competitors
must all consume the same repaired tree. Historical evidence is never rewritten; the new identity is admissible
only after independent cross-path/cross-run manifests and the exact embedded v0.28 bytes are preserved as durable
evidence. The inherited absolute v0.30 improvement floor must therefore remain unchanged even if repaired bytes
compress differently.
"""

import functools
import importlib.util
from pathlib import Path
import struct
import sys

HERE = Path(__file__).resolve().parent
BASE_PATH = HERE / "neutral_hostile_determinism_repair_v5.py"
DEVELOPER_NAME = "01_developer_repository"
CANONICAL_ELF_BYTES = 112_776
ELF_BASE_VADDR = 0x400000
ELF_HEADER_BYTES = 64
ELF_PROGRAM_HEADER_BYTES = 56
ELF_CODE_OFFSET = ELF_HEADER_BYTES + ELF_PROGRAM_HEADER_BYTES
ELF_VARIANTS = 2


def _load_base():
    name = "cmpct_neutral_hostile_repair_v5_for_v6"
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(name, BASE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {BASE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


BASE = _load_base()
AFFECTED = set(BASE.AFFECTED) | {DEVELOPER_NAME}
X264_CANONICAL_PARAMS = BASE.X264_CANONICAL_PARAMS


def _table_values(variant: int) -> list[int]:
    if not 0 <= variant < ELF_VARIANTS:
        raise ValueError(f"unsupported canonical ELF variant {variant}")
    return [(index * 17 + variant * 13) % 997 for index in range(25_000)]


def canonical_elf64(variant: int) -> bytes:
    """Return a deterministic runnable ELF64 image corresponding to historical ``app{variant}.c``.

    The code writes the precomputed table sum and exits through Linux x86-64 syscalls. The table itself is
    embedded byte-for-byte as little-endian u32 data, so the benchmark retains the large, similar-but-not-equal
    static payload that the generated C source was designed to produce without delegating fixture identity to a
    mutable compiler or linker.
    """
    values = _table_values(variant)
    message = f"{sum(values)}\n".encode("ascii")
    code = bytearray()
    code += b"\xb8\x01\x00\x00\x00"  # mov eax, SYS_write
    code += b"\xbf\x01\x00\x00\x00"  # mov edi, stdout

    # Footnote: RIP-relative addressing keeps the fixture position-independent inside its one fixed PT_LOAD
    # image. ``lea``'s displacement is derived from layout rather than copied as an unexplained magic constant.
    lea_next_offset = ELF_CODE_OFFSET + len(code) + 7
    code_bytes = 33
    message_offset = ELF_CODE_OFFSET + code_bytes
    code += b"\x48\x8d\x35" + struct.pack("<i", message_offset - lea_next_offset)
    code += b"\xba" + struct.pack("<I", len(message))  # mov edx, message length
    code += b"\x0f\x05"  # syscall
    code += b"\xb8\x3c\x00\x00\x00"  # mov eax, SYS_exit
    code += b"\x31\xff"  # xor edi, edi
    code += b"\x0f\x05"  # syscall
    if len(code) != code_bytes:
        raise RuntimeError("canonical ELF code layout drift")

    table = struct.pack("<25000I", *values)
    body_without_padding = bytes(code) + message + table
    prefix_bytes = ELF_HEADER_BYTES + ELF_PROGRAM_HEADER_BYTES + len(body_without_padding)
    if prefix_bytes > CANONICAL_ELF_BYTES:
        raise RuntimeError("canonical ELF payload exceeds preserved fixture envelope")
    padding = b"\x00" * (CANONICAL_ELF_BYTES - prefix_bytes)
    file_bytes = CANONICAL_ELF_BYTES

    ident = b"\x7fELF" + bytes((2, 1, 1, 0)) + b"\x00" * 8
    elf_header = struct.pack(
        "<16sHHIQQQIHHHHHH",
        ident,
        2,  # ET_EXEC
        62,  # EM_X86_64
        1,
        ELF_BASE_VADDR + ELF_CODE_OFFSET,
        ELF_HEADER_BYTES,
        0,
        0,
        ELF_HEADER_BYTES,
        ELF_PROGRAM_HEADER_BYTES,
        1,
        0,
        0,
        0,
    )
    program_header = struct.pack(
        "<IIQQQQQQ",
        1,  # PT_LOAD
        5,  # PF_R | PF_X
        0,
        ELF_BASE_VADDR,
        ELF_BASE_VADDR,
        file_bytes,
        file_bytes,
        0x1000,
    )
    result = elf_header + program_header + body_without_padding + padding
    if len(result) != CANONICAL_ELF_BYTES or result[:4] != b"\x7fELF":
        raise RuntimeError("canonical ELF framing drift")
    return result


def _canonicalize_developer_elf(workload: Path) -> None:
    build = workload / "build"
    for variant in range(ELF_VARIANTS):
        path = build / f"app{variant}"
        if not path.is_file():
            raise RuntimeError(f"developer-repository fixture missing {path.name}")
        path.write_bytes(canonical_elf64(variant))
        path.chmod(0o755)


def install_generation_hooks(neutral_module) -> None:
    """Install every producer-side repair needed to generate the accepted v6 bytes directly.

    Repair-v6 was originally safe only when every caller remembered to invoke ``normalize_root`` after the
    historical corpus builder returned. That is too fragile for a benchmark identity that now underpins several
    independent release gates: a forgotten post-pass can silently reintroduce host GCC/linker bytes before the
    first tree check. Keep ``normalize_root`` as an idempotent compatibility guard, but enforce the same accepted
    normalization at both the individual developer producer and aggregate ``build`` boundary.

    Footnote: some historical corpus modules assemble an internal builder table when the module is imported.
    Replacing ``corpus_source_repo`` afterward does not change a function object already captured by that table.
    Wrapping aggregate ``build`` closes that stale-reference path without changing any generated source byte: the
    post-pass is exactly the repair-v6 normalization accepted by two independent runner reproductions.
    """
    # Repair-v5 still owns CPU-canonical media generation and the earlier deterministic producer hooks.
    BASE.install_generation_hooks(neutral_module)

    current = getattr(neutral_module, "corpus_source_repo", None)
    if current is None:
        raise RuntimeError("neutral hostile generator no longer exposes corpus_source_repo")
    if not getattr(current, "_cmpct_developer_repair_v6_wrapper", False):
        historical_developer = current

        @functools.wraps(historical_developer)
        def deterministic_developer(root: Path) -> None:
            historical_developer(root)
            workload = Path(root) / DEVELOPER_NAME
            if not workload.is_dir():
                raise RuntimeError("developer-repository producer did not create its canonical workload directory")
            _canonicalize_developer_elf(workload)

        deterministic_developer._cmpct_developer_repair_v6_wrapper = True
        neutral_module.corpus_source_repo = deterministic_developer

    aggregate = getattr(neutral_module, "build", None)
    if callable(aggregate) and not getattr(aggregate, "_cmpct_repair_v6_aggregate_wrapper", False):
        historical_build = aggregate

        @functools.wraps(historical_build)
        def deterministic_aggregate(root: Path) -> None:
            historical_build(root)
            normalize_root(Path(root))

        deterministic_aggregate._cmpct_repair_v6_aggregate_wrapper = True
        neutral_module.build = deterministic_aggregate


def normalize_workload(workload: Path) -> None:
    if workload.name == DEVELOPER_NAME:
        _canonicalize_developer_elf(workload)
        return
    BASE.normalize_workload(workload)


def normalize_root(root: Path) -> None:
    for name in sorted(AFFECTED):
        path = root / name
        if path.exists():
            normalize_workload(path)
