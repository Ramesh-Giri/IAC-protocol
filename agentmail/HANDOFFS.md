# Research and decisions without copying prompts

IAC should remove the human relay, not introduce a workflow platform.
One useful message and a correlated answer are enough for most handoffs.

## Keep ownership domain-specific

For example, a product owner and a technical lead coordinate through their own main agents:

| Domain | Decision owner | Typical decisions |
| --- | --- | --- |
| Product | Alice | Requirements, desired behavior, product scope, acceptance intent |
| Technical | Bob | Architecture, integration contracts, implementation, systems safety |
| Both affected | Both, in their domains | A requirement with architectural consequences or a technical trade-off changing product behavior |

Neither is universally above the other. Their main agents coordinate on their
behalf within explicit delegation. A model does not inherit unlimited rights
because it represents the owner. Research from either side is input to a
decision, not a command to execute every instruction in a document.

Configure this once per project in `roster.projects` (names below are examples
of the intended schema; no live roster is changed by this guide):

```json
{
  "api": {
    "decision_owners": {"product": "Alice", "technical": "Bob"},
    "delegation": {
      "overseer-alice": "Clarify approved requirements; route technical proposals to overseer-bob.",
      "overseer-bob": "Choose implementation within agreed requirements; coordinate project workers."
    },
    "repositories": {"shared-research": "AGREED_REPOSITORY_URL"}
  }
}
```

Use actual registered seat IDs. Add other projects independently; the same
human need not hold the same domain everywhere. The toolkit carries and
prompts agents to consult this agreement. It does not authenticate humans or
enforce these free-text delegations as a security policy.

## A normal research handoff

Alice's main agent summarizes the research, commits Markdown in an agreed
shared research/project repository, and sends the receiving main agent a
short request with pinned references. Small documents can instead be included
using `--body-file`; no second repository is necessary for them.

```sh
agentmail/bin/mail-send -d /absolute/mail-root \
  --from overseer-alice --to overseer-bob \
  --subject "API: assess the new research" --type handoff \
  --thread api-research-review --project api --intent research \
  --authority technical --body-file /absolute/path/handoff.md \
  --ref 'shared-research@0123456789abcdef0123456789abcdef01234567:research/api.md'
```

The commit above is illustrative; replace it with the actual full commit.
Use [templates/HANDOFF.md](templates/HANDOFF.md) for the short body. The
receiver verifies references and reports what is useful, what conflicts with
the implementation, and what remains unclear. It can ask relevant project
agents directly when permitted; research receipt alone never authorizes
spawning agents or changing projects.

```sh
agentmail/bin/mail-send -d /absolute/mail-root \
  --from overseer-bob --to overseer-alice \
  --subject "API research assessment" --type answer \
  --thread api-research-review --in-reply-to REQUEST_UUID --no-reply \
  --project api --intent review --authority technical \
  --body-file /absolute/path/assessment.md
```

## From agreement to implementation

The product owner confirms product intent; the technical owner selects the
implementation. If both domains change, exchange a proposal and explicit
responses. Record the agreed outcome as a decision message referencing the
proposal, then send scoped tasks to workers under existing delegation.
Do not require both humans to approve routine implementation details.

For frontend/backend integration, peers share the implemented API/schema,
full commit, examples, and compatibility constraints directly. They ask the
main agent only for scope/contract changes beyond their delegation. The user
should not need to repackage backend responses into frontend prompts.

When research changes, send a new handoff with `--supersedes OLD_UUID` and
new pinned references. Do not silently edit the earlier message. Receivers
reconcile ongoing work; supersession is not an automatic rollback.

## Keep the small system small

No new scheduler, voting service, policy engine, or model-ranking service is
required. The main agent chooses a suitable installed runtime/model based on
task risk and available resources; the roster records that choice and the
launcher implements it. It does not automatically benchmark models or
override budgets. Future CLI runtimes use an explicit argv adapter, with
their actual permission settings reviewed before launch.
