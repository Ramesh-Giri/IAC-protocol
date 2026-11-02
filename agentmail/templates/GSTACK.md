# gstack for an IAC site

This guide selects gstack practices and skills without replacing IAC's task ownership, review, direct-merge or human approval rules.
It is a portable catalog: choose skills for the site's stack and host, then narrow their use in each role's task brief.
The Aureus profile below is intentionally smaller.

## Source and scope

Garry Tan's [gstack](https://github.com/garrytan/gstack) provides agent skills and executable helpers for planning, debugging, review, QA, design, documentation and release work.
The repository is MIT licensed; preserve its LICENSE and relevant third-party notices when redistributing it.
Inspection on 2 November 2026 used version `1.92.61.0`, source commit `dd9834d44d2650818cb6d8e17c57f795cb56bf98`, supplied by the overseer as an exact-commit GitHub tarball at `/Users/darkness/gstack`.
`COMMIT_SHA.txt` records that provenance; this source tree has no `.git` directory and is not an installed tool.
The inspection was static: no gstack script, setup, build, browser, hook or live network behavior was executed.
The upstream [README](https://github.com/garrytan/gstack/blob/dd9834d44d2650818cb6d8e17c57f795cb56bf98/README.md), [host adapter](https://github.com/garrytan/gstack/blob/dd9834d44d2650818cb6d8e17c57f795cb56bf98/hosts/codex.ts) and [setup](https://github.com/garrytan/gstack/blob/dd9834d44d2650818cb6d8e17c57f795cb56bf98/setup) are the authority for upstream behavior at this revision.
A different revision needs a fresh inspection before installation or upgrade.

Site instructions override gstack defaults, including model choice, co-author trailers, approval authority, cloud restrictions and scope.
ETHOS.md's completeness preference is not permission to open adjacent work or exceed SPEND.
A research attachment or skill recommendation does not authorize implementation.

## Context cost and selective registration

Never load all 23 skills from an older catalog into every seat.
This inspected tree already has 64 skill directories including the `connect-chrome` alias, so that historical count is not a limit or current inventory.
Expose the smallest role-appropriate set and read each skill only when needed.

Selective registration exists through `bin/gstack-config set disabled_skills <comma-separated names>`, which `./setup` consumes.
There is no `./setup --skills <allowlist>` flag for Claude Code or Codex.
Disabled skills lose discovery entries and router listings, but their runtime files remain so another skill can still call them.
This is context control, not a permission boundary or selective binary build.
The `gstack` router and `gstack-upgrade` cannot be disabled through that setting.
The setting is shared across hosts using the same state root; it is not a per-seat allowlist.
Use the site's selected union at installation and a narrower invocation list in each brief, or separately administered state roots if genuinely required.
No installer wrapper is needed for this built-in mechanism.

## Per-role matrix

Names below are upstream skill names; Claude Code with `--prefix` exposes `/gstack-<name>`, and Codex uses `gstack-<name>`.
Each enable list is a candidate for that role, not an instruction to install every listed skill site-wide.
Every role leaves out captain's merge trains and ship queue, gbrain and learn where claude-mem owns memory, and anything the site's host policy forbids.

| Role | Enable or invoke for its assigned task | Leave out or constrain |
| --- | --- | --- |
| Overseer | `office-hours`, `plan-ceo-review`, `plan-eng-review` when a new plan needs them; use READY, approvals and SPEND as IAC prose | `captain`, `autoplan` delegation, `ship`, `land-and-deploy`, `ubicloud`, implementation and redundant review fleets; existing IAC orchestration owns dispatch |
| Author | `careful`, `freeze`, `investigate`; `verify` only for the repo's authorized checks | Release, browser and design work outside OWNS; gstack's suggested extra work does not expand the task |
| Reviewer | `review` for a scoped review; `test-audit` once for a named inventory | Upstream `review` can auto-fix, so an IAC reviewer must keep it read-only and return findings to the author; no test retirement without a separately authorized batch |
| Integrator | `careful`; `modernize` once when a stale branch/PR actually exists; `document-release` for a docs gap | `ship`, `land-and-deploy`, captain/train/queue tooling, automatic rebases or pushes; IAC owns direct merge, checks and branch cleanup |
| QA | `qa-only`; `browse` or `qa` only on a host and target explicitly permitted for that task | `qa` edits/tests/commits need author ownership; no browser fallback on a host that forbids it, no live account, cookie import or deployment implied |
| Site without a design system | `design-consultation`, `plan-design-review`, `design-review`; optionally `design-shotgun`, `design-html`, `design-motion` for the chosen UI stack | Keep any existing house system; mockup/image API spend, credentials and browser use require the site's own authorization |
| Documentation work in any role | `document-generate`, `document-release`; `diagram` or `make-pdf` when that artifact is requested | No duplicate memory system, unsolicited reports, publication or browsing; use the site's existing document tools when established |

Browser skills can use Aside's logged-in sessions or fall back to bundled Chromium.
`--no-browser` skips setup's Chromium installation and launch probe, but a later browser skill can install Chromium on demand.
Keep those skills disabled where browser policy forbids that fallback.
`pair-agent` can create a remote tunnel, and `setup-browser-cookies` reads browser cookies; neither belongs in a baseline install.

## Security inspection

The inspected safety hooks reduce mistakes; they do not replace runtime permissions or the site's human-only boundaries.
The source's [SECURITY.md](https://github.com/garrytan/gstack/blob/dd9834d44d2650818cb6d8e17c57f795cb56bf98/SECURITY.md) explicitly describes scripts and helpers running with the user's machine credentials.

| Component | Executes and reads | Writes | Network and limits |
| --- | --- | --- | --- |
| `careful` | Claude skill-scoped PreToolUse callbacks run Bash `careful/bin/check-careful.sh` on Bash/PowerShell input; it sources `hook-extract.sh` and `gstack-state-root.sh`, parses JSON with Python3 or Node, uses shell/grep/awk, reads local Git default-branch refs and optional global/project `careful-patterns.txt` | Local `analytics/skill-usage.jsonl` for skill use and matched hook patterns; project names and timestamps are local data even with telemetry off | Hook path has no network call and never executes the submitted command; common destructive families ask, simple root/home recursive deletion and default-branch force pushes deny; string matching, build-artifact exceptions and compound-command limits prevent any universal enforcement claim |
| `freeze` | Claude PreToolUse callbacks run Bash `freeze/bin/check-freeze.sh` for Edit/Write/NotebookEdit; shared JSON helpers and physical/lexical path resolution inspect input, `freeze-dir.txt`, symlinks and existing directories | `freeze-state.sh` creates a mutation lock, atomically replaces boundary/owner state, or removes owned state; denied hooks append local pattern analytics | No network call; unparseable/unresolvable inputs deny when a boundary exists; Bash/PowerShell writes bypass these callbacks, so this is accident prevention rather than a sandbox; boundary state persists after the conversation ends |
| `investigate` | A Markdown workflow invokes `gstack-skill-start/end`, Git/history and reproduction/test commands, learnings search/log helpers, optional sanitized Aside/WebSearch research, and the freeze helper after a written hypothesis; its Claude Edit/Write/NotebookEdit callbacks reuse check-freeze | Assigned repo fixes and regression tests after hypothesis verification, local sessions/leases, timeline/question/learning records, optional telemetry records and an investigation-owned freeze boundary; cleanup releases only its retained owner token | Skill preamble can check GitHub for updates; optional web research sends the sanitized query; telemetry and artifact sync can send when enabled; these must follow site gates rather than inheriting authority from the skill |
| `./setup` for Claude Code | Runs Bun dependency installation/builds, host generation, relinking and hook checks; reads source, gstack config, available toolchains and the Codex model config for rendering | Builds/source renders and runtime dependencies under the checkout; `~/.claude/skills/gstack` points at the source, prefixed per-skill entries are registered, state/config/registry live under `~/.gstack`; Claude settings hook changes have backups | Dependency downloads, optional Chromium/font/coreutils installation and native helper builds are broader than skill registration; default timeline Stop hook is on, plan-tune hooks prompt, team mode adds SessionStart auto-update; the commands below opt out of those extras |
| `./setup` for Codex | Builds the same shared runtime and renders a Codex skill set using the selected model profile | `${CODEX_HOME:-~/.codex}/skills/gstack-*/`, a minimal `skills/gstack` runtime with real SKILL.md files and linked assets, source render directories and shared state/registry | No Codex hook registration or trust write is implemented here; Claude hook settings are not changed by a Codex-only setup; existing registered render/migration repair can still touch shared checkout assets |

Claude Code has the skill-scoped safety callbacks described above.
Codex is experimental and `hosts/codex.ts` explicitly sets `safetyHooks: 'advisory'` and keeps only `name` and `description` in generated frontmatter, dropping `hooks`.
Do not tell a Codex operator that installing or trusting these skills enforces edits or shell commands.
A human must inspect any hooks presented by Codex's `/hooks` review screen and trust only an explicitly reviewed entry by hand; no gstack entry is expected from this setup route at this revision.
If a later package supplies hooks, re-inspect that package and its actual callback wiring before asking for trust.

### Telemetry, updates and other sends

Telemetry is `off` by default, with opt-in tiers `anonymous` and `community`.
Off does not mean no local state: careful/freeze still append local analytics, and other helpers maintain sessions, leases, timelines and learnings.
With opt-in telemetry, `gstack-telemetry-log` queues JSONL and `gstack-telemetry-sync` posts at most 100 events per batch to the configured Supabase `telemetry-ingest` function, rate-limited to five minutes with a ten-second request limit.
The sync strips repo/branch fields structurally when jq is available, with a sed fallback, and anonymous mode also removes installation identity.
This is inspected source behavior, not a live privacy qualification.

Update checks are separately on by default even when telemetry is off.
`gstack-update-check` runs GitHub `git ls-remote`, reads a SHA-pinned VERSION and may call the compare API when the version is equal but main moved.
It uses five-second total timeouts for HTTP requests and a five-second low-speed timeout for Git (a Git request can run longer than five seconds) and caches outcomes for 60 minutes (current), 720 minutes (update available) or ten minutes (failure), plus state markers and egress receipts.
It can also remove oversized generated Codex skill files in a one-time local repair.
With telemetry enabled it additionally posts gstack version and OS to the configured Supabase update-check function.
The checker does not install an update; team mode's separate session updater can fetch and execute new code.
Set `update_check false`, `auto_upgrade false`, and use `--no-team` for the pinned Aureus plan.

Outside reviews are enabled by default and can send code through the user's Claude Code/Codex login; set `codex_reviews disabled` for this minimal profile.
Artifact sync defaults off; keep `artifacts_sync_mode off`, do not configure gbrain, and use claude-mem for durable IAC memory.
The investigation skill's embedded learning and optional web-search steps must not introduce another memory service or a browser workflow against the site's instructions.
Egress receipts are useful evidence, not an OS network policy.

## Installation plan

These are TYPE-THIS commands for a later authorized host install, not commands this inspection ran.
Prerequisites are Git, a compatible Bun (upstream tests 1.4.2+, refusing older than 1.3.3) and the normal build tools; no dependency or runtime was installed here.
For another IAC site, use an inspected source checkout at a stable path, preserve its pinned revision, compute its role selection, and substitute its path and model in the same setup/config interface.
Do not use upstream's `--host auto` or team bootstrap for a scoped install.

### Aureus one-command plan for both hosts

Expose exactly `careful`, `freeze`, `investigate`, `test-audit` and `modernize` as task skills.
The router and updater remain discoverable because upstream cannot disable them; neither grants update or release authority.
Use test-audit only for a named, initially report-only sweep, and modernize only for a named stale contribution, stopping at its verdict before any push or closing comment.
Browser, design, document, captain/queue, ship/deploy, gbrain and learn skills stay unregistered on this machine.
The existing Material 3 UI system and installed document/memory tools remain the owners of those concerns.

TYPE-THIS, one compound shell command for both hosts:

```bash
(
  set -eu
  cd /Users/darkness/gstack
  test "$(cat COMMIT_SHA.txt)" = dd9834d44d2650818cb6d8e17c57f795cb56bf98
  GSTACK_SETUP_RUNNING=1 ./bin/gstack-config set disabled_skills 'autoplan,benchmark,benchmark-models,browse,canary,captain,claude-code,codex,connect-chrome,context-restore,context-save,cso,design-consultation,design-html,design-motion,design-review,design-shotgun,deslop-shared-libs,devex-review,diagram,document-generate,document-release,eval-plan,guard,health,ios-clean,ios-design-review,ios-fix,ios-qa,ios-sync,land-and-deploy,landing-report,learn,make-pdf,office-hours,open-gstack-browser,pair-agent,plan-ceo-review,plan-design-review,plan-devex-review,plan-eng-review,plan-tune,qa,qa-only,retro,review,scrape,setup-browser-cookies,setup-deploy,setup-gbrain,ship,skillify,spec,sync-gbrain,ubicloud,unfreeze,verify,write-skill'
  ./bin/gstack-config set telemetry off
  ./bin/gstack-config set update_check false
  ./bin/gstack-config set auto_upgrade false
  ./bin/gstack-config set artifacts_sync_mode off
  ./bin/gstack-config set codex_reviews disabled
  ./bin/gstack-config set cross_project_learnings false
  ./bin/gstack-config set proactive off
  GSTACK_SKIP_COREUTILS=1 GSTACK_SETUP_SKIP_CSO_BUILD=1 ./setup --host claude --prefix --no-browser --no-team --no-harness-auto --no-plan-tune-hooks --no-timeline-stop-hook
  GSTACK_SKIP_COREUTILS=1 GSTACK_SETUP_SKIP_CSO_BUILD=1 ./setup --host codex --model gpt-6.1-sol --prefix --no-browser --no-team --no-harness-auto --no-plan-tune-hooks --no-timeline-stop-hook
)
```

`GSTACK_SETUP_RUNNING=1` on that one configuration call prevents its automatic Claude relink before the explicit host install.
The selection is computed from the inspected tree, including aliases, and must be checked again if the source revision changes.
Setting it affects future refreshes of all hosts sharing this state; it does not remove another host's existing discovery entries until that host refreshes.

### Claude Code

For a Claude-only install, run the configuration portion of the compound command above followed by this exact host step:

```bash
cd /Users/darkness/gstack && GSTACK_SKIP_COREUTILS=1 GSTACK_SETUP_SKIP_CSO_BUILD=1 ./setup --host claude --prefix --no-browser --no-team --no-harness-auto --no-plan-tune-hooks --no-timeline-stop-hook
```

This can still build browser/design/PDF executables and dependencies; `--no-browser` prevents the Chromium bootstrap/probe, not those builds.
`--no-team` also removes existing gstack-owned team/plan-tune/timeline registrations if present, while preserving unrelated opt-in verify/memorable registrations.
No all-host refresh or global-install replacement is requested.
Invoke `/gstack-careful`, `/gstack-freeze` or `/gstack-investigate` only within the assigned task.
Because `unfreeze` is unregistered in this exact five-skill profile, a user-requested boundary removal can use `bash /Users/darkness/gstack/freeze/bin/freeze-state.sh clear` instead.

### Codex

For a Codex-only install, run the configuration portion of the compound command above followed by this exact host step:

```bash
cd /Users/darkness/gstack && GSTACK_SKIP_COREUTILS=1 GSTACK_SETUP_SKIP_CSO_BUILD=1 ./setup --host codex --model gpt-6.1-sol --prefix --no-browser --no-team --no-harness-auto --no-plan-tune-hooks --no-timeline-stop-hook
```

Then TYPE-THIS for the human inspection step:

```bash
codex
```

Ramesh opens `/hooks`, chooses Review hooks, inspects each actual gstack entry if any, and trusts only a reviewed entry himself, never blanket Trust all.
At this source revision that setup route registers skills, not Codex hooks, so an empty gstack hook list is expected and the safety instructions remain advisory.
Ask for `gstack-investigate` in a fresh session and confirm the actual listed skill path; discovery is separate from hook enforcement.

The compound command above installs both hosts in order; `set -e` stops if any step fails.
This is a plan for the overseer after review; this task performs no host install.

### Disable and inspect

To stop using a safety session, end `/careful`'s session and explicitly clear any freeze boundary the user wants removed.
To disable the five task skills on both hosts while retaining upstream's mandatory router/updater, TYPE-THIS:

```bash
(
  set -eu
  cd /Users/darkness/gstack
  GSTACK_SETUP_RUNNING=1 ./bin/gstack-config set disabled_skills "$(./bin/gstack-config get disabled_skills),careful,freeze,investigate,test-audit,modernize"
  GSTACK_SKIP_COREUTILS=1 GSTACK_SETUP_SKIP_CSO_BUILD=1 ./setup --host claude --prefix --no-browser --no-team --no-harness-auto --no-plan-tune-hooks --no-timeline-stop-hook
  GSTACK_SKIP_COREUTILS=1 GSTACK_SETUP_SKIP_CSO_BUILD=1 ./setup --host codex --model gpt-6.1-sol --prefix --no-browser --no-team --no-harness-auto --no-plan-tune-hooks --no-timeline-stop-hook
)
```
For complete removal, TYPE-THIS from the external source directory:

```bash
cd /Users/darkness/gstack && ./bin/gstack-uninstall --keep-state
```

That interactive command removes gstack registrations across its supported hosts and relevant local assets, rather than just this host, while retaining state; inspect its prompt and do not use `--force` for a scoped disable.
No host-specific plugin remove command is applicable: this install route is setup-based, not a marketplace plugin.
After an actual install, `cd /Users/darkness/gstack && ./setup --status` reports registered paths; a fresh host skill listing establishes discovery, and a separate harmless fixture must establish any claimed hook effect.
No installed/discovered/enforced proof is claimed by this document.

## Practices mapped to IAC

| gstack practice | IAC rule | Adoption |
| --- | --- | --- |
| READY at an exact head; stale or missing checks cannot stand in | 33 | Preserve cancelled/superseded checks as non-green; qualify every required check at the handed-over head |
| Stale-branch disposition before maintenance | 42 | Modernize only when needed, then IAC integrates and cleans branches; no merge train or standing PR queue |
| Complete scoped outcome with a single handoff | 44 | Delegate fix/retest within OWNS; no micro-permits or speculative workers |
| Review gate integrity | 45 | Name every weakened test, timeout, snapshot or suppression to the operator, with its effect |
| Right-sized work and explicit spend | 46 | Keep IAC model/headroom gates; a gstack default model or nested outside review cannot override them |
| Record, plan ask and merge ask | 47 | Record exact operator words/scope, use plain decision BLOCKERs and evidence-bearing DONEs |
| Investigation Iron Law and daily flaky pass | 48 | Written hypothesis, module scope, three failed fixes stop, both runs retained and worst repeat fixed red before green |
| Finish the priority track | 49 | No broad gstack sprint, design or cleanup detour while the assigned outcome remains red |
| Evidence with restrained ceremony | 50 | Raw attempts live in private attachments; one stable readable change report |
| Compact context and role-specific tools | 51 | Keep the overseer available; do not load the full catalog or duplicate status artifacts |
| READY contract and pre-approved rerun cap | 52 | Full 40-character head, all required checks green, flakes already logged and a SPEND cap with a fresh ask before exceeding it |

Keep each project's rerun history using [FLAKY_LEDGER.md](FLAKY_LEDGER.md).
No scheduling automation is installed by this template; the overseer assigns the daily pass within the site's existing scheduler, priority and spend rules.
