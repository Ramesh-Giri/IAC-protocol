# -*- coding: utf-8 -*-
"""The panels, in reading order: triage first, evidence second, provenance last.

House style, applied everywhere in this file:
  * the data comes first and the reasoning goes into a `why(...)` disclosure;
  * a table cell holds one short line, never a paragraph (units live in the
    column header, not repeated in every row);
  * a value that could not be observed prints as a labelled hole;
  * a sender's words are quoted (.subject), derived prose is not (.prose),
    and text copied verbatim out of a file is marked as such (.verbatim).
"""

from __future__ import annotations

import math
import os

from .glyphs import (TONE_CLASS, g_mailbox, g_occ, g_session, g_work, slot_row, slots_inline,
                     sparkline, two_axis_cell)
from .state import COMPOSITE_DOC, LIVENESS_DOC, LIVENESS_TONE, OCCUPANCY_DOC
from .thresholds import *  # noqa: F401,F403
from . import __version__
from .paths import BIN_DIR, DEFAULT_OUT, REPO_ROOT, SNAPSHOT_BIN, helper, rel
from .util import (GEN_ERRORS, age_html, cmd, dur, e, epoch_of, hole, local_and_utc, mono, num,
                   vol, why)

# Panels that open on load. Everything a human is answerable for is here;
# the rest is evidence, one click away. A reader's own choices override this and
# are remembered, so this is only the state of a machine that has never seen
# this page before.
DEFAULT_OPEN = {1, 2, 3}

# how many alerts render in full before the tail folds
ALERTS_SHOWN = 6


def panel(idx, title, sub="", body="", extra_head="") -> str:
    """One collapsible, reorderable panel.

    The header is the whole summary: when a panel is shut, its title and its
    counts still read, so collapsing hides detail and never hides a fact. Order
    and open/shut state are the reader's, and are remembered per browser — but
    they are VIEW state only. Nothing here can act on the network, and no
    arrangement changes what the page asserts.
    """
    open_attr = "" if idx in DEFAULT_OPEN else ' data-collapsed="1"'
    expanded = "true" if idx in DEFAULT_OPEN else "false"
    return (f'<section class="panel" id="p{idx}" data-pid="p{idx}" data-idx="{e(idx)}"{open_attr}>'
            f'<h2 class="ph">'
            f'<span class="drag" role="button" tabindex="0" draggable="true" aria-label="Reorder panel '
            f'{e(idx)}: {e(title)}. Drag, or press alt with the up and down arrows.">&#10303;</span>'
            f'<button type="button" class="ph-btn" aria-expanded="{expanded}" aria-controls="p{idx}-body">'
            f'<span class="chev" aria-hidden="true"></span>'
            f'<span class="idx">{e(idx)}</span><span class="ptitle">{e(title)}</span>'
            + (f'<span class="sub">{sub}</span>' if sub else "")
            + "</button>"
            + (extra_head or "") + "</h2>"
            f'<div class="panel-body" id="p{idx}-body">' + body + "</div></section>")

def render_header(M) -> str:
    meta, now, snap = M["meta"], M["now"], M["snap_epoch"]
    loc, utc = local_and_utc(snap)
    counts = meta.get("counts") or {}
    failed = len(meta.get("warnings") or []) + len(GEN_ERRORS)
    src = (M["doc"].get("_source") or {})
    args = M["args"]
    rerun = helper("network-dashboard")
    rerun_cmd = rerun if os.path.abspath(M["out_path"]) == os.path.abspath(DEFAULT_OUT) \
        else f"{rerun} -o {M['out_path']}"
    age = now - snap
    word = "FRESH" if age < FRESH_SECONDS else ("AGING" if age < AGING_SECONDS else "STALE")
    return f"""
<header class="rail">
  <div class="rail-grid">
    <span class="brand">agentmail · {e(meta.get('roster_owner') or 'network')}</span>
    <span><span class="k">snapshot</span><span class="val">{e(loc)}</span></span>
    <span><span class="k">utc</span><span class="val">{e(utc)}</span></span>
    <span><span class="k">age</span><span class="val" id="snapage">{e(dur(age, short=True))} ago</span></span>
    <span id="staleword" class="stale-word stale-{word}">{word}</span>
    <span><span class="k">collected in</span><span class="val">{e(meta.get('collection_ms', '?'))} ms</span></span>
    <span><span class="k">failed checks</span><span class="val {'t-bad' if failed else 't-good'}">{failed}</span></span>
    <span><span class="k">seats</span><span class="val">{e(counts.get('seats', '—'))}</span></span>
    <span><span class="k">source</span><span class="val">{e(src.get('mode','?'))}{'' if src.get('mode')=='live' else ' · '+e(src.get('path',''))}</span></span>
    <span class="themectl" role="group" aria-label="theme (view only)">
      <button type="button" data-theme="auto" aria-pressed="true">auto</button>
      <button type="button" data-theme="light" aria-pressed="false">light</button>
      <button type="button" data-theme="dark" aria-pressed="false">dark</button>
    </span>
    <span class="themectl" role="group" aria-label="layout (view only)">
      <button type="button" id="expandall" title="open every panel">expand all</button>
      <button type="button" id="collapseall" title="shut every panel">collapse</button>
      <button type="button" id="resetlayout" title="restore the default order and open panels">reset</button>
    </span>
    <div class="rerun">
      <span class="k">re-run</span>{cmd(rerun_cmd)}
      <span class="k" style="margin-left:auto">host</span><span class="val">{e(meta.get('hostname','—'))}</span>
      <span class="k">mail root</span><span class="val">{e(meta.get('mail_root','—'))}</span>
    </div>
    <nav class="index" aria-label="sections">
      <a href="#p1">1 waiting</a><a href="#p2">2 seats</a><a href="#p3">3 alerts</a><a href="#p4">4 tree</a>
      <a href="#p5">5 work</a><a href="#p6">6 mail</a><a href="#p7">7 federation</a><a href="#p8">8 history</a>
      <a href="#p9">9 provenance</a>
    </nav>
    <p class="note" id="decaybanner" style="flex:1 1 100%;margin:0">volatile fields at full strength</p>
    <p class="note hint-line" style="flex:1 1 100%;margin:0">Panels collapse when you click their title and
       reorder when you drag <span class="drag-demo">&#10303;</span> (or focus it and press alt with the arrow
       keys). Your arrangement is remembered in this browser — it is view state only and changes nothing about
       the network.</p>
  </div>
</header>"""

def render_waiting(M) -> str:
    board = M["board"]
    waiting_title = f'Waiting on {M["ident"]["human_short"]}'
    items = [i for i in (board.get("items") or [])
             if (i.get("section") or "").upper().startswith("WAITING")]
    bm = M["board_mtime"]
    bm = M["board_mtime"]
    head_note = (
        '<p class="note"><b>Age unrecorded.</b> The board keeps no per-item timestamps, so this panel cannot '
        'rank by age and shows file order. Board last edited '
        + (age_html(bm) if bm else hole("unknown", "could not stat the board file")) + '.</p>'
        + why("why this panel cannot sort by age",
              'This is the one panel that fails its own brief. Items were to be sorted oldest-first, because age '
              'is the fact that decides which one has been waiting too long — but <code>'
              + e(board.get("path") or "the board") + '</code> is hand-written markdown with no date on any item, '
              'and inventing one would be worse than admitting the hole.',
              'The board file\'s own mtime bounds every item at "no older than the board" and says nothing about '
              'any single one.',
              'To make this panel work, give each item a date field — '
              '<code class="cmd" tabindex="0" style="user-select:all">- since:2026-08-01 | task | …</code> — '
              'and this page will sort on it automatically.'))
    if not board.get("exists"):
        return panel(1, waiting_title, "", '<div class="pad"><p class="empty">'
                     + e(f"{board.get('path')} does not exist — there is no board to read. "
                         "This panel is empty because the file is missing, NOT because nothing is waiting.")
                     + "</p></div>")
    if not items:
        return panel(1, waiting_title, "", '<div class="pad">' + head_note +
                     '<p class="empty">No section starting "WAITING" was found in the board.</p></div>')
    rows = []
    for n, i in enumerate(items, 1):
        f = i.get("fields") or [i.get("raw", "")]
        task = f[0] if f else i.get("raw", "")
        notes = " | ".join(f[1:]) if len(f) > 1 else ""
        rows.append(f'<div class="wait"><span class="n">{n:02d}</span><div>'
                    f'<div class="w-task">{e(task)}</div>'
                    + (f'<div class="w-notes">{e(notes)}</div>' if notes else "")
                    + f'<div class="w-notes" style="color:var(--ink-3);font-size:11px">'
                      f'{e(board.get("path"))}:{e(i.get("line"))} · age unrecorded</div>'
                    "</div></div>")
    sub = f"{len(items)} item(s) · from {e(os.path.basename(board.get('path') or 'board'))} · verbatim"
    return panel(1, waiting_title, sub, '<div class="pad">' + head_note + "".join(rows) + "</div>")

