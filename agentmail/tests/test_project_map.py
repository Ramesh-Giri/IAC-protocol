"""project-map: purposes come from header comments (tooling noise ignored),
links resolve package and relative imports, undocumented files stay visible."""
from importlib.machinery import SourceFileLoader
from pathlib import Path
import subprocess
import tempfile
import unittest

BASE = Path(__file__).resolve().parents[1]
pm = SourceFileLoader("project_map", str(BASE / "bin" / "project-map")).load_module()


class ProjectMapTest(unittest.TestCase):
    def test_map(self):
        with tempfile.TemporaryDirectory() as repo:
            subprocess.run(["git", "-C", repo, "init", "-q"], check=True)
            r = Path(repo)
            (r / "pubspec.yaml").write_text("name: demo\n")
            (r / "lib/pay").mkdir(parents=True)
            (r / "lib/pay/README.md").write_text("# Payments\n")
            (r / "lib/pay/send.dart").write_text("/// Sends a payment. Second sentence.\nlibrary;\nimport 'package:demo/pay/fee.dart';\n")
            (r / "lib/pay/fee.dart").write_text("// ignore_for_file: lint\nint fee() => 1;\n")
            (r / "functions/src").mkdir(parents=True)
            (r / "functions/src/a.ts").write_text("/** Handler A. */\nimport { b } from './b';\n")
            (r / "functions/src/b.ts").write_text("export const b = 1;\n")
            subprocess.run(["git", "-C", repo, "add", "-A"], check=True)
            files, purpose, links, used_by = pm.build(repo, ["lib", "functions/src"])
            md = pm.render(repo, files, purpose, links, used_by)

        self.assertEqual(purpose["lib/pay/send.dart"], "Sends a payment.")
        self.assertIsNone(purpose["lib/pay/fee.dart"])              # tooling line is not documentation
        self.assertEqual(links["lib/pay/send.dart"], {"lib/pay/fee.dart"})
        self.assertEqual(links["functions/src/a.ts"], {"functions/src/b.ts"})
        self.assertIn("Coverage: 2 of 4", md)
        self.assertIn("`fee.dart` — _undocumented_", md)
        self.assertIn("**pay/** — Payments", md)


if __name__ == "__main__":
    unittest.main()
