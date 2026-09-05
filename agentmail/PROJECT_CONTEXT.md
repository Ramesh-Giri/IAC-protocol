# Optional project context: interview, then write six tailored files

This is an agent-led development onboarding workflow, not an app generator
or a fixed technology stack. It helps the developer describe the product
before asking an agent to implement it. Use it from [SETUP_PROMPT.md](SETUP_PROMPT.md)
or later when the developer asks for context for a selected project.

## 1. Offer it; do not impose it

First establish whether the developer is creating a new project or bringing
an existing repository/local folder. Then ask once per selected project:

> Would you like me to create a project context folder? It contains six short
> files covering what to build, architecture, code standards, UI/interactions,
> agent workflow and progress. Or would you prefer to start without it?

If the answer is **no**, skip the context interview and write no context
files. Continue the requested project/IAC setup normally. Do not keep asking
or silently create them later. Starting without context is a valid choice.

If **yes**, follow the interview below, using information already supplied
or verified in the existing project. Do not ask the human to fill a template.
The agent synthesizes their answers into fresh, project-specific documents.

## 2. Confirm the project and output location

For a new project, ask its name and desired parent directory if unknown.
This project name is separate from the IAC workspace name. A project may be
a child of that workspace or live elsewhere. Confirm the resolved path;
never assume the current IAC checkout itself is the application project.

