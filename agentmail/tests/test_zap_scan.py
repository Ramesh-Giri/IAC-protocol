"""Inventory and active-authorization gates using fake Docker, no host scans."""
from contextlib import redirect_stdout
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
import io
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

TOOL = Path(__file__).resolve().parents[1] / "bin/zap-scan"
spec = spec_from_loader("zap_scan", SourceFileLoader("zap_scan", str(TOOL)))
z = module_from_spec(spec)
spec.loader.exec_module(z)
DIGEST = "zaproxy/zap-stable@sha256:" + "c" * 64


class ZAPTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.inventory = self.root / "websec.local.json"
        self.entry = {"host": "example.com", "paths": ["/", "/openapi.json"]}
        self.save()
        self.args = ["example.com", "--inventory", str(self.inventory),
                     "--output-root", str(self.root / "reports")]
        self.calls = []
        self.upstream_code = 0

    def save(self):
        self.inventory.write_text(json.dumps({"web_hosts": [self.entry], "mail_domains": []}))

    def docker(self, args, **kw):
        self.calls.append((args, kw))
        if args[1] == "image":
            return subprocess.CompletedProcess(args, 0, json.dumps([DIGEST]).encode(), b"")
        if args[1] == "inspect":
            run = next(a for a, _ in reversed(self.calls) if a[1] == "run")
            token = run[run.index("--label") + 1].split("=", 1)[1]
            return subprocess.CompletedProcess(args, 0, (json.dumps({"org.iac.secscan": token}) + '|' + json.dumps("d" * 64)).encode(), b"")
        if args[1] == "run":
            mount = next(x for x in args if x.endswith(":/zap/wrk:rw"))
            wrk = Path(mount.removesuffix(":/zap/wrk:rw"))
            (wrk / "report.html").write_text("<html>report</html>")
            (wrk / "report.json").write_text(json.dumps({"site": [{"@name": "https://example.com", "@host": "example.com", "@port": "443", "@ssl": "true", "alerts": []}]}))
            return subprocess.CompletedProcess(args, self.upstream_code, b"private upstream log", b"")
        if args[1] == "cp":
            Path(args[-1]).write_text("fixture ZAP application log\n")
            return subprocess.CompletedProcess(args, 0, b"", b"")
        return subprocess.CompletedProcess(args, 0, b"", b"")

    def invoke(self, args=None, runner=None):
        out = io.StringIO()
        with patch.object(z.subprocess, "run", side_effect=runner or self.docker), redirect_stdout(out):
            code = z.main(self.args if args is None else args)
        return code, out.getvalue()

    def test_passive_default_digest_no_updates_and_reports(self):
        code, out = self.invoke()
        self.assertEqual(code, 0)
        run = next(a for a, _ in self.calls if a[1] == "run")
        self.assertIn(DIGEST, run)
        self.assertIn("--pull=never", run)
        self.assertEqual(run[run.index("--workdir") + 1], "/zap/wrk")
        self.assertIn("zap-baseline.py", run)
        self.assertIn("--autooff", run)
        self.assertIn("-silent", run[run.index("-z") + 1])
        self.assertFalse(set(run) & {"zap-full-scan.py", "zap-api-scan.py", "-a", "-j", "-p"})
        self.assertNotIn("private upstream log", out)
        summaries = list((self.root / "reports/example.com").rglob("summary.json"))
        self.assertEqual(len(summaries), 1)
        self.assertEqual(json.loads(summaries[0].read_text())["mode"], "baseline")

    def test_every_mode_builds_explicit_silent_and_autooff(self):
        self.entry["active_scan_allowed"] = True
        self.save()
        for mode in ("baseline", "api", "full"):
            with self.subTest(mode=mode):
                args = self.args + ["--mode", mode]
                if mode != "baseline":
                    args += ["--ramesh-instruction", "Run this scan on example.com"]
                if mode == "api":
                    args += ["--api-path", "/openapi.json"]
                self.assertEqual(self.invoke(args)[0], 0)
                run = next(a for a, _ in reversed(self.calls) if a[1] == "run")
                self.assertIn("--autooff", run)
                options = shlex.split(run[run.index("-z") + 1])
                self.assertIn("-silent", options)
                self.assertFalse(set(options) & {"-addonupdate", "-addoninstall", "-autoupdate"})

    def test_launcher_preserves_silent_and_translates_autooff_for_pinned_scripts(self):
        for script in ("zap-baseline.py", "zap-api-scan.py", "zap-full-scan.py"):
            with self.subTest(script=script), patch.object(sys, "argv", ["launcher", script, "-t", "https://example.com/", "--autooff", "-z", "-silent"]), patch("runpy.run_path") as run:
                exec(z.PACKAGED_LAUNCHER, {})
                passed = sys.argv[:]
                self.assertEqual(passed[0], script)
                self.assertIn("-silent", passed)
                self.assertEqual("--autooff" in passed, script == "zap-baseline.py")
                run.assert_called_once_with("/zap/" + script, run_name="__main__")

    def test_failure_retains_console_and_zap_log_before_removal(self):
        self.upstream_code = 3
        code, out = self.invoke()
        self.assertEqual(code, 1)
        folder = next((self.root / "reports").rglob("iac_hook.py")).parent
        self.assertIn("private upstream log", (folder / "console.log").read_text())
        self.assertIn("fixture ZAP application log", (folder / "zap.log").read_text())
        self.assertEqual((folder / "console.log").stat().st_mode & 0o777, 0o600)
        self.assertEqual((folder / "zap.log").stat().st_mode & 0o777, 0o600)
        self.assertNotIn("private upstream log", out)
        commands = [a[1] for a, _ in self.calls]
        self.assertLess(commands.index("cp"), commands.index("rm"))

    def test_timeout_retains_partial_console_and_zap_log_and_fails(self):
        def timeout(args, **kw):
            if args[1] == "run":
                self.calls.append((args, kw))
                raise subprocess.TimeoutExpired(args, 1800, output=b"partial scanner output", stderr=b"partial scanner diagnostic")
            return self.docker(args, **kw)
        self.assertEqual(self.invoke(runner=timeout)[0], 1)
        folder = next((self.root / "reports").rglob("iac_hook.py")).parent
        self.assertIn("partial scanner output", (folder / "console.log").read_text())
        self.assertIn("partial scanner diagnostic", (folder / "console.log").read_text())
        self.assertIn("fixture ZAP application log", (folder / "zap.log").read_text())
        self.assertFalse((folder / "summary.json").exists())
        self.assertEqual(self.calls[-1][0][1:3], ["rm", "-f"])

    def test_image_home_log_fallback_is_copied_before_removal(self):
        def legacy(args, **kw):
            if args[1] == "cp" and ":/tmp/iac-zap/zap.log" in args[-2]:
                self.calls.append((args, kw))
                return subprocess.CompletedProcess(args, 1, b"", b"not at configured path")
            return self.docker(args, **kw)
        self.upstream_code = 3
        self.assertEqual(self.invoke(runner=legacy)[0], 1)
        copies = [a for a, _ in self.calls if a[1] == "cp"]
        self.assertEqual(len(copies), 2)
        self.assertTrue(copies[-1][-2].endswith(":/home/zap/.ZAP/zap.log"))
        self.assertIn("fixture ZAP application log", next((self.root / "reports").rglob("zap.log")).read_text())
        self.assertEqual(self.calls[-1][0][1:3], ["rm", "-f"])

    def test_interruption_retains_container_console_and_application_log(self):
        def interrupted(args, **kw):
            if args[1] == "run":
                self.calls.append((args, kw))
                raise KeyboardInterrupt()
            if args[1] == "logs":
                self.calls.append((args, kw))
                return subprocess.CompletedProcess(args, 0, b"recovered container output", b"")
            return self.docker(args, **kw)
        self.assertEqual(self.invoke(runner=interrupted)[0], 1)
        folder = next((self.root / "reports").rglob("iac_hook.py")).parent
        self.assertIn("recovered container output", (folder / "console.log").read_text())
        self.assertIn("fixture ZAP application log", (folder / "zap.log").read_text())
        self.assertEqual(self.calls[-1][0][1:3], ["rm", "-f"])

    def test_launcher_refuses_missing_silent_or_autooff_before_upstream(self):
        for args in (["--autooff", "-z", "-config foo=bar"], ["-z", "-silent"]):
            with self.subTest(args=args), patch.object(sys, "argv", ["launcher", "zap-baseline.py"] + args), patch("runpy.run_path") as run:
                with self.assertRaises(RuntimeError):
                    exec(z.PACKAGED_LAUNCHER, {})
                run.assert_not_called()

    def test_off_inventory_and_url_inputs_refused_before_docker(self):
        for host in ("evil.example", "example.com.evil.test", "https://example.com", "example.com:443",
                     "user@example.com", "EXAMPLE.com/", "127.0.0.1", "localhost", "--typo"):
            with self.subTest(host=host):
                self.assertEqual(self.invoke([host] + self.args[1:])[0], 2)
                self.assertFalse(self.calls)

    def test_active_needs_both_permissions(self):
        for mode in ("api", "full"):
            for allowed, instruction in ((False, None), (True, None), (False, "Ramesh said scan example.com")):
                self.entry["active_scan_allowed"] = allowed
                self.save()
                args = self.args + ["--mode", mode]
                if mode == "api":
                    args += ["--api-path", "/openapi.json"]
                if instruction:
                    args += ["--ramesh-instruction", instruction]
                self.assertEqual(self.invoke(args)[0], 2)
                self.assertFalse(self.calls)

    def test_active_rejects_truthy_non_boolean_and_blank_instruction(self):
        for allowed, instruction in (("true", "approved"), (1, "approved"), (True, "  ")):
            self.entry["active_scan_allowed"] = allowed
            self.save()
            self.assertEqual(self.invoke(self.args + ["--mode", "full", "--ramesh-instruction", instruction])[0], 2)
            self.assertFalse(self.calls)

    def test_active_full_records_instruction_and_bounded_rate(self):
        self.entry["active_scan_allowed"] = True
        self.save()
        instruction = "Run full scan on example.com at one request per second."
        self.assertEqual(self.invoke(self.args + ["--mode", "full", "--ramesh-instruction", instruction])[0], 0)
        run = next(a for a, _ in self.calls if a[1] == "run")
        self.assertIn("zap-full-scan.py", run)
        s = json.loads(next((self.root / "reports").rglob("summary.json")).read_text())
        self.assertEqual(s["ramesh_instruction"], instruction)
        self.assertEqual(s["requests_per_second"], 1)

    def test_api_spec_must_be_inventory_path_and_overrides_server(self):
        self.entry["active_scan_allowed"] = True
        self.save()
        args = self.args + ["--mode", "api", "--ramesh-instruction", "Run API scan example.com"]
        for p in (None, "/not-listed.json", "https://evil.test/spec", "//evil.test/spec"):
            self.assertEqual(self.invoke(args + (["--api-path", p] if p else []))[0], 2)
            self.assertFalse(self.calls)
        self.assertEqual(self.invoke(args + ["--api-path", "/openapi.json"])[0], 0)
        run = next(a for a, _ in self.calls if a[1] == "run")
        self.assertIn("zap-api-scan.py", run)
        self.assertEqual(run[run.index("-O") + 1], "https://example.com")
        self.assertEqual(run[run.index("-f") + 1], "openapi")

    def test_hook_requires_rate_limit_success_before_access(self):
        namespace = {}
        with patch.dict("sys.modules", {"zap_common": MagicMock()}):
            exec(z.make_hook("example.com", ["/", "/openapi.json"], 1), namespace)
        zap = MagicMock()
        zap.context.new_context.return_value = "1"
        for component, method in ((zap.context, "include_in_context"), (zap.context, "set_context_in_scope"),
                                  (zap.core, "set_mode"), (zap.spider, "exclude_from_scan"),
                                  (zap.ascan, "exclude_from_scan")):
            getattr(component, method).return_value = "OK"
        zap.network.add_rate_limit_rule.return_value = "OK"
        with patch.dict("sys.modules", {"zap_common": MagicMock()}):
            namespace["zap_started"](zap, "https://example.com/")
        self.assertEqual(zap.network.add_rate_limit_rule.call_args.kwargs["requestspersecond"], 1)
        zap.network.add_rate_limit_rule.return_value = "FAIL"
        with self.assertRaises(RuntimeError), patch.dict("sys.modules", {"zap_common": MagicMock()}):
            namespace["zap_started"](zap, "https://example.com/")

    def test_global_exclusion_blocks_host_confusion_and_alternate_ports(self):
        exclude = re.compile(z.exclusion_regex("example.com"))
        self.assertIsNone(exclude.fullmatch("https://example.com/a?x=1"))
        self.assertIsNone(exclude.fullmatch("https://example.com:443/"))
        for target in ("http://example.com/", "https://evil.test/", "https://example.com.evil.test/",
                       "https://example.com@evil.test/", "https://example.com:8443/", "file:///etc/passwd"):
            self.assertIsNotNone(exclude.fullmatch(target), target)

    def test_api_guard_rejects_external_refs_and_overrides_nested_servers(self):
        namespace = {}
        with patch.dict("sys.modules", {"zap_common": MagicMock()}):
            exec(z.make_hook("example.com", ["/openapi.json"], 1, "api"), namespace)
        guard = namespace["safe_openapi"]
        for ref in ("https://evil.test/defs.json#/x", "//evil.test/x", "../private.json", "file:///etc/passwd"):
            with self.subTest(ref=ref), self.assertRaises(RuntimeError):
                guard({"openapi": "3.0.0", "components": {"schemas": {"X": {"$ref": ref}}}})
        document = {"openapi": "3.0.0", "servers": [{"url": "https://evil.test"}],
                    "paths": {"/x": {"get": {"servers": [{"url": "http://wrong.test"}],
                                           "responses": {"200": {"$ref": "#/components/responses/OK"}}}}}}
        checked = guard(document)
        self.assertEqual(checked["servers"], [{"url": "https://example.com"}])
        self.assertEqual(checked["paths"]["/x"]["get"]["servers"], [{"url": "https://example.com"}])

    def test_api_guard_refuses_redirect_before_import(self):
        namespace = {}
        with patch.dict("sys.modules", {"zap_common": MagicMock()}):
            exec(z.make_hook("example.com", ["/openapi.json"], 1, "api"), namespace)
        zap = MagicMock()
        zap.core.access_url.return_value = [{"responseHeader": "HTTP/1.1 302 Found\r\nLocation: https://evil.test/", "responseBody": ""}]
        with self.assertRaises(RuntimeError):
            namespace["import_inventory_openapi"](zap, "https://example.com/openapi.json", "https://example.com")
        zap.core.access_url.assert_called_once_with("https://example.com/openapi.json", followredirects=False)
        zap.openapi.import_file.assert_not_called()

    def test_expiring_rules_generate_config_and_keep_raw_evidence(self):
        self.entry["zap_rules"] = {"10020": {"action": "IGNORE", "reason": "Accepted edge issue", "expires": "2099-01-01"}}
        self.save()
        self.assertEqual(self.invoke()[0], 0)
        rules = next((self.root / "reports").rglob("rules.conf")).read_text()
        self.assertIn("10020\tIGNORE", rules)
        self.assertIn("Accepted edge issue", rules)

    def test_invalid_or_expired_rules_refuse_before_docker(self):
        for rule in ({"action": "IGNORE", "reason": "", "expires": "2099-01-01"},
                     {"action": "IGNORE", "reason": "old", "expires": "2000-01-01"},
                     {"action": "BOGUS", "reason": "why", "expires": "2099-01-01"}):
            self.entry["zap_rules"] = {"10020": rule}
            self.save()
            self.assertEqual(self.invoke()[0], 2)
            self.assertFalse(self.calls)

    def test_upstream_exit_codes_map_to_gate_and_cleanup(self):
        for upstream, expected in ((0, 0), (1, 1), (2, 1), (3, 1), (7, 1)):
            self.upstream_code = upstream
            self.assertEqual(self.invoke()[0], expected)
            self.assertEqual(self.calls[-1][0][1:3], ["rm", "-f"])

    def test_missing_report_cannot_pass(self):
        def missing(args, **kw):
            if args[1] == "run":
                self.calls.append((args, kw))
                return subprocess.CompletedProcess(args, 0, b"", b"")
            return self.docker(args, **kw)
        self.assertEqual(self.invoke(runner=missing)[0], 1)
        folder = next((self.root / "reports").rglob("iac_hook.py")).parent
        self.assertTrue((folder / "console.log").is_file())
        self.assertTrue((folder / "zap.log").is_file())

    def test_unknown_flags_and_unlisted_paths_precede_docker(self):
        for args in (self.args + ["--typo"], self.args + ["--path", "/not-listed"],
                     self.args + ["--requests-per-second", "99"]):
            self.assertEqual(self.invoke(args)[0], 2)
            self.assertFalse(self.calls)

    def test_duplicate_host_and_invalid_path_refused(self):
        self.inventory.write_text(json.dumps({"web_hosts": [self.entry, self.entry]}))
        self.assertEqual(self.invoke()[0], 2)
        self.entry["paths"] = ["//evil.test"]
        self.save()
        self.assertEqual(self.invoke()[0], 2)
        self.assertFalse(self.calls)

    def test_version_and_no_args_do_not_call_docker(self):
        for args in ([], ["--version"], ["-v"], ["-V"], ["--help"]):
            self.assertEqual(self.invoke(args)[0], 0)
        self.assertFalse(self.calls)

    def test_overlay_permission_and_rules_preserve_base_inventory(self):
        original = self.inventory.read_bytes()
        policy = self.root / "scan-policy.json"
        policy.write_text(json.dumps({"web_hosts": [{"host": "example.com", "active_scan_allowed": True,
                                                   "zap_rules": {"10020": {"action": "IGNORE", "reason": "Owner accepted", "expires": "2099-01-01"}}}]}))
        code, _ = self.invoke(self.args + ["--scan-policy", str(policy), "--mode", "full",
                                          "--ramesh-instruction", "Run full scan on example.com"])
        self.assertEqual(code, 0)
        self.assertEqual(self.inventory.read_bytes(), original)
        summary = json.loads(next((self.root / "reports").rglob("summary.json")).read_text())
        self.assertEqual(summary["scan_policy"], str(policy.resolve()))
        self.assertIs(summary["active_scan_allowed"], True)
        self.assertEqual(summary["rules"]["10020"]["action"], "IGNORE")

    def test_overlay_cannot_add_host_or_path_or_override_base_permission(self):
        policy = self.root / "scan-policy.json"
        for row in ({"host": "evil.test", "active_scan_allowed": True},
                    {"host": "example.com", "paths": ["/not-in-base"]},
                    {"host": "example.com", "active_scan_allowed": "true"}):
            policy.write_text(json.dumps({"web_hosts": [row]}))
            self.assertEqual(self.invoke(self.args + ["--scan-policy", str(policy)])[0], 2)
            self.assertFalse(self.calls)
        self.entry["active_scan_allowed"] = False
        self.save()
        policy.write_text(json.dumps({"web_hosts": [{"host": "example.com", "active_scan_allowed": True}]}))
        self.assertEqual(self.invoke(self.args + ["--scan-policy", str(policy)])[0], 2)
        self.assertFalse(self.calls)

    def test_default_policy_is_discovered_beside_inventory(self):
        policy = self.root / "websec-scans.local.json"
        policy.write_text(json.dumps({"web_hosts": [{"host": "example.com", "active_scan_allowed": True}]}))
        self.assertEqual(self.invoke(self.args + ["--mode", "full", "--ramesh-instruction", "Run full scan on example.com"])[0], 0)

    def test_explicit_missing_policy_refuses_before_docker(self):
        self.assertEqual(self.invoke(self.args + ["--scan-policy", str(self.root / "missing.json")])[0], 2)
        self.assertFalse(self.calls)

    def test_cleanup_cannot_remove_unrelated_container(self):
        def unrelated(args, **kw):
            if args[1] == "inspect":
                self.calls.append((args, kw))
                return subprocess.CompletedProcess(args, 0, (json.dumps({"org.iac.secscan": "another-run"}) + '|' + json.dumps("e" * 64)).encode(), b"")
            return self.docker(args, **kw)
        self.assertEqual(self.invoke(runner=unrelated)[0], 1)
        self.assertFalse(any(a[1] == "rm" for a, _ in self.calls))

    def test_report_for_another_host_cannot_pass(self):
        def wrong(args, **kw):
            result = self.docker(args, **kw)
            if args[1] == "run":
                path = next((self.root / "reports").rglob("report.json"))
                path.write_text(json.dumps({"site": [{"@name": "https://evil.test", "@host": "evil.test", "@port": "443", "@ssl": "true", "alerts": []}]}))
            return result
        self.assertEqual(self.invoke(runner=wrong)[0], 1)

    def test_cli_subprocess_uses_fake_docker_and_local_socket(self):
        fake = self.root / "docker"
        fake.write_text('#!' + sys.executable + '''
import json, os, pathlib, sys
p = pathlib.Path(__file__).with_suffix('.calls')
with p.open('a') as f: f.write(json.dumps({'args':sys.argv[1:], 'daemon':os.environ.get('DOCKER_HOST'), 'context':os.environ.get('DOCKER_CONTEXT')}) + '\\n')
a = sys.argv[1:]
if a[0] == 'image': print(json.dumps([__DIGEST__]))
elif a[0] == 'run':
    pathlib.Path(__file__).with_suffix('.token').write_text(a[a.index('--label')+1].split('=',1)[1])
    mount = next(x for x in a if x.endswith(':/zap/wrk:rw'))
    wrk = pathlib.Path(mount.removesuffix(':/zap/wrk:rw'))
    (wrk/'report.html').write_text('<html>fixture</html>')
    (wrk/'report.json').write_text(json.dumps({'site':[{'@host':'example.com','@name':'https://example.com','@port':'443','@ssl':'true','alerts':[]}]}))
elif a[0] == 'inspect': print(json.dumps({'org.iac.secscan':pathlib.Path(__file__).with_suffix('.token').read_text()}) + '|' + json.dumps('d'*64))
elif a[0] == 'cp': pathlib.Path(a[-1]).write_text('fixture ZAP application log')
'''.replace('__DIGEST__', repr(DIGEST)))
        fake.chmod(0o700)
        env = {"PATH": str(self.root) + ":/usr/bin:/bin", "HOME": str(self.root),
               "DOCKER_HOST": "ssh://must-not-use", "DOCKER_CONTEXT": "production"}
        result = subprocess.run([sys.executable, str(TOOL)] + self.args, env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        calls = [json.loads(line) for line in fake.with_suffix('.calls').read_text().splitlines()]
        self.assertEqual(len(calls), 7)
        self.assertTrue(all(c["daemon"] == "unix:///var/run/docker.sock" and c["context"] is None for c in calls))
        self.assertEqual(calls[-1]["args"], ["rm", "-f", "d" * 64])


if __name__ == "__main__":
    unittest.main()
