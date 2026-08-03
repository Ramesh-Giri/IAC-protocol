# -*- coding: utf-8 -*-
"""One pass over the snapshot that produces every derived structure the page
renders: per-seat state, triage buckets, disagreements, alerts, the two-kind
reply-debt ledger, the wait-for graph and its cycles, and dead letters.

Renderers never derive anything themselves -- they only lay out what this
module already decided, which is what keeps the same verdict from being
computed two different ways in two different panels."""

from __future__ import annotations

import time

from .identity import site_identity
from .paths import helper
from .probes import cpu_probe, fetch_age, file_mtime, maildir_scan
from .state import (cadence, composite, depth_series, derive_liveness, derive_occupancy,
                    slot_mailbox, slot_session, slot_work)
from .thresholds import *  # noqa: F401,F403
from .util import GEN_ERRORS, dur, e, epoch_of

def build_model(doc: dict, out_path: str, args) -> dict:
    meta = doc.get("meta") or {}
    now = int(time.time())
    snap_epoch = meta.get("generated_at_epoch") or epoch_of(meta.get("generated_at")) or now
    seats = doc.get("seats") or []
    repos = doc.get("repos") or []
    repo_by_seat = {r.get("seat"): r for r in repos if r.get("seat")}
    flow = doc.get("mail_flow") or []
    threads = doc.get("threads") or []
    bridges = doc.get("bridges") or []
    board = doc.get("board") or {}
    fed = doc.get("federation") or {}

    seat_ids = [s.get("id") for s in seats]
    ident = site_identity(fed, meta, seats)

    def short_seat(sid: str) -> str:
        """Drop this site's own suffix for cramped labels — nothing else."""
        if ident["suffix"] and sid and sid.endswith(ident["suffix"]):
            return sid[: -len(ident["suffix"])]
        return sid or ""

    # last outbound message per seat, and self-reported blocked state
    last_out: dict[str, list] = {sid: [] for sid in seat_ids}
    last_in: dict[str, list] = {sid: [] for sid in seat_ids}
    for m in flow:
        if m.get("from") in last_out:
            last_out[m["from"]].append(m)
        if m.get("to") in last_in:
            last_in[m["to"]].append(m)

    # one CPU probe for every attributed pid: cumulative CPU cannot tell a
    # wedged process from a looping one; a delta can.
    pids = [((s.get("session") or {}).get("pid")) for s in seats]
    bridge_by_target = {b.get("target"): b for b in bridges}
    cpu = cpu_probe([p for p in pids if p])

    mail_root = meta.get("mail_root") or ""   # used to tell our helpers from another network's
    window_start = snap_epoch - int(meta.get("mail_window_hours") or 48) * 3600

    model_seats = []
    for idx, s in enumerate(seats, start=1):
        sid = s.get("id")
        repo = repo_by_seat.get(sid)
        sl_s = slot_session(s)
        sl_m = slot_mailbox(s)
        sl_w = slot_work(s, repo, snap_epoch)
        outs = sorted(last_out.get(sid, []), key=lambda m: m.get("timestamp") or "")
        ins = sorted(last_in.get(sid, []), key=lambda m: m.get("timestamp") or "")
        blocked = False
        blocked_msg = None
        if outs and (outs[-1].get("type") == "blocked"):
            b_epoch = epoch_of(outs[-1].get("timestamp"))
            later_in = [m for m in ins if (epoch_of(m.get("timestamp")) or 0) > (b_epoch or 0)]
            if not later_in:
                blocked = True
                blocked_msg = outs[-1]
        sent_epoch = epoch_of(s.get("last_sent_at"))
        silence = (snap_epoch - sent_epoch) if sent_epoch else None
        comp, tone = composite(sl_s, sl_m, sl_w, blocked, silence)

        # ---- events that define this seat's OWN cadence --------------------
        events, event_kinds = [], []
        for m in outs:
            ep = epoch_of(m.get("timestamp"))
            if ep:
                events.append(ep)
                event_kinds.append("mail sent")
        for c in ((repo or {}).get("last_commits") or []):
            ep = c.get("committed_at_epoch") or epoch_of(c.get("committed_at"))
            if ep:
                events.append(ep)
                event_kinds.append("commit")
        br = bridge_by_target.get(sid) or {}
        if (br.get("log") or {}).get("modified_at"):
            ep = epoch_of(br["log"]["modified_at"])
            if ep:
                events.append(ep)
                event_kinds.append("bridge.log write")
        cad = cadence(events, snap_epoch)
        cad["kinds"] = sorted(set(event_kinds))

        # ---- window deltas, not cumulative counters ------------------------
        commits_win = [c for c in ((repo or {}).get("last_commits") or [])
                       if (c.get("committed_at_epoch") or epoch_of(c.get("committed_at")) or 0) >= window_start]
        delta = {
            "sent": len(outs), "recv": len(ins), "commits": len(commits_win),
            "commits_capped": len(commits_win) >= len((repo or {}).get("last_commits") or []) and bool(commits_win),
        }

        # ---- mailbox depth from the filenames in new/ ----------------------
        scan = maildir_scan(mail_root, sid) if mail_root else {"read": False, "new_epochs": [], "tmp_stranded": []}
        depth = depth_series(scan.get("new_epochs") or [], snap_epoch) if scan.get("read") else None

        # A growing queue is only "falling behind" when the seat is also
        # holding mail longer than its own rhythm says it normally would.
        # +1 arrival that it will answer in a minute is traffic, not a fault.
        unread_age = s.get("unread_age_seconds")
        deadline = cad.get("deadline")
        if depth and depth.get("growing") and deadline and unread_age is not None:
            depth["falling_behind"] = unread_age > deadline
            depth["behind_why"] = (f"queue grew by {depth['grew_last_3h']} in 3h and its oldest unread has sat "
                                   f"{dur(unread_age, short=True)}, past the {dur(deadline, short=True)} it "
                                   "normally takes to act")
        elif depth:
            depth["falling_behind"] = False
            depth["behind_why"] = ("queue grew, but no cadence is established for this seat, so there is no "
                                   "basis to call it behind" if depth.get("growing") else "")

        seat_cpu = cpu.get((s.get("session") or {}).get("pid")) if (s.get("session") or {}).get("pid") else None
        liv = derive_liveness(s, events)
        occ = derive_occupancy(s, cad, seat_cpu, blocked, sl_m, liv["state"] == "live", delta)

        model_seats.append({
            "n": idx, "seat": s, "repo": repo, "s": sl_s, "m": sl_m, "w": sl_w,
            "composite": comp, "tone": tone, "blocked": blocked, "blocked_msg": blocked_msg,
            "outs": outs[-3:][::-1], "all_outs": outs, "ins": ins, "silence": silence,
            "cad": cad, "cpu": seat_cpu, "liv": liv, "occ": occ, "delta": delta,
            "scan": scan, "depth": depth, "bridge": br,
        })
    by_id = {ms["seat"].get("id"): ms for ms in model_seats}

    # ---- triage buckets: who needs the human, in that order ----------------
    APPROVAL_WORDS = ("approv", "escalat", "layer-3", "layer 3", "permission", "authoriz", "sign-off",
                      "signoff", "rule on", "ruling", "go/no-go", "decision")
    for ms in model_seats:
        b = "idle"
        why = ""
        if ms["occ"]["state"] == "interrupted":
            subj = ((ms.get("blocked_msg") or {}).get("subject") or "").lower()
            if any(w in subj for w in APPROVAL_WORDS):
                b, why = "needs-approval", "its blocked message asks for a ruling"
            else:
                b, why = "needs-input", "it reported itself blocked on a human"
        elif ms["liv"]["state"] in ("stopped-or-lost", "unreachable") or ms["m"]["state"] == "deaf":
            b = "failed"
            why = ("mailbox is deaf — mail sent to it will not be seen"
                   if ms["m"]["state"] == "deaf" else ms["liv"]["detail"])
        elif ms["occ"]["state"] == "spinning":
            b, why = "spinning", ms["occ"]["detail"]
        elif ms["depth"] and ms["depth"].get("falling_behind"):
            b = "spinning"
            why = ms["depth"].get("behind_why") or "its queue is filling faster than it drains"
        elif ms["occ"]["state"] == "working":
            d = ms["delta"]
            b = "working"
            why = (f'{d["commits"]} commit(s) and {d["sent"]} message(s) inside the window, and it is not '
                   f'overdue by its own rhythm (longest normal gap '
                   f'{dur(ms["cad"].get("deadline"), short=True)})')
        else:
            b, why = "idle", ms["occ"].get("detail", "")
        ms["bucket"], ms["bucket_why"] = b, why
    BUCKET_ORDER = ["needs-approval", "needs-input", "failed", "spinning", "working", "idle"]

    # ---- fetch ages (read by this tool, at generation time) ----------------
    fetches = []
    for r in repos:
        fa = fetch_age(r.get("path") or "")
        fa["seat"] = r.get("seat")
        fa["project"] = r.get("project")
        fetches.append(fa)
    mail_repo_path = (fed.get("mail_repo") or {}).get("path")
    board_mtime = file_mtime(board.get("path") or "")

    # ---- disagreements (never silently resolved) --------------------------
    dis = []
    for ms in model_seats:
        s, repo = ms["seat"], ms["repo"]
        sid = s.get("id")
        ses = s.get("session") or {}
        mf, rm = ses.get("model_flag"), s.get("model")
        if mf and rm and mf != rm:
            dis.append({"seat": sid, "what": "model",
                        "a": f"roster.json says {rm}", "b": f"the running process was launched with {mf}",
                        "why": "roster is intent, argv is reality — the seat is not running the model it was assigned."})
        if ses.get("live") and not s.get("watcher_running"):
            dis.append({"seat": sid, "what": "listening",
                        "a": "a session process is running",
                        "b": "no mail-watch/mail-bridge process names this seat",
                        "why": "the seat is alive but nothing will tell it mail arrived. This is the invisibility shape."})
        if s.get("activity") == "LIVE_IDLE" and repo and (repo.get("uncommitted_files") or 0) > 0:
            dis.append({"seat": sid, "what": "activity",
                        "a": "snapshot says LIVE_IDLE",
                        "b": f"the tree has {repo.get('uncommitted_files')} uncommitted files",
                        "why": "uncommitted work exists but no busy signal fired — either just-finished or wedged."})
        if s.get("activity") == "LIVE_BUSY" and repo and (repo.get("uncommitted_files") or 0) > 0 \
                and (repo.get("head_age_seconds") or 0) > 6 * 3600:
            dis.append({"seat": sid, "what": "activity",
                        "a": "LIVE_BUSY (dirty tree)",
                        "b": f"but HEAD is {dur(repo.get('head_age_seconds'), short=True)} old",
                        "why": "a dirty tree an idle session is sitting in reads as BUSY. Files prove work exists, not that it is happening."})
        if (s.get("to_header_mismatches") or 0) > 0:
            dis.append({"seat": sid, "what": "delivery",
                        "a": "the maildir owner says this seat received it",
                        "b": f"{s['to_header_mismatches']} message(s) carry a different to: header",
                        "why": "the header can lie; the directory cannot. Something addressed mail wrongly."})
    for ms in model_seats:
        sid = ms["seat"].get("id")
        snap_says = ms["seat"].get("activity")
        cad_says = ms["cad"].get("verdict")
        if snap_says == "LIVE_BUSY" and cad_says == "stalled":
            dis.append({"seat": sid, "what": "cadence",
                        "a": "snapshot says LIVE_BUSY (its fixed 600s window)",
                        "b": f"by its own cadence it is STALLED — {ms['cad'].get('why')}",
                        "why": "the fixed window and the seat's own rhythm disagree; the fixed one is the "
                               "one nobody calibrated."})
        if snap_says == "LIVE_IDLE" and cad_says == "on-cadence":
            dis.append({"seat": sid, "what": "cadence",
                        "a": "snapshot says LIVE_IDLE",
                        "b": f"by its own cadence it is still on time — {ms['cad'].get('why')}",
                        "why": "a seat that normally answers slowly is not idle just because 600s elapsed."})
        if ms["occ"]["state"] == "spinning":
            dis.append({"seat": sid, "what": "spinning",
                        "a": "the process is burning CPU right now",
                        "b": "nothing has been written or sent since " + dur(ms["cad"].get("silence"), short=True) + " ago",
                        "why": "effort without output. No process table calls this out; it is the agent-specific "
                               "failure mode."})
        owed = [t for t in threads if sid in (t.get("reply_owed_by") or [])]
        if owed and (ms["seat"].get("inbox_unread") or 0) == 0:
            dis.append({"seat": sid, "what": "mail",
                        "a": "inbox_unread is 0",
                        "b": f"{len(owed)} thread(s) list this seat in reply_owed_by",
                        "why": "thread bookkeeping and the maildir disagree about what is unread."})
    # board vs state
    board_items = board.get("items") or []
    inflight = [i for i in board_items if (i.get("section") or "").upper().startswith("IN FLIGHT")]
    for i in inflight:
        a = i.get("agent")
        if a and a in by_id:
            c = by_id[a]["composite"]
            if c in ("Dark", "Deaf", "Unknown"):
                dis.append({"seat": a, "what": "board",
                            "a": f"the board carries an IN FLIGHT item for this seat",
                            "b": f"its live composite state is {c}",
                            "why": "work is booked against a seat that cannot currently receive or is not running."})

    # ---- alerts (derived anomalies only) ----------------------------------
    alerts = []

    def alert(sev, title, evidence, fix=None):
        alerts.append({"sev": sev, "title": title, "evidence": evidence, "fix": fix})

    for ms in model_seats:
        s = ms["seat"]
        sid = s.get("id")
        if ms["m"]["state"] == "deaf":
            alert("red", f"{sid} is DEAF",
                  ms["m"]["detail"] + f"; {s.get('inbox_unread') or 0} message(s) waiting in new/",
                  helper("mail-read") + " " + sid)
        if ms["composite"] == "Dark":
            alert("red", f"{sid} is DARK", "no process could be attributed to this seat; mail sent to it will sit unread.")
        if ms["composite"] == "Unknown":
            alert("amber", f"{sid} state is UNKNOWN", ms["s"]["detail"])
    for b in bridges:
        if (b.get("instance_count") or 0) > 1:
            alert("amber", f"{b.get('instance_count')} copies of {b.get('kind')} for {b.get('target')}",
                  f"pids {', '.join(str(p) for p in (b.get('pids') or []))} — duplicate watchers double-deliver "
                  f"notifications and race each other.",
                  f"pgrep -fl 'mail-watch {b.get('target')}'")
        if not b.get("target_is_roster_seat"):
            # The collector scans the whole process table, so a second network
            # on the same machine shows up here. Its helpers are not stray —
            # they belong to someone else's spool, and saying otherwise sends a
            # reader hunting a fault that does not exist.
            cmdline = b.get("command") or ""
            ours = (mail_root and mail_root in cmdline) or "-d" not in cmdline
            if ours:
                alert("amber", f"{b.get('kind')} running for '{b.get('target')}', which is not a roster seat",
                      f"up {b.get('uptime_human')} — {e(cmdline)[:160]}. Either a leftover from an earlier "
                      "layout, or a seat someone forgot to add to the roster.")
            else:
                other = ""
                parts = cmdline.split()
                if "-d" in parts:
                    i = parts.index("-d")
                    if i + 1 < len(parts):
                        other = parts[i + 1]
                alert("amber", f"another AgentMail network is running on this machine",
                      f"a {b.get('kind')} for '{b.get('target')}' (up {b.get('uptime_human')}) points at "
                      f"{other or 'a different mail root'}, not at {mail_root}. Nothing is wrong with it — it is "
                      "simply not this network, and this page can say nothing about that one.")
    for f in fetches:
        if f.get("epoch") and (now - f["epoch"]) > STALE_FETCH_SECONDS:
            alert("amber", f"{f.get('project')}: last git fetch was {dur(now - f['epoch'], short=True)} ago",
                  "ahead/behind for this repo is measured against a remote ref that old. A fresh snapshot does not "
                  "refresh it.", f"git -C {f.get('path')} fetch --all")
    for r in repos:
        if (r.get("ahead") or 0) > 0:
            alert("amber", f"{r.get('project')}: {r.get('ahead')} commit(s) ahead of {r.get('upstream')}",
                  "work exists only on this machine.", f"git -C {r.get('path')} push")
        if (r.get("behind") or 0) > 0:
            alert("amber", f"{r.get('project')}: {r.get('behind')} commit(s) behind {r.get('upstream')}",
                  "the seat is working on top of an out-of-date branch.")
        if r.get("is_git") and not r.get("upstream") and not r.get("detached"):
            alert("amber", f"{r.get('project')}: branch '{r.get('branch')}' has no upstream",
                  "ahead/behind cannot be computed at all — that pair reads as unknown, not as zero.")
    mr = fed.get("mail_repo") or {}
    if mr.get("is_git") and not mr.get("remote_configured"):
        alert("amber", "the mail repo has no git remote",
              "FEDERATION.md documents git transport for .agent-mail, but no remote is configured: "
              "no other site can receive or send mail here.")
    if (mr.get("uncommitted_files") or 0) > 0:
        alert("amber", f"{mr.get('uncommitted_files')} uncommitted files in .agent-mail",
              "the mail spool is a git repo whose working tree has drifted from its last commit "
              f"({(mr.get('head') or {}).get('age_relative', 'unknown age')}). Nothing is being replicated.")
    for c in (fed.get("external_contributors") or []):
        alert("red" if (c.get("commits") or 0) >= 25 else "amber",
              f"{c.get('name')} has {c.get('commits')} commits in {len(c.get('repos') or [])} repo(s) and NO seat in this network",
              f"{c.get('identity')} — last commit "
              + (dur(now - (epoch_of(c.get('last_commit_at')) or now), short=True) + " ago"
                 if c.get("last_commit_at") else "unknown")
              + ". Every agent here is blind to this person's work; that blindness has already caused one overwrite.")
    for w in (meta.get("warnings") or []):
        alert("amber", "snapshot warning", str(w))
    if meta.get("mail_flow_truncated"):
        alert("amber", "mail flow was truncated",
              f"only the most recent {meta.get('mail_cap')} messages are in this document.")
    if (meta.get("counts") or {}).get("messages_malformed"):
        alert("amber", f"{meta['counts']['messages_malformed']} malformed message file(s)",
              "these could not be parsed and are missing from every count on this page.")
    for e_ in GEN_ERRORS:
        alert("red", "dashboard generator error", e_)

    # ---- reply-debt ledger: TWO kinds, not one ----------------------------
    # (1) NOT-EVEN-READ  — the file is still in new/. The snapshot computes it.
    # (2) READ-BUT-NOT-REPLIED — the file was renamed into cur/ and the
    #     recipient has said nothing on that thread since. The rename IS the
    #     ack under SPEC §3, which is exactly why it proves nothing. This is
    #     the common case and it had no representation anywhere before.
    flow_by_thread: dict = {}
    for m in flow:
        flow_by_thread.setdefault(m.get("thread"), []).append(m)
    debts = []
    for t in threads:
        frm, to = t.get("last_message_from"), t.get("last_message_to")
        if not frm or not to or frm == to:
            continue
        ts = epoch_of(t.get("last_message_at"))
        ack = None
        for m in flow_by_thread.get(t.get("thread"), []):
            if m.get("timestamp") == t.get("last_message_at") and m.get("from") == frm:
                ack = m.get("ack")
        unread = bool(t.get("last_message_unread"))
        debts.append({
            "kind": "not-even-read" if unread else "read-not-replied",
            "owes": to, "to": frm, "thread": t.get("thread"), "synthetic": t.get("synthetic"),
            "epoch": ts, "age": t.get("last_message_age_seconds"),
            "subject": t.get("last_message_subject"), "type": t.get("last_message_type"),
            "unread": unread, "unread_by": t.get("reply_owed_by") or [], "ack": ack,
            "copies": t.get("last_message_copies") or 1, "count": t.get("message_count"),
            "source": "thread bookkeeping (all time)",
        })
    # per-message read-but-not-replied inside the mail window: a message the
    # recipient has opened and left, even though the thread moved on elsewhere.
    for th, msgs in flow_by_thread.items():
        msgs_sorted = sorted(msgs, key=lambda m: m.get("timestamp") or "")
        for i, m in enumerate(msgs_sorted):
            if m.get("unread") or not m.get("to") or m.get("to") == m.get("from"):
                continue
            if m.get("ack") != "requested" and (m.get("type") not in ("task", "blocked")):
                continue
            later = [x for x in msgs_sorted[i + 1:] if x.get("from") == m.get("to")]
            if later:
                continue
            if any(d["thread"] == th and d["owes"] == m.get("to") and d["epoch"] == epoch_of(m.get("timestamp"))
                   for d in debts):
                continue
            debts.append({
                "kind": "read-not-replied", "owes": m.get("to"), "to": m.get("from"), "thread": th,
                "synthetic": th is None, "epoch": epoch_of(m.get("timestamp")),
                "age": m.get("age_seconds"), "subject": m.get("subject"), "type": m.get("type"),
                "unread": False, "unread_by": [], "ack": m.get("ack"), "copies": 1,
                "count": len(msgs_sorted), "source": f"per-message, {meta.get('mail_window_hours', 48)}h window only",
            })
    debts.sort(key=lambda d: (d["age"] is None, -(d["age"] or 0)))

    # ---- wait-for graph + cycle detection ---------------------------------
    edges: dict = {}
    for d in debts:
        if d["owes"] in by_id and d["to"] in by_id:
            k = (d["owes"], d["to"])
            cur = edges.get(k)
            if not cur or (d["age"] or 0) > (cur["age"] or 0):
                edges[k] = {"age": d["age"], "n": (cur or {}).get("n", 0) + 1, "kind": d["kind"],
                            "thread": d["thread"], "subject": d["subject"]}
            else:
                cur["n"] = cur.get("n", 0) + 1
    adj: dict = {}
    for (a, b) in edges:
        adj.setdefault(a, []).append(b)
    cycles = []
    seen_cycles = set()

    def dfs(node, stack):
        for nxt in adj.get(node, []):
            if nxt in stack:
                cyc = stack[stack.index(nxt):] + [nxt]
                key = tuple(sorted(set(cyc)))
                if key not in seen_cycles:
                    seen_cycles.add(key)
                    cycles.append(cyc)
            elif len(stack) < 8:
                dfs(nxt, stack + [nxt])
    for n0 in list(adj):
        dfs(n0, [n0])
    blocked_set = {a for (a, b) in edges}      # this seat owes -> it is blocking someone
    waiting_set = {b for (a, b) in edges}      # someone owes this seat -> it is waiting
    cycle_seats = {s for c in cycles for s in c}

    # ---- dead letters -----------------------------------------------------
    dead = []
    for ms in model_seats:
        sid = ms["seat"].get("id")
        for f in (ms["scan"].get("tmp_stranded") or []):
            dead.append({"seat": sid, "kind": "stranded in tmp/", "name": f["name"], "epoch": f["epoch"]})
        n = ms["seat"].get("to_header_mismatches") or 0
        if n:
            dead.append({"seat": sid, "kind": "to: header disagrees with the maildir it landed in",
                         "name": f"{n} message(s)", "epoch": None})

    # ---- pair matrix (window only) ----------------------------------------
    pairs: dict = {}
    for m in flow:
        f_, t_ = m.get("from"), m.get("to")
        if f_ and t_:
            pairs[(f_, t_)] = pairs.get((f_, t_), 0) + 1

    # ---- alerts that need the derived structures --------------------------
    for ms in model_seats:
        sid = ms["seat"].get("id")
        d = ms["depth"]
        if d and d.get("falling_behind"):
            alert("red" if d["grew_last_3h"] >= 3 else "amber",
                  f"{sid}: mailbox depth is GROWING (+{d['grew_last_3h']} in 3h)",
                  "the alarm is on the derivative, not the count: a backlog that grows is a seat falling behind, "
                  "whatever its absolute depth. Reconstructed from arrival times of mail still in new/ — it is a "
                  "lower bound, because anything already read is invisible to it.",
                  helper("mail-read") + " " + sid)
        if ms["occ"]["state"] == "spinning":
            alert("red", f"{sid} is SPINNING", ms["occ"]["detail"])
    for c in cycles:
        alert("red", "DEADLOCK: reply cycle " + " → ".join(c),
              "each seat in this ring is waiting for a reply from the next. Nobody in it will move without an "
              "outside interrupt — this is exactly the shape the overseer/child escalation loop makes.")
    if dead:
        alert("amber", f"{len(dead)} dead letter(s)",
              "; ".join(f"{x['seat']}: {x['kind']} ({x['name']})" for x in dead[:6])
              + ("…" if len(dead) > 6 else "")
              + ". SPEC §2 tells readers to ignore tmp/, which is why a write that died half-way is invisible "
                "to everything else in this network.")

    return {
        "meta": meta, "doc": doc, "now": now, "snap_epoch": snap_epoch,
        "seats": model_seats, "by_id": by_id, "seat_ids": seat_ids,
        "repos": repos, "repo_by_seat": repo_by_seat, "flow": flow, "threads": threads,
        "bridges": bridges, "board": board, "fed": fed, "fetches": fetches,
        "board_mtime": board_mtime, "alerts": alerts, "dis": dis, "debts": debts,
        "pairs": pairs, "out_path": out_path, "args": args,
        "mail_repo_path": mail_repo_path, "edges": edges, "cycles": cycles,
        "ident": ident, "short_seat": short_seat,
        "blocked_set": blocked_set, "waiting_set": waiting_set, "cycle_seats": cycle_seats,
        "dead": dead, "bucket_order": BUCKET_ORDER, "cpu_probed": bool(cpu),
        "window_start": window_start,
    }


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
