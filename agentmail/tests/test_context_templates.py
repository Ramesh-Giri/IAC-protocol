"""Contract checks for the optional agent-authored context assets.

These validate shipped skeletons and examples, not an LLM's interview or synthesis.
No live user project, private mail or agent runtime is used.
"""
from pathlib import Path
import re
import unittest


BASE = Path(__file__).resolve().parents[1]
TEMPLATES = BASE / "templates" / "project-context"
WEB_EXAMPLE = BASE / "examples" / "web"
EXPECTED = {
    "project-overview.md",
    "architecture-context.md",
    "code-standards.md",
    "ui-context.md",
    "ai-workflow-rules.md",
    "progress-tracker.md",
}
TOKEN = re.compile(r"\{\{[A-Z][A-Z0-9_]*\}\}")


class ContextTemplates(unittest.TestCase):
    def test_exactly_six_named_files(self):
        self.assertEqual({p.name for p in TEMPLATES.iterdir()}, EXPECTED)

    def test_each_template_has_project_identity_and_section_structure(self):
        for name in EXPECTED:
            with self.subTest(name=name):
                text = (TEMPLATES / name).read_text(encoding="utf-8")
                self.assertTrue(text.startswith("# {{PROJECT_NAME}} — "))
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

    def test_workflow_routes_to_every_other_context_file(self):
        text = (TEMPLATES / "ai-workflow-rules.md").read_text(encoding="utf-8")
        references = set(re.findall(r"`([a-z-]+\.md)`", text))
        self.assertEqual(references, EXPECTED - {"ai-workflow-rules.md"})

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
                    self.assertTrue((guide.parent / target).exists())

    def test_web_example_has_exactly_six_labeled_filled_documents(self):
        context = WEB_EXAMPLE / "context"
        self.assertEqual({p.name for p in context.iterdir()}, EXPECTED)
        for name in EXPECTED:
            with self.subTest(name=name):
                text = (context / name).read_text(encoding="utf-8")
                self.assertIn("Web-project example only.", text)
                self.assertIn("[the example guide](../README.md)", text)
                self.assertNotIn("{{", text)
                self.assertTrue(text.endswith("\n"))

    def test_web_example_guide_links_all_six_files_and_existing_assets(self):
        text = (WEB_EXAMPLE / "README.md").read_text(encoding="utf-8")
        links = re.findall(r"\]\(([^)]+)\)", text)
        self.assertTrue({f"context/{name}" for name in EXPECTED} <= set(links))
        for target in links:
            with self.subTest(target=target):
                self.assertTrue((WEB_EXAMPLE / target).exists())

    def test_web_example_does_not_claim_implementation_is_complete(self):
        text = (WEB_EXAMPLE / "context" / "progress-tracker.md").read_text(encoding="utf-8")
        self.assertIn("Implementation **not started**", text)
        self.assertIn("No application work completed.", text)
        self.assertIn("Verification to perform, not yet run", text)


if __name__ == "__main__":
    unittest.main()
