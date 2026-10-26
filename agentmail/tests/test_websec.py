"""Exercise websec CLI, recorded protocol/header fixtures and fetch boundaries.

Loads the stdlib tool directly; all DNS, sockets and subprocess TLS probes are
mocked. unittest is the entry point; no external service or config is modified.
"""
from contextlib import redirect_stdout
from datetime import date
from importlib.util import module_from_spec, spec_from_loader
from importlib.machinery import SourceFileLoader
import io
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

TOOL = Path(__file__).resolve().parents[1] / "bin/websec-check"
spec = spec_from_loader("websec", SourceFileLoader("websec", str(TOOL)))
w = module_from_spec(spec)
spec.loader.exec_module(w)

# Recorded OpenSSL output shapes, sanitized to retain only handshake evidence.
OPENSSL = {
    "brief": "CONNECTION ESTABLISHED\nProtocol version: TLSv1.2\nCiphersuite: ECDHE-RSA-AES128-SHA\n",
    "session": "New, TLSv1.0, Cipher is AES128-SHA\n    Protocol  : TLSv1\n    Cipher    : AES128-SHA\n",
    "refused": "SSL routines:ssl3_read_bytes:tlsv1 alert protocol version:SSL alert number 70\nNew, (NONE), Cipher is (NONE)",
    "handshake": "SSL routines:ssl3_read_bytes:sslv3 alert handshake failure:SSL alert number 40",
    "local": "SSL routines:SSL_CTX_set_cipher_list:no cipher match",
    "empty": "CONNECTED(00000003)\nCipher is (NONE)\n",
}
GOOD_HEADERS = [
    ("Strict-Transport-Security", "max-age=31536000; includeSubDomains"),
    ("X-Frame-Options", "DENY"), ("X-Content-Type-Options", "nosniff"),
    ("Referrer-Policy", "strict-origin-when-cross-origin"),
    ("Content-Security-Policy", "default-src 'self'; frame-ancestors 'none'"),
]


