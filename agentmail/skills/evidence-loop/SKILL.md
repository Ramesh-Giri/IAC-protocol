---
name: evidence-loop
description: Execute a non-trivial IAC task through bounded evidence gathering, a committed plan, delegated implementation and independent adversarial verification. Use for multi-step or cross-module work whose correctness cannot be settled by one focused check.
---

<!-- Defines the evidence-to-plan-to-break workflow for one delegated outcome. -->
# Evidence loop

Read the [shared seat boundaries](../README.md#shared-seat-boundaries) and IAC rules 43, 44, 45, 48 and 52.
Keep this loop inside one accepted outcome; use ordinary focused verification for a small mechanical edit.

1. Record the requested outcome, product and technical owners, acceptance observations, assumptions, OWNS and NOT THIS ROUND.
   Distinguish a research question from permission to implement.
   Open the actual source and relevant primary documentation before relying on a signature or contract.
2. Ask the overseer to allocate independent evidence questions to mail-native seats in one bounded batch.
   Count authors, gatherers, checkers and break reviewers together against the site's five-worker cap; use fewer seats or sequence work when full.
   Children with `allow_subagents: false` send questions by mail and never create nested agents or hidden sessions.
   Require concise findings with source paths/revisions and disconfirming evidence.
   Allow one follow-up evidence batch; justify further research against the task's SPEND cap.
3. Write one plan in the project's established plan location: cited evidence, intended behavior, exact scope, approach, assumptions, execution checklist and checks that would refute success.
   Have the authorized writer/integrator commit it before behavior-changing implementation, and record its full SHA in the task thread.
   A Codex child unable to write Git hands off the plan for that commit; it does not bypass the restriction.
   Proceed within existing delegated authority after that prerequisite; send genuine product decisions, scope changes and L3 matters to the overseer.
4. Delegate implementation to the owning child in a treehouse lease, with one writer per tree.
   Reproduce a defect at the user boundary where feasible, then preserve genuine RED/GREEN unit and integration evidence under rule 43.
   If evidence contradicts intent, amend the written hypothesis and plan within ownership before editing another module.
   Route checks and builds through [build-gate](../build-gate/SKILL.md).
5. After focused checks and normal review, allocate a separate read-only break seat that did not author the implementation.
   Ask it to disprove the requirements locally using boundary, ordering, concurrency, recovery, permission, cost and visible-state cases.
   Require `BREAK.md` with numbered severity, reproduction, impact and a proposed failing regression test.
   Do not target live systems or let the break reviewer repair its own findings.
6. Have the overseer triage every finding with the author and operator under rule 43.
   Accepted fixes begin with a failing test and receive a focused re-break; leave no finding untriaged or accepted fix unverified.
   After three failed fix/verify cycles on one issue, stop and mail the hypothesis, attempts, evidence and missing decision.
7. Apply [acceptance-gate](../acceptance-gate/SKILL.md), then report the outcome, exact tested inputs, evidence, unresolved limits and next owner.
   Keep raw receipts outside the repo and batch the final readable report once stable.
