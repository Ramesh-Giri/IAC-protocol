---
name: flutter-a11y-audit
description: Audit a app Flutter screen or flow for semantics, screen-reader order, 48dp targets, contrast, keyboard focus, large text and reduced motion. Use on Flutter UI changes or accessibility reports alongside the Material 3 design gate.
---

<!-- Defines Flutter accessibility evidence alongside app's existing Material 3 review. -->
# Flutter accessibility audit

Read the [shared seat boundaries](../README.md#shared-seat-boundaries), IAC rules 25, 43 and 53, and `~/.claude/skills/material3-ui/SKILL.md` with its brand-kit and review-rubric references.
Use the consuming repo's approved brand pin, semantic color/type roles and existing Material 3 widgets.
Audit only unless the task also delegates remediation.

1. Name the route, full source SHA/patch identity, device/browser, Flutter version, viewport, appearance and user task.
   Cover Android and web for app, all supported appearances, and loading, empty, error and successful states.
   Reserve shared device time through the overseer; report unavailable platforms as gaps.
2. Inspect the Flutter semantics tree and the actual screen-reader announcements.
   Check meaningful names, roles, values, checked/selected/expanded/disabled states, headings, image descriptions and understandable error announcements.
   Match accessible action names to visible labels; label icon-only controls.
   Prefer Material's built-in semantics; use `Semantics`, `MergeSemantics` or `ExcludeSemantics` only where necessary and verify the resulting tree for duplicates or lost actions.
   Keep decorative images out of the reading order.
3. Measure the interactive hit area at least 48 by 48 logical pixels (48dp), including compact rows and adjacent icons.
   Ensure targets do not overlap and work by touch, keyboard, switch and assistive action where supported.
   A larger painted icon or tooltip does not prove a larger hit area.
4. Check text and control contrast against their actual composited background in each state and appearance.
   Require at least 4.5:1 for normal text, 3:1 for qualifying large text and 3:1 for required control/focus indicators against adjacent colors.
   Verify the large-text criterion before using its relaxed threshold.
   Do not communicate status only through color; use a label or meaningful icon too.
   Fix role-pair usage in scope; route canonical token defects to the brand owner rather than inventing replacement colors.
5. Follow keyboard focus and screen-reader reading order separately through the complete flow.
   Inspect `FocusTraversalGroup`/policy and semantic sort order when custom layout changes the natural order.
   Check visible focus, activation, modal entry and dismissal, focus restoration, and absence of traps.
   Confirm Back/title, error sentence, Retry and any partial data remain reachable in failure states.
6. Honor the user's `TextScaler`; test default, 200% and the platform's supported large-text maximum on a narrow viewport.
   Look for clipping, hidden actions, fixed-height overflow and truncated essential instructions.
   Check the installed Flutter SDK's platform accessibility flags for reduced/disabled motion; verify OS settings on each target rather than assuming one flag covers Android and iOS alike.
   Replace nonessential movement with a calm state cue while preserving progress and completion feedback.
7. Run focused semantic and accessibility guideline tests through the authorized testlane, using the installed SDK's `androidTapTargetGuideline`, `labeledTapTargetGuideline` and `textContrastGuideline` where applicable.
   Obtain a semantics handle and dispose it after the check.
   Add actual TalkBack navigation on Android and keyboard plus screen-reader navigation on web; include VoiceOver when iOS is in scope.
   A green widget test or screenshot cannot prove usable reading/focus order or full conformance.
   Follow [build-gate](../build-gate/SKILL.md) if an updated artifact is needed; do not start a heavy local build.

Report findings by route/component with severity, reproduction, expected announcement/interaction, actual result, screenshot or semantics evidence, and the tested settings/platforms.
Keep unperformed manual checks explicit and send them to [acceptance-gate](../acceptance-gate/SKILL.md).
Retain the Material 3 preview, brand self-check and independent approve/block review; accessibility evidence supplements that gate.

API references: [Flutter accessibility testing](https://docs.flutter.dev/ui/accessibility/accessibility-testing), [UI accessibility](https://docs.flutter.dev/ui/accessibility/ui-design-and-styling), [platform animation preference](https://api.flutter.dev/flutter/widgets/MediaQueryData/disableAnimations.html).
