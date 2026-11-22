"""Task lifecycle vocabulary and local append-only evidence (Python 3.9+ stdlib)."""
from datetime import datetime, timezone
from enum import Enum
import json
import os
from pathlib import Path
import re
import subprocess
import uuid

from iac import atomic_write, line, lock, roster, valid_id


class EventType(str, Enum):
    LAUNCHED = "launched"
    TASK_SENT = "task_sent"
    ACK = "ack"
    CORRECTION = "correction"
    REVIEW_REQUESTED = "review_requested"
    REVIEW_COMPLETED = "review_completed"
    BLOCKER_OPENED = "blocker_opened"
    BLOCKER_RESOLVED = "blocker_resolved"
    DONE = "done"
    INTEGRATED = "integrated"
    REWORKED = "reworked"
    SUPERSEDED = "superseded"
    ABANDONED = "abandoned"
    CLOSED = "closed"


class Outcome(str, Enum):
    MERGED = "merged"
    MERGED_THEN_REWORKED = "merged_then_reworked"
    NOT_INTEGRATED = "not_integrated"
    ABANDONED = "abandoned"
    SUPERSEDED = "superseded"
    FAILED = "failed"


class SeatStatus(str, Enum):
    CLOSED = "closed"


def enum_value(enum, value):
    """Convert and validate vocabulary only at storage/CLI boundaries."""
    return enum(value).value


def utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def text_value(value):
    if not line(value).strip():
        raise ValueError("expected nonempty single-line text")
    return value


def single_task_id(entry):
    value = entry.get("task_id")
    if isinstance(value, list):
        value = value[0] if len(value) == 1 else None
    return value if isinstance(value, str) and value.strip() else None


def commit_sha(value, repo=None):
    if not re.fullmatch(r"(?:[a-fA-F0-9]{40}|[a-fA-F0-9]{64})", value):
        raise ValueError("commit must be a full SHA (40 or 64 hex characters)")
    value = value.lower()
    if repo is not None:
        result = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "--verify", "--end-of-options", value + "^{commit}"],
            capture_output=True, text=True, timeout=10)
        if result.returncode or result.stdout.strip().lower() != value:
            raise ValueError(f"commit {value} is not a commit in --repo {repo}")
    return value


def make_event(event_type, task_id, seat_id, actor, **fields):
    event = {"event_id": str(uuid.uuid4()), "time_utc": utc_now(),
             "event_type": enum_value(EventType, event_type),
             # Null is retained for legacy launches without an assigned task.
             "task_id": text_value(task_id) if task_id is not None else None,
             "seat_id": valid_id(seat_id), "actor": text_value(actor)}
    allowed = {"repo", "commit", "branch", "verdict", "review_round", "related_commit",
               "replaced_by", "reason", "outcome", "runtime", "model", "effort",
               "codex_home", "rules_revision", "commits"}
    if set(fields) - allowed:
        raise ValueError("unknown event fields: " + ", ".join(sorted(set(fields) - allowed)))
    for key, value in fields.items():
        if value is None:
            event[key] = None
        elif key == "outcome":
            event[key] = enum_value(Outcome, value)
        elif key == "review_round":
            if type(value) is not int or value < 1:
                raise ValueError("review_round must be a positive integer")
            event[key] = value
        elif key == "commits":
            event[key] = [commit_sha(sha, fields.get("repo")) for sha in value]
        elif key in ("commit", "related_commit"):
            event[key] = commit_sha(value, fields.get("repo"))
        else:
            event[key] = text_value(str(value))
    return event


