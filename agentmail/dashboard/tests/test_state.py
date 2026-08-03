# -*- coding: utf-8 -*-
"""The derivations that decide what a human is told. Each test names the real
failure it protects against, because that is the only reason any of them exist.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from netdash import state, thresholds  # noqa: E402

HOUR = 3600
NOW = 1_800_000_000


class TestCadence(unittest.TestCase):
    """A seat's deadline is its own rhythm, never a number we picked."""

    def test_no_events_gives_no_verdict(self):
        c = state.cadence([], NOW)
        self.assertEqual(c["verdict"], "no-cadence")
        self.assertIn("no observable output", c["why"])

    def test_too_few_events_refuses_to_judge(self):
        c = state.cadence([NOW - 60, NOW - 30], NOW)
        self.assertEqual(c["verdict"], "no-cadence")
        self.assertIn("fewer than", c["why"])

    def test_a_burst_alone_supports_no_verdict(self):
        # regression: six messages 8s apart used to yield an 8s deadline, so the
        # sender read as STALLED a minute after a broadcast. A burst is one
        # episode of activity, not a rhythm.
        burst = [NOW - 600 + i * 8 for i in range(6)]
        c = state.cadence(burst, NOW)
        self.assertEqual(c["verdict"], "no-cadence", c["why"])
        self.assertIn("too little observation", c["why"])

    def test_a_burst_inside_a_longer_history_is_still_judged(self):
        hist = [NOW - 6 * HOUR + i * 900 for i in range(12)]     # every 15m
        hist += [NOW - 300 + i * 8 for i in range(6)]            # then a burst
        c = state.cadence(hist, NOW)
        self.assertEqual(c["verdict"], "on-cadence", c["why"])

    def test_slow_seat_is_not_stalled_at_ten_minutes(self):
        six_hourly = [NOW - i * 6 * HOUR for i in range(6, 0, -1)]
        c = state.cadence(six_hourly, NOW - 0)
        self.assertEqual(c["verdict"], "on-cadence")

    def test_fast_seat_is_stalled_once_it_exceeds_its_own_worst_gap(self):
        every_3min = [NOW - 3600 + i * 180 for i in range(20)]
        silent = state.cadence(every_3min, NOW + 1800)
        self.assertEqual(silent["verdict"], "stalled")

    def test_old_activity_does_not_set_todays_deadline(self):
        ancient = [NOW - (60 + i) * 86400 for i in range(6)]
        c = state.cadence(ancient, NOW)
        self.assertEqual(c["verdict"], "no-cadence")
        self.assertIn("last %d days" % thresholds.CADENCE_LOOKBACK_DAYS, c["why"])

    def test_mail_arriving_mid_scan_never_prints_a_negative_age(self):
        c = state.cadence([NOW + 5], NOW)
        self.assertGreaterEqual(c["silence"], 0)


class TestMailbox(unittest.TestCase):
    """Deaf is a fact about listening, not about volume."""

    def base(self, **kw):
        seat = {"maildir_present": True, "inbox_unread": 0, "inbox_processed": 5,
                "unread_age_seconds": None, "watcher_running": True}
        seat.update(kw)
        return state.slot_mailbox(seat)

    def test_clear(self):
        self.assertEqual(self.base()["state"], "clear")

    def test_no_watcher_is_deaf_even_with_an_empty_inbox(self):
        sl = self.base(watcher_running=False)
        self.assertEqual(sl["state"], "deaf")
        self.assertIn("no mail-watch", sl["detail"])

    def test_old_unread_is_deaf(self):
        self.assertEqual(self.base(inbox_unread=9, unread_age_seconds=5 * HOUR)["state"], "deaf")

    def test_never_processed_is_deaf(self):
        self.assertEqual(self.base(inbox_unread=2, inbox_processed=0, unread_age_seconds=60)["state"], "deaf")

    def test_no_maildir_is_a_hole_not_a_zero(self):
        self.assertEqual(self.base(maildir_present=False)["state"], "dash")


