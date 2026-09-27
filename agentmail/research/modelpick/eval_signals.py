"""Requirement-SIGNAL extraction: does Laya read a task and emit the flags a catalogue matcher needs?
Two binary signals, wording FIXED BEFORE RUNNING, two option orders, description text only (n=230 routable seats).
Truth = the layaroute author's kind labels (regex-assisted, hand-reviewed): CIRCULAR for any regex baseline. Read as such.
Local CPU, HF_HUB_OFFLINE=1, no network, no GCP."""
import json, re, time, warnings, sys
warnings.filterwarnings("ignore")
import laya
rows = [x for x in json.load(open("dataset.json")) if not x["standing"]]
SIG = {
 "security": ("Does this task involve security testing, a security audit, penetration testing, exploit work, or a security fix?",
              {"yes": "yes, it is security work", "no": "no, it is not security work"},
              lambda k: k in ("security_audit", "security_fix")),
 "readonly": ("Is this task read-only, meaning it must not change any code (a review, a plan, research or a measurement)?",
              {"yes": "yes, read-only, no code changes", "no": "no, it changes or writes code"},
              lambda k: k in ("review", "plan_research", "security_audit")),
}
agent = laya.load(device="cpu")
out = {}
for name, (q, crit, truth) in SIG.items():
    for order in ("fwd", "rev"):
        keys = list(crit) if order == "fwd" else list(reversed(list(crit)))
        qq = {"s": {"type": "choice", "instructions": q, "criteria": {k: crit[k] for k in keys}}}
        t0 = time.time(); res = []
        for x in rows:
            a = agent.system_one(x["desc"], qq)["answers"]["s"]
            res.append(dict(id=x["id"], kind=x["kind"], truth=truth(x["kind"]), p_yes=a["probabilities"]["yes"], desc=x["desc"]))
        out[f"{name}|{order}"] = res
        print(name, order, f"{time.time()-t0:.0f}s", flush=True)
json.dump(out, open("signals_results.json", "w"))
