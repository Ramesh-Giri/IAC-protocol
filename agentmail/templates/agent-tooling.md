# Recommended agent tooling (for IAC)

Generic, portable catalog of the agent/dev tools an IAC site can install to write
and review code better. All are **machine-global** installs (not part of any repo),
so each machine installs them once — cloning IAC does **not** bring them; run the
commands below (a bootstrap installer is planned so a clone can provision itself).

> Interim note: some of these (worktree pooling, zero-token supervision,
> heterogeneous workers) are being **folded natively into IAC**. Until that lands,
> use the standalone tools below. `firstmate` (a separate crew-orchestration distro)
> was the idea donor for that work and is intentionally *not* listed as a standing
> tool.

Skills and CLIs run with full agent permissions — review a tool before relying on
it, and check each project's own security scan.

## The code-quality core (use where it applies, not on trivial edits)

- **treehouse** — a pool of reusable, pre-warmed git worktrees so agents get an
  instant isolated environment (`treehouse get` / `treehouse return`) instead of
  re-cloning or hand-rolling `git worktree`. Install: `curl -fsSL
  https://kunchenguid.github.io/treehouse/install.sh | sh` (review the script
  first) or `go install github.com/kunchenguid/treehouse@latest`.
- **gh-axi** (from AXI, https://axi.md) — wraps the official `gh` with
  token-optimized, agent-ergonomic output for issues/PRs/CI/releases; roughly half
  to a fraction of raw `gh --json`/MCP tokens for the same result. Prefer it over
  raw `gh` for GitHub ops. Needs `gh` installed + authed. Install:
  `npm install -g gh-axi`.
- **no-mistakes** — a push-gate: intercepts `git push`, runs review/tests/lint/docs
  in a throwaway worktree, and only forwards + opens a clean PR if it passes. The
  pre-ship validation gate; don't bypass it for "quick fixes". Skill:
  `npx skills add kunchenguid/no-mistakes -g`; CLI: review + run its
  `docs/install.sh`.
- **lavish** (lavish-axi) — turns design/review decisions and reports into
  structured, inspectable records instead of prose lost in scrollback. Install:
  `npm install -g lavish-axi` (needs Node ≥ 22).

## Long unattended work
- **gnhf** — runs an agent autonomously in a loop toward an objective, one small
  committed change per iteration. Auto-commits + runs unsupervised, so point it at
  an **isolated worktree** and treat output as a **draft for review**, never an
  auto-merge. Set `GNHF_TELEMETRY=0`. Install: `npm install -g gnhf`.

## Adjacent (not part of the code loop)
- **skill-creator** — author/improve agent skills. `npx skills add
  anthropics/skills --skill skill-creator -g`.
- **OpenSuperWhisper** — local (on-device) voice dictation for the human operator.
  `brew install --cask opensuperwhisper` (Apple Silicon, macOS ≥ 14; needs mic +
  accessibility permissions granted by the human).

## Supporting AXI tools (dependencies of the above / of firstmate)
`tasks-axi` (backlog), `quota-axi` (quota-aware dispatch data),
`chrome-devtools-axi` (browser automation, optional): `npm install -g <name>` /
`npx -y chrome-devtools-axi`. The AXI design guidelines skill: `npx skills add
kunchenguid/axi -g`.

## When to reach for which
Typical shippable task: `treehouse get` → work (using `gh-axi` for GitHub, `lavish`
to record real decisions) → `no-mistakes` to validate + open the PR →
`treehouse return`. Use `gnhf` for long unattended objectives. Skip whatever a
given task doesn't need — the point is the right tool at the right moment, not
ceremony. (A ready-to-use skill encoding this, `iac-dev-workflow`, can be installed
into an agent's skills directory.)
