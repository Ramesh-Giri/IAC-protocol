"""Static checks for README disclosure markup, not Mermaid rendering tests."""
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest


README = Path(__file__).resolve().parents[2] / "README.md"


class DisclosureParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.sections = []

    def handle_starttag(self, tag, attrs):
        if tag == "details":
            self.stack.append(dict(attrs))
        elif tag == "summary":
            if not self.stack:
                raise AssertionError("summary outside details")

    def handle_endtag(self, tag):
        if tag == "details":
            self.sections.append(self.stack.pop())


class ReadmeDiagrams(unittest.TestCase):
    def test_simple_open_complex_closed_and_disclosures_balanced(self):
        text = README.read_text()
        parser = DisclosureParser()
        parser.feed(text)
        self.assertFalse(parser.stack)
        self.assertEqual(len(parser.sections), 2)
        self.assertIn("open", parser.sections[0])
        self.assertNotIn("open", parser.sections[1])
        summaries = re.findall(r"<summary>(.*?)</summary>", text)
        self.assertEqual(len(summaries), 2)
        self.assertIn("Simple", summaries[0])
        self.assertIn("Complex", summaries[1])

    def test_each_view_has_a_complete_mermaid_block_with_markdown_spacing(self):
        sections = re.findall(r"<details(?: open)?>\n(.*?)\n</details>",
                              README.read_text(), re.S)
        self.assertEqual(len(sections), 2)
        for section in sections:
            self.assertIn("</summary>\n\n```mermaid\n", section)
            diagrams = re.findall(r"```mermaid\n(.*?)\n```", section, re.S)
            self.assertEqual(len(diagrams), 1)
            self.assertTrue(diagrams[0].startswith("flowchart TD\n"))
            self.assertEqual(section.count("```"), 2)


if __name__ == "__main__":
    unittest.main()
