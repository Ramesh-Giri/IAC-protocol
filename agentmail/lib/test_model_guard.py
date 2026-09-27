"""Exhaustive tests for model_guard.resolve(), per the overseer's requirement: 'the guard is
exhaustively unit-tested over the finite domain ... it is the only thing standing between a
security audit and a model whose safeguard dialog has already blocked two seats.'

Also encodes the 2026-09-27 ruling (security reviews lock out Opus too, default closed,
patterns biased towards over-locking on purpose) so nobody later "fixes" the over-matching
as a bug without reading why it's here.

The pattern list in security_lock_patterns.txt was written from the RULING's own wording
("audit, review, pen test, hardening, rules, secfix ..."), not derived from what the roster
currently holds -- the roster is the output the policy produces, not evidence for it. This
file uses real roster text only as a TEST CORPUS afterwards, to check the rule fires where it
should and stays silent where it shouldn't (overseer STOP mail, 2026-09-27, modelpick-0927-x2q5).

No network, no Laya, no file I/O except this file and security_lock_patterns.txt. Run:
  python3 -m unittest agentmail/lib/test_model_guard.py -v
from the repo root, or `python3 agentmail/lib/test_model_guard.py` directly.
"""
import itertools
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import model_guard as mg  # noqa: E402

ALL_KINDS = [
    "security_audit", "security_fix", "review", "feature", "ui", "bugfix",
    "integrate", "plan_research", "fix_findings", None,
]
ALL_MODELS = sorted(mg.OPUS_TIER | mg.FABLE_TIER | {
    "claude-sonnet-5", "claude-haiku-4-5-20251001",
    "gpt-6-astra", "gpt-6-sol", "gpt-6-luna", "gpt-5.6-terra", "gpt-5.6-sol", "gpt-5.6-luna", "gpt-5.5",
})
VERIFIED = {
    "claude-code": {"claude-sonnet-5", "claude-haiku-4-5-20251001", "claude-opus-5-5",
                    "claude-opus-5", "claude-fable-5-1", "claude-fable-5"},
    "codex-cli": {"gpt-6-astra", "gpt-6-sol", "gpt-6-luna", "gpt-5.6-terra", "gpt-5.6-sol",
                  "gpt-5.6-luna", "gpt-5.5"},
}

# The two real production seat descriptions that motivated the overseer's original question,
# and Ramesh's ruling on 2026-09-27 that both must now lock.
FINAL_REVIEW_TEXT = (
    "Independent read-only pre-deploy review of feature/chat-tasks security + UI "
    "(Claude, Codex saved)."
)
SEC_AUDIT_TEXT = "Full Cloudflare security-audit skill run, backend + rules, report only."

# A task with NO security flavour at all, for the "unrelated kinds must not lock" tests.
BENIGN_TEXT = "add a button and fix the spacing"

# Real production roster text used as a NEGATIVE test corpus -- per the overseer's STOP mail
# (2026-09-27, modelpick-0927-x2q5): "Calibrate against the RULE ... use the roster only as a
# test corpus to check the regex FIRES where it should", and specifically "test descriptions
# that must NOT lock ... a review with no security flavour, a KYB or payments seat, a UI task."
# These are read from the live roster as fixed strings, not used to DERIVE the pattern list --
# the pattern list came from the ruling's own wording (see security_lock_patterns.txt's
# header) before any of these were checked against it.
REAL_REVIEW_NO_SECURITY_FLAVOUR_TEXT = (
    "Read-only pre-deploy review of notes tree + chatTurn fixes 05e8a1bd..2d7b87fb."
)  # skyzai-notes-review-ramesh, still claude-opus-5 in the roster today -- proves ordinary
   # reviews are not swept up by the security ruling, only security-flavoured ones are.
REAL_PAYMENTS_TEXT = (
    "Circle backend + platform (payments blast radius — strong tier)"
)  # circle-ramesh -- a genuinely high-stakes, blast-radius-flagged seat with zero overlap
   # with any lock pattern; proves "blast radius" and "security" are not the same axis.
REAL_UI_TEXT = (
    "Circle MD3 parallel worker — draft-for-review in an isolated treehouse worktree; "
    "escalates by mail, never prompts the human"
)  # circle-sectors-ramesh -- a plain UI/MD3 task.

