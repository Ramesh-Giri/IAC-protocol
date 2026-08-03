# -*- coding: utf-8 -*-
"""Who this network belongs to -- read from the roster, never from this source.

No site name, human name, seat id, project or path is written down anywhere in
this package. Clone the repo onto another machine with another roster and the
page renders that site: its own human in the panel titles, its own seats in the
tree, its own suffix stripped from cramped labels. Where the roster names
nobody, the page says so instead of inventing a name."""

from __future__ import annotations

def site_identity(fed: dict, meta: dict, seats: list) -> dict:
    """Everything name-shaped comes from roster.json, never from this file.

    A different machine with a different roster renders as that site: its own
    human, its own seat ids, its own projects, its own suffix. Nothing here
    knows the name of any particular site or person.
    """
    site = next((x for x in (fed.get("sites") or []) if x.get("is_local")), None)
    if site is None:
        sites = fed.get("sites") or []
        site = sites[0] if len(sites) == 1 else {}
    human = (site.get("human") or "").strip()
    site_id = (site.get("site") or fed.get("local_site") or "").strip()
    owner = (meta.get("roster_owner") or "").strip()
    if not human:
        # The roster names no human for this site. A seat id is not a person,
        # so nothing is invented from it: the page says "the human" and the
        # tree card says the roster named nobody.
        human = "the human"
    short = human.split()[0] if human.split() else human
    # the seat-id suffix is whatever this site calls itself, e.g. "-<site>"
    suffix = f"-{site_id}" if site_id else ""
    if suffix and not any((x.get("id") or "").endswith(suffix) for x in seats):
        suffix = ""
    return {"site": site, "site_id": site_id, "human": human, "human_short": short,
            "owner": owner, "suffix": suffix,
            "human_named": bool((site.get("human") or "").strip())}
