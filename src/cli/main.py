"""Strict contract adapter for the pure t2-indep engine."""

from __future__ import annotations

import json
import math
import re
import sys
from typing import Any

from engine import (
    calculate_a_priori,
    calculate_compromise,
    calculate_criterion,
    calculate_post_hoc,
    calculate_sensitivity,
)

CONTRACT_VERSION = "1.0.0"
NUMBER = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")
INTEGER = re.compile(r"^[+-]?\d+$")
FIELDS = {"test", "mode", "tails", "d", "dz", "f", "alpha", "power", "ratio", "beta_alpha_ratio", "n1", "n2", "n_total", "groups", "w", "df", "f2", "predictors"}
MODES = {
    "a-priori": {"tails", "d", "alpha", "power", "ratio"},
    "post-hoc": {"tails", "d", "alpha", "n1", "n2"},
    "compromise": {"tails", "d", "beta_alpha_ratio", "n1", "n2"},
    "criterion": {"tails", "d", "power", "n1", "n2"},
    "sensitivity": {"tails", "alpha", "power", "n1", "n2"},
}


class ContractError(Exception):
    def __init__(self, message: str, code: str, field: str):
        super().__init__(message)
        self.code, self.field = code, field


def _error(message: str, code: str, field: str) -> int:
    print(json.dumps({"error": message, "code": code, "field": field}, separators=(",", ":")))
    return 2


def _parse_tokens(argv: list[str]) -> dict[str, str]:
    values: dict[str, str] = {}
    i = 0
    while i < len(argv):
        token = argv[i]
        if not token.startswith("--") or token == "--":
            raise ContractError("expected --field", "UNKNOWN_PARAM", token.lstrip("-") or "argument")
        field = token[2:]
        if field not in FIELDS:
            raise ContractError(f"unknown parameter: {field}", "UNKNOWN_PARAM", field)
        if field in values:
            raise ContractError(f"duplicate parameter: {field}", "INVALID_VALUE", field)
        if i + 1 >= len(argv) or argv[i + 1].startswith("--"):
            raise ContractError(f"missing parameter value: {field}", "MISSING_PARAM", field)
        values[field] = argv[i + 1]
        i += 2
    return values


def _number(raw: str, field: str) -> float:
    if not NUMBER.fullmatch(raw):
        raise ContractError(f"{field} must be a number", "INVALID_VALUE", field)
    value = float(raw)
    if not math.isfinite(value):
        raise ContractError(f"{field} must be finite", "INVALID_VALUE", field)
    return value


def _integer(raw: str, field: str) -> int:
    if not INTEGER.fullmatch(raw):
        raise ContractError(f"{field} must be an integer", "INVALID_VALUE", field)
    return int(raw)


def _validate(values: dict[str, str]) -> tuple[str, dict[str, Any]]:
    for field in ("test", "mode"):
        if field not in values:
            raise ContractError(f"missing parameter: {field}", "MISSING_PARAM", field)
    if values["test"] != "t2-indep":
        raise ContractError(f"unsupported test: {values['test']}", "UNSUPPORTED", "test")
    if values["mode"] not in MODES:
        raise ContractError(f"unsupported mode: {values['mode']}", "UNSUPPORTED", "mode")
    mode = values["mode"]
    supplied = set(values) - {"test", "mode"}
    irrelevant = supplied - MODES[mode]
    if irrelevant:
        field = sorted(irrelevant)[0]
        raise ContractError(f"parameter is not valid for {mode}: {field}", "UNKNOWN_PARAM", field)
    for field in sorted(MODES[mode] - supplied):
        raise ContractError(f"missing parameter: {field}", "MISSING_PARAM", field)

    parsed: dict[str, Any] = {"test": values["test"], "mode": mode}
    integer_fields = {"tails", "n1", "n2"}
    for field in MODES[mode]:
        parsed[field] = _integer(values[field], field) if field in integer_fields else _number(values[field], field)

    if parsed["tails"] not in (1, 2):
        raise ContractError("tails must be 1 or 2", "OUT_OF_RANGE", "tails")
    for field in ("d", "ratio", "beta_alpha_ratio"):
        if field in parsed and parsed[field] <= 0:
            raise ContractError(f"{field} must be greater than 0", "OUT_OF_RANGE", field)
    # REA-015: the contract admits positive d, but the calculation domain
    # stops at and includes 20.  Keep this check in validation so failures
    # happen before the numerical engine is invoked.
    if "d" in parsed and parsed["d"] > 20:
        raise ContractError(
            "Effect size d is outside the admissible range (-20, 20).",
            "NO_SOLUTION",
            "d",
        )
    for field in ("alpha", "power"):
        if field in parsed and not 0 < parsed[field] < 1:
            raise ContractError(f"{field} must be between 0 and 1", "OUT_OF_RANGE", field)
    for field in ("n1", "n2"):
        if field in parsed and parsed[field] < 2:
            raise ContractError(f"{field} must be at least 2", "OUT_OF_RANGE", field)
    if "alpha" in parsed and "power" in parsed and parsed["power"] <= parsed["alpha"]:
        raise ContractError("power must be greater than alpha", "INCONSISTENT", "power")
    return mode, parsed


def _run(mode: str, args: dict[str, Any]) -> dict[str, Any]:
    if mode == "a-priori":
        return calculate_a_priori(args["tails"], args["d"], args["alpha"], args["power"], args["ratio"]).as_dict()
    if mode == "post-hoc":
        result = calculate_post_hoc(args["tails"], args["d"], args["alpha"], args["n1"], args["n2"])
        return {"ncp": result.ncp, "critical_t": result.critical, "df": result.df, "power": result.actual_power}
    if mode == "compromise":
        return calculate_compromise(args["tails"], args["d"], args["beta_alpha_ratio"], args["n1"], args["n2"])
    if mode == "criterion":
        return calculate_criterion(args["tails"], args["d"], args["power"], args["n1"], args["n2"])
    return calculate_sensitivity(args["tails"], args["alpha"], args["power"], args["n1"], args["n2"])


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv == ["--version"]:
        print(json.dumps({"contract_version": CONTRACT_VERSION, "name": "RE-impl", "engine": "Python 3"}, separators=(",", ":")))
        return 0
    try:
        mode, args = _validate(_parse_tokens(argv))
        try:
            result = _run(mode, args)
        except ValueError as exc:
            if str(exc) == "no solution":
                raise ContractError("no solution", "NO_SOLUTION", mode)
            raise ContractError(str(exc), "INCONSISTENT", mode)
        print(json.dumps(result, separators=(",", ":"), allow_nan=False))
        return 0
    except ContractError as exc:
        return _error(str(exc), exc.code, exc.field)
    except Exception as exc:
        print(json.dumps({"error": str(exc), "code": "INTERNAL", "field": "internal"}, separators=(",", ":")))
        return 1


if __name__ == "__main__":
    sys.exit(main())
