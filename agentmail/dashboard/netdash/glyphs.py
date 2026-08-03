# -*- coding: utf-8 -*-
"""Shape first, colour second.

Every state on the page is legible in greyscale, from the glyph outline plus
the word printed beside it; colour is a redundant fourth channel, never the
only one. That is why these are hand-written inline SVG rather than characters
from a font: a filled square, a half square and a dash must stay distinct at
13px on any machine, with no webfont to fail to load."""

from __future__ import annotations

from .state import COMPOSITE_DOC, LIVENESS_DOC, LIVENESS_TONE, OCCUPANCY_DOC
from .util import age_html, e, hole, mono, vol

def g_session(state: str) -> str:
    b = '<svg class="gl" viewBox="0 0 20 20" width="18" height="18" aria-hidden="true">'
    if state == "filled":
        s = '<rect x="3" y="3" width="14" height="14" fill="currentColor"/>'
    elif state == "hollow":
        s = '<rect x="3.9" y="3.9" width="12.2" height="12.2" fill="none" stroke="currentColor" stroke-width="1.8"/>'
    elif state == "half":
        s = ('<rect x="3.9" y="3.9" width="12.2" height="12.2" fill="none" stroke="currentColor" stroke-width="1.8"/>'
             '<rect x="3.9" y="3.9" width="6.1" height="12.2" fill="currentColor"/>')
    else:
        s = '<line x1="3" y1="10" x2="17" y2="10" stroke="currentColor" stroke-width="2.2"/>'
    return b + s + "</svg>"

def g_mailbox(state: str, n) -> str:
    b = '<svg class="gl" viewBox="0 0 22 22" width="20" height="20" aria-hidden="true">'
    parts = []
    if state == "dash":
        parts.append('<line x1="3" y1="11" x2="19" y2="11" stroke="currentColor" stroke-width="2.2"/>')
        return b + "".join(parts) + "</svg>"
    if state == "deaf":
        parts.append('<rect x="1" y="1" width="20" height="17" fill="none" stroke="currentColor" stroke-width="1.6"/>')
    parts.append('<circle cx="11" cy="9.2" r="5.6" fill="none" stroke="currentColor" stroke-width="1.8"/>')
    if n:
        parts.append('<text x="11" y="12.3" text-anchor="middle" font-size="7.6" '
                     'font-family="ui-monospace,Menlo,monospace" font-weight="700" '
                     'fill="currentColor">' + e(str(n)[:2]) + "</text>")
    if state in ("lagging", "deaf"):
        parts.append('<line x1="2.5" y1="20.4" x2="19.5" y2="20.4" stroke="currentColor" stroke-width="2"/>')
    return b + "".join(parts) + "</svg>"

def g_work(state: str) -> str:
    b = '<svg class="gl" viewBox="0 0 20 20" width="18" height="18" aria-hidden="true">'
    chev = "4,2.5 14.5,10 4,17.5 8,10"
    if state == "producing":
        s = f'<polygon points="{chev}" fill="currentColor"/>'
    elif state == "recent":
        s = f'<polygon points="{chev}" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/>'
    elif state == "quiet":
        s = '<rect x="3" y="7.6" width="14" height="4.8" fill="currentColor"/>'
    else:
        s = '<line x1="3" y1="10" x2="17" y2="10" stroke="currentColor" stroke-width="2.2"/>'
    return b + s + "</svg>"

def g_occ(state: str) -> str:
    b = '<svg class="gl" viewBox="0 0 20 20" width="18" height="18" aria-hidden="true">'
    if state == "working":
        s = '<polygon points="4,2.5 14.5,10 4,17.5 8,10" fill="currentColor"/>'
    elif state == "waiting-for-mail":
        s = '<polygon points="10,3 17,10 10,17 3,10" fill="none" stroke="currentColor" stroke-width="1.8"/>'
    elif state == "interrupted":
        s = ('<rect x="4" y="3" width="4" height="14" fill="currentColor"/>'
             '<rect x="12" y="3" width="4" height="14" fill="currentColor"/>')
    elif state == "spinning":
        s = ('<circle cx="10" cy="10" r="6.6" fill="none" stroke="currentColor" stroke-width="2"'
             ' stroke-dasharray="3.2 3.2"/><circle cx="10" cy="10" r="1.6" fill="currentColor"/>')
    else:
        s = '<line x1="3" y1="10" x2="17" y2="10" stroke="currentColor" stroke-width="2.2"/>'
    return b + s + "</svg>"

TONE_CLASS = {"good": "t-good", "warn": "t-warn", "bad": "t-bad", "unknown": "t-unk"}