def render_alerts(M) -> str:
    alerts = M["alerts"]
    dis = M["dis"]
    body = ['<div class="pad">']
    if not alerts:
        body.append('<p class="empty">No derived anomaly fired. This panel is empty most days; '
                    'that is the intended resting state, not a health claim.</p>')
    def alert_html(a):
        return (f'<div class="alert {a["sev"]}"><span class="sev">{a["sev"]}</span><div>'
                f'<div class="ti">{e(a["title"])}</div>'
                f'<div class="ev">{e(a["evidence"])}</div>'
                + (f'<div style="margin-top:4px">{cmd(a["fix"])}</div>' if a.get("fix") else "")
                + "</div></div>")

    # red first, and only the first few in full: a wall of amber buries the one
    # line that matters. Nothing is dropped — the tail is one click away.
    ordered = [a for a in alerts if a["sev"] == "red"] + [a for a in alerts if a["sev"] != "red"]
    head, tail = ordered[:ALERTS_SHOWN], ordered[ALERTS_SHOWN:]
    body.extend(alert_html(a) for a in head)
    if tail:
        body.append(f'<details class="why"><summary>{len(tail)} more '
                    f'({sum(1 for a in tail if a["sev"] == "red")} red, '
                    f'{sum(1 for a in tail if a["sev"] != "red")} amber)</summary><div>'
                    + "".join(alert_html(a) for a in tail) + "</div></details>")
    if dis:
        body.append(f'<details class="why"><summary>{len(dis)} signal disagreement(s) — both shown, '
                    'neither picked</summary><div>')
        body.append('<div class="scroll"><table><thead><tr><th>Seat</th><th>About</th>'
                    '<th>Signal A</th><th>Signal B</th><th>Why it matters</th></tr></thead><tbody>')
        for d in dis:
            body.append(f'<tr><td>{e(d["seat"])}</td><td>{e(d["what"])}</td>'
                        f'<td class="t-warn">{e(d["a"])}</td><td class="t-warn">{e(d["b"])}</td>'
                        f'<td class="prose">{e(d["why"])}</td></tr>')
        body.append("</tbody></table></div></div></details>")
    body.append("</div>")
    sev = sum(1 for a in alerts if a["sev"] == "red")
    sub = f"{len(alerts)} anomaly · {sev} red · {len(dis)} disagreement(s)"
    return panel(3, "Alerts", sub, "".join(body))

BUCKET_LABEL = {
    "needs-approval": ("NEEDS APPROVAL", "bad", "it says it is waiting on a ruling only a human can give"),
    "needs-input": ("NEEDS INPUT", "bad", "it reported itself blocked on a human — resumable, not failed"),
    "failed": ("FAILED / DEAF", "bad", "it cannot be reached, or cannot hear mail sent to it"),
    "spinning": ("SPINNING / FALLING BEHIND", "warn",
                 "burning effort with nothing coming out, or a queue growing faster than it drains"),
    "working": ("WORKING", "good", "producing within its own cadence"),
    "idle": ("IDLE", "unknown", "listening, nothing outstanding — the resting state"),
}

def seat_row(ms, M) -> str:
    s = ms["seat"]
    sid = s.get("id")
    d = ms["depth"]
    cad = ms["cad"]
    depth_now = (s.get("inbox_unread") or 0)
    wait_role = []
    if sid in M["cycle_seats"]:
        wait_role.append('<span class="chip bad" title="in a reply cycle — a deadlock">cycle</span>')
    if sid in M["blocked_set"]:
        wait_role.append('<span class="chip bad" title="another seat is waiting on a reply from this one">'
                         'blocking</span>')
    if sid in M["waiting_set"]:
        wait_role.append('<span class="chip warn" title="this seat is waiting on a reply from someone else">'
                         'blocked</span>')
    dl = ms["delta"]
    if cad.get("verdict") == "stalled":
        cad_chip = '<span class="chip warn">stalled</span>'
    elif cad.get("verdict") == "on-cadence":
        cad_chip = '<span class="chip good">on time</span>'
    else:
        cad_chip = '<span class="chip unk">no cadence</span>'
    if cad.get("silence") is None:
        cad_line = "&mdash;"
    elif cad.get("verdict") == "no-cadence":
        # no deadline is claimed, so none is shown: quoting one here would
        # contradict the chip beside it
        cad_line = f'silent {dur(cad.get("silence"), short=True)} · no deadline claimed'
    elif cad.get("deadline"):
        cad_line = (f'silent {dur(cad.get("silence"), short=True)} · normal &le; '
                    f'{dur(cad.get("deadline"), short=True)}')
    else:
        cad_line = f'silent {dur(cad.get("silence"), short=True)}'
    return (
        f'<tr data-bucket="{e(ms["bucket"])}" data-depth="{depth_now}" data-name="{e(sid)}" '
        f'data-pos="{ms["n"]}" data-age="{cad.get("silence") or 0}">'
        # 1 seat
        f'<td class="c-seat"><span class="pos">{ms["n"]:02d}</span> <b>{e(sid)}</b>'
        f'<i class="sub">{e(s.get("project") or s.get("role") or "")}</i></td>'
        # 2 state: two axes, composite, then the evidence strip
        f'<td class="c-state">{two_axis_cell(ms["liv"], ms["occ"])}'
        f'<div class="row-2">{vol("<b class=" + chr(34) + "comp " + TONE_CLASS.get(ms["tone"], "t-unk") + chr(34) + ">" + e(ms["composite"]) + "</b>", unknown="<b class=" + chr(34) + "comp t-unk" + chr(34) + ">Unknown (stale)</b>")}'
        + ('<span class="chip unk" title="self-reported by the seat, not verified">self-reported</span>'
           if ms["blocked"] else "")
        + f'</div><div class="row-2">{slots_inline(ms)}</div></td>'
        # 3 mailbox depth
        f'<td class="c-depth num">{mono(str(depth_now))} {sparkline(d, width=64, height=16)}'
        + (f'<i class="sub t-bad">+{d["grew_last_3h"]} in 3h</i>' if d and d["growing"] else "")
        + (f'<i class="sub">oldest {mono(e(dur(s.get("unread_age_seconds"), short=True)))}</i>'
           if s.get("unread_age_seconds") else "")
        + "</td>"
        # 4 cadence
        f'<td class="c-cad" title="{e(cad.get("why") or "")}">{cad_chip}'
        f'<i class="sub">{cad_line}</i>'
        f'<i class="sub dim">{e(cad.get("n") or 0)} events: {e(", ".join(cad.get("kinds") or []) or "none")}</i>'
        "</td>"
        # 5 window delta
        f'<td class="c-delta num" title="commits · messages sent · messages received, inside the '
        f'{e(M["meta"].get("mail_window_hours", "?"))}h window">'
        f'{vol(str(dl["commits"]))}c &middot; {vol(str(dl["sent"]))}&uarr; &middot; {vol(str(dl["recv"]))}&darr;'
        + ('<i class="sub dim">commits capped at 5</i>' if dl.get("commits_capped") else "")
        + "</td>"
        # 6 wait-for
        f'<td class="c-wait">{"".join(wait_role) or "<i class=\'sub dim\'>&mdash;</i>"}</td>'
        # 7 why
        f'<td class="c-why">{e(ms["bucket_why"])}</td></tr>')

def render_triage(M) -> str:
    seats = M["seats"]
    order = M["bucket_order"]
    body = ['<div class="pad">']
    who = M["ident"]["human_short"]
    body.append(f'<p class="note"><b>Ranked by who needs {e(who)}</b>, not by roster position. '
                'Idle seats collapse; nothing else does. Sort any column — buckets stay grouped.</p>')
    body.append(why("how a seat lands in a bucket, and what the two axes mean",
                    'Bucket order is fixed: needs-approval &rarr; needs-input &rarr; failed &rarr; spinning &rarr; '
                    'working &rarr; idle. Seven equal rows would leave the ranking for you to do.',
                    'Colour carries <b>liveness</b> (live / never-started / stopped-or-lost / unreachable); shape '
                    'carries <b>occupancy</b> (working / waiting-for-mail / interrupted / spinning). They are '
                    'independent: a seat can be interrupted on a human ruling while its process is dead.',
                    '"Never started" is not "down", and "lost" is not "stopped". Nothing on this filesystem writes '
                    'an exit record, so those two are printed together and timestamped rather than guessed apart.',
                    'The <i>ses / box / wrk</i> strip is the evidence behind the state — hover any of it for the '
                    'full derivation, or read panel 5 for all of it.',
                    'The ranking is volatile: it was computed at snapshot time and does not re-rank while the page '
                    'sits open. The state cells fog; the order does not move.'))
    # column order must match seat_row() exactly: seat, state, depth, cadence,
    # delta, wait-for, why
    body.append('<div class="scroll"><table id="triage"><thead><tr>'
                '<th data-sort="pos" tabindex="0" title="click to sort by roster position">Seat</th>'
                '<th title="colour = liveness, shape = occupancy; the strip below is the evidence">'
                'State <span class="hint">liveness × occupancy</span></th>'
                '<th data-sort="depth" tabindex="0" title="click to sort — the MsgQ column, first symptom of a '
                'seat falling behind">Mailbox <span class="hint">depth · 24h</span></th>'
                '<th data-sort="age" tabindex="0" title="click to sort by silence">Cadence '
                '<span class="hint">its own</span></th>'
                f'<th title="commits · sent · received">&Delta; '
                f'<span class="hint">{e(M["meta"].get("mail_window_hours", "?"))}h</span></th>'
                '<th>Wait-for</th><th>Why it is here</th>'
                "</tr></thead><tbody>")
    for b in order:
        rows = [ms for ms in seats if ms["bucket"] == b]
        if not rows:
            continue
        label, tone, blurb = BUCKET_LABEL[b]
        collapse = (b == "idle" and len(rows) > 3)
        body.append(f'<tr class="bucket {TONE_CLASS.get(tone, "t-unk")}"><td colspan="7">'
                    f'<b>{e(label)}</b> · {len(rows)} '
                    f'<span class="prose" style="color:var(--ink-3)">{e(blurb)}</span></td></tr>')
        if collapse:
            names = ", ".join(ms["seat"].get("id") for ms in rows)
            body.append(f'<tr class="collapsed-row"><td colspan="7">'
                        f'<details><summary>{len(rows)} idle seats collapsed — {e(names)}</summary>'
                        f'<div class="scroll"><table><tbody>'
                        + "".join(seat_row(ms, M) for ms in rows)
                        + "</tbody></table></div></details></td></tr>")
        else:
            body.extend(seat_row(ms, M) for ms in rows)
    body.append("</tbody></table></div>")
    body.append("</div>")
    counts = {}
    for ms in seats:
        counts[ms["bucket"]] = counts.get(ms["bucket"], 0) + 1
    sub = " · ".join(f'{counts[b]} {BUCKET_LABEL[b][0].lower()}' for b in order if counts.get(b))
    return panel(2, f"Seats ranked by who needs {who}", sub, "".join(body))

