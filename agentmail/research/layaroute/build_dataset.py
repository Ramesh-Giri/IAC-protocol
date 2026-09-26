"""Join roster + kind labels + attachment brief text + inferred date -> dataset.json (routable seats only)."""
import json, re, os, collections
from label_kinds import kind, SKIP, STANDING, ROSTER
ATT = "/Users/darkness/Work/Aureus/.agent-mail/attachments/"
r = json.load(open(ROSTER))["agents"]
rows, last_date = [], None
for i, (k, a) in enumerate(r.items()):
    d = a["description"]
    m = re.search(r"attachments/(task-[\w.-]+\.md)", d)
    brief = None
    if m and os.path.exists(ATT + m.group(1)):
        t = open(ATT + m.group(1), errors="ignore").read()
        brief = re.sub(r"\s+", " ", t)[:1500]
    dm = re.search(r"(2026)(\d\d)(\d\d)", d) or re.search(r"-(09)(\d\d)-ramesh$", k)
    date = None
    if dm: date = f"2026-{dm.group(2)}-{dm.group(3)}" if dm.group(1) == "2026" else f"2026-09-{dm.group(2)}"
    if date: last_date = date
    if k in SKIP and k not in STANDING: continue
    rows.append(dict(i=i, id=k, project=a.get("project"), desc=d, brief=brief, date=date or last_date or "2026-09-14", date_inferred=date is None,
                     runtime=a["runtime"], model=a["model"], standing=k in STANDING, kind=None if k in STANDING else kind(k, d)))
json.dump(rows, open("dataset.json", "w"), indent=1)
t = [x for x in rows if not x["standing"]]
print(len(rows), "rows;", len(t), "task seats;", sum(1 for x in t if x["brief"]), "with attachment brief")
print(collections.Counter(x["runtime"] + "/" + x["model"] for x in t).most_common())
