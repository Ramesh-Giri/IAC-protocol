# -*- coding: utf-8 -*-
"""Where things are, discovered rather than assumed.

Nothing here hardcodes a checkout location. The repository root is found by
walking up from this file looking for the AgentMail helper scripts, so the
project can be cloned, renamed, moved, or vendored into someone else's tree and
still find its own snapshot tool and its own output directory. If the helper
cannot be found at all, the snapshot binary falls back to PATH and the failure
is reported on the page rather than guessed around.
"""

from __future__ import annotations

import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))          # .../agentmail/dashboard/netdash
PACKAGE_ROOT = os.path.dirname(HERE)                        # .../agentmail/dashboard

# the marker that identifies a repo root: the mail helpers live under it
MARKER = os.path.join("agentmail", "bin", "network-snapshot")


def find_repo_root(start: str = HERE) -> str:
    d = os.path.abspath(start)
    while True:
        if os.path.isfile(os.path.join(d, MARKER)):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            # no marker anywhere above us: fall back to the tree this package
            # sits in, three levels up (repo/agentmail/dashboard/netdash)
            return os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
        d = parent


REPO_ROOT = find_repo_root()
SNAPSHOT_BIN = (os.path.join(REPO_ROOT, MARKER)
                if os.path.isfile(os.path.join(REPO_ROOT, MARKER))
                else (shutil.which("network-snapshot") or os.path.join(REPO_ROOT, MARKER)))
DEFAULT_OUT = os.path.join(REPO_ROOT, "runbooks", "network.html")
BIN_DIR = os.path.dirname(SNAPSHOT_BIN)


def rel(path: str) -> str:
    """A path shown to a human: relative to the repo root when it is inside it,
    absolute when it is not."""
    try:
        r = os.path.relpath(path, REPO_ROOT)
        return r if not r.startswith("..") else path
    except ValueError:
        return path


def helper(name: str) -> str:
    """The command a human would type to run one of the mail helpers."""
    return rel(os.path.join(BIN_DIR, name))