def render_legend() -> str:
    def row(glyph, name, meaning):
        return (f'<li><span class="slot-g t-unk" style="vertical-align:middle">{glyph}</span> '
                f'<b>{e(name)}</b> — <span class="prose">{e(meaning)}</span></li>')
    return (
        '<details><summary>State vocabulary — three slots, never one badge</summary><div class="pad">'
        '<div class="cards">'
        '<div class="card"><header><span class="nm">SESSION</span><span class="meta">volatile</span></header>'
        '<div class="body"><ul class="tight mini">'
        + row(g_session("filled"), "filled square", "a process is attributed to this seat")
        + row(g_session("hollow"), "hollow square", "no process could be attributed")
        + row(g_session("half"), "half square", "ambiguous — more than one candidate process, or a forked/resumed one")
        + row(g_session("dash"), "dash", "not checked — home missing or the process table was unreadable")
        + '</ul></div></div>'
        '<div class="card"><header><span class="nm">MAILBOX</span><span class="meta">monotone</span></header>'
        '<div class="body"><ul class="tight mini">'
        + row(g_mailbox("clear", 0), "empty circle", "new/ is clear and a watcher names this seat")
        + row(g_mailbox("working", 3), "circle with N", "N in new/, oldest under 30 min — working through it")
        + row(g_mailbox("lagging", 3), "underlined", "oldest unread over 30 min — lagging")
        + row(g_mailbox("deaf", 9), "boxed + underlined", "DEAF: oldest unread over 4h, OR no watcher process, OR cur/ empty while new/ is not")
        + row(g_mailbox("dash", 0), "dash", "no maildir — nothing can be delivered")
        + '</ul></div></div>'
        '<div class="card"><header><span class="nm">WORK</span><span class="meta">volatile</span></header>'
        '<div class="body"><ul class="tight mini">'
        + row(g_work("producing"), "filled chevron", "producing — the snapshot's busy signal fired")
        + row(g_work("recent"), "outlined chevron", "produced within the last hour, nothing since")
        + row(g_work("quiet"), "bar", "quiet — no work signal fired")
        + row(g_work("dash"), "dash", "unknown — no observable output channel")
        + '</ul></div></div>'
        '<div class="card"><header><span class="nm">LIVENESS</span><span class="meta">carried by colour</span>'
        '</header><div class="body"><ul class="tight mini">'
        + "".join(f'<li><span class="{TONE_CLASS.get(LIVENESS_TONE.get(k, "unknown"))}">&#9632;</span> '
                  f'<b>{e(k)}</b> — <span class="prose">{e(v)}</span></li>'
                  for k, v in LIVENESS_DOC.items())
        + '</ul></div></div>'
        '<div class="card"><header><span class="nm">OCCUPANCY</span><span class="meta">carried by shape</span>'
        '</header><div class="body"><ul class="tight mini">'
        + "".join(row(g_occ(k), k, v) for k, v in OCCUPANCY_DOC.items())
        + '</ul></div></div>'
        '<div class="card"><header><span class="nm">COMPOSITE</span><span class="meta">derived</span></header>'
        '<div class="body"><ul class="tight mini">'
        + "".join(f'<li><b>{e(k)}</b> — <span class="prose">{e(v)}</span></li>'
                  for k, v in COMPOSITE_DOC.items())
        + '</ul><p class="note" style="margin-top:8px">The composite is printed beside the three slots '
          'that produced it. If they disagree with the word, believe the slots. The composite and the '
          'liveness&times;occupancy pair are computed from <b>different evidence</b> — the composite from the '
          'snapshot\'s fixed window, the two axes from the seat\'s own cadence and a live CPU sample — so they '
          'can disagree. That disagreement is information, not a bug: it usually means the fixed window is '
          'wrong about this particular seat.</p></div></div>'
        '</div></div></details>')

def jack(ms, extra_class="") -> str:
    s = ms["seat"]
    ses = s.get("session") or {}
    bits = []
    if s.get("role"):
        bits.append(s["role"])
    if s.get("model"):
        bits.append(s["model"])
    if ses.get("model_flag") and ses.get("model_flag") != s.get("model"):
        bits.append(f"argv:{ses['model_flag']}")
    if s.get("runtime"):
        bits.append(s["runtime"])
    # This panel's job is STRUCTURE: who reports to whom, in fixed positions.
    # State belongs to panel 2 and evidence to panel 5, so a jack carries only
    # enough state to make a dark or deaf seat impossible to miss in the shape.
    depth = ms["seat"].get("inbox_unread") or 0
    flags = []
    if ms["m"]["state"] == "deaf":
        flags.append('<span class="chip bad">deaf</span>')
    if ms["liv"]["state"] in ("stopped-or-lost", "never-started", "unreachable"):
        flags.append(f'<span class="chip bad">{e(ms["liv"]["state"])}</span>')
    if depth:
        flags.append(f'<span class="chip warn" title="unread in new/">{mono(str(depth))} queued</span>')
    return (f'<div class="jack {extra_class}">'
            f'<div class="jid"><span class="pos">{ms["n"]:02d}</span>'
            f'<span class="nm">{e(s.get("id"))}</span></div>'
            f'<div class="jack-meta">{e(" · ".join(bits))}</div>'
            f'<div class="jack-axis">{two_axis_cell(ms["liv"], ms["occ"])}</div>'
            + (f'<div class="jack-flags">{"".join(flags)}</div>' if flags else "")
            + f'<a class="jack-link" href="#p2" title="full state, mailbox depth and cadence for this seat">'
              f'state &rarr;</a>'
            + "</div>")

def render_tree(M) -> str:
    seats = M["seats"]
    meta = M["meta"]
    parent = next((x for x in seats if (x["seat"].get("role") == "parent")), None)
    council = [x for x in seats if x["seat"].get("role") == "council"]
    kids = [x for x in seats if x["seat"].get("role") not in ("parent", "council")]
    ident = M["ident"]
    site = ident["site"]
    human = ident["human"]
    body = ['<div class="tree">']
    body.append('<p class="note">Who reports to whom. Fixed roster order — position <b>01…{n}</b> stays where '
                'it is even when a seat goes dark, so the shape is memorizable. State lives in '
                '<a href="#p2">panel 2</a>; only a fault worth seeing in the shape is repeated here.</p>'
                .format(n=len(seats)))
    body.append(f'<div class="tier"><div class="jack human"><div class="jid">'
                f'<span class="pos">HU</span><span class="nm">{e(human)}</span>'
                f'<span class="meta">human · {e(site.get("machine") or "machine not in roster")}</span></div>'
                f'<div class="note" style="margin:6px 0 0">Not a seat. Has no maildir and no process. '
                f'Instructions enter as prompts, so this network can observe nothing about him except '
                f'his commits.</div></div></div>')
    body.append('<div class="rootline"><i></i>prompts · not mail · unobservable</div>')
    if parent:
        body.append('<div class="tier lateral">' + jack(parent))
        if council:
            body.append('<div class="dotline"><span>advisory · no authority</span></div>')
            body.append("".join(jack(c) for c in council))
        body.append("</div>")
    body.append('<div class="branchline"></div>')
    body.append('<div class="scroll"><div class="kids">')
    for k in kids:
        body.append(f'<div class="kid">{jack(k)}</div>')
    body.append("</div></div>")
    body.append("</div>")
    body.append(render_legend())
    counts = meta.get("counts") or {}
    rules = (meta.get("activity_rules") or {})
    sub = (f"{counts.get('seats','?')} seats · {vol(str(counts.get('sessions_live','?')))} live sessions · "
           f"the snapshot's own fixed-{rules.get('busy_window_seconds', 600)}s-window counts: "
           f"{vol(str(counts.get('seats_live_busy','?')))} busy / "
           f"{vol(str(counts.get('seats_live_idle','?')))} idle / "
           f"{vol(str(counts.get('seats_dark','?')))} dark — panel 2 judges the same seats against their own "
           "cadence and does not always agree")
    return panel(4, "The supervision tree", sub, "".join(body))

