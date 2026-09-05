"""Static codegen check for the ONE-G0.2 tail-return 8 KiB dispatcher.

Diagnostic only: confirm that the rehabilitation removes call/return + result-copy
work rather than merely rewriting C source.  The dispatcher object is compiled
with the same `-O3 -fPIC` settings used by the timing harness and disassembled
with relocations.  A supported tail shape contains branch relocations to both
selector targets and no `call` instruction in the dispatcher body.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

TARGETS = (
    "one_g02_minimizer_segmented_counter_kernel",
    "one_g02_minimizer_offset_only_kernel",
)
SYMBOL = "one_g02_minimizer_size_dispatch_tail_kernel"


def run() -> dict[str, object]:
    here = Path(__file__).parent
    with tempfile.TemporaryDirectory(prefix="cmpct-one-g02-tail-dispatch-asm-") as td:
        obj = Path(td) / "dispatch.o"
        subprocess.run(
            [
                os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-c",
                str(here / "one_g02_minimizer_size_dispatch_tail_kernel.c"),
                "-o", str(obj),
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        text = subprocess.run(
            [os.environ.get("OBJDUMP", "objdump"), "-dr", "-M", "intel", "--no-show-raw-insn", str(obj)],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ).stdout
        lines = text.splitlines()
        start = next((i + 1 for i, line in enumerate(lines) if re.search(rf"<{re.escape(SYMBOL)}>:$", line.strip())), None)
        if start is None:
            raise RuntimeError("dispatcher symbol not found")
        body: list[str] = []
        for line in lines[start:]:
            if re.search(r"^[0-9a-f]+ <[^>]+>:$", line.strip()):
                break
            body.append(line.rstrip())
        instructions = [line.strip() for line in body if re.match(r"^[0-9a-f]+:\s+[A-Za-z]", line.strip())]
        mnemonics = [re.sub(r"^[0-9a-f]+:\s+", "", line).split(None, 1)[0].lower() for line in instructions]
        target_mentions = {target: sum(target in line for line in body) for target in TARGETS}
        call_count = sum(m == "call" for m in mnemonics)
        jump_count = sum(m.startswith("j") for m in mnemonics)
        supported = call_count == 0 and all(target_mentions[target] >= 1 for target in TARGETS)
        output = os.environ.get("GITHUB_OUTPUT")
        if output:
            with open(output, "a", encoding="utf-8") as f:
                f.write(f"decision={'tail_shape_supported' if supported else 'tail_shape_not_proven'}\n")
        return {
            "schema": "cmpct-one-g02-size-dispatch-tail-asm-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "compiler": os.environ.get("CC", "cc"),
            "instruction_count": len(instructions),
            "call_instruction_count": call_count,
            "jump_instruction_count": jump_count,
            "target_relocation_mentions": target_mentions,
            "decision": "tail_shape_supported" if supported else "tail_shape_not_proven",
            "claim_boundary": "static integration codegen only; no dynamic speed authority",
        }


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