def _append_locked(root, event):
    """Caller holds events lock; O_APPEND never rewrites prior evidence."""
    payload = (json.dumps(event, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
    fd = os.open(Path(root) / "events.jsonl", os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW, 0o600)
    try:
        view = memoryview(payload)
        while view:
            written = os.write(fd, view)
            if written == 0:
                raise OSError("could not append event")
            view = view[written:]
        os.fsync(fd)
    finally:
        os.close(fd)


def append_event(root, event_type, task_id, seat_id, actor, **fields):
    event = make_event(event_type, task_id, seat_id, actor, **fields)
    with lock(root, "events", wait=10):
        _append_locked(root, event)
    return event


def close_seat(root, seat_id, outcome, reason, *, actor, task_id=None,
               repo=None, commits=(), replaced_by=None, **fields):
    valid_id(seat_id)
    outcome = Outcome(outcome)
    reason = text_value(reason)
    if commits and repo is None:
        raise ValueError("seat-close commits require --repo for verification")
    verified = list(dict.fromkeys(commit_sha(sha, repo) for sha in commits))
    if outcome in (Outcome.MERGED, Outcome.MERGED_THEN_REWORKED) and not verified:
        raise ValueError("merged outcomes require at least one verified --commit and --repo")
    if outcome == Outcome.SUPERSEDED and not replaced_by:
        raise ValueError("superseded requires --replaced-by TASK")
    if replaced_by is not None:
        text_value(replaced_by)
    # The transport lock also coordinates roster snapshots with mail-sync.
    with lock(root, "transport", wait=10), lock(root, "roster", wait=10):
        data = roster(root)
        if seat_id not in data.get("agents", {}):
            raise ValueError(f"unknown seat {seat_id!r}")
        entry = data["agents"][seat_id]
        assigned = single_task_id(entry)
        task_id = task_id if task_id is not None else assigned
        if not task_id:
            raise ValueError("seat-close requires one roster task_id or --task-id")
        text_value(task_id)
        if assigned and task_id != assigned:
            raise ValueError("--task-id differs from the seat's assigned task")
        if replaced_by == task_id:
            raise ValueError("a task cannot supersede itself")
        evidence = dict(fields, outcome=outcome, reason=reason, commits=verified)
        if repo is not None:
            evidence["repo"] = str(Path(repo).resolve())
        if verified:
            evidence["commit"] = verified[-1]
        if replaced_by is not None:
            evidence["replaced_by"] = replaced_by
        event = make_event(EventType.CLOSED, task_id, seat_id, actor, **evidence)
        if entry.get("status") == SeatStatus.CLOSED:
            if (entry.get("outcome") == outcome and entry.get("commits") == verified
                    and entry.get("close_reason") == reason and entry.get("replaced_by") == replaced_by):
                return None  # An identical close is a successful no-op.
            raise ValueError("seat is already closed; refusing to replace its outcome")
        entry.update(status=enum_value(SeatStatus, SeatStatus.CLOSED), closed_at=event["time_utc"],
                     outcome=enum_value(Outcome, outcome), commits=verified, close_reason=reason,
                     close_event_id=event["event_id"])
        if replaced_by:
            entry["replaced_by"] = replaced_by
        # Evidence is durable before the atomic roster replacement. These are two
        # files, not a crash-atomic transaction; never report success on failure.
        with lock(root, "events", wait=10):
            _append_locked(root, event)
            atomic_write(Path(root) / "roster.json", json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    return event


def cli_main(command):
    import argparse
    import sys

    class Parser(argparse.ArgumentParser):
        def error(self, message):
            print("error: " + json.dumps(message))
            self.print_help(file=sys.stdout)
            raise SystemExit(2)

    p = Parser(prog=command, allow_abbrev=False,
               description="Record durable task evidence without stopping any processes.",
               epilog=("Example: fleet-event integrated --task-id fix-1 --seat worker --actor overseer -d MAIL\n"
                       "Example: seat-close worker --outcome not_integrated --reason 'report delivered' -d MAIL"),
               formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("-v", "-V", "--version", action="version", version="1.0.0")
    p.add_argument("-d", "--mail-root", default=os.environ.get("AGENTMAIL_DIR", ".agent-mail"))
    p.add_argument("--task-id", required=command == "fleet-event")
    p.add_argument("--actor", default=os.environ.get("AGENTMAIL_SEAT"))
    p.add_argument("--repo", type=Path)
    p.add_argument("--branch")
    p.add_argument("--verdict")
    p.add_argument("--review-round", type=int)
    p.add_argument("--related-commit")
    p.add_argument("--replaced-by")
    p.add_argument("--reason", required=command == "seat-close")
    if command == "fleet-event":
        p.add_argument("event_type", choices=[enum_value(EventType, e) for e in EventType])
        p.add_argument("--seat", "--seat-id", dest="seat_id", required=True)
        p.add_argument("--commit")
    else:
        p.add_argument("seat_id")
        p.add_argument("--outcome", required=True, choices=[enum_value(Outcome, o) for o in Outcome])
        p.add_argument("--commit", action="append", default=[])
    args = p.parse_args()
    try:
        actor = args.actor or roster(args.mail_root).get("roster_owner")
        if not actor:
            raise ValueError("provide --actor (or set AGENTMAIL_SEAT or roster_owner)")
        fields = {k: getattr(args, k) for k in ("branch", "verdict", "review_round", "related_commit", "replaced_by", "reason")
                  if getattr(args, k) is not None}
        if command == "fleet-event":
            if args.repo is not None:
                fields["repo"] = str(args.repo.resolve())
            if args.commit is not None:
                fields["commit"] = args.commit
            event = append_event(args.mail_root, args.event_type, args.task_id, args.seat_id, actor, **fields)
        else:
            event = close_seat(args.mail_root, args.seat_id, args.outcome, actor=actor,
                               task_id=args.task_id, repo=args.repo, commits=args.commit, **fields)
        print("event_id: " + json.dumps(event["event_id"]) if event else "status: already closed")
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print("error: " + json.dumps(str(exc)))
        print("help: " + json.dumps(f"Run {command} --help for required evidence and flags"))
        return 1
