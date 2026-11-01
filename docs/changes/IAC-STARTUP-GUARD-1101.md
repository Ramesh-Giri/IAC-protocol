# Change report: IAC-STARTUP-GUARD-1101

Repo `/Users/darkness/Work/Aureus`, branch `main`, range `bc29de6..working tree`.
0 commits, 0 merges, 4 files, +476 / -34 lines.

Part 1 is written by the authoring agent. Part 2 is generated from git by `agentmail/bin/change-report` and is the ground truth: if they disagree, Part 2 wins and the disagreement is a review finding.

# Part 1: Narrative (authoring agent)

## What and why

The tmux startup fallback could interrupt a Codex worker that was already Working, because it recognized activity only on the final capture line and sent Escape for everything it could not classify.
The supplied recorded Codex 0.163 capture places Working above a Tip, composer, model/status row and warning footer, and the three supplied final idle captures use the newer placeholder and metadata layout.
Those captures establish the layouts; the earlier interruption history remains operator-provided context, not a reconstructed live observation.
This change recognizes the current bottom UI block, gives activity precedence over idle, removes Escape from unknown-screen handling, and requires a separate successful capture before submitting exact pending boot text.
The final B1 correction also prevents whitespace already admitted by the activity regex from making Compacting look like Working and bypass its bounded wait.

The canonical integration is `/Users/darkness/Work/Aureus`, on `main` at unchanged base/HEAD `bc29de69df31e14082a4186b6cff72a4960960dd` before the root-owned commit.
The exact accepted two-file source is `agentmail/bin/agentmail-launch` SHA256 `4442dfc327ed301baa512b7a85f16ce4f2172c7edbfacfb11dec82b4f83a03bd`, mode 0755, and `agentmail/SUPERVISOR_BOOTSTRAP.md` SHA256 `e5af6887031af662a3848db1a68126ca900f86727f226946c38607620ebf52fc`, mode 0644.
Integration also adds the maintained `docs/map/PROJECT_MAP.md`, `docs/map/graph.json` and this generated report.
The author's preserved local-only branch `fix/codex-startup-guard-1101` is historical source evidence, not the canonical integration branch.
The integrator verified both clean canonical preimages, a scoped write/read/remove probe, backups, 16 sealed author artifacts, all 66 final bound evidence inputs, exact postimages/modes and byte equality to accepted `SOURCE.patch` SHA256 `540b446dcf1d6f085f262c76e52021bc1e33ce094d36113b48b067132bd6ae41`.
The integrator made no Git metadata changes; root owns the explicit source/map staging baton and the subsequent ordinary-hook local commit.
No actual runtime launch, terminal/app control, network, cloud, authentication, hook approval or settings change was performed by this integration task.

The author narrative and source-specific RED/GREEN history below are preserved from `AUTHOR_NARRATIVE.md` SHA256 `705fd8ca0426da7bd14b6c91eaed18cda100ce5a5a844fac466f5aa8bd66399c` in `.agent-mail/attachments/overseer-arm-20261030/iac-startup-guard-author-1101/`.
Unqualified author evidence directories in the verification tables refer to that preserved packet.
Canonical integration receipts are in `.agent-mail/attachments/overseer-arm-20261030/iac-guard-integrate-1101/CANONICAL/`.

## Flow (step by step)

1. The existing `spawn` path creates its tmux window and passes the already assembled boot prompt to `_resend_boot_if_idle`.
2. `_submit_until_working` requests a new capture for every decision and discards failed or empty output without reusing earlier readiness.
3. The unchanged exact launch-cwd folder matcher remains the only automated folder-confirmation path, and Home and Enter require separate matching successful captures.
4. `_startup_state` examines a recognized bottom composer/footer suffix and the immediately preceding status, optionally separated by the recorded Tip line; any other nonempty preceding boundary must be the observed complete `Worked for` turn-ending marker.
5. Working returns readiness without any key, while Compacting receives no keys and stays within the existing bounded capture loops.
6. Unknown UI, hook review, wrong or unapproved folders, mismatched text and incomplete layouts warn and stop without a key in that state.
7. Verified empty idle receives one literal paste when a boot prompt is needed, then a new capture must show that exact pending text before Enter.
8. An initially pending exact boot prompt also consumes a separate successful capture before Enter, and a swallowed Enter may be retried without another paste.
9. The launcher still reports window-creation success independently of readiness, so the supervisor must separately verify a unique task ACK plus actual Working.

