# CMPCT licensing status

> **NON-FINAL PROPOSAL — NOT YET ADOPTED**

The project is evaluating the **Apache License, Version 2.0** (`Apache-2.0`) as its initial public
open-source license. This document records the proposal without pretending that the legal adoption
step has already happened.

`LICENSE-APACHE-2.0-PROPOSED.txt` contains the unmodified Apache License 2.0 reference text. Its
presence under a deliberately `PROPOSED` filename is documentation of the intended license choice,
not a statement that every current repository revision has already been publicly licensed under it.

## Why Apache-2.0 is the current proposal

For a systems-format project, Apache-2.0 is attractive because it provides a permissive copyright
license, an express patent grant from contributors, contribution terms, redistribution conditions,
and a well-understood SPDX identifier while allowing commercial and proprietary use.

This is a project-design rationale, not legal advice.

## Adoption checklist

Before this proposal becomes the canonical project license:

1. confirm the copyright owner(s) and whether any ownership/assignment agreements affect the code;
2. audit third-party code, generated code, vendored material, test vectors and copied snippets for
   incompatible or additional license/notice obligations;
3. decide whether CMPCT needs a `NOTICE` file and populate it only with notices actually required;
4. confirm contribution policy and whether any contributor agreement or Developer Certificate of
   Origin process is desired;
5. review patent/trademark implications for the format name, implementation and contributed code;
6. rename/copy the proposed license text to the canonical top-level `LICENSE` file without modifying
   the Apache-2.0 terms;
7. update `README.md`, package metadata and public website data from “proposed” to “adopted” in the
   same reviewed change;
8. only then add project-wide SPDX/source headers where useful, while preserving third-party notices;
9. run the public-surface and release checks before making the repository/site public.

## Until adoption

Do **not** describe CMPCT releases, source files, binaries or the website as finally licensed under
Apache-2.0 solely because this proposal exists. Existing third-party licenses remain effective and
must be honored independently.

When the license is adopted, this file should become a short licensing/provenance guide rather than a
proposal disclaimer.
