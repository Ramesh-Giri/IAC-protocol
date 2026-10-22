"""Exercise deterministic model filtering with synthetic policy and task fixtures.

Covers finite candidate combinations, conservative text triggers, catalogue failures,
policy validation and privacy-preserving append-only logs without network or live seats.
Run: python3 -m unittest agentmail/lib/test_model_guard.py.
"""
import itertools
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import model_guard as mg  # noqa: E402

RESTRICTED_MODELS = {"claude-test-restricted-a", "claude-test-restricted-b"}

ALL_KINDS = [
    "security_audit", "security_fix", "review", "feature", "ui", "bugfix",
    "integrate", "plan_research", "fix_findings", None,
]
ALL_MODELS = sorted(RESTRICTED_MODELS | {
    "claude-test-allowed-a", "claude-test-allowed-b",
    "gpt-test-allowed-a", "gpt-test-allowed-b", "gpt-test-allowed-c", "gpt-test-allowed-d", "gpt-test-allowed-e", "gpt-test-allowed-f", "gpt-test-allowed-g",
})
VERIFIED = {
    # Every ALL_MODELS id is verified here on purpose: this fixture stands in for "today's
    # catalogue says every candidate is real", so a test that isn't specifically about the
    # allowlist stage doesn't incidentally trip it. test_allowlist_drops_unverified_ids_* and
    # test_missing_catalogue_for_a_runtime_* cover the allowlist stage directly, with their
    # own deliberately-partial catalogues.
    "claude-code": {"claude-test-allowed-a", "claude-test-allowed-b"} | RESTRICTED_MODELS,
    "codex-cli": {"gpt-test-allowed-a", "gpt-test-allowed-b", "gpt-test-allowed-c", "gpt-test-allowed-d", "gpt-test-allowed-e",
                  "gpt-test-allowed-f", "gpt-test-allowed-g"},
}

# Synthetic examples cover independent policy concepts, with no private roster text.
FINAL_REVIEW_TEXT = "Review security and UI changes for a sample service."
SEC_AUDIT_TEXT = "Perform a security audit of the example API access rules."
BENIGN_TEXT = "add a button and fix the spacing"
REVIEW_TEXT = "Read-only review of a sample document editor."
PAYMENTS_TEXT = "Example payments backend with a high impact tier."
UI_TEXT = "Implement a sample Material interface in an isolated worktree."
DOCUMENT_RULES_TEXT = "Protect sample private documents with access rules."


def _all_candidates():
    """Every model paired with its plausible runtime -- not a full cross product, since a
    gpt-* id under runtime claude-code (or vice versa) is not a real seat shape."""
    out = []
    for m in ALL_MODELS:
        rt = "claude-code" if m.startswith("claude-") else "codex-cli"
        out.append(mg.Candidate(runtime=rt, model=m))
    return out


