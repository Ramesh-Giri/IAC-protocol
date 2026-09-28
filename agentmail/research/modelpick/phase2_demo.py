"""Phase 2 demo: run model_guard.resolve() over a handful of realistic task shapes, using
TODAY's real local catalogues (loaded via catalog-check's own loaders, not duplicated), and
write the decisions to an append-only JSONL log the overseer can inspect directly -- same
spirit as phase 1's catalogue_check_output.txt.

Run: python3 agentmail/research/modelpick/phase2_demo.py
"""
import importlib.util
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "lib"))
import model_guard as mg  # noqa: E402

# catalog-check has no .py extension (it's an executable, per agentmail/bin conventions) --
# load it as a module rather than re-implementing its cache readers. Explicit loader
# because spec_from_file_location can't infer one from an extension-less path.
_cc_path = str(HERE.parent.parent / "bin" / "catalog-check")
spec = importlib.util.spec_from_file_location("catalog_check", _cc_path, loader=SourceFileLoader("catalog_check", _cc_path))
catalog_check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalog_check)

codex_ids, codex_note = catalog_check.load_codex()
claude_ids, claude_note = catalog_check.load_claude()
VERIFIED = {"codex-cli": codex_ids or set(), "claude-code": claude_ids or set()}
print(f"codex catalog: {codex_note}")
print(f"claude catalog: {claude_note}\n")

ALL_CANDIDATES = [
    mg.Candidate("claude-code", "claude-opus-5"),
    mg.Candidate("claude-code", "claude-sonnet-5"),
    mg.Candidate("claude-code", "claude-haiku-4-5-20251001"),
    mg.Candidate("claude-code", "claude-fable-5-1"),
    mg.Candidate("codex-cli", "gpt-6-astra"),
    mg.Candidate("codex-cli", "gpt-5.6-terra"),
    mg.Candidate("codex-cli", "gpt-5.3-codex-spark"),  # the known-dead id, on purpose
]

SCENARIOS = [
    dict(task_id="demo-final-review", task_kind="review",
         task_text="Independent read-only pre-deploy review of feature/chat-tasks security + UI (Claude, Codex saved)."),
    dict(task_id="demo-sec-audit", task_kind="security_audit",
         task_text="Full Cloudflare security-audit skill run, backend + rules, report only."),
    dict(task_id="demo-plain-feature", task_kind="feature",
         task_text="Add a FAB to the composer and wire it to the new note flow."),
    dict(task_id="demo-host-tool", task_kind="feature",
         task_text="Run the flutter emulator locally and confirm the fix.", host_tool_required=True),
    dict(task_id="demo-pinned-overseer", task_kind=None, task_text="", pinned=True),
]

log_path = HERE / "decisions_demo.jsonl"
if log_path.exists():
    log_path.unlink()  # demo re-run should start clean; write_decision_log itself is append-only in real use

for s in SCENARIOS:
    d = mg.resolve(ALL_CANDIDATES, task_kind=s.get("task_kind"), task_text=s.get("task_text", ""),
                    host_tool_required=s.get("host_tool_required", False),
                    verified_ids=VERIFIED, pinned=s.get("pinned", False))
    final_choice = None if not d.candidates else {"runtime": d.candidates[0].runtime, "model": d.candidates[0].model}
    line = mg.write_decision_log(str(log_path), d, task_id=s["task_id"], seat=s["task_id"],
                                  task_kind=s.get("task_kind"), pinned=s.get("pinned", False),
                                  final_choice=final_choice)
    survivors = ", ".join(f"{c.runtime}:{c.model}" for c in d.candidates) or "(none)"
    print(f"{s['task_id']:24} locked={d.locked_audit!s:5} survivors=[{survivors}]")
    for r in d.reasons:
        print(f"  - {r}")
    print()

print(f"wrote {len(SCENARIOS)} lines to {log_path.relative_to(HERE.parent.parent.parent)}")
