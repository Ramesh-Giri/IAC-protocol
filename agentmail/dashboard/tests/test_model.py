# -*- coding: utf-8 -*-
"""Model-level derivations: identity, debts, the wait-for graph, and the
end-to-end contract that a broken input still produces a page."""

import argparse
import json
import os
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from netdash import identity, model, page  # noqa: E402


def snapshot(seats=None, flow=None, threads=None, **kw):
    now = int(time.time())
    doc = {
        "meta": {"generated_at_epoch": now, "generated_at": "2026-08-03T10:00:00Z", "mail_window_hours": 48,
                 "counts": {}, "roster_owner": "overseer-site", "mail_root": "/nonexistent",
                 "activity_rules": {"busy_window_seconds": 600}, "warnings": []},
        "seats": seats or [], "repos": [], "mail_flow": flow or [], "threads": threads or [],
        "bridges": [], "board": {"exists": False, "items": []},
        "federation": {"sites": [], "external_contributors": []},
    }
    doc.update(kw)
    return doc


def seat(sid, **kw):
    s = {"id": sid, "role": "child", "site": "acme", "home": "/nonexistent", "home_exists": True,
         "maildir_present": True, "inbox_unread": 0, "inbox_processed": 1, "watcher_running": True,
         "session": {"live": True, "pid": 0, "candidates": []}, "activity": "LIVE_IDLE",
         "activity_evidence": [], "mail_sent_total": 1}
    s.update(kw)
    return s


ARGS = argparse.Namespace(json=None, out="x", snapshot_bin="", mail_root=None, hours=None, quiet=True)


class TestIdentity(unittest.TestCase):
    """Nothing about any particular site is written into this package."""

    def test_identity_comes_from_the_roster(self):
        fed = {"sites": [{"site": "acme", "is_local": True, "human": "Dana Okafor", "machine": "mb"}]}
        ident = identity.site_identity(fed, {}, [seat("build-acme")])
        self.assertEqual(ident["human"], "Dana Okafor")
        self.assertEqual(ident["human_short"], "Dana")
        self.assertEqual(ident["suffix"], "-acme")

    def test_suffix_is_only_stripped_when_the_seats_actually_use_it(self):
        fed = {"sites": [{"site": "acme", "is_local": True, "human": "Dana"}]}
        ident = identity.site_identity(fed, {}, [seat("build-bot")])
        self.assertEqual(ident["suffix"], "")

    def test_unnamed_human_is_admitted_not_invented(self):
        ident = identity.site_identity({"sites": []}, {"roster_owner": "overseer-zed"}, [])
        self.assertFalse(ident["human_named"])
        self.assertEqual(ident["human"], "the human")   # never invented from a seat id

    def test_a_single_site_is_local_even_without_the_flag(self):
        fed = {"sites": [{"site": "solo", "human": "Sam"}]}
        self.assertEqual(identity.site_identity(fed, {}, [])["human"], "Sam")


