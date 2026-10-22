# Token-efficiency research checklist

This checklist covers generic ways to measure coordination cost.
The former site study is preserved in ignored `local/site-originals/agentmail/research/`.
It is historical context, not current runtime documentation or authorization.

- Keep durable instructions concise and reference stable artifacts instead of repeating full task bodies.
- Separate unrelated tasks so stale assumptions and transcripts do not follow a new assignment.
- Measure input, output and cached usage through the runtime's supported counters.
- Verify current cache semantics against official documentation before configuring provider-specific features.
- Keep stable instruction prefixes separate from changing timestamps, mail and tool results.
- Compare cost together with task correctness, latency and recovery behavior.
- Treat compression, routing and model-tier claims as hypotheses requiring representative evaluation.
- Include complete constraints and verified state in handoffs, while keeping private task data local.
- Prefer existing protocol helpers over adding a second orchestration framework without evidence.
- Keep measured results, account identifiers and runtime assignments out of public examples.
