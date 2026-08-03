# -*- coding: utf-8 -*-
"""Every number this dashboard judges by, in one file, each with the reason it
exists. A threshold you cannot justify is a threshold that gets ignored within
a week, so the ones that survive here are either (a) the site's own written
rule, or (b) a bound on this tool's own sampling — never a guess about how fast
an agent "should" work. The per-seat deadlines are NOT here: they are derived
from each seat's own observed cadence at runtime (see state.cadence)."""

from __future__ import annotations

DEAF_UNREAD_SECONDS = 4 * 3600     # from the site's own listening rule, not invented here

LAG_UNREAD_SECONDS = 30 * 60

RECENT_WORK_SECONDS = 3600

MUTE_SILENCE_SECONDS = 2 * 3600

STALE_FETCH_SECONDS = 24 * 3600

FRESH_SECONDS = 5 * 60

AGING_SECONDS = 15 * 60

CADENCE_EVENTS = 20                # how many of a seat's own events define its window

CADENCE_MIN_EVENTS = 3             # below this, no verdict is issued at all

CADENCE_LOOKBACK_DAYS = 7          # 'recent' means recent: older events do not set the deadline

CPU_SAMPLE_GAP = 1.5               # seconds between the two ps samples

CPU_SPIN_PERCENT = 8.0             # ≥ this much CPU in the sample = burning cycles now

DEPTH_BUCKET_HOURS = 1

DEPTH_BUCKETS = 24

TMP_STRANDED_SECONDS = 300         # a file in tmp/ younger than this may be mid-write
