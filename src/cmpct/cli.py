from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main():
    # Footnote: imports are intentionally command-local. A user opening or extracting an archive
    # should not pay startup/import cost for the encoder, transaction mutator and hostile-preflight
    # implementation before a single byte is read. ZIP's mature tooling has very low launch overhead;
    # keeping these dependency cones separate is part of making CMPCT competitive as a boring default.
    ap = argparse.ArgumentParser(prog="cmpct")
    sp = ap.add_subparsers(dest="cmd", required=True)

    p = sp.add_parser("create")
    p.add_argument("source")
    p.add_argument("archive")
    p.add_argument("--workers", type=int, default=None,
                   help="deterministic candidate-encode workers; CLI default is 1 to avoid fresh-process thread startup, pass N to opt in")
    p.add_argument("--reproducible", action="store_true",
                   help="normalize host-owned metadata and use SOURCE_DATE_EPOCH for byte-reproducible builds")

    for command in ("info", "list", "verify", "preflight"):
        p = sp.add_parser(command)
        p.add_argument("archive")

    p = sp.add_parser("cat")
    p.add_argument("archive")
    p.add_argument("member")

    p = sp.add_parser("range")
    p.add_argument("archive")
    p.add_argument("member")
    p.add_argument("start", type=int)
    p.add_argument("length", type=int)
    p.add_argument("-o", "--output")

    p = sp.add_parser("extract")
    p.add_argument("archive")
    p.add_argument("dest")
    p.add_argument("--no-metadata", action="store_true")
    p.add_argument("--max-bytes", type=int)
    p.add_argument("--unsafe-symlinks", action="store_true")

    p = sp.add_parser("export-zip")
    p.add_argument("archive")
    p.add_argument("output")
    p.add_argument("--level", type=int, default=6)

    p = sp.add_parser("update")
    p.add_argument("archive")
    p.add_argument("member")
    p.add_argument("source")

    p = sp.add_parser("delete")
    p.add_argument("archive")
    p.add_argument("member")

    p = sp.add_parser("rename")
    p.add_argument("archive")
    p.add_argument("old")
    p.add_argument("new")

    p = sp.add_parser("recover-blobs")
    p.add_argument("archive")

    p = sp.add_parser("compact")
    p.add_argument("archive")
    p.add_argument("output")

    a = ap.parse_args()

    if a.cmd == "create":
        from .builder import Builder

        # Footnote: Builder's library API keeps its parallel default because long-running/in-process
        # callers amortize thread-pool setup and measured workloads often benefit strongly. A fresh
        # `cmpct create` process is different: the v0.28 ABBA gate found a small media tree paying a
        # ~10 ms thread-startup tax while its actual library work moved by <1 ms. Keep CLI creation
        # serial unless the caller explicitly requests workers; this restores the low-latency default
        # without deleting deterministic parallel creation for batch/large-workload users.
        workers=1 if a.workers is None else a.workers
        builder=Builder(Path(a.source),workers=workers,reproducible=a.reproducible)
        print(json.dumps(builder.build(Path(a.archive)), indent=2))
        return
    if a.cmd in {"update", "delete", "rename", "recover-blobs", "compact"}:
        from .transactions import append_delete, append_rename, append_update, compact_archive, recover_blob_records

        if a.cmd == "update":
            print(json.dumps(append_update(Path(a.archive), a.member, Path(a.source)), indent=2))
        elif a.cmd == "delete":
            append_delete(Path(a.archive), a.member)
        elif a.cmd == "rename":
            append_rename(Path(a.archive), a.old, a.new)
        elif a.cmd == "recover-blobs":
            print(json.dumps(recover_blob_records(Path(a.archive)), indent=2))
        else:
            print(json.dumps(compact_archive(Path(a.archive), Path(a.output)), indent=2))
        return
    if a.cmd == "preflight":
        from .validation import preflight_archive

        # Footnote: preflight is intentionally an explicit command in this first parser-hardening
        # increment. That lets us fuzz and benchmark the structural gate before making every hot-path
        # open pay for it, while recover-blobs remains independent for severely damaged archives.
        print(json.dumps(preflight_archive(Path(a.archive)), indent=2))
        return

    from .codec import K_DIR
    from .reader import CMPCT

    with CMPCT(Path(a.archive)) as ar:
        if a.cmd == "info":
            print(json.dumps({
                "version": ar.index["v"],
                "files": sum(x[1] != K_DIR for x in ar.files),
                "dirs": sum(x[1] == K_DIR for x in ar.files),
                "blobs": len(ar.blobs),
                "virtual_archives": len(ar.recipes),
                "features": ar.index.get("features", []),
            }, indent=2))
        elif a.cmd == "list":
            for x in ar.files:
                print(f"{x[4]:>12}  {x[0]}")
        elif a.cmd == "verify":
            print(f"verified {ar.verify()} logical files")
        elif a.cmd == "cat":
            sys.stdout.buffer.write(ar.read(a.member))
        elif a.cmd == "range":
            b = ar.read_range(a.member, a.start, a.length)
            Path(a.output).write_bytes(b) if a.output else sys.stdout.buffer.write(b)
        elif a.cmd == "extract":
            ar.extractall(
                Path(a.dest),
                metadata=not a.no_metadata,
                max_bytes=a.max_bytes,
                safe_symlinks=not a.unsafe_symlinks,
            )
        elif a.cmd == "export-zip":
            print(ar.export_zip(Path(a.output), a.level))


if __name__ == "__main__":
    main()
