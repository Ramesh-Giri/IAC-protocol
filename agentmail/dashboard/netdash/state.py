# -*- coding: utf-8 -*-
"""The state machines. No HTML in this file.

Three independent slots (session / mailbox / work), two independent axes
(liveness x occupancy), one self-calibrating cadence rule, and one composite
word that is only ever printed next to the slots that produced it. Each
function returns a dict carrying its own `detail` string: the derivation
travels with the verdict so no renderer has to reconstruct it."""

from __future__ import annotations

from .thresholds import (CADENCE_EVENTS, CPU_SAMPLE_GAP, CADENCE_LOOKBACK_DAYS, CADENCE_MIN_EVENTS, CPU_SPIN_PERCENT,
                         DEAF_UNREAD_SECONDS, DEPTH_BUCKETS, DEPTH_BUCKET_HOURS, LAG_UNREAD_SECONDS,
                         MUTE_SILENCE_SECONDS, RECENT_WORK_SECONDS)
from .util import dur, epoch_of

def depth_series(new_epochs: list[int], now: int) -> dict:
    """Backlog depth over the last DEPTH_BUCKETS hours, reconstructed from the
    arrival times of mail that is STILL unread.

    This is a LOWER BOUND on past depth: anything that arrived and was read is
    invisible to it. It is exact about one thing — how the current backlog
    accumulated — and that is the thing the derivative alarm needs.
    """
    span = DEPTH_BUCKET_HOURS * 3600
    start = now - DEPTH_BUCKETS * span
    buckets = []
    for i in range(DEPTH_BUCKETS):
        edge = start + (i + 1) * span
        buckets.append(sum(1 for x in new_epochs if x <= edge))
    older = sum(1 for x in new_epochs if x <= start)
    grew = buckets[-1] - buckets[max(0, len(buckets) - 3)] if buckets else 0
    return {"buckets": buckets, "older_than_window": older, "max": max(buckets or [0]),
            "grew_last_3h": grew, "growing": grew > 0, "window_hours": DEPTH_BUCKETS}

