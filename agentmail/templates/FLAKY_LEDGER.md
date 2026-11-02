# Project flaky ledger

Copy this template to `<project-context-dir>/FLAKY_LEDGER.md` for each project.
Keep raw logs in the task's private attachments folder and link them here (rule 50).
The ledger belongs to the project, survives seat changes, and records failures even when a later attempt passes.

## Rerun events

One line per rerun event, with the exact repository, full 40-character head SHA, both run results and log locations, one-line symptom, and date in UTC.
Use a new line for each later rerun; never overwrite a red result.
If the source changed between runs, record both full SHAs in the corresponding run cells.

| Case | Repository | Head SHA | First run: command, result, log | Rerun: command, result, log | One-line symptom | Date (UTC) |
| --- | --- | --- | --- | --- | --- | --- |
| `<case>` | `<repo>` | `<40-character SHA>` | `<run ID/command, RED, log>` | `<run ID/command, result, log>` | `<observed failure>` | `<YYYY-MM-DD>` |

## Daily flaky pass

1. The overseer schedules one bounded flaky pass per day, assigning one author and the normal independent reviewer under rules 44 and 45.
2. Rank repeats from this ledger and select the worst repeat by frequency and impact, keeping within the active priority track and ownership boundary.
3. Attach the actual failure, write a root-cause hypothesis naming its module, and show the regression red before making the fix.
4. Fix the cause and, where applicable, its class; verify green on the resulting head with every required check and keep both results.
5. Stop and report after three failed fixes or before exceeding SPEND, whichever comes first.
6. Link the fix, exact head and verification beside the event; retain the historical failures and include outstanding flaky cases in the DONE evidence.

A case that fails twice is real.
Nothing is retried into green, and a wider timeout or a skip is never a hypothesis.