def render_work(M) -> str:
    cards = []
    inflight = [i for i in (M["board"].get("items") or [])
                if (i.get("section") or "").upper().startswith("IN FLIGHT")]
    for ms in M["seats"]:
        s, repo = ms["seat"], ms["repo"]
        sid = s.get("id")
        ses = s.get("session") or {}
        mine = [i for i in inflight if i.get("agent") == sid]
        c = [f'<div class="card"><header><span class="pos">{ms["n"]:02d}</span>'
             f'<span class="nm">{e(sid)}</span>'
             f'<span class="meta">{e(s.get("project") or "no project")}</span>'
             f'<span class="composite {TONE_CLASS.get(ms["tone"],"t-unk")}" style="margin-left:auto">'
             f'{vol("<b>"+e(ms["composite"])+"</b>", unknown="<b>Unknown (stale)</b>")}</span>'
             '</header><div class="body">']
        # in-flight
        c.append("<h4>In flight — from the board (hand-maintained, not a protocol object)</h4>")
        if mine:
            c.append('<ul class="tight mini">' + "".join(
                f'<li><span class="verbatim">{e(i.get("task") or i.get("raw"))}</span>'
                + (f' <span class="badge">{e(i.get("state"))}</span>' if i.get("state") else "")
                + f'<br><span style="color:var(--ink-3)">{e(M["board"].get("path"))}:{e(i.get("line"))}</span></li>'
                for i in mine) + "</ul>")
        else:
            c.append('<p class="empty mini">No board item resolves to this seat. The board is markdown: an item '
                     'only binds to a seat when its first field is exactly the seat id.</p>')
        # last outbound
        c.append("<h4>Last outbound — subjects are the sender's own words, not verified state</h4>")
        if ms["outs"]:
            c.append('<ul class="tight mini">' + "".join(
                f'<li>{age_html(epoch_of(m.get("timestamp")))} '
                f'<span class="badge {e(m.get("type") or "")}">{e(m.get("type") or "?")}</span> '
                f'&rarr; {e(m.get("to"))}<br><span class="subject">{e(m.get("subject"))}</span></li>'
                for m in ms["outs"]) + "</ul>")
            if ms["blocked"]:
                c.append('<p class="note t-warn" style="margin:6px 0 0">Its last word was <b>type: blocked</b> and '
                         'nothing has arrived for it since — self-reported, unverified.</p>')
        else:
            c.append('<p class="empty mini">Nothing sent inside the '
                     f'{e((M["meta"] or {}).get("mail_window_hours","?"))}h mail window. There are no outboxes in '
                     'AgentMail: sent mail is only visible while it sits in someone else\'s maildir.</p>')
        # everything below is evidence: one line of summary, the rest folded
        cad, dl = ms["cad"], ms["delta"]
        cad_word = ("stalled by its own standard" if cad.get("verdict") == "stalled"
                    else ("on cadence" if cad.get("verdict") == "on-cadence" else "no cadence established"))
        c.append(f'<div class="card-sum"><span class="{TONE_CLASS.get("warn" if cad.get("verdict")=="stalled" else ("good" if cad.get("verdict")=="on-cadence" else "unknown"))}">'
                 f'{e(cad_word)}</span> · {vol(str(dl["commits"]))}c {vol(str(dl["sent"]))}&uarr; '
                 f'{vol(str(dl["recv"]))}&darr; in {e(M["meta"].get("mail_window_hours","?"))}h · '
                 f'mailbox {mono(str(s.get("inbox_unread") or 0))} {sparkline(ms["depth"], width=54, height=14)}'
                 "</div>")
        c.append('<details class="why"><summary>evidence — cadence, session, mailbox, repo</summary><div>')
        c.append("<h4>Its own cadence — no borrowed threshold</h4><dl class=\"kv mini\">")
        c.append(f'<dt>verdict</dt><dd>' + (
            f'<span class="t-warn">stalled by its own standard</span>' if cad.get("verdict") == "stalled"
            else ('<span class="t-good">on cadence</span>' if cad.get("verdict") == "on-cadence"
                  else hole("no verdict", cad.get("why", "")))) + "</dd>")
        c.append(f'<dt>rule</dt><dd class="prose">{e(cad.get("why") or "")}</dd>')
        c.append(f'<dt>events</dt><dd>{e(cad.get("n"))} observed ({e(", ".join(cad.get("kinds") or []) or "none")})'
                 + (f' · typical gap {e(dur(cad.get("typical"), short=True))}' if cad.get("typical") else "")
                 + "</dd>")
        c.append(f'<dt>second opinion</dt><dd>the snapshot\'s fixed '
                 f'{e((M["meta"].get("activity_rules") or {}).get("busy_window_seconds", 600))}s window says '
                 f'<b>{e(s.get("activity"))}</b> ({e(s.get("activity_confidence"))} confidence)</dd>')
        c.append(f'<dt>window delta</dt><dd>{vol(str(dl["commits"]))} commit(s), {vol(str(dl["sent"]))} sent, '
                 f'{vol(str(dl["recv"]))} received in the last '
                 f'{e(M["meta"].get("mail_window_hours", "?"))}h'
                 + (' <span class="hole" title="git log is capped at 5 commits per repo in the snapshot">'
                    'commit delta is capped at 5</span>' if dl.get("commits_capped") else "")
                 + "</dd>")
        if ms["cpu"]:
            pct = "%.0f%%" % ms["cpu"]["pct"]
            gap = "%.1f" % ms["cpu"].get("gap", CPU_SAMPLE_GAP)
            cum = dur(int(ms["cpu"]["cum"]), short=True)
            c.append('<dt>cpu now</dt><dd>' + vol(e(pct)) + f' over a {gap}s sample taken by this tool '
                     f'<span style="color:var(--ink-3)">(cumulative {e(cum)} — which cannot tell working from '
                     "looping, and is why the delta is sampled)</span></dd>")
        elif (s.get("session") or {}).get("pid"):
            c.append('<dt>cpu now</dt><dd>' + hole("not sampled", "ps could not be read for this pid") + "</dd>")
        c.append("</dl>")
        # totals, deliberately demoted
        c.append(f'<p class="note" style="margin:6px 0 0;font-size:11px">Lifetime totals '
                 f'({e(num(s.get("mail_received_total")))} in / {e(num(s.get("mail_sent_total")))} out) prove '
                 f'this seat once existed, not that it is doing anything — that is what the deltas above are for.'
                 "</p>")
        # session facts
        c.append("<h4>Session</h4><dl class=\"kv mini\">")
        c.append(f'<dt>liveness</dt><dd class="{TONE_CLASS.get(LIVENESS_TONE.get(ms["liv"]["state"], "unknown"))}">'
                 f'{e(ms["liv"]["state"])}'
                 + (f' — last output {age_html(ms["liv"]["at"])}' if ms["liv"]["state"] == "stopped-or-lost"
                    and ms["liv"].get("at") else "")
                 + f'<div class="prose" style="color:var(--ink-3)">{e(ms["liv"]["detail"])}</div></dd>')
        c.append(f'<dt>occupancy</dt><dd>{e(ms["occ"]["state"])}'
                 f'<div class="prose" style="color:var(--ink-3)">{e(ms["occ"]["detail"])}</div></dd>')
        c.append(f'<dt>evidence</dt><dd>{e(ses.get("detection") or "—")}</dd>')
        c.append(f'<dt>pid</dt><dd>{vol(e(num(ses.get("pid"))))}</dd>')
        c.append(f'<dt>uptime</dt><dd>{vol(e(ses.get("elapsed_human") or "—"))}'
                 + (f' <span style="color:var(--ink-3)">(started {age_html(epoch_of(ses.get("started_at")))})</span>'
                    if ses.get("started_at") else "") + "</dd>")
        c.append(f'<dt>cwd</dt><dd>{e(ses.get("cwd") or "—")}</dd>')
        c.append(f'<dt>perms</dt><dd>' + (
            '<span class="t-warn">--dangerously-skip-permissions</span>'
            if ses.get("dangerously_skip_permissions") else "prompted") + "</dd>")
        if ses.get("model_flag") and ses.get("model_flag") != s.get("model"):
            c.append(f'<dt class="t-bad">model</dt><dd class="t-bad">roster {e(s.get("model"))} '
                     f'&ne; argv {e(ses.get("model_flag"))}</dd>')
        if len([x for x in (ses.get("candidates") or []) if not x.get("claimed_by_other_seat")]) > 1:
            c.append('<dt class="t-warn">candidates</dt><dd class="t-warn">'
                     + e(", ".join(f'{x.get("pid")}({x.get("kind")})' for x in ses.get("candidates") or []))
                     + "</dd>")
        if ses.get("note"):
            c.append(f'<dt>note</dt><dd class="prose">{e(ses["note"])}</dd>')
        c.append("</dl>")
        # mailbox facts
        c.append("<h4>Mailbox — depth first (observer's MsgQ column)</h4><dl class=\"kv mini\">")
        d = ms["depth"]
        c.append('<dt>depth</dt><dd>' + mono(e(str(s.get("inbox_unread") or 0))) + " " + sparkline(d)
                 + (f' <span class="t-bad">growing: +{d["grew_last_3h"]} in 3h</span>'
                    if d and d["growing"] else "")
                 + ('<div style="color:var(--ink-3)">depth over the last '
                    f'{d["window_hours"]}h, from arrival times of mail still in new/ — a lower bound; anything '
                    'already read left no trace</div>' if d else "")
                 + "</dd>")
        c.append(f'<dt>new/</dt><dd>{mono(e(str(s.get("inbox_unread", "—"))))} '
                 + (f'· oldest {mono(e(dur(s.get("unread_age_seconds"), short=True)))} old'
                    if s.get("unread_age_seconds") else "") + "</dd>")
        c.append(f'<dt>cur/</dt><dd>{e(num(s.get("inbox_processed")))} <span style="color:var(--ink-3)">'
                 '(a rename, not a reply)</span></dd>')
        c.append(f'<dt>watcher</dt><dd>{vol(("yes" if s.get("watcher_running") else chr(60)+"span class=\'t-bad\'"+chr(62)+"none"+chr(60)+"/span"+chr(62)))}</dd>')
        c.append(f'<dt>last in</dt><dd>{age_html(epoch_of(s.get("last_received_at")))} '
                 f'from {e(s.get("last_received_from") or "—")}</dd>')
        c.append(f'<dt>last out</dt><dd>{age_html(epoch_of(s.get("last_sent_at")))} '
                 f'to {e(s.get("last_sent_to") or "—")}</dd>')
        c.append(f'<dt>totals</dt><dd>{e(num(s.get("mail_received_total")))} in / '
                 f'{e(num(s.get("mail_sent_total")))} out '
                 '<span style="color:var(--ink-3)">(archived mail is gone from both)</span></dd>')
        c.append("</dl>")
        # repo
        c.append("<h4>Repo</h4>")
        if not repo:
            c.append('<p class="empty mini">' + e(
                f"{s.get('home')} is not a git work tree — this seat has no repo evidence at all, so its "
                "busy signal is substituted from mail/bridge activity (confidence: "
                f"{s.get('activity_confidence') or 'unknown'}).") + "</p>")
        else:
            fa = next((f for f in M["fetches"] if f.get("seat") == sid), None)
            c.append('<dl class="kv mini">')
            c.append(f'<dt>path</dt><dd>{e(repo.get("path"))}</dd>')
            c.append(f'<dt>branch</dt><dd>{e(repo.get("branch") or "—")}'
                     + (f' <span style="color:var(--ink-3)">&rarr; {e(repo.get("upstream"))}</span>'
                        if repo.get("upstream") else
                        ' <span class="hole" title="no upstream — ahead/behind are undefined, not zero">'
                        'no upstream</span>') + "</dd>")
            ab = (f'{vol(e(num(repo.get("ahead"))))} ahead / {vol(e(num(repo.get("behind"))))} behind'
                  if repo.get("upstream") else hole("undefined", "no upstream configured"))
            c.append(f'<dt>ahead/behind</dt><dd>{ab}<br><span style="color:var(--ink-3)">measured against a ref '
                     'last fetched ' + (age_html(fa["epoch"]) if fa and fa.get("epoch")
                                        else hole("never", (fa or {}).get("reason") or "")) + "</span></dd>")
            unc = repo.get("uncommitted_files")
            br = repo.get("uncommitted_breakdown") or {}
            c.append(f'<dt>dirty</dt><dd>{vol(e(num(unc)) + " file(s)")}'
                     + (f' <span style="color:var(--ink-3)">({br.get("staged",0)} staged, '
                        f'{br.get("unstaged",0)} unstaged, {br.get("untracked",0)} untracked)</span>'
                        if unc else "") + "</dd>")
            h = repo.get("head") or {}
            c.append(f'<dt>head</dt><dd><b>{e(h.get("sha") or "—")}</b> {age_html(epoch_of(h.get("committed_at")))} '
                     f'· {e(h.get("author") or "—")}<br><span class="subject">{e(h.get("subject"))}</span></dd>')
            c.append("</dl>")
        c.append("</div></details>")
        c.append("</div></div>")
        cards.append("".join(c))
    return panel(5, "Work per seat", "in-flight · last outbound · session · mailbox · repo",
                 '<div class="pad"><div class="cards">' + "".join(cards) + "</div></div>")

