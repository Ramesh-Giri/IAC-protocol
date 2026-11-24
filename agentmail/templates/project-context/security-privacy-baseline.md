# {{PROJECT_NAME}} - Security and Privacy Baseline

## Project and review scope

- Product, platforms and data flows: {{PLATFORMS_DATA_AND_THIRD_PARTIES}}
- Legal entity, establishment and markets: {{LEGAL_ENTITY_AND_MARKETS}}
- Product owner / technical owner / release owner: {{NAMED_DECISION_OWNERS}}
- Reviewed commit, release artifact, environment and UTC date: {{REVIEWED_RELEASE_AND_DATE}}
- Service deployment and rollback runbooks: {{SERVICE_RUNBOOK_REFERENCES}}

At setup, copy this file to `PROJECT_ROOT/context/security-privacy-baseline.md`, even when the optional six-file context is declined.
Preserve an existing baseline and review changes instead of overwriting it.
Record unknown facts as Open; creating this checklist does not mean the application is implemented.
Use the IAC **security-privacy-baseline** skill and operational rule 64.

## How to fill and decide

Keep every item and stable ID.
Split a row into linked subchecks if needed; the row cannot PASS until all applicable subchecks pass.
Fill the owner with a named accountable person/seat.
Risk is **Critical / High / Medium / Low**, with a short impact rationale; **Unrated** means triage is still required.

| Status | Required record |
| --- | --- |
| PASS | Dated evidence for the reviewed source/artifact/environment; all applicable parts verified. |
| FAIL | Missing, failed, incomplete or stale verification; record the gap, risk, owner and remediation task. The initial rows are intentionally unverified. |
| NA | Explain why the feature/control does not apply, cite the inspected scope, name the reviewer and give a review expiry date. Recheck when scope changes. |
| ACCEPTED | Preserve the failure and risk; link the accepting authority's explicit decision, reason, compensating controls, owner, remediation task and UTC expiry date. Never infer acceptance from a scanner suppression. |

Use `YYYY-MM-DD` UTC expiry dates, valid through that date.
Expired or unsupported NA/ACCEPTED records return to FAIL.
PASS is not permanent: review it for every release and after relevant changes or a security report.
An applicable R01–R20 PASS requires both implementation/configuration evidence and a named regression test with command, expected result and actual result.
For a provider-owned edge control, retain operator-supplied configuration or provider evidence and a bounded local/approved-fixture regression contract; if decisive evidence is unavailable, keep FAIL rather than inventing a test pass.

Every FAIL becomes a tracked task.
A **High or Critical FAIL blocks launch and release unless Ramesh explicitly accepts it with reason and expiry**.
Unrated failures remain blocked pending triage, so leaving risk blank cannot evade the gate.
Lower-risk failures remain visible with owners and due dates; stricter project, legal or scanner gates still apply.
Acceptance records risk, not legal compliance, and cannot waive a legal obligation or a failed scan.

Keep secrets, personal data, raw requests, private host inventory and scan reports in the approved private evidence store; link safe references here.
This checklist authorizes no scanning, cloud operation, deployment or fix.

## Privacy and legal checklist - 26 items

This is a planning checklist, **not legal advice**.
Start the applicability review with Nepal, India, EU/UK and US markets and a company established in Germany; replace that planning scope with verified project facts above.
**Ask a lawyer** on legal-only decisions: applicability, lawful bases, age thresholds/exceptions, notices, transfers/processor terms, rights, retention exceptions, breach duties, consumer terms and content/AI duties.
Do not apply one market's threshold or deadline to every user.
These defaults are project safeguards, not a statement that all laws require identical UX.

