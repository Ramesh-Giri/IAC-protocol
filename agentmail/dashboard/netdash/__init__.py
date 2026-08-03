# -*- coding: utf-8 -*-
"""netdash — render an AgentMail network-snapshot as one self-contained HTML
instrument panel.

The commitment, in one sentence: the page never asserts more than the
filesystem proved at snapshot time, and where the system is unobservable it
prints a labelled hole instead of a reassuring default.

Layer order (imports only ever point downwards):
    thresholds -> util -> probes -> state -> glyphs -> identity
                                          -> model -> panels -> page -> cli
"""

__version__ = "1.1.0"
