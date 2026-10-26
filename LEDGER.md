# GPowerNT.exe evidence ledger

Target: `GPowerNT.exe` (G*Power 3.1.9.7), SHA-256 `c63e6a133eb6372932f810c08cc33dc35a06d1ddb658f897bd6c34a754efc812`.

Evidence discipline: `[DOK]` is stated in the contract/manual/paper; `[REA]` has binary evidence with an address or string reference; `[AJAN]` is an agent inference or GUI-only finding. Ghidra/REA analysis was private and is not copied to the repository. No decompiled code is reproduced here.

## Binary-backed findings

### [REA-016] Generic admissible-range validator

REA/Ghidra evidence: `ev_81e2f111b5f30c480207a80fde1ea9c8bd1e270e74e02b60d54739273d5bc341`, target digest above, Ghidra 12.1.4. Function `0x487b70` (`FUN_00487b70`) references the string fragments at `0x5c61b4` (`Effect size `) and `0x5c61d8` (` is outside the admissible range (`). Incoming string references include `0x487bcf` and `0x487c18`; the direct string xrefs returned by REA include `0x487c18` and `0x4882b3`.

The recovered function is a reusable range-check/error-reporting helper: it compares a supplied value with lower and upper double arguments and takes the refusal path when the value is below the lower bound or above the upper bound. This proves the binary has a real range predicate and constructs the observed message; it does not, by itself, prove which caller supplied the d bounds.

### [REA-017] Sample-size refusal string

REA/Ghidra string inventory found `Sample size is outside the admissible range (` at `0x5c64f4`; its incoming reference includes `0x48876c`. This is binary evidence that a sample-size admissibility/refusal path exists. A complete caller-specific minimum-group rule was not established, so the exact minimum policy remains unknown.

### [REA-018] Binary identity and coverage

REA/Ghidra overview observed PE x86, image base `0x400000`, 9,116 procedures, and 2,570 defined strings. The Ghidra import completed only with the private 900-second startup limit. These counts are inventory evidence, not proof that every semantic routine was identified.

## Earlier findings deliberately re-tagged as agent/oracle findings

The following IDs are retained for continuity, but are `[AJAN]`, not binary-proven. Each was confirmed by the listed oracle rows/evidence, not by a recovered binary address.

- `[AJAN] REA-001`: baseline a-priori output; confirmed by golden oracle rows 1–120.
- `[AJAN] REA-002`: post-hoc fields and boundary behavior; confirmed by post-hoc oracle rows 1–65.
- `[AJAN] REA-003`: unequal-ratio allocation; confirmed by ratio/search oracle rows.
- `[AJAN] REA-004`: a-priori result is not an exhaustive minimum-N integer search; confirmed by boundary oracle rows.
- `[AJAN] REA-005`: even-total search, start 4, step 2, first passing candidate; confirmed by search-observations.csv and golden rows.
- `[AJAN] REA-006`: unrounded ratio shares determine stopping and displayed integer sizes are applied afterward; confirmed by apriori-boundary and fixed-boundary rows.
- `[AJAN] REA-007`: observed exact-half group-1 upward rounding; confirmed by ratio-3 oracle rows with totals 10 and 18.
- `[AJAN] REA-008`: corrected held-out row 21; confirmed by the live G*Power rerun and corrected CSV row.
- `[AJAN] REA-009`: JSONL contract serialization; confirmed by the contract and generated oracle artifacts, not binary evidence.
- `[AJAN] REA-010`: 71 edge/error probes and proposed error-code mappings; confirmed by edge-error-probes.json, with mappings inferred.
- `[AJAN] REA-011`: 65 post-hoc observations; confirmed by posthoc-observations.json/jsonl.
- `[AJAN] REA-012`: 50 compromise observations; confirmed by compromise-observations.json/jsonl.
- `[AJAN] REA-013`: 50 criterion observations; confirmed by criterion-observations.json/jsonl.
- `[AJAN] REA-014`: 50 sensitivity observations; confirmed by sensitivity-observations.json/jsonl.
- `[AJAN] REA-015`: d boundary and corrected post-hoc values; confirmed by the 2026-10-26 live G*Power reruns.

## DOK formulas and unresolved implementation claims

- `[DOK]` For independent equal-variance groups, `df=n1+n2-2` and `ncp=d*sqrt(n1*n2/(n1+n2))`; the manual/paper describes central and noncentral Student-t distributions.
- `[DOK]` Contract field names and error-code definitions are in `contract.md`.
- `[AJAN]` The exact critical-t and power numerical implementation is inferred from oracle agreement; no binary address for the distribution routine was established.
- `[AJAN]` The a-priori loop start, step, stopping rule, ratio allocation, half-tie behavior, minimum group size, and bonus-mode inverse solvers remain oracle findings, not binary findings.
- `[AJAN]` The best contract mapping for G*Power's d>20 refusal is `NO_SOLUTION`: section 5 permits every d>0, while the binary/UI refuses values above 20. This taxonomy is inferred even though the binary contains the range-refusal string.

## Unknowns and boundaries

The binary evidence proves the generic range helper and refusal strings, but not the semantic caller-to-field mapping, the complete a-priori search loop, or the general allocation rounding policy. Those claims remain explicitly `[AJAN]` and must not be presented as decompiled facts.
