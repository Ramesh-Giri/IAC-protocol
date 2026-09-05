"""Offline integration tests. Only temporary spools and dummy Python CLIs."""
import concurrent.futures
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


class Protocol(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="iac-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "mail"
        self.root.mkdir()
        self.env = dict(os.environ)
        for key in ("AGENTMAIL_SEAT", "AGENTMAIL_SITE", "AGENTMAIL_DIR"):
            self.env.pop(key, None)
        self.env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
                        GIT_AUTHOR_NAME="IAC Test", GIT_AUTHOR_EMAIL="test@example.invalid",
                        GIT_COMMITTER_NAME="IAC Test", GIT_COMMITTER_EMAIL="test@example.invalid")
        self.roster = {"agents": {s: {"home": str(self.root), "role": "child"} for s in ("a", "b", "c")},
                       "projects": {"demo": {}}}
        (self.root / "roster.json").write_text(json.dumps(self.roster))
        for seat in self.roster["agents"]:
            for box in ("new", "cur", "tmp"):
                (self.root / seat / box).mkdir(parents=True)
                if box != "tmp":
                    (self.root / seat / box / ".keep").touch()
        self.clean_env = patch.dict(os.environ, self.env, clear=True)
        self.clean_env.start()
        self.addCleanup(self.clean_env.stop)

    def cli(self, name, *args, root=None):
        return subprocess.run([sys.executable, str(BASE / "bin" / name), "-d", str(root or self.root), *args],
                              env=self.env, text=True, capture_output=True, timeout=15)

    def send(self, **kw):
        return iac.deliver(self.root, "a", "b", "same subject", "body", **kw)

    def bridge(self, code="print('answer')", *flags, seat="b"):
        return self.cli("mail-bridge", seat, "--once", *flags, "--", sys.executable, "-c", code)

    def files(self, seat, box="new"):
        return list((self.root / seat / box).glob("*.md"))

    def test_concurrent_sends_never_overwrite_read_or_unread(self):
        first = self.send()
        iac.acknowledge(self.root, first)
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            paths = list(pool.map(lambda _: self.send(), range(32)))
        self.assertEqual(len(set(paths)), 32)
        self.assertEqual(len(self.files("b")), 32)
        self.assertEqual(len(self.files("b", "cur")), 1)
        self.assertEqual(len({iac.headers(p.read_text())["id"] for p in paths}), 32)

    def test_stable_delivery_is_idempotent_even_after_read(self):
        mid = str(uuid.uuid4())
        p = self.send(message_id=mid)
        iac.acknowledge(self.root, p)
        p2 = self.send(message_id=mid)
        self.assertEqual(p2.parent.name, "cur")
        with self.assertRaises(ValueError):
            iac.deliver(self.root, "a", "b", "changed", "body", message_id=mid)

    def test_invalid_identity_and_header_injection_rejected(self):
        for frm, to, subject in [("absent", "b", "x"), ("a", "../escape", "x"),
                                 ("a", "b", "x\nto: c")]:
            with self.assertRaises(ValueError):
                iac.deliver(self.root, frm, to, subject, "body")
        with self.assertRaises(ValueError):
            self.send(metadata={"to": "c"})
        self.assertFalse(self.files("b"))

    def test_session_sender_binding(self):
        with patch.dict(os.environ, AGENTMAIL_SEAT="c"):
            with self.assertRaises(ValueError):
                self.send()

    def test_one_bound_main_can_send_to_two_explicit_roots_without_mirroring(self):
        team = Path(self.temp.name) / "team-mail"
        subprocess.run(["bash", str(BASE / "bin" / "agentmail-init"),
                        "a", "remote", "-d", str(team)],
                       env=self.env, check=True, capture_output=True, timeout=10)
        self.env.update(AGENTMAIL_SEAT="a", AGENTMAIL_DIR=str(self.root))
        local = self.cli("mail-send", "--from", "a", "--to", "b",
                         "--subject", "Local only", "-m", "Private project discussion")
        shared = self.cli("mail-send", "--from", "a", "--to", "remote",
                          "--subject", "Team handoff", "-m", "Approved summary", root=team)
        self.assertEqual(local.returncode, 0, local.stderr)
        self.assertEqual(shared.returncode, 0, shared.stderr)
        local_files = self.files("b")
        team_files = list((team / "remote" / "new").glob("*.md"))
        self.assertEqual(len(local_files), 1)
        self.assertEqual(len(team_files), 1)
        self.assertIn("Private project discussion", local_files[0].read_text())
        self.assertNotIn("Private project discussion", team_files[0].read_text())
        self.assertIn("Approved summary", team_files[0].read_text())
        self.assertFalse((team / "b").exists())
        self.assertFalse((self.root / "remote").exists())

    def test_symlink_maildir_is_rejected(self):
        (self.root / "b" / "tmp").rmdir()
        (self.root / "b" / "tmp").symlink_to(self.root / "a" / "tmp")
        with self.assertRaises(ValueError):
            self.send()

    def test_header_quoting_and_legacy_parser(self):
        p = iac.deliver(self.root, "a", "b", 'quote: "value" # detail', "x")
        self.assertEqual(iac.headers(p.read_text())["subject"], 'quote: "value" # detail')
        self.assertEqual(iac.headers("---\nfrom: a\nsubject: legacy: yes\n---\nbody")["subject"], "legacy: yes")
        with self.assertRaises(ValueError):
            iac.headers("---\nfrom: a\nfrom: c\n---\n")

    def test_handoff_body_file_and_pinned_reference(self):
        body = Path(self.temp.name) / "research.md"
        body.write_text("# Research\nUse `literal` and $(not-a-command).\n")
        ref = "shared-research@" + "a" * 40 + ":design.md"
        result = self.cli("mail-send", "--from", "a", "--to", "b", "--subject", "research",
                          "--type", "handoff", "--project", "demo", "--intent", "research",
                          "--authority", "technical", "--ref", ref, "--body-file", str(body))
        self.assertEqual(result.returncode, 0, result.stderr)
        text = self.files("b")[0].read_text()
        h = iac.headers(text)
        self.assertEqual(h["intent"], "research")
        self.assertEqual(json.loads(h["references"]), [ref])
        self.assertTrue(iac.expects_reply(h))
        self.assertIn(body.read_text(), text)

    def test_short_commit_and_unknown_project_rejected(self):
        for flags in [("--ref", "repo@abc123:file.md"), ("--project", "absent"), ("--intent", "research")]:
            result = self.cli("mail-send", "--from", "a", "--to", "b", "--subject", "x", "-m", "x", *flags)
            self.assertNotEqual(result.returncode, 0)

    def test_check_does_not_consume_read_does(self):
        self.send()
        self.assertEqual(self.cli("mail-check", "b").returncode, 0)
        self.assertEqual(len(self.files("b")), 1)
        self.assertEqual(self.cli("mail-read", "b").returncode, 0)
        self.assertFalse(self.files("b"))
        self.assertEqual(len(self.files("b", "cur")), 1)

    def test_failed_and_partial_bridge_outputs_remain_unread(self):
        self.send(kind="question")
        for code in ("raise SystemExit(1)", "print('partial'); raise SystemExit(2)", "pass"):
            result = self.bridge(code)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertEqual(len(self.files("b")), 1)
            self.assertFalse(self.files("a"))

    def test_retry_cap_and_explicit_recovery(self):
        self.send(kind="question")
        self.assertEqual(self.bridge("raise SystemExit(1)", "--max-attempts", "1").returncode, 1)
        self.assertEqual(self.bridge("print('okay')", "--max-attempts", "1").returncode, 1)
        result = self.bridge("print('okay')", "--max-attempts", "1", "--retry-failed")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(self.files("a")), 1)
        self.assertFalse(self.files("b"))

    def test_bridge_timeout_keeps_request(self):
        self.send(kind="task")
        result = self.bridge("import time; time.sleep(10)", "--timeout", "0.1")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(len(self.files("b")), 1)
        self.assertFalse(self.files("a"))

    def test_notifications_never_invoke_a_model(self):
        self.send()
        result = self.bridge("raise SystemExit(99)")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.files("a"))
        self.assertEqual(len(self.files("b", "cur")), 1)

    def test_reply_is_correlated_and_does_not_pingpong(self):
        request = self.send(kind="review")
        mid = iac.headers(request.read_text())["id"]
        result = self.bridge()
        self.assertEqual(result.returncode, 0, result.stderr)
        reply = iac.headers(self.files("a")[0].read_text())
        self.assertEqual(reply["in_reply_to"], mid)
        self.assertEqual(reply["type"], "verdict")
        self.assertFalse(iac.expects_reply(reply))
        result = self.bridge("raise SystemExit(99)", seat="a")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.files("b"))

    def test_cached_reply_recovery_does_not_reinvoke_cli(self):
        request = self.send(kind="question")
        mid = iac.headers(request.read_text())["id"]
        state = self.root / "b/tmp/bridge-state" / (hashlib.sha256(mid.encode()).hexdigest() + ".json")
        iac.atomic_write(state, json.dumps({"attempts": 1, "reply": "saved result\n"}))
        # Simulate crash after delivery, before acknowledging the request.
        iac.deliver(self.root, "b", "a", "RE: same subject", "saved result\n", kind="answer",
                    metadata={"in_reply_to": mid, "expects_reply": "false", "ack": "none"},
                    message_id=str(uuid.uuid5(uuid.NAMESPACE_URL, "b:" + mid)))
        result = self.bridge("raise SystemExit(99)")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(self.files("a")), 1)
        self.assertFalse(self.files("b"))

    def test_duplicate_session_and_consumers_refused(self):
        with iac.lock(self.root, "session-b"):
            result = self.cli("agentmail-run", "--seat", "b", "--", sys.executable, "-c", "print('STARTED')")
            self.assertEqual(result.returncode, 1)
            self.assertNotIn("STARTED", result.stdout)
            self.assertEqual(self.bridge().returncode, 1)
        with iac.lock(self.root, "consume-b"):
            self.assertEqual(self.cli("mail-read", "b").returncode, 1)

    def test_session_wrapper_binds_identity(self):
        result = self.cli("agentmail-run", "--seat", "b", "--", sys.executable, "-c",
                          "import os; print(os.environ['AGENTMAIL_SEAT']); print(os.environ['AGENTMAIL_DIR'])")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), ["b", str(self.root.resolve())])

    def test_local_site_never_inferred_from_roster_owner(self):
        data = {"sites": {"alice": {}, "bob": {}}, "roster_owner": "a", "agents": {"a": {"site": "alice"}}}
        with patch("iac.socket.gethostname", return_value="unrecognized"):
            self.assertIsNone(iac.local_site(self.root, data))
            (self.root / "local.json").write_text('{"site":"bob"}')
            self.assertEqual(iac.local_site(self.root, data), "bob")
            self.assertEqual(iac.local_site(self.root, data, "alice"), "alice")

    def test_foreign_consumers_refused_but_inspection_allowed(self):
        self.roster["sites"] = {"alice": {}, "bob": {}}
        self.roster["agents"]["b"]["site"] = "bob"
        (self.root / "roster.json").write_text(json.dumps(self.roster))
        (self.root / "local.json").write_text('{"site":"alice"}')
        self.send(kind="question")
        self.assertEqual(self.cli("mail-check", "b").returncode, 0)
        self.assertEqual(self.cli("mail-read", "b").returncode, 1)
        self.assertEqual(self.bridge().returncode, 1)
        self.assertEqual(self.cli("mail-read", "b", "--site", "bob").returncode, 0)

    def test_bridge_rebinds_inherited_supervisor_identity(self):
        self.send(kind="question")
        self.env["AGENTMAIL_SEAT"] = "a"
        result = self.bridge()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(iac.headers(self.files("a")[0].read_text())["from"], "b")

    def test_watcher_announces_existing_and_new_mail_without_consuming(self):
        self.send()
        calls = []
        def tick(_):
            calls.append(1)
            if len(calls) == 1:
                self.send()
            else:
                raise KeyboardInterrupt()
        out = io.StringIO()
        with patch.object(sys, "argv", ["mail-watch", "b", "-d", str(self.root)]), \
             patch("iac.time.sleep", side_effect=tick), patch("sys.stdout", out):
            with self.assertRaises(KeyboardInterrupt):
                iac.watch_main()
        self.assertEqual(out.getvalue().count("MAIL b "), 2)
        self.assertEqual(len(self.files("b")), 2)

    def test_timeout_terminates_descendant_command_group(self):
        marker = Path(self.temp.name) / "child-survived"
        child = "import time; from pathlib import Path; time.sleep(1); Path(" + repr(str(marker)) + ").touch()"
        parent = "import subprocess,sys,time; subprocess.Popen([sys.executable,'-c'," + repr(child) + "]); print('ready',flush=True); time.sleep(10)"
        with self.assertRaises(subprocess.TimeoutExpired):
            iac.run_bounded([sys.executable, "-c", parent], timeout=0.15, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(1.1)
        self.assertFalse(marker.exists(), "timed-out command left a running descendant")

    def test_snapshot_understands_new_frontmatter_and_reply_intent(self):
        self.send(kind="handoff", metadata={"expects_reply": "true", "intent": "research", "project": "demo"})
        module = runpy.run_path(str(BASE / "bin/network-snapshot"))
        rows = module["scan_mail"](str(self.root), list(self.roster["agents"]))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["from"], "a")
        self.assertEqual(rows[0]["intent"], "research")
        self.assertTrue(rows[0]["expects_reply"])
        self.assertIsNotNone(rows[0]["id"])

    def test_snapshot_and_dashboard_render_temporary_network(self):
        self.send(kind="handoff", metadata={"expects_reply": "true", "thread": "research", "intent": "research"})
        result = subprocess.run([sys.executable, str(BASE / "bin/network-snapshot"), "--mail-root", str(self.root)],
                                capture_output=True, text=True, env=self.env, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        doc = json.loads(result.stdout)
        self.assertNotIn("fatal_error", doc["meta"], doc["meta"])
        self.assertEqual(doc["meta"]["counts"]["messages_total"], 1)
        self.assertTrue(doc["mail_flow"][0]["expects_reply"])
        saved = Path(self.temp.name) / "snapshot.json"
        saved.write_text(result.stdout)
        output = Path(self.temp.name) / "dashboard.html"
        result = subprocess.run([sys.executable, str(BASE / "bin/network-dashboard"), "--json", str(saved), "-o", str(output), "--quiet"],
                                capture_output=True, text=True, env=self.env, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("<title>", output.read_text())
        self.assertIn("same subject", output.read_text())

    def test_launcher_filters_sites_and_uses_local_home(self):
        self.roster["sites"] = {"alice": {}, "bob": {}}
        self.roster["roster_owner"] = "a"
        for sid in self.roster["agents"]:
            self.roster["agents"][sid].update(site="alice", runtime="claude-code")
        self.roster["agents"]["b"].update(site="bob", runtime="codex-cli", home="/nonexistent")
        (self.root / "roster.json").write_text(json.dumps(self.roster))
        (self.root / "local.json").write_text(json.dumps({"site": "bob", "homes": {"b": str(self.root)}}))
        result = self.cli("agentmail-launch", "--all", "--terminal", "print")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--seat b", result.stdout)
        self.assertIn("--site bob", result.stdout)
        self.assertNotIn("--seat a", result.stdout)
        self.assertNotIn("/nonexistent", result.stdout)
        self.assertEqual(self.cli("agentmail-launch", "--seat", "a").returncode, 2)

    def test_launcher_codex_and_custom_commands_are_explicit_and_quoted(self):
        launch = runpy.run_path(str(BASE / "bin/agentmail-launch"))["build_command"]
        seat = {"id": "a", "role": "parent", "runtime": "codex-cli", "home": "/path with spaces", "model": "model-name"}
        command = launch(seat, str(self.root))
        for token in ("agentmail-run", "--seat a", "--sandbox workspace-write", "--add-dir", "--model model-name", "IAC seat a"):
            self.assertIn(token, command)
        self.assertNotIn("dangerously", command)
        with self.assertRaises(ValueError):
            launch(dict(seat, _skip_permissions=True), str(self.root))
        custom = dict(seat, role="child", runtime="custom", command=["dummy-cli", "--prompt", "{prompt}"])
        self.assertIn("dummy-cli", launch(custom, str(self.root)))

    def git(self, root, *args):
        result = subprocess.run(["git", "-C", str(root), *args], env=self.env, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def test_sync_rejects_nested_product_repo_before_mutation(self):
        parent = Path(self.temp.name)
        self.git(parent, "init", "-q")
        (parent / "product.py").write_text("unrelated")
        before = self.git(parent, "status", "--porcelain")
        result = self.cli("mail-sync", "--once")
        self.assertEqual(result.returncode, 1)
        self.assertIn("dedicated mail repository", result.stderr)
        self.assertEqual(self.git(parent, "status", "--porcelain"), before)
        self.assertFalse((self.root / ".gitignore").exists())

    def test_offline_federation_roundtrip_and_local_state_exclusion(self):
        remote = Path(self.temp.name) / "remote.git"
        remote.mkdir()
        self.git(remote, "init", "--bare", "-q")
        self.git(self.root, "init", "-q")
        self.git(self.root, "remote", "add", "origin", str(remote))
        (self.root / "local.json").write_text('{"site":"local-only"}')
        (self.root / "b/tmp/retry.json").write_text("private")
        self.send(kind="question")
        result = self.cli("mail-sync", "--once")
        self.assertEqual(result.returncode, 0, result.stderr)
        tracked = self.git(self.root, "ls-files")
        self.assertNotIn("local.json", tracked)
        self.assertNotIn("retry.json", tracked)
        peer = Path(self.temp.name) / "peer"
        self.git(Path(self.temp.name), "clone", "-q", str(remote), str(peer))
        result = self.cli("mail-read", "b", root=peer)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.cli("mail-sync", "--once", root=peer).returncode, 0)
        self.assertEqual(self.cli("mail-sync", "--once").returncode, 0)
        self.assertFalse(self.files("b"))
        self.assertEqual(len(self.files("b", "cur")), 1)

    def test_sync_rejects_product_payload(self):
        self.git(self.root, "init", "-q")
        self.git(self.root, "remote", "add", "origin", str(Path(self.temp.name) / "unused"))
        (self.root / "product.py").write_text("do not commit")
        result = self.cli("mail-sync", "--once")
        self.assertEqual(result.returncode, 1)
        self.assertIn("not a mail-only payload", result.stderr)
        self.assertEqual(self.git(self.root, "diff", "--cached", "--name-only"), "")

    def test_sync_refuses_unresolved_git_operation_and_tracked_local_state(self):
        self.git(self.root, "init", "-q")
        self.git(self.root, "remote", "add", "origin", str(Path(self.temp.name) / "unused"))
        (self.root / ".git/rebase-merge").mkdir()
        result = self.cli("mail-sync", "--once")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Git operation unresolved", result.stderr)
        self.assertEqual(self.git(self.root, "diff", "--cached", "--name-only"), "")
        (self.root / ".git/rebase-merge").rmdir()
        (self.root / "local.json").write_text("{}")
        self.git(self.root, "add", "local.json")
        result = self.cli("mail-sync", "--once")
        self.assertEqual(result.returncode, 1)
        self.assertIn("machine-local state is tracked", result.stderr)


if __name__ == "__main__":
    unittest.main()