## How it is implemented

`_IDLE_SCREENS` keeps both legacy layouts and adds the observed Codex composer/model/footer structure with the exact empty placeholder and optional warning suffix.
The modern composer requires nonempty captured text, so an unobserved bare glyph with model/footer cannot authorize a paste.
The model row matcher recognizes the display structure without consulting or changing model policy, selecting a model, or broadening filesystem authorization.
Unknown display formats remain unknown.
`_startup_activity` retains the legacy current-status forms and distinguishes Compacting from Working.
It trims the captured activity label after removing the glyph, so TAB, NBSP, mixed space/TAB and EM SPACE follow the same Compacting wait path as ordinary spacing.
This normalization applies only to the activity label, while exact pending boot text retains its existing whitespace-sensitive comparison.
`_startup_state` anchors those statuses to the bottom UI block instead of searching transcript words, while the observed complete turn-ending marker between historical Working and the current composer permits normal idle recovery.
Composer text retains trailing whitespace so pending boot text must match exactly rather than becoming equal after stripping it.
The existing `_startup_idle_matches` interface now delegates to that state classification.

The submission loop uses the state from the current capture and preserves the expected pending prompt after its one allowed paste.
An unexpectedly empty composer after that paste stops submission instead of accepting stale readiness, sending an empty Enter or pasting again.
Any unsupported preceding UI remains unknown even if the composer/model/footer matches, including changed Tip text, partial activity, or hook review with a different action tail.
The classifier uses only the current boundary and does not search earlier transcript words for activity or trust.
The private no-boot submission entry retains its legacy empty-idle Enter control; the actual spawn/resend boot-recovery path supplies the expected boot text.

`_startup_folder_matches`, `_resend_boot_if_idle`, `build_command`, `spawn` and `main` have identical production ASTs to the base.
The generated symbol list names `_startup_folder_matches` from diff context around the adjacent `_IDLE_SCREENS` change; the unchanged function body and AST are verified in `SOURCE_CONTRACT_AUDIT.json`.
The generated sensitive-area list uses filename heuristics, so its `None` entry does not qualify the input/trust boundary as security-insensitive.
The unchanged CLI output, argv, exit, model executor and window-creation contracts do not gain new flags, dependencies, formats or frameworks.
Existing file modes remain 0755 for the executable and 0644 for bootstrap documentation.
The launcher purpose header now describes dependencies, consumers, the guarded startup path and the limits of its launch result.
Bootstrap instructions explicitly replace the former one-Escape rule with zero-key warning-and-stop behavior.

A footer-only matcher expansion was rejected because the preserved old helpers demonstrably send keys into Working and into a post-paste activity transition.
The fix therefore keeps state classification and fresh capture checks together.
The code includes a `shortcut:` comment for the remaining capture-to-delivery interval.

## How it was verified

Canonical integration ran `PYTHONDONTWRITEBYTECODE=1 python3 agentmail/bin/agentmail-launch --self-check` once: actual exit 0 in 0.322 seconds, stdout `startup trust self-check: passed`.
The exact launcher, bootstrap, `iac.py`, `model_guard.py` and Git index hashes/modes stayed unchanged through actual exit; read-only `git diff --check` also exited 0.
`SELF_CHECK/receipt.json`, stdout and stderr preserve this canonical execution separately from all author/reviewer attempts.
The actual canonical import warning reports no site model policy at `/Users/darkness/Work/Aureus/local/model-policy.json` and zero site model restrictions active.
No policy/profile/configuration was created, changed or qualified to silence it.
The maintained check returns before roster/catalogue/launch work and mocks every target capture/key/window subprocess and sleep.

