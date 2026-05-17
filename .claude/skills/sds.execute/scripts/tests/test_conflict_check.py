"""Tests for conflict_check.py — uses real git repos in tmp dirs."""

import os
import subprocess
import tempfile
import unittest

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from conflict_check import check


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


class TestCheck(unittest.TestCase):
    def test_clean_merge(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_repo(tmp)
            # Create a branch with non-conflicting changes
            subprocess.run(["git", "-C", repo, "checkout", "-b", "feature"], capture_output=True)
            with open(os.path.join(repo, "feature.txt"), "w") as f:
                f.write("feature")
            subprocess.run(["git", "-C", repo, "add", "."], capture_output=True)
            subprocess.run(["git", "-C", repo, "commit", "-m", "feature"], capture_output=True)
            subprocess.run(["git", "-C", repo, "checkout", "main"], capture_output=True)

            result = check(repo, "main", "feature")
            self.assertEqual(result["status"], "clean")

    def test_conflict_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_repo(tmp)
            # Create conflicting changes
            subprocess.run(["git", "-C", repo, "checkout", "-b", "feature"], capture_output=True)
            with open(os.path.join(repo, "README.md"), "w") as f:
                f.write("feature version")
            subprocess.run(["git", "-C", repo, "add", "."], capture_output=True)
            subprocess.run(["git", "-C", repo, "commit", "-m", "feature"], capture_output=True)

            subprocess.run(["git", "-C", repo, "checkout", "main"], capture_output=True)
            with open(os.path.join(repo, "README.md"), "w") as f:
                f.write("main version")
            subprocess.run(["git", "-C", repo, "add", "."], capture_output=True)
            subprocess.run(["git", "-C", repo, "commit", "-m", "main change"], capture_output=True)

            result = check(repo, "main", "feature")
            self.assertEqual(result["status"], "conflict")
            self.assertTrue(len(result["conflictingFiles"]) > 0)


if __name__ == "__main__":
    unittest.main()
