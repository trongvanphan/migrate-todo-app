"""Tests for worktree.py — uses real git repos in tmp dirs."""

import os
import subprocess
import tempfile
import unittest

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from worktree import create, reset, list_worktrees, remove, remove_all


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


class TestCreate(unittest.TestCase):
    def test_creates_worktree(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_repo(tmp)
            head = subprocess.run(
                ["git", "-C", repo, "rev-parse", "HEAD"],
                capture_output=True, text=True,
            ).stdout.strip()
            result = create(repo, "sequential", head)
            self.assertEqual(result["status"], "created")
            self.assertTrue(os.path.isdir(os.path.join(repo, ".worktrees", "sequential")))
            self.assertEqual(result["branch"], "exec-sequential")

    def test_idempotent_create(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_repo(tmp)
            head = subprocess.run(
                ["git", "-C", repo, "rev-parse", "HEAD"],
                capture_output=True, text=True,
            ).stdout.strip()
            create(repo, "sequential", head)
            result = create(repo, "sequential", head)
            self.assertEqual(result["status"], "exists")

    def test_creates_parallel_worktrees(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_repo(tmp)
            head = subprocess.run(
                ["git", "-C", repo, "rev-parse", "HEAD"],
                capture_output=True, text=True,
            ).stdout.strip()
            for i in range(1, 4):
                result = create(repo, f"bundle-{i}", head)
                self.assertEqual(result["status"], "created")

    def test_create_with_install_cmd(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_repo(tmp)
            head = subprocess.run(
                ["git", "-C", repo, "rev-parse", "HEAD"],
                capture_output=True, text=True,
            ).stdout.strip()
            # Use a benign command as install
            result = create(repo, "sequential", head, install_cmd="echo installed")
            self.assertEqual(result["status"], "created")

    def test_create_with_failing_install(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_repo(tmp)
            head = subprocess.run(
                ["git", "-C", repo, "rev-parse", "HEAD"],
                capture_output=True, text=True,
            ).stdout.strip()
            result = create(repo, "sequential", head, install_cmd="false")
            self.assertEqual(result["status"], "created_install_failed")


class TestReset(unittest.TestCase):
    def test_resets_worktree(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_repo(tmp)
            head = subprocess.run(
                ["git", "-C", repo, "rev-parse", "HEAD"],
                capture_output=True, text=True,
            ).stdout.strip()
            create(repo, "sequential", head)

            # Make a commit on main
            with open(os.path.join(repo, "new.txt"), "w") as f:
                f.write("new")
            subprocess.run(["git", "-C", repo, "add", "."], capture_output=True)
            subprocess.run(["git", "-C", repo, "commit", "-m", "second"], capture_output=True)

            new_head = subprocess.run(
                ["git", "-C", repo, "rev-parse", "HEAD"],
                capture_output=True, text=True,
            ).stdout.strip()

            result = reset(repo, "sequential", new_head)
            self.assertEqual(result["status"], "ok")

    def test_reset_nonexistent(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_repo(tmp)
            result = reset(repo, "nonexistent", "HEAD")
            self.assertEqual(result["status"], "error")


class TestList(unittest.TestCase):
    def test_empty_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_repo(tmp)
            result = list_worktrees(repo)
            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["worktrees"], [])

    def test_lists_worktrees(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_repo(tmp)
            head = subprocess.run(
                ["git", "-C", repo, "rev-parse", "HEAD"],
                capture_output=True, text=True,
            ).stdout.strip()
            create(repo, "sequential", head)
            create(repo, "bundle-1", head)
            result = list_worktrees(repo)
            self.assertEqual(len(result["worktrees"]), 2)
            names = [w["name"] for w in result["worktrees"]]
            self.assertIn("sequential", names)
            self.assertIn("bundle-1", names)


class TestRemove(unittest.TestCase):
    def test_removes_worktree(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_repo(tmp)
            head = subprocess.run(
                ["git", "-C", repo, "rev-parse", "HEAD"],
                capture_output=True, text=True,
            ).stdout.strip()
            create(repo, "sequential", head)
            result = remove(repo, "sequential")
            self.assertEqual(result["status"], "ok")
            self.assertFalse(os.path.isdir(os.path.join(repo, ".worktrees", "sequential")))

    def test_remove_all(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_repo(tmp)
            head = subprocess.run(
                ["git", "-C", repo, "rev-parse", "HEAD"],
                capture_output=True, text=True,
            ).stdout.strip()
            create(repo, "bundle-1", head)
            create(repo, "bundle-2", head)
            result = remove_all(repo)
            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["removed"], 2)


if __name__ == "__main__":
    unittest.main()