def render_waitgraph(M) -> str:
    ids = M["seat_ids"]
    edges = M["edges"]
    if not edges:
        return ('<p class="empty">No seat owes another a reply. The wait-for graph is empty — that is the only '
                'state in which nothing here can deadlock.</p>')
    # circular layout; the geometry is computed here so the SVG is static
    import math
    n = len(ids)
    W = H = 320
    R = 116
    pos = {}
    for i, sid in enumerate(ids):
        a = -math.pi / 2 + 2 * math.pi * i / max(n, 1)
        pos[sid] = (W / 2 + R * math.cos(a), H / 2 + R * math.sin(a))
    parts = [f'<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
             f'aria-label="wait-for graph: who owes whom a reply">'
             '<defs>'
             '<marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" '
             'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="currentColor"/></marker>'
             "</defs>"]
    for (a, b), meta_ in edges.items():
        if a not in pos or b not in pos:
            continue
        x1, y1 = pos[a]
        x2, y2 = pos[b]
        dx, dy = x2 - x1, y2 - y1
        d = (dx * dx + dy * dy) ** 0.5 or 1
        x1 += dx / d * 26
        y1 += dy / d * 26
        x2 -= dx / d * 30
        y2 -= dy / d * 30
        in_cycle = a in M["cycle_seats"] and b in M["cycle_seats"]
        cls = "wf-cycle" if in_cycle else "wf-edge"
        parts.append(f'<line class="{cls}" x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                     f'marker-end="url(#ah)"><title>{e(a)} owes {e(b)} a reply — oldest '
                     f'{e(dur(meta_.get("age"), short=True))}</title></line>')
    for sid, (x, y) in pos.items():
        cls = "wf-node"
        if sid in M["cycle_seats"]:
            cls += " wf-n-cycle"
        elif sid in M["blocked_set"]:
            cls += " wf-n-blocking"
        elif sid in M["waiting_set"]:
            cls += " wf-n-waiting"
        short = M["short_seat"](sid)
        parts.append(f'<g class="{cls}"><circle cx="{x:.1f}" cy="{y:.1f}" r="22"/>'
                     f'<text x="{x:.1f}" y="{y + 3:.1f}" text-anchor="middle" font-size="8.5" '
                     f'font-family="ui-monospace,Menlo,monospace">{e(short[:9])}</text></g>')
    parts.append("</svg>")
    rows = ['<div class="scroll"><table><thead><tr><th>Owes a reply</th><th>To</th><th>Oldest debt</th>'
            '<th>Threads</th><th>In a cycle</th></tr></thead><tbody>']
    for (a, b), m_ in sorted(edges.items(), key=lambda kv: -(kv[1].get("age") or 0)):
        cyc = a in M["cycle_seats"] and b in M["cycle_seats"]
        rows.append(f'<tr><td class="t-bad">{e(a)}</td><td class="t-warn">{e(b)}</td>'
                    f'<td>{age_html(M["snap_epoch"] - (m_.get("age") or 0)) if m_.get("age") is not None else hole("unknown")}</td>'
                    f'<td>{e(m_.get("n"))}</td>'
                    f'<td>{"<b class=\'t-bad\'>yes — deadlock</b>" if cyc else "—"}</td></tr>')
    rows.append("</tbody></table></div>")
    cyc_html = ""
    if M["cycles"]:
        cyc_html = ('<div class="alert red" style="margin-top:10px"><span class="sev">deadlock</span><div>'
                    + "".join(f'<div class="ti">{e(" → ".join(c))}</div>' for c in M["cycles"])
                    + '<div class="ev">Every seat in the ring is waiting for the next one. None of them will '
                      'move on its own — the ring only breaks from outside it.</div></div></div>')
    return ('<div class="wfwrap"><div class="wfgraph">' + "".join(parts) + "</div><div class=\"wftable\">"
            + "".join(rows) + cyc_html + "</div></div>"
            '<p class="note">Arrows point from the seat that owes to the seat that is waiting. '
            '<span class="t-bad">Red</span> = this seat is blocking someone else; '
            '<span class="t-warn">orange</span> = this seat is itself blocked. A ring is a deadlock.</p>')