The author's final `UNIT_COMPLETE.md` SHA256 `cd9657fe1a60480e1dfb251c731c4b61c9ee6c944da713c2954a12718901a718` and `AUTHOR_FINAL_SEAL.json` SHA256 `cd5218f3a457fb52d71dccebca30fdca02eed3433ef2f789d6fa2cd74ca87231` establish the final completion status.
Final independent `BREAK.md` SHA256 `bf479e589de5f60e2c947b4aa9f3efdd64dcbe4033114c44971e7e4e54498b63` and `REVIEW_SEAL.json` SHA256 `cd2c503a04477ee61ebc0090d4dcfba9b09d5400c04bc5c1296b829717015c31` clear the exact B1 successor with zero open findings.
That preserved independent current-source execution passed the maintained self-check and 120 focused transitions plus eight pure checks; integration did not repeat those unchanged suites or relabel them as canonical executions.
Prior NORMAL report `768c1f71`/seal `9d051f69` retains its 73 checks on the prior source only.

All checks are offline and deterministic.
The inline self-check mocks every subprocess and sleep, asserts allowed key argv and a distinct successful nonempty capture before each key, and exercises the actual direct, resend and fake-window spawn paths.
The spawn assertions retain its exact `(True, "tmux window")` result even when readiness fails.
Legacy hook/path rejection controls, capture failures, exact-cwd confirmation, swallowed Enter retries and warning diagnostics remain covered.

| Evidence | Actual command and result |
| --- | --- |
| Old baseline | `PYTHONDONTWRITEBYTECODE=1 python3 agentmail/bin/agentmail-launch --self-check`, exit 0, recorded in `BASELINE01/`. |
| Failing first | Same command after only the self-check extension, exit 1, recorded in `RED01/`; the old implementation attempts Escape on the Working-above-composer fixture. |
| RED causality | `RED01/receipt.json` records an AST equality assertion for all production nodes excluding the self-check, plus stable before/after input hashes. |
| First fix | Same self-check command, exit 0, recorded in `GREEN01/`. |
| Prior candidate check | Same self-check command, exit 0, recorded in `GREEN02/`; independent review subsequently found a missing current-boundary negative case. |
| Review finding RED | Same self-check command with additional tests only, exit 1, recorded in `NORMAL_FINDING_RED02/`; production AST equals the prior frozen candidate. |
| Narrow modern RED | `NARROW_MODERN_RED01/receipt.json` and `assertion.txt` retain an actual-helper failing assertion: an unsupported bare modern glyph received a literal boot paste. |
| N1/A1 candidate maintained check | Same self-check command, exit 0, recorded in `GREEN03/`; its five recorded inputs remain unchanged through completion, before the subsequent B1 finding. |
| N1/A1 candidate recorded/synthetic replay | `PYTHONDONTWRITEBYTECODE=1 python3 ../REGRESSION_MATRIX.py`, exit 0, recorded in `MATRIX02/`; 33/33 then-current `7ba7c6db` cases pass, while preserved original helpers fail 24/33. |
| N1/A1 candidate finding controls | `PYTHONDONTWRITEBYTECODE=1 python3 ../NORMAL_FINDING_REPLAY.py`, exit 0, recorded in `NORMAL_FINDING_GREEN01/`; the exact seven copied reviewer fixtures pass 7/7 on `7ba7c6db`, with their original five-negative RED preserved separately. |
| B1 causal RED | Same maintained self-check command with only B1 regression tests added, exit 1 in `BREAK_B1_RED01/`; production AST equals prior `7ba7c6db` and incorrectly returns readiness for tab-spaced Compacting. |
| Final maintained B1 GREEN | Same self-check command, exit 0 in `GREEN04/`, with all five inputs stable; includes bounded no-key Compacting counts and Working positive controls for four admitted whitespace forms across standalone, legacy and modern layouts. |
| Source compatibility | `SOURCE_CONTRACT_AUDIT.json` records unchanged caller/CLI/folder ASTs and modes; `git diff --check` exits 0. |

`REGRESSION_MATRIX.json` records each expected result, actual old/current result, key argv and the capture index preceding each key.
Its inputs include hashes of the actual capture artifacts, original launcher, the qualified launcher for that attempt, and replay script.
It AST-extracts actual helper definitions and constants rather than reimplementing their decisions.
The four raw captures are the supplied report-builder Working capture and the three final idle pane files, and synthetic transition inputs are explicitly labeled.

