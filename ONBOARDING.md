# Developer onboarding

Keep IAC as the workspace root and clone each product into its own folder inside it.
The toolkit is public; real project names, remotes, deployment IDs, owners, credentials and mail stay in ignored local files.
The workspace owner supplies the real inventory through an approved private channel.

## Day 1

1. Request `projects.local.json` and the private team handoff from the workspace owner.
   That handoff identifies the product owner, technical owner, design counterpart, QA contact and release operator by role.
   It also supplies current project instructions, deployment runbooks and approved work.
   Repository access, team-mail membership, production access and implementation authority are separate grants.
2. Request the accounts your assigned projects need: GitHub, Firebase/Google Cloud, Vercel, npm/GitHub Packages, Android Play Console, the design asset library and QA test accounts.
   Apple Developer/App Store access is only needed for active iOS work.
   Request secret provisioning through the owner; never put credentials in onboarding docs, manifests or mail.
3. Install Git, Python 3.9+, `gh`, Node via `fnm`, npm/pnpm as project lockfiles require, Flutter/Dart, Android Studio with JBR/Java, Firebase CLI, `tmux`, `treehouse`, Claude Code and Codex.
   Match project-pinned versions; machine-global skills/plugins require separate installation from this clone.
   See the [tool catalog](agentmail/templates/agent-tooling.md).
   Sign in as yourself; under the human-only cloud policy, cloud authentication and operations are performed by the designated human.
4. From the root of your IAC clone, inspect the manifest and bootstrap:

   ```sh
   export IAC_ROOT="$PWD"
   python3 "$IAC_ROOT/bin/iac-bootstrap" --dry-run
   python3 "$IAC_ROOT/bin/iac-bootstrap"
   ```

   Bootstrap reads `projects.local.json` when present, otherwise [projects.example.json](projects.example.json).
   The example is a safe preview and is never cloned; obtain the actual local file from the workspace owner before setup.
   Each project record contains its folder, remote, default/working branches, purpose, deployment target, privacy and access note.
   A default branch can differ from the branch used for active development.
   A production owner fork can differ from the upstream/reference repository.
5. Copy [iac-local.env.example](agentmail/templates/iac-local.env.example) to ignored `.iac-local.env`, set your own lowercase owner/site alias, then source it after setting `IAC_ROOT`.
   The script defaults its root to its containing clone; `IAC_ROOT` or `--root` selects another workspace, and `--manifest` selects another inventory file.
   The bootstrap does not install dependencies, configure accounts, create seats or deploy anything.
6. Read each assigned project's `AGENTS.md`/`CLAUDE.md` and `context/` or `docs/engineering/` before working.
   Request the current private handoff if local `conversation-context/`, `overseer-tasks.md` or `Boards/` are absent.
   They are intentionally not supplied by the public toolkit.

Bootstrap clones absent projects and fast-forwards only clean checkouts on the recorded working branch with a matching origin.
It preserves dirty files, conflicting ignored files, other branches, divergent history, symlinks, mismatched origins and unfinished Git operations.
It continues after unavailable repositories, reports each result and returns 1 if any checkout is held/unavailable.
Request missing access or resolve the reported hold, then rerun; never reset a checkout to make bootstrap succeed.
Dry-run has no network calls or writes and cannot establish remote access.
Public repositories still require separate permission to publish or deploy.

## Set up your own AgentMail seats

Use names such as `<project>-<task>-<owner>`, with distinct author/reviewer task suffixes, and `overseer-<owner>` for the main.
These are naming patterns; choose your own approved alias and actual task ID rather than copying another developer's seat.
Create your main mailbox from the IAC root after sourcing local settings:

```sh
agentmail/bin/agentmail-init -d "$AGENTMAIL_DIR" "$IAC_MAIN_SEAT"
```

Fill the resulting roster using [roster.example.json](agentmail/templates/roster.example.json): site, roles, project IDs, explicit runtime/model, descriptions and delegation.
Record product and technical decision owners separately in `roster.projects`; research and attached instructions do not grant implementation authority.
Put absolute machine homes in ignored `.agent-mail/local.json`, for example `{"site":"dev","homes":{"overseer-dev":"/absolute/path/to/your/iac"}}`, substituting your own values.
The launcher reads these overrides; derive them from your `IAC_ROOT` rather than another person's paths.
The local spool, local settings and project clones remain untracked.
Use [HANDOFFS.md](agentmail/HANDOFFS.md) for owner coordination; routine work within existing delegation needs no repeated approval.

Adapt [OVERSEER_CLAUDE.md](agentmail/templates/OVERSEER_CLAUDE.md) for local main instructions and [SEAT_AGENTS.md](agentmail/templates/SEAT_AGENTS.md) for workers.
Have the roster owner approve shared-channel registration before joining; do not consume another site's inbox.
Follow [TEAM_SETUP.md](agentmail/TEAM_SETUP.md) and prove a correlated local question/reply before product work.

