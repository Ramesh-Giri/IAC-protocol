# Portable onboarding and bootstrap: author narrative

This is the author narrative for the uncommitted onboarding change, not generated Git facts or merge clearance.
The integrator must generate Part 2 from the committed candidate and combine it with this narrative before merging under rule 27.

## What and why

A new developer needs a reproducible workspace entry point without publishing the team's private repositories, targets or owner identities in the public toolkit.
The change adds generic onboarding, a safe example manifest, local-setting guidance and a standard-library bootstrap.
Reusable operational lessons move out of runtime-private memory into canonical generic rules, while actual inventory/team context remains ignored.

## Flow

The developer receives the real ignored local inventory privately, configures their own root/site/seat, previews bootstrap, then runs it for authorized repository setup.
`main` resolves the workspace and manifest, and `load_projects` validates folders/remotes/working branches before any project mutation.
Example inventory produces a safe preview/refusal and never reaches `update_project`.
For real inventory, `update_project` clones absent targets through a temporary staging directory or fetches/fast-forwards a clean matching branch.
It holds mismatches, local edits, unfinished operations and symlink destinations; merge arguments prohibit overwriting ignored files.
A repository failure is reported and the loop continues with later projects.
After setup, normal mail-native author/reviewer/integrator delegation remains unchanged.

## Implementation and limits

The script uses Python's standard library and existing Git, with argument arrays, bounded subprocesses and noninteractive credential/SSH behavior.
It adds no dependency installer, account provisioning, credential reader, runtime launcher, cloud execution or deployment mechanism.
The script validates metadata and preserves checkout state; it is not an operating-system sandbox or authorization system.
Existing Git hooks and configured credential helpers remain the developer's responsibility; no hook is disabled to perform setup.
Dry-run checks only local state and cannot prove access or that the remote branch/deployment exists.
Unknown production mappings remain private handoff questions.
Legacy launcher/guard defects are documented but not repaired in this scope.

## Verification

`python3 bin/test_iac_bootstrap.py` checks dry-run/no project operations, successful update arguments, dirty/other-branch/origin/unfinished-operation preservation, symlink refusal, failed-clone cleanup, manifest rejection, example refusal and continuation after an access failure.
Git mutation and network effects are simulated; real cloning/fast-forward behavior is not claimed as end-to-end tested.
Fresh-root CLI probes verify placeholder preview/refusal, unknown-flag handling, version output and no created checkout directories.
The deliverable link/privacy scan checks relative Markdown links, rejects the known private identifiers in public files and validates the real local inventory's shape.
Git ignore checks verify the real inventory/team notes/local settings stay out of the default tracked payload.
`git diff --check` verifies whitespace.
No production or device test is applicable to the generic toolkit changes.

## Deploy/release impact

No product backend, rule, index, package or application deployment is required.
The public manifest is illustrative and the real local manifest must not be staged.
The integrator/reviewer must include the newly untracked public files explicitly, generate the Git-fact report/project map as required by local policy, and review before any publication.
