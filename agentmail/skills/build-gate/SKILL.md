---
name: build-gate
description: Decide whether an IAC or product build, full suite, release artifact, or deployment handoff should happen now. Use before requesting or starting one, especially after several small fixes or when the Mac is busy.
---

<!-- Defines the IAC pre-build decision and evidence handoff; owns no runner or deployment authority. -->
# Build gate

Read the [shared seat boundaries](../README.md#shared-seat-boundaries) and IAC rules 29 and 54 before acting.
Treat this gate as a scheduling decision, never as permission to deploy.

1. Identify the task, exact input revision, dirty patch fingerprint if applicable, artifact, affected platforms, and authorized build owner.
   Map each changed behavior to a focused check, a negative case, and any check that requires the final artifact or Ramesh's hands.
   Distinguish compilation from observed behavior; a successful build alone cannot prove the feature works.
2. Finish the focused checks first, through the configured `testlane` when required.
   Batch only ready changes already inside the accepted outcome; do not open adjacent work to fill a build.
   Keep required failing or missing evidence visible.
3. Check the existing queue and owned jobs before submitting anything.
   On Ramesh's Mac allow one heavy build at a time, even if two test lanes exist.
   Children do not start heavy local builds; the overseer arranges one combined build per cleared merge through the authorized integration/build seat.
   State priority level 0, 1 or 2 and an estimate; preserve the short lane under rule 54.
   Use only runner command forms accepted by the installed helper's help.
   After a queue wait expires, inspect the original job before retrying; expiry does not cancel it.
4. Choose `ready`, `defer`, or `blocked` as the decision vocabulary.
   Choose `ready` only for the named build owner with prepared inputs, completed prerequisite checks and available capacity.
   Choose `defer` for remaining in-scope checks or batching; name the event that will release it.
   Choose `blocked` for missing authority, an actual runtime denial or a required external prerequisite; mail the overseer with the missing fact.
5. Freeze inputs until the actual client/exporter and runner finish.
   Bind output to the tested revision, patch fingerprint, command, job ID, exit status, artifact digest and elapsed time.
   Rebuild only when changed inputs, failure or a named qualification gap warrants it.
   Keep post-build behavior and manual checks separate from build success.

Return one short mail: decision, input identity, checks completed, remaining checks, queue/job identity, owner and release condition.
For cloud/deployment work, prepare a source-bound TYPE-THIS packet for Ramesh; never execute cloud commands, APIs, authentication, SSH or deployments.
Pass completed evidence to [acceptance-gate](../acceptance-gate/SKILL.md).
