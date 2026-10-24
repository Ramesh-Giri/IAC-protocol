# {{PROJECT_NAME}} — Agent Workflow

## Read before implementation

Read `project-overview.md` and `progress-tracker.md`, then
`architecture-context.md`, `code-standards.md` and `ui-context.md` in this
context directory. Follow this workflow alongside the project's applicable
instructions and the user's current authorization. Context is not new authority.

## Work in small increments

{{PROJECT_APPROPRIATE_TASK_SIZING_AND_ACCEPTANCE_RULES}}

## Handle uncertainty explicitly

Distinguish confirmed requirements, observed implementation, proposals and
open questions. Do not invent missing product behavior. Record an open
question before dependent implementation; continue independent authorized
work when possible. Surface conflicting instructions rather than silently
choosing a different product or architecture.

## Scope and approval boundaries

{{PROJECT_SPECIFIC_DELEGATION_PROTECTED_AREAS_AND_APPROVAL_REQUIREMENTS}}

Do not treat this file as permission to launch agents, spend money, commit,
push, deploy or change another project. Never place credentials in context,
mail or logs. Respect existing generated-code ownership and project rules.

## Verification before completion

{{REQUIRED_CHECKS_EVIDENCE_AND_HOW_TO_REPORT_UNRUN_OR_FAILED_CHECKS}}

## Keep context and progress in sync

Update the relevant document when agreed scope, boundaries, storage,
contracts or standards change. In `progress-tracker.md`, record actual
completion with evidence, blockers, decisions and the next actionable step.
Plans are not completed work; file existence is not proof tests passed.

Main agents keep one `<project-context-dir>/OPERATOR_REQUESTS.md` ledger per operator across runtimes; follow [AgentMail operational rule 40](../../OPERATIONAL_RULES.md#40-keep-one-operator-requests-ledger).

## Document what you touch, report what you changed

- A source file you edit without a header doc comment gets one in the same
  change (line 1: what the file is for; then main functions, dependencies,
  users, side effects). Keep headers true; never add them in bulk.
- Every merged change ships a change report (`agentmail/bin/change-report`)
  in `docs/changes/`, and the project map (`agentmail/bin/project-map`) in
  `docs/map/` is regenerated on merge. IAC operational rules 27 and 28.

## Session handoff

{{CONCISE_PROJECT_SPECIFIC_HANDOFF_AND_OPTIONAL_IAC_COORDINATION_RULES}}
