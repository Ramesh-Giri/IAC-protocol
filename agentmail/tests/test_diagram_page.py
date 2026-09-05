"""Static page asset/markup tests; these do not perform browser visual QA."""
from html.parser import HTMLParser
from pathlib import Path
import runpy
import shutil
import tempfile
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1] / "diagram"


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elements = []

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))


class DiagramPage(unittest.TestCase):
    def test_tab_relationships_and_no_script_fallback(self):
        parser = PageParser()
        parser.feed((ROOT / "index.html").read_text())
        elements = parser.elements
        tabs = [a for _, a in elements if a.get("role") == "tab"]
        panels = {a["id"]: a for _, a in elements if a.get("role") == "tabpanel"}
        self.assertEqual(len(tabs), 2)
        self.assertEqual(len(panels), 2)
        for tab in tabs:
            panel = panels[tab["aria-controls"]]
            self.assertEqual(panel["aria-labelledby"], tab["id"])
            self.assertNotIn("hidden", panel)  # readable if JS is unavailable
        tablist = next(a for _, a in elements if a.get("role") == "tablist")
        self.assertIn("hidden", tablist)  # revealed only after listeners are ready
        for tag, attributes in elements:
            if tag in {"img", "script"}:
                self.assertTrue((ROOT / attributes["src"]).is_file())
            if tag == "img":
                self.assertTrue(attributes.get("alt"))
            if tag == "link" and attributes.get("rel") == "stylesheet":
                self.assertTrue((ROOT / attributes["href"]).is_file())

    def test_svgs_are_well_formed_with_accessible_titles_and_no_remote_assets(self):
        ns = {"svg": "http://www.w3.org/2000/svg"}
        for name in ("simple.svg", "complex.svg"):
            with self.subTest(name=name):
                root = ET.parse(ROOT / name).getroot()
                self.assertIsNotNone(root.find("svg:title", ns))
                self.assertIsNotNone(root.find("svg:desc", ns))
                self.assertFalse(root.findall(".//svg:script", ns))
                self.assertFalse(root.findall(".//svg:image", ns))
                self.assertIn("viewBox", root.attrib)

    def test_build_only_copies_public_browser_assets(self):
        with tempfile.TemporaryDirectory(prefix="iac-diagram-test-") as tmp:
            project = Path(tmp)
            for name in ("index.html", "styles.css", "switch.js", "simple.svg", "complex.svg", "build.py"):
                shutil.copyfile(ROOT / name, project / name)
            (project / "private.txt").write_text("Not a browser asset")
            build = runpy.run_path(str(project / "build.py"))["build"]
            build()
            self.assertEqual({p.name for p in (project / "dist").iterdir()},
                             {"index.html", "styles.css", "switch.js", "simple.svg", "complex.svg"})
            build()  # repeatable without collecting unrelated source files
            (project / "dist" / "unexpected.txt").write_text("Inspect before packaging")
            with self.assertRaises(ValueError):
                build()


if __name__ == "__main__":
    unittest.main()
