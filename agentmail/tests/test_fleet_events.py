"""Outcome evidence through real CLIs, isolated spools, and temporary Git repos."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stderr, redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import time
import unittest
import uuid
from unittest.mock import patch

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / "lib"))
import iac
import fleet_events as fe


class FleetEvents(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="iac-outcomes-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = {"roster_owner": "parent", "agents": {
            "parent": {"role": "parent"},
            "worker": {"role": "child", "task_id": "task-1", "custom": "preserved"},
            "reviewer": {"role": "worker", "task_id": "review-1"}}}
        self.save()
        for seat in self.data["agents"]:
            for box in ("new", "cur", "tmp"):
                (self.root / seat / box).mkdir(parents=True)
        self.env = dict(os.environ)
        for key in ("AGENTMAIL_SEAT", "AGENTMAIL_SITE", "AGENTMAIL_DIR"):
            self.env.pop(key, None)
        self.env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
                        GIT_AUTHOR_NAME="IAC Test", GIT_AUTHOR_EMAIL="test@example.invalid",
                        GIT_COMMITTER_NAME="IAC Test", GIT_COMMITTER_EMAIL="test@example.invalid")

    def save(self):
        (self.root / "roster.json").write_text(json.dumps(self.data), encoding="utf-8")

    def cli(self, command, *args):
        return subprocess.run([sys.executable, str(BASE / "bin" / command), "-d", str(self.root), *args],
                              env=self.env, capture_output=True, text=True, timeout=15)

    def events(self):
        return [json.loads(row) for row in (self.root / "events.jsonl").read_text(encoding="utf-8").splitlines()]

    def event_cli(self, *args):
        return self.cli("fleet-event", fe.EventType.INTEGRATED.value, "--task-id", "task-1",
                        "--seat", "worker", "--actor", "parent", *args)

    def close_cli(self, outcome=fe.Outcome.NOT_INTEGRATED, *args):
        return self.cli("seat-close", "worker", "--outcome", outcome.value,
                        "--reason", "Report delivered", *args)

    def git_repo(self):
        repo = self.root / "repo"
        repo.mkdir()
        def git(*args):
            return subprocess.run(["git", "-C", str(repo), *args], env=self.env, capture_output=True,
                                  text=True, timeout=10, check=True).stdout.strip()
        git("init", "-q")
        git("commit", "-q", "--allow-empty", "-m", "fixture")
        return repo, git("rev-parse", "HEAD"), git

    def test_append_preserves_prior_bytes_and_utf8(self):
        first = self.event_cli("--reason", "Research café")
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        old = (self.root / "events.jsonl").read_bytes()
        self.assertIn("café".encode("utf-8"), old)
        self.assertEqual(self.event_cli("--review-round", "2", "--verdict", "pass").returncode, 0)
        self.assertTrue((self.root / "events.jsonl").read_bytes().startswith(old))
        events = self.events()
        self.assertEqual(len(events), 2)
        for event in events:
            self.assertEqual(str(uuid.UUID(event["event_id"])), event["event_id"])
            self.assertTrue(event["time_utc"].endswith("Z"))
            self.assertEqual(event["event_type"], fe.EventType.INTEGRATED)
            self.assertEqual(event["task_id"], "task-1")
            self.assertEqual(event["seat_id"], "worker")
            self.assertEqual(event["actor"], "parent")
        self.assertEqual(events[1]["review_round"], 2)

    def test_concurrent_appends_are_complete_unique_lines(self):
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda n: self.event_cli("--reason", str(n)), range(24)))
        self.assertTrue(all(result.returncode == 0 for result in results))
        events = self.events()
        self.assertEqual(len(events), 24)
        self.assertEqual(len({event["event_id"] for event in events}), 24)
        self.assertEqual({event["reason"] for event in events}, {str(n) for n in range(24)})

    def test_append_waits_for_kernel_lock(self):
        with iac.lock(self.root, "events"):
            process = subprocess.Popen([sys.executable, str(BASE / "bin/fleet-event"), "-d", str(self.root),
                                        fe.EventType.ACK.value, "--task-id", "task-1", "--seat", "worker"],
                                       env=self.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                time.sleep(0.15)
                self.assertIsNone(process.poll())
                self.assertFalse((self.root / "events.jsonl").exists())
            except BaseException:
                process.kill()
                process.communicate()
                raise
        stdout, stderr = process.communicate(timeout=5)
        self.assertEqual(process.returncode, 0, stdout + stderr)
        self.assertEqual(len(self.events()), 1)

    def test_invalid_enums_flags_and_rounds_do_not_write(self):
        for args in (("unknown", "--task-id", "task-1", "--seat", "worker"),
                     (fe.EventType.DONE.value, "--task-id", "task-1", "--seat", "worker", "--typo"),
                     (fe.EventType.DONE.value, "--task-id", "task-1", "--seat", "worker", "--review-rou", "1")):
            with self.subTest(args=args):
                result = self.cli("fleet-event", *args)
                self.assertEqual(result.returncode, 2)
                self.assertIn("error:", result.stdout)
        self.assertNotEqual(self.event_cli("--review-round", "0").returncode, 0)
        self.assertEqual(self.cli("seat-close", "worker", "--outcome", "unknown", "--reason", "x").returncode, 2)
        with self.assertRaises(ValueError):
            fe.append_event(self.root, "unknown", "task-1", "worker", "parent")
        self.assertFalse((self.root / "events.jsonl").exists())

    def test_full_commit_is_verified_and_short_missing_and_blob_refused(self):
        repo, sha, git = self.git_repo()
        self.assertEqual(self.event_cli("--repo", str(repo), "--commit", sha).returncode, 0)
        blob = git("hash-object", "-w", "--stdin")
        for value in (sha[:8], "0" * 40, blob):
            with self.subTest(value=value):
                self.assertNotEqual(self.event_cli("--repo", str(repo), "--commit", value).returncode, 0)
        self.assertEqual(len(self.events()), 1)

    def test_full_commit_without_repo_and_all_optional_fields(self):
        sha = "a" * 40
        result = self.event_cli("--commit", sha, "--related-commit", "b" * 40,
                                "--branch", "main", "--replaced-by", "task-2", "--reason", "fixed",
                                "--verdict", "accepted", "--review-round", "1")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(self.events()[0]["related_commit"], "b" * 40)
        self.assertEqual(self.events()[0]["commit"], sha)

    def test_close_atomically_preserves_roster_and_records_evidence(self):
        result = self.close_cli()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        data = iac.roster(self.root)
        entry = data["agents"]["worker"]
        self.assertEqual(entry["status"], fe.SeatStatus.CLOSED)
        self.assertEqual(entry["outcome"], fe.Outcome.NOT_INTEGRATED)
        self.assertEqual(entry["commits"], [])
        self.assertEqual(entry["custom"], "preserved")
        self.assertEqual(data["agents"]["parent"], self.data["agents"]["parent"])
        event, = self.events()
        self.assertEqual(event["event_type"], fe.EventType.CLOSED)
        self.assertEqual(entry["closed_at"], event["time_utc"])
        self.assertEqual(entry["close_event_id"], event["event_id"])

    def test_identical_close_is_noop_and_conflicting_close_refused(self):
        self.assertEqual(self.close_cli().returncode, 0)
        original = (self.root / "roster.json").read_bytes()
        self.assertEqual(self.close_cli().returncode, 0)
        self.assertNotEqual(self.close_cli(fe.Outcome.FAILED).returncode, 0)
        self.assertEqual(len(self.events()), 1)
        self.assertEqual((self.root / "roster.json").read_bytes(), original)

    def test_merged_requires_verified_commits_and_records_multiple(self):
        for outcome in (fe.Outcome.MERGED, fe.Outcome.MERGED_THEN_REWORKED):
            with self.subTest(outcome=outcome):
                self.assertNotEqual(self.close_cli(outcome).returncode, 0)
                self.assertNotEqual(self.close_cli(outcome, "--commit", "a" * 40).returncode, 0)
        repo, first, git = self.git_repo()
        git("commit", "-q", "--allow-empty", "-m", "second")
        second = git("rev-parse", "HEAD")
        self.assertNotEqual(self.close_cli(fe.Outcome.MERGED, "--repo", str(repo), "--commit", "0" * 40).returncode, 0)
        result = self.close_cli(fe.Outcome.MERGED_THEN_REWORKED, "--repo", str(repo), "--commit", first,
                                "--commit", second, "--branch", "main")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(iac.roster(self.root)["agents"]["worker"]["commits"], [first, second])
        self.assertEqual(self.events()[0]["commits"], [first, second])

    def test_superseded_requires_replacement_and_refuses_self(self):
        self.assertNotEqual(self.close_cli(fe.Outcome.SUPERSEDED).returncode, 0)
        self.assertNotEqual(self.close_cli(fe.Outcome.SUPERSEDED, "--replaced-by", "task-1").returncode, 0)
        self.assertEqual(self.close_cli(fe.Outcome.SUPERSEDED, "--replaced-by", "task-2").returncode, 0)
        self.assertEqual(iac.roster(self.root)["agents"]["worker"]["replaced_by"], "task-2")

    def test_missing_reason_unknown_seat_task_mismatch_and_legacy_task(self):
        original = (self.root / "roster.json").read_bytes()
        for args in (("worker", "--outcome", fe.Outcome.FAILED.value),
                     ("absent", "--outcome", fe.Outcome.FAILED.value, "--reason", "x")):
            self.assertNotEqual(self.cli("seat-close", *args).returncode, 0)
        self.assertNotEqual(self.close_cli(fe.Outcome.FAILED, "--task-id", "other").returncode, 0)
        self.assertNotEqual(self.cli("seat-close", "worker", "--outcome", fe.Outcome.FAILED.value,
                                    "--reason", "  ").returncode, 0)
        self.assertEqual((self.root / "roster.json").read_bytes(), original)
        self.data["agents"]["worker"].pop("task_id")
        self.save()
        self.assertNotEqual(self.close_cli().returncode, 0)
        self.assertEqual(self.close_cli(fe.Outcome.NOT_INTEGRATED, "--task-id", "legacy-task").returncode, 0)

    def test_event_failure_leaves_roster_unchanged(self):
        original = (self.root / "roster.json").read_bytes()
        with patch.object(fe, "_append_locked", side_effect=OSError("fixture event failure")):
            with self.assertRaises(OSError):
                fe.close_seat(self.root, "worker", fe.Outcome.FAILED, "failed", actor="parent")
        self.assertEqual((self.root / "roster.json").read_bytes(), original)

    def test_symlink_log_is_refused_without_changing_target_or_roster(self):
        target = self.root / "other-file"
        target.write_text("preserve\n")
        (self.root / "events.jsonl").symlink_to(target)
        original = (self.root / "roster.json").read_bytes()
        self.assertNotEqual(self.event_cli().returncode, 0)
        self.assertNotEqual(self.close_cli().returncode, 0)
        self.assertEqual(target.read_text(), "preserve\n")
        self.assertEqual((self.root / "roster.json").read_bytes(), original)

    def test_concurrent_closes_preserve_each_seat(self):
        for n in range(8):
            self.data["agents"][f"worker-{n}"] = {"task_id": f"task-{n}"}
        self.save()
        def close(n):
            return self.cli("seat-close", f"worker-{n}", "--outcome", fe.Outcome.ABANDONED.value, "--reason", "stopped")
        with ThreadPoolExecutor(max_workers=8) as pool:
            self.assertTrue(all(result.returncode == 0 for result in pool.map(close, range(8))))
        data = iac.roster(self.root)
        self.assertTrue(all(data["agents"][f"worker-{n}"]["outcome"] == fe.Outcome.ABANDONED for n in range(8)))
        self.assertEqual(len(self.events()), 8)

    def launch(self, success=True, dry=False):
        main = runpy.run_path(str(BASE / "bin/agentmail-launch"))["main"]
        self.data["agents"] = {"worker": {"role": "child", "home": str(self.root), "runtime": "fixture",
                                           "model": "fixture-model", "effort": "high", "task_id": "task-1",
                                           "codex_home": "/fixture/codex"}}
        self.save()
        output, errors = io.StringIO(), io.StringIO()
        with patch.dict(main.__globals__, build_command=lambda *a: "fixture command",
                        spawn=lambda *a, **kw: (success, "fixture failure"),
                        guard_report=lambda *a: {}, _guard_summary_line=lambda *a: "fixture",
                        _launch_gate_problems=lambda *a: [], _log_launch_decision=lambda *a: None), \
                patch.dict(os.environ, self.env, clear=True), redirect_stdout(output), redirect_stderr(errors):
            code = main(["-d", str(self.root), "--seat", "worker", "--terminal", "tmux"] + ([] if dry else ["--apply"]))
        return code, output.getvalue(), errors.getvalue()

    def test_launch_writes_runtime_and_rules_blob_hash(self):
        code, out, err = self.launch()
        self.assertEqual(code, 0, out + err)
        event, = self.events()
        self.assertEqual(event["event_type"], fe.EventType.LAUNCHED)
        for key in ("task_id", "runtime", "model", "effort", "codex_home"):
            self.assertEqual(event[key], self.data["agents"]["worker"][key])
        rules = (BASE / "OPERATIONAL_RULES.md").read_bytes()
        expected = hashlib.sha1(b"blob " + str(len(rules)).encode() + b"\0" + rules).hexdigest()
        self.assertEqual(event["rules_revision"], expected)

    def test_failed_and_dry_launches_write_no_event(self):
        self.assertEqual(self.launch(dry=True)[0], 0)
        self.assertFalse((self.root / "events.jsonl").exists())
        self.assertEqual(self.launch(success=False)[0], 1)
        self.assertFalse((self.root / "events.jsonl").exists())

    def test_launch_event_failure_warns_but_launch_succeeds(self):
        with patch.object(fe, "append_event", side_effect=OSError("fixture cannot append")):
            code, out, err = self.launch()
        self.assertEqual(code, 0, out + err)
        self.assertIn("warning:", err)
        self.assertIn("fixture cannot append", err)

    def test_legacy_launch_keeps_null_task_id(self):
        log = runpy.run_path(str(BASE / "bin/agentmail-launch"))["_log_launch_event"]
        log({"id": "worker"}, str(self.root))
        self.assertIsNone(self.events()[0]["task_id"])

    def test_mail_task_id_inference_and_override(self):
        cases = [("task", "parent", "worker", (), "task-1"),
                 ("done", "worker", "parent", (), "task-1"),
                 ("review", "worker", "reviewer", (), "task-1"),
                 ("review", "parent", "reviewer", (), "review-1"),
                 ("task", "parent", "worker", ("--task-id", "explicit"), "explicit"),
                 ("info", "worker", "parent", (), None)]
        for kind, sender, target, flags, expected in cases:
            with self.subTest(kind=kind, sender=sender, flags=flags):
                result = self.cli("mail-send", "--type", kind, "--from", sender, "--to", target,
                                  "--subject", "fixture", "--no-reply", "-m", "body", *flags)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                message = Path(result.stdout.strip().removeprefix("delivered: "))
                self.assertEqual(iac.headers(message.read_text()).get("task_id"), expected)

    def test_mail_legacy_and_multiple_task_entries_remain_valid(self):
        for value, expected in ((None, None), (["one", "two"], None), (["one"], "one")):
            self.data["agents"]["worker"]["task_id"] = value
            self.save()
            result = self.cli("mail-send", "--type", "done", "--from", "worker", "--to", "parent",
                              "--subject", "legacy", "--no-reply", "-m", "body")
            self.assertEqual(result.returncode, 0, result.stderr)
            message = Path(result.stdout.strip().removeprefix("delivered: "))
            self.assertEqual(iac.headers(message.read_text()).get("task_id"), expected)

    def test_review_with_ambiguous_author_never_uses_reviewers_task(self):
        self.data["agents"]["worker"]["task_id"] = ["one", "two"]
        self.save()
        result = self.cli("mail-send", "--type", "review", "--from", "worker", "--to", "reviewer",
                          "--subject", "ambiguous", "--no-reply", "-m", "body")
        self.assertEqual(result.returncode, 0, result.stderr)
        message = Path(result.stdout.strip().removeprefix("delivered: "))
        self.assertNotIn("task_id", iac.headers(message.read_text()))

    def test_help_version_and_unknown_close_flags(self):
        for command in ("fleet-event", "seat-close"):
            self.assertEqual(self.cli(command, "--help").returncode, 0)
            for flag in ("--version", "-v", "-V"):
                result = self.cli(command, flag)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stdout.strip(), "1.0.0")
        result = self.close_cli(fe.Outcome.FAILED, "--typo")
        self.assertEqual(result.returncode, 2)
        self.assertIn("--typo", result.stdout)
        self.assertFalse((self.root / "events.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