class ExhaustiveGuardTests(unittest.TestCase):
    def setUp(self):
        policy = mock.patch.multiple(mg, LOCKED_TIER=RESTRICTED_MODELS,
                                     ALLOW_SECURITY_REVIEW=False,
                                     LAYA_SECURITY_LOCK_FLOOR=0.2,
                                     HOST_TOOL_RUNTIME="claude-code", _POLICY_ERROR=None)
        policy.start()
        self.addCleanup(policy.stop)

    def test_pinned_seat_bypasses_everything(self):
        """pinned seat bypasses everything."""
        cands = _all_candidates()
        for kind, host_tool in itertools.product(ALL_KINDS, (True, False)):
            d = mg.resolve(cands, task_kind=kind, task_text=SEC_AUDIT_TEXT, pinned=True,
                            host_tool_required=host_tool, verified_ids=VERIFIED)
            self.assertEqual([c.model for c in d.candidates], [c.model for c in cands],
                              f"pinned seat was filtered for kind={kind}")

    def test_audit_lock_kinds_always_remove_restricted_models(self):
        """Audit lock kinds always remove restricted models."""
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
        """always tier text locks regardless of kind."""
        cands = _all_candidates()
        always_texts = [
            "Full example API security-audit skill run, backend + rules, report only.",
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
        """flavour tier locks by default for every kind including review."""
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
        """laya floor locks even with benign kind and text."""
        cands = _all_candidates()
        for laya in (0.0, 0.1, 0.19):
            d = mg.resolve(cands, task_kind="feature", task_text=BENIGN_TEXT,
                            laya_p_security=laya, verified_ids=VERIFIED)
            self.assertFalse(d.locked_audit, f"laya={laya} locked below the floor")
            self.assertTrue({c.model for c in d.candidates} & mg.LOCKED_TIER,
                             f"laya={laya} removed restricted models when it should not have")
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

    def test_review_and_audit_both_lock_with_configured_policy(self):
        """Review and audit both lock with configured policy."""
        cands = _all_candidates()
        self.assertFalse(mg.ALLOW_SECURITY_REVIEW,
                          "this fixture uses the conservative review default; if you flipped "
                          "the flag deliberately, update the test fixture "
                          "in the configured policy")
        d_review = mg.resolve(cands, task_kind="review", task_text=FINAL_REVIEW_TEXT, verified_ids=VERIFIED)
        d_audit = mg.resolve(cands, task_kind="security_audit", task_text=SEC_AUDIT_TEXT, verified_ids=VERIFIED)
        self.assertTrue(d_review.locked_audit, "a security-flavoured review brief did not lock under the configured policy")
        self.assertTrue(d_audit.locked_audit)
        self.assertTrue({c.model for c in d_review.candidates}.isdisjoint(mg.LOCKED_TIER))
        self.assertTrue({c.model for c in d_audit.candidates}.isdisjoint(mg.LOCKED_TIER))

    def test_non_security_briefs_do_not_lock(self):
        """non security briefs do not lock."""
        cands = _all_candidates()
        for label, text, kind in (
            ("plain review", REVIEW_TEXT, "review"),
            ("payments/blast-radius seat", PAYMENTS_TEXT, "feature"),
            ("UI seat", UI_TEXT, "ui"),
        ):
            d = mg.resolve(cands, task_kind=kind, task_text=text, verified_ids=VERIFIED)
            self.assertFalse(d.locked_audit, f"{label} ({text!r}) locked -- pattern is over-broad")
            self.assertTrue({c.model for c in d.candidates} & RESTRICTED_MODELS,
                             f"{label} lost a restricted candidate despite not being security-flavoured")

    def test_document_rules_trigger_conservative_lock(self):
        """document rules trigger conservative lock."""
        cands = _all_candidates()
        d = mg.resolve(cands, task_kind="feature", task_text=DOCUMENT_RULES_TEXT, verified_ids=VERIFIED)
        self.assertTrue(d.locked_audit,
                         "the document-access brief no longer locks on 'rules' -- if this was a deliberate "
                         "narrowing of security_lock_patterns.txt, update this test's docstring "
                         "and confirm the policy change was authorized")

    def test_one_line_toggle_is_the_only_thing_that_would_reopen_review(self):
        """one line toggle is the only thing that would reopen review."""
        cands = _all_candidates()
        original = mg.ALLOW_SECURITY_REVIEW
        try:
            mg.ALLOW_SECURITY_REVIEW = True  # the one-line change, hypothetical future relax
            d_review_flavour = mg.resolve(cands, task_kind="review", task_text=FINAL_REVIEW_TEXT, verified_ids=VERIFIED)
            d_review_always = mg.resolve(cands, task_kind="review", task_text=SEC_AUDIT_TEXT, verified_ids=VERIFIED)
            d_audit = mg.resolve(cands, task_kind="security_audit", task_text=SEC_AUDIT_TEXT, verified_ids=VERIFIED)
            d_benign = mg.resolve(cands, task_kind="feature", task_text=BENIGN_TEXT, verified_ids=VERIFIED)
            self.assertFalse(d_review_flavour.locked_audit, "flag flip did not exempt a bare-flavour review")
            self.assertTrue(d_review_always.locked_audit, "flag flip exempted ALWAYS-tier text on a review -- must never happen")
            self.assertTrue(d_audit.locked_audit, "flag flip changed the audit-kind lock -- must never depend on this flag")
            self.assertFalse(d_benign.locked_audit, "flag flip locked an unrelated benign task")
        finally:
            mg.ALLOW_SECURITY_REVIEW = original

    def test_bias_towards_over_locking_is_intentional_do_not_narrow(self):
        """bias towards over locking is intentional do not narrow."""
        cands = _all_candidates()
        # "rules" is genuine over-match bait (Firestore/security rules jargon in this fleet,
        # but the word alone could describe an unrelated "business rules" task) -- kept IN
        # the FLAVOUR tier on purpose.
        d = mg.resolve(cands, task_kind="feature", task_text="update the pricing rules", verified_ids=VERIFIED)
        self.assertTrue(d.locked_audit, "the FLAVOUR tier stopped over-matching 'rules' -- if this "
                         "was deliberate, update the explicit fixture rather than silently narrowing it")

    def test_host_tool_removes_non_claude_candidates_only(self):
        cands = _all_candidates()
        for kind in ALL_KINDS:
            d = mg.resolve(cands, task_kind=kind, task_text=BENIGN_TEXT, host_tool_required=True, verified_ids=VERIFIED)
            self.assertTrue(all(c.runtime == "claude-code" for c in d.candidates),
                             f"kind={kind} let a non-claude-code candidate through a host-tool task")

    def test_allowlist_drops_unverified_ids_deterministically(self):
        """allowlist drops unverified ids deterministically."""
        cands = _all_candidates() + [mg.Candidate(runtime="codex-cli", model="gpt-test-unverified")]
        for kind in ALL_KINDS:
            d = mg.resolve(cands, task_kind=kind, task_text=BENIGN_TEXT, verified_ids=VERIFIED)
            self.assertNotIn("gpt-test-unverified", {c.model for c in d.candidates},
                              f"kind={kind} let an unverified id through")

    def test_missing_catalogue_for_a_runtime_drops_its_candidates_not_passes_them(self):
        """missing catalogue for a runtime drops its candidates not passes them."""
        cands = _all_candidates()
        partial = {"claude-code": VERIFIED["claude-code"]}  # no codex-cli entry at all
        d = mg.resolve(cands, task_kind="feature", task_text=BENIGN_TEXT, verified_ids=partial)
        self.assertTrue(all(c.runtime == "claude-code" for c in d.candidates),
                         "a runtime with no catalogue reader let its candidates through unverified")

    def test_no_verified_ids_arg_skips_allowlist_explicitly(self):
        """no verified ids arg skips allowlist explicitly."""
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

    def test_log_schema_has_every_field_the_overseer_specified(self):
        """log schema has every field the overseer specified."""
        import json
        import tempfile
        cands = _all_candidates()
        d = mg.resolve(cands, task_kind="feature", task_text=BENIGN_TEXT, verified_ids=VERIFIED)
        with tempfile.TemporaryDirectory() as td:
            path = f"{td}/decisions.jsonl"
            mg.write_decision_log(path, d, task_id="demo-1", seat="demo-1",
                                    task_kind="feature", pinned=False,
                                    final_choice={"runtime": "claude-code", "model": "claude-test-allowed-a"})
            with open(path) as f:
                row = json.loads(f.readline())
        for key in ("seat", "brief_hash", "candidates_in", "locks_fired", "final_choice", "decided_by"):
            self.assertIn(key, row, f"log line is missing required field {key!r}")
        self.assertEqual(row["seat"], "demo-1")
        self.assertEqual(len(row["brief_hash"]), 64)  # sha256 hex digest
        self.assertEqual(row["candidates_in"], [{"runtime": c.runtime, "model": c.model} for c in cands])
        self.assertEqual(row["final_choice"], {"runtime": "claude-code", "model": "claude-test-allowed-a"})
        self.assertEqual(row["decided_by"], "guard")

    def test_brief_hash_never_leaks_the_text_itself(self):
        import json
        d = mg.resolve(_all_candidates(), task_kind="security_audit", task_text=SEC_AUDIT_TEXT, verified_ids=VERIFIED)
        row = d.to_log_dict(task_id="x")
        blob = json.dumps(row)
        self.assertNotIn(SEC_AUDIT_TEXT, blob)
        self.assertNotIn("example API", blob)  # a distinctive word from the raw brief

    def test_locks_fired_is_structured_not_prose(self):
        # host_tool_required would ALSO remove the invalid codex-cli id (wrong runtime for a
        # host-tool task), masking whether the allowlist stage independently fires -- so each
        # stage is checked in isolation here, not stacked in one call.
        cands_with_bad_id = _all_candidates() + [mg.Candidate(runtime="codex-cli", model="gpt-test-unverified")]
        d_security_and_allowlist = mg.resolve(cands_with_bad_id, task_kind="security_audit",
                                               task_text=SEC_AUDIT_TEXT, verified_ids=VERIFIED)
        self.assertEqual(set(d_security_and_allowlist.locks_fired), {"security_lock", "allowlist"})

        d_host_tool = mg.resolve(_all_candidates(), task_kind="feature", task_text=BENIGN_TEXT,
                                  host_tool_required=True, verified_ids=VERIFIED)
        self.assertEqual(d_host_tool.locks_fired, ["host_tool"])

        d_benign = mg.resolve(_all_candidates(), task_kind="feature", task_text=BENIGN_TEXT, verified_ids=VERIFIED)
        self.assertEqual(d_benign.locks_fired, [])  # nothing removed -- must stay empty, not omitted

    def test_patterns_file_missing_fails_loud_not_silent(self):
        """patterns file missing fails loud not silent."""
        import importlib
        import model_guard as real_mg  # noqa
        original = real_mg._PATTERNS_FILE
        try:
            real_mg._PATTERNS_FILE = Path("/nonexistent/security_lock_patterns.txt")
            with self.assertRaises(RuntimeError):
                real_mg._load_patterns()
        finally:
            real_mg._PATTERNS_FILE = original


class LocalPolicyTests(unittest.TestCase):
    def test_policy_is_explicit_and_validated(self):
        import json
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "policy.json"
            values = {"restricted_models": ["test-model"], "allow_security_review": False,
                      "security_score_floor": 0.3, "host_tool_runtime": "test-runtime"}
            path.write_text(json.dumps(values))
            self.assertEqual(mg._load_policy(path), values)
            for bad in ([], {"unknown": True}, {"restricted_models": "model"},
                        {"allow_security_review": "false"}, {"security_score_floor": 2},
                        {"security_score_floor": True}, {"host_tool_runtime": ""}):
                with self.subTest(bad=bad):
                    path.write_text(json.dumps(bad))
                    with self.assertRaises(ValueError):
                        mg._load_policy(path)
            path.unlink()
            with mock.patch.dict("os.environ", {}, clear=True):
                self.assertEqual(mg._load_policy(path), {})
            with mock.patch.dict("os.environ", {"IAC_MODEL_POLICY": str(path)}):
                with self.assertRaises(ValueError):
                    mg._load_policy(path)


if __name__ == "__main__":
    unittest.main()
