# G*Power GUI evidence captured 2026-10-25

These records come from visible interaction with G*Power 3.1.9.7. No binary inspection was used. Screenshots are under `evidence/`.

## [REA-001] Baseline a-priori calculation

- Experiment: independent means, a priori, two tails; establishes the baseline and output precision.
- Inputs: `d=0.5`, `alpha=0.05`, target power `0.95`, allocation ratio `1`.
- Procedure: select `t tests` → `Means: Difference between two independent means (two groups)`; select a priori; set inputs; press Calculate.
- Observed outputs: `n1=105`, `n2=105`, `N=210`, `df=208`, `delta=3.6228442`, `critical t=1.9714347`, `actual power=0.9501287`.
- Evidence: `evidence/baseline-independent-a-priori.png`.
- Reproducibility: calculation repeated through the same GUI controls; values remained identical.
- Consequence: the public CSV uses these field names and raw displayed precision; the CLI contract rounds decimal fields to four places.

## [REA-002] Post hoc input/output and minimum-search boundary

- Experiment: post hoc mode with the same `d`, alpha, tails, and nearby integer allocations.
- Inputs: `tails=2`, `d=0.5`, `alpha=0.05`; tested `(n1,n2)=(105,105),(104,105),(105,104),(104,104)`.
- Procedure: select post hoc; enter group sizes; press Calculate for each pair.
- Observed outputs:
  - `(105,105)`: `N=210`, `df=208`, `delta=3.6228442`, `critical t=1.9714347`, power `0.9501287`.
  - `(104,105)`: `N=209`, `df=207`, `delta=3.6141667`, `critical t=1.9714904`, power `0.9492249`.
  - `(105,104)`: same outputs as `(104,105)`.
  - `(104,104)`: `N=208`, `df=206`, `delta=3.6055513`, `critical t=1.9715467`, power `0.9483147`.
- Evidence: `evidence/posthoc-search-boundary.png`; machine-readable values: `docs/posthoc-observations.csv`.
- Reproducibility: all four cases were calculated in one GUI session.
- Consequence: for this baseline, `N=210` is the first tested allocation at or above target power; `N=209` is below target. General search behavior beyond this tested boundary remains an inference.

## [REA-003] Unequal-ratio allocation observations

- Experiment: a priori, two tails, `d=0.5`, alpha `.05`, target power `.80`; vary only allocation ratio.
- Inputs and outputs are recorded in `docs/ratio-observations.csv` for 12 ratios: `0.3, 0.5, 0.7, 0.8, 1.3, 1.5, 1.7, 2, 2.5, 3.7, 4.2, 5`.
- Evidence: `evidence/ratio-case-01.png` through `evidence/ratio-case-12.png`.
- Observed examples: ratio `.3` returned `(n1,n2,N)=(138,42,180)`; ratio `1.5` returned `(54,80,134)`; ratio `3.7` returned `(40,150,190)`.
- Claim established for these 12 cases: `n1+n2=N`; the group counts match nearest-integer rounding of the two total-weight shares `N/(1+r)` and `Nr/(1+r)` while preserving the reported total. They do not generally equal `ceil(n1*r)`, `round(n1*r)`, or `floor(n1*r)`; for example ratio `1.5` has `n1*r=81` but observed `n2=80`.
- Reproducibility: each ratio was calculated once and screenshot-captured; the baseline ratio cases were also included in the public GUI vector run.
- Consequence: the implementation uses nearest-integer rounding of the total-weight share as the observed rule for tested cases. Half-tie behavior and untested ratios remain unresolved.

## [REA-004] A-priori search is not proven to be exhaustive integer-N search

- Experiment: one-tailed a priori, `d=2`, alpha `.05`, target power `.80`, ratio `1.5`; compare the GUI a-priori result with post hoc power for nearby integer pairs.
- A-priori GUI output: `(n1,n2,N)=(4,6,10)`, `df=8`, `delta=3.0983867`, `critical t=1.8595480`, actual power `0.8804686`.
- Post hoc observations: `(4,5,N=9)` has power `0.8490690`; `(3,6,N=9)` has power `0.8150194`; `(3,7,N=10)` has power `0.8405229`.
- Evidence: `evidence/posthoc-nonminimal-a-priori.png`; machine-readable values: `docs/posthoc-nonminimal.csv`; the corresponding public a-priori row is in `golden_vectors.csv`.
- Claim: the observed a-priori result is not the smallest total N among these post hoc-tested integer pairs that reaches `.80`. The exact internal search/rounding procedure remains unresolved; do not describe it as exhaustive minimum-N search.
- Implementation consequence: implementations must preserve this discrepancy as an unresolved compatibility rule until more GUI experiments establish the search procedure.

## [REA-005] A-priori search uses even total sample sizes