def render_mail(M) -> str:
    meta = M["meta"]
    counts = meta.get("counts") or {}
    body = ['<div class="pad">']

    # (a) reply debt
    n_read = sum(1 for d in M["debts"] if d["kind"] == "read-not-replied")
    n_new = sum(1 for d in M["debts"] if d["kind"] == "not-even-read")
    body.append('<h4 style="margin:0 0 4px;font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;'
                'color:var(--ink-2)">a · Reply-debt ledger <span class="badge">inferred — verify before acting'
                '</span></h4>')
    body.append(f'<p class="note"><b>{n_new}</b> not even read · <b>{n_read}</b> read but not replied · '
                'oldest first.</p>')
    body.append(why("what counts as a debt, and why the second kind is the one that rots",
                    '<b>NOT-EVEN-READ</b>: the file is still in <code>new/</code>. '
                    '<b>READ-BUT-NOT-REPLIED</b>: it was renamed into <code>cur/</code> and nothing has come back '
                    'on that thread since.',
                    'Under SPEC §3 that rename <em>is</em> the acknowledgement — which is exactly why it proves '
                    'nothing was done. Read-and-forgotten is the common case and the corrosive one, and it had no '
                    'representation anywhere before this ledger.',
                    'This is inference. A reply that travelled out of band, on another thread, or was since '
                    'archived, appears here as a debt that does not exist. Verify a row before acting on it.'))
    if M["debts"]:
        body.append('<div class="scroll"><table><thead><tr><th>Age</th><th>Kind</th><th>Owes</th><th>To</th>'
                    '<th>Thread</th><th>Type</th><th>Ack</th><th>Nudge</th><th>Last message (their words)</th>'
                    '</tr></thead><tbody>')
        for d in M["debts"]:
            kind_cell = ('<span class="t-bad">not even read</span>' if d["unread"]
                         else '<span class="t-warn">read, not replied</span>')
            nudge = ""
            if d.get("age"):
                who = d["to"]
                nudge = (f'sent {dur(d["age"], short=True)} ago — follow up?'
                         if not d["unread"] else f'unopened for {dur(d["age"], short=True)}')
            body.append(
                f'<tr><td>{age_html(d["epoch"])}</td>'
                f'<td>{kind_cell}<div style="color:var(--ink-3);font-size:10px">{e(d.get("source"))}</div></td>'
                f'<td><b>{e(d["owes"])}</b></td><td>{e(d["to"])}</td>'
                f'<td>{e(d["thread"] or "(no thread header)")}'
                + (' <span class="badge">synthetic</span>' if d.get("synthetic") else "")
                + f' <span style="color:var(--ink-3)">{e(d.get("count"))} msg</span></td>'
                f'<td><span class="badge {e(d.get("type") or "")}">{e(d.get("type") or "?")}</span></td>'
                f'<td>{e(d.get("ack") or "—")}</td>'
                f'<td class="prose">{e(nudge)}</td>'
                f'<td class="subject">{e(d.get("subject"))}</td></tr>')
        body.append("</tbody></table></div>")
    else:
        body.append('<p class="empty">No outstanding reply debt of either kind.</p>')

    # (a2) wait-for graph
    body.append('<h4 style="margin:18px 0 4px;font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;'
                'color:var(--ink-2)">a2 · Wait-for graph — a cycle is a deadlock</h4>')
    body.append(render_waitgraph(M))

    # (a3) dead letters
    body.append('<h4 style="margin:18px 0 4px;font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;'
                'color:var(--ink-2)">a3 · Dead letters</h4>')
    if M["dead"]:
        body.append('<div class="scroll"><table><thead><tr><th>Seat</th><th>Kind</th><th>What</th><th>Age</th>'
                    "</tr></thead><tbody>")
        for x in M["dead"]:
            body.append(f'<tr><td>{e(x["seat"])}</td><td class="t-warn">{e(x["kind"])}</td>'
                        f'<td>{e(x["name"])}</td><td>{age_html(x["epoch"]) if x.get("epoch") else "—"}</td></tr>')
        body.append("</tbody></table></div>")
    else:
        body.append('<p class="empty">Nothing stranded in any <code>tmp/</code> older than '
                    f'{dur(TMP_STRANDED_SECONDS, short=True)}, and no message whose <code>to:</code> header '
                    'disagrees with the maildir it landed in.</p>')
    body.append(why("why anyone looks in tmp/ at all",
                    'SPEC §2 tells readers to ignore <code>tmp/</code>, so a delivery that died half-written is '
                    'invisible to every other tool in this network. That is precisely why it is counted here.',
                    'Names and mtimes only — never contents — and anything younger than '
                    f'{dur(TMP_STRANDED_SECONDS, short=True)} is skipped, because it may still be mid-write.'))

    # (b) pair matrix
    ids = M["seat_ids"]
    ident = M["ident"]
    human, human_short = ident["human"], ident["human_short"]
    mx = max([v for v in M["pairs"].values()] or [1])
    body.append('<h4 style="margin:18px 0 4px;font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;'
                'color:var(--ink-2)">b · Pair matrix — who wrote to whom</h4>')
    body.append(f'<p class="note">Senders down, recipients across · last '
                f'<b>{e(meta.get("mail_window_hours","?"))}h</b> only · activate a cell to filter the river '
                'below.</p>')
    body.append(why("what the window hides, and why one row is empty",
                    f'Counts cover {e(counts.get("messages_in_window","?"))} of '
                    f'{e(counts.get("messages_total","?"))} messages in the spool. Everything older is outside '
                    'the window: those cells are unmeasured, not zero.',
                    'Recipients come from the maildir the file physically sits in, not from the '
                    '<code>to:</code> header, which can lie.',
                    f'The {e(human_short)} row and column are <b>structurally empty, not silent</b>. No seat and '
                    'no maildir: instructions enter as prompts to a session and leave no file behind. A zero '
                    'there would be a lie — this page cannot observe that channel at all.'))
    body.append('<div class="scroll"><table class="matrix"><thead><tr><th class="rowhead">from \\ to</th>')
    for c in ids:
        body.append(f'<th class="colhead">{e(M["short_seat"](c))}</th>')
    body.append(f'<th class="colhead">{e(human_short)}</th></tr></thead><tbody>')
    for r in ids:
        body.append(f'<tr><th class="rowhead">{e(r)}</th>')
        for c in ids:
            n = M["pairs"].get((r, c), 0)
            if r == c:
                body.append('<td class="diag" title="a seat does not mail itself"></td>')
                continue
            a = 0.0 if not n else 0.10 + 0.35 * (n / mx)
            body.append(f'<td><span class="cell" role="button" tabindex="0" aria-pressed="false" '
                        f'data-f="{e(r)}" data-t="{e(c)}" data-n="{n}" style="--a:{a:.3f}" '
                        f'title="{e(r)} &rarr; {e(c)}: {n} message(s) in window">{n}</span></td>')
        body.append(f'<td><span class="struct" title="structurally empty">n/a</span></td>')
        body.append("</tr>")
    body.append(f'<tr><th class="rowhead">{e(human)}</th>')
    for c in ids:
        body.append('<td><span class="struct" title="structurally empty">n/a</span></td>')
    body.append('<td class="diag"></td></tr>')
    body.append("</tbody></table></div>")
    body.append('<div class="legend-ramp"><span>0</span>'
                + "".join(f'<i style="background:rgba(var(--accent-rgb),{0.10+0.35*(k/4):.2f})"></i>'
                          for k in range(5))
                + f'<span>{mx}</span><span style="margin-left:12px">msgs per pair, {e(meta.get("mail_window_hours","?"))}h window</span></div>')

    # (c) river
    rows = []
    for m in reversed(M["flow"]):
        ep = epoch_of(m.get("timestamp"))
        rows.append(
            f'<tr data-f="{e(m.get("from"))}" data-t="{e(m.get("to"))}">'
            f'<td>{age_html(ep)}</td>'
            f'<td style="color:var(--ink-3);white-space:nowrap">{e(m.get("timestamp"))}'
            + (f' <span class="badge" title="the sent: header was missing or malformed; the filename timestamp '
               f'was used">filename</span>' if m.get("timestamp_source") != "sent-header" else "")
            + f'</td><td>{e(m.get("from"))}</td><td>{e(m.get("to"))}</td>'
            f'<td><span class="badge {e(m.get("type") or "")}">{e(m.get("type") or "?")}</span></td>'
            f'<td>{e(m.get("thread") or "—")}</td>'
            f'<td>{"<span class=\'dot-unread\' title=\'still in new/\'>&#9679; unread</span>" if m.get("unread") else ""}</td>'
            f'<td class="subject">{e(m.get("subject"))}</td></tr>')
    river = (
        '<details id="riverwrap"><summary>c · Chronological river — every message in the '
        f'{e(meta.get("mail_window_hours","?"))}h window, newest first '
        f'({len(M["flow"])} rows)</summary><div class="pad">'
        '<span id="filterchip" class="filterchip" hidden><span></span>'
        '<button type="button" id="clearfilter" style="font:inherit;background:none;border:0;'
        'color:inherit;cursor:pointer;text-decoration:underline">clear</button></span>'
        '<p class="note">Subjects are what the sender chose to write. They are claims about work, never evidence '
        'of it. "unread" means the file is still in <code>new/</code>.</p>'
        '<div class="scroll"><table id="river"><thead><tr><th>Age</th><th>Sent (UTC)</th><th>From</th><th>To</th>'
        '<th>Type</th><th>Thread</th><th></th><th>Subject</th></tr></thead><tbody>'
        + "".join(rows) + "</tbody></table></div></div></details>")

    body.append("</div>")
    sub = (f'{e(counts.get("messages_total","?"))} messages · {e(counts.get("threads","?"))} threads · '
           f'{mono(e(str(counts.get("messages_unread","?"))) + " unread")}')
    return panel(6, "Mail", sub, "".join(body) + river)