| Item / requirement | Risk | Status / reason / expiry | Evidence to supply | Owner |
| --- | --- | --- | --- | --- |
| P01 Age gate: where sign-up exists, collect DOB before account creation for the age decision; minimize access/retention and retain only the age result where feasible. **Ask a lawyer** about necessity and local design. | Unrated | FAIL - not verified | Sign-up flow and age-boundary tests; data inventory. | Assign |
| P02 Block under-18 users in the India/DPDP flow and under-13 users in the US/COPPA flow, or use verified parental consent before covered processing. **Ask a lawyer** about applicability, effective dates, exceptions and EU/UK/local thresholds. | Unrated | FAIL - not verified | Approved market/age matrix; blocked and parental-consent flow tests. | Assign |
| P03 Keep tracking, profiling and targeted advertising off for children; age/consent changes cannot silently re-enable them. **Ask a lawyer** about the applicable child-protection rules. | Unrated | FAIL - not verified | SDK/config inventory and child-account network/consent tests. | Assign |
| P04 Provide a readable, accurate privacy policy at sign-up and in the footer or platform equivalent. **Ask a lawyer** to review controller identity, purposes, rights, processors and international transfers. | Unrated | FAIL - not verified | Published notice/version, entrypoint links and legal review. | Assign |
| P05 Obtain separate choices for each consent-based purpose, with no pre-ticked boxes or bundled optional consent. **Ask a lawyer** to distinguish consent from other lawful bases. | Unrated | FAIL - not verified | Consent screen, purpose records and default-state tests. | Assign |
| P06 Make withdrawal as easy as giving consent and stop the relevant future processing, including third-party collection. **Ask a lawyer** about legal effects and record retention. | Unrated | FAIL - not verified | Withdraw/reload/cross-device tests and processor propagation evidence. | Assign |
| P07 Provide US do-not-sell/share opt-out and applicable preference-signal handling where required. **Ask a lawyer** to identify applicable states and processing. | Unrated | FAIL - not verified | Applicability decision and end-to-end opt-out evidence. | Assign |
| P08 Inventory every third-party domain and SDK: purpose, data sent, trigger, recipient, retention and owner; include fonts, embeds, analytics, chat and AI. | Unrated | FAIL - not verified | Dependency inventory and network evidence before/after consent. | Assign |
| P09 Self-host fonts; no requests to fonts.googleapis.com or fonts.gstatic.com, including indirect CSS imports. | Unrated | FAIL - not verified | Asset/import inspection and clean-session network test. | Assign |
| P10 Load external embeds only after the required click/consent; previews must not preconnect or fetch the third party early. | Unrated | FAIL - not verified | Pre-click and post-consent request traces with safe redaction. | Assign |
| P11 Where non-essential trackers exist, block them until consent; make Reject as accessible and easy as Accept, with persistent choices. **Ask a lawyer** about local cookie/consent requirements. | Unrated | FAIL - not verified | Fresh-session Accept/Reject/withdraw tests, including SDK startup. | Assign |
| P12 Leave session replay and heatmaps off by default; any approved activation requires appropriate consent and masked inputs. Never capture password, payment or identity-document fields. | Unrated | FAIL - not verified | Default config, masking tests and sanitized capture inspection. | Assign |
| P13 Disclose chat widgets and form capture, and gate non-essential collection on consent before loading or capturing keystrokes. **Ask a lawyer** on lawful basis and disclosures. | Unrated | FAIL - not verified | Widget/form inventory and pre-consent network tests. | Assign |
| P14 Marketing email includes a working unsubscribe and valid postal address; US opt-outs are honored within 10 business days. **Ask a lawyer** about applicable email laws and any shorter duties. | Unrated | FAIL - not verified | Sample message, unsubscribe delivery test and suppression timing record. | Assign |
| P15 Separate marketing from transactional email and require marketing opt-in as the project default. **Ask a lawyer** about message classification and local consent rules. | Unrated | FAIL - not verified | Separate templates/lists, opt-in proof and transactional-only test. | Assign |
| P16 Keep secrets out of frontend bundles, Git/history and public environment variables; rotate any exposed secret instead of merely deleting it. | Unrated | FAIL - not verified | Source/build secret checks and private remediation reference if needed. | Assign |
| P17 Deny unauthorized database access and user-file bucket access; no open rules or public user uploads. | Unrated | FAIL - not verified | Rules/policy review and cross-user/unauthenticated deny tests. | Assign |
| P18 Use strong password hashing and HTTPS, rate-limit sign-in/sign-up/reset, and validate input at every trusted boundary. | Unrated | FAIL - not verified | Auth/validation tests and configuration; link R02/R06/R11 and W08. | Assign |
| P19 Return safe errors and keep personal data, secrets and stack traces out of user-visible errors and routine logs. | Unrated | FAIL - not verified | Error-path tests, logging/redaction config and sanitized samples. | Assign |
| P20 Provide authenticated data export and a documented rights-request route. **Ask a lawyer** about scope, identity checks and response deadlines. | Unrated | FAIL - not verified | Own-user export/other-user denial tests and legal scope decision. | Assign |
| P21 Account deletion removes data from active stores and third parties; backups have a bounded deletion/expiry process and restores reapply deletion. **Ask a lawyer** about justified holds and disclosures. | Unrated | FAIL - not verified | Deletion/processor receipts, backup schedule and restore-deletion test. | Assign |
| P22 Set and implement retention limits per data class, including logs, uploads, consent records and backups. **Ask a lawyer** about required retention and deletion exceptions. | Unrated | FAIL - not verified | Data schedule, deletion jobs and expiry tests. | Assign |
| P23 Maintain a written breach response plan with contacts, triage and notification evidence. **Ask a lawyer** about GDPR's qualified 72-hour authority deadline, user notices and DPDP Board + affected-user duties/effective dates. | Unrated | FAIL - not verified | Dated tabletop, contact tree and jurisdiction/deadline decision. | Assign |
| P24 Show total price, billing period and auto-renewal before purchase; cancellation is as easy as subscription. Keep card data solely with the payment provider. **Ask a lawyer** about consumer terms, refunds and market rules. | Unrated | FAIL - not verified | Checkout/cancel tests, terms review and payment data-flow evidence. | Assign |
| P25 For uploads/user content, provide usage terms, a report-content route and copyright-takedown handling. **Ask a lawyer** about applicable liability, notices and procedures. | Unrated | FAIL - not verified | Published terms, tested reporting path and takedown owner/runbook. | Assign |
| P26 Label AI-generated content; disclose personal data sent to AI providers and check provider retention/training settings. **Ask a lawyer** about transparency, lawful basis and processor/transfer terms. | Unrated | FAIL - not verified | Labels, data-flow notice, provider settings/terms and retention tests. | Assign |

