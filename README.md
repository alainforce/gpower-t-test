# Independent two-sample t-test engine

This clean-room implementation follows `SPEC.md` for the equal-variance independent two-group t test. The engine is pure Python and uses SciPy's exact `nctdtr`/`stdtrit` special-function ufuncs; `cli.main` only parses arguments, invokes the engine, and emits one-line JSON.

The a-priori search follows REA-006: each even candidate total is tested using real-valued ratio-weighted shares; after the first passing total, group sizes are rounded for display and all reported statistics are recomputed from those integers.

Install and run:

```text
pip install -e . && gpower-clone --test t2-indep --mode a-priori --tails 2 --d 0.5 --alpha 0.05 --power 0.95 --ratio 1
```

The executable supports the contract modes `a-priori`, `post-hoc`, `compromise`, `criterion`, and `sensitivity`. It emits one JSON line on stdout; validation errors use the contract `{error, code, field}` shape and exit code 2.

## Correctness and provenance

Correctness is assessed against an independent behavioural oracle: the 120-row `golden_vectors.jsonl` set, the 25 public contract vectors in `public_vectors.jsonl`, and held-out vectors kept outside this repository. Tests compare integer fields exactly and floating-point fields under the contract tolerance. Property tests cover allocation invariants, accelerated-search equivalence to the linear reference, validation, and CLI/MCP equivalence. The implementation is clean-room separated: the engine is rebuilt from `SPEC.md`, while oracle observations are used only as external test data. Every behavioural choice is traceable to a `[REA-###]` finding in `SPEC.md` where available.

The repository intentionally contains no held-out vector file. The held-out suite is run by the evaluation harness without being copied into this tree.

`evidence/` contains supporting observation records and provenance notes. The machine-readable files under `evidence/observations/` contain only values displayed by G*Power during black-box observation; they contain no decompiled code or implementation internals.

An early implementation session shared a workspace with the analysis session. The final engine was subsequently rebuilt from `SPEC.md` only; oracle vectors are test inputs, not source material.

The remaining unresolved points are those explicitly marked in `SPEC.md` (including inferred behaviour and the scope of general half-tie allocation). They are reported rather than tuned to fit vectors.

The golden-vector test checks exact `n1`, `n2`, and total `N`, prints the pass rate and every mismatch, and tests run with:

```text
python -m unittest discover -s tests -v
```

## Ethics

This is a non-commercial university course run solely for educational purposes, with respect for the work the authors of G\*Power (Faul, Erdfelder, Lang and Buchner) have freely made available to the scientific community. We do not modify, redistribute or sell G\*Power, and none of our outputs is presented as G\*Power. G\*Power is used only as a behavioural reference: no source code or decompiled output is published, and the calculations are reimplemented independently from published methods and observed behaviour. Our aim is not to compete with G\*Power but to propose a contribution for the age of AI agents; we will offer the best results to the authors for review and promptly withdraw material at their request.

## MCP server

The stdio server follows contract section 7 and exposes exactly one tool: `power_analysis`. The custom protocol adapter is used because the official MCP SDK was not available in the base runtime; the SDK is listed as a test extra for independent protocol verification.

```text
python -m mcp_server.server
```

Configure an MCP client to launch that command from this directory. The server handles `initialize`, `notifications/initialized`, `tools/list`, and `tools/call` over stdio. Tool results contain the exact CLI JSON as text; errors additionally set `isError: true`. All calculations are delegated to `engine/`.

The independent protocol test uses the official SDK client and checks CLI/MCP text equivalence for all 25 `public_vectors.jsonl` rows:

```text
pip install -e .[test]
python -m unittest tests.test_mcp -v
```