def sparkline(depth: dict | None, width=92, height=20) -> str:
    if not depth:
        return hole("no listing", "the maildir could not be listed by this tool")
    b = depth["buckets"]
    mx = max(depth["max"], 1)
    n = len(b)
    step = width / max(n - 1, 1)
    pts = " ".join(f"{i*step:.1f},{height - 2 - (v / mx) * (height - 4):.1f}" for i, v in enumerate(b))
    last = b[-1] if b else 0
    growing = depth["growing"]
    cls = "t-bad" if growing else "t-unk"
    bars = "".join(
        f'<rect x="{i*step:.1f}" y="{height - 2 - (v / mx) * (height - 4):.1f}" width="{max(step - 1, 1):.1f}" '
        f'height="{(v / mx) * (height - 4) + 0.6:.1f}" fill="currentColor" opacity=".28"/>'
        for i, v in enumerate(b))
    return (f'<span class="spark {cls}" title="backlog depth by hour over the last {depth["window_hours"]}h, '
            f'reconstructed from arrival times of mail still in new/ — a LOWER BOUND: anything already read is '
            f'invisible here">'
            f'<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" aria-hidden="true">'
            f'{bars}<polyline points="{pts}" fill="none" stroke="currentColor" stroke-width="1.6"/></svg>'
            f'<span class="sparknum">{last}{"↑" if growing else ""}</span></span>')

def slot_row(sl_s, sl_m, sl_w, comp, comp_tone, blocked_note="") -> str:
    """The three slots, always same order and position, each with its word."""
    def cell(label, glyph, word, detail, tone, decay):
        inner = (f'<span class="slot-g {TONE_CLASS.get(tone, "t-unk")}">{glyph}</span>'
                 f'<span class="slot-t"><span class="slot-l">{e(label)}</span>'
                 f'<span class="slot-w">{e(word)}</span></span>')
        body = vol(inner, unknown=f'<span class="slot-g t-unk">{g_session("dash")}</span>'
                                  f'<span class="slot-t"><span class="slot-l">{e(label)}</span>'
                                  f'<span class="slot-w">stale</span></span>') if decay else inner
        return (f'<div class="slot" title="{e(detail)}">{body}</div>')

    out = ['<div class="slots">']
    out.append(cell("SESSION", g_session(sl_s["state"]), sl_s["word"], sl_s["detail"], sl_s["tone"], True))
    # mailbox is monotone, not volatile: unread can only grow while the page sits open
    out.append(f'<div class="slot" title="{e(sl_m["detail"])}">'
               f'<span class="slot-g {TONE_CLASS.get(sl_m["tone"], "t-unk")}">{g_mailbox(sl_m["state"], sl_m.get("n"))}</span>'
               f'<span class="slot-t"><span class="slot-l">MAILBOX</span>'
               f'<span class="slot-w">{e(sl_m["word"])}'
               + (f' {mono(e(str(sl_m.get("n"))) + " unread", "unread can only grow while this page is open")}'
                  if sl_m.get("n") else "")
               + "</span></span></div>")
    out.append(cell("WORK", g_work(sl_w["state"]), sl_w["word"], sl_w["detail"], sl_w["tone"], True))
    out.append(f'<div class="composite {TONE_CLASS.get(comp_tone, "t-unk")}" '
               f'title="{e(COMPOSITE_DOC.get(comp, ""))}">'
               f'{vol("<b>" + e(comp) + "</b>", unknown="<b>Unknown (stale)</b>")}'
               + (f'<span class="selfrep">self-reported</span>' if blocked_note else "")
               + "</div>")
    out.append("</div>")
    return "".join(out)


# ---------------------------------------------------------------------------
# derivation: everything else
# ---------------------------------------------------------------------------

def slots_inline(ms) -> str:
    """The three slots as one compact evidence strip: glyph + one word each.
    The full derivation stays in the title, and in panel 5."""
    out = []
    for label, sl, glyph in (("ses", ms["s"], g_session(ms["s"]["state"])),
                             ("box", ms["m"], g_mailbox(ms["m"]["state"], ms["m"].get("n"))),
                             ("wrk", ms["w"], g_work(ms["w"]["state"]))):
        out.append(f'<span class="si" title="{e(label.upper())}: {e(sl["word"])} — {e(sl["detail"])}">'
                   f'<i>{e(label)}</i>'
                   f'<span class="si-g {TONE_CLASS.get(sl["tone"], "t-unk")}">{glyph}</span>'
                   f'<b>{e(sl["word"])}</b></span>')
    return '<span class="sis">' + "".join(out) + "</span>"

def two_axis_cell(liv: dict, occ: dict) -> str:
    tone = LIVENESS_TONE.get(liv["state"], "unknown")
    inner = (f'<span class="ax-g {TONE_CLASS.get(tone, "t-unk")}" title="{e(OCCUPANCY_DOC.get(occ["state"], ""))}">'
             f'{g_occ(occ["state"])}</span>'
             f'<span class="ax-t"><span class="ax-l {TONE_CLASS.get(tone, "t-unk")}" '
             f'title="{e(LIVENESS_DOC.get(liv["state"], ""))}">{e(liv["state"])}</span>'
             f'<span class="ax-o">{e(occ["state"])}</span></span>')
    at = ""
    if liv["state"] == "stopped-or-lost":
        at = ('<span class="ax-at">last output ' + (age_html(liv["at"]) if liv.get("at")
              else hole("time unknown", "no timestamped output survives")) + "</span>")
    return (f'<span class="axis" title="{e(liv["detail"])} || {e(occ["detail"])}">'
            + vol(inner, unknown='<span class="ax-g t-unk">' + g_occ("unknown") + '</span>'
                                 '<span class="ax-t"><span class="ax-l t-unk">fogged</span>'
                                 '<span class="ax-o">last seen above</span></span>')
            + at + "</span>")
