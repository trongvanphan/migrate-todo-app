"""Tests for merge.py — uses real git repos in tmp dirs."""

import os
import subprocess
import tempfile
import unittest

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from merge import merge, squash, sync_base, abort_merge, hard_reset


def _init_repo(tmpdir: str) -> str:
    repo = os.path.join(tmpdir, "repo")
    os.makedirs(repo)
    subprocess.run(["git", "init", repo], capture_output=True)
    subprocess.run(["git", "-C", repo, "config", "user.email", "test@test.com"], capture_output=True)
    subprocess.run(["git", "-C", repo, "config", "user.name", "Test"], capture_output=True)
    open(os.path.join(repo, "README.md"), "w").close()
    subprocess.run(["git", "-C", repo, "add", "."], capture_output=True)
    subprocess.run(["git", "-C", repo, "commit", "-m", "init"], capture_output=True)
    return repo


def _create_exec_branch(repo: str, branch: str = "spec-driven/test/exec"):
    """Create exec branch with a divergent commit."""
    subprocess.run(["git", "-C", repo, "checkout", "-b", branch], capture_output=True)
    with open(os.path.join(repo, "feature.txt"), "w") as f:
        f.write("feature code")
    subprocess.run(["git", "-C", repo, "add", "."], capture_output=True)
    subprocess.run(["git", "-C", repo, "commit", "-m", "feat: add feature [STEP-1]"], capture_output=True)
    return branch


class TestMerge(unittest.TestCase):
    def test_successful_merge(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_repo(tmp)
            exec_branch = _create_exec_branch(repo)
            result = merge(repo, exec_branch, "main", "merge: Bundle 1 — Foundation")
            self.assertEqual(result["status"], "ok")
            # Should be back on exec branch
            r = subprocess.run(
                ["git", "-C", repo, "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True, text=True,
            )
            self.assertEqual(r.stdout.strip(), exec_branch)

    def test_merge_conflict(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_repo(tmp)
            # Create conflicting changes on both branches
            exec_branch = _create_exec_branch(repo)
            subprocess.run(["git", "-C", repo, "checkout", "main"], capture_output=True)
            with open(os.path.join(repo, "feature.txt"), "w") as f:
                f.write("conflicting code")
            subprocess.run(["git", "-C", repo, "add", "."], capture_output=True)
            subprocess.run(["git", "-C", repo, "commit", "-m", "conflict"], capture_output=True)
            subprocess.run(["git", "-C", repo, "checkout", exec_branch], capture_output=True)

            result = merge(repo, exec_branch, "main", "merge: Bundle 1")
            self.assertEqual(result["status"], "conflict")
            self.assertIn("feature.txt", result["conflictingFiles"])


class TestSquash(unittest.TestCase):
    def test_successful_squash(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_repo(tmp)
            exec_branch = _create_exec_branch(repo)
            result = squash(repo, exec_branch, "main", "feat: Bundle 1 — Foundation")
            self.assertEqual(result["status"], "ok")


class TestSyncBase(unittest.TestCase):
    def test_sync_base_after_squash(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_repo(tmp)
            exec_branch = _create_exec_branch(repo)
            # Squash first
            squash(repo, exec_branch, "main", "feat: Bundle 1")
            # Now sync base (we're on main after squash)
            result = sync_base(
                repo, exec_branch, "main",
                "sync: advance merge base after Bundle 1 squash",
            )
            self.assertEqual(result["status"], "ok")


class TestAbort(unittest.TestCase):
    def test_abort_no_merge(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_repo(tmp)
            # Abort when no merge in progress — git merge --abort returns error
            result = abort_merge(repo)
            self.assertEqual(result["status"], "error")


class TestHardReset(unittest.TestCase):
    def test_hard_reset(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_repo(tmp)
            result = hard_reset(repo)
            self.assertEqual(result["status"], "ok")


if __name__ == "__main__":
    unittest.main()
