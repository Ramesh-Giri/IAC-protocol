"""Offline checks for team-onboarding assets and the fork's privacy boundary.

These test documentation links, example data and real Git ignore behavior.
They do not simulate an agent interview, host access or remote onboarding.
"""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest


BASE = Path(__file__).resolve().parents[1]


class TeamSetup(unittest.TestCase):
    def test_connection_example_is_data_only_and_not_a_real_team(self):
        data = json.loads((BASE / "templates" / "iac-team.example.json").read_text())
        self.assertEqual(set(data), {"version", "mail_repository"})
        self.assertIs(type(data["version"]), int)
        self.assertEqual(data["version"], 1)
        self.assertEqual(data["mail_repository"],
                         "git@github.com:YOUR_ORG/YOUR_PRIVATE_MAIL_REPO.git")

    def test_entrypoints_route_to_team_setup(self):
        for path in (BASE.parent / "README.md", BASE / "README.md",
                     BASE / "SETUP_PROMPT.md", BASE / "FEDERATION.md"):
            with self.subTest(path=path):
                targets = re.findall(r"\]\(([^)]+)\)", path.read_text())
                resolved = {(path.parent / t).resolve() for t in targets
                            if t.endswith("TEAM_SETUP.md")}
                self.assertIn((BASE / "TEAM_SETUP.md").resolve(), resolved)

    def test_team_guide_links_exist_and_example_matches(self):
        guide = BASE / "TEAM_SETUP.md"
        text = guide.read_text()
        for target in re.findall(r"\]\(([^)]+)\)", text):
            with self.subTest(target=target):
                self.assertTrue((guide.parent / target).exists())
        blocks = re.findall(r"```json\n(.*?)\n```", text, re.S)
        self.assertEqual(len(blocks), 1)
        self.assertEqual(json.loads(blocks[0]),
                         json.loads((BASE / "templates" / "iac-team.example.json").read_text()))

    def test_fork_tracks_connection_but_neither_live_mail_channel(self):
        with tempfile.TemporaryDirectory(prefix="iac-fork-test-") as tmp:
            root = Path(tmp)
            shutil.copyfile(BASE.parent / ".gitignore", root / ".gitignore")
            env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
            env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
            subprocess.run(["git", "init", "-q", str(root)], env=env,
                           check=True, capture_output=True, timeout=10)
            for name, ignored in {
                "iac-team.json": False,
                "agentmail/templates/iac-team.example.json": False,
                ".team-mail/roster.json": True,
                ".team-mail/overseer-local/new/private.md": True,
                ".team-mail/local.json": True,
                ".agent-mail/overseer-local/new/private.md": True,
                "frontend/source.ts": True,
            }.items():
                with self.subTest(name=name):
                    result = subprocess.run(
                        ["git", "-C", str(root), "check-ignore", "--no-index", "-q", name],
                        env=env, capture_output=True, timeout=10)
                    self.assertEqual(result.returncode, 0 if ignored else 1, result.stderr)


if __name__ == "__main__":
    unittest.main()