# Real production text that DOES lock, and a documented reason it is not a false positive
# even though it comes from a currently-Sonnet (not currently Opus-locked-out) seat: it is
# the deliberate over-locking bias, not a bug -- see the test using it, below.
REAL_KYB_TEXT = (
    "KYB private documents: backend, rules, migration (+ RAG block fix)."
)  # skyzai-kyb-backend-ramesh -- trips the FLAVOUR tier's bare "rules". Two independent
   # reasons this is intended, not a hole in the pattern: (1) Ramesh's ruling named "rules"
   # explicitly as a lock word, so removing it because ONE example over-matches would be
   # overriding an explicit instruction on a guess; (2) read plainly, "backend, rules,
   # migration" for a PRIVATE DOCUMENTS feature plausibly means the Firestore/access-control
   # rules protecting those documents, which is exactly the kind of change worth a
   # conservative lock. It is invisible today because the seat is already claude-sonnet-5,
   # so this changes no live behaviour -- it only matters if a future task ever proposed
   # Opus for KYB backend work. Flagged to the overseer as a live tension rather than
   # resolved silently either way (modelpick-0927-x2q5 mail thread).


def _all_candidates():
    """Every model paired with its plausible runtime -- not a full cross product, since a
    gpt-* id under runtime claude-code (or vice versa) is not a real seat shape."""
    out = []
    for m in ALL_MODELS:
        rt = "claude-code" if m.startswith("claude-") else "codex-cli"
        out.append(mg.Candidate(runtime=rt, model=m))
    return out


