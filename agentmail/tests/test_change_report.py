"""change-report: facts come from a real throwaway git repo, so the parser is
checked against git's own diff output, not a hand-written diff."""
from importlib.machinery import SourceFileLoader
from pathlib import Path
import subprocess
import tempfile
import unittest

BASE = Path(__file__).resolve().parents[1]
cr = SourceFileLoader("change_report", str(BASE / "bin" / "change-report")).load_module()


def sh(repo, *args):
    subprocess.run(["git", "-C", repo, *args], check=True, capture_output=True)


class ChangeReportTest(unittest.TestCase):
    def test_symbols_and_sections(self):
        with tempfile.TemporaryDirectory() as repo:
            sh(repo, "init", "-q")
            sh(repo, "config", "user.email", "t@example.com")
            sh(repo, "config", "user.name", "t")
            src = Path(repo, "lib/pay.dart")
            src.parent.mkdir()
            src.write_text("class Pay {\n  Future<void> send({\n    required int amount,\n  }) async {\n    print(1);\n  }\n}\n")
            Path(repo, "old.py").write_text("def gone():\n    pass\n")
            sh(repo, "add", "-A"); sh(repo, "commit", "-qm", "base")
            src.write_text("class Pay {\n  Future<void> send({\n    required int amount,\n  }) async {\n    print(2);\n  }\n\n  int fee() => 1;\n}\n")
            Path(repo, "old.py").unlink()
            t = Path(repo, "test/pay_test.dart")
            t.parent.mkdir()
            t.write_text("void main() {\n  test('fee is one', () {\n    expect(1, 1);\n  });\n}\n")
            Path(repo, "pubspec.yaml").write_text("dependencies:\n  web3dart: ^3.0.3\n")
            sh(repo, "add", "-A"); sh(repo, "commit", "-qm", "change")

            class A: pass
            a = A(); a.repo, a.base, a.head, a.task, a.narrative = repo, "HEAD~1", "HEAD", "t", None
            out = cr.build(a)

        self.assertIn("Added: `fee()`", out)          # new method
        self.assertIn("Changed: `send()`", out)       # multi-line signature, body edit
        self.assertIn("Removed: `gone()`", out)       # deleted file keeps its name
        self.assertIn("fee is one", out)              # test case named
        self.assertIn("**Payments / money**", out)    # sensitive path flagged
        self.assertIn("+  web3dart: ^3.0.3", out)     # dependency diff shown
        self.assertIn("TODO(author)", out)            # narrative left for the author


if __name__ == "__main__":
    unittest.main()