class TestDebtsAndGraph(unittest.TestCase):
    def build(self, **kw):
        return model.build_model(snapshot(**kw), "out.html", ARGS)

    def test_read_but_not_replied_is_found(self):
        seats = [seat("a-acme"), seat("b-acme")]
        threads = [{"thread": "t1", "message_count": 1, "last_message_from": "a-acme",
                    "last_message_to": "b-acme", "last_message_at": "2026-08-03T09:00:00Z",
                    "last_message_age_seconds": 3600, "last_message_unread": False,
                    "reply_owed_by": [], "last_message_subject": "please do x", "last_message_type": "task"}]
        M = self.build(seats=seats, threads=threads)
        self.assertEqual(len(M["debts"]), 1)
        self.assertEqual(M["debts"][0]["kind"], "read-not-replied")
        self.assertEqual(M["debts"][0]["owes"], "b-acme")

    def test_unread_debt_is_labelled_differently(self):
        seats = [seat("a-acme"), seat("b-acme")]
        threads = [{"thread": "t1", "message_count": 1, "last_message_from": "a-acme",
                    "last_message_to": "b-acme", "last_message_at": "2026-08-03T09:00:00Z",
                    "last_message_age_seconds": 60, "last_message_unread": True,
                    "reply_owed_by": ["b-acme"], "last_message_subject": "s", "last_message_type": "task"}]
        M = self.build(seats=seats, threads=threads)
        self.assertEqual(M["debts"][0]["kind"], "not-even-read")

    def test_a_reply_cycle_is_reported_as_possible_not_proven_deadlock(self):
        seats = [seat("a-acme"), seat("b-acme")]
        threads = [
            {"thread": "t1", "message_count": 1, "last_message_from": "a-acme", "last_message_to": "b-acme",
             "last_message_at": "2026-08-03T09:00:00Z", "last_message_age_seconds": 3600,
             "last_message_unread": False, "reply_owed_by": [], "last_message_subject": "x",
             "last_message_type": "task"},
            {"thread": "t2", "message_count": 1, "last_message_from": "b-acme", "last_message_to": "a-acme",
             "last_message_at": "2026-08-03T09:30:00Z", "last_message_age_seconds": 1800,
             "last_message_unread": False, "reply_owed_by": [], "last_message_subject": "y",
             "last_message_type": "task"},
        ]
        M = self.build(seats=seats, threads=threads)
        self.assertTrue(M["cycles"], "a mutual wait must be reported as a cycle")
        self.assertEqual(M["cycle_seats"], {"a-acme", "b-acme"})
        self.assertTrue(any("POSSIBLE WAIT CYCLE" in a["title"] for a in M["alerts"]))
        self.assertFalse(any("DEADLOCK" in a["title"] for a in M["alerts"]))

    def test_notifications_create_no_reply_debt(self):
        for m in ({"type": "info", "ack": "none"}, {"type": "task", "expects_reply": False}):
            flow = [dict(m, id="r1", thread="t", **{"from": "a", "to": "b", "timestamp": "2026-08-03T09:00:00Z"})]
            self.assertFalse(self.build(flow=flow)["debts"])

    def test_only_correlated_recipient_response_clears_request(self):
        request = {"id": "r1", "from": "a", "to": "b", "thread": "t", "type": "task",
                   "timestamp": "2026-08-03T09:00:00Z"}
        response = {"id": "r2", "from": "b", "to": "a", "thread": "t", "type": "report",
                    "in_reply_to": "r1", "timestamp": "2026-08-03T10:00:00Z"}
        for changes in ({"from": "c"}, {"in_reply_to": "different"}, {"type": "ack"}):
            self.assertEqual(len(self.build(flow=[request, dict(response, **changes)])["debts"]), 1)
        self.assertFalse(self.build(flow=[request, response])["debts"])

    def test_same_second_requests_do_not_collapse(self):
        request = {"from": "a", "to": "b", "thread": "t", "type": "task", "timestamp": "2026-08-03T09:00:00Z"}
        self.assertEqual(len(self.build(flow=[dict(request, id="r1"), dict(request, id="r2")])["debts"]), 2)

    def test_legacy_filename_reply_works_without_thread(self):
        request = {"from": "a", "to": "b", "type": "task", "file": "legacy.md", "timestamp": "2026-08-03T09:00:00Z"}
        response = {"from": "b", "to": "a", "type": "report", "in_reply_to": "legacy.md", "timestamp": "2026-08-03T10:00:00Z"}
        self.assertFalse(self.build(flow=[request, response])["debts"])

    def test_no_debt_no_graph(self):
        M = self.build(seats=[seat("a-acme")])
        self.assertEqual(M["edges"], {})
        self.assertEqual(M["cycles"], [])


class TestTriage(unittest.TestCase):
    def test_a_deaf_seat_outranks_a_working_one(self):
        seats = [seat("busy-acme", activity="LIVE_BUSY"),
                 seat("deaf-acme", watcher_running=False, inbox_unread=4, unread_age_seconds=99999)]
        M = model.build_model(snapshot(seats=seats), "out.html", ARGS)
        by_id = {ms["seat"]["id"]: ms["bucket"] for ms in M["seats"]}
        order = M["bucket_order"]
        self.assertEqual(by_id["deaf-acme"], "failed")
        self.assertLess(order.index(by_id["deaf-acme"]), order.index(by_id["busy-acme"]))

    def test_every_seat_lands_in_exactly_one_known_bucket(self):
        seats = [seat("a-acme"), seat("b-acme", session={"live": False, "candidates": []}, activity="DARK")]
        M = model.build_model(snapshot(seats=seats), "out.html", ARGS)
        for ms in M["seats"]:
            self.assertIn(ms["bucket"], M["bucket_order"])


