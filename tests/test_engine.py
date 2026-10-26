import csv
import unittest
from pathlib import Path

from engine import calculate_a_priori, calculate_post_hoc, split_groups


def rows():
    with Path("golden_vectors.csv").open(newline="") as f:
        yield from csv.DictReader(f)


class EngineTests(unittest.TestCase):
  def test_golden_vectors_exact_n_and_report_mismatches(self):
    mismatches = []
    total = 0
    for i, row in enumerate(rows(), 1):
        total += 1
        result = calculate_a_priori(int(row["tails"]), float(row["d"]), float(row["alpha"]), float(row["power"]), float(row["ratio"]))
        expected = (int(row["n1"]), int(row["n2"]), int(row["N"]))
        actual = (result.n1, result.n2, result.n_total)
        if actual != expected:
            mismatches.append((i, expected, actual))
    print(f"golden total-N exact-match rate: {total - len(mismatches)}/{total} ({(total-len(mismatches))/total:.1%})")
    print(f"mismatches: {mismatches}")
    # This is intentionally a reporting test: unresolved oracle/spec behavior
    # must remain visible instead of being hidden by a tuned implementation.

  def test_invalid_tails(self):
    for tails in (0, 3):  # [SPEC-5]
      with self.assertRaises(ValueError):
        calculate_a_priori(tails, .5, .05, .8, 1)

  def test_invalid_d(self):
    for d in (0, -1):  # [SPEC-5]
      with self.assertRaises(ValueError):
        calculate_a_priori(2, d, .05, .8, 1)

  def test_allocation_preserves_total_and_uses_ratio(self):
    assert split_groups(10, 2) == (3, 7)  # [REA-003]/[REA-005]
    assert split_groups(10, .5) == (7, 3)

  def test_search_starts_at_four_and_steps_by_two(self):
    result = calculate_a_priori(1, 2, .05, .8, 1)  # [REA-004]/[REA-005]
    assert result.n_total == 8
    assert result.n_total % 2 == 0

  def test_unrounded_shares_control_stopping_then_display_rounds(self):
    # [REA-006]: N=16's unrounded shares do not reach target, while N=18
    # does; displayed groups are rounded only after stopping.
    result = calculate_a_priori(2, 2.0, .1, .95, .3)
    self.assertEqual((result.n1, result.n2, result.n_total), (14, 4, 18))

  def test_displayed_power_is_recomputed_after_rounding(self):
    # [REA-006]: displayed rounded groups can report power below target.
    result = calculate_a_priori(2, .1, .1, .95, .3)
    self.assertEqual((result.n1, result.n2, result.n_total), (4691, 1407, 6098))
    self.assertLess(result.actual_power, .95)

  def test_post_hoc_uses_supplied_sizes(self):
    result = calculate_post_hoc(2, .5, .05, 105, 105)  # [REA-002]
    assert (result.n1, result.n2, result.n_total, result.df) == (105, 105, 210, 208)

  def test_invalid_ratio(self):
    for ratio in (0, -1):  # [SPEC-5]
      with self.assertRaises(ValueError):
        calculate_a_priori(2, .5, .05, .8, ratio)


if __name__ == "__main__":
  unittest.main()
