"""Filter ranked runtime/model candidates and append privacy-preserving decision logs.

`resolve` applies deterministic text, runtime and catalogue checks without network calls.
The launcher uses this as advisory evidence and retains the roster's selected model.
Site model restrictions live in ignored local/model-policy.json, never in public defaults.
Set IAC_MODEL_POLICY to an explicit file, or IAC_ROOT to the workspace containing local/.
Missing policy warns that no site model restrictions are active; malformed supplied policy is an error.
Security trigger phrases remain in security_lock_patterns.txt and are loaded at import.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

_PATTERNS_FILE = Path(__file__).resolve().with_name("security_lock_patterns.txt")

def _load_policy(path: Path) -> dict:
    """Load optional local policy, refusing malformed or silently ignored settings."""
    if not path.exists():
        if os.environ.get("IAC_MODEL_POLICY"):
            raise ValueError(f"model_guard: configured policy is missing: {path}")
        print(f"WARNING: model_guard: NO SITE MODEL POLICY at {path}; "
              "zero site model restrictions are active. Set IAC_MODEL_POLICY to the approved policy file.",
              file=sys.stderr)
        return {}
    policy = json.loads(path.read_text())
    allowed = {"restricted_models", "allow_security_review", "security_score_floor", "host_tool_runtime"}
    if not isinstance(policy, dict) or set(policy) - allowed:
        raise ValueError("model_guard: policy must be an object containing only supported keys")
    models = policy.get("restricted_models", [])
    if not isinstance(models, list) or any(not isinstance(m, str) or not m.strip() for m in models):
        raise ValueError("model_guard: restricted_models must be a list of nonempty model IDs")
    if not isinstance(policy.get("allow_security_review", False), bool):
        raise ValueError("model_guard: allow_security_review must be boolean")
    floor = policy.get("security_score_floor", 0.2)
    if isinstance(floor, bool) or not isinstance(floor, (float, int)) or not 0 <= floor <= 1:
        raise ValueError("model_guard: security_score_floor must be between 0 and 1")
    runtime = policy.get("host_tool_runtime", "claude-code")
    if not isinstance(runtime, str) or not runtime.strip():
        raise ValueError("model_guard: host_tool_runtime must be a nonempty runtime ID")
    return policy


_POLICY_PATH = Path(os.environ.get("IAC_MODEL_POLICY") or
                    Path(os.environ.get("IAC_ROOT", Path(__file__).resolve().parents[2])) /
                    "local" / "model-policy.json")
try:
    _POLICY = _load_policy(_POLICY_PATH)
    _POLICY_ERROR = None
except (OSError, ValueError) as exc:
    _POLICY = {}
    _POLICY_ERROR = str(exc)
ALLOW_SECURITY_REVIEW = _POLICY.get("allow_security_review", False)
AUDIT_LOCK_KINDS = {"security_audit", "security_fix"}
LAYA_SECURITY_LOCK_FLOOR = _POLICY.get("security_score_floor", 0.2)
LOCKED_TIER = set(_POLICY.get("restricted_models", []))
HOST_TOOL_RUNTIME = _POLICY.get("host_tool_runtime", "claude-code")


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
    candidates_in: list[Candidate]        # the input list, before any filter ran
    reasons: list[str]                    # every filter that fired, in order, even if it removed nothing
    locked_audit: bool                    # True if the security lock was active for this task
    locks_fired: list[str]                # machine-readable: which stages actually removed >=1 candidate
    brief_hash: str                       # sha256(task_text) -- the log gets this, never the text itself
    decided_by: str = "guard"

    def to_log_dict(self, *, task_id: str, seat: Optional[str] = None, task_kind: Optional[str] = None,
                     pinned: bool = False, final_choice: Optional[dict] = None) -> dict:
        """`final_choice` is what the CALLER actually launched with (always the roster's own
        value at this integration point -- the guard is advisory here, see module docstring),
        as {"runtime": ..., "model": ...} or None if this decision was never tied to a launch
        (e.g. a demo run). It is a separate concept from `survivors`: the guard's opinion and
        the value actually used are logged side by side on purpose, so a later reader can see
        every case where they disagreed, not just today's (empty) diff."""
        return {
            "ts": time.time(),
            "task_id": task_id,
            "seat": seat if seat is not None else task_id,
            "kind": task_kind,
            "pinned": pinned,
            "brief_hash": self.brief_hash,
            "candidates_in": [{"runtime": c.runtime, "model": c.model} for c in self.candidates_in],
            "locked_audit": self.locked_audit,
            "locks_fired": self.locks_fired,
            "survivors": [{"runtime": c.runtime, "model": c.model} for c in self.candidates],
            "final_choice": final_choice,
            "reasons": self.reasons,
            "decided_by": self.decided_by,
        }