| Requirement | Failing old behavior and final passing coverage |
| --- | --- |
| Current Working precedence | Recorded Working capture, Working above legacy idle, and post-paste recorded Working fail on old helpers and pass with zero active-state keys. |
| Compacting precedence and bounds | Compacting above legacy/modern idle and post-paste Compacting fail on old helpers and pass with zero keys and bounded recapture. |
| Complete modern idle | All three recorded final idle layouts and the no-warning variant fail on old helpers and pass with one paste plus separately captured exact-pending Enter. |
| Zero keys for unknown/hook/unapproved states | Old Escape behavior fails; current unknown, hook, wrong-cwd and unapproved-cwd cases record no key in those states. |
| Fresh exact pending submission | Old post-paste Working, resumed pending-to-Working, hooks, truncated/mismatched text and unexpectedly empty composer cases fail; current sequences prevent the extra key. |
| Failed/stale-ready output | Existing failed/empty capture controls remain green, including failed captures whose stdout contains the previously ready idle, pending or folder text. |
| Exact-cwd authorization | The original matcher and positive Home/capture/Enter control are unchanged; wrong/new-cwd zero-key outcomes pass and selection resets after a failed capture. |
| Historical activity and handoff contract | Completed historical Working permits idle recovery; fake spawn retains its exact creation-success tuple and no readiness result substitutes for a live ACK. |
| Unsupported current boundary | Independent NORMAL's five negative cases were genuinely RED on the first candidate; changed Tip, truncated activity and alternate hook tails now remain unknown with zero keys, while recorded activity and completed-history positives remain green. |
| Narrow modern composer | Bare/blank modern glyphs are unknown with zero keys; the observed placeholder, exact pending text and original legacy empty composers remain green. |
| B1 Compacting whitespace | Author pure RED and break's independent RED establish premature Working/readiness for TAB, NBSP, space/TAB and EM SPACE. The maintained tests-only RED exits 1 before a one-line label trim; final `GREEN04` asserts exact bounded Compacting counts, one-capture Working, two-capture Compacting-to-Working, and three-capture post-paste transitions with no active-state keys. |

`TRIAGE.md` records N1, A1 and B1, their accepted scope, causal RED and focused GREEN evidence.
The prior `e7fc1fcb` candidate is preserved under `CANDIDATE_01/`; its passing limited tests are historical, not proof that the later-discovered boundary gap was absent.
The prior `5b522299` candidate is preserved under `CANDIDATE_02/`, including its normal 73-case clearance; break's initial 271-case clearance was explicitly superseded when B1 arrived and is not final clearance for this successor.
`B1_DELTA_AUDIT.json` verifies that only `_startup_activity` and the inline self-check ASTs changed from that candidate, with the bootstrap and all other production functions unchanged.
The older 33/7/73/271-case qualifications remain historical evidence and are not relabeled as executions on the B1 successor.

The inherited import warning about a missing site model policy appears in baseline, RED and GREEN logs because the isolated lease has no private local policy overlay.
No policy file was created or changed, and these startup tests do not claim that site model restrictions were verified.
There was no live launcher/native UI, real runtime, product E2E, build, device or deployment acceptance run.
No unrelated broad suite or package installation was needed for this two-file fake-capture change.

## Deploy / release impact

No product deployment, database migration, app release, dependency update or cloud action is required.
Independent normal/focused-break disposition is complete and accepted, with zero open findings.
This integrator generated the canonical map and report; root retains exact final intake verification, ordinary hooks, the local commit and safe contained branch/worktree closeout.
Normal's completed review remains exact history for its unchanged candidate, and main decision `39d49fe0-24b7-4951-a4dc-8541139117fc` accepts the subsequent B1 correction through focused failing-first tests and a short independent rebreak without waking closed normal or repeating its whole review.
The final focused break clearance for the exact B1 successor is present in the sealed packet cited above.
The canonical source/map were frozen for the root-owned four-path staging baton before this report was generated with the maintained `change-report` CLI.
The report's Part 2 comes directly from the actual staged working-tree facts against base `bc29de69`; it remains unedited.
The report itself is excluded from its own generated facts using the maintained `--out` path and is supplied to root for final staging.
Publication is not authorized.

