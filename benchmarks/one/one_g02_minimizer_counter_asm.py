"""ONE-G0.2 causal companion: inspect generated hot-loop division instructions.

This is architecture/compiler evidence only. It does not replace elapsed A/B evidence.
The exact same CI compiler builds the promoted tail-aware baseline and the counter Builder,
then objdump extracts each target function and counts integer div/idiv mnemonics. The result
supports the bookkeeping explanation only when the baseline contains at least one integer
division instruction and the counter Builder contains none.
"""
from __future__ import annotations
import json, os, re, subprocess, tempfile
from pathlib import Path


def _compile(source: Path, output: Path) -> None:
    subprocess.run([os.environ.get("CC","cc"),"-O3","-std=c11","-c",str(source),"-o",str(output)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)


def _function_assembly(obj: Path, symbol: str) -> list[str]:
    text=subprocess.run([os.environ.get("OBJDUMP","objdump"),"-d","--no-show-raw-insn",str(obj)],check=True,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE).stdout
    lines=text.splitlines(); start=None
    for i,line in enumerate(lines):
        if re.search(rf"<{re.escape(symbol)}>:$",line.strip()): start=i+1; break
    if start is None: raise RuntimeError(f"symbol not found in objdump: {symbol}")
    body=[]
    for line in lines[start:]:
        stripped=line.strip()
        if re.search(r"^[0-9a-f]+ <[^>]+>:$",stripped): break
        if stripped: body.append(stripped)
    return body


def _mnemonics(lines: list[str]) -> list[str]:
    out=[]
    for line in lines:
        match=re.match(r"^[0-9a-f]+:\s+([a-zA-Z][a-zA-Z0-9.]*)",line)
        if match: out.append(match.group(1).lower())
    return out


def run() -> dict[str, object]:
    here=Path(__file__).parent
    with tempfile.TemporaryDirectory(prefix="cmpct-one-g02-counter-asm-") as td:
        td_path=Path(td); tail_obj=td_path/"tail.o"; counter_obj=td_path/"counter.o"
        _compile(here/"one_g02_minimizer_segmented_tail_kernel.c",tail_obj)
        _compile(here/"one_g02_minimizer_segmented_counter_kernel.c",counter_obj)
        tail_mnemonics=_mnemonics(_function_assembly(tail_obj,"one_g02_minimizer_segmented_tail_kernel"))
        counter_mnemonics=_mnemonics(_function_assembly(counter_obj,"one_g02_minimizer_segmented_counter_kernel"))
        div_names={"div","divl","divq","idiv","idivl","idivq"}
        tail_divs=sum(m in div_names for m in tail_mnemonics); counter_divs=sum(m in div_names for m in counter_mnemonics)
        supported=tail_divs>=1 and counter_divs==0
        decision="division_removal_mechanism_supported" if supported else "division_removal_mechanism_not_proven_by_static_codegen"
        output=os.environ.get("GITHUB_OUTPUT")
        if output:
            with open(output,"a",encoding="utf-8") as f:
                f.write(f"decision={decision}\n")
                f.write(f"baseline_divs={tail_divs}\n")
                f.write(f"counter_divs={counter_divs}\n")
        return {"schema":"cmpct-one-g02-minimizer-counter-asm-v1","experimental_version":"ONE-G0.2","source_sha":os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound","compiler":os.environ.get("CC","cc"),"baseline_instruction_count":len(tail_mnemonics),"counter_instruction_count":len(counter_mnemonics),"baseline_integer_division_instructions":tail_divs,"counter_integer_division_instructions":counter_divs,"decision":decision,"claim_boundary":"same-compiler runner static causal companion only; elapsed A/B remains primary performance evidence"}


if __name__=="__main__": print(json.dumps(run(),sort_keys=True,indent=2))
