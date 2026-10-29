# J24G28 — ZIP DOS timestamp portability repair preregistration

Date: 2026-10-29 UTC. State: **PREREGISTERED / BEFORE PRODUCT MUTATION**.
Current released authority: `main@80c358f8824ec1b20d349c92ed94c898090969b0`, v0.30.0, revision-24. Existing ZIP integration owner #492 exact `ca01d885fedc8ffc343b9c3c624eddd134158452`. This branch is a *stacked child* of that owner's branch, not an independent replacement ZIP writer.

## Problem / baseline

Original scientific J24G27 / #719 / tracking #721 recorded physically identical genuine signed-r24 input on Ubuntu, macOS and Windows: `mtime_ns=-1000000000` is read/verified on 3/3 hosts, yet `export_zip` fails on Windows with `OSError [Errno 22]` at `_zip_dos_time -> time.localtime`. Ordinary 2020 controls pass; original hosted run: https://github.com/FCMO-AI/.CMPCT/actions/runs/40796399439 . The current #492 stack inherits the same conversion.

## Hypothesis / disproof

H1: A preconversion check for dates preceding the representable ZIP DOS epoch, followed by a conventional **1980-01-01 00:00:00 local DOS** encoding, allows the existing ZIP fast writer to export signed pre-1970 genuine CMPCT metadata on all three hosts without invoking platform-local negative-epoch `localtime`. H2: Already-representable 2020 dates and arbitrary payload bytes remain identical to the inherited writer on the same host. H3: malformed/CRC-damaged input remains rejected under inherited #284/#492 protection and the staged destination is unchanged upon failure. H4: strong/weak checkpoint, direct-Deflate reuse, count-only ZIP64 and staged publication behavior are not changed by this narrowly scoped date conversion.

Kill/rollback: any changed 2020 output relative to the inherited parent for the identical input and environment, any change to file/read/verify acceptance, any positive date outside DOS range, any failure to retain #492 staged publication safety, or any OS still failing the signed-date input. Generic CI green alone cannot earn product credit.

## Cheapest decisive evidence

Use the previously hosted J24G27 genuine physical signed-r24 fixture produced on Ubuntu, carrying the exact source/index/physical SHA in an artifact manifest, **not a host-local negative os.utime on Windows**. Run candidate Reader from the exact source HEAD on Ubuntu/macOS/Windows with the *same physical input*, twice per host in fresh processes; verify content, archived signed mtime, ZIP bytes and DOS timestamp using Python stdlib. Produce same-host inherited-parent comparison for the 2020 control; no cross-host ZIP-byte equality claim because ZIP DOS timestamps are local. For affected timestamp test expected DOS 1980-01-01 00:00:00. Check only the source materialization from Git HEAD, allowing Git-for-Windows CRLF normalization as a separately reported reversible transform.

## Alternative explanations and whole-system debt

Existing platform failure might arise from packaging, physical Builder timestamps, Reader corruption, or output path: control these with byte-identical fixed archive SHA, raw member SHA, generation index and ordinary-2020 ZIP export. The candidate does not make ZIP timestamps nanosecond-exact and does not repair the inherited #284 trailing-Deflate compatibility gap, #492 stage-path concurrency race, or count/global ZIP64 metadata differences. Do not weaken any gates, do not promote until whole stack has review and full exact-head CI. Do not change `docs/discovery/STATE.json` (independently owned under #574).