def _security_locked(kind: Optional[str], text: str, laya_p_security: Optional[float]) -> bool:
    if kind in AUDIT_LOCK_KINDS:
        return True
    if AUDIT_TEXT_PATTERN.search(text or ""):
        return True  # never gated by ALLOW_SECURITY_REVIEW, whatever the kind
    if laya_p_security is not None and laya_p_security >= LAYA_SECURITY_LOCK_FLOOR:
        return True  # Laya only ever adds a lock, never removes one
    if FLAVOUR_TEXT_PATTERN.search(text or ""):
        if kind == "review" and ALLOW_SECURITY_REVIEW:
            return False  # only the explicitly configured review exception
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
    locks_fired: list[str] = []
    candidates_in = list(candidates)
    survivors = list(candidates)
    brief_hash = hashlib.sha256((task_text or "").encode("utf-8")).hexdigest()

    if pinned:
        reasons.append("pinned seat -- guard should not have been called; returning candidates unfiltered")
        return Decision(candidates=survivors, candidates_in=candidates_in, reasons=reasons,
                         locked_audit=False, locks_fired=locks_fired, brief_hash=brief_hash)

    if _POLICY_ERROR:
        raise RuntimeError(f"model_guard: local policy unavailable: {_POLICY_ERROR}")

    locked = _security_locked(task_kind, task_text, laya_p_security)
    if locked:
        before = len(survivors)
        survivors = [c for c in survivors if c.model not in LOCKED_TIER]
        if before != len(survivors):
            locks_fired.append("security_lock")
        reasons.append(
            f"security lock active (kind={task_kind!r}, text/Laya matched a lock pattern): "
            f"removed {before - len(survivors)} restricted candidate(s)"
        )
    else:
        reasons.append("security lock not triggered")

    if host_tool_required:
        before = len(survivors)
        survivors = [c for c in survivors if c.runtime == HOST_TOOL_RUNTIME]
        if before != len(survivors):
            locks_fired.append("host_tool")
        reasons.append(f"host-tool task: removed {before - len(survivors)} candidate(s) outside {HOST_TOOL_RUNTIME}")

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
        if before != len(survivors):
            locks_fired.append("allowlist")
        else:
            reasons.append("allowlist check: all survivors verified in today's catalogue")

    return Decision(candidates=survivors, candidates_in=candidates_in, reasons=reasons,
                     locked_audit=locked, locks_fired=locks_fired, brief_hash=brief_hash)


def write_decision_log(log_path: str, decision: Decision, *, task_id: str, seat: Optional[str] = None,
                        task_kind: Optional[str] = None, pinned: bool = False,
                        final_choice: Optional[dict] = None) -> str:
    """Append one JSONL line. Append-only, never rewrites a prior line.

    Returns the line written (also useful for a caller that wants to print it, e.g. a demo
    or a future CLI, without re-reading the file).
    """
    line = json.dumps(decision.to_log_dict(task_id=task_id, seat=seat, task_kind=task_kind,
                                            pinned=pinned, final_choice=final_choice), sort_keys=True)
    with open(log_path, "a") as f:
        f.write(line + "\n")
    return line