## Secure coding - R1–R20

IDs below use zero padding (R01 is R1).
Verify each applicable requirement with evidence **and a regression test**.
A scanner result alone is insufficient.
Use bounded local fixtures; never send a reset flood, parser attack, brute force or other availability test to a live/shared service under this checklist.

| Item / requirement | Risk | Status / reason / expiry | Evidence and regression test to supply | Owner |
| --- | --- | --- | --- | --- |
| R01 Bound HTTP/2 stream-reset work at the edge; retain supported flood mitigations, limits and patch ownership. | Unrated | FAIL - not verified | Edge/provider evidence; bounded isolated reset-budget regression with resource limits. | Assign |
| R02 Derive client IP only through the trusted proxy chain; client-supplied X-Forwarded-For cannot control rate-limit keys or trusted logs. | Unrated | FAIL - not verified | Proxy trust config; spoofed-header test preserves the real client identity and limit. | Assign |
| R03 For SAML/SSO, verify the signature on the exact assertion element consumed, and check audience, recipient and expiry. | Unrated | FAIL - not verified | SSO validation path; wrapping, unsigned-element and wrong/expired-claim rejection tests. | Assign |
| R04 Link accounts on the immutable provider subject plus issuer/provider namespace; email may assist only when verified and authoritative, never as an untrusted merge key. | Unrated | FAIL - not verified | Linking code; unverified/reassigned-email and different-subject takeover rejection tests. | Assign |
| R05 Bound GraphQL aliases, batching, depth/complexity and aggregate work; apply authorization and rate budgets to every operation. | Unrated | FAIL - not verified | Query budgets; bounded alias/batch limit and mixed-authorization tests. | Assign |
| R06 Make one-time codes single-use, short-lived, attempt-limited and bound to the intended user/session and purpose; consume atomically. | Unrated | FAIL - not verified | Token lifecycle; replay/race, expiry, attempt-limit and cross-session rejection tests. | Assign |
| R07 Avoid catastrophic-backtracking regexes on user input; bound input length and execution work. | Unrated | FAIL - not verified | Regex/input review; worst-case local fixture completes within an explicit resource budget. | Assign |
| R08 Pin JWT algorithms and key types; reject none and public-key-as-HMAC confusion; verify issuer, audience and expiry. | Unrated | FAIL - not verified | Verifier config; none/wrong-algorithm/wrong-key/claim rejection tests. | Assign |
| R09 Reject ambiguous HTTP framing across every proxy hop, including Content-Length/Transfer-Encoding disagreement; do not forward mismatched interpretations. | Unrated | FAIL - not verified | Proxy parser/config evidence; isolated conflicting-framing rejection contract. | Assign |
| R10 Keep per-user and unkeyed-header-dependent responses out of public/shared caches; key or bypass correctly at every cache layer. | Unrated | FAIL - not verified | Cache policy; two-user and varied-header fixtures never receive another response variant. | Assign |
| R11 Never silently truncate passwords or secrets in hashing; handle bcrypt's 72-byte boundary explicitly with a suitable scheme. | Unrated | FAIL - not verified | Hashing policy; distinct long and multibyte inputs beyond 72 bytes cannot authenticate interchangeably. | Assign |
| R12 Enforce row-level authorization through views, aggregates and administrative endpoints as well as direct queries. | Unrated | FAIL - not verified | Data access policies; two-tenant denial tests for every alternate access path. | Assign |
| R13 Generate all security tokens using a CSPRNG, never Math.random or a non-secure Random implementation. | Unrated | FAIL - not verified | Generator/dependency review; regression prevents insecure generators on token paths. | Assign |
| R14 Compare secrets/HMACs with the platform's constant-time primitive, with safe fixed-length handling. | Unrated | FAIL - not verified | Comparison code; test the approved primitive and malformed/unequal-length rejection, not a flaky timing benchmark. | Assign |
| R15 Remove legacy CBC/padding-oracle paths and crypto fallbacks; failures must not reveal distinguishable padding details. | Unrated | FAIL - not verified | Algorithm/error-path review; deprecated-mode rejection and uniform-failure tests. | Assign |
| R16 Treat client JSON keys as untrusted: __proto__, constructor and prototype cannot modify object prototypes or privileged state through parsing/merging. | Unrated | FAIL - not verified | Schema/merge boundaries; nested dangerous-key fixtures leave prototypes/state unchanged. | Assign |
| R17 Never compile server-side templates from user strings or eval user input; use fixed templates and data-only parameters. | Unrated | FAIL - not verified | Rendering/evaluation paths; local expression fixtures remain inert data. | Assign |
| R18 Disable external entities and DTDs for XML/SVG parsing, including conversion/import pipelines. | Unrated | FAIL - not verified | Parser settings; fixture rejects DTD/entity input without reading files or making network requests. | Assign |
| R19 Check Origin against an explicit allowlist and authenticate each WebSocket/stream connection; define an authenticated no-Origin policy for native clients. | Unrated | FAIL - not verified | Connection policy; disallowed-Origin, unauthenticated and reconnect tests, including approved native behavior. | Assign |
| R20 Compare and reserve usernames/handles with a shared canonical Unicode policy: NFKC, full case folding and confusable detection/reservation, enforced atomically. | Unrated | FAIL - not verified | Canonicalizer/unique registry; equivalent, confusable and concurrent-reservation tests. | Assign |