class ExhaustiveGuardTests(unittest.TestCase):
    def test_pinned_seat_bypasses_everything(self):
        """A pinned seat must get its candidates back untouched, whatever else is set --
        rule 2 (overseer/council are never routed)."""
        cands = _all_candidates()
        for kind, host_tool in itertools.product(ALL_KINDS, (True, False)):
            d = mg.resolve(cands, task_kind=kind, task_text=SEC_AUDIT_TEXT, pinned=True,
                            host_tool_required=host_tool, verified_ids=VERIFIED)
            self.assertEqual([c.model for c in d.candidates], [c.model for c in cands],
                              f"pinned seat was filtered for kind={kind}")

    def test_audit_lock_kinds_always_remove_opus_and_fable(self):
        """Exhaustive over every locked kind x every candidate: no survivor is ever in
        LOCKED_TIER. This is the invariant the overseer called out by name."""
        cands = _all_candidates()
        for kind in mg.AUDIT_LOCK_KINDS:
            for laya in (None, 0.0, 0.19, 0.2, 0.5, 1.0):
                d = mg.resolve(cands, task_kind=kind, task_text=BENIGN_TEXT, laya_p_security=laya,
                                verified_ids=VERIFIED)
                survivors = {c.model for c in d.candidates}
                self.assertTrue(survivors.isdisjoint(mg.LOCKED_TIER),
                                 f"kind={kind} laya={laya} let through {survivors & mg.LOCKED_TIER}")
                self.assertTrue(d.locked_audit)

    def test_always_tier_text_locks_regardless_of_kind(self):
        """A brief whose TEXT matches the ALWAYS tier locks even if the kind label says
        something else, and even for kind='review' -- this tier is never gated by
        ALLOW_OPUS_FOR_SECURITY_REVIEW, no exceptions, per the ruling."""
        cands = _all_candidates()
        always_texts = [
            "Full Cloudflare security-audit skill run, backend + rules, report only.",
            "security audit, penetration test or vulnerability hunt",
            "Pen test the payment webhook before go-live",
            "supply-chain audit of the release pipeline",
            "red-team the auth flow",
        ]
        for kind in ALL_KINDS:
            for text in always_texts:
                d = mg.resolve(cands, task_kind=kind, task_text=text, verified_ids=VERIFIED)
                survivors = {c.model for c in d.candidates}
                self.assertTrue(survivors.isdisjoint(mg.LOCKED_TIER),
                                 f"kind={kind} text={text!r} let through {survivors & mg.LOCKED_TIER}")
                self.assertTrue(d.locked_audit)

    def test_flavour_tier_locks_by_default_for_every_kind_including_review(self):
        """The 2026-09-27 ruling: default is CLOSED. A bare security-flavour mention locks
        for every kind, review included -- not just the ALWAYS-tier phrases."""
        cands = _all_candidates()
        flavour_texts = [
            "security + UI cleanup",
            "secfix the login flow",
            "hardening pass on the API",
            "Firestore rules review",
            "rotate the private key",
        ]
        for kind in ALL_KINDS:
            for text in flavour_texts:
                d = mg.resolve(cands, task_kind=kind, task_text=text, verified_ids=VERIFIED)
                self.assertTrue(d.locked_audit, f"kind={kind} text={text!r} did not lock under the closed default")
                self.assertTrue({c.model for c in d.candidates}.isdisjoint(mg.LOCKED_TIER))

    def test_laya_floor_locks_even_with_benign_kind_and_text(self):
        """Laya may only TIGHTEN, never loosen -- confirm it can independently trigger the
        lock at/above the floor, and does not below it, holding kind and text constant and
        benign (a 'feature' task with no security words at all)."""
        cands = _all_candidates()
        for laya in (0.0, 0.1, 0.19):
            d = mg.resolve(cands, task_kind="feature", task_text=BENIGN_TEXT,
                            laya_p_security=laya, verified_ids=VERIFIED)
            self.assertFalse(d.locked_audit, f"laya={laya} locked below the floor")
            self.assertTrue({c.model for c in d.candidates} & mg.LOCKED_TIER,
                             f"laya={laya} removed Opus/Fable when it should not have")
        for laya in (0.2, 0.3, 0.9, 1.0):
            d = mg.resolve(cands, task_kind="feature", task_text=BENIGN_TEXT,
                            laya_p_security=laya, verified_ids=VERIFIED)
            self.assertTrue(d.locked_audit, f"laya={laya} did not lock at/above the floor")

    def test_non_security_kinds_with_benign_text_never_lock(self):
        benign_kinds = set(ALL_KINDS) - mg.AUDIT_LOCK_KINDS
        cands = _all_candidates()
        for kind in benign_kinds:
            d = mg.resolve(cands, task_kind=kind, task_text=BENIGN_TEXT, verified_ids=VERIFIED)
            self.assertFalse(d.locked_audit, f"kind={kind} locked with no trigger present")
            self.assertTrue({c.model for c in d.candidates} & mg.LOCKED_TIER)

    def test_review_and_audit_both_lock_per_the_ruling(self):
        """The RULE says any security-flavoured task locks, review included. This checks the
        pattern list FIRES on the two real briefs that raised the original question -- it is
        not where the rule came from (the pattern list was written from the ruling's own
        wording in security_lock_patterns.txt, before this test existed), it is confirmation
        that the rule, tested against real text, does what the ruling says. Per the overseer's
        2026-09-27 STOP mail: the roster is the output the rule produces, not the evidence for
        it -- do not read this test the other way around."""
        cands = _all_candidates()
        self.assertFalse(mg.ALLOW_OPUS_FOR_SECURITY_REVIEW,
                          "this test documents the RULING's default (closed); if you flipped "
                          "the flag on purpose per a NEW ruling, update this test and say so "
                          "in the phase 2 mail")
        d_review = mg.resolve(cands, task_kind="review", task_text=FINAL_REVIEW_TEXT, verified_ids=VERIFIED)
        d_audit = mg.resolve(cands, task_kind="security_audit", task_text=SEC_AUDIT_TEXT, verified_ids=VERIFIED)
        self.assertTrue(d_review.locked_audit, "a security-flavoured review brief did not lock -- the ruling requires it to")
        self.assertTrue(d_audit.locked_audit)
        self.assertTrue({c.model for c in d_review.candidates}.isdisjoint(mg.LOCKED_TIER))
        self.assertTrue({c.model for c in d_audit.candidates}.isdisjoint(mg.LOCKED_TIER))

    def test_non_security_briefs_do_not_lock(self):
        """The negative side the overseer's STOP mail specifically asked for, or the pattern
        is useless: a review with no security flavour, a payments seat, and a UI task, all
        real production text, none of it used to build the pattern list (which came from the
        ruling's wording). If any of these locks, the pattern over-matches badly enough to be
        worthless -- these are exactly the honest failure cases that would show it."""
        cands = _all_candidates()
        for label, text, kind in (
            ("plain review", REAL_REVIEW_NO_SECURITY_FLAVOUR_TEXT, "review"),
            ("payments/blast-radius seat", REAL_PAYMENTS_TEXT, "feature"),
            ("UI seat", REAL_UI_TEXT, "ui"),
        ):
            d = mg.resolve(cands, task_kind=kind, task_text=text, verified_ids=VERIFIED)
            self.assertFalse(d.locked_audit, f"{label} ({text!r}) locked -- pattern is over-broad")
            self.assertTrue({c.model for c in d.candidates} & mg.OPUS_TIER,
                             f"{label} lost Opus as a candidate despite not being security-flavoured")

    def test_real_kyb_brief_locks_on_the_word_rules_documented_tension(self):
        """A real, currently-benign-looking brief (skyzai-kyb-backend-ramesh, today
        claude-sonnet-5, so this changes no live behaviour) trips the FLAVOUR tier's bare
        'rules'. This is flagged, not silently resolved: Ramesh's ruling named 'rules'
        explicitly as a lock word, and read plainly this brief's 'rules' plausibly means the
        access-control rules for a PRIVATE DOCUMENTS feature -- a defensible over-lock, not
        an obvious bug. Kept locking on purpose; see the mail thread (modelpick-0927-x2q5) for
        the reasoning and the standing invitation to narrow 'rules' if Ramesh says otherwise."""
        cands = _all_candidates()
        d = mg.resolve(cands, task_kind="feature", task_text=REAL_KYB_TEXT, verified_ids=VERIFIED)
        self.assertTrue(d.locked_audit,
                         "the KYB brief no longer locks on 'rules' -- if this was a deliberate "
                         "narrowing of security_lock_patterns.txt, update this test's docstring "
                         "and confirm it was an explicit ruling, not a guess")

    def test_one_line_toggle_is_the_only_thing_that_would_reopen_review(self):
        """Flip the flag (the one-line change the overseer asked to keep available for a
        FUTURE ruling); confirm ONLY a bare-flavour review is affected -- the ALWAYS tier
        never is, for any kind, and unrelated benign kinds never are either."""
        cands = _all_candidates()
        original = mg.ALLOW_OPUS_FOR_SECURITY_REVIEW
        try:
            mg.ALLOW_OPUS_FOR_SECURITY_REVIEW = True  # the one-line change, hypothetical future relax
            d_review_flavour = mg.resolve(cands, task_kind="review", task_text=FINAL_REVIEW_TEXT, verified_ids=VERIFIED)
            d_review_always = mg.resolve(cands, task_kind="review", task_text=SEC_AUDIT_TEXT, verified_ids=VERIFIED)
            d_audit = mg.resolve(cands, task_kind="security_audit", task_text=SEC_AUDIT_TEXT, verified_ids=VERIFIED)
            d_benign = mg.resolve(cands, task_kind="feature", task_text=BENIGN_TEXT, verified_ids=VERIFIED)
            self.assertFalse(d_review_flavour.locked_audit, "flag flip did not exempt a bare-flavour review")
            self.assertTrue(d_review_always.locked_audit, "flag flip exempted ALWAYS-tier text on a review -- must never happen")
            self.assertTrue(d_audit.locked_audit, "flag flip changed the audit-kind lock -- must never depend on this flag")
            self.assertFalse(d_benign.locked_audit, "flag flip locked an unrelated benign task")
        finally:
            mg.ALLOW_OPUS_FOR_SECURITY_REVIEW = original

    def test_bias_towards_over_locking_is_intentional_do_not_narrow(self):
        """Documents the explicit trade-off from the ruling: a false lock is free (target is
        Sonnet, already the default), so the FLAVOUR patterns are allowed to over-match
        unrelated text that happens to share a word. This test exists so a future cleanup
        that "fixes" over-matching by narrowing these patterns fails loudly and has to read
        why, instead of silently reintroducing a missed-lock risk."""
        cands = _all_candidates()
        # "rules" is genuine over-match bait (Firestore/security rules jargon in this fleet,
        # but the word alone could describe an unrelated "business rules" task) -- kept IN
        # the FLAVOUR tier on purpose.
        d = mg.resolve(cands, task_kind="feature", task_text="update the pricing rules", verified_ids=VERIFIED)
        self.assertTrue(d.locked_audit, "the FLAVOUR tier stopped over-matching 'rules' -- if this "
                         "was deliberate, it needs a new ruling recorded here, not a silent narrowing")

    def test_host_tool_removes_non_claude_candidates_only(self):
        cands = _all_candidates()
        for kind in ALL_KINDS:
            d = mg.resolve(cands, task_kind=kind, task_text=BENIGN_TEXT, host_tool_required=True, verified_ids=VERIFIED)
            self.assertTrue(all(c.runtime == "claude-code" for c in d.candidates),
                             f"kind={kind} let a non-claude-code candidate through a host-tool task")

    def test_allowlist_drops_unverified_ids_deterministically(self):
        """The exact live finding from phase 1: a model id absent from today's catalogue
        must never survive, whatever the kind or lock state."""
        cands = _all_candidates() + [mg.Candidate(runtime="codex-cli", model="gpt-5.3-codex-spark")]
        for kind in ALL_KINDS:
            d = mg.resolve(cands, task_kind=kind, task_text=BENIGN_TEXT, verified_ids=VERIFIED)
            self.assertNotIn("gpt-5.3-codex-spark", {c.model for c in d.candidates},
                              f"kind={kind} let an unverified id through")

    def test_missing_catalogue_for_a_runtime_drops_its_candidates_not_passes_them(self):
        """UNKNOWN must never be treated as a pass (design's failure-path rule)."""
        cands = _all_candidates()
        partial = {"claude-code": VERIFIED["claude-code"]}  # no codex-cli entry at all
        d = mg.resolve(cands, task_kind="feature", task_text=BENIGN_TEXT, verified_ids=partial)
        self.assertTrue(all(c.runtime == "claude-code" for c in d.candidates),
                         "a runtime with no catalogue reader let its candidates through unverified")

    def test_no_verified_ids_arg_skips_allowlist_explicitly(self):
        """verified_ids=None is a deliberate opt-out (documented), not an accidental pass --
        confirm nothing is silently dropped for allowlist reasons when it's omitted."""
        cands = _all_candidates()
        d = mg.resolve(cands, task_kind="feature", task_text=BENIGN_TEXT)
        self.assertEqual(len(d.candidates), len(cands))
        self.assertFalse(any("allowlist" in r or "catalogue" in r for r in d.reasons))

    def test_decision_log_is_append_only_jsonl(self):
        import json
        import tempfile
        cands = _all_candidates()
        d1 = mg.resolve(cands, task_kind="security_audit", task_text=SEC_AUDIT_TEXT, verified_ids=VERIFIED)
        d2 = mg.resolve(cands, task_kind="feature", task_text=BENIGN_TEXT, verified_ids=VERIFIED)
        with tempfile.TemporaryDirectory() as td:
            path = f"{td}/decisions.jsonl"
            mg.write_decision_log(path, d1, task_id="t1", task_kind="security_audit")
            mg.write_decision_log(path, d2, task_id="t2", task_kind="feature")
            with open(path) as f:
                lines = f.read().splitlines()
            self.assertEqual(len(lines), 2)
            row1, row2 = json.loads(lines[0]), json.loads(lines[1])
            self.assertEqual(row1["task_id"], "t1")
            self.assertTrue(row1["locked_audit"])
            self.assertEqual(row2["task_id"], "t2")
            self.assertFalse(row2["locked_audit"])
            self.assertTrue(all(m not in mg.LOCKED_TIER for s in row1["survivors"] for m in [s["model"]]))

    def test_patterns_file_missing_fails_loud_not_silent(self):
        """The one piece of I/O this module does: if the pattern file vanished, refuse to
        run rather than silently disable the lock. Exercised via the loader directly since
        module-level load already happened at import time for the real file."""
        import importlib
        import model_guard as real_mg  # noqa
        original = real_mg._PATTERNS_FILE
        try:
            real_mg._PATTERNS_FILE = Path("/nonexistent/security_lock_patterns.txt")
            with self.assertRaises(RuntimeError):
                real_mg._load_patterns()
        finally:
            real_mg._PATTERNS_FILE = original


if __name__ == "__main__":
    unittest.main()
