"""Independent-samples, equal-variance t-test calculations.

This module deliberately has no input/output or command-line concerns.
"""

from __future__ import annotations

import math
import glob
import importlib.util
import os
import sys
import types
from dataclasses import dataclass
from functools import lru_cache
from statistics import NormalDist


@lru_cache(maxsize=1)
def _special_functions():
    # Load the exact SciPy special ufuncs while avoiding the expensive Python
    # wrapper graph. Fall back to the public import on unsupported layouts.
    # [REA-009] preserves the contract's full-precision numerical output;
    # this is an import-time optimization, not a changed calculation.
    try:
        scipy_spec = importlib.util.find_spec("scipy")
        scipy_root = str(next(iter(scipy_spec.submodule_search_locations)))
        special_root = os.path.join(scipy_root, "special")
        if hasattr(os, "add_dll_directory"):
            for directory in (os.path.join(os.path.dirname(scipy_root), "scipy.libs"), os.path.join(os.path.dirname(scipy_root), "numpy.libs")):
                if os.path.isdir(directory):
                    os.add_dll_directory(directory)
        path = next(path for path in glob.glob(os.path.join(special_root, "_ufuncs*")) if "_cxx" not in os.path.basename(path) and path.endswith((".pyd", ".so")))
        if "scipy" not in sys.modules:
            scipy = types.ModuleType("scipy")
            scipy.__path__ = [scipy_root]
            scipy.__spec__ = scipy_spec
            sys.modules["scipy"] = scipy
        if "scipy.special" not in sys.modules:
            special = types.ModuleType("scipy.special")
            special.__path__ = [special_root]
            sys.modules["scipy.special"] = special
        name = "scipy.special._ufuncs"
        module = sys.modules.get(name)
        if module is None:
            spec = importlib.util.spec_from_file_location(name, path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            assert spec.loader is not None
            spec.loader.exec_module(module)
        return module.nctdtr, module.stdtrit
    except Exception:
        from scipy.special import nctdtr, stdtrit
        return nctdtr, stdtrit


def _brentq():
    # The fast ufunc loader installs a minimal scipy package shell. Restore
    # SciPy's normal package before importing optimize, which needs the wider
    # public scipy.special namespace. [REA-009]
    scipy = sys.modules.get("scipy")
    if scipy is not None and getattr(scipy, "__file__", None) is None:
        for name in [name for name in sys.modules if name == "scipy" or name.startswith("scipy.")]:
            sys.modules.pop(name, None)
    from scipy.optimize import brentq
    return brentq


@dataclass(frozen=True)
class Result:
    n1: int
    n2: int
    n_total: int
    actual_power: float
    critical: float
    df: int
    ncp: float

    def as_dict(self) -> dict:
        return {
            "n1": self.n1,
            "n2": self.n2,
            "n_total": self.n_total,
            "actual_power": self.actual_power,
            "critical_t": self.critical,
            "df": self.df,
            "ncp": self.ncp,
        }


def _validate_common(tails: int, d: float, alpha: float, ratio: float) -> None:
    if tails not in (1, 2):
        raise ValueError("tails must be 1 or 2")
    if not math.isfinite(d) or d <= 0:
        raise ValueError("d must be a positive finite number")
    if not math.isfinite(alpha) or not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1")
    if not math.isfinite(ratio) or ratio <= 0:
        raise ValueError("ratio must be a positive finite number")


def split_groups(total: int, ratio: float) -> tuple[int, int]:
    """Allocate N2/N1=ratio, preserving total N.

    [REA-003]/[REA-005]/[REA-007] define the observed ratio allocation. The
    spec says nearest integer but does not resolve exact half ties. Python's
    round (ties-to-even) is used as the documented deterministic policy.
    """
    if not isinstance(total, int) or total < 4 or total % 2:
        raise ValueError("total must be an even integer of at least 4")
    if not math.isfinite(ratio) or ratio <= 0:
        raise ValueError("ratio must be a positive finite number")
    n1 = int(round(total / (1.0 + ratio)))
    n1 = max(1, min(total - 1, n1))
    return n1, total - n1


def _power_components(tails: int, d: float, alpha: float, n1: float, n2: float) -> tuple[float, float, int, float]:
    nctdtr, stdtrit = _special_functions()
    df = n1 + n2 - 2
    ncp = d * math.sqrt(n1 * n2 / (n1 + n2))
    if tails == 1:
        critical = float(stdtrit(df, 1 - alpha))
        actual_power = float(1.0 - nctdtr(df, ncp, critical))
    else:
        critical = float(stdtrit(df, 1 - alpha / 2))
        actual_power = float(nctdtr(df, ncp, -critical) + 1.0 - nctdtr(df, ncp, critical))
    return actual_power, critical, int(df), ncp


def _evaluate(tails: int, d: float, alpha: float, n1: int, n2: int) -> Result:
    actual_power, critical, df, ncp = _power_components(tails, d, alpha, n1, n2)
    return Result(n1, n2, n1 + n2, actual_power, critical, df, ncp)


def calculate_a_priori(tails: int, d: float, alpha: float, power: float, ratio: float) -> Result:
    """Find the first even total N >= 4 whose calculated power reaches target.

    [REA-006] uses unrounded ratio-weighted shares for stopping and rounds only
    after the stopping total has been selected.
    """
    _validate_common(tails, d, alpha, ratio)
    if not math.isfinite(power) or not 0 < power < 1:
        raise ValueError("power must be between 0 and 1")
    max_iterations = 64
    evaluations = 0
    cached_power: dict[int, float] = {}

    def stopping_power(total: int) -> float:
        nonlocal evaluations
        if total in cached_power:
            return cached_power[total]
        evaluations += 1
        if evaluations > max_iterations:
            raise ValueError("no solution")
        share1 = total / (1.0 + ratio)
        share2 = total - share1
        cached_power[total] = _power_components(tails, d, alpha, share1, share2)[0]
        return cached_power[total]

    if stopping_power(4) >= power:
        n1, n2 = split_groups(4, ratio)
        return _evaluate(tails, d, alpha, n1, n2)

    normal = NormalDist()
    z_alpha = normal.inv_cdf(1 - alpha if tails == 1 else 1 - alpha / 2)
    z_power = normal.inv_cdf(power)
    effective = d * math.sqrt(ratio) / (1.0 + ratio)
    estimate = ((z_alpha + z_power) / effective) ** 2
    low, high = 2, max(2, math.ceil(estimate / 2))
    while stopping_power(2 * high) < power:
        low, high = high, high * 2
        if high > 2**62:
            raise ValueError("no solution")
    while high - low > 1:
        middle = (low + high) // 2
        if stopping_power(2 * middle) >= power:
            high = middle
        else:
            low = middle
    total = 2 * high
    if stopping_power(total) < power or (total > 4 and stopping_power(total - 2) >= power):
        start = max(2, high - 8)
        stop = min(2**62, high + 8)
        found = None
        for index in range(start, stop + 1):
            if stopping_power(2 * index) >= power:
                found = index
                break
        if found is None:
            raise ValueError("no solution")
        total = 2 * found
    n1, n2 = split_groups(total, ratio)
    return _evaluate(tails, d, alpha, n1, n2)


def calculate_a_priori_linear(tails: int, d: float, alpha: float, power: float, ratio: float) -> Result:
    """Reference linear search used to verify the accelerated search."""
    _validate_common(tails, d, alpha, ratio)
    if not math.isfinite(power) or not 0 < power < 1:
        raise ValueError("power must be between 0 and 1")
    total = 4
    while True:
        share1 = total / (1.0 + ratio)
        share2 = total - share1
        if _power_components(tails, d, alpha, share1, share2)[0] >= power:
            n1, n2 = split_groups(total, ratio)
            return _evaluate(tails, d, alpha, n1, n2)
        total += 2


def calculate_post_hoc(tails: int, d: float, alpha: float, n1: int, n2: int) -> Result:
    """Evaluate power for supplied group sizes."""
    _validate_common(tails, d, alpha, 1.0)
    if not isinstance(n1, int) or not isinstance(n2, int) or n1 < 2 or n2 < 2:
        raise ValueError("n1 and n2 must be integers of at least 2")
    return _evaluate(tails, d, alpha, n1, n2)


def calculate_sensitivity(tails: int, alpha: float, power: float, n1: int, n2: int) -> dict:
    """Find the positive d that reaches target power for fixed groups."""
    if tails not in (1, 2):
        raise ValueError("tails must be 1 or 2")
    if not math.isfinite(alpha) or not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1")
    if not math.isfinite(power) or not 0 < power < 1:
        raise ValueError("power must be between 0 and 1")
    if not isinstance(n1, int) or not isinstance(n2, int) or n1 < 2 or n2 < 2:
        raise ValueError("n1 and n2 must be integers of at least 2")

    def difference(d: float) -> float:
        return _power_components(tails, d, alpha, n1, n2)[0] - power

    if difference(0.0) >= 0:
        d = 0.0
    else:
        upper = 1.0
        while difference(upper) < 0 and upper < 1_000_000:
            upper *= 2.0
        if difference(upper) < 0:
            raise ValueError("no solution")
        d = _brentq()(difference, 0.0, upper)
    actual_power, critical, df, ncp = _power_components(tails, d, alpha, n1, n2)
    return {"ncp": ncp, "critical_t": critical, "df": df, "d": d}


def _validate_fixed(tails: int, d: float, n1: int, n2: int) -> None:
    if tails not in (1, 2):
        raise ValueError("tails must be 1 or 2")
    if not math.isfinite(d) or d <= 0:
        raise ValueError("d must be a positive finite number")
    if not isinstance(n1, int) or not isinstance(n2, int) or n1 < 2 or n2 < 2:
        raise ValueError("n1 and n2 must be integers of at least 2")


def calculate_criterion(tails: int, d: float, power: float, n1: int, n2: int) -> dict:
    _validate_fixed(tails, d, n1, n2)
    if not math.isfinite(power) or not 0 < power < 1:
        raise ValueError("power must be between 0 and 1")

    def difference(alpha: float) -> float:
        return _power_components(tails, d, alpha, n1, n2)[0] - power

    if difference(1e-15) > 0 or difference(1 - 1e-12) < 0:
        raise ValueError("no solution")
    alpha = _brentq()(difference, 1e-15, 1 - 1e-12)
    _, critical, df, ncp = _power_components(tails, d, alpha, n1, n2)
    return {"ncp": ncp, "critical_t": critical, "df": df, "alpha": alpha}


def calculate_compromise(tails: int, d: float, beta_alpha_ratio: float, n1: int, n2: int) -> dict:
    _validate_fixed(tails, d, n1, n2)
    if not math.isfinite(beta_alpha_ratio) or beta_alpha_ratio <= 0:
        raise ValueError("beta_alpha_ratio must be positive")
    upper = min(1.0 - 1e-12, (1.0 - 1e-12) / beta_alpha_ratio)

    def difference(alpha: float) -> float:
        return _power_components(tails, d, alpha, n1, n2)[0] + beta_alpha_ratio * alpha - 1.0

    if difference(1e-15) > 0 or difference(upper) < 0:
        raise ValueError("no solution")
    alpha = _brentq()(difference, 1e-15, upper)
    actual_power, critical, df, ncp = _power_components(tails, d, alpha, n1, n2)
    beta = 1.0 - actual_power
    return {"ncp": ncp, "critical_t": critical, "df": df, "alpha": alpha, "beta": beta, "power": actual_power}


def calculate_effect_size(mean1: float, mean2: float, sd1: float, sd2: float, n1: int, n2: int) -> dict:
    """Calculate Cohen's d from two independent groups.

    This is a provisional extension: CONTRACT.md explicitly excludes the
    original application's Determine window and specifies no effect_size
    schema. The formula is kept here, outside the MCP adapter.
    """
    values = (mean1, mean2, sd1, sd2)
    if not all(math.isfinite(value) for value in values):
        raise ValueError("means and standard deviations must be finite")
    if sd1 <= 0 or sd2 <= 0:
        raise ValueError("standard deviations must be positive")
    if not isinstance(n1, int) or not isinstance(n2, int) or n1 < 2 or n2 < 2:
        raise ValueError("n1 and n2 must be integers of at least 2")
    pooled_sd = math.sqrt(((n1 - 1) * sd1**2 + (n2 - 1) * sd2**2) / (n1 + n2 - 2))
    return {"d": (mean1 - mean2) / pooled_sd}
