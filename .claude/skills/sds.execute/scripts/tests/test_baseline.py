"""Tests for baseline.py — uses real git repos in tmp dirs."""

import os
import subprocess
import tempfile
import unittest

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from baseline import record, compare


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


class TestRecord(unittest.TestCase):
    def test_records_hash_and_exit_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_repo(tmp)
            result = record(repo, "true")
            self.assertEqual(result["status"], "ok")
            self.assertEqual(len(result["hash"]), 40)  # full SHA
            self.assertEqual(result["exitCode"], 0)

    def test_records_failing_tests(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_repo(tmp)
            result = record(repo, "false")
            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["exitCode"], 1)

    def test_no_test_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_repo(tmp)
            result = record(repo, None)
            self.assertEqual(result["status"], "ok")
            self.assertIsNone(result["exitCode"])


class TestCompare(unittest.TestCase):
    def test_no_regression(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_repo(tmp)
            result = compare(repo, "true", 0)
            self.assertEqual(result["status"], "ok")
            self.assertFalse(result["regression"])

    def test_regression_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_repo(tmp)
            result = compare(repo, "false", 0)
            self.assertEqual(result["status"], "ok")
            self.assertTrue(result["regression"])
            self.assertEqual(result["baselineExitCode"], 0)
            self.assertEqual(result["currentExitCode"], 1)

    def test_pre_existing_failure_same_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_repo(tmp)
            # Baseline was 1, current is 1 — not a regression
            result = compare(repo, "false", 1)
            self.assertFalse(result["regression"])

    def test_null_baseline_skips(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_repo(tmp)
            result = compare(repo, "true", None)
            self.assertEqual(result["status"], "skip")


if __name__ == "__main__":
    unittest.main()
