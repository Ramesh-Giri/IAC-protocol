<!-- Documents websec-check for operators and CI; config is private, probes are read-only, and no scheduler is installed. -->
# Public web and mail security checks

`bin/websec-check` reads a local inventory, performs bounded read-only public probes, and prints one PASS/WARN/FAIL line per check with observed evidence.
It requires Python 3.9+ and an OpenSSL executable capable of offering the requested protocols and ciphers.
It installs nothing and never changes a site or sends mail.
Rule [41](OPERATIONAL_RULES.md#41-check-public-web-and-mail-security-regularly) defines the session-start, weekly and release checks; arrange these in your site's existing operating schedule.

From the workspace root:

```sh
cp local/websec.local.example.json local/websec.local.json
# Edit the private copy with your actual inventory and remove the example exception.
agentmail/bin/websec-check
agentmail/bin/websec-check --config local/websec.local.json --json
python3 -m unittest agentmail.tests.test_websec -v
```

The default config path is relative to the toolkit repository, independent of the current working directory.
Only `local/README.md` and `local/websec.local.example.json` are admitted by `.gitignore`; the actual inventory and results stay private.
`web_hosts` and `mail_domains` are arrays, and either can be omitted when the other is populated.
An empty inventory is a usage failure, never a pass.
Unknown fields/flags fail before any network operation.

A web entry uses `host` (DNS name without scheme or port), optional `paths` (defaults to `["/"]`), and optional `exceptions`.
Paths may include query parameters but must be ASCII absolute paths; never include secrets, tokens or authenticated URLs.
Always list sensitive landing routes, login routes and known error paths.
Every run also checks a new random `/.well-known/websec-missing-<token>` path.
A single-page application may return 200 for that path; the checker still checks the actual response headers and status.
Redirects are not followed: their headers are checked, a WARN is emitted, and the destination must be listed separately.
The HTTP GET response body is streamed only to enforce a 2 MiB limit and is never printed.

Web checks cover refusal of TLS 1.0/1.1, TLS 1.2 CBC-SHA refusal, verified certificate hostname/chain and more than 21 days remaining, HSTS of at least 31536000 seconds, framing protection, nosniff, Referrer-Policy, CSP, local framing sources and HTTP 5xx outages.
Framing requires an enforced CSP `frame-ancestors` directive with a nonempty source list without an unrestricted `*`, or X-Frame-Options DENY/SAMEORIGIN.
Report-only CSP is WARN and cannot satisfy framing protection.
Duplicate singleton headers fail the relevant check rather than guessing browser behavior.
Legacy/CBC probes use OpenSSL with `@SECLEVEL=0`; unsupported local features, timeouts and ambiguous failures are FAIL/inconclusive, never proof of remote refusal.
The CBC offer covers AES-CBC SHA1/SHA256/SHA384 suites with RSA, DHE-RSA, ECDHE-RSA and ECDHE-ECDSA authentication where supported locally.
A negotiated version and exact cipher are printed on acceptance; explicit peer protocol/handshake/security alerts establish refusal.
This is a sampled baseline check, not exhaustive TLS cipher enumeration or browser policy validation.

An exception is scoped to a web host and the single `tls12-cbc` check:

```json
{"tls12-cbc": {"reason": "Managed edge does not expose a CBC control; owner reviewed", "expires": "2027-01-01"}}
```

A current exception downgrades observed CBC acceptance to WARN, retaining the cipher, reason and expiry in evidence.
It cannot waive an inconclusive probe, legacy TLS, certificate failures or header failures.
Expiry is inclusive through the configured date in UTC; an expired exception is FAIL even if the edge now refuses CBC, prompting removal or review.
Do not copy the illustrative example exception as an accepted site risk.

A mail entry uses `domain`, optional `dkim_selector` (a single DNS label), and `advertised_contacts` (boolean, default false).
SPF must contain exactly one SPF record ending in `-all` or `~all`, with no earlier `all` mechanism.
Softfail is WARN when DMARC is not fully enforcing.
DMARC is required; `p=none` and partial `pct` enforcement are WARN, while missing/invalid/multiple policies fail.
A configured DKIM selector must have a single nonempty public key record; this does not verify actual outbound signatures or alignment.
Missing CAA is WARN; CAA presence is checked at the exact configured name, without inherited-parent policy evaluation.
For advertised contacts, missing or null MX is FAIL; the domain must additionally publish exactly `v=spf1 -all` and full `p=reject` to prevent spoofing while non-mailing.
Those defensive records do not repair a nonexistent mailbox.
Even an MX PASS requires a separate owner delivery test of each product contact address; the checker does not issue SMTP probes or send email.
SPF include expansion, syntax/lookup-budget validation, DMARC report delivery and mailbox existence are outside this baseline.

DNS uses the [Cloudflare JSON DoH API](https://developers.cloudflare.com/1.1.1.1/encryption/dns-over-https/make-api-requests/dns-json/) at `https://cloudflare-dns.com/dns-query`, bootstrapped to its public `1.1.1.1` address with hostname/chain validation.
A/AAAA answers are checked for public addressing before any web connection, and the selected IP is pinned for HTTPS and [OpenSSL probes](https://docs.openssl.org/master/man1/openssl-s_client/).
The checker rejects private, loopback, metadata, link-local, CGNAT, multicast, reserved and IPv4-mapped destinations, and refuses mixed public/private DNS answers.
It never forwards cookies or authorization and never follows redirects, including redirects to private IPs.
Each HTTPS request has a 10-second total deadline, including slow header/body reads; subprocess probes also have a 10-second timeout.
DoH responses have a 256 KiB cap.
Fetch audit lines on stderr identify the caller, host, path without query, pinned IP and result; they never include response bodies or credentials.
One resolved public IP per web host is sampled, so results do not qualify every edge region or address.
Network, trust-store or resolver failures remain visible FAIL results.

Exit codes are 0 for no FAILs (WARNs may remain), 1 for observed FAILs/incomplete checks, and 2 for config/usage errors.
`--json` emits `checks` with `target`, `check`, `status`, `evidence`, plus PASS/WARN/FAIL summary counts.
`--help` and `--version` do not access the network.
Preserve raw results locally, turn each FAIL into an owned task and explicitly review WARNs before claiming a release complete.

## Header contract in each web repository

Keep the header contract in the web project's own CI, so a regression is caught on its deployed preview before release.
The following workflow assumes the project vendors the reviewed `agentmail/bin/websec-check` at `tools/websec-check` and its deployment job exposes an HTTPS URL through `needs.deploy-preview.outputs.url`.
Adapt that dependency and route list to the project; commit the resulting contract to that repository.
No access token is forwarded to the preview.
This tests the actual unauthenticated GET response, including errors, rather than checking source configuration text.
For authenticated routes, add a separate project-owned integration test with controlled fixture credentials.

```yaml
header-contract:
  needs: deploy-preview
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - name: Assert deployed preview headers
      env:
        PREVIEW_URL: ${{ needs.deploy-preview.outputs.url }}
      run: |
        python3 - <<'PY'
        import os, runpy, secrets
        from urllib.parse import urlsplit
        w = runpy.run_path('tools/websec-check')
        url = urlsplit(os.environ['PREVIEW_URL'])
        assert url.scheme == 'https' and url.hostname and url.port in (None, 443)
        assert not url.username and not url.password and not url.query and not url.fragment
        host = w['domain'](url.hostname)
        client = w['PublicHTTPS']()
        ip = client.resolve(host)[0]
        rows = []
        routes = ['/', '/account', '/.well-known/websec-missing-' + secrets.token_hex(12)]
        for route in routes:
            status, headers, _, _ = client.request(host, route, ip)
            rows.extend(w['header_checks'](host + route, status, headers))
        raise SystemExit(w['emit'](rows, False))
        PY
```

The offline tests record sanitized OpenSSL output formats and representative header/DNS policy fixtures inline in `tests/test_websec.py`.
They also exercise pinned-IP requests, redirect refusal, body caps, deadlines, config validation, exceptions and CLI exit codes without network access.
