# -*- coding: utf-8 -*-
"""Command line. Writes exactly one file, atomically, and returns 0 whenever a
page was produced -- including the "no snapshot" page, which is a legitimate
answer, not a crash."""

from __future__ import annotations

import argparse
import os
import sys

from .model import build_model
from .page import render_failure_page, render_page
from .probes import load_snapshot
from .paths import DEFAULT_OUT, SNAPSHOT_BIN
from .util import GEN_ERRORS


# thresholds (printed on the page — a reader must be able to check the rule)

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="network-dashboard",
        description="Render a network-snapshot document as one self-contained HTML instrument panel.")
    ap.add_argument("-o", "--out", default=DEFAULT_OUT, help=f"output HTML (default {DEFAULT_OUT})")
    ap.add_argument("--json", help="read a saved snapshot JSON instead of running the snapshot tool")
    ap.add_argument("--snapshot-bin", default=SNAPSHOT_BIN, help="path to network-snapshot")
    ap.add_argument("--mail-root", help="passed through to network-snapshot")
    ap.add_argument("--hours", type=int, help="mail window, passed through to network-snapshot")
    ap.add_argument("--quiet", action="store_true", help="print nothing on success")
    args = ap.parse_args(argv)

    out_path = os.path.abspath(args.out)
    doc = load_snapshot(args)

    # an empty roster is a real state and must render; only a document we could
    # not parse at all falls back to the "no snapshot" page.
    if not doc or ("seats" not in doc and "meta" not in doc):
        page = render_failure_page("; ".join(GEN_ERRORS) or "the snapshot document was empty.", out_path)
    else:
        M = build_model(doc, out_path, args)
        page = render_page(M)

    try:
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        tmp = out_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(page)
        os.replace(tmp, out_path)
    except OSError as exc:
        print(f"network-dashboard: could not write {out_path}: {exc}", file=sys.stderr)
        return 1

    if not args.quiet:
        size = os.path.getsize(out_path)
        print(f"{out_path}  ({size/1024:.0f} KB)")
        for w in GEN_ERRORS:
            print(f"  warning: {w}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
