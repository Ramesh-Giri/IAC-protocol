---
name: web-dast-scan
description: Run an inventory-only ZAP passive baseline weekly and after web deploys, review expiring rule exceptions, and retain HTML/JSON evidence. API/full active scans require both per-host permission and Ramesh's literal instruction.
---

# Web baseline gate

Apply rule 62 alongside rule 41. Read the site's ignored `local/websec.local.json`, roster and deployment task; do not copy real hosts, paths, tokens or findings into tracked files. Research and this skill grant no permission to scan another host, run active tests, deploy, or change inventory.

The rule-41 inventory remains the sole authority for **hosts and paths**. The current `websec-check` rejects extra scan fields, so keep it unchanged and place optional per-host scan metadata in the ignored sibling `local/websec-scans.local.json`. The wrapper merges that policy overlay into the selected base inventory entry. The overlay may add only `active_scan_allowed` and `zap_rules` to an existing host: it cannot introduce a host, add paths, or override scan fields already present in the base. `--scan-policy <file>` selects an explicit overlay and fails if missing; otherwise the sibling file is optional. This separation preserves the original checker while reusing its target inventory and reason/expiry convention. Absent permission metadata means passive-only; absent rule metadata means no exceptions.

## Default workflow

After Ramesh approves the image download, the overseer can run:

```sh
docker --host unix:///var/run/docker.sock pull zaproxy/zap-stable:2.17.0
agentmail/bin/zap-scan '<exact-inventory-host>'
```

The wrapper validates all inventory entries before invoking Docker. Host arguments are exact lowercase DNS names, with no URL, credentials, port, wildcard or path. `--path` must exactly match a listed path. The default target is the first inventory path; all listed paths are seeded. ZAP then discovers URLs on that **same HTTPS host on port 443**: inventory paths are starting points, not a promise to crawl only those exact URLs. Obtain a narrower reviewed plan if some paths on the host must never be requested.

`zap-baseline.py` makes normal HTTP requests through a bounded traditional spider and runs passive rules; it does not run the active scanner. Even a passive baseline has traffic and can reach badly designed GET endpoints with side effects, so use the owning project's scan window. No Ajax spider, authentication context, supplied arbitrary hook, extra command options, add-on update or image download is enabled.

The local Docker tag is resolved to its digest and run with `--pull=never`, `-silent`, `--autooff`, generated inventory scope and global URL exclusions, a protected context, no published ports, and a unique run ownership label. Ramesh's Mac local socket is explicit; ambient remote Docker contexts are ignored. Only the private per-run report directory is mounted, as the host UID/GID. Required guard API failures stop before target access. All modes have a Network add-on rate limit of 1 request/second by default (operator may select 2), one spider/active worker, no spider form submissions, and a 30-minute wrapper timeout. The default spider duration is one minute (`--minutes` accepts 1–5); packaged readiness/passive waiting is bounded separately.

The generated access step disables automatic redirects; the scoped spider can discover allowed destinations. Global exclusions and spider/active exclusions reject other schemes, hosts and ports. These are ZAP application controls, not an OS network firewall. The first approved real run must verify the pinned image's guard APIs, scope behavior (including cross-host redirect/spec references), and rate control against owner-controlled fixtures before active production use. A failed guard or incomplete report is not permission to remove the guard.

## Reports and disposition

Reports go to `~/Work/Aureus/.agent-mail/attachments/zap/<host>/<UTC-date>/<unique-run>/`: `report.html`, `report.json`, `summary.json`, generated `rules.conf` and the original generated hook. Keep private response content and host inventory out of source control. Raw alerts remain available even when a rule is ignored for the gate.

Upstream packaged exit codes are 0=pass, 1=FAIL rule, 2=WARN rule, 3=execution trouble. The wrapper maps completed FAIL/WARN scans to exit 1 for review; missing/empty HTML, missing/invalid JSON, absent site evidence, timeouts and execution errors also fail. CLI/config refusal returns 2. Only a completed accepted scan returns 0. No arguments shows idle state; `--help` lists flags and `-v`, `-V`, `--version` report the wrapper version without Docker.

Attach HTML/JSON and the review disposition to the web deploy DONE and weekly evidence. Give each finding an owner, task and evidence; explicitly review warnings. A baseline complements `websec-check` and preview header contract tests; it does not replace them or establish absence of vulnerabilities in authenticated flows.

## Rules and active scans

Per-host `zap_rules` in the scan overlay maps numeric upstream rule IDs to `FAIL`, `WARN` or `IGNORE`, each with **reason + expiry**. For the documented overlay shape, read [the sanitized template](../../templates/websec-scans.example.json). It contains no paths: use the existing base inventory's paths, and replace the placeholder host/remove the example exception before use. Expiry is a UTC date, inclusive. Invalid/expired entries refuse the scan before Docker. Do not accept raw `.conf` overrides that evade reason/expiry review, blanket IGNORE rules, or unrecorded renewals.