def cadence(events: list[int], now: int) -> dict:
    """Burrow's rule, adapted: a seat's own recent rhythm sets its own deadline.

    The deadline is the LONGEST gap between consecutive events in the seat's
    own recent history — the longest silence it has recently shown to be
    normal. Silence beyond that is stalled BY ITS OWN STANDARD: a seat that
    answers every three minutes is stalled after ten, one that answers every
    six hours is not, and neither number was invented here.

    (Total span was tried first and is wrong: a seat that broadcasts six
    messages in forty seconds gets a forty-second span and reads as stalled a
    minute later. The longest observed gap is burst-proof, and errs toward
    saying nothing rather than crying wolf.)

    With fewer than CADENCE_MIN_EVENTS events no verdict is issued at all — an
    unjustifiable threshold is worse than an admitted hole.
    """
    all_ev = sorted(x for x in events if x)
    cutoff = now - CADENCE_LOOKBACK_DAYS * 86400
    ev = [x for x in all_ev if x >= cutoff]
    out = {"n": len(ev), "n_all": len(all_ev), "last": all_ev[-1] if all_ev else None,
           "span": None, "silence": None, "verdict": "no-cadence", "ratio": None,
           "typical": None, "deadline": None}
    if not all_ev:
        out["why"] = "no observable output at all in the evidence available"
        return out
    out["silence"] = max(0, now - all_ev[-1])  # mail can arrive mid-scan; never print a negative age
    if len(ev) < CADENCE_MIN_EVENTS:
        out["why"] = (f"only {len(ev)} event(s) in the last {CADENCE_LOOKBACK_DAYS} days — fewer than "
                      f"{CADENCE_MIN_EVENTS}, so this seat has no established recent rhythm and no deadline can "
                      "be justified from it. Older activity is not used: a cadence from two months ago is not "
                      "this seat's cadence.")
        return out
    recent = ev[-CADENCE_EVENTS:]
    gaps = [b - a for a, b in zip(recent, recent[1:]) if b > a]
    out["span"] = recent[-1] - recent[0]
    out["typical"] = sorted(gaps)[len(gaps) // 2] if gaps else None
    if not gaps:
        out["why"] = "its recent events share one timestamp (a broadcast) — no rhythm to measure against"
        return out
    deadline = max(gaps)
    span = out["span"]
    out["deadline"] = deadline
    out["ratio"] = out["silence"] / deadline if deadline else None
    if out["silence"] > span:
        # We have watched this seat for less time than it has now been quiet.
        # A burst of six messages eight seconds apart is one episode of
        # activity, not a rhythm, and nine minutes of silence after it supports
        # no verdict at all. Refusing to answer is the honest answer; the
        # alternative is a deadline derived from forty seconds of evidence.
        out["verdict"] = "no-cadence"
        out["why"] = (f"its last {len(recent)} events span only {dur(span, short=True)}, which is less than the "
                      f"{dur(out['silence'], short=True)} it has now been silent — too little observation to "
                      "call this seat late or on time")
        return out
    out["verdict"] = "stalled" if out["silence"] > deadline else "on-cadence"
    out["why"] = (f"over its last {len(recent)} events the longest normal gap was {dur(deadline, short=True)} "
                  f"(median {dur(out['typical'], short=True)}); it has now been silent "
                  f"{dur(out['silence'], short=True)}")
    return out


# ---------------------------------------------------------------------------
# derivation: the three slots
# ---------------------------------------------------------------------------

def slot_session(seat: dict) -> dict:
    ses = seat.get("session") or {}
    if not seat.get("home_exists", True) or seat.get("activity") == "UNREACHABLE" or "live" not in ses:
        return {"state": "dash", "word": "not checked",
                "detail": "liveness undecidable — home missing or the process table could not be read",
                "tone": "unknown"}
    if not ses.get("live"):
        return {"state": "hollow", "word": "no process",
                "detail": "no process could be attributed to this seat", "tone": "bad"}
    cands = [c for c in (ses.get("candidates") or []) if not c.get("claimed_by_other_seat")]
    ambiguous = len(cands) > 1 or ses.get("kind") == "forked-background"
    bits = []
    if ses.get("pid"):
        bits.append(f"pid {ses['pid']}")
    if ses.get("elapsed_human"):
        bits.append(f"up {ses['elapsed_human']}")
    if ses.get("detection"):
        bits.append(ses["detection"])
    if ses.get("kind"):
        bits.append(ses["kind"])
    detail = " · ".join(bits)
    if ambiguous:
        detail += f" · {len(cands)} candidate processes share this seat's evidence"
        return {"state": "half", "word": "ambiguous", "detail": detail, "tone": "warn"}
    return {"state": "filled", "word": "running", "detail": detail, "tone": "good"}

def slot_mailbox(seat: dict) -> dict:
    if not seat.get("maildir_present"):
        return {"state": "dash", "word": "no maildir", "n": None,
                "detail": "this seat has no maildir — nothing can be delivered to it", "tone": "unknown"}
    unread = seat.get("inbox_unread") or 0
    processed = seat.get("inbox_processed") or 0
    age = seat.get("unread_age_seconds")
    deaf = []
    if age is not None and age > DEAF_UNREAD_SECONDS:
        deaf.append(f"oldest unread is {dur(age, short=True)} old (>4h)")
    if not seat.get("watcher_running"):
        deaf.append("no mail-watch/mail-bridge process for this seat")
    if unread > 0 and processed == 0:
        deaf.append("cur/ is empty while new/ is not — nothing has ever been processed")
    if deaf:
        return {"state": "deaf", "word": "DEAF", "n": unread, "detail": "; ".join(deaf), "tone": "bad"}
    if age is not None and age > LAG_UNREAD_SECONDS:
        return {"state": "lagging", "word": "lagging", "n": unread,
                "detail": f"oldest unread {dur(age, short=True)} old (>30m)", "tone": "warn"}
    if unread > 0:
        return {"state": "working", "word": "working through", "n": unread,
                "detail": f"{unread} in new/, oldest {dur(age, short=True)}", "tone": "warn"}
    return {"state": "clear", "word": "clear", "n": 0,
            "detail": ("new/ is empty and a watcher is running. Marking mail read is a file "
                       "rename — it proves delivery was acknowledged, not that anything was done."),
            "tone": "good"}

def slot_work(seat: dict, repo: dict | None, now: int) -> dict:
    if seat.get("activity") == "UNREACHABLE":
        return {"state": "dash", "word": "unknown",
                "detail": "evidence could not be gathered", "tone": "unknown"}
    ev = [str(x) for x in (seat.get("activity_evidence") or [])]
    conf = seat.get("activity_confidence") or "unknown"
    if seat.get("activity") == "LIVE_BUSY":
        return {"state": "producing", "word": "producing", "detail": "; ".join(ev) or "busy signal fired",
                "tone": "good", "conf": conf}
    head_age = (repo or {}).get("head_age_seconds")
    sent_epoch = epoch_of(seat.get("last_sent_at"))
    sent_age = (now - sent_epoch) if sent_epoch else None
    recent = []
    if head_age is not None and head_age < RECENT_WORK_SECONDS:
        recent.append(f"HEAD committed {dur(head_age, short=True)} ago")
    if sent_age is not None and sent_age < RECENT_WORK_SECONDS:
        recent.append(f"sent mail {dur(sent_age, short=True)} ago")
    if recent:
        return {"state": "recent", "word": "produced recently", "detail": "; ".join(recent),
                "tone": "warn", "conf": conf}
    if repo or seat.get("maildir_present"):
        d = "; ".join(ev) or "no recent-work signal fired"
        if sent_age is not None:
            d += f"; last outbound mail {dur(sent_age, short=True)} ago"
        return {"state": "quiet", "word": "quiet", "detail": d, "tone": "warn", "conf": conf}
    return {"state": "dash", "word": "unknown",
            "detail": "no repo and no maildir — this seat has no observable output channel",
            "tone": "unknown", "conf": conf}


# ---------------------------------------------------------------------------
# derivation: the two axes — liveness (colour) x occupancy (shape)
# ---------------------------------------------------------------------------

LIVENESS_DOC = {
    "live": "a process is attributed to this seat right now",
    "never-started": "no process, and no trace that this seat has EVER produced anything — "
                     "this is not 'down', it is 'never connected'",
    "stopped-or-lost": "no process, but it was producing until T. This filesystem keeps no exit record, "
                       "so a graceful stop and a crash leave identical evidence and are NOT guessed apart",
    "unreachable": "liveness is undecidable — home missing, or the process table could not be read. "
                   "Losing sight of a seat makes it UNKNOWN, never DOWN",
}

OCCUPANCY_DOC = {
    "working": "producing within its own cadence",
    "waiting-for-mail": "listening, nothing to do — the resting state, not a fault",
    "interrupted": "blocked on a human and resumable — a named state, not a terminal one (A2A). "
                   "Self-reported by the seat's own last message",
    "spinning": "burning CPU right now with nothing written since — the agent-specific failure "
                "no process table calls out",
    "unknown": "not enough evidence to place it",
}

LIVENESS_TONE = {"live": "good", "never-started": "unknown", "stopped-or-lost": "bad", "unreachable": "unknown"}

def derive_liveness(seat: dict, events: list[int]) -> dict:
    ses = seat.get("session") or {}
    if not seat.get("home_exists", True) or seat.get("activity") == "UNREACHABLE" or "live" not in ses:
        return {"state": "unreachable", "at": None,
                "detail": "home missing or the process table could not be read"}
    if ses.get("live"):
        return {"state": "live", "at": epoch_of(ses.get("started_at")),
                "detail": (f"{ses.get('detection') or 'attributed'}"
                           + (f" · pid {ses['pid']}" if ses.get("pid") else "")
                           + (f" · up {ses['elapsed_human']}" if ses.get("elapsed_human") else ""))}
    last = max(events) if events else None
    if last is None and not (seat.get("inbox_processed") or 0) and not (seat.get("mail_sent_total") or 0):
        return {"state": "never-started", "at": None,
                "detail": "no process, and no message or commit has ever been attributed to this seat"}
    return {"state": "stopped-or-lost", "at": last,
            "detail": ("no process. Last observed output at the time shown; no exit record exists anywhere on "
                       "this filesystem, so stopped-cleanly and crashed cannot be told apart")}

def derive_occupancy(seat: dict, cad: dict, cpu: dict | None, blocked: bool, sl_m: dict, live: bool,
                     delta: dict | None = None) -> dict:
    if blocked:
        return {"state": "interrupted", "detail": "its own last outbound message was type:blocked and nothing has "
                                                  "arrived for it since — self-reported, resumable"}
    burning = bool(cpu and cpu.get("pct", 0) >= CPU_SPIN_PERCENT)
    stalled = cad.get("verdict") == "stalled"
    if live and burning and (stalled or (cad.get("silence") or 0) > 1800):
        return {"state": "spinning",
                "detail": (f"{cpu['pct']:.0f}% CPU over a {cpu.get('gap', CPU_SAMPLE_GAP):.1f}s sample taken now, "
                           f"but nothing written or sent for {dur(cad.get('silence'), short=True)}"
                           + (f" (its own longest normal gap is {dur(cad.get('deadline'), short=True)})" if cad.get("deadline") else ""))}
    if not live:
        return {"state": "unknown", "detail": "no process — occupancy cannot be observed, only the debt it left"}
    produced = ((delta or {}).get("sent") or 0) + ((delta or {}).get("commits") or 0)
    if cad.get("verdict") == "on-cadence":
        if produced:
            return {"state": "working", "detail": cad.get("why", "") + f"; {produced} output event(s) inside "
                                                                       "the mail window"}
        # on-cadence only means "not overdue by its own standard" — it is not
        # evidence of output. Without a window delta, nothing was produced.
        return {"state": "waiting-for-mail",
                "detail": "not overdue by its own standard, but nothing was produced inside the window either: "
                          + cad.get("why", "")}
    if cad.get("verdict") == "stalled":
        if sl_m.get("state") in ("clear",):
            return {"state": "waiting-for-mail",
                    "detail": "silent past its own rhythm, mailbox clear — idle by its own standard: "
                              + cad.get("why", "")}
        return {"state": "unknown",
                "detail": "silent past its own rhythm with mail outstanding: " + cad.get("why", "")}
    # no cadence could be established: say what the window shows and nothing more
    if produced:
        return {"state": "working",
                "detail": f"{produced} output event(s) inside the mail window. No deadline is claimed: "
                          + cad.get("why", "")}
    if sl_m.get("state") == "clear":
        return {"state": "waiting-for-mail",
                "detail": "mailbox clear and nothing produced inside the window. " + cad.get("why", "")}
    return {"state": "unknown", "detail": cad.get("why", "no cadence established")}

COMPOSITE_DOC = {
    "Working": "session running · mailbox not deaf · work slot producing",
    "Idle-listening": "session running · mailbox current · no work signal, but it spoke or committed recently",
    "Mute": f"session running · mailbox current · nothing produced and nothing said for >{dur(MUTE_SILENCE_SECONDS, short=True)}",
    "Deaf": "mailbox failed the listening test (oldest unread >4h, or no watcher, or cur/ empty while new/ is not)",
    "Dark": "no process could be attributed to this seat",
    "Blocked-on-human": "the seat's own last outbound message was type:blocked and nothing has arrived for it since — SELF-REPORTED, not verified",
    "Unknown": "at least one slot could not be evaluated",
}

def composite(sl_s, sl_m, sl_w, blocked: bool, silence_seconds) -> tuple[str, str]:
    if sl_s["state"] == "dash" or (sl_w["state"] == "dash" and sl_m["state"] == "dash"):
        return "Unknown", "unknown"
    if sl_s["state"] == "hollow":
        return "Dark", "bad"
    if sl_m["state"] == "deaf":
        return "Deaf", "bad"
    if blocked:
        return "Blocked-on-human", "warn"
    if sl_w["state"] == "producing":
        return "Working", "good"
    if sl_w["state"] == "quiet" and (silence_seconds is None or silence_seconds > MUTE_SILENCE_SECONDS):
        return "Mute", "warn"
    return "Idle-listening", "good"


# ---------------------------------------------------------------------------
# glyphs — shape first, colour is only a redundant fourth channel
# ---------------------------------------------------------------------------
