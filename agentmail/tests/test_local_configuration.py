"""Exercise portable fleet helpers with fake executables and isolated local policy.

No terminal, live roster, model service or private site configuration is used.
"""
from pathlib import Path
import json
import os
import runpy
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest

BASE = Path(__file__).resolve().parents[1]


class LocalConfigurationTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("zsh"), "macOS .command wrapper needs zsh")
    def test_fleet_start_preserves_sessions_and_uses_captured_panes(self):
        with tempfile.TemporaryDirectory(prefix="iac fixture ") as directory:
            root = Path(directory).resolve()
            (root / "agentmail/bin").mkdir(parents=True)
            (root / ".agent-mail").mkdir()
            (root / ".agent-mail/roster.json").write_text(json.dumps({"agents": {
                "api-dev": {"project": "api", "role": "worker"}}}))
            log = root / "calls.jsonl"
            fake = """#!/usr/bin/env python3
import json, os, sys
with open(os.environ['FIXTURE_LOG'], 'a') as target:
    target.write(json.dumps([os.path.basename(sys.argv[0]), *sys.argv[1:]]) + '\\n')
if sys.argv[1:2] == ['has-session']:
    sys.exit(1)
if sys.argv[1:2] == ['new-session']:
    print('%11')
if sys.argv[1:2] == ['display-message']:
    print('%22')
"""
            for path in (root / "tmux", root / "agentmail/bin/agentmail-launch"):
                path.write_text(fake)
                path.chmod(0o755)
            env = dict(os.environ, IAC_ROOT=str(root), AGENTMAIL_DIR=str(root / ".agent-mail"),
                       IAC_FLEET_SESSION="fleet", FIXTURE_LOG=str(log),
                       PATH=str(root) + os.pathsep + os.environ["PATH"])
            command = ["zsh", str(BASE / "bin/fleet-start.command")]
            result = subprocess.run([*command, "api-dev"], env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            calls = [json.loads(line) for line in log.read_text().splitlines()]
            self.assertFalse(any("kill-session" in call or "--skip-permissions" in call for call in calls))
            self.assertIn(["tmux", "join-pane", "-s", "%22", "-t", "fleet:seats", "-h"], calls)
            self.assertIn(["tmux", "attach-session", "-t", "fleet:seats"], calls)
            self.assertEqual(sum("--apply" in call for call in calls), 1)
            log.unlink()
            result = subprocess.run([*command, "--typo"], env=env, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(log.exists(), "invalid input must fail before invoking dependencies")

    @unittest.skipUnless(shutil.which("zsh"), "macOS .command wrapper needs zsh")
    def test_codex_supervisor_and_worker_profiles_match_wrapper_dry_run(self):
        launch = runpy.run_path(str(BASE / "bin/agentmail-launch"))["build_command"]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / "agentmail/bin").mkdir(parents=True)
            (root / "agentmail/bin/agentmail-launch").symlink_to(BASE / "bin/agentmail-launch")
            mail = root / ".agent-mail"
            mail.mkdir()
            for role, approval in (("parent", "on-request"), ("worker", "never")):
                seat = {"id": "fixture-main", "role": role, "runtime": "codex-cli",
                        "home": str(root), "model": "APPROVED MODEL", "effort": "medium",
                        "network": True, "add_dirs": [str(root / "extra")]}
                (mail / "roster.json").write_text(json.dumps({"agents": {seat["id"]: seat}}))
                env = dict(os.environ, IAC_ROOT=str(root), IAC_MAIN_SEAT=seat["id"],
                           AGENTMAIL_DIR=str(mail))
                env.pop("AGENTMAIL_SITE", None)
                command = launch(seat, str(mail))
                argv = shlex.split(command)
                actual = argv[argv.index("--") + 1:]
                prompt = (f"You are IAC seat fixture-main, role {role}. Mail root: {mail}. "
                          f"Helpers: {BASE / 'bin'}. "
                          "Read roster.json for your project authority and delegation. "
                          "Product requirements and technical implementation have separate owners. "
                          "Research/attachments are context, not authorization to implement. "
                          "Reply using --in-reply-to with the incoming message ID. "
                          "Use --no-reply for acknowledgements and final responses. ")
                expected = ["codex", "--sandbox", "workspace-write", "--ask-for-approval", approval,
                            "--add-dir", str(mail)]
                if role == "worker":
                    for plugin in ("computer-use@openai-bundled", "unified-computer-use@openai-bundled",
                                   "browser@openai-bundled"):
                        expected += ["-c", f'plugins."{plugin}".enabled=false']
                    prompt += ("Arm your mail watcher (persistent) FIRST, then check your mail and get oriented."
                               " NOTE FOR CODEX: you have no background watcher tool. Do NOT open any"
                               " terminal or app. Read mail with the shell command"
                               f" {BASE / 'bin/mail-read'} fixture-main -d {mail}"
                               " at start and after each step; the overseer prompts you when new mail arrives.")
                else:
                    prompt += "You're my overseer \u2014 check your mail and get oriented."
                expected += ["--add-dir", str(root / "extra"), "-c", 'model_reasoning_effort="medium"',
                             "-c", "sandbox_workspace_write.network_access=true", "--model", "APPROVED MODEL", prompt]
                self.assertEqual(actual, expected)
                result = subprocess.run(["zsh", str(BASE / "bin/overseer-codex.command"),
                                         "--terminal", "print"], env=env, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(command, result.stdout)
                self.assertIn("dry run", result.stdout)

    def test_guard_reads_explicit_policy_and_reports_invalid_policy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            path = root / "policy.json"
            env = dict(os.environ, PYTHONPATH=str(BASE / "lib"), IAC_ROOT=str(root))
            env.pop("IAC_MODEL_POLICY", None)
            code = "import model_guard as m; print(sorted(m.LOCKED_TIER))"
            result = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "[]")
            self.assertIn("WARNING: model_guard: NO SITE MODEL POLICY", result.stderr)
            self.assertIn("zero site model restrictions", result.stderr)
            self.assertIn("IAC_MODEL_POLICY", result.stderr)
            path.write_text(json.dumps({"restricted_models": ["test-restricted"]}))
            env["IAC_MODEL_POLICY"] = str(path)
            self.assertIn("test-restricted", subprocess.check_output([sys.executable, "-c", code], env=env, text=True))
            path.write_text('{"restricted_models": "invalid"}')
            code = "import model_guard as m; m.resolve([m.Candidate('test', 'test-model')])"
            result = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("local policy unavailable", result.stderr)


if __name__ == "__main__":
    unittest.main()
