"""Score laya_zeroshot_results.json against the author's kind labels; then end-to-end against the model actually chosen."""
import json, collections
rows = {x["id"]: x for x in json.load(open("dataset.json")) if not x["standing"]}
res = json.load(open("laya_zeroshot_results.json"))
COLL = {"review": "review", "security_audit": "security", "security_fix": "security", "plan_research": "plan_research"}
def cls(x): return "codex" if x["runtime"].startswith("codex") else ("opus" if "opus" in x["model"] else "sonnet")
def truth(x, v): return x["kind"] if v.startswith("v1") else COLL.get(x["kind"], "build")
print("=== kind accuracy vs author labels (zero-shot; majority-class baseline in brackets) ===")
best = {}
for key, preds in res.items():
    inp, v, order = key.split("|")
    ids = [p["id"] for p in preds]; y = [truth(rows[i], v) for i in ids]; pr = [p["pred"] for p in preds]
    acc = sum(a == b for a, b in zip(y, pr)) / len(y); maj = collections.Counter(y).most_common(1)[0]
    print(f"{key:28s} n={len(y):3d} acc={acc:.3f}  [majority '{maj[0]}' {maj[1]/len(y):.3f}]")
key = "desc|v1_9way|fwd"
for key in ("desc|v1_9way|fwd", "desc|v2_4way|fwd"):
    inp, v, order = key.split("|"); preds = res[key]
    y = [truth(rows[p["id"]], v) for p in preds]; pr = [p["pred"] for p in preds]
    print(f"\n--- per-kind recall/precision, {key} ---")
    for k in sorted(set(y) | set(pr), key=lambda k: -y.count(k)):
        tp = sum(a == b == k for a, b in zip(y, pr)); n = y.count(k); npred = pr.count(k)
        print(f"  {k:15s} n={n:3d} recall={tp/n if n else float('nan'):.2f} predicted={npred:3d} precision={tp/npred if npred else float('nan'):.2f}")
    print("  confusion (rows=truth, cols=pred):")
    ks = sorted(set(y) | set(pr)); print("   " + " ".join(f"{k[:6]:>7s}" for k in ks))
    for t in ks: print(f"  {t[:6]:6s}" + " ".join(f"{sum(a==t and b==c for a,b in zip(y,pr)):7d}" for c in ks))
# ---- end to end: Laya kind -> policy -> model class, vs actual choice ----
print("\n=== END TO END: does policy(Laya kind) predict the model that was actually chosen? ===")
allrows = list(rows.values())
def best_policy(train, keyf):  # majority class per group
    g = collections.defaultdict(collections.Counter)
    for x in train: g[keyf(x)][cls(x)] += 1
    return {k: c.most_common(1)[0][0] for k, c in g.items()}
def e2e(key):
    inp, v, order = key.split("|"); preds = {p["id"]: p["pred"] for p in res[key]}
    ids = list(preds); ok_laya = ok_oracle = ok_const = 0
    for i in ids:                      # leave-one-out policy so the policy never sees the row it is scored on
        train = [rows[j] for j in ids if j != i]
        pol_l = best_policy([dict(rows[j], k2=preds[j]) for j in ids if j != i], lambda x: x["k2"])
        pol_o = best_policy(train, lambda x: truth(x, v))
        ok_laya += pol_l.get(preds[i], "sonnet") == cls(rows[i])
        ok_oracle += pol_o.get(truth(rows[i], v), "sonnet") == cls(rows[i])
        ok_const += cls(rows[i]) == "sonnet"
    n = len(ids); return n, ok_const/n, ok_oracle/n, ok_laya/n
for key in res:
    n, c, o, l = e2e(key); print(f"{key:28s} n={n:3d} always-Sonnet={c:.3f}  perfect-classifier={o:.3f}  Laya={l:.3f}  (Laya - constant = {100*(l-c):+.1f} pts)")