## Web and edge

Cover every production path and relevant response class: HTML, APIs, static files, redirects and errors.
Record provider-controlled limitations rather than guessing that a managed edge can change every setting.

| Item / requirement | Risk | Status / reason / expiry | Evidence to supply | Owner |
| --- | --- | --- | --- | --- |
| W01 Return HSTS and X-Content-Type-Options: nosniff on every applicable HTTPS path, including static assets and error responses. | Unrated | FAIL - not verified | Header matrix and preview contract tests across response classes. | Assign |
| W02 Enforce a reviewed Content-Security-Policy. Report-Only is transitional only, with a named owner and dated enforcement plan; do not mark that transition PASS. | Unrated | FAIL - not verified | Enforced header and CSP tests, or dated remediation/acceptance reference. | Assign |
| W03 Set CSP frame-ancestors explicitly to deny or allow only intended framing. | Unrated | FAIL - not verified | Header and allowed/disallowed framing tests. | Assign |
| W04 Set appropriate Referrer-Policy and restrictive Permissions-Policy on applicable responses. | Unrated | FAIL - not verified | Header matrix and browser capability/referrer tests. | Assign |
| W05 Remove X-Powered-By and Server version banners from application and edge responses. | Unrated | FAIL - not verified | Headers across normal/static/error paths; provider exception if unavoidable. | Assign |
| W06 Use explicit CORS origin allowlists; never wildcard HTML or authenticated APIs. Reject unapproved browser origins while requests without Origin keep working for authorized native clients. | Unrated | FAIL - not verified | Allowed/disallowed/no-Origin and credentialed preflight/response tests. | Assign |
| W07 Pin every CDN asset and apply SRI to each pinned asset that supports it; self-host assets that cannot meet the integrity contract. | Unrated | FAIL - not verified | Asset inventory, integrity/crossorigin attributes and tamper-rejection tests. | Assign |
| W08 Require TLS 1.2 or newer and disable CBC suites where the edge supports configuration. For a managed-edge limitation, record reason, mitigation, owner and expiry as ACCEPTED, not PASS. | Unrated | FAIL - not verified | Operator/provider TLS evidence and protocol/cipher contract. | Assign |
| W09 Publish CAA records authorizing only intended certificate issuers; identify DNS/certificate ownership and renewal. | Unrated | FAIL - not verified | Private inventory reference and operator-provided DNS evidence. | Assign |
| W10 Inventory every domain's mail role; sending domains have valid SPF, DKIM signing and DMARC policy/alignment. | Unrated | FAIL - not verified | Domain/selector configuration and delivered-message authentication evidence. | Assign |
| W11 Non-sending domains publish SPF v=spf1 -all and DMARC p=reject; confirm no legitimate sender is broken. | Unrated | FAIL - not verified | Operator DNS evidence and verified non-sending classification. | Assign |
| W12 Unlaunched endpoints do not expose working production features; use an explicit disabled state with access enforced server-side. | Unrated | FAIL - not verified | Route inventory and disabled/unauthorized endpoint tests. | Assign |

