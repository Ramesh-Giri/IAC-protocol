# research-token-efficiency-20260914

Date: 2026-09-14
Task: research-token-0914
goal: reduce token spend in multi-agent (overseer + worker seats) setup

## Verified from source

1. Keep durable project memory in `CLAUDE.md` (or equivalent AGENTS file in Codex) and let runtime read it once per session start
   - Expected saving: high (replaces repeated setup text with one-time startup cost)
   - Effort: low
   - Risk: low
   - Evidence: Claude docs says `CLAUDE.md` files are read at session start as user messages, not re-read each turn, and `/compact` applies edits immediately in-session. [support.claude.com](https://support.claude.com/en/articles/14553240-give-claude-context-claude-md-and-better-prompts)

2. Use short, high-signal project memory files instead of full docs
   - Expected saving: medium to high (fewer cached and prompt tokens)
   - Effort: low
   - Risk: low
   - Evidence: same source recommends short under ~200 lines and only include conventions, gotchas, build/test rules. [support.claude.com](https://support.claude.com/en/articles/14553240-give-claude-context-claude-md-and-better-prompts)

3. Use `/clear` between unrelated tasks to prevent transcript accumulation
   - Expected saving: medium (avoids long-context drift and unnecessary replay)
   - Effort: low
   - Risk: low
   - Evidence: `CLAUDE.md` carries durable context while `/clear` starts a fresh turn. [support.claude.com](https://support.claude.com/en/articles/14553240-give-claude-context-claude-md-and-better-prompts)

4. Enable and preserve Anthropic cache across repeated turns by keeping static prefixes stable
   - Expected saving: high
   - Effort: low
   - Risk: medium (cache key sensitivity)
   - Evidence: Anthropic prompt caching uses exact prefix matches; stable prefix at last identical block maximizes hits; changing block/content invalidates cache and TTL is standard 5m or 1h for extended cache. [platform.claude.com](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)

5. Precompute static instruction/tool blocks once to avoid first-turn misses
   - Expected saving: medium
   - Effort: medium
   - Risk: low
   - Evidence: Anthropic doc supports pre-warming cache with `max_tokens: 0`; useful for latency and avoids initial cache-miss cost. [platform.claude.com](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)

6. Don’t place cache breakpoints on changing content (timestamps/messages); place on shared stable block
   - Expected saving: high
   - Effort: medium
   - Risk: low
   - Evidence: Anthropic warns changing suffix block on explicit cache point causes misses; cache miss persists every turn. [github.io raw Claude docs](https://github.com/MOFU0712/claude-docs/blob/main/content/api-models/build-with-claude/prompt-caching.md)

7. Route heavy prompt work through cached reusable segments only; cap block count and inspect `cache_creation_input_tokens`/cache hit metrics
   - Expected saving: medium
   - Effort: medium
   - Risk: medium
   - Evidence: Anthropic documents cache pricing based on hit depth and provides usage counters (`cache_creation_input_tokens`). [github.io raw Claude docs](https://github.com/MOFU0712/claude-docs/blob/main/content/api-models/build-with-claude/prompt-caching.md)

8. In OpenAI workflows, track request usage with per-run counters and decide routing from observed prompt, input, output, and cached token counts
   - Expected saving: medium
   - Effort: medium
   - Risk: low
   - Evidence: OpenAI help defines input/output/cached/reasoning tokens and token counting; Agents SDK usage tracking exposes per-request and aggregated usage entries. [help.lingus?](https://help-lb.openai.com/en/articles/4936856-understanding-and-counting-tokens), [openai agents sdk usage](https://openai.github.io/openai-agents-python/usage/)

9. Use Codex `/status` and `/model` to standardize seat-level model/effort choices
   - Expected saving: medium
   - Effort: low
   - Risk: low
   - Evidence: Codex CLI documents session model/effort selection via `/model` and status visibility via `/status`. [learn.chatgpt.com codex cli](https://help.openai.com/en/articles/11096431)

10. Treat tool outputs as expensive prompt payloads and normalize/dedupe repeated command/file read outputs before including in mails
    - Expected saving: high
    - Effort: medium
    - Risk: medium
    - Evidence: OpenAI examples show tool call/response objects and usage accounting includes structured input/output; Anthropic also includes tool result blocks and tool schemas in cacheable content. [OpenAI usage docs](https://help-lb.openai.com/en/articles/4936856-understanding-and-counting-tokens), [platform.claude.com](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)

11. For long multi-agent sessions, avoid rebuilding full history by passing concise task/status handoff with stable references
    - Expected saving: high
    - Effort: medium
    - Risk: medium
    - Evidence: MCP spec is built for typed tool schemas and deterministic capabilities (JSON-RPC, typed errors/inputSchema) and supports discoverable tools/ resources. Structured handoffs avoid repeated free-form context. [MCP spec](https://modelcontextprotocol.io/specification/2025-03-26/basic), [MCP tools spec raw](https://raw.githubusercontent.com/modelcontextprotocol/modelcontextprotocol/main/docs/specification/2025-03-26/server/tools.mdx)

12. Add compact handoff files for overseer transfer only (task, decision, constraints, acceptance, state, next action)
    - Expected saving: medium
    - Effort: medium
    - Risk: medium
    - Evidence: no hard-cost spec, but supported by Agents SDK run-state design where run history and usage are separate from custom metadata/attachments. [openai agents sdk usage](https://openai.github.io/openai-agents-python/usage/)

## Claimed by blog / third-party writeups (verify before prod)

1. Open-source prompt-compression middlewares can cut token bills 40-60% in practice
   - Claimed by: leanctx README + PyPI metadata
   - License: MIT
   - Effort: medium
   - Risk: medium-high (benchmark context and quality drift)
   - Source: [leanctx GitHub](https://github.com/jia-gao/leanctx), [leanctx PyPI](https://pypi.org/project/leanctx/)

2. LLMLingua/LongLLMLingua up to 20x compression claims
   - Claimed by: Microsoft LLMLingua project/readme; papers linked
   - Effort: high
   - Risk: high if no quality guardrails
   - Source: [microsoft/LLMLingua README](https://github.com/microsoft/LLMLingua), [paper links](https://aclanthology.org/2024.findings-acl.57), [aclanthology 2023 paper](https://aclanthology.org/2023.emnlp-main.825)

3. Community notes suggest tokenized handoff schema with receipts outperforms “full thread replay” for handoff reliability
   - Claimed by: workflow discussions (community)
   - Effort: medium
   - Risk: low
   - Source: practitioner threads discussing failures when summaries lose constraints (examples in open-agent communities)

4. Frameworks to consider for structured handoff/agent orchestration
   - AutoGen: typed tool classes and multi-agent conversation patterns
   - CrewAI: event-driven flow and state persistence claims
   - Effort: high integration
   - Risk: medium (tooling complexity)
   - Sources: [Autogen docs](https://microsoft.github.io/autogen/dev/user-guide/core-user-guide/components/tools.html), [Autogen getting started](https://autogenhub.github.io/autogen/docs/Getting-Started/), [CrewAI docs](https://docs.crewai.com/)

## Recommended action order (top 5 first)

1) Standardize CLAUDE.md/AGENTS.md format and `/clear` policy
2) Add fixed handoff envelope + artifact-only mails
3) Introduce explicit Anthropic cache breakpoints and prewarm for fixed prefixes
4) Add run-level usage dashboards for both providers and seats
5) Pilot model routing matrix (`gpt-4o mini` for simple static checks, `o3/Claude Opus/Sonnet` only for heavy reasoning)
