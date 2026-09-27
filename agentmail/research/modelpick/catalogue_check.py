"""Read-only demonstration of the ONLY verification the design trusts: does the account actually
have this model right now. Two local, dated, machine-readable sources, no web search, no vendor copy.
  - Codex: ~/.codex/models_cache.json (fetched_at, client_version, one row per model the ChatGPT
    account can invoke, with context_window and supported_reasoning_levels).
  - Claude Code: ~/.claude/cache/model-catalog/*.json (fetchedAt/staleAt TTL, one row per model this
    Claude Code install + account can select, with min_claude_code_version gating and section
    main/overflow).
Cross-references the roster (READ ONLY - this script writes nothing, changes no live tooling).
Run: python3 catalogue_check.py
"""
import glob, json, os, sys, time

ROSTER = os.path.expanduser("~/Work/Aureus/.agent-mail/roster.json")
CODEX_CACHE = os.path.expanduser("~/.codex/models_cache.json")
CLAUDE_CACHE_GLOB = os.path.expanduser("~/.claude/cache/model-catalog/*.json")


def load_codex_ids():
    d = json.load(open(CODEX_CACHE))
    age_s = time.time() - os.path.getmtime(CODEX_CACHE)
    return {m["slug"] for m in d["models"]}, d.get("fetched_at"), age_s


def load_claude_ids():
    # Claude Code writes one cache file per (org, surface) it has queried this run; take the newest.
    files = sorted(glob.glob(CLAUDE_CACHE_GLOB), key=os.path.getmtime, reverse=True)
    if not files:
        return set(), None, None, None
    d = json.load(open(files[0]))
    now_ms = time.time() * 1000
    stale = now_ms > d.get("staleAt", 0)
    ids = {m["id"] for m in d["catalog"]["config"]["models"]}
    return ids, d.get("fetchedAt"), stale, files[0]


def main():
    codex_ids, codex_fetched, codex_age_s = load_codex_ids()
    claude_ids, claude_fetched, claude_stale, claude_file = load_claude_ids()
    print(f"codex cache: {len(codex_ids)} model ids, fetched_at={codex_fetched}, age={codex_age_s:.0f}s")
    print(f"claude cache: {len(claude_ids)} model ids, fetchedAt={claude_fetched}, stale={claude_stale}, file={os.path.basename(claude_file) if claude_file else None}")
    if not codex_ids or not claude_ids:
        print("WARNING: a cache is empty or missing; a real matcher must treat this as UNKNOWN, never as 'no models exist'.")

    roster = json.load(open(ROSTER))["agents"]
    bad = []
    for name, seat in roster.items():
        rt = seat.get("runtime") or "claude-code"
        model = seat.get("model")
        if model is None:
            continue
        ids = claude_ids if rt == "claude-code" else codex_ids if rt == "codex-cli" else None
        if ids is None:
            continue  # codex-subagent / codex-sol / custom runtimes: no local cache to check against here
        if model not in ids:
            bad.append((name, rt, model))

    print(f"\nroster seats whose pinned model is NOT in today's local catalogue: {len(bad)}")
    for name, rt, model in bad:
        print(f"  {name}  runtime={rt}  model={model}")
    if bad:
        print("\nThese are exactly the seats a discovery-only, no-web-search, no-invented-id catalogue check")
        print("would flag TODAY, with zero Laya involvement and zero model calls.")


if __name__ == "__main__":
    main()
