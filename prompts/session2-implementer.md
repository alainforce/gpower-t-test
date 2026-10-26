# Session 2 implementer prompt

ROLE
You are an implementer working clean-room. Your ONLY source of truth is
SPEC.md and golden_vectors.csv. You have never seen G*Power. Do not
look up or reproduce G*Power internals.

GOAL
Implement the power/sample-size engine for "t test, difference between two
independent means" exactly as SPEC.md specifies, then wrap it in a CLI.

LANGUAGE: [Python recommended (scipy.stats.nct handles the noncentral t).
C# also works, but then you must implement or import a noncentral t CDF.]

ARCHITECTURE
/engine   -> pure functions, no I/O: a_priori(), post_hoc(), sensitivity(), effect_size()
/cli      -> thin argument parsing + formatting, calls engine only
/mcp      -> (bonus) MCP server exposing engine functions as tools
/agent    -> (bonus) natural-language agent calling MCP tools
/tests    -> unit, golden-vector, and property tests
README.md -> usage, how correctness is verified

CLI CONTRACT
[PASTE THE EXACT CLI CONTRACT FROM THE ASSIGNMENT FILE: flags, JSON/text
output format, exit codes]

REQUIREMENTS
- Match SPEC.md on rounding, search procedure, minimum n, ratio handling,
  and error behavior, including quirks that differ from textbook formulas.
- Input validation exactly as specified; helpful error messages.
- Deterministic output; no network calls; no G*Power binary in the repo.
- Tests:
  1. All golden vectors pass (N exact match).
  2. Property tests: N decreases as d or power-tolerance grows; N increases
     as alpha shrinks or power rises; symmetry rules from SPEC.
  3. Edge-case tests for every [REA] finding, citing its ID.
- Report the golden-vector pass rate. If < 100%, list each mismatch and
  which SPEC section is ambiguous. Do NOT tune code to fit vectors
  without a SPEC-based reason; instead report SPEC gaps.

BONUS (only after the base CLI passes)
- MCP server: tools a_priori, post_hoc, sensitivity, effect_size with typed
  schemas, calling the same engine.
- Agent: accepts e.g. "How many patients per group to detect d=0.5 between
  drug and placebo at 80% power, alpha 0.05, two-sided?", maps it to the MCP
  tool, and returns an answer plus the parameters it used.

FINISH
Run the full test suite, show results, and summarize any places where
SPEC.md was unclear.