def render_federation(M) -> str:
    fed = M["fed"]
    meta = M["meta"]
    site = M["ident"]["site"]
    mr = fed.get("mail_repo") or {}
    body = ['<div class="pad">']
    body.append('<p class="note">Three registers, never mixed: '
                '<span class="vis revealed">revealed</span> observed live here · '
                '<span class="vis fogged">fogged</span> last known, stamped · '
                '<span class="vis shrouded">shrouded</span> never observed.</p>')
    body.append(why("why a lost site goes UNKNOWN and not DOWN",
                    '<b>Revealed</b> is what this machine can see right now. <b>Fogged</b> is last-known state, '
                    'always stamped "as of T" and drawn dimmer and dashed — never redrawn as if it were current. '
                    '<b>Shrouded</b> is never observed at all: an outline and the reason, never a state.',
                    'Carrying a last-known value forward as though it were fresh is the cardinal sin of a panel '
                    'like this. Losing sight of something makes it UNKNOWN, not DOWN — the control plane lost '
                    'visibility, it did not observe a failure.',
                    'The two connectors below mean different things: a solid one-way arrow for code arriving by '
                    'git, and a dotted line ending in open air for a federation that is documented but not '
                    'configured.'))
    body.append('<div class="univ">')
    body.append('<div class="mine"><span class="vis revealed">revealed</span>'
                '<div style="font-weight:700;letter-spacing:.1em;text-transform:uppercase;'
                f'color:var(--accent)">site: {e(site.get("site") or "?")} · local</div>'
                f'<div class="mini" style="margin-top:6px">{e(site.get("seat_count") or 0)} seats · '
                f'machine {e(site.get("machine") or "?")} · human {e(site.get("human") or "?")} · '
                f'sync {e(site.get("sync") or "?")}</div>'
                '<ul class="tight mini" style="margin-top:6px">'
                + "".join(f'<li>{e(x)}</li>' for x in (site.get("seats") or []))
                + "</ul></div>")
    remotes = fed.get("remote_sites") or []
    if not remotes:
        body.append('<div class="other"><span class="vis shrouded">shrouded</span>'
                    '<div>no other universe is drawn<br><br>'
                    '<b>reason:</b> roster.json lists ' + str(len(fed.get("sites") or []))
                    + ' site(s), all local — no mail bridge, no seat in the roster, '
                    'and no remote on .agent-mail. Nothing has ever been observed there, so nothing is drawn: '
                    'not a seat, not a count, not an "unknown" state.</div></div>')
    else:
        for r in remotes:
            body.append('<div class="other"><span class="vis shrouded">shrouded</span><div>site: '
                        + e(r.get("site")) + '<br><br>'
                        '<b>outline only.</b> Its seats, their states and their activity are not observable '
                        'from this machine: ' + (
                            "no remote is configured on .agent-mail, so no mail from that site has ever arrived"
                            if not mr.get("remote_configured") else
                            "mail may replicate, but process state never does") + "</div></div>")
    body.append("</div>")

    # connectors
    body.append('<h4 style="margin:16px 0 6px;font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;'
                'color:var(--ink-2)">Connectors</h4>')
    body.append('<div class="conn"><span class="lbl">git · observation only · one-way</span>'
                '<span class="arrow-solid"></span></div>')
    body.append('<p class="note"><span class="vis fogged">fogged</span> every row below is aged by '
                '<b>its own</b> fetch, not by the snapshot.</p>')
    body.append(why("why a fresh snapshot does not refresh these numbers",
                    'Code arrives from GitHub into these clones; nothing about this network travels back out that '
                    'way.',
                    'A fetch is only as recent as the last time a human or an agent ran one. A snapshot taken one '
                    'second ago tells you nothing new about a remote last read four days ago — so ahead/behind '
                    'is printed beside the age of the fetch it was measured against.'))
    body.append('<div class="scroll"><table><thead><tr><th>Project</th><th>Seat</th><th>Remote</th>'
                '<th>Last fetch (own age)</th><th>Ahead/behind — as of that fetch</th>'
                '<th>External commits in clone</th></tr></thead><tbody>')
    ext = fed.get("external_contributors") or []
    for r in M["repos"]:
        fa = next((f for f in M["fetches"] if f.get("seat") == r.get("seat")), None)
        rem = (r.get("remotes") or [{}])[0].get("fetch") or "—"
        extc = []
        for c in ext:
            for pr in (c.get("repos") or []):
                if pr.get("project") == r.get("project"):
                    extc.append(f'{c.get("name")} {pr.get("commits")}')
        fetch_cell = (age_html(fa["epoch"]) if fa and fa.get("epoch")
                      else hole("never fetched", (fa or {}).get("reason") or "no FETCH_HEAD"))
        stale_flag = ""
        if fa and fa.get("epoch") and (M["now"] - fa["epoch"]) > STALE_FETCH_SECONDS:
            stale_flag = ' <span class="badge" style="border-color:var(--amber);color:var(--amber)">stale</span>'
        ab = (f'{vol(e(num(r.get("ahead"))))}/{vol(e(num(r.get("behind"))))}'
              if r.get("upstream") else hole("undefined", "no upstream"))
        body.append(f'<tr><td>{e(r.get("project"))}</td><td>{e(r.get("seat"))}</td>'
                    f'<td style="word-break:break-all">{e(rem)}</td>'
                    f'<td>{fetch_cell}{stale_flag}</td><td>{ab}</td>'
                    f'<td>{e(", ".join(extc) or "—")}</td></tr>')
    body.append("</tbody></table></div>")

    body.append('<div class="conn" style="margin-top:16px"><span class="lbl">agentmail federation · not connected'
                '</span><span class="arrow-gap"></span></div>')
    body.append('<dl class="kv mini" style="margin-top:6px">')
    body.append(f'<dt>doc</dt><dd>{e((fed.get("federation_doc") or {}).get("path") or "—")} — transport: '
                f'{e((fed.get("federation_doc") or {}).get("transport") or "—")}</dd>')
    body.append(f'<dt>mail repo</dt><dd>{e(mr.get("path") or "—")} · branch {e(mr.get("branch") or "—")}</dd>')
    body.append('<dt>remotes</dt><dd>' + (
        e(", ".join(x.get("name", "?") for x in (mr.get("remotes") or [])))
        if mr.get("remotes") else '<span class="t-bad">none configured — the line terminates in open air</span>')
        + "</dd>")
    body.append(f'<dt>uncommitted</dt><dd>{vol(e(num(mr.get("uncommitted_files"))) + " file(s)")} · last commit '
                f'{age_html(epoch_of((mr.get("head") or {}).get("committed_at")))}</dd>')
    body.append(f'<dt>sync daemon</dt><dd>{vol("running" if fed.get("sync_daemon_running") else "not running")}</dd>')
    body.append("</dl>")

    # external contributors
    body.append('<h4 style="margin:16px 0 6px;font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;'
                'color:var(--ink-2)">Humans in these repos with no seat in this network</h4>')
    body.append(f'<p class="note">Distinct git authors in the last '
                f'{e(fed.get("contributor_window_days","?"))} days with no seat in this network.</p>')
    body.append(why("why this list exists",
                    'These people commit into the same repositories the agents work in, and no agent here can see '
                    'them: they have no seat, no maildir, and nothing this network records. That blindness has '
                    'already caused one overwrite.',
                    'Identity matching is by raw git author string, so one person using two emails appears twice, '
                    'and the list is only as complete as the last fetch of each clone.'))
    if ext:
        body.append('<div class="scroll"><table><thead><tr><th>Identity</th><th>Commits (fogged)</th>'
                    '<th>Repos</th><th>Last commit</th><th>In this network</th></tr></thead><tbody>')
        for c in ext:
            repos_txt = ", ".join(f'{p.get("project")}:{p.get("commits")}' for p in (c.get("repos") or []))
            body.append(f'<tr><td>{e(c.get("identity"))}</td>'
                        f'<td class="fogged-val">{e(c.get("commits"))} <span class="vis fogged">as of last '
                        f'fetch</span></td>'
                        f'<td class="fogged-val">{e(repos_txt)}</td>'
                        f'<td>{age_html(epoch_of(c.get("last_commit_at")))}</td>'
                        f'<td><span class="vis shrouded">shrouded</span> no seat, no maildir — this person has '
                        f'never been observed inside this network at all</td></tr>')
        body.append("</tbody></table></div>")
    else:
        body.append('<p class="empty">No external author in the window.</p>')
    body.append("</div>")
    sub = (f'{len(fed.get("sites") or [])} site(s) known · {len(remotes)} remote · '
           f'{len(ext)} seatless contributor(s)')
    return panel(7, "Federation", sub, "".join(body))

def render_history(M) -> str:
    body = ['<div class="pad">']
    body.append('<p class="note">Durable facts only: a commit that happened stays happened, so nothing in this '
                'panel decays. Ages tick from each item\'s own timestamp.</p>')
    body.append('<div class="scroll"><table><thead><tr><th>When</th><th>Project</th><th>SHA</th><th>Author</th>'
                '<th>Subject</th></tr></thead><tbody>')
    rows = []
    for r in M["repos"]:
        for c in (r.get("last_commits") or []):
            rows.append((c.get("committed_at_epoch") or epoch_of(c.get("committed_at")) or 0, r, c))
    rows.sort(key=lambda x: -(x[0] or 0))
    for ep, r, c in rows[:30]:
        rows_ext = ""
        body.append(f'<tr><td>{age_html(ep)}</td><td>{e(r.get("project"))}</td>'
                    f'<td>{e(c.get("sha"))}</td><td>{e(c.get("author"))}</td>'
                    f'<td class="subject">{e(c.get("subject"))}</td></tr>{rows_ext}')
    body.append("</tbody></table></div>")
    settled = [i for i in (M["board"].get("items") or [])
               if (i.get("section") or "").upper().startswith("SETTLED")]
    facts = [i for i in (M["board"].get("items") or [])
             if (i.get("section") or "").upper().startswith("KEY FACTS")]
    for name, items in (("Settled (from the board, verbatim)", settled),
                        ("Key facts not to re-litigate (from the board, verbatim)", facts)):
        if items:
            body.append(f'<h4 style="margin:16px 0 6px;font-size:10.5px;letter-spacing:.14em;'
                        f'text-transform:uppercase;color:var(--ink-2)">{e(name)}</h4>')
            body.append('<ul class="tight mini">' + "".join(
                f'<li><span class="verbatim">{e(i.get("raw"))}</span></li>' for i in items) + "</ul>")
    body.append("</div>")
    return panel(8, "History", "commits + settled board items · all durable", "".join(body))

