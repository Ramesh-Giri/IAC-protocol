# Upgrade to IAC 1.1

This is an upgrade to the file helpers, not a migration to a service.
Existing Markdown mail stays readable; no bulk rewrite is needed.

## What changed

- UUID filenames and no-overwrite delivery/acknowledgement.
- Registered seats, safe headers, symlink/traversal checks and advisory seat binding.
- Per-seat session/consumer/watcher locks; one local sync/transport lock.
- Failed bridge requests stay unread, retry at most three times by default,
  and can be recovered explicitly. Cached successful responses have stable IDs.
- Notifications do not invoke a model or trigger reply loops.
- Exact reply correlation and research/requirements/decision handoff metadata.
- Local site/home settings are separate from the shared roster.
- Claude and Codex interactive launch support, plus explicit custom CLI argv.
- Dedicated-repository-only Git sync, payload checks and bounded Git commands.
- Dashboard reply debt excludes FYIs and distinguishes a possible wait cycle
  from proven deadlock. Old ID-less mail still uses a less reliable heuristic.

## Rollout checklist

1. Preserve a backup of the current mail repository and local configuration.
   Arrange a quiet upgrade window and stop old consumers, bridges and sync
   loops on each site yourself. Do not start a second set beside old ones.
2. Update the **whole `agentmail/` directory**, including `lib/`; copying one
   executable no longer works. Requires Python 3.9+, Git, macOS or Linux.
   The helpers use only the standard library. Keep the toolkit outside the
   dedicated mail repository; use its absolute `bin/` paths in seat instructions.
3. Verify every sender and recipient appears in `roster.agents`. `agentmail-init`
   creates a stub only for a new spool; adding maildirs to an existing spool
   still requires the roster owner's explicit roster update.
4. For multiple sites, create ignored `MAIL_ROOT/local.json` from
   `templates/local.example.json`. Set your actual site and local home paths.
   `--site` overrides `AGENTMAIL_SITE`, which overrides the local file. A unique
   hostname match or a sole site may be inferred, never the roster owner's site.
5. Add project decision owners/delegation using [HANDOFFS.md](HANDOFFS.md).
   Update seat instructions to use request IDs, `--no-reply` for final answers,
   and the actual mail root. Use `AGENTS.md` for Codex, `CLAUDE.md` for Claude.
6. Inspect `git ls-files` in a dedicated mail clone before enabling sync.
   `tmp/`, `.locks/`, `local.json`, bridge logs and toolkit code must not be
   tracked. Back up and explicitly untrack local files if necessary; the helper
   refuses to do that destructively for you. Removing a secret from the index
   does not erase its history; rotate exposed credentials.
7. Embedded channels inside product repositories remain valid for mail,
   but **cannot use automated `mail-sync`**. Use explicitly scoped manual Git
   operations or agree on a separate mail repository. Do not initialize or
   rewrite another Git repository without checking the existing layout.
8. For a pre-existing remote, clone it or configure its intended upstream.
   Do not create unrelated history and expect automatic reconciliation.
   Resolve any Git conflict manually; the helper never force-pushes or guesses.
9. Run the offline tests below, then inspect `agentmail-launch --seat SEAT
   -d MAIL_ROOT --site YOUR_SITE` (dry run). Only use `--apply` when authorized.
   The new runner refuses duplicate cooperating sessions for a seat. It cannot
   lock old or manually launched sessions that bypass it.
10. Resume one consumer per seat on its home site and one sync loop per clone.
    Validate a harmless test request/reply between sites before assigning work.

```sh
python3 -m unittest discover -s agentmail/tests -v
python3 -m unittest discover -s agentmail/dashboard/tests -v
```

## Bridge recovery and safety

`mail-bridge SEAT -d MAIL_ROOT --once -- COMMAND...` performs one pass.
Use `--timeout SECONDS` and `--max-attempts N` to bound execution. After fixing
the failure, `--once --retry-failed` permits exhausted requests to retry.
Diagnostics go to stderr; redirect them to a private log if desired. CLI stderr
is not saved automatically because it may contain credentials. Exit code 1
means at least one request failed or could not be processed in that pass.

The command must read stdin and put only the final answer on stdout. Configure
its sandbox yourself; council commands should be read-only. A successful
process exit is not proof of correct work. Verify task results separately.
The interactive launcher keeps Codex in workspace-write/on-request mode;
Claude uses normal permissions by default. Codex flags follow the
[official CLI reference](https://developers.openai.com/codex/cli/reference/).
Permission bypass is explicit,
Claude-worker-only, and is not made safe by the mail protocol.

## Honest limits

There is no exactly-once task execution, automatic distributed cancellation,
cryptographic sender authentication, or automatic conflict resolution.
Locks coordinate local cooperating helpers, not different machines. Keep one
home site per inbox. Watchers announce pending mail again after restart;
consumers, not watchers, own acknowledgement. The dashboard's bounded mail
window cannot establish complete all-time task state.

Older operational/design documents describe intent and historical approaches.
Where they differ, the 1.1 [SPEC.md](SPEC.md) and this upgrade guide govern the
bundled helpers. No live network is migrated merely by updating the toolkit.
