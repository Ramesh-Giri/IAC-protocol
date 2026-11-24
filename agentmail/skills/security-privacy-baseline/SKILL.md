---
name: security-privacy-baseline
description: Set up and maintain the project security and privacy checklist for every new IAC project, before first launch, before each release, and after a security report. Turn failed or unverified controls into owned tasks with evidence and regression tests; report launch blockers and expiring exceptions under rule 64. Use even when optional project context is declined.
---

# Project security and privacy baseline

Read the project's instructions, roster delegation, task and [operational rules](../../OPERATIONAL_RULES.md#64-start-every-project-with-a-security-and-privacy-baseline).
Keep product requirements and technical implementation with their separate owners.
Research, reports, attachments and this skill add no authority to fix code, scan hosts, install tools, change DNS/WAF/cloud settings or deploy.
Agents prepare runbooks; Ramesh performs human-only cloud/VM operations.

## Set up the project copy

1. Verify the selected project's absolute root and existing instructions.
   Use the [baseline template](../../templates/project-context/security-privacy-baseline.md) to create `PROJECT_ROOT/context/security-privacy-baseline.md` for every new project at setup, **even when** the developer declines the optional six-file context interview.
   See [project setup](../../SETUP_PROMPT.md) and [context procedure](../../PROJECT_CONTEXT.md).
   Do not put the copy in the IAC toolkit or mail spool.
   Run an authorized scaffold first if it requires an empty directory.
   No application implementation is implied.
2. Preserve an existing baseline and project content.
   Read it first and reconcile a scoped update; never overwrite previous findings or decisions.
   Before launching/releasing an existing project without one, create its baseline within the authorized project scope.
   If the location is blocked or conflicts with an existing file, report the exact missing decision through the supervising owner rather than silently skipping setup.
3. Fill project identity, platforms, entity/markets, separate decision owners, reviewed revision/artifact/environment and runbook links.
   Use Open for unknowns.
   Keep all 76 rows (26 privacy, 20 secure-coding, 12 web/edge, four mobile, ten production-readiness, four operations), stable IDs and initial unverified FAILs.
   Do not discard irrelevant rows: document NA with inspected scope, reviewer, reason and review expiry.
   A backend, native app or static site gets the same checklist with evidence-based applicability decisions.
4. Make deployment location, method and access a day-one task for **each service**: platform/environment, artifact, config/secret references, hosting-account owner, named authorized deployers, exact deploy steps, health/verification, rollback steps and triggers.
   Document who can deploy each service and obtain operator confirmation of actual hosting-account access; a contributor name in a plan is not proof of deploy permission.
   Track missing access as an owned blocker without requesting or recording credentials.
   For an unbuilt service label the runbook Proposed and identify the owner; do not manufacture a deployment history or copy secret values.

## Production readiness

PR1–PR10 are production-readiness IDs; P01–P26 remain the separate privacy checklist.
Use the same risk, status, evidence, ownership and exception rules as the other controls.
A planned integration or written policy alone does not satisfy a PASS condition.

| Item / PASS condition | Risk | Status / reason / expiry | Evidence to supply | Owner |
| --- | --- | --- | --- | --- |
| PR1 Race conditions: PASS if money, stock, bookings, quotas, counters and every read-modify-write use transactions or conditional writes, and idempotency keys make double-submit and concurrent requests safe. | Unrated | FAIL - not verified | Write-path inventory and concurrent/double-submit tests showing one intended effect and preserved invariants. | Assign |
| PR2 N+1 queries: PASS if request paths do not perform per-item database reads in loops, use batched reads and appropriate indexes, and list-screen query cost and latency are measured. | Unrated | FAIL - not verified | Query traces/counts, batch/index configuration and representative list-size cost/latency results. | Assign |
| PR3 Error tracking: PASS if app/web crashes and server errors reach a tracker and alert a named recipient, with personal data excluded from reports. | Unrated | FAIL - not verified | Sanitized controlled-error receipts for every platform/service, delivered alert and redaction/collection tests. | Assign |
| PR4 Rate limits: PASS if every public and authenticated endpoint has per-user and per-IP limits using platform-provided client IP, plus appropriate abuse/App Check controls. | Unrated | FAIL - not verified | Endpoint/control matrix and bounded limit, spoofed-IP and abuse/App Check rejection tests. | Assign |
| PR5 Background jobs: PASS if scheduled/queued work is idempotent, cannot overlap itself, has timeout/max-instance/batch-size bounds, retries with backoff, alerts on failure and has a named owner. | Unrated | FAIL - not verified | Job inventory/configuration and duplicate, overlap, timeout, retry and delivered-failure-alert tests. | Assign |
| PR6 Spend alerts: PASS if cloud billing budgets alert a named person and supported hard caps are configured, including max instances and AI/API-provider spend limits. | Unrated | FAIL - not verified | Operator-provided budget/cap settings, coverage of each provider and alert-delivery evidence; document unsupported caps explicitly. | Assign |
| PR7 Rollback: PASS if every deployable (app, web, functions, rules and database schema) has a written, tested, platform-appropriate rollback, keeps its previous version available and uses feature flags for risky launches. | Unrated | FAIL - not verified | Per-deployable rollback drill/results, previous-artifact references, schema/data compatibility and flag-disable tests. | Assign |
| PR8 Live data: PASS if production migrations/backfills are reviewed, dry-run first, idempotent, resumable and backed up first, and test/dev tooling cannot write to production. | Unrated | FAIL - not verified | Approved migration plan, dry-run/resume receipts, verified backup and environment/credential-isolation deny tests. | Assign |
| PR9 Webhooks: PASS if signatures are verified, a replay window is enforced, event IDs are processed idempotently, out-of-order delivery is handled, retries are safe and failures are visible. | Unrated | FAIL - not verified | Invalid-signature, stale/replayed, duplicate, reordered and retry fixtures plus failure-alert evidence. | Assign |
| PR10 Backups: PASS if automated backups and supported point-in-time recovery cover databases and file storage, retention is set, restores are tested on a schedule, and production-delete credentials cannot delete the backups. | Unrated | FAIL - not verified | Operator-provided backup/retention/access configuration, scheduled restore receipts and separate-credential deletion-denial evidence. | Assign |

