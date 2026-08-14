# Agent instructions

This repository is the canonical CMPCT project.

- Optimize for arbitrary computer files and filesystems, not Hermes specifically.
- Hermes is one regression corpus only.
- Do not delete design footnotes/comments from code when rewriting or refactoring.
- Every code fix should include concise nearby commentary explaining why the fix exists when the
  invariant is non-obvious.
- Never claim a benchmark win without equivalent semantics and a reproducible test.
- Prefer adding a losing/adversarial corpus over tuning a threshold to one successful corpus.
- Keep the reader contract simpler than encoder heuristics: old archives must remain readable after
  encoder strategy changes once 1.0 is frozen.
- Treat malformed archives as hostile input. Bounds, path and resource-limit checks are mandatory.
- Preserve fallback behavior when optional native helpers/codecs are absent.
- Update `docs/FORMAT.md` in the same change as any on-disk format mutation.
