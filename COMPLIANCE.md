# Oracle compliance report

Source: `oracle/golden_vectors.csv` (120 rows). The differential test is
`tests/test_differential.py`; integer fields are compared exactly and decimal
fields use the contract tolerance of `1e-6` absolute or relative.

| Field | Matches | Rate |
|---|---:|---:|
| n1 | 120/120 | 100% |
| n2 | 120/120 | 100% |
| N | 120/120 | 100% |
| df | 120/120 | 100% |
| delta/ncp | 120/120 | 100% |
| crit_t/critical_t | 120/120 | 100% |
| actual_power | 120/120 | 100% |

## Mismatches

There are no mismatches. No vector was tuned or exempted; the differential
test reports every mismatch if one occurs.

## Fractional shares versus displayed integer groups

The oracle contains 27/120 rows where ratio-weighted shares are fractional.
The stopping total N remains an even integer; only the displayed group sizes
are rounded after stopping, with the second group set to the total-preserving
remainder. Representative differences are:

| Row | Fractional shares | Displayed groups | N difference |
|---:|---|---|---:|
| 2 | 1031.2, 1546.8 | 1031, 1547 | 0 |
| 5 | 2681.5385, 804.4615 | 2682, 804 | 0 |
| 9 | 3.3333, 6.6667 | 3, 7 | 0 |
| 10 | 6.6667, 3.3333 | 7, 3 | 0 |
| 12 | 2.5532, 9.4468 | 3, 9 | 0 |

Thus fractional and displayed calculations differ in group allocation, but not
in total N. Displayed power is recomputed from the rounded integer groups as
required by REA-006.
