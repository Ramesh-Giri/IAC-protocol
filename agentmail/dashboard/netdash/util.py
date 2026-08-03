# -*- coding: utf-8 -*-
"""Escaping, durations, and the four freshness wrappers every rendered value
passes through.

The wrappers are the whole honesty mechanism in miniature:
  age_html  an absolute instant -> an age that ticks live and never decays
  vol       volatile: dimmed after FRESH_SECONDS, blanked after AGING_SECONDS
  mono      monotone: rendered as a lower bound once the page is not fresh
  hole      a value that could not be observed, with the reason attached
Nothing renders a bare string if one of these applies to it."""

from __future__ import annotations

import html
import time
from datetime import datetime, timezone

from .thresholds import *  # noqa: F401,F403  (thresholds are printed on the page)

GEN_ERRORS: list[str] = []

def e(v) -> str:
    """Escape anything for HTML text/attribute context."""
    if v is None:
        return ""
    return html.escape(str(v), quote=True)

def epoch_of(iso_str) -> int | None:
    if not iso_str or not isinstance(iso_str, str):
        return None
    try:
        dt = datetime.strptime(iso_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        return int(dt.timestamp())
    except ValueError:
        return None

def dur(seconds, short: bool = False) -> str:
    """Human duration. None -> the hole marker."""
    if seconds is None:
        return "unknown"
    try:
        s = int(seconds)
    except (TypeError, ValueError):
        return "unknown"
    neg = s < 0
    s = abs(s)
    if s < 60:
        out = f"{s}s"
    elif s < 3600:
        out = f"{s // 60}m" if short else f"{s // 60}m {s % 60}s"
    elif s < 86400:
        h, r = divmod(s, 3600)
        out = f"{h}h" if short else f"{h}h {r // 60}m"
    else:
        d, r = divmod(s, 86400)
        out = f"{d}d" if short else f"{d}d {r // 3600}h"
    return ("-" + out) if neg else out

def num(v, default="—"):
    return default if v is None else str(v)

def local_and_utc(epoch: int) -> tuple[str, str]:
    lt = datetime.fromtimestamp(epoch).astimezone()
    ut = datetime.fromtimestamp(epoch, tz=timezone.utc)
    return (lt.strftime("%Y-%m-%d %H:%M:%S %Z"), ut.strftime("%Y-%m-%dT%H:%M:%SZ"))

def age_html(epoch, suffix=" ago", cls="durable", fallback="unknown") -> str:
    """A live-ticking age computed from the value's own epoch (never decays —
    an absolute timestamp stays true; only its distance from now grows)."""
    if epoch is None:
        return f'<span class="hole" title="not recorded in the snapshot">{e(fallback)}</span>'
    return (f'<span class="age" data-epoch="{int(epoch)}" data-suffix="{e(suffix)}" '
            f'data-fc="{cls}">{e(dur(int(time.time()) - int(epoch), short=True))}{e(suffix)}</span>')

def vol(inner: str, unknown: str = "—", title: str = "") -> str:
    """Wrap a volatile value: degraded 5-15 min after the snapshot, forced to
    the unknown marker past 15 min."""
    t = f' title="{e(title)}"' if title else ""
    return (f'<span class="v" data-fc="volatile" data-unknown="{e(unknown)}"{t}>{inner}</span>')

def mono(inner: str, title: str = "") -> str:
    """Monotone value: can only grow while the page sits open, so past the
    fresh window it is rendered as a lower bound."""
    t = f' title="{e(title)}"' if title else ""
    return f'<span class="m" data-fc="monotone"{t}>{inner}</span>'

def hole(text: str, why: str = "") -> str:
    return f'<span class="hole" title="{e(why)}">{e(text)}</span>'

def cmd(text: str) -> str:
    """A pre-filled command. This page has no control plane: a human runs it."""
    return f'<code class="cmd" tabindex="0">{e(text)}</code>'


# ---------------------------------------------------------------------------
# snapshot acquisition
# ---------------------------------------------------------------------------

def why(label: str, *paragraphs: str) -> str:
    """Reasoning, evidence and caveats — one click away instead of in the way.

    Every claim on this page still carries its derivation; it just does not
    shout it. Collapsed by default, and forced open when printing.
    """
    return ('<details class="why"><summary>' + e(label) + "</summary><div>"
            + "".join(f"<p>{t}</p>" for t in paragraphs if t) + "</div></details>")