## Mobile release

| Item / requirement | Risk | Status / reason / expiry | Evidence to supply | Owner |
| --- | --- | --- | --- | --- |
| M01 Before every Android store upload, satisfy rule 61's local MobSF gate on the release APK matching the store build's commit, flavor, defines, signing setup and version. Scan errors fail; upload success alone is insufficient. | Unrated | FAIL - not verified | Artifact hash/provenance, JSON/PDF, image digest and reviewed findings. | Assign |
| M02 Remove legacy cryptography and downgrade/fallback paths, including native dependencies. | Unrated | FAIL - not verified | Crypto inventory, dependency/config review and legacy-mode rejection tests. | Assign |
| M03 Restrict Firebase/Google API keys to the intended app identities and needed APIs; a key is not an authorization rule or a secret substitute. | Unrated | FAIL - not verified | Operator-provided restriction evidence and denied-other-app/API tests. | Assign |
| M04 Name all tracker SDKs and purposes in the privacy policy; verify actual release behavior matches consent and store disclosures. | Unrated | FAIL - not verified | Release tracker inventory, notice and consent/network tests. | Assign |

Rule 61's MobSF wrapper is an Android gate, not an iOS scan.
Record M01 as NA with evidence for an iOS-only project and establish the platform's actual release checks; do not claim MobSF Android evidence verifies iOS.