PROVENANCE_ROWS = [
    ("seat roster, roles, models, homes", ".agent-mail/roster.json (verbatim)", "durable",
     "roster is INTENT. A seat can be launched with a different model or in a different directory; "
     "the page prints both when they differ."),
    ("SESSION slot — process attributed to a seat", "ps -axo pid,ppid,etime,command + lsof -d cwd, "
     "matched by watcher-ancestry, then cwd, then bridge", "volatile",
     "a process is not a thinking model. A wedged session looks identical to a working one. Two agents sharing "
     "one home directory can only be told apart by which watcher named them."),
    ("session model / permissions", "argv of the pid", "volatile",
     "reflects launch time only — nothing here follows a /model change made inside the session."),
    ("MAILBOX slot — unread, oldest unread", "count of *.md in <seat>/new/ and <seat>/cur/", "monotone",
     "unread is a filename, not a state of mind: mail moves to cur/ by rename, which proves acknowledgement, "
     "never action. Archived or deleted mail is gone from every count."),
    ("watcher present", "ps for mail-watch/mail-bridge naming the seat", "volatile",
     "a watcher process can be alive and its session dead, and vice versa. Both are shown separately."),
    ("WORK slot / activity", "snapshot's state machine: uncommitted files OR HEAD younger than 600s; "
     "for repo-less seats, mail sent or bridge.log touched within 600s", "volatile",
     "uncommitted files prove work EXISTS, not that it is happening now — an idle session in a dirty tree reads "
     "BUSY. Repo-less seats use a substituted signal (confidence: medium)."),
    ("repo branch / dirty / ahead / behind", "git status --porcelain=v1 -b in the seat's home", "volatile",
     "ahead/behind are undefined (not zero) without an upstream, and are measured against whatever the LAST "
     "FETCH left behind — see the fetch column."),
    ("commit sha / author / subject / time", "git log -5", "durable",
     "author is a git identity string, not a person; one human with two emails is two rows."),
    ("last fetch age", "stat <repo>/.git/FETCH_HEAD — read by network-dashboard at page build time, "
     "NOT by the snapshot", "volatile",
     "mtime moves on any fetch, including a fetch of one unrelated ref. A missing file means never fetched in "
     "this clone, and is printed as a hole."),
    ("messages, senders, recipients, times", "frontmatter of *.md in every seat's new/ + cur/; recipient is the "
     "maildir owner, not the to: header", "durable",
     "there are no outboxes: sent mail is only visible while a copy sits in a recipient's maildir. Mail to a "
     "non-roster seat, or already archived, is invisible."),
    ("subject lines", "the sender's own `subject:` header", "durable",
     "a claim, never verified state. This page never promotes a subject into a status."),
    ("threads and reply debt", "grouped by the `thread:` header; debt = last message in a thread plus the "
     "recipient's maildir", "durable",
     "INFERRED. A reply that travelled out of band, on another thread, or was archived, reads here as an "
     "outstanding debt that does not exist."),
    ("pair matrix counts", "mail_flow window only (default 48h)", "durable",
     "cells outside the window are not zero — they are unmeasured. The human's row and column are structurally "
     "empty: his instructions are prompts, and leave no file."),
    ("items waiting on the human", "overseer-tasks.md, parsed as markdown", "durable",
     "hand-maintained prose with no schema and NO per-item timestamps, so this page cannot sort them by age. "
     "An item binds to a seat only when its first field is exactly a seat id."),
    ("federation sites / mail remote", "roster.json + git remote -v in .agent-mail", "volatile",
     "a documented transport is not a configured one. With no remote, no mail from another site can ever have "
     "arrived — so no other site's seats are drawn."),
    ("external contributors", "git log --since=30.days across all repo clones", "durable",
     "only as complete as the last fetch of each clone; identity matching is by raw author string."),
    ("LIVENESS axis (colour)", "session.live from the snapshot + the seat's last observed output", "volatile",
     "'never-started' and 'stopped-or-lost' are different states with different evidence, and 'stopped' vs "
     "'lost' CANNOT be separated here: nothing on this filesystem records an exit. They are printed together, "
     "timestamped, rather than guessed apart."),
    ("OCCUPANCY axis (shape)", "cadence verdict + the CPU delta + the seat's own last message type", "volatile",
     "'interrupted' is self-reported by the seat and never verified. 'spinning' needs a live pid — for a seat "
     "with no process it cannot be evaluated at all."),
    ("cadence verdict (stalled / on-cadence)", "the seat's own last %d events (mail sent, commits, bridge.log "
     "writes); stalled iff silence exceeds the LONGEST gap those events show" % CADENCE_EVENTS, "volatile",
     "needs at least %d events or no verdict is issued. Mail evidence is limited to the snapshot's window, so a "
     "seat quiet for longer than the window looks event-poor. Replaces the fixed 600s window, which is shown "
     "beside it as a second opinion." % CADENCE_MIN_EVENTS),
    ("CPU now (spinning)", "two `ps -o time=` samples %.1fs apart, taken by network-dashboard" % CPU_SAMPLE_GAP,
     "volatile",
     "a %.1fs sample can miss a burst and can catch an unrelated spike; cumulative CPU is shown beside it and "
     "proves nothing about now. If ps fails the field is a hole, never a zero." % CPU_SAMPLE_GAP),
    ("mailbox depth sparkline + growth alarm",
     "filenames in <seat>/new/ (SPEC §4 timestamps), listed by network-dashboard", "monotone",
     "a LOWER BOUND on past depth: mail that arrived and was read left no trace, so a drained backlog looks "
     "like it never existed. The alarm is on the derivative, which survives that bias; the absolute number "
     "does not."),
    ("read-but-not-replied debt", "a message in cur/ with no later message from that recipient on that thread",
     "durable",
     "window-limited to the snapshot's mail window for per-message rows. Blind to replies sent out of band, on "
     "another thread, or since archived. The cur/ rename is the protocol's ack, so it can never distinguish "
     "'handled' from 'opened and forgotten'."),
    ("wait-for graph and cycles", "the debt ledger, as directed edges", "durable",
     "only as good as the debt inference beneath it: a false debt can manufacture a false deadlock, and an "
     "out-of-band reply can hide a real one."),
    ("dead letters", "listing of <seat>/tmp/ (names and mtimes only) + to_header_mismatches", "volatile",
     "SPEC §2 tells readers to ignore tmp/; files younger than %ds are skipped because they may be mid-write. "
     "A stranded file is counted, never opened." % TMP_STRANDED_SECONDS),
    ("window deltas (commits / sent / received)", "mail_flow window + last_commits inside that window",
     "durable",
     "the snapshot keeps only 5 commits per repo, so a busy repo's commit delta saturates at 5 and is labelled "
     "capped. Deltas are the work signal; the lifetime totals beside them are not."),
    ("bridges and watchers", "ps for processes that actually EXECUTE the helper scripts", "volatile",
     "a pgrep/echo mentioning a helper is not a helper; duplicates are counted and flagged."),
    ("snapshot warnings / failed checks", "meta.warnings[] from the snapshot", "durable",
     "a snapshot that could not answer says so here rather than crashing — an empty list is not proof of health."),
]

def render_provenance(M) -> str:
    body = ['<div class="pad">']
    body.append('<p class="note">Every field on this page, the exact command that produced it, how fast it rots, '
                'and how it lies. <b>durable</b> = a fact about a moment, never decays. <b>monotone</b> = can only '
                'grow while this page sits open, so it is shown as a lower bound. <b>volatile</b> = full strength '
                f'for {dur(FRESH_SECONDS, short=True)}, dimmed to {dur(AGING_SECONDS, short=True)}, then forced to '
                'the unknown glyph.</p>')
    body.append('<div class="scroll"><table><thead><tr><th>Field</th><th>Source</th><th>Freshness</th>'
                '<th>Known failure mode</th></tr></thead><tbody>')
    for f_, src, cls, fail in PROVENANCE_ROWS:
        body.append(f'<tr><td><b>{e(f_)}</b></td><td>{e(src)}</td>'
                    f'<td><span class="fc {cls}">{cls}</span></td>'
                    f'<td class="prose">{e(fail)}</td></tr>')
    body.append("</tbody></table></div>")
    meta = M["meta"]
    src = M["doc"].get("_source") or {}
    body.append('<h4 style="margin:16px 0 6px;font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;'
                'color:var(--ink-2)">This document</h4><dl class="kv mini">')
    body.append(f'<dt>snapshot tool</dt><dd>{e(meta.get("tool","?"))} v{e(meta.get("tool_version","?"))}</dd>')
    body.append(f'<dt>dashboard tool</dt><dd>network-dashboard v{__version__}</dd>')
    body.append(f'<dt>acquired</dt><dd>{e(src.get("cmd") or src.get("path") or "?")} '
                f'({e(src.get("mode","?"))})</dd>')
    body.append(f'<dt>written</dt><dd>{e(M["out_path"])}</dd>')
    body.append(f'<dt>roster</dt><dd>{e(meta.get("roster_path","?"))} v{e(meta.get("roster_version","?"))}</dd>')
    body.append(f'<dt>mail window</dt><dd>{e(meta.get("mail_window_hours","?"))}h · cap '
                f'{e(meta.get("mail_cap","?"))} · truncated: {e(meta.get("mail_flow_truncated"))}</dd>')
    body.append('<dt>warnings</dt><dd>' + (
        "<br>".join(e(w) for w in (meta.get("warnings") or [])) or "none reported") + "</dd>")
    rules = (meta.get("activity_rules") or {})
    if rules:
        body.append('<dt>busy window</dt><dd>' + e(rules.get("busy_window_seconds", "?")) + "s</dd>")
        for k, v in (rules.get("states") or {}).items():
            body.append(f'<dt>{e(k)}</dt><dd class="prose">{e(v)}</dd>')
        for i, v in enumerate(rules.get("documented_deviations") or []):
            body.append(f'<dt>{"deviation" if i == 0 else ""}</dt><dd class="prose">{e(v)}</dd>')
        for i, v in enumerate(rules.get("known_limits") or []):
            body.append(f'<dt>{"known limit" if i == 0 else ""}</dt><dd class="prose">{e(v)}</dd>')
    body.append("</dl>")
    body.append('<h4 style="margin:16px 0 6px;font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;'
                'color:var(--ink-2)">What this page cannot show, at all</h4>')
    body.append('<ul class="tight mini"><li>Whether a live process is thinking, stuck, or waiting on a '
                f'permission prompt.</li><li>What {e(M["ident"]["human"])} said: prompts are not mail and leave no file.</li>'
                '<li>Any other site\'s seats — nothing here can observe them.</li>'
                '<li>Mail that was archived or deleted, or sent to an address outside the roster.</li>'
                '<li>Whether a task was done well, or done at all — only that someone claimed it.</li>'
                '<li>Per-item age on the board: the file records none.</li></ul>')
    body.append('<h4 style="margin:16px 0 6px;font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;'
                'color:var(--ink-2)">This page has no control plane</h4>')
    body.append('<p class="note">The controls on this page are <b>view state only</b> — theme, panel order, '
                'what is open, column sorting, and the pair-matrix filter. They are remembered in this browser '
                'and they change what you see; not one of them touches a seat, a maildir, a repository or a '
                'process. There is deliberately no button here that sends mail, kills a session or edits the '
                'board, because a page that reports on a system should not also be able to disturb it. '
                'Every action is a command you run yourself:</p><ul class="tight mini">'
                f'<li>{cmd(helper("mail-read") + " <seat>")} read a seat\'s mail</li>'
                f'<li>{cmd(helper("mail-watch") + " <seat>")} arm a watcher (fixes a DEAF-by-no-watcher seat)</li>'
                f'<li>{cmd(helper("mail-send") + " <from> <to> --subject ... --type task")} dispatch work</li>'
                f'<li>{cmd(helper("network-snapshot") + " --pretty | less")} inspect the raw evidence</li>'
                '</ul>')
    body.append("</div>")
    return panel(9, "Provenance", "field → source → freshness → failure mode", "".join(body))
