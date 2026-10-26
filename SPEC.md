# Clean-room specification: independent-samples t test

Status: investigation-only draft. This is the implementation contract for a later clean-room coding session. It contains no implementation code and no binary/decompiler output.

## 1. Scope and non-goals

Assigned family: `t2-indep`, the independent-samples t test (difference between two independent means; drug versus placebo). Primary workflow: a priori power analysis for required sample size. The teacher brief also requires post hoc mode, but its complete parameter contract is missing.

Non-goals: paired t tests, ANOVA, chi-square, multiple regression, clinical decisions, patient data, and reproducing G*Power source or binaries. The result must not be named or presented as G*Power.

## 2. Requirements extracted from the teacher brief

- CLI is mandatory and JSON output is one line.
- Hidden tests require exact integer agreement for `N`, `n1`, and `n2`; the brief states at least 90% exact agreement for `N`.
- Other numeric outputs must match G*Power's displayed precision.
- One calculation engine is shared by CLI, MCP, and optional agent wrappers.
- scipy or an equivalent distribution library is allowed; search, rounding, and degrees-of-freedom behavior must be evidenced.
- At least 30 G*Power vectors with screenshots are required, plus guide examples and a larger library-comparison set.
- Required submission artifacts include a spec, evidence ledger, hallucination log, agent-cost log, prompts, oracle vectors/screenshots, source, tests, and README.
- Reference application: G*Power 3.1.9.7 for Windows. The executable must not be committed.

Source read: `C:\Users\ASUS_PC\Downloads\2026-10-16-odev-supp`. It references a `CONTRACT.md` that was not available.

## 3. CLI contract

The only exact syntax supplied is:

```text
gpower-clone --test t2-indep --mode a-priori --tails 2 --d 0.5 --alpha 0.05 --power 0.95 --ratio 1
```

The supplied example output is:

```json
{"n1":105,"n2":105,"n_total":210,"actual_power":0.9501,"critical":1.9714,"df":208,"ncp":3.6228}
```

This is a teacher-provided contract/example, not an observation made here. No other flags, post hoc syntax, JSON fields, or numeric exit code may be invented until the missing `CONTRACT.md` is supplied. Invalid input must produce `{"error":"<description>"}` and a nonzero exit status.

## 4. Supported modes

Required selector: `t2-indep`. Required modes: `a-priori` and `post hoc`. GUI observation `[REA-002]` establishes post hoc inputs `tails`, `d`, `alpha`, `n1`, and `n2`, and outputs `actual_power`, `critical`, `df`, and `ncp` in addition to the sample-size values. The exact CLI flag spelling for post hoc remains unresolved. Tail selection supports one and two in the observed GUI.

## 5. Inputs and validation

Named inputs are `tails`, `d`, `alpha`, `power`, and `ratio`: tail choice, standardized mean difference, significance level, target power, and allocation ratio N2/N1. A priori also needs test and mode.

The brief requires testing very small/large `d`, power equal to or below alpha, unequal ratios, invalid values, and rounding. It does not state accepted bounds or exact messages. Bounds, zero/negative behavior, missing values, decimal parsing, locale behavior, stale output, and recalculation rules remain unresolved until GUI evidence and the missing contract exist.

## 6. Outputs and formatting

For the example, field names and types are integer `n1`, `n2`, `n_total`, `df`; decimal `actual_power`, `critical`, `ncp`. Four decimal places are shown for decimals, but a general precision rule is not specified. Keep one-line JSON and the documented number types. Do not infer hidden fields.

## 7. Mathematical definitions

The official G*Power 3.1 manual documents this as an independent, normally distributed two-group t test with equal population variances; it is not Welch's test. It defines `d = (mu1 - mu2) / sigma`, with conventional reference values 0.2, 0.5, and 0.8. The manual documents a central Student t null distribution and a noncentral Student t alternative distribution with `df = N - 2` and:

```text
df = n1 + n2 - 2
ncp = d * sqrt(n1*n2 / (n1+n2))
```

These are `[DOK]` facts from the official manual, not `[REA]` observations of the installed application. Exact sign handling, one-tail direction, critical quantile, numerical method, inverse search, allocation rounding, and version-specific validation must still be established against G*Power 3.1.9.7.

## 8. Allocation and rounding

GUI observations `[REA-003]`, `[REA-005]`, `[REA-006]`, and `[REA-007]` establish the displayed allocation rule: preserve the candidate total, assign group 1 the nearest integer to its total-weight share, and assign group 2 the remainder so that `n1+n2=N`. This is not equivalent in general to rounding `n1*ratio`. For the observed exact half ties at ratio `3` (`N=10` and `N=18`), group 1 rounds upward: `(2.5,7.5)` becomes `(3,7)` and `(4.5,13.5)` becomes `(5,13)`. Tie behavior for other exact-half configurations, extreme ratios, and values outside the observed range remains inferred.

### [REA] Exact a-priori search procedure

