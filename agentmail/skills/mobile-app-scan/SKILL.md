---
name: mobile-app-scan
description: Run the local MobSF Android release gate before a store upload, review high and warning findings, and attach private JSON/PDF evidence. Use the same-commit release APK when AAB analysis fails; excludes iOS and online scanners.
---

# Android release scan

Apply rule 61 before every store upload. Read the roster and release task first: this skill grants no permission to build, download images, upload to a store, fix application code, or use an online scanner.
The release owner supplies the artifact; on Ramesh's site only the overseer schedules the heavy build.

Link the release scan and reviewed findings to the project's [security-privacy-baseline](../security-privacy-baseline/SKILL.md) under rule 64.
Also verify legacy-crypto removal, Firebase/Google key restrictions and named trackers in the privacy policy; MobSF alone does not close those rows or the full checklist.

## Run and review

1. Record the release commit, package, build name/number, and APK/AAB SHA-256 in the release evidence. Prefer the **release APK from the same commit, flavor, defines, signing setup and version as the store AAB**. A dev APK is supplementary evidence, not the release gate.
   On 2026-11-24 the overseer's real MobSF 4.6.9 run accepted an AAB but failed at `/api/v1/scan`. Upload support does not establish successful AAB analysis. Do not silently substitute a dev APK, build another app, or call a failed scan clean.
2. After Ramesh approves the download, the overseer runs the pinned pull below. The wrapper never pulls, installs, starts Docker Desktop, changes restart policies, or uses a remote Docker context.

   ```sh
   docker --host unix:///var/run/docker.sock pull opensecurity/mobile-security-framework-mobsf:v4.6.9
   agentmail/bin/mobsf-scan /path/to/same-commit-release.apk --app app --release '0.0.19+52'
   ```

3. The wrapper resolves that local tag to a repository digest and runs the digest with `--pull=never`, a unique name and ownership label, a per-run API key, disabled container logging, and **`--network none`**. No host ports or directories are exposed. A busy host port 8000 cannot receive a file or key: all HTTP runs through `docker exec` to `127.0.0.1:8000` *inside the verified full container ID*. Identity, image, name, network mode, empty port mappings, Docker health, and the image's `/login/` readiness contract must pass before upload. This deliberately replaces the upstream published-port example; never upload to an arbitrary localhost service.
4. REST sequence: multipart `upload` → hash → `scan` → `report_json` → `download_pdf`. An HTTP failure, JSON `error`, invalid hash, incomplete Android report, mismatched report/artifact SHA-256, or missing/non-PDF report fails the gate. Cleanup checks the run's ownership label before removing its container; no unrelated containers are stopped, restarted or removed. The completed summary is published only after verified cleanup.
5. Read `report.json`, `report.pdf`, and `summary.json` in `~/Work/Aureus/.agent-mail/attachments/mobsf/<app>-<release>/`. Reruns need a distinct release/run label; existing evidence is never overwritten. Summary includes artifact hash, package/version, image digest, high/warning findings and differences from the most recently completed report for that app: new, changed and resolved IDs. A first run has no previous baseline; it does not imply improvement. Inspect the full reports for permissions, embedded secrets, trackers and native/Flutter coverage beyond the summarized severity findings.
6. Unaccepted high/warning findings return exit 1 and require an owner and evidence. Exit 0 means the automated severity gate passed, not that the app is secure. Validate package/version and commit provenance separately. Attach the reports and review disposition to release DONE before any store upload. Failed or incomplete analysis, missing required evidence, or an unreviewed warning cannot support DONE.

## Suppressions

Keep a private JSON file outside tracked source. `--suppressions /path/to/mobsf-suppressions.local.json` accepts an array:

```json
[
  {"id":"manifest:example_rule","reason":"Named owner reviewed this exact release condition; task reference","expires":"2026-12-15"}
]
```

Use the exact ID from `summary.json`; code IDs use `code:<upstream-rule>`. No wildcard suppressions. Every entry needs a nonempty reason and UTC expiry (`YYYY-MM-DD`, inclusive). Invalid, duplicate or expired entries stop before Docker. Accepted findings remain in raw reports and the summary with their reason/expiry; suppression changes do not rewrite evidence. Review renewals with the owning human/task authority. No API key is retained in attachments or passed in command arguments.

## Upstream reading and limits

Read 2026-11-24: **MobSF v4.6.9, GPL-3.0-only**, separate Docker program `opensecurity/mobile-security-framework-mobsf:v4.6.9`. The download brief estimates ~0.73 GB for arm64; actual transfer/storage is the operator's pull result, not a wrapper guarantee.

- [Versioned README and Docker quickstart](https://github.com/MobSF/Mobile-Security-Framework-MobSF/blob/v4.6.9/README.md), [Dockerfile and healthcheck](https://github.com/MobSF/Mobile-Security-Framework-MobSF/blob/v4.6.9/Dockerfile), [license](https://github.com/MobSF/Mobile-Security-Framework-MobSF/blob/v4.6.9/LICENSE).
- [Running MobSF with Docker](https://mobsf.github.io/docs/#/running_mobsf_docker), [Docker options](https://mobsf.github.io/docs/#/docker_options), [REST API documentation entry](https://mobsf.github.io/docs/#/extras?id=rest-api). These live docs are not versioned; pinned implementation below controls this wrapper. The complete API reference is served at `/api_docs` by MobSF itself; no localhost reference from an unrelated service is trusted.
- [v4.6.9 API reference](https://github.com/MobSF/Mobile-Security-Framework-MobSF/blob/v4.6.9/mobsf/templates/general/apidocs.html), [REST handlers: upload, scan, JSON and PDF](https://github.com/MobSF/Mobile-Security-Framework-MobSF/blob/v4.6.9/mobsf/MobSF/views/api/api_static_analysis.py), [API authentication](https://github.com/MobSF/Mobile-Security-Framework-MobSF/blob/v4.6.9/mobsf/MobSF/views/api/api_middleware.py), [per-run environment key](https://github.com/MobSF/Mobile-Security-Framework-MobSF/blob/v4.6.9/mobsf/MobSF/init.py), [settings including AAB and outbound integrations](https://github.com/MobSF/Mobile-Security-Framework-MobSF/blob/v4.6.9/mobsf/MobSF/settings.py), [Android report shape](https://github.com/MobSF/Mobile-Security-Framework-MobSF/blob/v4.6.9/mobsf/StaticAnalyzer/views/android/db_interaction.py).

No GPL source is copied into IAC; the wrapper's transport and summarization are original. Network isolation disables reputation/feed lookups and other network-dependent enrichment. If bundled tools or PDF generation fail offline, record failure and escalate; do not enable network access or an online scanner to manufacture a pass. Fake-based wrapper tests do not qualify the real image; the overseer owns the first approved real run.
