"""Exercise testlane's CLI, command boundary and crash recovery using temporary repos.

TestlaneTest uses only fake installed Flutter/Node commands and stdlib unittest.
It creates disposable git histories, queues, lane workers and logs; no real SDK,
product checkout, network, live seat or treehouse pool is used or modified.
"""
import base64
from importlib.machinery import SourceFileLoader
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
import uuid
from unittest.mock import patch

BIN = Path(__file__).resolve().parents[1] / "bin" / "testlane"
tl = SourceFileLoader("testlane", str(BIN)).load_module()

FAKE = r'''#!/usr/bin/env python3
import hashlib,json,os,sys,time
from pathlib import Path
tool=Path(sys.argv[0]).name
cwd=Path.cwd()
root=cwd.parent if cwd.name=='functions' else cwd
trace=Path(__file__).resolve().parent.parent/'trace.jsonl'
def record(phase):
 with trace.open('a') as f:
  f.write(json.dumps({'tool':tool,'argv':sys.argv[1:],'cwd':str(cwd),
                      'phase':phase,'time':time.time()})+'\n')
record('start')
if tool=='flutter' and sys.argv[1:]==['pub','get']:
 delay=Path(__file__).resolve().parent.parent/'warm-delay'
 if delay.exists():
  time.sleep(float(delay.read_text()))
 (cwd/'.dart_tool').mkdir(exist_ok=True)
elif tool=='npm' and sys.argv[1:]==['ci']:
 compiler=cwd/'node_modules/typescript/bin/tsc'
 compiler.parent.mkdir(parents=True,exist_ok=True)
 compiler.write_text('local compiler fixture\n')
else:
 behavior=json.loads((root/'behavior.json').read_text())
 if tool=='node' and 'node_modules/typescript/bin/tsc' in sys.argv[1]:
  if sys.argv[-1]=='tsconfig.test.json':
   source=cwd/'test/generated.test.ts'
   output=cwd/'.test-build/test/generated.test.js'
   if source.exists():
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(source.read_text())
   time.sleep(behavior.get('compile_sleep',0))
  record('end')
  sys.exit(behavior.get('compile_exit',0))
 if behavior.get('expect_compiled'):
  for name in sys.argv[2:]:
   assert (cwd/name).read_text()==behavior['expect_compiled']
  print('compiled target verified',flush=True)
 if behavior.get('require_patch'):
  assert (root/'new.txt').read_text()=='untracked snapshot\n'
  assert (root/'new.bin').read_bytes()==bytes(range(256))
  assert (root/'tracked.bin').read_bytes()==b'\x00changed\xff'
  print('snapshot verified',flush=True)
 if behavior.get('junk'):
  for name in ('node_modules','.dart_tool','build','functions/node_modules',
               'functions/lib-cache','.test-build'):
   p=root/name
   p.mkdir(parents=True,exist_ok=True)
   (p/'keep').write_text('warm')
  (root/'junk.txt').write_text('remove')
  (root/'.trash').mkdir(exist_ok=True)
  (root/'.trash/ignored.txt').write_text('remove ignored output')
 print('job command:',json.dumps(sys.argv[1:]),flush=True)
 time.sleep(behavior.get('sleep',0))
 record('end')
 sys.exit(behavior.get('exit',0))
record('end')
'''


class TestlaneTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="iac-testlane-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.queue = self.root / "queue"
        self.tools = self.root / "bin"
        self.tools.mkdir()
        (self.tools / "fake-tool").write_text(FAKE)
        (self.tools / "fake-tool").chmod(0o755)
        for tool in ("node", "npm", "npx", "flutter"):
            (self.tools / tool).symlink_to("fake-tool")
        self.env = dict(os.environ, PATH=str(self.tools) + os.pathsep + os.environ["PATH"],
                        GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1",
                        GIT_AUTHOR_NAME="Testlane Test", GIT_AUTHOR_EMAIL="test@example.invalid",
                        GIT_COMMITTER_NAME="Testlane Test", GIT_COMMITTER_EMAIL="test@example.invalid")
        self.env_patch = patch.dict(os.environ, self.env, clear=True)
        self.env_patch.start()
        self.addCleanup(self.env_patch.stop)
        files = {"behavior.json": "{}", "tracked.bin": b"\x00original\xff",
                 "pubspec.yaml": "name: fixture\n", "pubspec.lock": "fixture lock\n",
                 "functions/package.json": '{"name":"fixture","version":"1.0.0"}',
                 "functions/package-lock.json": '{"lockfileVersion":3}',
                 "functions/tsconfig.json": "{}", "functions/tsconfig.test.json": "{}",
                 "functions/test/generated.test.ts": "compiled fixture base\n",
                 "tool/analyzer_gate.py": "print('gate')\n",
                 "test/example_test.dart": "// fixture\n",
                 "functions/test/example.test.cjs": "// fixture\n",
                 ".gitignore": "node_modules/\n.dart_tool/\nbuild/\nfunctions/lib*\n.test-build/\n.trash/\n"}
        for name, data in files.items():
            p = self.repo / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data if isinstance(data, bytes) else data.encode())
        self.git("init", "-q")
        self.git("add", "--all")
        self.git("commit", "-qm", "fixture base")
        self.base = self.git("rev-parse", "HEAD").strip()
        self.runners = []
        self.addCleanup(self.stop_runners)

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.repo), *args], env=self.env, text=True)

    def cli(self, *args, timeout=20):
        return subprocess.run([sys.executable, str(BIN), *map(str, args)], env=self.env,
                              capture_output=True, text=True, timeout=timeout)

    def wait_for(self, predicate, timeout=45):
        until = time.monotonic() + timeout
        while time.monotonic() < until:
            value = predicate()
            if value:
                return value
            time.sleep(0.04)
        logs = "\n".join(p.read_text() for p in self.root.glob("runner*.log"))
        self.fail("fixture timed out\n" + logs)

    def events(self):
        p = self.queue / "events.log"
        return [json.loads(s) for s in p.read_text().splitlines()] if p.exists() else []

    def trace(self):
        p = self.root / "trace.jsonl"
        return [json.loads(s) for s in p.read_text().splitlines()] if p.exists() else []

    def start(self, lanes=1, ready=True):
        before = len([e for e in self.events() if e["event"] == "lane_ready"])
        log = (self.root / f"runner{len(self.runners)}.log").open("w")
        p = subprocess.Popen([sys.executable, str(BIN), "runner", "--repo", str(self.repo),
                              "--queue", str(self.queue), "--lanes", str(lanes)],
                             env=self.env, stdout=log, stderr=log)
        log.close()
        self.runners.append(p)
        if ready:
            self.wait_for(lambda: len([e for e in self.events() if e["event"] == "lane_ready"]) >= before + lanes)
        return p

    def stop_runners(self):
        for p in reversed(self.runners):
            if p.poll() is None:
                p.terminate()
                try:
                    p.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    p.kill()
                    p.wait(timeout=3)

    def behavior(self, **kwargs):
        (self.repo / "behavior.json").write_text(json.dumps(kwargs))

    def job(self, argv=None, timeout=5):
        tl.queue_dirs(self.queue)
        base, data = tl.snapshot(self.repo, self.base, self.queue / "tmp")
        return {"id": uuid.uuid4().hex, "base": base,
                "patch": base64.b64encode(data).decode(), "timeout": timeout, "attempt": 0,
                "argv": argv or ["node", "--test", "functions/test/example.test.cjs"], "cwd": "."}

    def submit(self, job):
        tl.write_json(self.queue / "jobs" / f"{job['id']}.json", job)
        return job["id"]

    def result(self, job_id):
        p = self.queue / "results" / f"{job_id}.json"
        self.wait_for(p.exists)
        return json.loads(p.read_text())

    def test_cli_empty_status_version_and_unknown_flag(self):
        result = self.cli("status", "--queue", self.queue)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("queued: 0", result.stdout)
        self.assertIn('runner: "not started"', result.stdout)
        for flag in ("-v", "-V", "--version"):
            self.assertEqual(self.cli(flag).stdout.strip(), tl.VERSION)
        bad = self.cli("status", "--queue", self.queue, "--lanez", "2")
        self.assertEqual(bad.returncode, 2)
        self.assertIn("--lanez", bad.stdout)
        self.assertIn("--queue", bad.stdout)
        self.assertNotIn("Traceback", bad.stdout + bad.stderr)

    def test_allowlist_accepts_only_explicit_repo_paths(self):
        accepted = [(["flutter", "test", "--no-pub", "test/example_test.dart"], "."),
                    (["flutter", "test", "--no-pub", "--concurrency", "1", "test"], "."),
                    (["flutter", "analyze", "test/example_test.dart"], "."),
                    (["python3", "tool/analyzer_gate.py"], "."),
                    (["npm", "test"], "functions"), (["npm", "run", "build"], "functions"),
                    (["npx", "tsc", "-p", "tsconfig.json"], "functions"),
                    (["node", "--test", "functions/test/example.test.cjs"], ".")]
        for argv, cwd in accepted:
            with self.subTest(argv=argv):
                tl.validate_command(argv, cwd, self.repo)

    def test_allowlist_rejects_shell_flags_network_and_escapes(self):
        rejected = [("node --test file.js", "."), (["sh", "-c", "true"], "."),
                    (["/bin/node", "--test", "functions/test/example.test.cjs"], "."),
                    (["flutter", "test", "test/example_test.dart"], "."),
                    (["flutter", "test", "--no-pub"], "."),
                    (["flutter", "test", "--no-pub", "--concurrency=4", "test"], "."),
                    (["flutter", "test", "--no-pub", "--packages=/tmp/evil", "test"], "."),
                    (["flutter", "build", "apk"], "."), (["flutter", "analyze"], "."),
                    (["npm", "install"], "functions"), (["npm", "test", "--", "anything"], "functions"),
                    (["npm", "test"], "."), (["npx", "--yes", "tsc"], "functions"),
                    (["npx", "tsc", "-p", "../../outside.json"], "functions"),
                    (["node", "--test", "/tmp/external.js"], "."),
                    (["node", "--test", "../external.js"], "."),
                    (["node", "--test", "--import=external.js"], "."),
                    (["node", "--test", "functions/test/example.test.cjs;touch evil"], "."),
                    (["python3", "-c", "print(1)"], "."), (["npm", "test"], "../functions")]
        for argv, cwd in rejected:
            with self.subTest(argv=argv, cwd=cwd), self.assertRaises(tl.Error):
                tl.validate_command(argv, cwd, self.repo)
        (self.repo / "external.js").symlink_to(self.root / "outside.js")
        with self.assertRaises(tl.Error):
            tl.validate_command(["node", "--test", "external.js"], ".", self.repo)

    def test_binary_untracked_patch_and_clean_reset_without_seat_writes(self):
        self.start()
        index = (self.repo / ".git/index").read_bytes()
        objects = sorted(str(p) for p in (self.repo / ".git/objects").rglob("*"))
        (self.repo / "new.txt").write_text("untracked snapshot\n")
        (self.repo / "new.bin").write_bytes(bytes(range(256)))
        (self.repo / "tracked.bin").write_bytes(b"\x00changed\xff")
        self.behavior(require_patch=True, junk=True)
        result = self.result(self.submit(self.job()))
        self.assertEqual(result["exit_code"], 0, result)
        self.assertIn("snapshot verified", (self.queue / result["log_path"]).read_text())
        self.assertEqual((self.repo / ".git/index").read_bytes(), index)
        self.assertEqual(sorted(str(p) for p in (self.repo / ".git/objects").rglob("*")), objects)
        lane = self.queue / "lanes/0"
        self.assertEqual((lane / "tracked.bin").read_bytes(), b"\x00original\xff")
        for name in ("new.txt", "new.bin", "junk.txt", ".trash"):
            self.assertFalse((lane / name).exists(), name)
        for name in ("node_modules", ".dart_tool", "build", "functions/node_modules",
                     "functions/lib-cache", ".test-build"):
            self.assertEqual((lane / name / "keep").read_text(), "warm")
        clean = subprocess.check_output(["git", "-C", str(lane), "status", "--porcelain"], text=True)
        self.assertEqual(clean, "")

    def test_manifest_hash_reinstalls_changed_group_only(self):
        self.start()
        def installs(tool):
            return len([e for e in self.trace() if e["tool"] == tool and e["phase"] == "start"
                        and (e["argv"][:1] == ["ci"] or e["argv"] == ["pub", "get"])])
        self.assertEqual((installs("npm"), installs("flutter")), (1, 1))
        self.assertEqual(self.result(self.submit(self.job()))["exit_code"], 0)
        self.assertEqual((installs("npm"), installs("flutter")), (1, 1))
        (self.repo / "functions/package-lock.json").write_text('{"lockfileVersion":3,"changed":true}')
        for _ in range(2):
            self.assertEqual(self.result(self.submit(self.job()))["exit_code"], 0)
        self.assertEqual((installs("npm"), installs("flutter")), (2, 1))
        (self.repo / "pubspec.yaml").write_text("name: changed_fixture\n")
        self.assertEqual(self.result(self.submit(self.job()))["exit_code"], 0)
        self.assertEqual((installs("npm"), installs("flutter")), (2, 2))

    def test_concurrent_jobs_never_share_a_lane(self):
        self.start(lanes=2)
        self.behavior(sleep=0.15)
        ids = [self.submit(self.job()) for _ in range(5)]
        results = [self.result(job_id) for job_id in ids]
        self.assertEqual({r["exit_code"] for r in results}, {0})
        self.assertEqual({r["lane"] for r in results}, {0, 1})
        active = set()
        for e in self.trace():
            if e["tool"] != "node":
                continue
            if e["phase"] == "start":
                self.assertNotIn(e["cwd"], active)
                active.add(e["cwd"])
            else:
                active.remove(e["cwd"])
        self.assertFalse(active)

    def test_dead_job_requeued_once_and_second_interruption_is_terminal(self):
        job = self.job()
        job["_lane"] = 0
        tl.write_json(self.queue / "running" / f"{job['id']}.json", job)
        self.start()
        result = self.result(job["id"])
        self.assertEqual((result["exit_code"], result["attempt"]), (0, 1))
        self.assertEqual(len([e for e in self.events() if e["event"] == "requeued"]), 1)
        again = self.job()
        again.update(attempt=1, _lane=0)
        tl.write_json(self.queue / "running" / f"{again['id']}.json", again)
        self.assertEqual(self.result(again["id"])["exit_code"], 125)

    def test_runner_crash_does_not_release_live_worker_lane(self):
        p = self.start()
        self.behavior(sleep=0.7)
        first = self.submit(self.job())
        self.wait_for(lambda: any(e["tool"] == "node" and e["phase"] == "start" for e in self.trace()))
        p.kill()
        p.wait(timeout=3)
        self.behavior(sleep=0)
        second = self.submit(self.job())
        self.start(ready=False)
        self.assertEqual(self.result(first)["exit_code"], 0)
        self.assertEqual(self.result(second)["exit_code"], 0)
        records = [e for e in self.trace() if e["tool"] == "node"]
        self.assertEqual([e["phase"] for e in records], ["start", "end", "start", "end"])

    def test_runner_crash_during_warmup_keeps_the_lane_locked(self):
        (self.root / "warm-delay").write_text("2")
        p = self.start(ready=False)
        self.wait_for(lambda: any(e["tool"] == "flutter" and e["phase"] == "start" for e in self.trace()))
        p.kill()
        p.wait(timeout=3)
        self.start(ready=False)
        self.assertEqual(self.result(self.submit(self.job()))["exit_code"], 0)
        records = [e["phase"] for e in self.trace() if e["tool"] == "flutter"]
        self.assertEqual(records, ["start", "end", "start", "end"])

    def test_stale_results_never_overwritten(self):
        job = self.job()
        old = {"id": job["id"], "exit_code": 42, "status": "old", "log_path": None}
        tl.write_json(self.queue / "results" / f"{job['id']}.json", old)
        before = (self.queue / "results" / f"{job['id']}.json").read_bytes()
        self.submit(job)
        self.start()
        self.wait_for(lambda: any(e["event"] == "rejected" for e in self.events()))
        self.assertEqual((self.queue / "results" / f"{job['id']}.json").read_bytes(), before)

    def test_boundary_rejections_are_logged_and_do_not_execute(self):
        self.start()
        job = self.job(argv=["sh", "-c", "touch escaped"])
        result = self.result(self.submit(job))
        self.assertEqual(result["status"], "rejected")
        self.assertIn("not allowlisted", result["error"])
        self.assertTrue(any(e["event"] == "rejected" and e.get("id") == job["id"] for e in self.events()))
        self.assertFalse(any(e["tool"] == "node" for e in self.trace()))

    def test_patch_symlinks_and_cache_changes_rejected(self):
        self.start()
        (self.repo / "escape.js").symlink_to(self.root / "outside.js")
        result = self.result(self.submit(self.job()))
        self.assertEqual(result["status"], "rejected")
        self.assertIn("symlink", result["error"])
        (self.repo / "escape.js").unlink()
        (self.repo / "functions/lib-new.js").write_text("cache injection")
        result = self.result(self.submit(self.job()))
        # Ignored untracked build output is excluded from a normal snapshot.
        self.assertEqual(result["exit_code"], 0)
        base, data = tl.snapshot(self.repo, self.base, self.queue / "tmp")
        self.assertNotIn(b"lib-new.js", data)
        job = self.job()
        data = (b"diff --git a/node_modules/injected.js b/node_modules/injected.js\n"
                b"new file mode 100644\n--- /dev/null\n+++ b/node_modules/injected.js\n"
                b"@@ -0,0 +1 @@\n+cache injection\n")
        job["patch"] = base64.b64encode(data).decode()
        result = self.result(self.submit(job))
        self.assertEqual(result["status"], "rejected")
        self.assertIn("caches", result["error"])
        self.assertFalse((self.queue / "lanes/0/node_modules/injected.js").exists())

    def test_malformed_jobs_and_symlink_queue_entries_are_rejected(self):
        self.start()
        for change in ({"argv": "node --test"}, {"timeout": float("inf")},
                       {"cwd": "../escape"}, {"base": "HEAD"}, {"base": int("1" * 40)}, {"unknown": True}):
            job = self.job()
            job.update(change)
            result = self.result(self.submit(job))
            self.assertEqual(result["status"], "rejected", change)
            self.assertTrue((self.queue / result["log_path"]).exists())
        outside = self.root / "outside.json"
        outside.write_text('{"untouched":true}')
        job_id = uuid.uuid4().hex
        (self.queue / "jobs" / f"{job_id}.json").symlink_to(outside)
        self.assertEqual(self.result(job_id)["status"], "rejected")
        self.assertEqual(outside.read_text(), '{"untouched":true}')

    def test_recovery_publish_crash_does_not_consume_the_retry(self):
        original = self.job()
        original["_lane"] = 0
        retried = dict(original, attempt=1)
        retried.pop("_lane")
        tl.write_json(self.queue / "running" / f"{original['id']}.json", original)
        tl.write_json(self.queue / "jobs" / f"{original['id']}.json", retried)
        self.start()
        result = self.result(original["id"])
        self.assertEqual((result["exit_code"], result["attempt"]), (0, 1))

    def test_finishing_worker_can_remove_a_job_during_recovery_scan(self):
        job = self.job()
        job["_lane"] = 0
        path = self.queue / "running" / f"{job['id']}.json"
        tl.write_json(path, job)
        def finished_during_scan(_path):
            path.unlink()
            raise FileNotFoundError(str(path))
        with patch.object(tl, "read_json", side_effect=finished_during_scan):
            tl.recover(self.queue, {0})
        self.assertFalse(path.exists())
        self.assertFalse(list((self.queue / "results").glob("*.json")))

    def test_killed_worker_holds_lane_until_its_command_finishes_then_retries(self):
        self.start()
        self.behavior(sleep=0.7)
        job_id = self.submit(self.job())
        self.wait_for(lambda: any(e["tool"] == "node" and e["phase"] == "start" for e in self.trace()))
        started = next(e for e in self.events() if e["event"] == "started" and e["id"] == job_id)
        os.kill(started["worker_pid"], 9)
        result = self.result(job_id)
        self.assertEqual((result["exit_code"], result["attempt"]), (0, 1))
        records = [e["phase"] for e in self.trace() if e["tool"] == "node"]
        self.assertEqual(records, ["start", "end", "start", "end"])

    def test_client_exit_code_and_log_tail_mirror_job(self):
        self.start()
        self.behavior(exit=7)
        result = self.cli("run", "--queue", self.queue, "--repo-dir", self.repo, "--base", self.base,
                          "--", "node", "--test", "functions/test/example.test.cjs")
        self.assertEqual(result.returncode, 7, result.stdout + result.stderr)
        self.assertIn("exit_code: 7", result.stdout)
        self.assertIn("log_tail[", result.stdout)
        self.assertIn("job command:", result.stdout)

    def test_timeout_resets_lane_and_next_job_runs(self):
        self.start()
        self.behavior(sleep=2, junk=True)
        result = self.result(self.submit(self.job(timeout=0.15)))
        self.assertEqual((result["exit_code"], result["status"]), (124, "timeout"))
        self.assertFalse((self.queue / "lanes/0/junk.txt").exists())
        self.behavior()
        self.assertEqual(self.result(self.submit(self.job()))["exit_code"], 0)

    def test_npx_uses_installed_compiler_without_network_fallback(self):
        self.start()
        job = self.job(argv=["npx", "tsc", "-p", "tsconfig.json"])
        job["cwd"] = "functions"
        self.assertEqual(self.result(self.submit(job))["exit_code"], 0)
        self.assertFalse(any(e["tool"] == "npx" for e in self.trace()))
        self.assertTrue(any(e["tool"] == "node" and "node_modules/typescript/bin/tsc" in e["argv"][0]
                            for e in self.trace()))

    def test_second_runner_rejected(self):
        self.start()
        result = self.cli("runner", "--repo", self.repo, "--queue", self.queue, "--lanes", "1")
        self.assertEqual(result.returncode, 2)
        self.assertIn("already owns", result.stdout)

    def test_generated_node_targets_compile_from_each_patch_in_the_same_lane(self):
        self.start(lanes=2)
        ids = []
        for cwd, expected in ((".", "first patch\n"), ("functions", "second patch\n")):
            (self.repo / "functions/test/generated.test.ts").write_text(expected)
            self.behavior(expect_compiled=expected)
            target = "functions/.test-build/test/generated.test.js" if cwd == "." else ".test-build/test/generated.test.js"
            argv = ["node", "--test", target]
            tl.validate_command(argv, cwd, self.repo, allow_generated=True)
            job = self.job(argv=argv)
            job["cwd"] = cwd
            ids.append(self.submit(job))
        for job_id in ids:
            result = self.result(job_id)
            self.assertEqual(result["exit_code"], 0, result)
            log = (self.queue / result["log_path"]).read_text()
            self.assertIn("compiled target verified", log)
            lane = str(self.queue / "lanes" / str(result["lane"]))
            self.assertIn(lane + "/functions/node_modules/typescript/bin/tsc", log)
        self.assertFalse((self.repo / "functions/.test-build").exists())
        client = self.cli("run", "--queue", self.queue, "--repo-dir", self.repo, "--base", self.base,
                          "--cwd", "functions", "--", "node", "--test", ".test-build/test/generated.test.js")
        self.assertEqual(client.returncode, 0, client.stdout + client.stderr)
        self.assertIn("compiled target verified", client.stdout)

    def test_generated_node_compile_failure_and_timeout_skip_tests(self):
        self.start()
        for behavior, expected in (({"compile_exit": 13}, 13), ({"compile_sleep": 2}, 124)):
            self.behavior(**behavior)
            job = self.job(argv=["node", "--test", "functions/.test-build/test/generated.test.js"],
                           timeout=5 if expected == 13 else 0.5)
            result = self.result(self.submit(job))
            self.assertEqual(result["exit_code"], expected, result)
            log = (self.queue / result["log_path"]).read_text()
            self.assertNotIn('"--test"', log)

    def test_deleted_generated_test_cannot_execute_stale_cached_output(self):
        self.start()
        target = self.queue / "lanes/0/functions/.test-build/test/generated.test.js"
        target.parent.mkdir(parents=True)
        target.write_text("stale old passing test")
        (self.repo / "functions/test/generated.test.ts").unlink()
        job = self.job(argv=["node", "--test", "functions/.test-build/test/generated.test.js"])
        result = self.result(self.submit(job))
        self.assertEqual(result["status"], "rejected", result)
        self.assertIn("does not exist", result["error"])
        self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