class TestFallingBehind(unittest.TestCase):
    """A growing queue is only a fault when the seat is also slow to it."""

    def seats_with(self, unread_age, sent_gaps_hours=2):
        # a seat with an established rhythm and one queued message
        s = seat("q-acme", inbox_unread=1, unread_age_seconds=unread_age, inbox_processed=3)
        return [s]

    def test_one_new_message_is_traffic_not_a_fault(self):
        M = model.build_model(snapshot(seats=self.seats_with(60)), "o.html", ARGS)
        ms = M["seats"][0]
        self.assertNotEqual(ms["bucket"], "spinning")
        self.assertFalse((ms["depth"] or {}).get("falling_behind"))

    def test_no_cadence_means_no_falling_behind_claim(self):
        M = model.build_model(snapshot(seats=self.seats_with(99999)), "o.html", ARGS)
        d = M["seats"][0]["depth"] or {}
        self.assertFalse(d.get("falling_behind"))
        if d.get("growing"):
            self.assertIn("no cadence", d.get("behind_why", ""))


class TestPageContract(unittest.TestCase):
    """A page is always produced, and it never contains an unresolved value."""

    def render(self, doc):
        M = model.build_model(doc, "out.html", ARGS)
        return page.render_page(M)

    def test_empty_roster_still_renders(self):
        html = self.render(snapshot())
        self.assertIn("<title>", html)
        self.assertNotIn("{", html.split("<style>")[0])

    def test_page_is_self_contained(self):
        html = self.render(snapshot(seats=[seat("a-acme")]))
        for forbidden in ("http://", "https://", "<script src", "<link rel=\"stylesheet\""):
            self.assertNotIn(forbidden, html)

    def test_failure_page_is_produced_when_there_is_no_snapshot(self):
        html = page.render_failure_page("collector exploded", "out.html")
        self.assertIn("deliberately empty", html)
        self.assertIn("collector exploded", html)

    def test_panels_are_collapsible_and_reorderable(self):
        html = self.render(snapshot(seats=[seat("a-acme")]))
        # every panel is addressable, has a drag handle and a labelled toggle
        import re
        pids = re.findall(r'<section class="panel" id="(p\d+)" data-pid="\1"', html)
        self.assertEqual(len(pids), 9)
        self.assertEqual(html.count('class="drag"'), 9)
        self.assertEqual(html.count('class="ph-btn"'), 9)
        for pid in pids:
            self.assertIn(f'aria-controls="{pid}-body"', html)
            self.assertIn(f'<div class="panel-body" id="{pid}-body">', html)
        # only the panels a human is answerable for open on a first visit
        self.assertEqual(html.count('data-collapsed="1"'), 9 - 3)

    def test_the_page_admits_its_controls_are_view_only(self):
        html = self.render(snapshot(seats=[seat("a-acme")]))
        self.assertIn("view state only", html)
        self.assertIn("no control plane", html.lower())

    def test_tags_are_balanced(self):
        from html.parser import HTMLParser
        void = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param",
                "source", "track", "wbr", "path", "circle", "line", "rect", "polygon", "polyline",
                "text", "marker", "use", "stop"}

        class P(HTMLParser):
            def __init__(s):
                super().__init__(convert_charrefs=True)
                s.stack, s.err = [], []

            def handle_starttag(s, t, a):
                if t not in void:
                    s.stack.append(t)

            def handle_endtag(s, t):
                if t in void:
                    return
                if s.stack and s.stack[-1] == t:
                    s.stack.pop()
                else:
                    s.err.append(t)

        p = P()
        p.feed(self.render(snapshot(seats=[seat("a-acme"), seat("b-acme")])))
        self.assertEqual(p.err, [])
        self.assertEqual(p.stack, [])


if __name__ == "__main__":
    unittest.main()
