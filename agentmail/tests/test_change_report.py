"""change-report: facts come from a real throwaway git repo, so the parser is
checked against git's own diff output, not a hand-written diff."""
from importlib.machinery import SourceFileLoader
from pathlib import Path
import subprocess
import sys
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

    def test_working_tree_report_preserves_index_and_includes_new_files(self):
        with tempfile.TemporaryDirectory() as repo:
            sh(repo, "init", "-q")
            sh(repo, "config", "user.email", "fixture@example.invalid")
            sh(repo, "config", "user.name", "Report fixture")
            Path(repo, "old.py").write_text("def existing():\n    return 1\n")
            sh(repo, "add", "old.py")
            sh(repo, "commit", "-qm", "base")
            Path(repo, "old.py").write_text("def existing():\n    return 2\n")
            Path(repo, "new.py").write_text("def added():\n    return 3\n")
            Path(repo, "ignored.txt").write_text("private fixture")
            Path(repo, ".gitignore").write_text("ignored.txt\n")
            index = Path(repo, ".git/index")
            before = index.read_bytes(), index.stat().st_mtime_ns
            command = [sys.executable, str(BASE / "bin/change-report"), "HEAD",
                       "--working-tree", "--repo", repo, "--task", "sample"]
            out = subprocess.check_output(command, text=True)
            self.assertEqual(before, (index.read_bytes(), index.stat().st_mtime_ns))
            self.assertIn("working tree", out)
            self.assertIn("Changed: `existing()`", out)
            self.assertIn("Added: `added()`", out)
            self.assertNotIn("ignored.txt", out)
            self.assertIn("0 commits", out)


if __name__ == "__main__":
    unittest.main()
