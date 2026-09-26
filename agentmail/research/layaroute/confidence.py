"""Accuracy and coverage of Laya's kind answer as a function of its top probability (to set a data-based confidence floor)."""
import json
rows = {x["id"]: x for x in json.load(open("dataset.json")) if not x["standing"]}
res = json.load(open("laya_zeroshot_results.json"))
COLL = {"review": "review", "security_audit": "security", "security_fix": "security", "plan_research": "plan_research"}
for key in ("desc|v1_9way|fwd", "desc|v2_4way|fwd"):
    v = key.split("|")[1]; print(key)
    P = [(max(p["probs"].values()), p["pred"] == (rows[p["id"]]["kind"] if v.startswith("v1") else COLL.get(rows[p["id"]]["kind"], "build")), p) for p in res[key]]
    for t in (0.0, 0.5, 0.6, 0.7, 0.8, 0.9):
        s = [ok for pr, ok, _ in P if pr >= t]
        print(f"  floor {t:.1f}: coverage {len(s)/len(P):.2f} accuracy-on-covered {sum(s)/len(s):.3f}")
    if v.startswith("v2"):
        sec = [(max(p['probs'].values()), p['probs'].get('security', 0)) for pr, ok, p in P if COLL.get(rows[p['id']]['kind']) == "security"]
        for t in (0.5, 0.3, 0.2, 0.1):
            print(f"  seats truly security-flavored with P(security) >= {t}: {sum(1 for _, s in sec if s >= t)}/{len(sec)}")
        non = [p['probs'].get('security', 0) for pr, ok, p in P if COLL.get(rows[p['id']]['kind']) != "security"]
        for t in (0.5, 0.3, 0.2, 0.1):
            print(f"  NON-security seats wrongly locked at P(security) >= {t}: {sum(1 for s in non if s >= t)}/{len(non)}")
