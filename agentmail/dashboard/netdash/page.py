# -*- coding: utf-8 -*-
"""Assembles one self-contained file: no CDN, no webfont, no external image,
no network call at view time. The CSS and JS live beside this module as real
files (editable, diffable) and are inlined here at build time -- the page has
to survive being emailed, committed, or opened on a machine with no internet."""

from __future__ import annotations

import os
import time

from . import panels
from .thresholds import AGING_SECONDS, FRESH_SECONDS
from .paths import SNAPSHOT_BIN
from .util import GEN_ERRORS, cmd, e, local_and_utc

_STATIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


def asset(name: str) -> str:
    """Read a static asset. A missing asset is a build error, not a silent
    unstyled page."""
    with open(os.path.join(_STATIC, name), "r", encoding="utf-8") as fh:
        return fh.read()


CSS = asset("dashboard.css")
JS = asset("dashboard.js")

def render_page(M) -> str:
    meta = M["meta"]
    title = f"agentmail network — {meta.get('roster_owner') or 'site'}"
    js = (JS.replace("%SNAP%", str(int(M["snap_epoch"])))
            .replace("%FRESH%", str(FRESH_SECONDS))
            .replace("%AGING%", str(AGING_SECONDS)))
    parts = [
        "<!doctype html>", '<html lang="en">', "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{e(title)}</title>",
        f"<style>{CSS}</style>", "</head>", "<body>",
        panels.render_header(M),
        "<main>",
        panels.render_waiting(M),
        panels.render_triage(M),
        panels.render_alerts(M),
        panels.render_tree(M),
        panels.render_work(M),
        panels.render_mail(M),
        panels.render_federation(M),
        panels.render_history(M),
        panels.render_provenance(M),
        "</main>",
        f"<script>{js}</script>",
        "</body></html>",
    ]
    return "\n".join(parts)

def render_failure_page(reason: str, out_path: str) -> str:
    now = int(time.time())
    loc, utc = local_and_utc(now)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>agentmail network — NO SNAPSHOT</title><style>{CSS}</style></head><body>
<header class="rail"><div class="rail-grid">
<span class="brand">agentmail · no data</span>
<span><span class="k">attempted</span><span class="val">{e(loc)} / {e(utc)}</span></span>
<span class="stale-word stale-STALE">NO SNAPSHOT</span></div></header>
<main><section class="panel"><h2><span class="idx">!</span> The snapshot could not be read</h2>
<div class="pad"><div class="alert red"><span class="sev">red</span><div>
<div class="ti">This page is deliberately empty.</div>
<div class="ev">{e(reason)}</div>
<div class="ev">No seat, state or count is shown, because none was observed. An empty dashboard is the
honest rendering of "the collector failed" — a stale one would not be.</div>
<div style="margin-top:6px">{cmd(SNAPSHOT_BIN + " --pretty | head -40")}</div>
</div></div></div></section></main></body></html>"""


# ---------------------------------------------------------------------------