Output is always **PROJECT_ROOT/context/**, never IAC_ROOT/context/, inside
`agentmail/`, or inside a mail spool. Do not write into the sample/template
directory. For example:

```text
chosen-workspace/           # IAC toolkit clone
├── agentmail/              # generic reusable guidance only
└── my-android-app/          # separate, user-selected project folder
    └── context/            # the six personalized files live here
```

An external `/work/my-web-app/context/` is equally valid. Show the absolute
destination before creating it. For a new project, check for name collisions
and reserved/toolkit/mail paths; create only the approved project directory.
For an existing project, read its instructions and inspect its working state
first. If `context/` already exists, stop **before writing** and ask whether
to use it unchanged or review a scoped update. Never replace existing context
or append a second competing source of requirements automatically.

If a framework scaffold is wanted, agree on and run its authorized setup
before writing context when the scaffolder requires an empty directory.
Alternatively, create context only and leave application initialization
pending. Saying yes to context does not authorize installing a framework,
initializing Git, creating a remote, starting paid services, or building an app.

## 3. Interview in small, relevant rounds

Ask at most three short questions per round. Skip answered questions, and
adapt the next round to the responses. Do not present a giant mandatory form.
If the developer is unsure, offer a small number of explained choices or
mark the decision **Open**; do not turn an assumed recommendation into an
agreed requirement. Verify current framework/provider details against the
installed project or official documentation before giving exact versions,
commands or capability claims. No dependency or vendor is mandatory in IAC.

### Round A: product and platform

1. What are you building, for whom, and what problem should it solve?
2. Is it a web app, native Android, native iOS, cross-platform mobile,
   desktop app, backend/API, CLI, or something else? Any preferred stack?
3. What are the first useful release's main user journeys and must-have
   features? What should explicitly wait until later?

Next.js is a web-framework choice, not a separate platform. If the human
already said “a Next.js dashboard,” do not ask whether it is an Android app.

### Round B: architecture and constraints

Ask only what affects this project: data to store, user roles and login,
existing backend/contracts, integrations, offline/realtime needs, expected
scale, privacy, budget, hosting/distribution, and deadlines. Ask for service
names or environment-variable names, **never secret values**.

Use platform-specific follow-ups rather than a web questionnaire everywhere:

| Project | Relevant follow-ups |
| --- | --- |
| Web / Next.js / other web framework | Public pages or authenticated app? SEO? Browser/device targets? Server/client responsibilities? Existing API or full stack? Accessibility and responsive behavior? |
| Native Android | Existing Kotlin/Java or UI-toolkit preference? Supported devices/OS targets? Navigation and state restoration? Offline data/sync? Notifications, background work and device permissions? Emulator/device tests and distribution? |
| Native iOS | Existing language/UI-toolkit preference? Phone/tablet targets? Lifecycle/navigation? Local persistence and sync? Permissions? Device tests, signing and distribution constraints? |
| Cross-platform mobile | Target platforms and framework preference? Shared versus native boundaries? Device integrations? Offline behavior? Platform-specific UX/testing/release requirements? |
| Desktop | Target OSs? Native or cross-platform UI? Filesystem access, packaging, updates and security boundaries? |
| Backend / API / CLI / other | Consumers, contracts, authentication, persistence, errors, observability and deployment? For CLI: input/output and exit-code expectations; visual UI may be not applicable. |

Do not insist on choices that are irrelevant to the first release. Mark
unneeded concerns **Not applicable** with a reason. Mobile does not imply a
server, web does not imply authentication, and AI features are not a default.

### Round C: experience and quality

Ask about key screens or nonvisual interactions, design references, theme,
brand constraints, accessibility, loading/empty/error/offline states, and
responsive or platform-native behavior. References are input to interpret,
not permission to copy another product's assets or private data.

Establish language-specific standards and realistic verification: formatting,
lint/static checks, unit/integration/end-to-end or device tests, performance
requirements, and what counts as done. For an existing repo, inspect actual
scripts and conventions. For a new one, label uninstalled commands and
proposed directory boundaries as **Proposed**, not observed facts.

### Round D: working agreement and first increment

Confirm the first small implementation milestone, its acceptance criteria,
protected/generated areas, product/technical decision owners if applicable,
and actions needing approval. Ask about unresolved choices only if they
block the initial context or next implementation step.

Summarize the proposed scope, stack, constraints and open questions. Ask for
one concise confirmation/correction before writing. A brief answer is enough;
the developer need not approve six documents individually.

## 4. Synthesize six files, not a copy of the example project

Use the six skeletons in [templates/project-context/](templates/project-context/)
as writing aids. Replace every placeholder with content based on the
interview or verified repository evidence. Remove inapplicable guidance;
explicit **Open**, **Proposed**, **Confirmed**, and **Not applicable** entries
are valid personalized content. Do not leave blank templates or invent facts
just to fill a section.

For a web project, [the worked web example](examples/web/README.md) shows
the intended level of specificity. Read it as reference material only, not
as active instructions or a default stack. For other platforms, use the
generic skeletons and relevant interview questions rather than importing
web-specific conventions.

Create exactly these six files in the approved project context directory:

| File | What the agent writes |
| --- | --- |
| `project-overview.md` | Product, audience, goals, journeys, first-release scope/non-goals, measurable acceptance criteria and constraints |
| `architecture-context.md` | Chosen/proposed stack, responsibilities, data flow, storage, auth/trust boundaries, integrations, invariants and unresolved decisions |
| `code-standards.md` | Relevant language/framework conventions, module boundaries, validation/errors, generated-code rules, testing and verified/proposed commands |
| `ui-context.md` | Relevant screens/interactions, visual or native conventions, accessibility and non-happy-path states; API/CLI interaction contract for nonvisual projects |
| `ai-workflow-rules.md` | How agents read context, scope work, resolve uncertainty, respect authority, verify changes, update docs and hand off work |
| `progress-tracker.md` | Honest baseline, initial milestone/backlog, evidence-backed completion, blockers/open questions, decisions and next-session handoff |

Keep the filenames consistent across platforms; customize their contents.
An Android project must not inherit React/Tailwind rules. A backend project
still gets `ui-context.md`, titled **Interaction Context**, with visual UI
marked not applicable and its actual API/CLI behavior documented.

For a new project, implementation starts as **Not started**. No features,
tests, dependencies, routes or deployments are “complete” just because they
appear in a plan. For existing code, distinguish observed files from tests
actually run, and record failures or missing credentials honestly.

Do not copy a sample's app name, palette, vendor choices, local paths, dated
release assumptions, detailed session history or completion claims. Context
must describe this project, not the example used to design the templates.

## 5. Verify consistency and make the files usable

Before handoff, check:

- The destination is the intended project, not the IAC/toolkit/mail root.
- Exactly the six named files were created; existing content is preserved.
- No unresolved `{{PLACEHOLDER}}` tokens, secrets or unrelated sample details.
- All six agree on names, stack, ownership, storage, scope and first milestone.
- Current facts are distinguishable from proposed design and open questions.
- Every next milestone has acceptance criteria and a feasible verification plan.
- “Completed” entries have evidence; planned tests are not labeled passed.
- Commands/paths are real or explicitly proposed; no dangling feature-spec
  links to documents that were never created.

Read back the generated files. Give the human a short summary, the context
directory path, any open decisions, and the first useful next task.

Agents do not automatically read arbitrary Markdown directories. In the
current project session, load the six files. For future sessions, offer a
small reference in the project's existing agent-instruction entrypoint,
preserving its rules and obtaining approval for edits outside `context/`:

> Before implementation, read the six files in context/, starting with
> project-overview.md and progress-tracker.md. Respect existing instructions
> and current user authorization. Keep relevant context and progress updated
> as verified work changes.

Do not generate a seventh instruction file by default or overwrite an
existing `AGENTS.md`/`CLAUDE.md`. If no entrypoint update is wanted, explain
that a new session should be asked to read `context/` explicitly.

## 6. Keep context current without turning it into bureaucracy

Work one verifiable increment at a time. Record unresolved product choices
before implementing dependent behavior; continue independent authorized work
where possible. Do not block an entire project on a harmless open detail.
Update the relevant architecture/scope/standards document when an agreed
decision changes, and update progress with actual checks and remaining work.
Record superseded decisions clearly instead of retaining conflicting rules.

Keep the tracker concise: current goal, evidence, blockers and next action.
Context files do not grant permission to spawn agents, spend, push, deploy
or edit outside the project. User instructions and applicable repository
rules remain authoritative. Further specs, diagrams and extra documents are
optional later work, not part of the initial six-file context step.