## Production readiness

PR1–PR10 are production-readiness IDs; P01–P26 remain the separate privacy checklist.
Use the same risk, status, evidence, ownership and exception rules as the other controls.
A planned integration or written policy alone does not satisfy a PASS condition.

| Item / PASS condition | Risk | Status / reason / expiry | Evidence to supply | Owner |
| --- | --- | --- | --- | --- |
| PR1 Race conditions: PASS if money, stock, bookings, quotas, counters and every read-modify-write use transactions or conditional writes, and idempotency keys make double-submit and concurrent requests safe. | Unrated | FAIL - not verified | Write-path inventory and concurrent/double-submit tests showing one intended effect and preserved invariants. | Assign |
| PR2 N+1 queries: PASS if request paths do not perform per-item database reads in loops, use batched reads and appropriate indexes, and list-screen query cost and latency are measured. | Unrated | FAIL - not verified | Query traces/counts, batch/index configuration and representative list-size cost/latency results. | Assign |
| PR3 Error tracking: PASS if app/web crashes and server errors reach a tracker and alert a named recipient, with personal data excluded from reports. | Unrated | FAIL - not verified | Sanitized controlled-error receipts for every platform/service, delivered alert and redaction/collection tests. | Assign |
| PR4 Rate limits: PASS if every public and authenticated endpoint has per-user and per-IP limits using platform-provided client IP, plus appropriate abuse/App Check controls. | Unrated | FAIL - not verified | Endpoint/control matrix and bounded limit, spoofed-IP and abuse/App Check rejection tests. | Assign |
| PR5 Background jobs: PASS if scheduled/queued work is idempotent, cannot overlap itself, has timeout/max-instance/batch-size bounds, retries with backoff, alerts on failure and has a named owner. | Unrated | FAIL - not verified | Job inventory/configuration and duplicate, overlap, timeout, retry and delivered-failure-alert tests. | Assign |
| PR6 Spend alerts: PASS if cloud billing budgets alert a named person and supported hard caps are configured, including max instances and AI/API-provider spend limits. | Unrated | FAIL - not verified | Operator-provided budget/cap settings, coverage of each provider and alert-delivery evidence; document unsupported caps explicitly. | Assign |
| PR7 Rollback: PASS if every deployable (app, web, functions, rules and database schema) has a written, tested, platform-appropriate rollback, keeps its previous version available and uses feature flags for risky launches. | Unrated | FAIL - not verified | Per-deployable rollback drill/results, previous-artifact references, schema/data compatibility and flag-disable tests. | Assign |
| PR8 Live data: PASS if production migrations/backfills are reviewed, dry-run first, idempotent, resumable and backed up first, and test/dev tooling cannot write to production. | Unrated | FAIL - not verified | Approved migration plan, dry-run/resume receipts, verified backup and environment/credential-isolation deny tests. | Assign |
| PR9 Webhooks: PASS if signatures are verified, a replay window is enforced, event IDs are processed idempotently, out-of-order delivery is handled, retries are safe and failures are visible. | Unrated | FAIL - not verified | Invalid-signature, stale/replayed, duplicate, reordered and retry fixtures plus failure-alert evidence. | Assign |
| PR10 Backups: PASS if automated backups and supported point-in-time recovery cover databases and file storage, retention is set, restores are tested on a schedule, and production-delete credentials cannot delete the backups. | Unrated | FAIL - not verified | Operator-provided backup/retention/access configuration, scheduled restore receipts and separate-credential deletion-denial evidence. | Assign |

