# Canvas Studio — Progress Tracker

> **Web-project example only.** This is sample context, not active IAC rules
> or an implemented app. See [the example guide](../README.md) before adapting.
> All stack, path and design choices belong to this example, not your project.

## Current phase

Planning. Implementation **not started**. This repository includes only the
six example context documents; it does not include the Canvas Studio app.

## Current goal

Confirm the sample design's assumptions with the actual developer, then plan
the first implementation slice. If these were real project requirements, the
first slice would be an accessible static editor shell with no AI or realtime
services yet.

## Completed

No application work completed. No dependencies installed, tests passed,
authentication verified, or deployment performed for this example.

## In progress

None. Writing a plan is not evidence of a working feature.

## Next up — illustrative milestones

| Milestone | Acceptance criteria | Verification to perform, not yet run |
| --- | --- | --- |
| UI foundation and editor shell | Agreed theme, navigation and empty states work on desktop and narrow screens; keyboard/touch access does not depend on hover | Type/static checks and build after scaffold; visual review, contrast and keyboard checks |
| Authentication and membership | Signed-out users cannot access private projects; owner and collaborator access is enforced at server mutation boundaries | Authorized/unauthorized request tests; signed-in/out flow checks with development credentials |
| Project management | Create, rename and delete work against real persistence; loading, empty and failure states are handled | Input validation and membership integration tests; UI flows including failure recovery |
| Collaborative canvas | Two authorized sessions see edits; graph schema stays valid; snapshots persist to Vercel Blob with database references | Two-session collaboration test; graph schema and persistence/reload tests |
| AI generation and spec export | A bounded background task produces validated graph updates or an exported spec; failures are visible | Stubbed-provider task tests, membership checks and artifact export/reload tests |

These milestones are a planning example, not a command to implement the
whole application. Choose and authorize one small unit at a time.

## Open questions

- Are the sample vendors, budget and deployment assumptions acceptable?
- What graph size and collaborator count must the first release support?
- How will users edit/connect canvas nodes using keyboard and touch?
- What retention/deletion rules apply to projects, snapshots and generated specs?
- Which installed scaffold and package scripts will provide the real checks?

## Architecture decisions

- Proposed: PostgreSQL holds metadata, ownership and task records; Vercel Blob
  holds snapshots/specs. Both layers enforce the same project access boundary.
- Proposed: realtime collaboration is separate from durable artifact storage.
- Proposed: long-lived generation runs outside request handlers.
- Proposed: dark technical-workspace design, subject to accessibility checks.

Each real decision should record its source/approver and status. Supersede
an old decision explicitly and update all affected context files together.

## Evidence format for future completed work

For each real completion, record: the small feature, changed paths/commit,
checks actually run and results, manual/device checks, known gaps, and the
next action. If a check was not run, say why. Do not import another project's
completed tasks or assume commands exist before inspecting its scripts.

## Next-session handoff

Confirm the actual product requirements and stack. Generate personalized
context before implementation; this example has no active work to resume.