The root-owned `AUREUS_TEST_CASES.xlsx` was inspected read-only as ZIP/XML and remains SHA256 `9f3f3cdc39f5a51c6a2a1c5d129fb7e05decd6ff1872a1ce41bcf59b50d4be11`.
Its actual tabs are CIRCLE, SKYZAI, REALITY_FUTURES and AGENTS; no IAC tab or matching operator-startup case was found.
`OPERATOR_STARTUP_PENDING.json` records the new IAC operator case using the existing six-column ID/Feature area/Test case/Expected result/Actual result/Status schema at A1:F2.
Root staging reply `6351643e-94c5-4052-8b09-9e85f330010a` accepted this placement and delegated preparation of the external workbook candidate.
`AUREUS_TEST_CASES_IAC_STARTUP_GUARD_1101_CANDIDATE.xlsx` in the canonical integration evidence directory is SHA256 `349d0250b0f8ea46ab74877fa97024e2359a53528abde318afa93b0b4fb520ca`; it adds only the IAC tab and twelve header/case cells at A1:F2.
`WORKBOOK_CANDIDATE.receipt.json` records actual ZIP CRC, sheet/schema/content/status and preservation assertions.
All nine unrelated ZIP members retain exact original local headers, compressed bytes and metadata; this includes all four original worksheets and `styles.xml`.
Only workbook.xml, its relationship list and content types gain one required new-sheet element each, with reverse-patch assertions proving all prior XML bytes unchanged.
The new case uses existing header style 4 and wrapped/top-aligned style 30; no style definition was changed.
The candidate is an external intake artifact, excluded from the source Git delta and kept separate from the root-owned canonical workbook.
The proposed case `IAC-STARTUP-GUARD-1101-01` is PENDING and records the offline qualification while explicitly leaving actual native startup, human-only trust cases and unique task ACK plus Working observation unperformed.
Root owns canonical workbook intake and mutation; this task wrote no canonical workbook cell and did no recalculation or rendering, preserving all 24 formulas, their caches, styles and unrelated ZIP records.
`conversation-context/OPERATOR_REQUESTS.md` remains the unchanged alias to the one `RAMESH_REQUESTS.md` ledger; no second request ledger was created.

The maintained `project-map --repo /Users/darkness/Work/Aureus --roots agentmail` generated the two canonical map records: 31 public tracked supported-source files, 29 documented, 29 internal links.
No previous canonical `docs/map/` existed, so no map backup was needed; this absence is recorded in `PROJECT_MAP.receipt.json`.
Collection is limited to tracked IAC `agentmail/` source, with no foreign business repositories, ignored attachments or credentials included.
The maintained extension filter excludes extensionless executables and Markdown, including the changed launcher/bootstrap, so their exact intake is covered by the separate source seal and report; generated map facts were not manually expanded or edited.
`docs/map/PROJECT_MAP.md` SHA256 is `44e71abcbd04f84b4bc6ca934cc7896ffd847265245d0ad2708afb72d3ee0011`; `docs/map/graph.json` SHA256 is `7be301c97b28b17b357f0f5dfdb3d5a38fc357c4e530ce9e112395c99647a243`.

The precise remaining race is the interval between completion of a successful capture/classification and tmux delivery of its following key, for paste, Home and Enter alike.
Text captures carry no generation identity, so a faulty provider replaying successful old output cannot be detected from these strings alone.
Only runtime support for atomic readiness and input could close that interval.
Unknown preceding UI, missing turn-ending boundaries, wrapped or truncated pending layouts stop instead of being guessed; this may require human handling of an unsupported layout.
The change grants no trust or operating-system permission and makes no universal-safety claim.

# Part 2: Facts (generated from git)

## Sensitive areas touched

- None.

## Commits


## Source files (2)

### `agentmail/bin/agentmail-launch` (modified, +161/-33)
- Added: `_startup_activity()`, `_startup_state()`
- Changed: `_startup_folder_matches()`, `_startup_idle_matches()`, `_submit_until_working()`, `check()`, `run()`

### `docs/map/graph.json` (added, +246/-0)

## Docs and context files (2)

### `agentmail/SUPERVISOR_BOOTSTRAP.md` (modified, +13/-1)

### `docs/map/PROJECT_MAP.md` (added, +56/-0)
