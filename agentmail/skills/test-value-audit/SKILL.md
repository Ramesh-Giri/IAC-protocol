---
name: test-value-audit
description: Audit the regression value of tests in a named IAC or product change without editing them. Use for tests that cannot fail, duplicates, implementation coupling or trivial checks, especially when a new test should fail against the base implementation.
---

<!-- Defines report-only test-value analysis and isolated base-versus-candidate evidence. -->
# Test value audit

Read the [shared seat boundaries](../README.md#shared-seat-boundaries) and IAC rules 29, 43 and 48.
Keep the working source and tests unchanged; the deliverable is a report, not deletions or a repair branch.
Complement `gstack-test-audit`: reuse its existing candidate/retention evidence and focus this pass on changed tests and base-code sensitivity.
Do not invoke its mutation/ship flow or rerun a whole-repo sweep without a separate brief.

1. Bound the audit by named paths, full candidate/base SHAs, changed tests, time and candidate-count budget.
   Resolve the base from the actual integration target, not a remembered default branch.
   Read each complete candidate test, its real production owner and relevant overlapping coverage.
2. Identify assertion-free or constant assertions, swallowed failures, unawaited async checks, excessive internal mocking, duplicate behavior and trivial framework or pass-through checks.
   Treat these as leads: a test may fail through an expected exception or a helper assertion, and changed inputs may protect different boundary cases.
   Retain independent business, security, auth, money, protocol, serialization, default and platform contracts even when their tests look simple.
   Respect documented retention markers and explain false positives.
3. For a claimed new behavior or regression test, state which assertion should reject the base implementation.
   Ask the authorized lease owner for an isolated treehouse worktree at the exact base; never create or force-remove raw Git worktrees or modify the author's checkout.
   Transfer only the candidate test and the minimum identified test fixtures, recording their hashes; do not smuggle in the implementation fix.
   Keep dependencies and runner configuration identifiable.
4. Run the same focused test against the candidate and base through the approved testlane or authorized focused runner.
   Verify the intended named test was collected and actually executed.
   Record both source identities, copied inputs, command, counts, exit status, job/log reference and the failing assertion.
   A base compile/import/setup failure or missing API is `inconclusive`, not proof of regression sensitivity.
   A base assertion failure plus candidate pass supports `sensitive`; a genuine pass on both is `passes-base` for this change only.
   A candidate failure is `candidate-fails`; a check not run is `unrun`.
   Do not declare an existing invariant worthless merely because it correctly passes on both revisions.
5. Report each candidate's file:line, category, protected contract, credible missed regression, overlap and observed runtime result.
   Recommend `retain`, `rewrite`, `combine`, or `retire-proposal`, with evidence and the behavior that must remain protected.
   Separate static suspicion from confirmed runtime observations; never suggest weakening required coverage to improve counts.
   Leave edits to a separately authorized implementation task and checker.
6. Preserve the base/candidate receipts outside Git and release only the owned treehouse lease through its approved lifecycle after runners exit.
   Send the overseer the concise report path, findings, retained cases, checks actually run, and unrun/inconclusive controls.
