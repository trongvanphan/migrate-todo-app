"""Tests for exec_branch.py — uses real git repos in tmp dirs."""

import os
import subprocess
import tempfile
import unittest

# Allow imports from parent directory
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from exec_branch import create, validate, delete, current_branch, branch_exists


def _init_repo(tmpdir: str) -> str:
    """Create a git repo with one commit, return path."""
    repo = os.path.join(tmpdir, "repo")
    os.makedirs(repo)
    subprocess.run(["git", "init", repo], capture_output=True)
    subprocess.run(["git", "-C", repo, "config", "user.email", "test@test.com"], capture_output=True)
    subprocess.run(["git", "-C", repo, "config", "user.name", "Test"], capture_output=True)
    # Create initial commit on main
    open(os.path.join(repo, "README.md"), "w").close()
    subprocess.run(["git", "-C", repo, "add", "."], capture_output=True)
    subprocess.run(["git", "-C", repo, "commit", "-m", "init"], capture_output=True)
    return repo


class TestCreate(unittest.TestCase):
    def test_creates_branch(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_repo(tmp)
            result = create(repo, "spec-driven/test/exec")
            self.assertEqual(result["status"], "created")
            self.assertEqual(result["execBranch"], "spec-driven/test/exec")
            self.assertTrue(branch_exists(repo, "spec-driven/test/exec"))

    def test_returns_exists_if_branch_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_repo(tmp)
            create(repo, "spec-driven/test/exec")
            # Switch back to main so we're not on the exec branch
            subprocess.run(["git", "-C", repo, "checkout", "main"], capture_output=True)
            result = create(repo, "spec-driven/test/exec")
            self.assertEqual(result["status"], "exists")

    def test_records_user_branch(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_repo(tmp)
            result = create(repo, "spec-driven/test/exec")
            self.assertIn("userBranch", result)
            self.assertNotEqual(result["userBranch"], "HEAD")

    def test_detached_head_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_repo(tmp)
            head = subprocess.run(
                ["git", "-C", repo, "rev-parse", "HEAD"],
                capture_output=True, text=True,
            ).stdout.strip()
            subprocess.run(["git", "-C", repo, "checkout", head], capture_output=True)
            result = create(repo, "spec-driven/test/exec")
            self.assertEqual(result["status"], "error")
            self.assertIn("Detached HEAD", result["error"])


class TestValidate(unittest.TestCase):
    def test_validates_existing_branch(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_repo(tmp)
            create(repo, "spec-driven/test/exec")
            subprocess.run(["git", "-C", repo, "checkout", "main"], capture_output=True)
            result = validate(repo, "spec-driven/test/exec")
            self.assertEqual(result["status"], "ok")
            self.assertEqual(current_branch(repo), "spec-driven/test/exec")

    def test_missing_branch(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_repo(tmp)
            result = validate(repo, "spec-driven/test/exec")
            self.assertEqual(result["status"], "missing")


class TestDelete(unittest.TestCase):
    def test_deletes_branch(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_repo(tmp)
            create(repo, "spec-driven/test/exec")
            subprocess.run(["git", "-C", repo, "checkout", "main"], capture_output=True)
            result = delete(repo, "spec-driven/test/exec")
            self.assertEqual(result["status"], "deleted")
            self.assertFalse(branch_exists(repo, "spec-driven/test/exec"))

    def test_cannot_delete_current_branch(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_repo(tmp)
            create(repo, "spec-driven/test/exec")
            result = delete(repo, "spec-driven/test/exec")
            self.assertEqual(result["status"], "error")

    def test_missing_branch(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_repo(tmp)
            result = delete(repo, "spec-driven/test/exec")
            self.assertEqual(result["status"], "missing")


if __name__ == "__main__":
    unittest.main()