- Experiment: targeted a-priori probes designed to distinguish total-N search from group-size search, odd/even increments, starting value, and allocation timing.
- Inputs: 60 observations in `docs/search-observations.csv`, spanning one and two tails, `d=0.5,0.8,1.0,1.2,1.5,2.0,2.5`, alpha `.05` or `.10`, target power `.80`, `.90`, or `.95`, and ratios `.5,.7,1,1.3,1.5,2,2.5,3,3.7`; plus ten high-effect boundary probes with `d=10`, target power `.80`, ratios `.5,1,1.5,2,3.7`.
- Procedure: select the independent-means a-priori analysis, vary only the listed input tuple, press Calculate, and record the visible group sizes, total, df, noncentrality, critical value, and actual power. The reference was G*Power 3.1.9.7.
- Observed outputs: every targeted result has an even total. The high-effect probes all return `N=4`, establishing the lower search value in the tested domain. At the mismatch boundary, G*Power returns `N=10` for the one-tailed `d=2`, ratio `1.5` and `2` cases even though post hoc `N=9` allocations meet the target; the same behavior occurs for the reciprocal ratio `.5`.
- Mismatch analysis: the 24 existing mismatches contain 13 two-tailed and 11 one-tailed rows; 13 have `d=.1` and 11 have `d=2.0`; alpha and target power split evenly across `.05/.80` and `.10/.95`. Ratios are `.3`, `.5`, `1.5`, and `2` five times each, and `3.7` four times. Relative to the reference, the current engine is low by one total in 20 rows, low by two in 2 rows, high by one in 1 row, and high by two in 1 row. The expected totals are all even. The low results are the skipped odd candidates; the two high results are allocation differences at the boundary.
- Observed allocation: for each returned even total, the displayed groups are the nearest integer total-share allocation for the requested ratio, with the reported total preserved. Examples include `(N,ratio)=(14,1.5)->(6,8)`, `(12,2)->(4,8)`, `(4,3.7)->(1,3)`.
- Finding: the tested a-priori procedure searches total `N`, starts at `N=4`, advances by `2`, allocates that candidate total, evaluates power, and returns the first passing candidate. It therefore never evaluates odd totals. This explains all 24 mismatch directions: the current engine generally accepts an odd candidate one below G*Power, while the two positive differences occur where the engine's allocation at an even candidate differs from the reference allocation.
- Reproducibility: the 60-probe batch and ten boundary probes were run against the same visible GUI session; the known baseline and all prior ratio cases remained reproducible.
- Confidence: search variable, start `N=4`, step `2`, and first-passing behavior are high-confidence observations. Tie handling for exact half-share allocations and behavior outside the tested input domain remain inferred.

## [REA-006] A-priori stopping uses unrounded ratio shares

- Experiment: repeat the four remaining clean-room mismatches and probe the immediately surrounding candidate totals and target-power boundaries.
- Inputs: row 6 is one-tailed `d=.1`, alpha `.05`, target `.8`, ratio `3.7`; row 18 is two-tailed with the same inputs; row 113 is two-tailed `d=.1`, alpha `.1`, target `.95`, ratio `.3`; row 119 is two-tailed `d=2`, alpha `.1`, target `.95`, ratio `.3`.
- Boundary evidence: `docs/apriori-boundary-observations.csv` records 16 fresh a-priori observations. `docs/fixed-boundary-observations.csv` records 12 fresh fixed-size/post-hoc observations at the surrounding integer pairs.
- Observed fixed-size checks: `(786,2906)` has power `0.8001034` but a-priori still returns `(786,2908,N=3694)`; `(997,3691)` has power `0.7998798` while a-priori returns it at `N=4688`; `(4691,1407)` has power `0.9499853` while a-priori returns it at `N=6098`; `(12,4)` has power `0.9500139` while a-priori returns `(14,4,N=18)`.
- Finding: G*Power’s a-priori stopping test uses the unrounded ratio-weighted shares at each even total. The displayed group sizes are rounded only after the stopping total is selected, and displayed actual power is then calculated from those displayed integers. This accounts for both below-target displayed powers and for skipping an integer pair that passes fixed-size power.
- Numerical-precision assessment: the mismatch is not explained by ordinary large-`N` floating-point noise alone; the same direction appears at the small `N=16/18` boundary. The exact numerical implementation remains inferred, but the unrounded-share rule is strongly supported by all four cases.
- Minimum-size assessment: the `N=18` result is not evidence of a hidden minimum group size. G*Power accepts smaller positive groups in other a-priori observations, and the `N=16` displayed pair is accepted by fixed-size calculation. The remaining minimum-boundary behavior outside the observed domain is inferred.

## [REA-007] Exact-half allocation rounds group 1 upward

- Experiment: analyze the three held-out mismatches after an unchanged CLI run against all 50 held-out rows.
- Observed mismatches: 49/50 totals matched and 47/50 matched all three integers. The remaining inputs were one-tailed `d=1.5`, alpha `.05`, power `.8`, ratio `3`, and one-tailed `d=2`, alpha `.05`, power `.8`, ratio `3`.
- Expected G*Power outputs: `(5,13,N=18)` and `(3,7,N=10)`. The candidate group-1 shares are exactly `4.5` and `2.5`; group-2 is the total-preserving remainder.
- Builder outputs: `(4,14,N=18)` and `(2,8,N=10)`, consistent with ties-to-even rounding.
- Finding: for these exact-half cases, G*Power rounds group 1 upward rather than to even, then sets group 2 to preserve the total. The broader exact-half policy remains inferred beyond these observed cases.

## [REA-008] Corrected held-out row 21

- Experiment: rerun the held-out input that had inconsistent recorded statistics.
- Inputs: one-tailed a-priori, `d=.6`, alpha `.025`, target power `.9`, ratio `.6`.
- Observed G*Power output: `(n1,n2,N)=(80,48,128)`, `df=126`, `delta=3.2863353`, critical `t=1.9789706`, actual power `0.9034086`.
- Correction: row 21 in `held_out_vectors.csv` had stale values from an unrelated baseline (`N=224`, power about `.95`). It was corrected to the observed output above. This was an oracle-recording error, not an engine-behavior finding.
