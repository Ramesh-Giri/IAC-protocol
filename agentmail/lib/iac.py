"""IAC 1.1 primitives. Standard library only; trusted collaborators, not a sandbox."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import re
import signal
import socket
import subprocess
import sys
import tempfile
import time
import uuid

REQUEST_TYPES = {"task", "question", "proposal", "escalation", "handoff", "review"}
LOCAL_IGNORES = ["*/tmp/*", "/.locks/", "/local.json", "*/bridge.log"]


def valid_id(value):
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", value):
        raise ValueError(f"invalid seat id: {value!r}")
    return value


def line(value):
    if not isinstance(value, str) or any(ord(c) < 32 for c in value):
        raise ValueError("header values must be single-line text")
    return value


def roster(root):
    return json.loads((Path(root) / "roster.json").read_text())


def inbox(root, seat):
    valid_id(seat)
    root = Path(root).resolve()
    if seat not in roster(root).get("agents", {}):
        raise ValueError(f"seat {seat!r} is not registered in {root}/roster.json")
    path = root / seat
    for p in (path, path / "new", path / "cur", path / "tmp"):
        if p.is_symlink() or not p.resolve().is_relative_to(root):
            raise ValueError(f"mailbox path escapes the spool: {p}")
    if not (path / "new").is_dir() or not (path / "cur").is_dir():
        raise ValueError(f"missing maildir for {seat}")
    return path


@contextmanager
def lock(root, name, wait=0):
    """Kernel-released locks: no stale PID lock to delete after a crash."""
    directory = Path(root) / ".locks"
    if directory.is_symlink():
        raise ValueError(".locks must not be a symlink")
    directory.mkdir(exist_ok=True)
    fd = os.open(directory / (name + ".lock"), os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        deadline = time.monotonic() + wait
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise RuntimeError(f"busy: {name}; another IAC process owns it") from None
                time.sleep(0.02)
        yield fd
    finally:
        os.close(fd)


def atomic_write(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, "w") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def headers(text):
    """Flat YAML frontmatter; JSON-quoted new strings and legacy plain strings.

    Never evaluates YAML tags. Duplicate fields fail closed.
    """
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise ValueError("message has no frontmatter")
    result = {}
    for row in lines[1:]:
        if row == "---":
            return result
        if not row.strip() or row.lstrip().startswith("#"):
            continue
        key, sep, value = row.partition(":")
        if not sep or key in result:
            raise ValueError(f"invalid or duplicate header: {key}")
        value = value.strip()
        if value.startswith('"'):
            value = json.loads(value)
        result[key] = value
    raise ValueError("unterminated frontmatter")


def expects_reply(h):
    if h.get("expects_reply") is not None:
        return str(h["expects_reply"]).lower() == "true"
    return h.get("ack") in ("requested", "yes") or h.get("type") in REQUEST_TYPES


def message_key(path, h):
    return h.get("id") or path.name


def deliver(root, frm, to, subject, body, *, kind="info", metadata=None, message_id=None):
    root = Path(root).resolve()
    inbox(root, frm)
    target = inbox(root, to)
    line(subject)
    line(kind)
    bound = os.environ.get("AGENTMAIL_SEAT")
    if bound and bound != frm:
        raise ValueError(f"session is bound to {bound}, not {frm}")
    mid = str(uuid.UUID(message_id)) if message_id else str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    h = {"id": mid, "from": frm, "to": to, "subject": subject, "type": kind,
         "sent": now.strftime("%Y-%m-%dT%H:%M:%SZ")}
    if set(metadata or {}) & set(h):
        raise ValueError("metadata cannot replace core message headers")
    for key in metadata or {}:
        if not re.fullmatch(r"[a-z][a-z0-9_]*", key):
            raise ValueError("invalid metadata key")
    h.update(metadata or {})
    text = "---\n" + "".join(f"{k}: {json.dumps(line(v), ensure_ascii=False)}\n" for k, v in h.items()) + "---\n\n" + body.rstrip() + "\n"
    slug = re.sub(r"[^a-z0-9]+", "-", subject.lower()).strip("-")[:40]
    name = f"{now.strftime('%Y-%m-%dT%H-%M-%SZ')}-{frm}-{slug}--{mid}.md"
    with lock(root, "transport", wait=10):
        for box in ("new", "cur"):
            matches = list((target / box).glob(f"*--{mid}.md"))
            if matches:
                if matches[0].is_symlink():
                    raise ValueError("message must not be a symlink")
                old = matches[0].read_text()
                prior = headers(old)
                if any(prior.get(k) != v for k, v in h.items() if k != "sent") or old.split("\n---\n", 1)[1] != text.split("\n---\n", 1)[1]:
                    raise ValueError(f"message id {mid} already has different contents")
                return matches[0]
        (target / "tmp").mkdir(exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=target / "tmp")
        try:
            with os.fdopen(fd, "w") as f:
                f.write(text)
                f.flush()
                os.fsync(f.fileno())
            os.link(tmp, target / "new" / name)  # atomic, refuses overwrite
            directory_fd = os.open(target / "new", os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            os.unlink(tmp)
    return target / "new" / name


def acknowledge(root, path):
    with lock(root, "transport", wait=10):
        target = path.parent.parent / "cur" / path.name
        if path.is_symlink() or target.is_symlink():
            raise ValueError("message must not be a symlink")
        if target.exists():
            if target.read_bytes() != path.read_bytes():
                raise ValueError(f"refusing to overwrite read message: {target.name}")
        else:
            os.link(path, target)
        path.unlink()


def local_config(root):
    path = Path(root) / "local.json"
    return json.loads(path.read_text()) if path.exists() else {}


def local_site(root, data, explicit=None):
    sites = data.get("sites", {})
    chosen = explicit or os.environ.get("AGENTMAIL_SITE") or local_config(root).get("site")
    if chosen:
        if chosen not in sites:
            raise ValueError(f"unknown local site {chosen!r}")
        return chosen
    if len(sites) == 1:
        return next(iter(sites))
    host = socket.gethostname().lower().removesuffix(".local")
    matches = [s for s, cfg in sites.items() if cfg.get("machine", "").lower().removesuffix(".local") == host]
    return matches[0] if len(matches) == 1 else None


def run_bounded(command, *, timeout, input=None, **kwargs):
    """Terminate the entire command group on timeout or runner interruption."""
    proc = subprocess.Popen(command, start_new_session=True, **kwargs)
    try:
        out, err = proc.communicate(input=input, timeout=timeout)
        return subprocess.CompletedProcess(command, proc.returncode, out, err)
    except BaseException:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
            proc.wait(timeout=2)
        except (ProcessLookupError, subprocess.TimeoutExpired):
            pass
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        proc.wait()
        raise
    finally:
        for pipe in (proc.stdin, proc.stdout, proc.stderr):
            if pipe is not None:
                try:
                    pipe.close()
                except OSError:
                    pass


def require_home_site(root, seat, explicit=None):
    data = roster(root)
    if not data.get("sites"):
        return  # legacy local-only spool
    site = local_site(root, data, explicit)
    owner = data["agents"][seat].get("site")
    if not site or (len(data["sites"]) > 1 and not owner):
        raise ValueError("local site or seat site is ambiguous; configure local.json.site and roster.agents[seat].site")
    if owner and site != owner:
        raise ValueError(f"{seat} belongs to site {owner}; only its home site may consume or run it")


def parser(name):
    p = argparse.ArgumentParser(prog=name)
    p.add_argument("-d", "--mail-root", default=os.environ.get("AGENTMAIL_DIR", ".agent-mail"))
    p.add_argument("--site", help="local site override for federated mailboxes")
    return p


def send_main():
    p = parser("mail-send")
    for name in ("from", "to", "subject"):
        p.add_argument("--" + name, required=True)
    p.add_argument("--type", default="info")
    for name in ("thread", "in-reply-to", "supersedes", "project"):
        p.add_argument("--" + name)
    p.add_argument("--intent", choices=["research", "requirements", "proposal", "implementation", "review", "decision"])
    p.add_argument("--authority", choices=["product", "technical", "joint"])
    p.add_argument("--ref", action="append", default=[], help="shared-repository@full-commit:path (repeatable)")
    reply = p.add_mutually_exclusive_group()
    reply.add_argument("--ack", "--request-reply", action="store_true")
    reply.add_argument("--no-reply", action="store_true")
    body = p.add_mutually_exclusive_group()
    body.add_argument("-m", dest="body")
    body.add_argument("--body-file", type=Path)
    args = p.parse_args()
    if args.project and args.project not in roster(args.mail_root).get("projects", {}):
        p.error("project must appear in roster.projects")
    if (args.intent or args.authority) and not args.project:
        p.error("intent/authority requires --project")
    meta = {k: getattr(args, k) for k in ("thread", "in_reply_to", "supersedes", "project", "intent", "authority") if getattr(args, k)}
    requested = not args.no_reply and (args.ack or args.type in REQUEST_TYPES)
    meta.update(expects_reply=str(requested).lower(), ack="requested" if requested else "none")
    for ref in args.ref:
        line(ref)
        if not re.fullmatch(r".+@(?:[a-fA-F0-9]{40}|[a-fA-F0-9]{64}):[^\r\n]+", ref):
            p.error("--ref must be shared-repository@full-commit:path")
    if args.ref:
        meta["references"] = json.dumps(args.ref)
    text = args.body_file.read_text() if args.body_file else args.body if args.body is not None else sys.stdin.read()
    result = deliver(args.mail_root, getattr(args, "from"), args.to, args.subject, text, kind=args.type, metadata=meta)
    print(f"delivered: {result}")


def read_main(check=False):
    p = parser("mail-check" if check else "mail-read")
    p.add_argument("seat")
    p.add_argument("--headers", action="store_true")
    args = p.parse_args()
    target = inbox(args.mail_root, args.seat)
    if not check:
        require_home_site(args.mail_root, args.seat, args.site)
    with lock(args.mail_root, "consume-" + args.seat):
        count = 0
        for path in sorted((target / "new").glob("*.md")):
            if path.is_symlink():
                raise ValueError("message must not be a symlink")
            with lock(args.mail_root, "transport"):
                text = path.read_text()
            h = headers(text)
            if args.headers:
                print(f"{path.name} — {h.get('from')}: {h.get('subject')}")
            else:
                print(f"═══ {path.name} ═══\n{text}")
            sys.stdout.flush()
            if not check:
                acknowledge(args.mail_root, path)
            count += 1
        if not count:
            print(f"(no unread mail for {args.seat})")


def watch_main():
    p = parser("mail-watch")
    p.add_argument("seat")
    p.add_argument("-i", "--interval", type=float, default=5)
    args = p.parse_args()
    if args.interval <= 0:
        p.error("interval must be positive")
    target = inbox(args.mail_root, args.seat)
    require_home_site(args.mail_root, args.seat, args.site)
    with lock(args.mail_root, "watch-" + args.seat):
        seen = set()
        while True:
            try:
                with lock(args.mail_root, "transport"):
                    for path in sorted((target / "new").glob("*.md")):
                        if path.name in seen or path.is_symlink():
                            continue
                        try:
                            h = headers(path.read_text())
                        except ValueError as exc:
                            print(f"MAIL {args.seat} {path.name} — malformed: {exc}", flush=True)
                            seen.add(path.name)
                            continue
                        print(f"MAIL {args.seat} {path.name} — {h.get('from')}: {h.get('subject')}", flush=True)
                        seen.add(path.name)
            except (RuntimeError, FileNotFoundError):
                pass
            time.sleep(args.interval)


def main(name):
    try:
        {"mail-send": send_main, "mail-read": read_main,
         "mail-check": lambda: read_main(check=True), "mail-watch": watch_main}[name]()
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"{name}: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130
