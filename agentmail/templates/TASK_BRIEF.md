# Task brief template (rule 52)

Every `task` mail from a parent to a worker carries these headings, in this order, each filled in or marked `none`.
A brief missing any heading is returned unread.
Keep the whole brief under one screen; link to files for detail instead of pasting them.

```
OUTCOME
  One sentence: what exists when this task is done that does not exist now.

OWNS
  The files, directories or artefacts this seat may change. Nothing else.

RECEIVES
  Exact inputs: paths, SHAs, mail ids, prior reports. No "see above".

OUTPUTS
  Exact deliverables and where they land (worktree branch, attachments folder, one DONE mail).

TRIGGERS
  What starts this seat (this mail) and what ends it (the DONE mail and process exit).

TOOLS
  Runtimes, test lanes, scripts it may run. Builds and lanes it may NOT run.

HUMAN CHECKPOINT
  The one point where Ramesh or the overseer must look before the work goes further, or `none`.

NOT THIS ROUND
  Adjacent work the seat will see and must leave alone. Name it so it is not re-discovered.

DONE MEANS
  The evidence the DONE mail must contain: test names and counts, SHAs, the five manual cases if user-visible.

MAIL BUDGET
  ACK once, BLOCKER if stuck, DONE once. Five mails maximum (rule 47).

SPEND
  Pre-approved rerun budget and hard cap in explicit units (attempts, time or cost).
  Anything over the cap is a fresh ask to the operator before it runs (rule 52).
```

Why: the 31 Oct to 2 Nov 2026 run had briefs that said what to build and never what to leave alone, which is how side tracks opened while the priority track was red.
Five manual cases is the definition of done for anything user-visible: cases Ramesh can run on the phone or in a browser in twenty minutes, written into the DONE mail, not into a 45-row workbook nobody runs.
