---
name: waf-fit
description: Write a SafeLine WAF fit and rollback plan for human approval, distinguishing managed Firebase/Vercel edges from Circle Linux VM candidates. Planning only; agents do not install, change WAF policy, or run cloud commands.
---

# SafeLine fit plan

Apply rule 63. Produce a plan with evidence, named owner and rollback for Ramesh's approval. Product requirements and technical implementation retain their separate owners. This skill does not authorize a VM command, image download, DNS/firewall change, certificate transfer, installation or WAF configuration change. Ramesh performs VM operations himself through his existing console workflow; never invoke cloud CLIs, SDKs, remote shell, or a browser console on his behalf.

Record the fit decision, operator and deployment/rollback runbooks in the project's [security-privacy-baseline](../security-privacy-baseline/SKILL.md) under rule 64.
A WAF plan or installation does not replace application fixes or satisfy unrelated checklist rows.

## Current hosting decision

| Workload | Fit | Protection decision |
| --- | --- | --- |
| app web: Firebase Hosting + Cloud Functions | Do not insert SafeLine into these managed edges by default. There is no host-level ingress under our control there. | Review Firebase/Google's own supported edge/application controls and, where compatible with the verified domain/routing setup, a separately approved Cloudflare edge. Functions still need authentication, authorization, abuse limits and application fixes. |
| apu.bot landing: Vercel | Do not install SafeLine on the Vercel platform. | Review Vercel's own firewall/protection controls or a separately assessed Cloudflare front door. Validate domain, caching, TLS, client-IP and origin-bypass behavior first. |
| Circle: GCP Linux VMs | Candidate for an isolated pilot; insufficient evidence to approve production installation now. | Prefer a dedicated WAF VM in front of the existing origin, with a human-configured origin allowlist. Inspect current VM capacity and topology through Ramesh's evidence before deciding placement. Same-VM ingress would contend for 80/443 and share a failure domain. |

These decisions follow the task's hosting facts and SafeLine's reverse-proxy architecture; they are a local fit judgment, not a vendor claim. A WAF filters only HTTP/S traffic that traverses it. It cannot fix payment logic, account authorization, client flaws, outbound SSRF generally, direct-origin bypass, non-HTTP services, or volumetric exhaustion before the VM. Do not treat the upstream attack coverage/latency marketing as measured protection for Circle.

## Information required in each plan

Record privately: candidate VM architecture/OS, Docker/Compose versions, CPU/memory/disk and competing services; current DNS/TLS/80/443 listeners; app upstream address and trusted proxy/IP handling; WebSocket/SSE, uploads, webhooks/payment callbacks, health checks and API clients; existing firewall/origin exposure; expected request rate; certificate renewal owner; admin access path; owner/operator; maintenance window; monitoring destination and exact rollback routing values. Do not paste secrets or real host inventory into this public skill.

Upstream live deploy docs list Linux, x86_64/arm64, Docker ≥20.10.14, Compose ≥2.0.0, and a minimum 1 CPU core / 1 GB memory / 5 GB disk. The x86 CPU requirement is SSSE3. Those are vendor minima, not a Circle capacity estimate. Start the pilot budget at **2 vCPU / 4 GiB RAM / 20 GiB free disk** with log limits, then load-test on a disposable owner-controlled target; this is a proposed allowance, not a benchmark. Live docs currently say ARM operation requires a Pro license: do not assume GPL repository availability makes every bundled image/architecture free to use. Prefer an x86_64 candidate until licensing and image compatibility are checked.

The v9.4.7 compose runs Postgres, management, detector, tengine, luigi, fvm and chaos. Tengine uses **host networking**; management mounts `/var/run` and exposes a console port by default. Account for those host capabilities in the approval. Compare a contained deployment or vendor-supported mount restriction before using a shared production VM; do not claim container isolation removes this risk. Use a non-overlapping Docker subnet, bound logs, private admin access and least-privilege origin ingress.

## Paste-ready preparation for Ramesh

The following is a **reviewable pilot recipe**, not an approved installation. It assumes an unused dedicated **x86_64 Linux** WAF VM, Docker/Compose already installed, no existing `/data/safeline`, a reviewed non-overlapping `172.22.222.0/24` subnet, free 80/443, and an existing private administrative tunnel to loopback 9443. Stop and adapt the plan if any assumption is false. No software installer or `curl | bash` is used.

Ramesh runs this **inside his VM console only after approving this plan and downloads**:

