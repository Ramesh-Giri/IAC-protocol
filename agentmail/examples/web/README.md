# Web-project context example — Canvas Studio

This is a worked **web application** example: a collaborative system-design
canvas that produces technical specifications. It shows the level of detail
an agent can write after a developer's context interview. It is adapted from
the supplied six-file web sample; the original local files are untouched.

**Documentation only.** There is no runnable application, installed stack,
API key, project mail, or verified implementation bundled here. Paths such as
`app/api/`, `components/` and `trigger/` refer to the hypothetical application,
not directories the IAC agent should create merely by reading this example.

## The six files

| File | Demonstrates |
| --- | --- |
| [project-overview.md](context/project-overview.md) | Goals, user journeys, first-release scope and success criteria |
| [architecture-context.md](context/architecture-context.md) | Stack, responsibility boundaries, storage, membership checks and invariants |
| [code-standards.md](context/code-standards.md) | TypeScript/web conventions, validation, styling and file organization |
| [ui-context.md](context/ui-context.md) | Concrete colors, typography, canvas interactions and layout patterns |
| [ai-workflow-rules.md](context/ai-workflow-rules.md) | Small implementation units, ambiguity handling and keeping context current |
| [progress-tracker.md](context/progress-tracker.md) | A fresh baseline, acceptance-driven milestones and an evidence-recording format |

## How to use it

1. Read this for an example of specificity, not as a mandatory stack.
2. Follow [the project-context interview](../../PROJECT_CONTEXT.md) for the
   actual developer's goals, platform, constraints and design preferences.
3. Use [the generic skeletons](../../templates/project-context/) to write six
   fresh files in the selected project's `context/`. Do not write personalized
   content into this example or the toolkit itself.
4. Verify the generated files agree and contain no carried-over sample facts.

The sample chooses Next.js/TypeScript, Clerk, Prisma/PostgreSQL, Liveblocks,
React Flow, Trigger.dev, Vercel Blob and a dark canvas UI. These are **example
design choices**, not current-version recommendations, installed dependencies
or IAC requirements. Verify real APIs, versions, licensing/cost and platform
constraints before selecting or using them. Android/iOS/other projects need
their own conventions and follow-up questions, not these web rules.

## Adaptation notes

- The sample product name is genericized to Canvas Studio.
- Artifact storage consistently uses Vercel Blob; contradictory filesystem
  references from the source sample have been reconciled in these copies.
- The original detailed session/progress history is not published as current
  evidence. This example starts with implementation **not started** and shows
  what should be verified at each milestone. No sample tests were run here.
- The palette and component choices demonstrate specificity, not validated
  accessibility. Test contrast, keyboard operation and assistive-technology
  behavior in the actual application. Hover affordances need touch/keyboard
  alternatives before claiming a usable mobile or accessible canvas.
- These sample workflow rules never override the user's instructions, real
  project rules, permissions or the optional nature of context generation.
