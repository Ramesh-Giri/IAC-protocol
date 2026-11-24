"""Contract checks for optional context and the required security baseline.

These validate shipped skeletons and examples, not an LLM's interview or synthesis.
No live user project, private mail or agent runtime is used.
"""
from pathlib import Path
import re
import unittest


BASE = Path(__file__).resolve().parents[1]
TEMPLATES = BASE / "templates" / "project-context"
WEB_EXAMPLE = BASE / "examples" / "web"
OPTIONAL_CONTEXT = {
    "project-overview.md",
    "architecture-context.md",
    "code-standards.md",
    "ui-context.md",
    "ai-workflow-rules.md",
    "progress-tracker.md",
}
BASELINE = "security-privacy-baseline.md"
EXPECTED = OPTIONAL_CONTEXT | {BASELINE}
TOKEN = re.compile(r"\{\{[A-Z][A-Z0-9_]*\}\}")


class ContextTemplates(unittest.TestCase):
    def test_six_optional_templates_and_required_baseline(self):
        self.assertEqual({p.name for p in TEMPLATES.iterdir()}, EXPECTED)

    def test_each_template_has_project_identity_and_section_structure(self):
        for name in EXPECTED:
            with self.subTest(name=name):
                text = (TEMPLATES / name).read_text(encoding="utf-8")
                self.assertTrue(text.startswith("# {{PROJECT_NAME}} "))
                self.assertGreaterEqual(len(re.findall(r"^## ", text, re.M)), 5)
                self.assertTrue(text.endswith("\n"))

    def test_template_slots_are_well_formed_and_replaceable(self):
        for name in EXPECTED:
            with self.subTest(name=name):
                text = (TEMPLATES / name).read_text(encoding="utf-8")
                slots = TOKEN.findall(text)
                self.assertGreaterEqual(len(slots), 3)
                filled = TOKEN.sub("Project-specific content supplied by the setup agent", text)
                self.assertNotIn("{{", filled)
                self.assertNotIn("}}", filled)

    def test_optional_workflow_routes_to_other_optional_context_files(self):
        text = (TEMPLATES / "ai-workflow-rules.md").read_text(encoding="utf-8")
        references = set(re.findall(r"`([a-z-]+\.md)`", text))
        self.assertEqual(references, OPTIONAL_CONTEXT - {"ai-workflow-rules.md"})

    def test_onboarding_links_to_the_context_procedure(self):
        for path in (BASE.parent / "README.md", BASE / "README.md", BASE / "SETUP_PROMPT.md"):
            with self.subTest(path=path.name):
                text = path.read_text(encoding="utf-8")
                links = re.findall(r"\]\(([^)]+PROJECT_CONTEXT\.md|PROJECT_CONTEXT\.md)\)", text)
                self.assertTrue(links)
                for link in links:
                    self.assertEqual((path.parent / link).resolve(), (BASE / "PROJECT_CONTEXT.md").resolve())

    def test_context_guide_lists_every_output_and_links_existing_assets(self):
        guide = BASE / "PROJECT_CONTEXT.md"
        text = guide.read_text(encoding="utf-8")
        self.assertTrue(EXPECTED <= set(re.findall(r"`([a-z-]+\.md)`", text)))
        for target in re.findall(r"\]\(([^)]+)\)", text):
            if not target.startswith(("https:", "http:", "#")):
                with self.subTest(target=target):
                    self.assertTrue((guide.parent / target.split("#", 1)[0]).exists())

    def test_web_example_has_exactly_six_labeled_filled_documents(self):
        context = WEB_EXAMPLE / "context"
        self.assertEqual({p.name for p in context.iterdir()}, OPTIONAL_CONTEXT)
        for name in OPTIONAL_CONTEXT:
            with self.subTest(name=name):
                text = (context / name).read_text(encoding="utf-8")
                self.assertIn("Web-project example only.", text)
                self.assertIn("[the example guide](../README.md)", text)
                self.assertNotIn("{{", text)
                self.assertTrue(text.endswith("\n"))

    def test_web_example_guide_links_all_six_files_and_existing_assets(self):
        text = (WEB_EXAMPLE / "README.md").read_text(encoding="utf-8")
        links = re.findall(r"\]\(([^)]+)\)", text)
        self.assertTrue({f"context/{name}" for name in OPTIONAL_CONTEXT} <= set(links))
        for target in links:
            with self.subTest(target=target):
                self.assertTrue((WEB_EXAMPLE / target).exists())

    def test_web_example_does_not_claim_implementation_is_complete(self):
        text = (WEB_EXAMPLE / "context" / "progress-tracker.md").read_text(encoding="utf-8")
        self.assertIn("Implementation **not started**", text)
        self.assertIn("No application work completed.", text)
        self.assertIn("Verification to perform, not yet run", text)

    def test_baseline_has_complete_unverified_fillable_checklists(self):
        text = (TEMPLATES / BASELINE).read_text(encoding="utf-8")
        rows = re.findall(r"^\| (PR\d{1,2}|[PRWMO]\d{2}) [^\n]+", text, re.M)
        expected = {f"{prefix}{n:02}" for prefix, count in
                    (("P", 26), ("R", 20), ("W", 12), ("M", 4), ("O", 4))
                    for n in range(1, count + 1)}
        expected |= {f"PR{n}" for n in range(1, 11)}
        self.assertEqual(set(rows), expected)
        self.assertEqual(len(rows), len(expected))
        for line in text.splitlines():
            if re.match(r"^\| (?:PR\d{1,2}|[PRWMO]\d{2}) ", line):
                with self.subTest(row=line.split(" ", 2)[1]):
                    cells = [cell.strip() for cell in line.strip("|").split("|")]
                    self.assertEqual(len(cells), 5)
                    self.assertEqual(cells[1], "Unrated")
                    self.assertEqual(cells[2], "FAIL - not verified")
                    self.assertTrue(cells[3])
                    self.assertEqual(cells[4], "Assign")

    def test_production_readiness_pass_conditions_match_skill_and_template(self):
        template = (TEMPLATES / BASELINE).read_text()
        skill = (BASE / "skills" / "security-privacy-baseline" / "SKILL.md").read_text()
        template_rows = re.findall(r"^\| PR\d{1,2} .*", template, re.M)
        skill_rows = re.findall(r"^\| PR\d{1,2} .*", skill, re.M)
        self.assertEqual(len(template_rows), 10)
        self.assertEqual(skill_rows, template_rows)
        for n, row in enumerate(template_rows, 1):
            with self.subTest(item=n):
                self.assertTrue(row.startswith(f"| PR{n} "))
                self.assertIn("PASS if", row)
        for path in (TEMPLATES / BASELINE,
                     BASE / "skills" / "security-privacy-baseline" / "SKILL.md",
                     BASE / "PROJECT_CONTEXT.md", BASE / "SETUP_PROMPT.md",
                     BASE / "OPERATIONAL_RULES.md"):
            with self.subTest(path=str(path)):
                self.assertIn("who can deploy each service", path.read_text())

    def test_baseline_is_wired_into_setup_and_release_policy(self):
        skill = BASE / "skills" / "security-privacy-baseline" / "SKILL.md"
        self.assertTrue(skill.read_text().startswith("---\nname: security-privacy-baseline\n"))
        for path in (BASE / "PROJECT_CONTEXT.md", BASE / "SETUP_PROMPT.md"):
            with self.subTest(path=path.name):
                text = path.read_text()
                self.assertIn(BASELINE, text)
                self.assertIn("even when", text)
        rules = (BASE / "OPERATIONAL_RULES.md").read_text()
        self.assertEqual(len(re.findall(r"^## 64\.", rules, re.M)), 1)
        rule = rules.split("## 64.", 1)[1]
        self.assertIn("Ramesh", rule)
        self.assertIn("reason and expiry", rule)
        self.assertIn("blocks launch", rule)
        index = (BASE / "skills" / "README.md").read_text()
        self.assertIn("(security-privacy-baseline/SKILL.md)", index)
        for name in ("web-dast-scan", "mobile-app-scan", "waf-fit"):
            with self.subTest(skill=name):
                text = (BASE / "skills" / name / "SKILL.md").read_text()
                self.assertIn("../security-privacy-baseline/SKILL.md", text)

    def test_baseline_skill_and_template_relative_links_resolve(self):
        paths = (TEMPLATES / BASELINE,
                 BASE / "skills" / "security-privacy-baseline" / "SKILL.md")
        for path in paths:
            for target in re.findall(r"\]\(([^)]+)\)", path.read_text()):
                if not target.startswith(("https:", "http:", "#")):
                    with self.subTest(path=path.name, target=target):
                        self.assertTrue((path.parent / target.split("#", 1)[0]).exists())


if __name__ == "__main__":
    unittest.main()
