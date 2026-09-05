"""Builder-independent semantic oracle for ONE-G0.1 tests.

This intentionally does not import ONE IR or VM classes. Its tiny tuple language exists
only to independently derive expected bytes for the frozen semantic vectors.
"""
from __future__ import annotations


def evaluate(spec: tuple[tuple, ...]) -> tuple[bytes, ...]:
    values: list[bytes] = []

    def ref(item: tuple[int, int, int | None]) -> bytes:
        node, start, length = item
        source = values[node]
        return source[start:] if length is None else source[start : start + length]

    for item in spec:
        op = item[0]
        if op == "surprise":
            value = bytes(item[1])
        elif op == "concat":
            refs, tail = item[1], item[2]
            value = b"".join(ref(r) for r in refs) + bytes(tail)
        elif op == "repeat":
            value = ref(item[1]) * item[2]
        elif op == "fill":
            value = bytes([item[1]]) * item[2]
        elif op in {"xor", "add8"}:
            parts = [ref(r) for r in item[1]]
            if item[2]:
                parts.append(bytes(item[2]))
            if not parts or any(len(part) != len(parts[0]) for part in parts[1:]):
                raise ValueError("oracle operands differ in length")
            if op == "xor":
                acc = bytearray(len(parts[0]))
                for part in parts:
                    for index, byte in enumerate(part):
                        acc[index] ^= byte
                value = bytes(acc)
            else:
                value = bytes(sum(part[index] for part in parts) & 0xFF for index in range(len(parts[0])))
        else:
            raise ValueError(f"unknown oracle operation {op!r}")
        values.append(value)
    return tuple(values)
