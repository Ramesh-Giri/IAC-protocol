"""Is the +2.2pt ceiling (perfect kind classifier, best fixed policy) distinguishable from 'always Sonnet' at n=230? Paired bootstrap on per-seat LOO outcomes."""
import json, collections, random
rows = [x for x in json.load(open("dataset.json")) if not x["standing"]]
def cls(x): return "codex" if x["runtime"].startswith("codex") else ("opus" if "opus" in x["model"] else "sonnet")
for x in rows: x["cls"] = cls(x)
def loo_hits(keyf):
    h = []
    for i, x in enumerate(rows):
        c = collections.Counter(y["cls"] for j, y in enumerate(rows) if j != i and keyf(y) == keyf(x))
        h.append(int((c.most_common(1)[0][0] if c else "sonnet") == x["cls"]))
    return h
const = [int(x["cls"] == "sonnet") for x in rows]
for name, keyf in (("kind", lambda x: x["kind"]), ("kind+date", lambda x: (x["kind"], x["date"])), ("project", lambda x: x["project"])):
    h = loo_hits(keyf); d = [a - b for a, b in zip(h, const)]
    rnd = random.Random(0); bs = sorted(sum(d[rnd.randrange(len(d))] for _ in d) / len(d) for _ in range(5000))
    print(f"{name:10s} acc={sum(h)/len(h):.3f} diff_vs_constant={sum(d)/len(d)*100:+.1f}pts  95% CI [{bs[125]*100:+.1f}, {bs[4874]*100:+.1f}]")
# the same with Opus-vs-not only (the expensive-model decision) and codex-vs-not (the budget decision)
for target in ("opus", "codex"):
    y = [x["cls"] == target for x in rows]; n = sum(y)
    print(f"{target}: {n} seats = {n/len(y):.1%}; predicting 'never {target}' is right {1-n/len(y):.1%} of the time")
# what fraction of post-0922 seats are anything but Sonnet?
late = [x for x in rows if x["date"] >= "2026-09-22"]
print("since 2026-09-22:", len(late), "seats,", sum(x["cls"] != "sonnet" for x in late), "non-Sonnet")