class TestLiveness(unittest.TestCase):
    """Never-started, stopped-or-lost and unreachable are three different
    claims and must never collapse into 'down'."""

    def test_live(self):
        seat = {"home_exists": True, "session": {"live": True, "pid": 1, "detection": "watcher-ancestry"}}
        self.assertEqual(state.derive_liveness(seat, [NOW])["state"], "live")

    def test_unreachable_when_home_is_gone(self):
        seat = {"home_exists": False, "session": {"live": True}}
        self.assertEqual(state.derive_liveness(seat, [])["state"], "unreachable")

    def test_never_started_when_nothing_was_ever_observed(self):
        seat = {"home_exists": True, "session": {"live": False}, "inbox_processed": 0, "mail_sent_total": 0}
        self.assertEqual(state.derive_liveness(seat, [])["state"], "never-started")

    def test_stopped_or_lost_keeps_the_last_output_time(self):
        seat = {"home_exists": True, "session": {"live": False}, "mail_sent_total": 3}
        liv = state.derive_liveness(seat, [NOW - 900])
        self.assertEqual(liv["state"], "stopped-or-lost")
        self.assertEqual(liv["at"], NOW - 900)
        self.assertIn("no exit record", liv["detail"])


class TestOccupancy(unittest.TestCase):
    def test_interrupted_beats_everything_and_says_it_is_self_reported(self):
        occ = state.derive_occupancy({}, {"verdict": "on-cadence"}, {"pct": 90.0},
                                     True, {"state": "clear"}, True, {"sent": 5})
        self.assertEqual(occ["state"], "interrupted")
        self.assertIn("self-reported", occ["detail"])

    def test_spinning_needs_burn_and_silence_together(self):
        cad = {"verdict": "stalled", "silence": 4000, "deadline": 600}
        hot = state.derive_occupancy({}, cad, {"pct": 40.0, "gap": 1.5}, False, {"state": "clear"}, True, {})
        self.assertEqual(hot["state"], "spinning")
        cold = state.derive_occupancy({}, cad, {"pct": 0.2, "gap": 1.5}, False, {"state": "clear"}, True, {})
        self.assertNotEqual(cold["state"], "spinning")

    def test_on_cadence_without_output_is_not_working(self):
        # regression: "not overdue" was being reported as "producing"
        occ = state.derive_occupancy({}, {"verdict": "on-cadence", "why": ""}, None, False,
                                     {"state": "clear"}, True, {"sent": 0, "commits": 0})
        self.assertEqual(occ["state"], "waiting-for-mail")

    def test_a_dead_process_has_no_observable_occupancy(self):
        occ = state.derive_occupancy({}, {"verdict": "stalled"}, None, False, {"state": "clear"}, False, {})
        self.assertEqual(occ["state"], "unknown")


class TestDepth(unittest.TestCase):
    """The alarm is on the derivative; the absolute number is a lower bound."""

    def test_growing_backlog_is_detected(self):
        arrivals = [NOW - 30 * HOUR, NOW - 2 * HOUR, NOW - HOUR, NOW - 600]
        d = state.depth_series(arrivals, NOW)
        self.assertTrue(d["growing"])
        self.assertEqual(d["buckets"][-1], 4)

    def test_old_backlog_that_stopped_growing_does_not_alarm(self):
        d = state.depth_series([NOW - 40 * HOUR] * 9, NOW)
        self.assertFalse(d["growing"])
        self.assertEqual(d["older_than_window"], 9)

    def test_empty_is_flat(self):
        d = state.depth_series([], NOW)
        self.assertEqual(d["max"], 0)
        self.assertFalse(d["growing"])


class TestComposite(unittest.TestCase):
    def test_deaf_outranks_working(self):
        word, _ = state.composite({"state": "filled"}, {"state": "deaf"}, {"state": "producing"}, False, 10)
        self.assertEqual(word, "Deaf")

    def test_dark_outranks_deaf(self):
        word, _ = state.composite({"state": "hollow"}, {"state": "deaf"}, {"state": "quiet"}, False, 10)
        self.assertEqual(word, "Dark")

    def test_unknown_when_a_slot_could_not_be_read(self):
        word, _ = state.composite({"state": "dash"}, {"state": "clear"}, {"state": "quiet"}, False, 10)
        self.assertEqual(word, "Unknown")


if __name__ == "__main__":
    unittest.main()
