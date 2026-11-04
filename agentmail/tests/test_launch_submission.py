"""Offline account gates and submission output; no Git, providers or lanes."""
import json
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch


BIN = Path(__file__).resolve().parents[1] / "bin"

# Exercise main/client in a real child process with real queue publication and
# redirected descriptors. Only the Git snapshot and external result producer
# are replaced, so this fixture never starts a lane or touches a Git store.
SUBMIT = """
from pathlib import Path
import runpy, sys
main = runpy.run_path(sys.argv[1])['main']
scope = main.__globals__
mode = sys.argv[2]
def snapshot(*args):
    if mode == 'unexpected':
        raise RuntimeError('fixture snapshot failed')
    return 'a' * 40, b''
scope['snapshot'] = snapshot
publish = scope['write_json']
def write_json(path, value, **kwargs):
    publish(path, value, **kwargs)
    if path.parent.name == 'jobs' and mode == 'success':
        publish(path.parent.parent / 'results' / path.name,
                {'id': value['id'], 'status': 'passed', 'exit_code': 0})
scope['write_json'] = write_json
raise SystemExit(main(sys.argv[3:]))
"""


class LaunchSubmissionTests(unittest.TestCase):
    def test_gate_uses_roster_codex_home_account(self):
        gate = runpy.run_path(str(BIN / "agentmail-launch"))["_launch_gate_problems"]
        seat = {"id": "fixture", "role": "child", "runtime": "codex-cli",
                "codex_home": "~/.codex-ramesh"}
        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory) / "cache.json"
            cache.write_text(json.dumps({"checked_at": time.time(),
                                         "weekly_pct_left": {"codex": 0, "codex-ramesh": 70}}))
            with patch.dict(gate.__globals__, HEADROOM_CACHE=str(cache)):
                for home in ("~/.codex-ramesh", "/fixture/.codex-ramesh/"):
                    self.assertEqual(gate([dict(seat, codex_home=home)], ""), [])
                expected = ("fixture: codex weekly headroom is 0% (< 20%); route to the other "
                            "provider or pass --override-headroom with the operator's word")
                self.assertEqual(gate([dict(seat, codex_home="~/.codex")], ""), [expected])
                self.assertEqual(gate([dict(seat, codex_home=None)], ""), [expected])
                cache.write_text(json.dumps({"checked_at": time.time(),
                                             "weekly_pct_left": {"codex": 70, "codex-ramesh": 0}}))
                self.assertEqual(gate([seat], ""), [expected.replace("codex weekly", "codex-ramesh weekly")])
                self.assertEqual(gate([seat], "operator instruction"), [])

    def test_run_emits_queued_or_error_with_pipe_or_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            repo.mkdir()
            (repo / "example.test.cjs").write_text("// fixture\n")
            for output in ("pipe", "file", "closed_pipe"):
                for mode in ("success", "validation", "unexpected", "wait_timeout"):
                    with self.subTest(output=output, mode=mode):
                        queue = root / (output + mode)
                        command = [sys.executable, "-c", SUBMIT, str(BIN / "testlane"), mode,
                                   "run", "--queue", str(queue), "--repo-dir", str(repo),
                                   "--base", "a" * 40, "--wait-timeout", "0.01", "--",
                                   "node", "--test", "example.test.cjs"]
                        if mode == "validation":
                            command[-1] = "missing.test.cjs"
                        if output == "closed_pipe":
                            process = subprocess.Popen(command, stdout=subprocess.PIPE,
                                                       stderr=subprocess.PIPE, text=True)
                            process.stdout.close()
                            stderr = process.stderr.read()
                            process.stderr.close()
                            code = process.wait(timeout=5)
                            stdout = ""
                        else:
                            with (root / "stdout.txt").open("w+") as stream:
                                result = subprocess.run(command, stdout=subprocess.PIPE if output == "pipe" else stream,
                                                        stderr=subprocess.PIPE, text=True, timeout=5)
                                stream.seek(0)
                                stdout = result.stdout if output == "pipe" else stream.read()
                            code, stderr = result.returncode, result.stderr
                        jobs = list((queue / "jobs").glob("*.json"))
                        self.assertEqual(len(jobs), 0 if mode in ("validation", "unexpected") else 1)
                        if mode == "success" and output != "closed_pipe":
                            self.assertEqual(code, 0, stdout + stderr)
                            self.assertIn("queued: " + jobs[0].stem + "\n", stdout)
                            self.assertIn('status: "passed"', stdout)
                        else:
                            self.assertEqual(code, 2, stdout + stderr)
                            self.assertIn("Error: ", stderr)
                            if output != "closed_pipe":
                                self.assertIn("Error: ", stdout)
                        self.assertNotIn("Traceback", stdout + stderr)


if __name__ == "__main__":
    unittest.main()
