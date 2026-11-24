"""Local-only MobSF gate: fake Docker/API boundaries, never pull or scan."""
from contextlib import redirect_stdout
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
import io
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

TOOL = Path(__file__).resolve().parents[1] / "bin/mobsf-scan"
spec = spec_from_loader("mobsf_scan", SourceFileLoader("mobsf_scan", str(TOOL)))
m = module_from_spec(spec)
spec.loader.exec_module(m)
DIGEST = "opensecurity/mobile-security-framework-mobsf@sha256:" + "a" * 64
REPORT = {"package_name": "org.example.app", "version_name": "1.0", "version_code": "1",
          "sha256": hashlib.sha256(b"PK-test-app").hexdigest(),
          "manifest_analysis": {"manifest_findings": [
              {"rule": "exported", "severity": "high", "title": "Exported component"}]},
          "code_analysis": {"findings": {"weak_crypto": {
              "metadata": {"severity": "warning", "description": "Weak crypto"},
              "files": {"Foo.java": "1"}}}}}


class MobSFTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.app = self.root / "release.aab"
        self.app.write_bytes(b"PK-test-app")
        self.args = [str(self.app), "--app", "demo", "--release", "1.0+1",
                     "--output-root", str(self.root / "reports")]
        self.calls = []

    def docker(self, args, **kwargs):
        self.calls.append((args, kwargs))
        if args[:2] == ["docker", "image"]:
            return subprocess.CompletedProcess(args, 0, json.dumps([DIGEST]).encode(), b"")
        if args[1] == "inspect":
            run = next(a for a, _ in reversed(self.calls) if a[1] == "run")
            if "Config.Labels" in args[3]:
                token = run[run.index("--label") + 1].split("=", 1)[1]
                return subprocess.CompletedProcess(args, 0, (json.dumps({"org.iac.secscan": token}) + '|' + json.dumps("d" * 64)).encode(), b"")
            fields = ["d" * 64, DIGEST, "/" + run[run.index("--name") + 1], "none", {},
                      {"Running": True, "Health": {"Status": "healthy"}}]
            return subprocess.CompletedProcess(args, 0, "|".join(json.dumps(f) for f in fields).encode(), b"")
        if args[1] == "exec":
            endpoint = args[-2]
            out = {"health": b"mobsf-login-ready\n", "upload": json.dumps({"hash": "b" * 32, "scan_type": "aab"}).encode(),
                   "scan": b'{"ok":true}', "report_json": json.dumps(REPORT).encode(),
                   "download_pdf": b"%PDF-1.4\nreport"}[endpoint]
            return subprocess.CompletedProcess(args, 0, out, b"")
        return subprocess.CompletedProcess(args, 0, ("d" * 64 + "\n").encode(), b"")

    def invoke(self, args=None, runner=None):
        output = io.StringIO()
        with patch.object(m.subprocess, "run", side_effect=runner or self.docker), redirect_stdout(output):
            code = m.main(self.args if args is None else args)
        return code, output.getvalue()

    def test_full_aab_lifecycle_and_reports(self):
        code, out = self.invoke()
        self.assertEqual(code, 1)  # unsuppressed high/warning gate
        folder = self.root / "reports/demo-1.0+1"
        self.assertEqual(json.loads((folder / "report.json").read_text()), REPORT)
        self.assertTrue((folder / "report.pdf").read_bytes().startswith(b"%PDF-"))
        summary = json.loads((folder / "summary.json").read_text())
        self.assertEqual(summary["high"], 1)
        self.assertEqual(summary["warning"], 1)
        self.assertEqual(summary["image"], DIGEST)
        self.assertIn("high: 1", out)
        endpoints = [a[-2] for a, _ in self.calls if a[1] == "exec"]
        self.assertEqual(endpoints, ["health", "upload", "scan", "report_json", "download_pdf"])
        self.assertEqual(self.calls[-1][0][1:3], ["rm", "-f"])

    def test_no_network_no_mount_no_port_no_pull_digest_run(self):
        self.invoke()
        run, kw = next((a, k) for a, k in self.calls if a[1] == "run")
        self.assertIn("--pull=never", run)
        self.assertEqual(run[run.index("--network") + 1], "none")
        self.assertEqual(run[-1], DIGEST)
        self.assertFalse(set(run) & {"-p", "--publish", "-v", "--volume", "--privileged"})
        self.assertFalse(any(a[1] == "pull" for a, _ in self.calls))
        self.assertIn("MOBSF_VT_UPLOAD=0", run)
        self.assertIn("MOBSF_DOMAIN_MALWARE_SCAN=0", run)
        self.assertIn("MOBSF_API_KEY", kw["env"])
        self.assertNotIn(kw["env"]["MOBSF_API_KEY"], " ".join(run))

    def test_key_is_per_run_and_not_retained(self):
        self.invoke()
        key = next(k["env"]["MOBSF_API_KEY"] for a, k in self.calls if a[1] == "run")
        self.args[self.args.index("1.0+1")] = "1.0+2"
        self.invoke()
        keys = [k["env"]["MOBSF_API_KEY"] for a, k in self.calls if a[1] == "run"]
        self.assertNotEqual(*keys)
        for f in (self.root / "reports").rglob("*"):
            if f.is_file():
                self.assertNotIn(key.encode(), f.read_bytes())

    def test_missing_image_refuses_without_pull(self):
        def absent(args, **kw):
            self.calls.append((args, kw))
            return subprocess.CompletedProcess(args, 1, b"", b"not present")
        self.assertEqual(self.invoke(runner=absent)[0], 1)
        self.assertEqual(len(self.calls), 1)

    def test_cleanup_on_api_failure(self):
        def fail(args, **kw):
            if args[1] == "exec":
                self.calls.append((args, kw))
                return subprocess.CompletedProcess(args, 1, b"", b"sensitive failure")
            return self.docker(args, **kw)
        code, out = self.invoke(runner=fail)
        self.assertEqual(code, 1)
        self.assertNotIn("sensitive failure", out)
        self.assertEqual(self.calls[-1][0][1:3], ["rm", "-f"])

    def test_cleanup_on_interruption(self):
        def fail(args, **kw):
            if args[1] == "exec":
                raise KeyboardInterrupt()
            return self.docker(args, **kw)
        self.assertEqual(self.invoke(runner=fail)[0], 1)
        self.assertEqual(self.calls[-1][0][1:3], ["rm", "-f"])

    def test_scan_error_never_fetches_report_or_claims_clean(self):
        def error(args, **kw):
            if args[1] == "exec" and args[-2] == "scan":
                self.calls.append((args, kw))
                return subprocess.CompletedProcess(args, 0, b'{"error":"AAB analysis failed"}', b"")
            return self.docker(args, **kw)
        code, out = self.invoke(runner=error)
        self.assertEqual(code, 1)
        self.assertIn("no clean result", out)
        self.assertNotIn("report_json", [a[-2] for a, _ in self.calls if a[1] == "exec"])
        self.assertFalse((self.root / "reports/demo-1.0+1/summary.json").exists())

    def test_wrong_container_or_published_busy_port_refuses_before_upload(self):
        for changed in ((0, "e" * 64), (1, "unrelated-fastapi-image"),
                        (3, "bridge"), (4, {"8000/tcp": [{"HostIp": "127.0.0.1", "HostPort": "8000"}]})):
            self.calls.clear()
            self.args[self.args.index("--release") + 1] = "case" + str(changed[0])
            def wrong(args, **kw):
                res = self.docker(args, **kw)
                if args[1] == "inspect" and "Config.Labels" not in args[3]:
                    fields = [json.loads(f) for f in res.stdout.decode().split("|")]
                    fields[changed[0]] = changed[1]
                    res.stdout = "|".join(json.dumps(f) for f in fields).encode()
                return res
            self.assertEqual(self.invoke(runner=wrong)[0], 1)
            self.assertFalse(any(a[1] == "exec" for a, _ in self.calls))
            self.assertEqual(self.calls[-1][0][-1], "d" * 64)

    def test_only_own_unique_container_is_removed(self):
        self.invoke()
        run = next(a for a, _ in self.calls if a[1] == "run")
        self.assertRegex(run[run.index("--name") + 1], r"^iac-mobsf-[0-9a-f]{24}$")
        self.assertEqual(self.calls[-1][0], ["docker", "rm", "-f", "d" * 64])
        self.assertFalse(any(a[1] in ("ps", "stop", "restart") for a, _ in self.calls))

    def test_bad_artifact_and_labels_precede_docker(self):
        for args in ([str(self.root / "absent.apk"), "--app", "demo", "--release", "1"],
                     [str(self.app), "--app", "../escape", "--release", "1"],
                     [str(self.app), "--app", "demo", "--release", ".."],
                     self.args + ["--typo"]):
            with self.subTest(args=args):
                self.assertEqual(self.invoke(args)[0], 2)
                self.assertEqual(self.calls, [])

    def test_repeated_release_cannot_overwrite_evidence(self):
        self.invoke()
        self.calls.clear()
        self.assertEqual(self.invoke()[0], 2)
        self.assertFalse(self.calls)

    def test_suppressions_require_reason_and_unexpired_date(self):
        p = self.root / "suppressions.json"
        for entry in ({"id": "manifest:exported", "reason": "", "expires": "2099-01-01"},
                      {"id": "manifest:exported", "reason": "reviewed", "expires": "2020-01-01"},
                      {"id": "manifest:exported", "reason": "reviewed", "expires": "tomorrow"}):
            p.write_text(json.dumps([entry]))
            self.assertEqual(self.invoke(self.args + ["--suppressions", str(p)])[0], 2)
            self.assertFalse(self.calls)

    def test_suppression_retains_raw_findings_and_diff(self):
        self.invoke()
        p = self.root / "suppressions.json"
        p.write_text(json.dumps([{"id": id, "reason": "Owner accepted", "expires": "2099-01-01"}
                                 for id in ("manifest:exported", "code:weak_crypto")]))
        self.args[self.args.index("1.0+1")] = "1.0+2"
        self.assertEqual(self.invoke(self.args + ["--suppressions", str(p)])[0], 0)
        folder = self.root / "reports/demo-1.0+2"
        s = json.loads((folder / "summary.json").read_text())
        self.assertEqual(s["suppressed"], 2)
        self.assertEqual(s["new"], [])
        self.assertEqual(s["resolved"], [])
        self.assertIn("demo-1.0+1", s["previous"])
        self.assertEqual(json.loads((folder / "report.json").read_text()), REPORT)

    def test_bad_report_is_incomplete_and_container_removed(self):
        def bad(args, **kw):
            if args[1] == "exec" and args[-2] == "report_json":
                return subprocess.CompletedProcess(args, 0, b'{"error":"bad"}', b"")
            return self.docker(args, **kw)
        self.assertEqual(self.invoke(runner=bad)[0], 1)
        self.assertEqual(self.calls[-1][0][1:3], ["rm", "-f"])
        self.assertFalse((self.root / "reports/demo-1.0+1/summary.json").exists())

    def test_report_missing_findings_schema_is_not_clean(self):
        for report in ({"package_name": "org.example.app", "manifest_analysis": {}, "code_analysis": {}},
                       {"package_name": "org.example.app", "manifest_analysis": {"manifest_findings": []}, "code_analysis": {"findings": []}}):
            with self.assertRaises(RuntimeError):
                m.findings(report)

    def test_report_hash_mismatch_cannot_pass(self):
        def mismatch(args, **kw):
            if args[1] == "exec" and args[-2] == "report_json":
                report = dict(REPORT, sha256="0" * 64)
                return subprocess.CompletedProcess(args, 0, json.dumps(report).encode(), b"")
            return self.docker(args, **kw)
        self.assertEqual(self.invoke(runner=mismatch)[0], 1)
        self.assertFalse((self.root / "reports/demo-1.0+1/summary.json").exists())

    def test_nested_native_and_js_findings_are_in_summary(self):
        report = json.loads(json.dumps(REPORT))
        report["binary_analysis"] = [{"name": "libfoo.so", "nx": {"severity": "high", "description": "Executable stack"}}]
        report["js_analysis"] = {"findings": {"js_rule": {"metadata": {"severity": "warning", "description": "Unsafe JS"}}}}
        rows = m.findings(report)
        self.assertTrue(any("Executable stack" in r["title"] for r in rows))
        self.assertTrue(any("Unsafe JS" in r["title"] for r in rows))

    def test_cleanup_cannot_remove_an_unrelated_container(self):
        def unrelated(args, **kw):
            if args[1] == "inspect" and "Config.Labels" in args[3]:
                self.calls.append((args, kw))
                return subprocess.CompletedProcess(args, 0, (json.dumps({"org.iac.secscan": "other-owner"}) + '|' + json.dumps("e" * 64)).encode(), b"")
            return self.docker(args, **kw)
        self.assertEqual(self.invoke(runner=unrelated)[0], 1)
        self.assertFalse(any(a[1] == "rm" for a, _ in self.calls))

    def test_cleanup_unverifiable_cannot_print_pass(self):
        def missing(args, **kw):
            if args[1] == "inspect" and "Config.Labels" in args[3]:
                return subprocess.CompletedProcess(args, 1, b"", b"daemon unavailable")
            return self.docker(args, **kw)
        code, out = self.invoke(runner=missing)
        self.assertEqual(code, 1)
        self.assertNotIn('status: "pass"', out)
        self.assertIn("cleanup", out)
        self.assertFalse((self.root / "reports/demo-1.0+1/summary.json").exists())

    def test_health_request_does_not_send_key_or_file(self):
        self.invoke()
        health = next((a, kw) for a, kw in self.calls if a[1] == "exec" and a[-2] == "health")
        self.assertNotIn("stdin", health[1])
        self.assertNotIn("MOBSF_API_KEY", health[1]["env"])
        self.assertEqual(health[0][3], "d" * 64)

    def test_api_transport_streams_upload_and_health_uses_no_auth(self):
        from unittest.mock import MagicMock
        for action, argument in (("upload", "apk:4"), ("health", "")):
            connection = MagicMock()
            response = connection.getresponse.return_value
            response.status = 200
            response.read.return_value = b'{"hash":"test"}'
            output = io.BytesIO()
            wrapped = io.TextIOWrapper(output, encoding="utf-8", write_through=True)
            stdin = io.TextIOWrapper(io.BytesIO(b"DATA"))
            with patch("http.client.HTTPConnection", return_value=connection), patch.object(sys, "argv", ["api", action, argument]), patch.object(sys, "stdin", stdin), patch.object(sys, "stdout", wrapped), patch.dict("os.environ", {"MOBSF_API_KEY": "fake-key"}):
                exec(m.API_CLIENT, {})
            if action == "health":
                connection.request.assert_called_once_with("GET", "/login/")
                connection.putheader.assert_not_called()
            else:
                sent = b"".join(c.args[0] for c in connection.send.call_args_list)
                self.assertIn(b"DATA", sent)
                headers = dict(c.args for c in connection.putheader.call_args_list)
                self.assertEqual(int(headers["Content-Length"]), len(sent))
                self.assertEqual(headers["Authorization"], "fake-key")

    def test_local_daemon_is_forced_even_with_remote_ambient_context(self):
        with patch.dict("os.environ", {"DOCKER_HOST": "ssh://remote", "DOCKER_CONTEXT": "production"}), patch.object(m.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, b"", b"")) as run:
            m.docker(["version"])
        env = run.call_args.kwargs["env"]
        self.assertEqual(env["DOCKER_HOST"], "unix:///var/run/docker.sock")
        self.assertNotIn("DOCKER_CONTEXT", env)

    def test_changed_finding_is_compared_with_previous_report(self):
        self.invoke()
        old = self.root / "reports/demo-1.0+1/summary.json"
        summary = json.loads(old.read_text())
        summary["findings"][0]["severity"] = "warning"
        old.write_text(json.dumps(summary))
        self.args[self.args.index("1.0+1")] = "1.0+2"
        self.invoke()
        current = json.loads((self.root / "reports/demo-1.0+2/summary.json").read_text())
        self.assertIn(summary["findings"][0]["id"], current["changed"])

    def test_cli_subprocess_runs_full_fake_lifecycle(self):
        fake = self.root / "docker"
        fake.write_text('#!' + sys.executable + '''
import json, os, pathlib, sys
a = sys.argv[1:]
p = pathlib.Path(__file__)
with p.with_suffix('.calls').open('a') as stream:
    stream.write(json.dumps({'args':a[:3], 'daemon':os.environ.get('DOCKER_HOST'), 'context':os.environ.get('DOCKER_CONTEXT')}) + '\\n')
if a[0] == 'image':
    print(json.dumps([__DIGEST__]))
elif a[0] == 'run':
    p.with_suffix('.state').write_text(json.dumps({'name':a[a.index('--name')+1], 'label':a[a.index('--label')+1].split('=',1)[1]}))
    print('d'*64)
elif a[0] == 'inspect':
    state = json.loads(p.with_suffix('.state').read_text())
    fields = [{'org.iac.secscan':state['label']}, 'd'*64] if 'Config.Labels' in a[2] else [
        'd'*64, __DIGEST__, '/'+state['name'], 'none', {}, {'Running':True,'Health':{'Status':'healthy'}}]
    print('|'.join(json.dumps(x) for x in fields))
elif a[0] == 'exec':
    action = a[-2]
    if action == 'upload':
        p.with_suffix('.uploaded').write_bytes(sys.stdin.buffer.read())
    response = {'health': b'mobsf-login-ready', 'upload':b'{"hash":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"}',
                'scan':b'{}', 'report_json':json.dumps(__REPORT__).encode(), 'download_pdf':b'%PDF-1.4 fixture'}
    sys.stdout.buffer.write(response[action])
'''.replace('__DIGEST__', repr(DIGEST)).replace('__REPORT__', repr(REPORT)))
        fake.chmod(0o700)
        env = {"PATH": str(self.root) + ":/usr/bin:/bin", "HOME": str(self.root),
               "DOCKER_HOST": "ssh://must-not-use", "DOCKER_CONTEXT": "production"}
        result = subprocess.run([sys.executable, str(TOOL)] + self.args, env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("high: 1", result.stdout)
        self.assertEqual(fake.with_suffix(".uploaded").read_bytes(), self.app.read_bytes())
        calls = [json.loads(line) for line in fake.with_suffix(".calls").read_text().splitlines()]
        self.assertEqual(len(calls), 10)
        self.assertTrue(all(c["daemon"] == "unix:///var/run/docker.sock" and c["context"] is None for c in calls))
        self.assertTrue((self.root / "reports/demo-1.0+1/report.pdf").is_file())

    def test_version_and_no_args_do_not_call_docker(self):
        for args in ([], ["--version"], ["-v"], ["-V"], ["--help"]):
            self.assertEqual(self.invoke(args)[0], 0)
        self.assertFalse(self.calls)


if __name__ == "__main__":
    unittest.main()
