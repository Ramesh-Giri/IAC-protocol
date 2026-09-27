"""Phase 2 of modelpick-0927-x2q5: the deterministic hard-rule guard and the decision log.

Scope, deliberately narrow (per overseer GO on phase 2, 2026-09-27):
  - This module does NOT choose a model. A matcher (not built yet -- it needs a real
    capability catalogue, which is a separate, bigger piece of work) is assumed to have
    already produced an ORDERED list of (runtime, model) candidates for a task. This
    module's only jobs are: veto candidates a hard rule forbids, and log the decision.
  - It calls no network and no Laya. `resolve()` is a pure function over its arguments,
    exactly as agentmail/research/modelpick/DESIGN.md specifies: "One pure function ...
    lives in launcher-side code, not in the Laya client." Anything that needs live data
    (today's verified model ids, a headroom snapshot) is read OUTSIDE this module and
    passed in, so the guard itself stays exhaustively testable with almost no I/O -- the
    one exception is `security_lock_patterns.txt`, read once at import time, by design
    (see RULING below): it is a human-editable data file, never a code path.
  - Headroom/budget selection is OUT OF SCOPE here -- it is a later stage in the
    architecture ("Only the choice among ALREADY-PERMITTED candidates happens here.
    Headroom can never re-admit a model the hard-constraint filter removed.") and it needs
    a `fleet-usage` snapshot format that does not exist yet. This guard produces the
    ALREADY-PERMITTED list that stage would consume.
  - Nothing here is wired into `agentmail-launch`. That is a separate, later step needing
    its own explicit GO, same boundary the original design task set ("do not modify
    agentmail-launch ... touch no live fleet tooling") and nothing since has lifted it.

RULING (Ramesh via overseer-ramesh, 2026-09-27, modelpick-0927-x2q5, superseding this
module's first draft): security REVIEWS lock out Opus/Fable the same as audits. The lock is
triggered by TEXT, not by a kind classifier -- Laya's security recall tops out at 0.706 and
its own signals swing 28 points on option order alone (see DESIGN.md Part 4), so the pattern
list in `security_lock_patterns.txt` is the mechanism, Laya may only ADD locks, never remove
one, and the default is CLOSED: any security-flavoured text locks, whatever the kind says and
whatever the seat calls itself. A false lock costs nothing here (the lock target is Sonnet,
already ~78% of the fleet); a missed lock costs a blocked seat and a wasted launch, so the
patterns are deliberately biased towards over-matching -- see that file's own header.

The overseer still asked for the audit/review distinction to stay expressible as a one-line
change, in case a future ruling relaxes it: ALLOW_OPUS_FOR_SECURITY_REVIEW below, default
False (closed), gates ONLY the bare "flavour" tier of patterns for kind=review specifically.
The "always" tier (actual audit/pentest/exploit language) is never gated by this flag, for
any kind, ever -- see test_model_guard.py for the guarantee.
"""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

_PATTERNS_FILE = Path(__file__).resolve().with_name("security_lock_patterns.txt")

# ---------------------------------------------------------------------------
# Policy constants -- the parts meant to be edited without touching resolve()'s logic.
# ---------------------------------------------------------------------------

# One-line change, per the overseer's ask, for a FUTURE ruling only. Default False (closed):
# today, per the 2026-09-27 ruling, a bare security-flavour mention locks Opus/Fable out even
# for a review kind. Set True to exempt kind="review" from the FLAVOUR tier only -- the
# ALWAYS tier (real audit/pentest/exploit language) keeps locking regardless of this flag or
# the kind, no exceptions.
ALLOW_OPUS_FOR_SECURITY_REVIEW = False

# Kinds that lock unconditionally, regardless of what the text says (belt + suspenders --
# the pattern file should also catch these, but a kind label is stronger evidence than a
# keyword match and should not depend on the brief happening to use one of its exact words).
AUDIT_LOCK_KINDS = {"security_audit", "security_fix"}

# Laya's P(security) may TIGHTEN the lock (never loosen it), per the design's measured
# cost/benefit (a false lock just sends a seat to Sonnet, already 79% of seats) and the
# ruling above ("Laya may only ADD locks, never remove one"). This module never calls Laya;
# if a caller has a score, it passes it in. No caller does yet -- Laya is not wired in for
# phase 2.
LAYA_SECURITY_LOCK_FLOOR = 0.2

# Models that must never be recommended when the lock is active, however good a catalogue's
# `claimed` tier says they are. IDs, not display names, matching what a roster entry or a
# local catalogue actually uses.
OPUS_TIER = {"claude-opus-5-5", "claude-opus-5", "claude-opus-4-8", "claude-opus-4-7", "claude-opus-4-6"}
FABLE_TIER = {"claude-fable-5-1", "claude-fable-5"}
LOCKED_TIER = OPUS_TIER | FABLE_TIER


def _load_patterns() -> tuple[re.Pattern, re.Pattern]:
    """Read security_lock_patterns.txt -- fail LOUD if it's missing or empty, never fall
    back to an empty pattern (that would silently disable the lock, the one failure mode
    this whole module exists to prevent)."""
    if not _PATTERNS_FILE.exists():
        raise RuntimeError(f"model_guard: {_PATTERNS_FILE} is missing -- refusing to run "
                            f"with no security-lock patterns rather than silently disable the lock")
    always, flavour, section = [], [], None
    for raw in _PATTERNS_FILE.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line == "[ALWAYS]":
            section = always
            continue
        if line == "[FLAVOUR]":
            section = flavour
            continue
        if section is None:
            raise RuntimeError(f"model_guard: {_PATTERNS_FILE} has a phrase before any [SECTION] header: {line!r}")
        section.append(line)
    if not always or not flavour:
        raise RuntimeError(f"model_guard: {_PATTERNS_FILE} has an empty ALWAYS or FLAVOUR section")
    to_pattern = lambda phrases: re.compile("(?i:" + "|".join(re.escape(p) for p in phrases) + ")")
    return to_pattern(always), to_pattern(flavour)