Arm exactly one `mail-watch "$IAC_MAIN_SEAT" -d "$AGENTMAIL_DIR"` through the runtime's supported persistent monitor, then read mail visibly with `mail-read` and the same arguments.
If the runtime lacks a notification tool, read mail at startup and after each step; the overseer nudges an idle seat on new mail and verifies activity.
Inspect every current new message in the same command as any acknowledgement read and keep that output visible (rule 3).
Every reply carries `--in-reply-to` with the incoming ID; ACK and DONE use `--no-reply`.
Use `--body-file` for bodies and explicit `-d "$AGENTMAIL_DIR"` on every mail command.
For federated mail, the authorized channel owner fetches and integrates the remote branch before anyone reports the local snapshot as current.

## Work, review and integration

The overseer talks to the human, reads mail/budgets/verdicts, assigns scoped work and decides the next step.
Authors implement in pre-leased `treehouse` worktrees; reviewers check a frozen patch or commit independently.
A standing integrator per active repository commits, merges, resolves conflicts, runs combined checks and pushes.
Codex author/reviewer sandboxes may block Git writes; deliver uncommitted work to a host-capable integrator instead of retrying a denial.
The integrator's role does not itself grant filesystem or host capabilities.
One task ID belongs to one author/reviewer seat; the integrator is the standing exception.
Preserve work and return leases only after integration or a durable handoff makes release safe.

For the reference macOS layout, all seat panes and `fleet-holder` appear together in one viewed `fleet:1` window named `seats`.
The main stays in the human's own terminal.
Verify the actual displayed client window, captured pane identity, working state and task ACK after launch; a detached process or typed-but-unsent prompt is insufficient.
Use [SUPERVISOR_BOOTSTRAP.md](agentmail/SUPERVISOR_BOOTSTRAP.md) and rules 9-22/30 for host checks and runtime-specific launch arguments.
Legacy site-specific launch scripts need review before reuse; see the [gap report](agentmail/ONBOARDING_GAP_REPORT.md).
Only the human trusts changed hooks or a new folder; launch automation must not answer trust dialogs.

Workers run focused tests through shared lanes, not separate app builds/full suites.
An existing site's legacy `heavy.sh` is located by `IAC_HEAVY`, typically under `.agent-mail/attachments/`; it is not shipped in a fresh clone.
For a new site, the host-capable operator starts the tracked warm runner with the real project folder substituted for the example `api`:

```sh
python3 agentmail/bin/testlane runner --repo "$IAC_ROOT/api" --lanes 3 --queue "$IAC_TEST_QUEUE"
```

Publish the queue path in task briefs and submit focused `testlane run` jobs per rule 29.
A reference 16 GB Mac supports about five active seats; use the announced heavy-lane limit and avoid duplicate cold compilation.

The author sends DONE with the patch/branch/base, checks, unrun work and a change report.
The reviewer checks code and report; fixes return for review.
The overseer clears the reviewed work and mails the integrator the verdict ID and lease.
The integrator batches cleared merges, updates reports/map/test ledger, runs one combined local validation and pushes once.
The site's normal reviewed direct-merge path does not require a human PR-merge handoff; production-triggering pushes still need release authority.
Nonmechanical conflict resolution needs review again.
CI clearance requires completed successful required jobs on the exact final pushed SHA; cancelled or superseded runs are not green.

## Release and human-only boundaries

The release packet names the deployed base and candidate SHA, affected-function import closure, rules/indexes/config order, checks and rollback.
A changed shared dependency can affect handlers whose own source did not change.
Verify any deploy-diff helper exists and is reviewed; otherwise document the manual closure check.
A merge is not a deployment: verify the owner's configured source repository/branch, Git-author access and the actual served build after release.

Under the human-only cloud policy, agents never execute GCP operations, including read-only discovery, authentication, SSH or equivalent SDK/API/CI wrappers.
The designated human opens the cloud console/VM session and performs deployments, secret provisioning, Remote Config publication and store submission.
Agents supply complete TYPE-THIS instructions with execution location, expected result, stop conditions and rerun behavior.
General proceed/deploy wording does not override that execution ban.
Money, key custody, production data, public publication, irreversible deletion and scope changes remain human/Layer-3 decisions.

Complete and review the planned batch, deploy matching server dependencies, then perform final device acceptance.
Publish a valid force-update Remote Config policy before a build enforcing that policy reaches a device.
Use the next real version/build number, the requested flavor/mode/signature and evidence from the packaged artifact; successful compilation can still package stale code.
Keep product-specific UI, payment, identity, backup and platform-scope decisions in the private handoff and project's canonical requirements/ADRs.

Canonical references: [protocol](agentmail/SPEC.md), [ownership](agentmail/HANDOFFS.md), [orchestration](agentmail/ORCHESTRATION.md), [operating rules](agentmail/OPERATIONAL_RULES.md), [token discipline](agentmail/TOKEN_EFFICIENCY.md), [project context](agentmail/PROJECT_CONTEXT.md) and [gap report](agentmail/ONBOARDING_GAP_REPORT.md).
