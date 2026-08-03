# -*- coding: utf-8 -*-
"""python -m netdash — same entry point as bin/network-dashboard."""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