For a-priori analysis, search over total sample size `N`, not over `n1`. Begin at `N=4` and advance by exactly `2`; odd totals are not candidates. At each candidate, use the real-valued ratio-weighted group shares for the stopping calculation. Stop at the first candidate whose power reaches the requested target using those unrounded shares. Only after stopping, round the two shares to displayed integer group sizes while preserving `n1+n2=N`; report power recomputed for those displayed integers. Therefore the displayed actual power can be slightly below the requested target, and a post hoc calculation for the displayed previous/equal pair is not the a-priori stopping criterion (`[REA-004]`, `[REA-005]`, `[REA-006]`).

The start value and step are directly supported by the high-effect `N=4` boundary probes and targeted observations. The unrounded-share stopping criterion is observed indirectly through repeated boundary pairs; the exact internal numerical implementation is inferred. No extra minimum-group-size rule explains the `N=18` case: the displayed `N=16` pair is valid post hoc but its unrounded-share stopping power is below target. General half-tie behavior and behavior outside the observed ratio/effect domain remain inferred.

### [REA-007] Exact-half allocation tie behavior

Two held-out mismatches isolate the tie rule without changing the stopping total. For one-tailed `d=1.5`, alpha `.05`, target power `.8`, ratio `3`, G*Power returns `(n1,n2,N)=(5,13,18)`; for one-tailed `d=2`, with the same alpha, target, and ratio, it returns `(3,7,10)`. Both totals produce an exact `.5` group-1 share. The builder’s ties-to-even allocation returned `(4,14)` and `(2,8)` respectively. Existing G*Power observations in `docs/search-observations.csv` support these same two tie cases. The observed compatibility rule is group-1 half-up rounding with group 2 as the total-preserving remainder; a universal rule for every possible tie representation remains inferred.

## 9. Errors and edge cases

Required experiments cover missing, zero, negative, out-of-range, and decimal values; invalid ratios/sample sizes; stale outputs after invalid calculation; edit-without-Calculate; and displayed precision. These edge cases remain unresolved. The known CLI behavior is nonzero exit plus an `error` JSON object for invalid input. GUI post hoc behavior is documented by `[REA-002]`.

## 10. Conformance examples

The teacher example is `[DOK/ASSIGNMENT-EXAMPLE]` and is independently reproduced by `[REA-001]`. Public GUI vectors are in `golden_vectors.csv` (120 rows); private held-out GUI vectors are in `held_out_vectors.csv` (50 rows). Ratio evidence is `[REA-003]`; post hoc evidence is `[REA-002]`; search evidence is `[REA-005]` and `[REA-006]`, with boundary observations in `docs/apriori-boundary-observations.csv` and fixed-size checks in `docs/fixed-boundary-observations.csv`. The official manual's chapter-21 text is `[DOK/MANUAL-CH21]`; it documents the model and formulas but is not GUI evidence.

## 11. Acceptance criteria

- Implement the exact flags/schemas from the missing contract.
- Support a priori and post hoc modes.
- Match oracle integers for `n1`, `n2`, and `n_total`.
- Match displayed decimal precision.
- Match observed boundary and invalid-input behavior.
- Report differential mismatches rather than hiding them.
- Make CLI and MCP identical for identical inputs.
- Commit no G*Power binary or decompiler output.

Gherkin scenarios cannot be completed until the missing contract and oracle observations exist.

## 12. Architecture

Use one pure calculation engine. CLI parses flags and serializes results; MCP adapts the same schema. The optional Turkish-language agent only selects a test and gathers parameters; it must never calculate N, power, or effect size.

## 13. Clean-room and licensing restrictions

Only permitted black-box GUI observations may inform `[REA]` records. Do not decompile/disassemble for this phase, copy code, commit `GPower.exe`, or include decompilation output. Cite Faul, Erdfelder, Lang, and Buchner as required. Use fictional scenarios only.

## 14. Limitations and assumptions

The complete MCP contract, lecture slides, exact post hoc CLI flags, general half-tie allocation behavior, and several invalid-input/UI behaviors remain unresolved. The official manual was consulted online at https://www.psychologie.hhu.de/fileadmin/redaktion/Fakultaeten/Mathematisch-Naturwissenschaftliche_Fakultaet/Psychologie/AAP/gpower/GPowerManual.pdf. GUI-specific claims added here are limited to `[REA-001]` through `[REA-007]` and their existing artifacts.

## 15. Contract-aligned REA addendum (2026-10-25)

This section supersedes the earlier missing-contract statements. The teacher contract is present as `contract.md`; the selected family is `t2-indep`. Contract field names are used exactly in the JSONL artifacts.

### [REA-008] Corrected held-out oracle

Live G*Power rerun: `tails=1,d=.6,alpha=.025,power=.9,ratio=.6` returned `n1=80,n2=48,n_total=128,df=126,ncp=3.2863353,critical_t=1.9789706,actual_power=.9034086`. Held-out CSV row 21 was corrected from stale unrelated values. This is an oracle-recording correction, not a numerical inference.

### [REA-009] Contract serialization

