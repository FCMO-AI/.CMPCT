"""ONE-G0.2 static discriminator for the rolling-min suffix result.

The dynamic A/B cut the source-level derived-state-read counter by ~50% but
moved cross-large elapsed by only ~1.3%.  Before inventing another suffix
counter optimization, inspect whether -O3 already compiles the baseline
recurrence into machine work similar to the explicit rolling-min source.

This is generated-code evidence only.  It cannot promote either implementation.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

BASELINE_FN = "one_g02_minimizer_offset_only_kernel"
CANDIDATE_FN = "one_g02_minimizer_offset_rollmin_kernel"


def _extract(lines: list[str], fn: str) -> list[str]:
    start = None
    end = None
    for i, line in enumerate(lines):
        if line.strip() == f"{fn}:":
            start = i + 1
        if start is not None and line.strip().startswith(f".size\t{fn},"):
            end = i
            break
    if start is None:
        raise RuntimeError(f"function not found in assembly: {fn}")
    return lines[start:end]


def _metrics(body: list[str]) -> dict[str, int]:
    instructions: list[str] = []
    for line in body:
        text = line.strip()
        if not text or text.startswith(".") or text.endswith(":") or text.startswith("#"):
            continue
        # GCC Intel assembly instruction lines are tab/space indented and begin
        # with the mnemonic after stripping.  Ignore assembler directives above.
        mnemonic = text.split(None, 1)[0]
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9.]*", mnemonic):
            continue
        instructions.append(text)
    mnemonics = [x.split(None, 1)[0].lower() for x in instructions]
    return {
        "instruction_count": len(instructions),
        "memory_operand_instruction_count": sum("[" in x and "]" in x for x in instructions),
        "conditional_jump_count": sum(m.startswith("j") and m not in {"jmp", "jmpq"} for m in mnemonics),
        "unconditional_jump_count": sum(m in {"jmp", "jmpq"} for m in mnemonics),
        "call_count": sum(m.startswith("call") for m in mnemonics),
    }


def _compile(source: Path, fn: str, temp: Path) -> dict[str, object]:
    asm = temp / f"{source.stem}.s"
    compiler = os.environ.get("CC", "cc")
    subprocess.run(
        [compiler, "-O3", "-std=c11", "-S", "-masm=intel", str(source), "-o", str(asm)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    lines = asm.read_text(encoding="utf-8").splitlines()
    body = _extract(lines, fn)
    return {"function": fn, **_metrics(body)}


def run() -> dict[str, object]:
    here = Path(__file__).parent
    with tempfile.TemporaryDirectory(prefix="cmpct-one-g02-rollmin-codegen-") as td:
        temp = Path(td)
        baseline = _compile(here / "one_g02_minimizer_offset_only_kernel.c", BASELINE_FN, temp)
        candidate = _compile(here / "one_g02_minimizer_offset_rollmin_kernel.c", CANDIDATE_FN, temp)
    instruction_ratio = candidate["instruction_count"] / baseline["instruction_count"]
    memory_ratio = candidate["memory_operand_instruction_count"] / baseline["memory_operand_instruction_count"]
    if instruction_ratio >= 0.95 and memory_ratio >= 0.95:
        interpretation = "generated_shape_near_equivalent"
    elif instruction_ratio <= 0.85 or memory_ratio <= 0.85:
        interpretation = "candidate_has_material_static_work_reduction"
    else:
        interpretation = "mixed_codegen_difference"
    return {
        "schema": "cmpct-one-g02-offset-rollmin-codegen-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "compiler": os.environ.get("CC", "cc"),
        "baseline": baseline,
        "candidate": candidate,
        "candidate_over_baseline_instruction_ratio": instruction_ratio,
        "candidate_over_baseline_memory_operand_ratio": memory_ratio,
        "interpretation": interpretation,
        "interpretation_thresholds": {
            "near_equivalent_min_ratio": 0.95,
            "material_reduction_max_ratio": 0.85,
        },
        "claim_boundary": "static generated-code diagnostic only; no elapsed/product authority",
    }


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
