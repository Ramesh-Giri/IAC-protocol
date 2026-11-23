---
name: scheduled-loop
description: Prepare or revise an IAC scheduled or overnight agent run with a charter, independent outcome check, bounded runner and explicit stop conditions. Use when asked for recurring autonomous work or an overnight run; reading this skill alone does not authorize scheduling.
---

<!-- Defines preparation and qualification of one bounded recurring outcome, without installing a scheduler. -->
# Scheduled loop

Read the [shared seat boundaries](../README.md#shared-seat-boundaries), IAC rules 44, 48, 49, 51 and 52, and the [overnight lessons](../../templates/agent-tooling.md#running-a-long--overnight-autonomous-run-safely).
Use a deterministic script for work that needs no judgment.

1. Write a charter for one phase in the project's existing documentation location.
   Record the outcome, product/technical owners, permitted paths, source baseline, schedule/timezone, runtime/model, mail seat, reviewer and explicit authorization for recurrence.
   Name the independent source of success and any measured baseline; write `unmeasured` and the missing measurement when none exists.
   Do not use commits, test counts or the agent's self-report as the objective.
2. Write the outcome check before the agent prompt.
   Make it inspect actual task results independently of the runner's report, with source and environment identity.
   Demonstrate a negative case that fails and a legitimate success case that passes.
   A report existing or a process exiting zero is insufficient.
3. Name what is finished and off-limits, adjacent tracks, forbidden operations and escalation points.
   Keep the priority track locked until its required checks are green and its human deployment packet is handed over.
   Advance after the phase's core is reasonably tested; stop rather than harden finished phases or invent another task.
   Default to reviewable local output with no push, merge, publication, deployment, credential changes or production data operations.
4. Specify hard caps in explicit units: iterations, wall-clock duration, per-run and total model spend, focused reruns and failed fix attempts.
   Size the iteration cap to the phase; the historical 15-25 range is a planning reference, not a default grant.
   Enforce caps in the reviewed runner, outside the prompt, with no self-extension or retry wrapper that resets them.
   Stop on completion, a cap, repeated failure, missing authority or an actual runtime denial.
   If hard enforcement or spend measurement is unavailable, report the gap and keep unattended activation on hold.
5. Design the runner around the approved IAC launcher and a named treehouse lease, mail-native seat and explicit provider/model.
   Prevent overlapping runs and multiple inbox consumers; count all workers within the five-seat cap.
   Share testlane fairly and allow only the authorized build seat to own the Mac's single heavy build.
   Preserve runtime protections; do not import permission-skipping flags, auto-trust, foreign hooks or unattended supervisor settings.
6. Define a kill switch for this run, durable checkpoint, crash cleanup, heartbeat and owner responsible for noticing silence.
   Record actual cost, duration, tested inputs, completed outcome and stop reason per attempt outside the repository.
   Send alerts only through authorized AgentMail routes; never add an external notifier by assumption.
7. Prepare the charter, check, runner and proposed schedule as reviewable files when the task authorizes those files.
   Have the designated owner review them and inspect one authorized bounded trial before enabling recurrence under the operator's actual scheduling request.
   Do not install cron/launchd jobs, activate app tasks or claim persistent monitoring from a drafting request.
   Honor rule 51's context/handoff limits; end a completed run with a readable handoff instead of overnight status polishing.

Mail the overseer the charter/check/runner paths, activation authority, trial evidence, caps, first-run time, kill switch and unresolved holds.
Cloud execution and deployment remain human-only even inside an authorized overnight run.
