# O61-D preregistration — Win32 directory named-$DATA source completeness

Date: 2026-10-25 UTC. Status: **prospective, independent low-cost falsifier; no product fix authorized by this document**.

## Authority and frozen starting point

- O57 owner [PR #413](https://github.com/FCMO-AI/.CMPCT/pull/413), exact base HEAD `d9f9fa724c139c6281f0e2a92c66601bee912618`, Builder blob `7a13545c7dc22ea973f90930fae6cf053f13f1f2`, Win32 source guard blob `23207ac06797fb21322cf327e97928fdbb5241c2`.
- Shipped CMPCT v0.30.0 and revision-24 archive layout unchanged. O57 protects **regular files** only, with controls on three hosts; its result explicitly leaves directory named streams unmeasured.
- Primary external source: Microsoft [MS-FSCC 5.1 NTFS Streams](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-fscc/c54dec26-1551-4d3a-a0ea-4fa40f848eb3), which says directories have no default unnamed data stream but **can carry named data streams**.
- Separate O52 mutable-tree custody, O60 deferred ZIP source coherency, and O57 regular-file admission are owned elsewhere. Do not modify their branches or weaken their gates.

## One primary research question

**Can an O57 installed Builder return successful, SHA-verifiable r24 output while silently omitting a named NTFS $DATA stream attached to a stable *nested directory* in the source tree?**

### Prospective prediction / hard disproof

1. On a Windows-2025 NTFS source tree with one nested directory, create an actual named data stream on the nested directory, then independently verify the named stream through Windows `FindFirstStreamW/FindNextStreamW`, re-read its bytes, and confirm it is not a regular child file in `os.scandir()`.
2. Run the actual source-exact O57 installed Builder and actual Reader on that untouched tree. **If it succeeds**, require valid archive verification, exact regular child reconstruction and *absence* of the nested directory's named stream in the extracted tree. This is a positive confirmation of silent source-completeness loss. No SHA cryptographic break is claimed.
3. If Builder refuses the directory, if the source stream is not constructible/enumerable on the runner, or if the restored stream is preserved, **do not claim defect confirmed**. Distinguish policy refusal, source-host unsupported/infrastructure, and successful faithful representation. No skip/no fake PASS for a missing Windows NTFS primitive.
4. Separate control: an ordinary nested directory without named streams must produce an exact reconstructible archive. Original O57 regular-file ADS refusal tests execute unchanged as inheritance.

The test must use authentic installed CMPCT (not a mocked Builder) and must record actual executed pytest/JUnit cases and source blobs. A test which anticipates the defect is a *falsifier*, not an approval test of the product; an observed loss is a scientific PASS and a product FAILURE.

## BONK / alternative mechanisms

- Simpler control: directory has no named stream -> succeeds and extracts.
- Competing explanation: NTFS cannot create directory streams on the runner -> classify an evidence limitation, not a proof of safety.
- More expensive alternatives (full Windows ACL audit; cross-file-system replication; format extension) do not precede the binary native Windows falsifier.
- Research has no meaningful compressor/memory/performance accounting and cannot authorize promotion. If defect confirmed, the smallest plausible response is fail-closed admission for named directory data streams, taking care that directories lack the ordinary `::$DATA` default stream and that the **root directory** has a separate source-contract question.

## Promotion / continuity

This result may justify a new, separately owned small Builder guard and a real product re-run including O47/O48/O50/O57. Do not modify O57 owner's Builder, helper, frozen benchmark, version or release gates in O61-D. Keep negative observations and any Windows API host limitation. Leave `docs/discovery/STATE.json` untouched unless a decision-changing result is obtained.
