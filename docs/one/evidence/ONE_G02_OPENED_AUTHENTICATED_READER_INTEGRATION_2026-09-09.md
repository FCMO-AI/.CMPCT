# ONE-G0.2 shared-open authenticated reader integration

Date: 2026-09-09  
Status: engineering integration green; inherits `ADVANCE_VALIDATED_AUTHENTICATED_LIFECYCLE`

## Exact source / CI truth

- source: `9d082b3c8aa27b4120cfedfa7978eaee8051f958`
- commit: `feat(one): bind shared-open authenticated reader`
- workflow: `CMPCT1 ONE-G0.2 opened authenticated reader`
- run: `34397358283`
- job: `102620244461`
- result: **SUCCESS**
- exact-source checkout: PASS
- tests: **63 passed in 1.83 s**

This is an engineering integration receipt, not a new performance promotion. The performance authority remains `ONE_G02_VALIDATED_AUTHENTICATED_SELECTIVE_LIFECYCLE_RESULT_2026-09-09.md`.

## Integrated surface

`experiments/one/opened_authenticated_reader.py` now exposes one shared-open research reader:

`open_authenticated_reader(program, root_name, tree, expected_root)`

Open performs:

1. expected authentication commitment shape/equality check;
2. immutable Program snapshot;
3. complete global ONE shape/resource preflight once;
4. economically compact node-length proof retention when safe/smaller;
5. selected-root existence and AuthTree length binding.

The returned opaque `OpenedAuthenticatedReader` is sealed and repeated `.read(start, length)` calls use the already-promoted validated authenticated native cone path. Every read still authenticates the reconstructed leaf payloads against the same bound root commitment. No whole-root reconstruction/hash shortcut is introduced.

## Hostile/invariant coverage

The dedicated tests verify:

- repeated selective ranges reconstruct exact reference bytes;
- AuthTree/index statistics remain visible;
- mutating the caller-owned root mapping after open cannot change the sealed snapshot authority;
- wrong expected authentication commitment fails at open;
- an AuthTree for the wrong root length fails at open;
- unknown root selection fails at open;
- inherited validation/native-range/selective-authentication tests remain green.

## Scope boundary

This API deliberately represents the **shared/repeated-open** case whose economics advanced. It does not replace the simple raw one-shot helper. The lifecycle falsifier showed worst one-shot cost at `1.248532x` raw; preserving both call surfaces is therefore an economic boundary, not a representation portfolio. Both execute the same ONE grammar and the same authenticated cone semantics.

## Next research target

Do not spend another experiment proving that sealed validation can be reused. The next reader question is route economics at the interface boundary: when a caller explicitly opens a shared reader, use the reusable authority; when the request is genuinely one-shot, retain the simple raw path unless future evidence shows a universally cheaper open strategy.

Future optimization should focus on the remaining per-cone plan/source/proof preparation cost and generic topology coverage, not Law-specific decode mechanisms.
