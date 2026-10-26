import json
import random
import shutil
import subprocess
import sys
import time
import unittest
from pathlib import Path

from engine import calculate_a_priori, calculate_a_priori_linear


ROOT = Path(__file__).resolve().parents[1]
CLI = shutil.which("gpower-clone") or sys.executable


def run_cli(arguments):
    started = time.perf_counter()
    command = [CLI, *arguments] if CLI != sys.executable else [sys.executable, "-m", "cli.main", *arguments]
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    elapsed = time.perf_counter() - started
    lines = completed.stdout.strip().splitlines()
    return completed, json.loads(lines[-1]) if lines else {}, elapsed


def close_enough(actual, expected):
    return abs(actual - expected) <= 1e-6 or abs(actual - expected) <= 1e-6 * max(abs(actual), abs(expected))


class ContractCLITests(unittest.TestCase):
    def test_public_vectors_and_unsupported_families(self):
        rows = [json.loads(line) for line in (ROOT / "public_vectors.jsonl").read_text().splitlines() if line]
        for row in rows:
            args = []
            for key, value in row["input"].items():
                args += [f"--{key}", str(value)]
            completed, actual, _ = run_cli(args)
            if row["input"]["test"] != "t2-indep":
                self.assertNotEqual(completed.returncode, 0, row["id"])
                self.assertEqual(actual["code"], "UNSUPPORTED", row["id"])
                continue
            self.assertEqual(completed.returncode, 0, row["id"])
            for field, expected in row["expected"].items():
                self.assertIn(field, actual, row["id"])
                if isinstance(expected, int):
                    self.assertEqual(actual[field], expected, row["id"])
                else:
                    self.assertTrue(close_enough(actual[field], expected), (row["id"], field, actual[field], expected))

    def test_golden_vectors(self):
        rows = [json.loads(line) for line in (ROOT / "golden_vectors.jsonl").read_text().splitlines() if line]
        slowest = 0.0
        for row in rows:
            args = []
            for key, value in row["input"].items():
                args += [f"--{key}", str(value)]
            completed, actual, elapsed = run_cli(args)
            slowest = max(slowest, elapsed)
            self.assertEqual(completed.returncode, 0, row["id"])
            for field, expected in row["expected"].items():
                if isinstance(expected, int):
                    self.assertEqual(actual[field], expected, row["id"])
                else:
                    self.assertTrue(close_enough(actual[field], expected), (row["id"], field, actual[field], expected))
        print(f"slowest CLI call: {slowest:.6f}s")
        # Pre-submission audit threshold; this includes interpreter startup.
        self.assertLess(slowest, 1.5)

    def test_fast_search_matches_linear_search(self):
        rows = [json.loads(line) for line in (ROOT / "golden_vectors.jsonl").read_text().splitlines() if line]
        for row in rows:
            inp = row["input"]
            if inp["mode"] != "a-priori":
                continue
            fast = calculate_a_priori(inp["tails"], inp["d"], inp["alpha"], inp["power"], inp["ratio"])
            linear = calculate_a_priori_linear(inp["tails"], inp["d"], inp["alpha"], inp["power"], inp["ratio"])
            self.assertEqual(fast.as_dict(), linear.as_dict(), row["id"])

    def test_fast_search_matches_linear_on_200_random_inputs(self):
        rng = random.Random(20261025)
        for index in range(200):
            tails = rng.choice((1, 2))
            d = rng.uniform(.1, 2.0)
            alpha = rng.uniform(.01, .1)
            power = rng.uniform(max(.2, alpha + .01), .98)
            ratio = rng.uniform(.25, 4.0)
            fast = calculate_a_priori(tails, d, alpha, power, ratio)
            linear = calculate_a_priori_linear(tails, d, alpha, power, ratio)
            self.assertEqual(fast.as_dict(), linear.as_dict(), index)

    def test_adversarial_cli_timing_under_one_second(self):
        cases = [
            ["--test", "t2-indep", "--mode", "a-priori", "--tails", "2", "--d", ".01", "--alpha", ".05", "--power", ".99", "--ratio", "1"],
            ["--test", "t2-indep", "--mode", "a-priori", "--tails", "1", "--d", "10", "--alpha", ".001", "--power", ".999", "--ratio", "100"],
            ["--test", "t2-indep", "--mode", "a-priori", "--tails", "2", "--d", ".1", "--alpha", ".999", "--power", ".9999", "--ratio", ".01"],
        ]
        timings = []
        for args in cases:
            completed, _, elapsed = run_cli(args)
            self.assertEqual(completed.returncode, 0)
            timings.append((elapsed, args))
        print(f"slowest adversarial CLI calls: {sorted(timings, reverse=True)[:5]}")
        self.assertLess(max(t[0] for t in timings), 1.0)

    def test_version(self):
        completed, actual, _ = run_cli(["--version"])
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(actual["contract_version"], "1.0.0")
        self.assertIn("name", actual)
        self.assertIn("engine", actual)

    def test_error_codes(self):
        cases = [
            (["--test", "t2-indep", "--mode", "a-priori"], "MISSING_PARAM", "alpha"),
            (["--test", "t2-indep", "--mode", "a-priori", "--tails", "1", "--d", ".5", "--alpha", ".05", "--power", ".9", "--ratio", "1", "--bogus", "1"], "UNKNOWN_PARAM", "bogus"),
            (["--test", "t2-indep", "--mode", "a-priori", "--tails", "1.0", "--d", ".5", "--alpha", ".05", "--power", ".9", "--ratio", "1"], "INVALID_VALUE", "tails"),
            (["--test", "t2-indep", "--mode", "a-priori", "--tails", "3", "--d", ".5", "--alpha", ".05", "--power", ".9", "--ratio", "1"], "OUT_OF_RANGE", "tails"),
            (["--test", "t2-indep", "--mode", "post-hoc", "--tails", "1", "--d", ".5", "--alpha", ".05", "--power", ".9", "--n1", "2", "--n2", "2"], "UNKNOWN_PARAM", "power"),
            (["--test", "t2-indep", "--mode", "a-priori", "--tails", "1", "--d", ".5", "--alpha", ".05", "--power", ".05", "--ratio", "1"], "INCONSISTENT", "power"),
            (["--test", "t-paired", "--mode", "a-priori"], "UNSUPPORTED", "test"),
        ]
        for args, code, field in cases:
            completed, actual, _ = run_cli(args)
            self.assertEqual(completed.returncode, 2)
            self.assertEqual((actual["code"], actual["field"]), (code, field))

    def test_rea015_effect_size_boundary_and_refusal(self):
        # REA-015: d=20 is admissible; values above 20 are NO_SOLUTION on d.
        base = {
            "test": "t2-indep",
            "tails": 1,
            "alpha": ".05",
            "power": ".8",
            "ratio": 1,
        }
        for mode in ("a-priori", "post-hoc", "compromise", "criterion"):
            for d in (20, 20.0001, 21, 100, 1000):
                if d == 20 and mode != "a-priori":
                    continue
                values = dict(base, mode=mode, d=d)
                if mode == "compromise":
                    values.pop("alpha")
                    values.pop("power")
                    values.pop("ratio")
                    values["beta_alpha_ratio"] = 1
                    values["n1"] = 2
                    values["n2"] = 2
                elif mode == "criterion":
                    values.pop("alpha")
                    values.pop("ratio")
                    values["n1"] = 2
                    values["n2"] = 2
                elif mode == "post-hoc":
                    values.pop("power")
                    values.pop("ratio")
                    values["n1"] = 2
                    values["n2"] = 2
                args = [item for key, value in values.items() for item in (f"--{key}", str(value))]
                completed, actual, _ = run_cli(args)
                if d == 20:
                    self.assertEqual(completed.returncode, 0, ("REA-015", mode))
                    if mode == "a-priori":
                        self.assertEqual((actual["n1"], actual["n2"], actual["n_total"]), (2, 2, 4))
                else:
                    self.assertEqual(completed.returncode, 2, ("REA-015", mode, d))
                    self.assertEqual(
                        actual,
                        {"error": "Effect size d is outside the admissible range (-20, 20).", "code": "NO_SOLUTION", "field": "d"},
                    )

    def test_no_solution_mapping(self):
        import cli.main as cli_main
        original = cli_main._run
        try:
            cli_main._run = lambda mode, args: (_ for _ in ()).throw(ValueError("no solution"))
            self.assertEqual(cli_main.main(["--test", "t2-indep", "--mode", "post-hoc", "--tails", "1", "--d", ".5", "--alpha", ".05", "--n1", "2", "--n2", "2"]), 2)
        finally:
            cli_main._run = original

if __name__ == "__main__":
    unittest.main()