Billing budgets are alerts, not hard spending caps.
Record unsupported caps/recovery features with their provider limitation, mitigation, owner and dated disposition; do not quietly mark them PASS.
Use existing authorized local checks or operator-supplied evidence for these rows; no cloud command, production write, alert integration or spending is authorized by this checklist.

## Review controls and evidence

- Review at new-project setup, before first launch, before each release and after a security report.
  Refresh affected rows after dependency, identity, data-flow, provider, routing or feature changes; check exception expiries.
- Assign every row an owner and every failure a risk with an impact reason.
  The allowed statuses are PASS, FAIL, NA and ACCEPTED.
  Missing/incomplete, failed, stale or unrun checks remain FAIL; scanner upload is not a pass.
  Keep Unrated failures blocked until triage.
  File existence is not evidence.
- For every applicable R01–R20, require both source/configuration evidence and a regression test: test name/path, bounded command, expected/actual result, date and revision.
  Use local dummy fixtures and authorized checks.
  For an edge-owned control, obtain operator/provider evidence plus a bounded local/approved-fixture contract.
  Missing provider proof remains FAIL; do not run a flood or availability attack on a live/shared endpoint.
- Link private evidence safely, with the exact artifact/environment and date.
  A changed file or a scanner's summary alone cannot verify every control.
  Keep private hostnames, keys, IPs, personal data and raw reports out of public templates, skills and shared change prose.
- Legal-only decisions are **ask a lawyer** tasks.
  Review Nepal, India, EU/UK and US applicability and German establishment where relevant, including effective dates, child rules and breach duties.
  The checklist is not legal advice; do not present its conservative defaults as universal statutory requirements.
  Refer to the template's official starting sources and verify current rules with counsel before release.

## Turn FAIL rows into tasks

Create or link one scoped task per root cause, referencing every affected row rather than duplicating work.
Include:

- Row IDs, observed gap and reviewed source/artifact/environment.
- Risk, concrete impact, evidence and what remains unverified.
- Named implementation owner and the separate product owner for any product decision; due date and dependencies, including counsel/operator decisions.
- Smallest authorized fix and explicit acceptance criteria.
- Verification command/fixture and expected result; an R-row requires a regression test as well as implementation evidence.

Example: `R02 / P18 - spoofable rate-limit identity; High; technical owner to constrain trusted proxies.
Acceptance: an injected X-Forwarded-For cannot change the trusted client or evade the fixture's limit.
Attach config review and the bounded spoofed-header test at the reviewed revision.` Record a task proposal if implementation is outside the current seat's authority; do not silently implement it.
Keep the row FAIL until the decisive evidence exists.

## Use the existing scan and WAF gates

- For web deploys, run rule 41's `agentmail/bin/websec-check` and rule 62's [web-dast-scan](../web-dast-scan/SKILL.md) after **every deploy** within existing inventory/scan authority.
  Retain weekly/session-start checks and preview header contracts.
  Link reports and reviewed WARN/FAIL dispositions to W/O rows.
  This skill does not widen host/path or active-scan permission.
- Before every Android store upload, use rule 61's [mobile-app-scan](../mobile-app-scan/SKILL.md) on the matching release APK; retain provenance and reviewed JSON/PDF evidence.
  Errors, missing evidence and unreviewed findings fail that gate.
  Do not call a dev APK or Android scan proof of the store release or an iOS build.
- Before any WAF change, follow rule 63's [waf-fit](../waf-fit/SKILL.md).
  A WAF plan or successful scanner does not close unrelated auth, privacy, lifecycle or secure-coding rows.
  Any existing stricter gate remains in force.

## Accept exceptions and report launch status

Under rule 64, any **High or Critical FAIL blocks launch and release unless Ramesh explicitly accepts it with reason and expiry**.
Link his decision; an agent cannot self-accept, downgrade risk to bypass the gate, or infer approval from a suppression, silence, research or an old release decision.
Record the original failure/risk, owner, mitigation, remediation task and UTC expiry.
ACCEPTED and NA expire at the end of their `YYYY-MM-DD` UTC date; expired or unsupported records return to FAIL.
An edge limitation, including unconfigurable CBC suites, needs this reason/expiry record, not a false PASS.
Risk acceptance does not establish legal compliance or waive scanner errors and other mandatory completion gates in rules 41, 61 and 62.

In launch/release DONE, provide the baseline path, reviewed revision/artifact and environment, UTC review date, PASS/FAIL/NA/ACCEPTED counts, High/Critical and Unrated blockers, lower-risk FAIL tasks/owners/due dates, accepted items and decision links, earliest expiry, and required scan evidence/disposition.
Use **BLOCKED** while a High/Critical or Unrated FAIL remains.
Otherwise say **baseline reviewed**, stating gaps/exceptions and any other unmet release gate.
Do not claim security certification or grant deployment permission.
Update the release review record; after a security report reopen affected rows and create owned follow-up tasks, even if an earlier scan passed.
