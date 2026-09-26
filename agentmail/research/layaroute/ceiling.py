"""How predictable is the chosen model from task KIND (oracle classifier = my labels)? Upper bound on any kind-router."""
import json, collections
rows = [x for x in json.load(open("dataset.json")) if not x["standing"]]
def cls(x): return "codex" if x["runtime"].startswith("codex") else ("opus" if "opus" in x["model"] else "sonnet")
for x in rows: x["cls"] = cls(x)
print("N task seats", len(rows), dict(collections.Counter(x["cls"] for x in rows)))
print("always-Sonnet acc: %.3f" % (sum(x["cls"]=="sonnet" for x in rows)/len(rows)))
print("\nkind x model-class")
kinds = sorted({x["kind"] for x in rows}, key=lambda k: -sum(x["kind"]==k for x in rows))
print("%-16s %4s %6s %6s %6s" % ("kind","n","sonnet","opus","codex"))
for k in kinds:
    s = [x for x in rows if x["kind"]==k]; c = collections.Counter(x["cls"] for x in s)
    print("%-16s %4d %6d %6d %6d" % (k, len(s), c["sonnet"], c["opus"], c["codex"]))
def loo(keyf):
    ok = 0
    for i, x in enumerate(rows):
        c = collections.Counter(y["cls"] for j, y in enumerate(rows) if j != i and keyf(y) == keyf(x))
        pred = c.most_common(1)[0][0] if c else "sonnet"
        ok += pred == x["cls"]
    return ok / len(rows)
print("\nLeave-one-out accuracy of 'majority model-class within group' (a ceiling for a PERFECT classifier + best fixed policy):")
print(" kind only            %.3f" % loo(lambda x: x["kind"]))
print(" project only         %.3f" % loo(lambda x: x["project"]))
print(" kind+project         %.3f" % loo(lambda x: (x["kind"], x["project"])))
print(" date only            %.3f" % loo(lambda x: x["date"]))
print(" kind+date            %.3f" % loo(lambda x: (x["kind"], x["date"])))
print(" review-vs-not        %.3f" % loo(lambda x: x["kind"]=="review"))
print("\nmodel class by date")
for d in sorted({x["date"] for x in rows}):
    s = [x for x in rows if x["date"]==d]; c = collections.Counter(x["cls"] for x in s)
    print(" ", d, len(s), dict(c))
print("\ntext leakage: descriptions containing 'Codex' -> class")
print(collections.Counter(x["cls"] for x in rows if "codex" in x["desc"].lower()))
print("Codex-class seats whose text does NOT say codex:", [x["id"] for x in rows if x["cls"]=="codex" and "codex" not in x["desc"].lower() and "codex" not in x["id"]])
print("\nopus seats:"); [print(" ", x["id"], x["kind"], x["date"]) for x in rows if x["cls"]=="opus"]
print("\nsonnet seats of kind review (same kind as opus reviews):", sum(1 for x in rows if x["kind"]=="review" and x["cls"]=="sonnet"))
