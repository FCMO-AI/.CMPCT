from __future__ import annotations

import atheris

with atheris.instrument_imports():
    from cmpct.resemblance import delta_decode


def TestOneInput(data: bytes) -> None:
    # Split one fuzz buffer into an arbitrary base and arbitrary opcode stream. The small output cap is
    # intentional: this target is about parser/bounds correctness, not allocating whatever a malicious
    # varint asks for.
    if not data:return
    split=data[0] % len(data)
    base=data[1:1+split];payload=data[1+split:]
    try:
        delta_decode(base,payload,max_output=256*1024)
    except ValueError:
        return


if __name__=='__main__':
    atheris.Setup(__import__('sys').argv,TestOneInput)
    atheris.Fuzz()
