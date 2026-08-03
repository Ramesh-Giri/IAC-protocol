# -*- coding: utf-8 -*-
"""Everything this tool observes for itself, rather than taking from the
snapshot -- and therefore everything that carries its OWN clock.

network-snapshot answers "what does the mail network look like". It does not
stat FETCH_HEAD, it does not sample CPU, and SPEC 2 tells it to ignore tmp/.
Those three gaps are where the interesting failures live, so they are probed
here, at page-build time, and every value produced is labelled with when it was
read -- never merged into the snapshot's timestamp."""

from __future__ import annotations

import json
import os
import subprocess
import time
from datetime import datetime, timezone

from .thresholds import CPU_SAMPLE_GAP, TMP_STRANDED_SECONDS
from .util import GEN_ERRORS

def load_snapshot(args) -> dict:
    if args.json:
        try:
            with open(args.json, "r", encoding="utf-8") as fh:
                doc = json.load(fh)
            doc.setdefault("_source", {})
            doc["_source"] = {"mode": "file", "path": os.path.abspath(args.json),
                              "read_at": int(time.time())}
            return doc
        except (OSError, ValueError) as exc:
            GEN_ERRORS.append(f"could not read --json {args.json}: {exc}")
            return {}
    cmdline = [args.snapshot_bin]
    if args.mail_root:
        cmdline += ["--mail-root", args.mail_root]
    if args.hours:
        cmdline += ["--hours", str(args.hours)]
    try:
        p = subprocess.run(cmdline, capture_output=True, text=True, timeout=180, errors="replace")
    except (OSError, subprocess.TimeoutExpired) as exc:
        GEN_ERRORS.append(f"could not run {args.snapshot_bin}: {exc}")
        return {}
    if p.returncode != 0:
        GEN_ERRORS.append(f"{os.path.basename(args.snapshot_bin)} exited {p.returncode}: "
                          f"{(p.stderr or '').strip()[:400]}")
    try:
        doc = json.loads(p.stdout)
    except ValueError as exc:
        GEN_ERRORS.append(f"snapshot output was not JSON: {exc}")
        return {}
    if (p.stderr or "").strip():
        doc.setdefault("meta", {}).setdefault("warnings", []).append(
            "network-snapshot stderr: " + p.stderr.strip()[:300])
    doc["_source"] = {"mode": "live", "cmd": " ".join(cmdline), "read_at": int(time.time())}
    return doc

def fetch_age(repo_path: str) -> dict:
    """stat <repo>/.git/FETCH_HEAD. Read by THIS tool, at generation time —
    its own clock, its own decay. Never fabricated when absent."""
    out = {"path": repo_path, "epoch": None, "reason": None}
    try:
        git = os.path.join(repo_path, ".git")
        if os.path.isfile(git):  # worktree / submodule pointer
            with open(git, "r", encoding="utf-8", errors="replace") as fh:
                line = fh.readline().strip()
            if line.startswith("gitdir:"):
                git = line.split(":", 1)[1].strip()
                if not os.path.isabs(git):
                    git = os.path.normpath(os.path.join(repo_path, git))
        fh_path = os.path.join(git, "FETCH_HEAD")
        st = os.stat(fh_path)
        out["epoch"] = int(st.st_mtime)
        out["file"] = fh_path
    except OSError as exc:
        out["reason"] = ("no .git/FETCH_HEAD — this clone has never been fetched, "
                         "or the file was pruned" if isinstance(exc, FileNotFoundError)
                         else f"unreadable: {exc}")
    return out

def file_mtime(path: str):
    try:
        return int(os.stat(path).st_mtime)
    except OSError:
        return None

def cpu_probe(pids: list[int]) -> dict:
    """Two `ps` samples CPU_SAMPLE_GAP apart -> CPU seconds burned in between.

    Cumulative CPU cannot answer "is it spinning right now" — a process that
    worked hard yesterday and is now wedged has the same total as one that is
    looping. A delta can. Returns {pid: {"pct": float, "cum": seconds}}; an
    empty dict when ps is unavailable, which renders as a hole, not as zero.
    """
    pids = [p for p in pids if p]
    if not pids:
        return {}

    def sample() -> dict:
        try:
            p = subprocess.run(["ps", "-o", "pid=,time=", "-p", ",".join(str(x) for x in pids)],
                               capture_output=True, text=True, timeout=8, errors="replace")
        except (OSError, subprocess.TimeoutExpired):
            return {}
        out = {}
        for line in (p.stdout or "").splitlines():
            parts = line.split()
            if len(parts) < 2:
                continue
            try:
                pid = int(parts[0])
            except ValueError:
                continue
            t = parts[1]
            secs = 0.0
            try:
                bits = t.replace("-", ":").split(":")
                for b in bits:
                    secs = secs * 60 + float(b)
            except ValueError:
                continue
            out[pid] = secs
        return out

    a = sample()
    if not a:
        return {}
    t0 = time.time()
    time.sleep(CPU_SAMPLE_GAP)
    b = sample()
    gap = max(time.time() - t0, 0.001)
    res = {}
    for pid, cum in b.items():
        if pid in a:
            res[pid] = {"pct": max(0.0, (cum - a[pid]) / gap * 100.0), "cum": cum, "gap": gap}
    return res

FNAME_TS_LEN = len("2026-08-03T10-51-11Z")

def maildir_scan(mail_root: str, seat_id: str) -> dict:
    """Directory listing only — names and mtimes, never contents.

    new/ filenames carry the UTC timestamp (SPEC §4), which is enough to
    reconstruct when the current backlog arrived. tmp/ is scanned ONLY to count
    stranded files: SPEC §2 tells readers to ignore tmp/, which is exactly why
    nothing else would ever notice a write that died half-finished.
    """
    out = {"new_epochs": [], "tmp_stranded": [], "read": False, "read_at": int(time.time())}
    base = os.path.join(mail_root or "", seat_id or "")
    try:
        names = os.listdir(os.path.join(base, "new"))
        out["read"] = True
    except OSError:
        return out
    for n in names:
        if not n.endswith(".md"):
            continue
        stamp = n[:FNAME_TS_LEN]
        try:
            dt = datetime.strptime(stamp, "%Y-%m-%dT%H-%M-%SZ").replace(tzinfo=timezone.utc)
            out["new_epochs"].append(int(dt.timestamp()))
        except ValueError:
            ep = file_mtime(os.path.join(base, "new", n))
            if ep:
                out["new_epochs"].append(ep)
    out["new_epochs"].sort()
    try:
        for n in os.listdir(os.path.join(base, "tmp")):
            p = os.path.join(base, "tmp", n)
            ep = file_mtime(p)
            if ep is not None and (out["read_at"] - ep) > TMP_STRANDED_SECONDS:
                out["tmp_stranded"].append({"name": n, "epoch": ep})
    except OSError:
        pass
    return out
