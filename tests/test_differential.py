import csv
import unittest
from pathlib import Path

from engine import calculate_a_priori


ROOT = Path(__file__).resolve().parents[1]


class OracleDifferentialTests(unittest.TestCase):
    def test_every_oracle_field(self):
        rows = list(csv.DictReader((ROOT / "oracle" / "golden_vectors.csv").open(newline="")))
        mismatches = []
        for index, row in enumerate(rows, 1):
            result = calculate_a_priori(
                int(row["tails"]), float(row["d"]), float(row["alpha"]),
                float(row["power"]), float(row["ratio"]),
            )
            actual = {
                "n1": result.n1, "n2": result.n2, "N": result.n_total,
                "df": result.df, "delta": result.ncp,
                "crit_t": result.critical, "actual_power": result.actual_power,
            }
            for field, value in actual.items():
                expected = int(row[field]) if field in {"n1", "n2", "N", "df"} else float(row[field])
                if field in {"n1", "n2", "N", "df"}:
                    matched = value == expected
                else:
                    matched = abs(value - expected) <= 1e-6 or abs(value - expected) <= 1e-6 * max(abs(value), abs(expected))
                if not matched:
                    mismatches.append((index, field, value, expected))
        self.assertEqual(mismatches, [])
        self.assertEqual(len(rows), 120)


if __name__ == "__main__":
    unittest.main()
