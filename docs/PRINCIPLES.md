# CMPCT design principles

1. **General before local.** Any real-world development corpus is evidence, never the format specification.
2. **Lossless means byte-exact.** A logical file must reconstruct to the original bytes unless the
   user explicitly asks for a lossy transform outside the CMPCT core contract.
3. **Measure, then select.** Representation choice is made from actual bytes and cost, not filename.
4. **Graceful worst case.** Incompressible/encrypted/random data should approach input size plus small
   structural overhead rather than suffering pathological expansion.
5. **Random access is first-class.** Better ratio is not worth turning the archive into a mandatory
   sequential stream.
6. **Filesystem fidelity is data.** Directories, permissions, times, links, sparse extents, ownership,
   xattrs and Unicode names need explicit semantics.
7. **Integrity is layered.** Cheap checks belong on hot reads; cryptographic verification remains
   available for strong validation.
8. **Recovery is designed, not improvised.** Critical metadata is redundant and physical blobs are
   self-describing enough for salvage.
9. **Mutations are transactional.** A failed write must not destroy the last committed generation.
10. **Parallel by construction.** Independent blobs/chunks should permit multicore encode/decode,
    verification, range serving and remote retrieval.
11. **Codec agility.** The CMPCT container must outlive any one compressor. Codecs and reversible
    transforms are versioned capabilities, not the identity of the format.
12. **Compatibility is an endpoint.** Import/export legacy formats rather than permanently carrying
    their limitations in every CMPCT archive.
13. **No benchmark laundering.** A claimed win must use equivalent durability, fidelity and integrity
    semantics, and must state when runtime/language overhead contaminates the result.
14. **No corpus overfitting.** Every optimization must be tested against heterogeneous and adversarial
    corpora, including cases where it should deliberately decline to act.
15. **Keep code notes.** Design footnotes in the reference implementation are intentional executable
    documentation and should not be silently deleted during refactors.
16. **Public CMPCT stands alone.** Private corpus identities, unrelated internal projects, personal
    information and private artifact provenance are not part of the format contract and must not leak
    into the public repository/site surface.