Billing budgets are alerts, not hard spending caps.
Record unsupported caps/recovery features with their provider limitation, mitigation, owner and dated disposition; do not quietly mark them PASS.
Use existing authorized local checks or operator-supplied evidence for these rows; no cloud command, production write, alert integration or spending is authorized by this checklist.

## Operations from day one

| Item / requirement | Risk | Status / reason / expiry | Evidence to supply | Owner |
| --- | --- | --- | --- | --- |
| O01 For every service, document where/how it is deployed and who can deploy each service: environment/platform, artifact source, config/secret references, hosting-account owner, named authorized deployers, confirmed hosting-account access, exact deploy steps, health check and rollback steps/triggers. For an unbuilt service, mark the runbook Proposed and missing access as an owned task. | Unrated | FAIL - not verified | Per-service runbook/access matrix, operator-confirmed hosting-account permissions and deploy/rollback evidence; never credentials or secret values. | Assign |
| O02 After every web deploy run websec-check (rule 41) and zap-scan (rule 62), review failures/warnings and retain evidence; also follow the rules' session-start/weekly and preview-contract requirements. | Unrated | FAIL - not verified | Exact deployed revision/environment, private reports and review dispositions. | Assign |
| O03 Apply waf-fit (rule 63) before any WAF install, upgrade, routing or policy change; preserve the human-only operation and approval boundaries. | Unrated | FAIL - not verified | Approved fit, limitations, capacity, pilot and rollback plan, or justified NA. | Assign |
| O04 Before first launch and each release, refresh this checklist, link remediation/acceptance decisions, and report counts plus unresolved blockers in release DONE. Reopen affected rows after a security report. | Unrated | FAIL - not verified | Release review, decision references and due/expired-exception review. | Assign |

## Release review record

Fill one record per launch/release; retain prior reviews or link their history.

| Reviewed release / UTC date | PASS / FAIL / NA / ACCEPTED counts | High/Critical and Unrated blockers | Earliest exception expiry | Decision, owner and evidence |
| --- | --- | --- | --- | --- |
| Not reviewed | Not counted | Not triaged; launch blocked | No exceptions accepted | Assign release owner; no launch claim. |

List lower-risk FAIL task IDs/due dates and all accepted items with their original risk.
Report **BLOCKED** while High/Critical or Unrated FAIL remains.
Otherwise report **baseline reviewed**, with remaining gaps and exceptions; do not call that a security certification or permission to launch.
Required scan failures still block completion under rules 41, 61 and 62.

## Legal review starting sources

Reference check: 2026-11-24.
Recheck applicability and current law at release; these links do not replace Nepal, Germany, UK or US-state-specific advice.

- [GDPR official text, Articles 8 and 33](https://eur-lex.europa.eu/eli/reg/2016/679/): child consent thresholds vary within the stated framework; the authority-notification deadline has conditions and exceptions.
- [FTC COPPA guidance](https://www.ftc.gov/business-guidance/resources/complying-coppa-frequently-asked-questions): covered under-13 processing generally requires verifiable parental consent; ask counsel about coverage and exceptions.
- [FTC CAN-SPAM business guidance](https://www.ftc.gov/business-guidance/resources/can-spam-act-compliance-guide-business): commercial mail needs a postal address and opt-out, honored within 10 business days; opt-in above is a project default.
- [India's official DPDP commencement notification](https://www.meity.gov.in/static/uploads/2025/11/c56ceae6c383460ca69577428d36828b.pdf) and [DPDP Rules 2025](https://www.meity.gov.in/static/uploads/2025/11/53450e6e5dc0bfa85ebd78686cadad39.pdf): implementation is phased.
  Have counsel confirm which child-processing and breach-notice duties are in force for the release date; keep the safeguards planned from day one.
