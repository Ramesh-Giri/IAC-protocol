# The Council — setup and operations

**1.1 bridge behavior:** only requests (`proposal`, `review`, etc., or explicit
`--request-reply`) invoke the CLI. FYIs and closing notices are acknowledged
without a model call. Replies carry `in_reply_to` and never request another
automatic reply. Failures stay unread; retry is bounded. See
[UPGRADE.md](UPGRADE.md) for `--once --retry-failed` recovery. Role text is
advisory; configure the command's actual read-only sandbox before running it.

Cross-model deliberation for consequential decisions. Concept in
ORCHESTRATION.md §7; this page is the practical guide: setting up council
seats, the commands, and the convening policy.

## 1. What a council seat is

An ordinary roster seat (`role: council`) with three properties:

- **Different vendor/model than the overseer** — the value is uncorrelated
  blind spots. A Claude overseer wants Codex/Gemini councilors, and vice
  versa.
- **Advisory only** — it reviews and attacks proposals; it never decides,
  never tasks anyone, never modifies repositories.
- **Usually bridged** — summoned headlessly per message, no live session.

No APIs anywhere: the bridge shells out to the CLI you already have, which
uses its own subscription sign-in (Codex CLI → ChatGPT account, etc.).

## 2. Setting up a council seat (one-time, per seat)

```bash
cd <your .agent-mail directory>

# 1. Create the seat's maildir and add it to roster.json (role: council)
<agentmail>/bin/agentmail-init codex-<site>

# 2. Install + sign in to the CLI once (no API key)
#    Codex:      npm i -g @openai/codex   && codex   (sign in with ChatGPT)
#    Gemini CLI: npm i -g @google/gemini-cli && gemini (sign in with Google)

# 3. Start the bridge — the seat now answers mail autonomously
<agentmail>/bin/mail-bridge codex-<site> -- codex exec --sandbox read-only --skip-git-repo-check -C <workspace>
#    Gemini variant:
<agentmail>/bin/mail-bridge gemini-<site> -- gemini -p -
```

Run the bridge persistently: a background process, a `tmux` pane, or a
launchd/systemd service. `--sandbox read-only` (or the vendor's equivalent)
is the council leash: the model can read code to form an opinion, and
nothing else.

**Interactive fallback (no bridge):** open the CLI in the mail root with
`templates/SEAT_AGENTS.md` installed as its instruction file (`AGENTS.md`
for Codex, `GEMINI.md` for Gemini) and say "check your mail". A GUI-only
app can't be bridged — use the CLI for seats.

Codex notes: `--skip-git-repo-check -C <workspace>` is required when the
workspace isn't a git repo; if the CLI is older than your account's model
you'll get a 400 in bridge.log — `npm i -g @openai/codex` fixes it. Bridge
failures go to stderr; redirect to `<mail-dir>/<seat>/bridge.log` if desired.
Retry receipts live in the seat's ignored `tmp/bridge-state/` directory.

## 3. Convening — the commands

Fan out one `proposal` per councilor, one thread for the whole deliberation:

```bash
for seat in codex-alice gemini-alice; do
  <agentmail>/bin/mail-send \
    --from overseer-alice --to "$seat" \
    --subject "Council: should /submit response add receiptUrl?" \
    --type proposal --thread council-submit-shape --ack <<'EOF'
PROPOSAL: <the decision, concretely>
CONTEXT:  <links to repo files/PRs/spec — councilors read, they don't guess>
QUORUM:   <e.g. majority decides; unanimity required; advisory only>
DEADLINE: <e.g. reply within 1h; convener proceeds without stragglers after>
ASK:      Verdict with: position, reasoning, confidence (low/med/high),
          and your strongest attack on the proposal.
EOF
done
```

Verdicts arrive as replies on the same thread (bridged seats answer
automatically). Collect, then close the loop **in the same thread** — the
ruling is part of the record:

```bash
<agentmail>/bin/mail-read overseer-alice        # verdicts land in your inbox

<agentmail>/bin/mail-send --from overseer-alice --to codex-alice \
  --subject "RULING: council-submit-shape" --type info --thread council-submit-shape \
  -m "Adopted with amendment X. Votes 2-1; dissent (version-pinning risk) noted and tracked as <task>."
```

Audit later: `grep -rl "council-submit-shape" <mail-dir>/*/cur/` — the full
deliberation, verbatim, forever.

## 4. Convening policy (the overseer's standing orders)

Convening is the **overseer's call under policy** — not a per-case question
to the human, or the council becomes an interruption stream. The shipped
policy (edit in your overseer's CLAUDE.md):

**Auto-convene — no human asked:**
- security-sensitive designs: auth, key custody, payment paths
- interface/contract changes that cross project or site boundaries
- plans the overseer itself authored and is about to self-approve at
  Layer 2 (self-review is the weakest review — buy an independent attack)
- genuine uncertainty: low confidence, or two children disagreeing

**Convene on request:** the human says "run this by the council" — explicit
always trumps policy.

**Never convene:** routine tasks, mechanical work, anything a test suite
already settles. A council on everything is latency theater.

**Reporting duty:** convening is silent; the outcome never is. The
overseer's next report states: convened, vote split, dissent summary.
The human sees every deliberation's result without pre-approving any.

**Seat selection:** default = every `role: council` seat (marginal cost of
one more subscription-auth verdict ≈ zero; diversity is the point). If the
roster grows specialist councilors, the proposal names its subset.

## 5. Health rules

- Council **advises, never decides** — authority stays overseer → human.
- Quorum declared in the proposal, not invented after the verdicts arrive.
- Dissent is preserved verbatim; it's the most valuable artifact when
  reality later disagrees with the majority.
- A bridged seat that stops answering (auth expired, CLI broken) fails
  loudly: the convener's deadline passes → it proceeds and *reports the
  absent seat* rather than silently shrinking the council.