AUDIT_TEXT_PATTERN, FLAVOUR_TEXT_PATTERN = _load_patterns()


@dataclass
class Candidate:
    runtime: str
    model: str


@dataclass
class Decision:
    candidates: list[Candidate]           # survivors, in the order they were given
    reasons: list[str]                    # every filter that fired, in order, even if it removed nothing
    locked_audit: bool                    # True if the security lock was active for this task
    decided_by: str = "guard"

    def to_log_dict(self, task_id: str, task_kind: Optional[str], pinned: bool) -> dict:
        return {
            "ts": time.time(),
            "task_id": task_id,
            "kind": task_kind,
            "pinned": pinned,
            "locked_audit": self.locked_audit,
            "survivors": [{"runtime": c.runtime, "model": c.model} for c in self.candidates],
            "reasons": self.reasons,
            "decided_by": self.decided_by,
        }


def _security_locked(kind: Optional[str], text: str, laya_p_security: Optional[float]) -> bool:
    if kind in AUDIT_LOCK_KINDS:
        return True
    if AUDIT_TEXT_PATTERN.search(text or ""):
        return True  # never gated by ALLOW_OPUS_FOR_SECURITY_REVIEW, whatever the kind
    if laya_p_security is not None and laya_p_security >= LAYA_SECURITY_LOCK_FLOOR:
        return True  # Laya only ever adds a lock, never removes one
    if FLAVOUR_TEXT_PATTERN.search(text or ""):
        if kind == "review" and ALLOW_OPUS_FOR_SECURITY_REVIEW:
            return False  # the one exemption a future ruling could grant, and only this one
        return True
    return False


def resolve(
    candidates: list[Candidate],
    *,
    task_kind: Optional[str] = None,
    task_text: str = "",
    laya_p_security: Optional[float] = None,
    host_tool_required: bool = False,
    verified_ids: Optional[dict[str, set[str]]] = None,
    pinned: bool = False,
) -> Decision:
    """Filter an already-ranked candidate list down to what the hard rules permit.

    NEVER re-orders or adds candidates -- only removes them, and only for a reason it
    records. `verified_ids` is {runtime: {model_id, ...}} from TODAY's local catalogue
    (see agentmail/bin/catalog-check); pass None to skip the allowlist check (e.g. a
    runtime this module doesn't have a catalogue reader for yet), not to mean "anything
    goes" -- callers that have no catalogue at all should treat the result as UNKNOWN,
    same as the design's failure-path rule, not as a pass.

    `pinned=True` means the caller already knows this is the overseer/council seat and
    should never have reached a matcher at all -- resolve() still returns a valid Decision
    for testability, but callers must short-circuit before ever building `candidates` for
    a pinned seat. This function does not know how to look up "is this seat pinned" itself
    (that lives in roster.json, which this module never reads).
    """
    reasons: list[str] = []
    survivors = list(candidates)

    if pinned:
        reasons.append("pinned seat -- guard should not have been called; returning candidates unfiltered")
        return Decision(candidates=survivors, reasons=reasons, locked_audit=False)

    locked = _security_locked(task_kind, task_text, laya_p_security)
    if locked:
        before = len(survivors)
        survivors = [c for c in survivors if c.model not in LOCKED_TIER]
        reasons.append(
            f"security lock active (kind={task_kind!r}, text/Laya matched a lock pattern): "
            f"removed {before - len(survivors)} Opus/Fable candidate(s)"
        )
    else:
        reasons.append("security lock not triggered")

    if host_tool_required:
        before = len(survivors)
        survivors = [c for c in survivors if c.runtime == "claude-code"]
        reasons.append(f"host-tool task: removed {before - len(survivors)} non-claude-code candidate(s)")

    if verified_ids is not None:
        before = len(survivors)
        kept = []
        for c in survivors:
            ids = verified_ids.get(c.runtime)
            if ids is None:
                # No catalogue reader for this runtime -- can't verify, don't silently allow.
                reasons.append(f"no local catalogue for runtime {c.runtime!r}: dropping {c.model!r} (unverifiable, not a pass)")
                continue
            if c.model not in ids:
                reasons.append(f"{c.model!r} not in today's {c.runtime} catalogue: removed, never invented")
                continue
            kept.append(c)
        survivors = kept
        if before == len(survivors):
            reasons.append("allowlist check: all survivors verified in today's catalogue")

    return Decision(candidates=survivors, reasons=reasons, locked_audit=locked)


def write_decision_log(log_path: str, decision: Decision, *, task_id: str, task_kind: Optional[str], pinned: bool = False) -> str:
    """Append one JSONL line. Append-only, never rewrites a prior line.

    Returns the line written (also useful for a caller that wants to print it, e.g. a demo
    or a future CLI, without re-reading the file).
    """
    line = json.dumps(decision.to_log_dict(task_id, task_kind, pinned), sort_keys=True)
    with open(log_path, "a") as f:
        f.write(line + "\n")
    return line