Active scanning may change application data. Both controls are mandatory:

- The chosen host's merged inventory entry contains the literal JSON boolean `"active_scan_allowed": true` in its private scan-policy overlay (default absent/false).
- The operator explicitly selects `--mode api` or `--mode full` and passes `--ramesh-instruction` with Ramesh's actual literal instruction. The wrapper checks a nonempty value and records it; a string is an audit receipt, not proof of the speaker's identity. The operator must verify the source instruction and its host/window/mode before invocation.

```sh
agentmail/bin/zap-scan '<inventory-host>' --mode full \
  --ramesh-instruction '<copy Ramesh’s literal instruction for this host/window/mode>'
agentmail/bin/zap-scan '<inventory-host>' --mode api --api-path '/openapi.json' \
  --ramesh-instruction '<copy Ramesh’s literal instruction for this host/window/mode>'
```

API mode supports a remote OpenAPI document at an **exact inventoried path**. The generated guard fetches it without redirects, rejects external `$ref`/`$dynamicRef` values, rewrites root/path/operation servers to this HTTPS origin, and imports only that checked local copy. It also copies the image's API-Minimal policy into its temporary ZAP home; no policy source is added to IAC. The packaged `-O https://<inventory-host>` override remains enabled. Verify redirect/reference behavior in the approved fixture check; third-party definitions or off-inventory references are not allowed. SOAP, GraphQL, supplied local definitions and custom Automation Framework jobs require a separate reviewed extension. Full mode includes spidering and active scanning. Both modes keep the same required rate guard; never remove it to speed up a run.

The pinned upstream API script uses API-Minimal when its rules config is empty, but switches to Default Policy and enables its scanners when a nonempty rules map is supplied. Include that broader active-rule choice in the approved API scan plan; a rule's gate disposition does not itself authorize additional requests.

## Upstream reading

Read 2026-11-24: **ZAP v2.17.0, Apache-2.0**, separate Docker image `zaproxy/zap-stable:2.17.0`. Brief estimate ~1.17 GB arm64; operator pull output is authoritative for actual storage/transfer.

- [Versioned README](https://github.com/zaproxy/zaproxy/blob/v2.17.0/README.md), [stable Dockerfile](https://github.com/zaproxy/zaproxy/blob/v2.17.0/docker/Dockerfile-stable), [license](https://github.com/zaproxy/zaproxy/blob/v2.17.0/LICENSE).
- [v2.17.0 baseline source](https://github.com/zaproxy/zaproxy/blob/v2.17.0/docker/zap-baseline.py), [API source](https://github.com/zaproxy/zaproxy/blob/v2.17.0/docker/zap-api-scan.py), [full source](https://github.com/zaproxy/zaproxy/blob/v2.17.0/docker/zap-full-scan.py), [hook/config/scan helpers](https://github.com/zaproxy/zaproxy/blob/v2.17.0/docker/zap_common.py). These establish script flags, hook ordering, rules-file syntax, exit codes, and the normal widening of path targets to the host root.
- [Baseline documentation](https://www.zaproxy.org/docs/docker/baseline-scan/), [API documentation](https://www.zaproxy.org/docs/docker/api-scan/), [full scan documentation](https://www.zaproxy.org/docs/docker/full-scan/), [Automation Framework](https://www.zaproxy.org/docs/automate/automation-framework/). Live docs are explanatory, not pinned runtime inputs. Automation Framework offers YAML environments/jobs; this wrapper deliberately disables baseline's automatic switch to AF so the required Python guard hooks run.
- Network add-on sources separately inspected at `ec3f8f76bc1abaea50eeb9d36749f5496c814f37`: [rate-limit API](https://github.com/zaproxy/zap-extensions/blob/ec3f8f76bc1abaea50eeb9d36749f5496c814f37/addOns/network/src/main/java/org/zaproxy/addon/network/NetworkApi.java), [rate documentation](https://github.com/zaproxy/zap-extensions/blob/ec3f8f76bc1abaea50eeb9d36749f5496c814f37/addOns/network/src/main/javahelp/help/contents/options/ratelimit.html), [global exclusion settings](https://github.com/zaproxy/zap-extensions/blob/ec3f8f76bc1abaea50eeb9d36749f5496c814f37/addOns/network/src/main/java/org/zaproxy/addon/network/GlobalExclusionsOptions.java). Add-on versions vary independently of core; first real-run evidence must confirm compatibility with the pulled digest.

Original wrapper/hook code only; no upstream source vendored. Fake tests establish wrapper behavior, not effectiveness of every rule or the real image's network controls.