Each JSONL row is `{id,input,expected}`. `input` contains `test`, `mode`, and the mode-specific contract fields. For t2-indep a-priori, outputs are `ncp,critical_t,df,n1,n2,n_total,actual_power`; post-hoc outputs are `ncp,critical_t,df,power`; compromise adds `alpha,beta,power`; criterion returns `alpha`; sensitivity returns `d`. CSV `delta`, `crit_t`, and `N` map to `ncp`, `critical_t`, and `n_total`.

### [REA-010] Validation and edge probes

Seventy-one fresh live GUI probes are recorded in `docs/edge-error-probes.json` (51 result records, 20 visible input-error records). `power < alpha` opens an input error stating that power must be greater than or equal to alpha; `power=alpha` is accepted; alpha as small as `.0000001` is accepted; `d=.001,.01,5,10,20` and ratios `.01,100` are accepted; `d=100` is refused as outside the admissible range. Post-hoc minimum-group probes with `n1/n2=2` and very large n were also recorded.

The following contract-code mappings are inferred because G*Power exposes no contract codes: `power < alpha` -> `INCONSISTENT` (field `power`); d outside the displayed admissible range -> `OUT_OF_RANGE` (field `d`); a valid-domain `?` result -> `NO_SOLUTION`. `power=alpha`, tiny alpha, accepted extreme d, and extreme ratios are successful observations. No clamp was observed. Exact endpoint and message mapping remains inferred.

### [REA-011] Post-hoc observations

Sixty-five fresh G*Power post-hoc observations are in `docs/posthoc-observations.json` and its non-held-out JSONL companion. They include both tails, unequal groups, `n1/n2=2`, small and large effects, and n through 7000. Each records `ncp`, `critical_t`, `df`, and `power`. The section-9 t2-indep post-hoc vector was directly rechecked and matches. Distribution and inverse-solver implementation details beyond these records are inferred.

### [REA-012] Compromise mode

Fifty fresh observations, including both tails and unequal groups, are in `evidence/observations/compromise-observations.jsonl`. The section-9 compromise vector matches `ncp=3.3166248,critical_t=1.6606859,df=174,alpha=.0492887,beta=.0492887,power=.9507113`. Formula details beyond observed outputs are inferred.

### [REA-013] Criterion mode

Fifty fresh observations, including both tails and unequal groups, are in `evidence/observations/criterion-observations.jsonl`. The section-9 criterion vector matches `ncp=3.3166248,critical_t=1.6676050,df=174,alpha=.0485965`. Remaining inverse-solver details are inferred.

### [REA-014] Sensitivity mode

Fifty fresh observations, including both tails and unequal groups, are in `evidence/observations/sensitivity-observations.jsonl`. The section-9 sensitivity vector matches `ncp=3.3025887,critical_t=1.6536580,df=174,d=.4978840`. Extreme `?` displays are observed UI no-result behavior; the exact failure boundary is inferred.

### Contract error table

The contract defines `MISSING_PARAM`, `UNKNOWN_PARAM`, `INVALID_VALUE`, `OUT_OF_RANGE`, `INCONSISTENT`, `UNSUPPORTED`, and `NO_SOLUTION`. The observed-to-code proposals above are inferred. JSONL error cases retain the actual visible message; no error text or numeric result was fabricated.

### Held-out separation

`held_out_final.jsonl` contains 30 fresh a-priori rows, 20 fresh post-hoc rows, and 15 live error probes. It remains only in RE. Only `SPEC.md`, `golden_vectors.jsonl`, and non-held-out post-hoc/bonus JSONL rows are copied to `RE-impl`.

### [REA-015] Post-hoc corrections and the d boundary

Fresh visible G*Power reruns filled the two previously missing post-hoc records:

| ID | Input | Observed output |
|---|---|---|
| `observed-017` | tails=2, d=.5, alpha=.01, n1=8, n2=28 | `ncp=1.2472191`, `critical_t=2.7283944`, `df=34`, `power=.0826020` |
| `observed-020` | tails=2, d=.8, alpha=.05, n1=17, n2=43 | `ncp=2.7923706`, `critical_t=2.0017175`, `df=58`, `power=.7840379` |

The d-boundary probe tested `19,19.9,19.99,20,20.000001,20.01,20.1,100` in live a-priori G*Power. Values through and including `d=20` computed successfully; at `d=20`, G*Power displayed `n1=2,n2=2,n_total=4,df=2,ncp=20.0000000,critical_t=2.9199856,actual_power=1.0000000`. Every tested value above 20, including d=100, produced a modal input refusal with the exact visible text: `Effect size d is outside the admissible range (-20, 20).` No silent clamp was observed. The same refusal was recorded for both d=100 held-out inputs.

The contract’s section 5 says only `d > 0`, so d=100 is contract-valid but reference-incomputable. Therefore the proposed contract mapping is `NO_SOLUTION`, field `d` (**inferred**); `OUT_OF_RANGE` would describe G*Power’s UI bound but not the contract’s declared range. Held-out error rows 003 and 004 now carry `NO_SOLUTION` while preserving the observed message. The distinction between reference UI rejection and contract-range rejection remains an inference about the best code taxonomy.
