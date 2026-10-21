"""Offline bootstrap preservation checks using mocks and disposable local Git repos.

Developers run this file to verify checkout safety without network access.
Writes only temporary fixtures, never operational checkouts.
"""
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
from unittest.mock import patch

loader = importlib.machinery.SourceFileLoader("bootstrap", str(Path(__file__).with_name("iac-bootstrap")))
spec = importlib.util.spec_from_loader(loader.name, loader)
bootstrap = importlib.util.module_from_spec(spec)
loader.exec_module(bootstrap)


def check_dry_run_index():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory).resolve()
        target = root / "app"
        target.mkdir()
        def fixture_git(*args):
            return subprocess.run(["git", *args], cwd=target, check=True, capture_output=True)
        fixture_git("init", "-b", "development")
        fixture_git("config", "user.name", "Fixture")
        fixture_git("config", "user.email", "fixture@example.invalid")
        fixture_git("config", "core.fsmonitor", "false")
        fixture_git("config", "core.ignorestat", "false")
        fixture_git("remote", "add", "origin", "https://github.com/team/app.git")
        tracked = target / "tracked.txt"
        tracked.write_text("unchanged content\n")
        fixture_git("add", "tracked.txt")
        fixture_git("commit", "-m", "fixture")
        fixture_git("status", "--porcelain")
        stat = tracked.stat()
        os.utime(tracked, ns=(stat.st_atime_ns, stat.st_mtime_ns - 10_000_000_000))
        index = target / ".git/index"
        before = (index.read_bytes(), index.stat().st_mtime_ns)
        project = {"folder": "app", "remote": "https://github.com/team/app.git", "working_branch": "development"}
        (root / "projects.local.json").write_text(json.dumps({"version": 1, "projects": [project]}))
        result = subprocess.run([str(Path(bootstrap.__file__).resolve()), "--root", str(root), "--dry-run"],
                                capture_output=True, text=True)
        assert result.returncode == 0 and "would_update" in result.stdout, result.stdout + result.stderr
        assert before == (index.read_bytes(), index.stat().st_mtime_ns), "dry-run refreshed Git index"


def check_manual_manifest():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        manifest = root / "projects.local.json"
        project = {"folder": "app", "remote": "https://github.com/team/app.git", "working_branch": "development", "bootstrap": False}
        for note in (None, "", "   ", 123, [], {}):
            record = dict(project)
            if note is not None:
                record["setup_note"] = note
            manifest.write_text(json.dumps({"version": 1, "projects": [record]}))
            result = subprocess.run([str(Path(bootstrap.__file__).resolve()), "--root", str(root), "--dry-run"],
                                    capture_output=True, text=True)
            assert result.returncode == 2 and 'error: "Cannot read a valid project manifest or run Git"' in result.stdout, result.stdout + result.stderr
            assert not result.stderr, "invalid manifest must not emit a traceback"
            assert not (root / "app").exists()
        project["setup_note"] = "Follow the manual setup guide"
        manifest.write_text(json.dumps({"version": 1, "projects": [project]}))
        assert bootstrap.load_projects(manifest)["projects"] == [project]
        assert bootstrap.update_project(root, project, True) == ("manual", project["setup_note"])


def check():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory).resolve()
        project = {"folder": "app", "remote": "https://github.com/team/app.git", "working_branch": "development"}
        with patch.object(bootstrap, "git") as git:
            assert bootstrap.update_project(root, project, True)[0] == "would_clone"
            git.assert_not_called()
            assert list(root.iterdir()) == []
        target = root / "app"
        target.mkdir()
        sentinel = target / "work.txt"
        sentinel.write_text("preserve me")

        def clean_git(*args, **kwargs):
            if args[0] == "rev-parse":
                return str(target) if args[1] == "--show-toplevel" else ".git/" + args[2]
            if args[0] == "remote":
                return project["remote"]
            if args[0] == "branch":
                return "development"
            return ""

        with patch.object(bootstrap, "git", side_effect=clean_git) as git:
            assert bootstrap.update_project(root, project, True)[0] == "would_update"
            assert not any(call.args[0] in ("fetch", "merge") for call in git.call_args_list)
            assert bootstrap.update_project(root, project, False)[0] == "updated"
            assert ("merge", "--ff-only", "--no-edit", "--no-overwrite-ignore", "FETCH_HEAD") in [call.args for call in git.call_args_list]
        for reason in ("dirty", "branch", "origin", "operation"):
            def held_git(*args, **kwargs):
                if reason == "dirty" and args[0] == "status":
                    return "?? work.txt"
                if reason == "branch" and args[0] == "branch":
                    return "feature/keep"
                if reason == "origin" and args[0] == "remote":
                    return "https://github.com/other/app.git"
                return clean_git(*args, **kwargs)
            if reason == "operation":
                (target / ".git").mkdir()
                (target / ".git/MERGE_HEAD").touch()
            with patch.object(bootstrap, "git", side_effect=held_git) as git:
                assert bootstrap.update_project(root, project, False)[0] == "held", reason
                assert not any(call.args[0] in ("fetch", "merge") for call in git.call_args_list)
            assert sentinel.read_text() == "preserve me"
        linked = dict(project, folder="linked")
        (root / "linked").symlink_to(target, target_is_directory=True)
        with patch.object(bootstrap, "git") as git:
            assert bootstrap.update_project(root, linked, False)[0] == "held"
            git.assert_not_called()
        missing = dict(project, folder="missing")
        with patch.object(bootstrap, "git", side_effect=subprocess.CalledProcessError(128, "git")):
            try:
                bootstrap.update_project(root, missing, False)
            except subprocess.CalledProcessError:
                pass
            else:
                assert False, "failed clone must report failure"
        assert not (root / "missing").exists()
        assert not list(root.glob(".iac-clone-*"))
        manifest = root / "manifest.json"
        for change in ({"folder": "../escape"}, {"remote": "https://token@github.com/team/app.git"}, {"bootstrap": "false"}):
            manifest.write_text(json.dumps({"version": 1, "projects": [dict(project, **change)]}))
            try:
                bootstrap.load_projects(manifest)
            except ValueError:
                pass
            else:
                assert False, "invalid manifest must fail before mutation"
        example = {"version": 1, "example": True, "projects": [project]}
        (root / "projects.example.json").write_text(json.dumps(example))
        for arguments, code in ((["--dry-run"], 0), ([], 1)):
            with patch.object(bootstrap, "update_project") as update, patch("sys.argv", ["iac-bootstrap", "--root", str(root), *arguments]):
                assert bootstrap.main() == code
                update.assert_not_called()
        assert not (root / "projects.local.json").exists()
        inventory = {"version": 1, "projects": [project, dict(project, folder="other")]}
        with patch.object(bootstrap, "load_projects", return_value=inventory), patch.object(
            bootstrap, "update_project", side_effect=[subprocess.CalledProcessError(128, "git"), ("cloned", "main")]
        ) as update, patch("sys.argv", ["iac-bootstrap", "--root", str(root)]):
            assert bootstrap.main() == 1
            assert update.call_count == 2, "unavailable repositories must not stop remaining setup"
    print("bootstrap preservation checks passed")


if __name__ == "__main__":
    check_dry_run_index()
    check_manual_manifest()
    check()
