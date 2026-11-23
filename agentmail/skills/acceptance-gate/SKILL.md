---
name: acceptance-gate
description: Check IAC or app completion evidence before merge or a READY claim. Use when a runner sends DONE, a batch is proposed for integration, or required checks and manual evidence need an independent verdict.
---

<!-- Defines independent runner/checker acceptance and source-bound verdicts before integration. -->
# Acceptance gate

Read the [shared seat boundaries](../README.md#shared-seat-boundaries) and IAC rules 27, 28, 33, 43 and 52.
Treat DONE as a handoff requiring verification, never as the verdict.

1. Name a runner and a different checker in the roster-backed task mail.
   Use the other provider for checking where possible, within the fleet cap and actual headroom.
   Keep product requirements with the product owner and implementation judgments with the technical owner; send conflicts to the overseer.
2. Write a compact acceptance matrix before execution: requirement, observable result, refusal/failure case, exact check, required artifact and responsible seat.
   Have the checker inspect the scope and executable plan against actual entry points.
   Name external fakes and the real application behavior each leaves intact.
3. Have the runner execute on fixed inputs and preserve actual failed and successful observations.
   Record full source SHA, patch fingerprint for uncommitted work, command, environment, fixture, UTC interval, job ID, exit status and counts with each receipt.
   For writes, include an independent persistent readback; for refusals, include preserved-state evidence.
4. Have the checker read the source and rerun the decisive focused checks itself on the same identified inputs in its own treehouse lease or approved testlane job.
   Require the checker's own command, source identity, job/log reference, exit status and observed result.
   Reading the runner's log or repeating its claim is not a rerun.
   Missing runtime or capacity leaves the affected acceptance row `uncertain`; do not bypass the boundary or duplicate a heavy build to fill it.
5. Assign each row `pass`, `fail` or `uncertain`.
   Use `fail` for an observed contradiction and `uncertain` for absent or unbound evidence, including required jobs that are missing, skipped, cancelled, stale or still running.
   Require all mandatory rows to pass on the candidate; explain any reused evidence's exact source association and continued applicability.
   Keep mock, device, web, CI, artifact and production claims distinct.
6. Confirm normal review and the separate independent break pass are complete, with findings triaged and accepted fixes rechecked under rule 43.
   Check the stable change report, touched-file header docs, merge-time project map and applicable acceptance workbook updates.
   For user-visible changes include five practical manual cases, real loading/empty/error states and each shipped platform; name untested gaps.

Mail the overseer the candidate identity, runner/checker names, matrix with evidence links, independent rerun receipts and merge recommendation.
Hold acceptance while any required row is `fail` or `uncertain`.
The checker advises the authorized merge owner; it does not merge, publish or deploy.