```sh
set -eu
umask 077
uname -m
docker version
docker compose version
free -h
df -h
lscpu
sudo ss -lntp
docker network ls
# Review output first: x86_64 with SSSE3, capacity, subnet and free ports.
test ! -e /data/safeline
sudo install -d -m 0700 -o "$(id -u)" -g "$(id -g)" /data/safeline
cd /data/safeline
curl --fail --show-error --location --proto '=https' --tlsv1.2 \
  https://raw.githubusercontent.com/chaitin/SafeLine/v9.4.7/compose.yaml \
  -o compose.yaml
cat > .env <<'ENV'
SAFELINE_DIR=/data/safeline
IMAGE_TAG=9.4.7
MGT_PORT=127.0.0.1:9443
SUBNET_PREFIX=172.22.222
IMAGE_PREFIX=chaitin
ARCH_SUFFIX=
RELEASE=
REGION=-g
ENV
printf 'POSTGRES_PASSWORD=%s\n' "$(od -An -N32 -tx1 /dev/urandom | tr -d ' \n')" >> .env
chmod 600 .env compose.yaml
docker compose config --quiet
docker compose config --images
# Review every image/version and the rendered management bind before the pull.
docker compose config > compose.review.yaml
chmod 600 compose.review.yaml
docker compose pull
docker compose config --resolve-image-digests > compose.pinned.yaml
chmod 600 compose.pinned.yaml
docker compose -f compose.pinned.yaml up -d
docker compose -f compose.pinned.yaml ps
docker stats --no-stream
docker exec safeline-mgt resetadmin
```

The rendered compose files include the DB secret: keep them private, never attach their contents to mail or Git. Record **only image versions/digests** and non-secret capacity observations in the plan. Check tag availability and rendered compose compatibility before starting; live docs have evolved beyond this pinned compose, so do not splice newer settings in blindly. Keep console on loopback and access it through Ramesh's existing approved tunnel; do not open 9443 publicly. Reset credentials, bind the administrator's MFA, and retain secrets in the site's approved private store. Do not record the reset output in task evidence.

In the console, add a pilot domain and TLS certificate with the **existing Circle origin as upstream**; verify Host forwarding, TLS verification and renewal, real client IP only from the trusted proxy, and streaming/WebSocket behavior. Use observation/log-only mode if this edition exposes it; otherwise use a disposable pilot hostname and controlled clients before enabling blocking. Leave browser challenges and HTML/JS rewriting off for APIs, SSE, mobile clients and signed callbacks unless separately proven compatible.

Before public cutover, record old/new DNS values and TTL, original firewall rules, direct-origin probes and the exact operator route-restoration procedure. Ramesh changes routing and origin ingress through his human workflow. Allow origin HTTP only from the approved WAF/admin/health paths; reject direct public bypass while preserving a reviewed emergency access route. Pilot normal traffic and owner-controlled attack fixtures, then test auth, signed webhooks, payments, uploads, cache behavior, errors and streams. Do not send attack payloads to production based solely on this skill.

## Failure, monitoring and rollback

Expect an extra TLS/HTTP hop, inspection CPU, body buffering and a new single point of failure. Detection errors can block valid users; detector/DB/disk trouble can disrupt ingress. Do not assume fail-open or high availability: measure actual failure behavior in the pilot and choose an explicit outage-versus-bypass policy with Ramesh.

Suggested pilot acceptance targets (must be approved, not measured claims): added p95 latency ≤50 ms for representative non-streaming requests, no new functional failures or lost stream events, no false-positive blocks on the critical-flow suite, CPU/RAM/disk within reserved headroom. Monitor request latency, 4xx/5xx and block rates, origin health, stream disconnects, detector/management health, container restarts, CPU/RAM, disk/log growth, TLS expiry and update age. Use the existing monitoring service; a new external alert channel requires authority. Redact cookies, authorization headers and request bodies; set access controls, short retention and a disk cap before collecting real traffic.

Rollback trigger examples: failed critical callback/auth flow, sustained 5xx increase, detector outage, disk exhaustion, or breached latency target. **Restore the recorded prior DNS/load-balancer and origin ingress rules first through Ramesh's console workflow, verify direct-origin service and DNS propagation, then stop only this SafeLine stack**:

```sh
cd /data/safeline
docker compose -f compose.pinned.yaml ps
docker compose -f compose.pinned.yaml down
```

Do not remove volumes, data directories, certificates or unrelated containers. If bypassing the WAF reopens origin exposure, time-limit and monitor that exception with reason + expiry. Keep private config/backups and logs for diagnosis. No automatic upgrade: each version/policy change needs a new approved fit/diff/rollback plan under rule 63.

## Sources inspected

Read 2026-11-24: **SafeLine v9.4.7**, repository **GPL-3.0**. It remains a separate upstream Docker program; no GPL code or installer is copied into IAC.

- [v9.4.7 README and reverse-proxy model](https://github.com/chaitin/SafeLine/blob/v9.4.7/README.md), [versioned compose](https://github.com/chaitin/SafeLine/blob/v9.4.7/compose.yaml), [license](https://github.com/chaitin/SafeLine/blob/v9.4.7/LICENSE.md), [release notes](https://github.com/chaitin/SafeLine/releases/tag/v9.4.7).
- [Official deploy requirements, manual setup and uninstall](https://docs.waf.chaitin.com/en/GetStarted/Deploy), [application/upstream/TLS routing](https://docs.waf.chaitin.com/en/GetStarted/AddApplication). These live pages are not version-pinned; reviewed as context and adapted above. Their latest/root installer and destructive data-removal example are not adopted.

Deliver a written recommendation with unresolved assumptions, expected protection, budget, pilot evidence needed, operator steps, rollback and explicit Ramesh approval status. This round's status is **plan only, not installed or approved**.
