"""Independent pure-stdlib J24V01 logical-SHA oracle; never imports CMPCT.

Prospective decision: incremental holes + extents must hash exactly like a fully
materialized logical byte stream. This test does not earn product or RSS credit.
"""
import hashlib
import json
import random


def streaming(size, extents):
    digest = hashlib.sha256()
    zero = bytes(1024 * 1024)
    pos = 0

    def append_zeros(length):
        while length:
            n = min(length, len(zero))
            digest.update(zero if n == len(zero) else zero[:n])
            length -= n

    for off, payload in extents:
        if off < pos or not payload or off + len(payload) > size:
            raise ValueError("invalid extent geometry")
        append_zeros(off - pos)
        digest.update(payload)
        pos = off + len(payload)
    append_zeros(size - pos)
    return digest.digest()


def main():
    rng = random.Random(240126)
    passed = 0
    for _ in range(1500):
        size = rng.randrange(0, 262144)
        full = bytearray(size)
        extents = []
        pos = 0
        for _ in range(rng.randrange(0, 16)):
            if pos >= size:
                break
            off = rng.randrange(pos, size)
            n = rng.randint(1, min(4096, size - off))
            payload = rng.randbytes(n)
            full[off:off + n] = payload
            extents.append((off, payload))
            pos = off + n
        assert streaming(size, extents) == hashlib.sha256(full).digest()
        passed += 1
    rejected = 0
    for size, extents in ((6, [(0, b"abcd"), (3, b"xy")]),
                          (3, [(0, b"1234")]), (3, [(0, b"")])):
        try:
            streaming(size, extents)
        except ValueError:
            rejected += 1
        else:
            raise AssertionError("invalid extent accepted")
    print(json.dumps({"schema": "j24v01-stdlib-digest-oracle-v1",
                      "seed": 240126, "cases": passed, "invalid_rejected": rejected,
                      "result": "PASS"}))


if __name__ == "__main__":
    main()
