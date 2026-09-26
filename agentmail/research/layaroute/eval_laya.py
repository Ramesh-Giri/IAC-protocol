"""Zero-shot Laya task-KIND classification over the roster (local CPU inference, no network, no GCP).
Wordings are FIXED BEFORE RUNNING (no tuning on this set - see LAYA_TODO_DETECTOR_STATE: ~60 tuned combos inflated a number before).
Two wordings x two option orders, on two inputs (description; description + attachment brief head)."""
import json, time, collections, sys, warnings
warnings.filterwarnings("ignore")
import laya
V1 = {  # 9-way, the full choice set
 "review": "read-only review or re-review of someone else's change",
 "fix_findings": "fix the problems a reviewer found",
 "security_audit": "security audit, penetration test or vulnerability hunt",
 "security_fix": "implement a security hardening fix",
 "feature": "build a new feature or capability",
 "bugfix": "fix a bug or live incident",
 "ui": "change the look or layout of the user interface",
 "integrate": "merge, land or release branches",
 "plan_research": "plan, design, research or measure without changing code",
}
V2 = {  # 4-way, only the distinctions a policy would act on
 "review": "read-only review or re-review of someone else's change",
 "security": "security audit, penetration test, or a security fix",
 "plan_research": "plan, design, research or measure without changing code",
 "build": "write or change code: feature, bug fix, UI change, merge or release",
}
COLLAPSE = {"review": "review", "security_audit": "security", "security_fix": "security", "plan_research": "plan_research"}
INSTR = "What kind of work does this task brief describe?"
rows = [x for x in json.load(open("dataset.json")) if not x["standing"]]
agent = laya.load(device="cpu")
def run(table, order, texts):
    keys = list(table) if order == "fwd" else list(reversed(list(table)))
    q = {"kind": {"type": "choice", "instructions": INSTR, "criteria": {k: table[k] for k in keys}}}
    out = []
    for t in texts:
        a = agent.system_one(t, q)["answers"]["kind"]
        out.append((a["choice"], a["probabilities"]))
    return out
res = {}
for inp in ("desc", "desc+brief"):
    sub = rows if inp == "desc" else [x for x in rows if x["brief"]]
    texts = [x["desc"] if inp == "desc" else x["desc"] + "\n" + x["brief"][:700] for x in sub]
    for vn, table in (("v1_9way", V1), ("v2_4way", V2)):
        for order in ("fwd", "rev"):
            t0 = time.time(); r = run(table, order, texts)
            res[f"{inp}|{vn}|{order}"] = [dict(id=x["id"], pred=p[0], probs=p[1]) for x, p in zip(sub, r)]
            print(inp, vn, order, len(sub), f"{time.time()-t0:.0f}s", flush=True)
json.dump(res, open("laya_zeroshot_results.json", "w"))
