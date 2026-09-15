# A01 external prior-art boundary

Status: **research boundary / no product evidence**. Sources checked 2026-09-15 UTC.

A01's core idea — that a synthesized reference can outperform an observed member — is **not novel in the abstract**. The CMPCT research question is whether that idea can become a content-derived, exact, general-purpose arbitrary-data ownership mechanism with bounded product semantics.

## Direct adjacent evidence

1. **Brandon et al., 2009, “Data structures and compression algorithms for genomic sequence data”** (Bioinformatics; PMCID: PMC2705231). On 3,615 mitochondrial genomes, the paper reports 167 KB using the revised Cambridge observed reference versus **133 KB using a consensus sequence**, roughly **23% smaller**. This is strong evidence that a non-member/consensus reference can reduce referential residual cost in a real collection.
   - https://pmc.ncbi.nlm.nih.gov/articles/PMC2705231/

2. **Vertical lossless genomic data compression tools for assembled genomes: a systematic literature review** (2020; PMCID: PMC7250429) describes RCC as clustering target sequences and generating an **artificial consensus reference sequence** per cluster before reference compression. This establishes synthetic-reference ownership as prior art in a specialized genomic setting.
   - https://pmc.ncbi.nlm.nih.gov/articles/PMC7250429/

3. **GDC 2: Compression of large collections of genomes** (2015; PMCID: PMC4479802) and later collection compressors show that multi-reference / second-order reference structures can substantially outperform naive fixed-reference schemes. These are important controls against attributing every family-level win to a synthetic root when richer observed-reference ownership may suffice.
   - https://pmc.ncbi.nlm.nih.gov/articles/PMC4479802/

4. **CHAPAO** (2022; PMCID: PMC9015123) models sequence collections as a weighted encodability graph and chooses hierarchical reference relationships. It reinforces that reference ownership topology itself is a compression variable, not merely a codec parameter.
   - https://pmc.ncbi.nlm.nih.gov/articles/PMC9015123/

## CMPCT-specific boundary

A01 earns no “invented synthetic references” claim. Its potentially new/useful contribution must instead survive all of the following:

- arbitrary computer data rather than a known genomic alphabet/alignment;
- content-derived applicability without file extension, workload identity, schema or external biological reference;
- complete charging of synthetic root, residuals, descriptors, integrity and access/recovery semantics;
- comparison against CMPCT's strongest observed multi-root/Mosaic/resemblance mechanisms;
- bounded generic discovery/admission rather than an offline consensus gifted forever;
- safe fallback and negligible global carrying cost when no latent family exists.

## Consequence for O1

The O0 result is best interpreted as **independent confirmation that the A01 opportunity exists inside CMPCT's accounting model**, not as novelty proof. O1 must therefore be harder than the friendly oracle: it must establish transfer beyond aligned same-length substitution families and demonstrate a generic predictor/proposal mechanism that distinguishes latent-root opportunity from ordinary multi-reference or shared-context compression.

A failure there should retire or sharply narrow A01 even though synthetic references are known to work in specialized genomics.