# Agent cost record

This record is intentionally conservative. Values not available from the
repository or conversation history remain TODO rather than being estimated as
facts.

| Agent/model | Session | Iterations | Approx. tokens | Cost |
|---|---|---:|---:|---:|
| Codex / GPT-5 | Session 1 analyst | TODO | TODO | TODO |
| Codex / GPT-5 | Session 2 implementer | TODO | TODO | TODO |

What we would do differently: record model usage, token counts, wall time, and
per-session cost at the time each session runs; preserve the exact initial
prompts in `prompts/`; and keep the analyst and implementation workspaces
separate from the beginning.