class WebsecTests(unittest.TestCase):
    def test_recorded_openssl_parsing(self):
        for key, expected in (("brief", "accepted"), ("session", "accepted"),
                              ("refused", "refused"), ("handshake", "refused"),
                              ("local", "inconclusive"), ("empty", "inconclusive")):
            with self.subTest(key=key):
                self.assertEqual(w.openssl_result(OPENSSL[key])[0], expected)
        self.assertIn("ECDHE-RSA-AES128-SHA", w.openssl_result(OPENSSL["brief"])[1])

    def test_tls_probe_pins_ip_and_bounds_subprocess(self):
        with patch.object(w.subprocess, "run", return_value=subprocess.CompletedProcess([], 1, "", OPENSSL["refused"])) as run:
            self.assertEqual(w.tls_probe("example.com", "1.1.1.1", "-tls1", "ALL:@SECLEVEL=0")[0], "refused")
        args, kwargs = run.call_args
        self.assertIn("1.1.1.1:443", args[0])
        self.assertIn("example.com", args[0])
        self.assertEqual(kwargs["timeout"], w.TIMEOUT)
        with patch.object(w.subprocess, "run", side_effect=subprocess.TimeoutExpired("openssl", 10)):
            self.assertEqual(w.tls_probe("example.com", "1.1.1.1", "-tls1", "ALL")[0], "inconclusive")

    def test_headers_good_and_missing(self):
        self.assertTrue(all(r["status"] == "PASS" for r in w.header_checks("example.com/", 200, GOOD_HEADERS)))
        rows = {r["check"]: r for r in w.header_checks("example.com/404", 522, [])}
        for check in ("http-status", "hsts", "framing", "nosniff", "referrer-policy", "csp"):
            self.assertEqual(rows[check]["status"], "FAIL")

    def test_report_only_cannot_prevent_framing_and_localhost_is_blocked(self):
        headers = [("Content-Security-Policy-Report-Only", "frame-ancestors http://localhost:3000")]
        rows = {r["check"]: r for r in w.header_checks("example.com/", 200, headers)}
        self.assertEqual(rows["framing"]["status"], "FAIL")
        self.assertEqual(rows["csp"]["status"], "WARN")
        self.assertEqual(rows["frame-ancestors-public"]["status"], "FAIL")

    def test_hsts_duplicate_invalid_xfo_and_csp_wildcard(self):
        headers = [("Strict-Transport-Security", "max-age=10"), ("X-Frame-Options", "ALLOWALL"),
                   ("Content-Security-Policy", "frame-ancestors *")]
        rows = {r["check"]: r for r in w.header_checks("example.com/", 200, headers)}
        self.assertEqual(rows["framing"]["status"], "FAIL")
        self.assertEqual(rows["hsts"]["status"], "FAIL")
        headers = GOOD_HEADERS + [("Strict-Transport-Security", "max-age=1")]
        self.assertEqual({r["check"]: r["status"] for r in w.header_checks("example.com/", 200, headers)}["hsts"], "FAIL")

    def test_spf_dmarc_and_dkim(self):
        def statuses(spf, dmarc, **kwargs):
            return {r["check"]: r["status"] for r in w.mail_checks("example.com", spf, dmarc, ["10 mail.example.com."], [], **kwargs)}
        rows = statuses(["v=spf1 include:_spf.example.com ~all"], ["v=DMARC1; p=none"], dkim=["v=DKIM1; p=abcdef"])
        self.assertEqual(rows, dict(dmarc="WARN", spf="WARN", caa="WARN", dkim="PASS"))
        self.assertEqual(statuses(["v=spf1 ~all"], ["v=DMARC1; p=reject"])["spf"], "PASS")
        for spf in ([], ["v=spf1 +all"], ["v=spf1 -all", "v=spf1 ~all"], ["v=spf1 +all -all"]):
            self.assertEqual(statuses(spf, ["v=DMARC1; p=reject"])["spf"], "FAIL")
        for dmarc in ([], ["v=DMARC1; p=nope"], ["v=DMARC1; p=none; p=reject"], ["v=DMARC1; p=reject; pct=999"]):
            self.assertEqual(statuses(["v=spf1 -all"], dmarc)["dmarc"], "FAIL")
        self.assertEqual(statuses(["v=spf1 ~all"], ["v=DMARC1; p=reject; pct=0"])["spf"], "WARN")
        self.assertEqual(statuses(["v=spf1 -all"], ["v=DMARC1; p=reject"], dkim=["v=DKIM1; p="])["dkim"], "FAIL")

    def test_advertised_nonmail_domain_needs_protection_but_contact_still_fails(self):
        rows = {r["check"]: r["status"] for r in w.mail_checks("example.com", ["v=spf1 -all"], ["v=DMARC1; p=reject"], ["0 ."], [], True)}
        self.assertEqual(rows["nonmail-domain"], "PASS")
        self.assertEqual(rows["contact-mx"], "FAIL")

    def test_txt_split_and_escaped_dns_strings(self):
        self.assertEqual(w.decode_txt('"v=spf1 " "-all"'), "v=spf1 -all")
        self.assertEqual(w.decode_txt('"v=DKIM1; p=ab\\099d"'), "v=DKIM1; p=abcd")
        with self.assertRaises(ValueError):
            w.decode_txt('"unfinished')

    def test_expiring_exception_only_waives_accepted_cbc(self):
        exception = dict(reason="edge CBC setting unavailable", expires="2030-01-01")
        row = w.result("example.com", "tls12-cbc", "FAIL", "accepted: TLSv1.2 AES128-SHA")
        self.assertEqual(w.apply_exception(row, exception, date(2029, 1, 1))["status"], "WARN")
        self.assertEqual(w.apply_exception(row, exception, date(2030, 1, 2))["status"], "FAIL")
        self.assertEqual(w.apply_exception(dict(row, evidence="inconclusive: timeout"), exception, date(2029, 1, 1))["status"], "FAIL")

    def test_config_validation_precedes_network(self):
        for config in ({}, {"web_hosts": "example.com"}, {"web_hosts": [{"host": "https://example.com"}]},
                       {"web_hosts": [{"host": "example.com", "paths": ["//evil.example.com"]}]},
                       {"web_hosts": [{"host": "example.com", "exceptions": {"tls10": {}}}]},
                       {"web_hosts": [{"host": "example.com", "exceptions": {"tls12-cbc": {"reason": "", "expires": "tomorrow"}}}]}):
            with self.subTest(config=config), self.assertRaises((ValueError, TypeError)):
                w.validate_config(config)

    def test_ssrf_addresses_and_schemes_blocked_before_connect(self):
        for addr in ("127.0.0.1", "169.254.169.254", "10.0.0.1", "100.64.0.1", "224.0.0.1", "::1", "fc00::1", "fe80::1", "::ffff:127.0.0.1"):
            with self.subTest(addr=addr), self.assertRaises(ValueError):
                w.public_ip(addr)
        for host in ("file:///etc/passwd", "http://example.com", "gopher://example.com", "user:secret@example.com", "localhost"):
            with self.subTest(host=host), self.assertRaises(ValueError):
                w.domain(host)
        with patch.object(w.socket, "create_connection") as connect:
            with self.assertRaises(ValueError):
                w.PublicHTTPS().request("example.com", "/", "10.0.0.1")
            connect.assert_not_called()

    def test_resolve_rejects_mixed_private_dns_answers(self):
        with patch.object(w.PublicHTTPS, "dns", side_effect=[["1.1.1.1", "127.0.0.1"], []]):
            with self.assertRaises(ValueError):
                w.PublicHTTPS().resolve("example.com")

    def request_fixture(self, response, limit=1000):
        class FakeSocket:
            def __init__(self):
                self.body = io.BytesIO(response)
            def recv(self, size):
                return self.body.read(size)
            def settimeout(self, value):
                pass
            def sendall(self, data):
                self.sent = data
            def getpeercert(self):
                return {"notAfter": "Jan  1 00:00:00 2035 GMT"}
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        sock = FakeSocket()
        context = unittest.mock.Mock()
        context.wrap_socket.return_value = sock
        with patch.object(w.socket, "create_connection", return_value=sock) as connect, patch.object(w.ssl, "create_default_context", return_value=context):
            result = w.PublicHTTPS().request("example.com", "/", "1.1.1.1", limit=limit)
        self.assertEqual(connect.call_args.args[0], ("1.1.1.1", 443))
        self.assertEqual(context.wrap_socket.call_args.kwargs["server_hostname"], "example.com")
        self.assertNotIn(b"Authorization", sock.sent)
        return result

    def test_redirect_to_private_is_not_followed(self):
        status, headers, body, _ = self.request_fixture(b"HTTP/1.1 302 Found\r\nLocation: https://127.0.0.1/\r\nContent-Length: 0\r\n\r\n")
        self.assertEqual(status, 302)
        self.assertEqual(body, b"")

    def test_response_cap_and_chunked_body(self):
        with self.assertRaisesRegex(ValueError, "exceeds"):
            self.request_fixture(b"HTTP/1.1 200 OK\r\nContent-Length: 2000\r\n\r\n", limit=100)
        with self.assertRaisesRegex(ValueError, "exceeds"):
            self.request_fixture(b"HTTP/1.1 200 OK\r\n\r\n" + b"x" * 101, limit=100)
        self.assertEqual(self.request_fixture(b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n3\r\nabc\r\n0\r\n\r\n")[2], b"abc")

    def test_total_timeout_applies_to_slow_headers(self):
        reader = w.DeadlineReader(unittest.mock.Mock(), 10)
        with patch.object(w.time, "monotonic", return_value=11), self.assertRaises(TimeoutError):
            reader.readline()

    def test_dns_underscore_questions_and_txt_reassembly(self):
        answer = {"Status": 0, "Answer": [{"type": 16, "data": '"v=DMARC1; " "p=reject"'}]}
        with patch.object(w.PublicHTTPS, "request", return_value=(200, [], json.dumps(answer).encode(), {})) as request:
            self.assertEqual(w.PublicHTTPS().dns("_dmarc.example.com", "TXT"), ["v=DMARC1; p=reject"])
        self.assertIn("1.1.1.1", request.call_args.args)

    def test_paths_plus_random_404_and_cert_expiry(self):
        client = unittest.mock.Mock()
        client.resolve.return_value = ["1.1.1.1"]
        client.request.return_value = (404, GOOD_HEADERS, b"", {"notAfter": "Jan  1 00:00:00 2035 GMT"})
        with patch.object(w, "tls_probe", return_value=("refused", "peer alert")):
            rows = w.check_web({"host": "example.com", "paths": ["/", "/account"]}, client, date.today())
        self.assertEqual(client.request.call_count, 3)
        self.assertTrue(client.request.call_args.args[1].startswith("/.well-known/websec-missing-"))
        self.assertTrue(all(row["status"] == "PASS" for row in rows))
        client.request.return_value = (200, GOOD_HEADERS, b"", {"notAfter": "Jan  1 00:00:00 2020 GMT"})
        with patch.object(w, "tls_probe", return_value=("refused", "peer alert")):
            self.assertTrue(any(r["check"] == "certificate" and r["status"] == "FAIL" for r in w.check_web({"host": "example.com"}, client, date.today())))

    def test_cli_json_failure_and_success_exit(self):
        with tempfile.TemporaryDirectory() as temp:
            config = Path(temp) / "config.json"
            config.write_text(json.dumps({"web_hosts": [{"host": "example.com"}]}))
            for status, expected in (("PASS", 0), ("WARN", 0), ("FAIL", 1)):
                output = io.StringIO()
                with patch.object(w, "run_checks", return_value=[w.result("example.com", "test", status, "fixture")]), redirect_stdout(output):
                    self.assertEqual(w.main(["--config", str(config), "--json"]), expected)
                self.assertEqual(json.loads(output.getvalue())["summary"][status], 1)
        command = subprocess.run([sys.executable, str(TOOL), "--typo", "--json"], capture_output=True, text=True)
        self.assertEqual(command.returncode, 2)
        self.assertEqual(json.loads(command.stdout)["summary"]["FAIL"], 1)


if __name__ == "__main__":
    unittest.main()
