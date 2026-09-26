"""Label every roster seat with a TASK KIND from its description text ALONE (never the model).
These labels are the author's judgement (research-layaroute-0926-ramesh), rule-assisted then hand-reviewed.
Order matters: first match wins."""
import json, re, sys, collections
ROSTER = "~/Work/Aureus/.agent-mail/roster.json"
SKIP0 = {"overseer-ramesh", "codex-ramesh", "research-layaroute-0926-ramesh"}   # + STANDING below
SKIP = SKIP0
STANDING = {"circle-ramesh","app-ramesh","connect-sdk-ramesh","project-b-ramesh","apu-ramesh","aia-ramesh"}  # long-lived per-PROJECT seats, not tasks   # not routed / advisory / this seat
RULES = [
 ("security_audit", r"(?i:security audit|security test|security review|pen ?test|supply-chain audit|phase 5 verifier|security-audit|Deep security test|Defensive security|Pre-go-live security)"),
 ("review",         r"\breview\b|re-review|reviewer|\bReview\b"),
 ("fix_findings",   r"^Fix .*(BLOCK|review)|BLOCK|Close (the )?(two )?(rules )?review|Close narrow|Fix review findings|Fix chips review|Fix final-review|Fix re-review|fix of .*BLOCK|Codex fix|Codex: fix"),
 ("plan_research",  r"^PLAN ONLY|Read-only (plan|design|study)|Design doc only|research|^Web/open-source|design:|APU Level 3 design|Investigation and report|Measure how often|Laya viability|Design \+ measure|Tune Laya|Triage|Codex Spark read-only plan|Read-only plan"),
 ("integrate",      r"^Integrate|Integrate |^Merge|Land |merge the four|Fast-forward|Build release|Run every non-cloud|Write the CORRECT deploy|Fresh integrator|Fresh integrat|Integrate security|fast-forward"),
 ("security_fix",   r"security fix|Hedera|KYC|KYB|hardening|Defence in depth|rate limit|leak|forge|anonymous|private key|secret|self-grant|read rule|rules (fix|security)|Firestore|rules,|Wave [12]|Wave 2b|Finding A|Users exposure|M6:|Client auth|Functions security"),
 ("bugfix",         r"^Fix|LIVE BUG|URGENT|incident|fails|hangs|Debug|regression|refused|not being applied|renders|overlaps|race fix|Voice recording|crash|make two notes|made two notes|slow delete"),
 ("ui",             r"\bM3\b|Material|[Ll]ayout|FAB|\bmic\b|composer|status bar|theme|dock|chip|bubble|drawer|focus ring|\bUI\b|pixel|density|banner|arrow|Hamburger|logo|tooltip|Outline panel|send-button|hints card|panel|splash"),
]
OVERRIDE = {
 **{k: "fix_findings" for k in ["app-sec-fix2-ramesh","app-sec-fix3-ramesh","app-notes-fix-ramesh","app-nest-fix2-ramesh","app-rules-fix2-ramesh",
    "app-backend-fix2-ramesh","app-legalfix-ramesh","app-chipfix-ramesh"]},
 "app-sec-rules-ramesh":"security_fix","app-security-fix-0919-ramesh":"security_fix","circle-sectors-ramesh":"ui","circle-brand-ramesh":"ui",
 "circle-recovery-ramesh":"bugfix","app-apu-inapp-0921-ramesh":"feature",  # hand corrections where the regex misfires (reviewed by reading each row)
 **{k: "feature" for k in ["app-chat-backend-ramesh","app-apu-l2-build-0922-ramesh","app-apu-anon-0924-ramesh","circle-apuguest-0925-ramesh",
    "app-voiceanon-0925-ramesh","app-cleanup-ramesh","app-webbooking-ramesh","app-chat-app-ramesh","app-apu-initmsg-0924-ramesh",
    "app-apudrawer-0925-ramesh","circle-apu-native-0924-ramesh","app-detector-trace-0924-ramesh","app-kyb-app-ramesh","app-kyb-backend-ramesh"]},
 "app-quality-sweep-0921-ramesh": "bugfix", "app-recall-run-0924-ramesh": "plan_research", "app-apu-device-0921-ramesh": "plan_research",
}
def kind(k, d):
    if k in OVERRIDE: return OVERRIDE[k]
    for name, rx in RULES:
        if re.search(rx, d): return name
    return "feature"
if __name__ == "__main__":
    r = json.load(open(ROSTER))["agents"]
    c = collections.defaultdict(list)
    for k, a in r.items():
        if k in SKIP: continue
        c[kind(k, a["description"])].append((k, a["description"][:110]))
    for n, v in sorted(c.items(), key=lambda x: -len(x[1])):
        print("==", n, len(v))
        if n in (None,) or "-v" in sys.argv:
            for x in v: print("  ", x[0], "|", x[1])
