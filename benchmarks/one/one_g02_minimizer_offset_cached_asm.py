"""ONE-G0.2 static causal companion for offset-only cached recurrence.

The paired ABBA experiment falsified the claim that halving modeled C-level
suffix-build reads yields a repeatable elapsed win.  This instrument asks the
next causal question without changing the implementation: does the eliminated
logical reread survive -O3 as materially different generated machine code?

It reports exact same-compiler function size, instruction count and static
memory-reference instruction count for the old offset-only and cached forms.
Those are diagnostics, not dynamic traffic counters and not performance gates.
If codegen is effectively identical, C-level derived-read accounting was an
invalid proxy for physical work.  If it differs materially, cache/OOO behavior
or measurement sensitivity remains the stronger explanation.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile


def _compile(source: Path, output: Path) -> None:
    subprocess.run(
        [os.environ.get("CC", "cc"), "-O3", "-std=c11", "-c", str(source), "-o", str(output)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _function(obj: Path, symbol: str) -> list[str]:
    text = subprocess.run(
        [os.environ.get("OBJDUMP", "objdump"), "-d", "-M", "intel", "--no-show-raw-insn", str(obj)],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if re.search(rf"<{re.escape(symbol)}>:$", line.strip()):
            start = i + 1
            break
    if start is None:
        raise RuntimeError(f"symbol not found: {symbol}")
    body: list[str] = []
    for line in lines[start:]:
        stripped = line.strip()
        if re.search(r"^[0-9a-f]+ <[^>]+>:$", stripped):
            break
        if re.match(r"^[0-9a-f]+:\s+[a-zA-Z]", stripped):
            body.append(stripped)
    return body


def _instruction_text(line: str) -> str:
    return re.sub(r"^[0-9a-f]+:\s+", "", line).strip().lower()


def _mnemonic(line: str) -> str:
    return _instruction_text(line).split(None, 1)[0]


def _metrics(lines: list[str]) -> dict[str, object]:
    inst = [_instruction_text(line) for line in lines]
    mnemonics = [_mnemonic(line) for line in lines]
    memory = [text for text in inst if "[" in text]
    branches = [m for m in mnemonics if m.startswith("j") or m in {"call", "ret"}]
    # Normalize branch/call addresses before hashing structural text.  This is a
    # reproducibility fingerprint, not a semantic equivalence proof.
    normalized = [re.sub(r"\b[0-9a-f]+\s*<[^>]+>", "<target>", text) for text in inst]
    digest = hashlib.sha256("\n".join(normalized).encode()).hexdigest()
    return {
        "instruction_count": len(inst),
        "memory_reference_instruction_count": len(memory),
        "branch_call_ret_instruction_count": len(branches),
        "normalized_instruction_sha256": digest,
    }


def run() -> dict[str, object]:
    here = Path(__file__).parent
    with tempfile.TemporaryDirectory(prefix="cmpct-one-g02-offset-cached-asm-") as td:
        td_path = Path(td)
        old_obj = td_path / "offset.o"
        cached_obj = td_path / "cached.o"
        _compile(here / "one_g02_minimizer_offset_only_kernel.c", old_obj)
        _compile(here / "one_g02_minimizer_offset_cached_kernel.c", cached_obj)
        old_lines = _function(old_obj, "one_g02_minimizer_offset_only_kernel")
        cached_lines = _function(cached_obj, "one_g02_minimizer_offset_cached_kernel")
        old = _metrics(old_lines)
        cached = _metrics(cached_lines)
        return {
            "schema": "cmpct-one-g02-minimizer-offset-cached-asm-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "compiler": os.environ.get("CC", "cc"),
            "old_offset_only": old,
            "cached_recurrence": cached,
            "instruction_count_delta": int(cached["instruction_count"]) - int(old["instruction_count"]),
            "memory_reference_instruction_delta": int(cached["memory_reference_instruction_count"]) - int(old["memory_reference_instruction_count"]),
            "claim_boundary": "static same-compiler codegen diagnostic only; no dynamic traffic or elapsed authority",
        }


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
