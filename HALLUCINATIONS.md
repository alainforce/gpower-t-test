# Hallucinations and corrections — analyst side

This is the analyst-side record. It documents incorrect or overconfident claims made during the clean-room/oracle work and the observation that corrected each one.

## Held-out row 21

The original held-out row 21 recorded stale values around `N=224` and power near `.95` for input `tails=1,d=.6,alpha=.025,power=.9,ratio=.6`. A fresh G*Power rerun returned `(n1,n2,N)=(80,48,128)`, `df=126`, `ncp=3.2863353`, `critical_t=1.9789706`, and `actual_power=.9034086`. The mismatch was caught by the held-out comparison and corrected in `held_out_vectors.csv`.

## d=100 error-code mapping

The first mapping labeled the d=100 refusal `OUT_OF_RANGE` because G*Power displayed “outside the admissible range (-20, 20).” Contract section 5, however, declares only `d > 0`, so d=100 is contract-valid even though the reference refuses it. Boundary probes showed d=20 computes and d=20.000001 refuses. The expected contract code was therefore changed to inferred `NO_SOLUTION`; the exact GUI message is preserved. This was caught by the contract-vs-reference boundary analysis.

## Half-share rounding

The builder initially used ties-to-even rounding. G*Power returned `(3,7)` for total 10 and ratio 3 and `(5,13)` for total 18 and ratio 3, while the builder returned `(2,8)` and `(4,14)`. The exact-half oracle probes caught the error; the observed rule is group-1 half-up with group-2 remainder. General tie behavior remains inferred.

## A-priori search hypothesis

An early hypothesis treated a-priori as exhaustive integer-N search. Boundary probes and the nonminimal post-hoc checks showed that G*Power searches even totals from 4 in steps of 2, evaluates unrounded ratio shares for stopping, and rounds displayed groups only afterward. This was corrected in REA-005/006 and the search-observations evidence.

## Missing post-hoc observations

Two observation records were initially written with `?` despite G*Power producing ordinary numeric output. Direct reruns filled `observed-017` with `1.2472191, 2.7283944, 34, .0826020` and `observed-020` with `2.7923706, 2.0017175, 58, .7840379`. The held-out CLI mismatch report exposed the stale records.

## Evidence boundary

GUI observations were previously labeled `[REA]` too broadly. The final ledger re-tags REA-001 through REA-015 as `[AJAN]`/oracle findings unless a binary address or string reference exists. Only the generic range helper and refusal strings have binary-backed `[REA]` entries.
