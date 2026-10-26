"""Contract section 7 MCP adapter.

The official MCP SDK was not present when this project was built, so this
module implements the small MCP stdio JSON-RPC surface required by section 7.
It is intentionally an adapter: validation is shared with the CLI and every
calculation is delegated to engine/.
"""

from __future__ import annotations

import json
import sys
from typing import Any

from cli.main import ContractError, _validate
from engine import calculate_a_priori, calculate_compromise, calculate_criterion, calculate_post_hoc, calculate_sensitivity

TOOL_NAME = "power_analysis"
INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "test": {"type": "string"},
        "mode": {"type": "string", "enum": ["a-priori", "post-hoc", "compromise", "criterion", "sensitivity"]},
        "tails": {"type": "integer", "enum": [1, 2]},
        "d": {"type": "number", "exclusiveMinimum": 0},
        "alpha": {"type": "number", "exclusiveMinimum": 0, "exclusiveMaximum": 1},
        "power": {"type": "number", "exclusiveMinimum": 0, "exclusiveMaximum": 1},
        "ratio": {"type": "number", "exclusiveMinimum": 0},
        "beta_alpha_ratio": {"type": "number", "exclusiveMinimum": 0},
        "n1": {"type": "integer", "minimum": 2},
        "n2": {"type": "integer", "minimum": 2},
        "dz": {"type": "number", "exclusiveMinimum": 0},
        "f": {"type": "number", "exclusiveMinimum": 0},
        "w": {"type": "number", "exclusiveMinimum": 0},
        "f2": {"type": "number", "exclusiveMinimum": 0},
        "n_total": {"type": "integer", "minimum": 2},
        "groups": {"type": "integer", "minimum": 2},
        "df": {"type": "integer", "minimum": 1},
        "predictors": {"type": "integer", "minimum": 1},
    },
    "required": ["test", "mode"],
    "additionalProperties": False,
}


def list_tools() -> list[dict[str, Any]]:
    return [{"name": TOOL_NAME, "description": "Power analysis using the contract schema.", "inputSchema": INPUT_SCHEMA}]


def _error(exc: ContractError) -> dict[str, str]:
    return {"error": str(exc), "code": exc.code, "field": exc.field}


def _calculate(mode: str, args: dict[str, Any]) -> dict[str, Any]:
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


def call_power_analysis(arguments: dict[str, Any]) -> tuple[str, bool]:
    """Return the exact CLI JSON text and whether it represents an error."""
    raw = {key: str(value) for key, value in arguments.items()}
    try:
        mode, args = _validate(raw)
        try:
            result = _calculate(mode, args)
        except ValueError as exc:
            if str(exc) == "no solution":
                raise ContractError("no solution", "NO_SOLUTION", mode)
            raise ContractError(str(exc), "INCONSISTENT", mode)
        return json.dumps(result, separators=(",", ":"), allow_nan=False), False
    except ContractError as exc:
        return json.dumps(_error(exc), separators=(",", ":")), True


def _jsonrpc_response(request_id: Any, result: Any = None, error: Any = None) -> dict[str, Any]:
    response = {"jsonrpc": "2.0", "id": request_id}
    if error is not None:
        response["error"] = error
    else:
        response["result"] = result
    return response


def serve() -> None:
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            request = json.loads(line)
            request_id = request.get("id")
            method = request.get("method")
            if method == "initialize":
                result = {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "gpower-clone", "version": "1.0.0"}}
                print(json.dumps(_jsonrpc_response(request_id, result), separators=(",", ":")), flush=True)
            elif method == "notifications/initialized":
                continue
            elif method == "tools/list":
                print(json.dumps(_jsonrpc_response(request_id, {"tools": list_tools()}), separators=(",", ":")), flush=True)
            elif method == "tools/call":
                params = request.get("params", {})
                if params.get("name") != TOOL_NAME:
                    text = json.dumps({"error": "unknown tool", "code": "UNKNOWN_PARAM", "field": "name"}, separators=(",", ":"))
                    is_error = True
                else:
                    text, is_error = call_power_analysis(params.get("arguments", {}))
                result = {"content": [{"type": "text", "text": text}], "isError": is_error}
                print(json.dumps(_jsonrpc_response(request_id, result), separators=(",", ":")), flush=True)
            elif request_id is None:
                continue
            else:
                print(json.dumps(_jsonrpc_response(request_id, error={"code": -32601, "message": f"method not found: {method}"}), separators=(",", ":")), flush=True)
        except Exception as exc:
            request_id = locals().get("request", {}).get("id") if isinstance(locals().get("request"), dict) else None
            print(json.dumps(_jsonrpc_response(request_id, error={"code": -32603, "message": str(exc)}), separators=(",", ":")), flush=True)


if __name__ == "__main__":
    serve()
