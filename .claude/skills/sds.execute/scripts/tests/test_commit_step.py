"""Tests for commit_step.py — uses real git repos in tmp dirs."""

import os
import subprocess
import tempfile
import unittest

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from commit_step import commit_step


PROGRESS_TEMPLATE = """\
# Progress: Bundle 1

## Step Status

| Step | Status | Commit | Notes |
|------|--------|--------|-------|
| STEP-1 | done | — | — |
| STEP-2 | pending | — | — |
| STEP-3 | pending | — | — |
"""


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


def _write_progress(repo: str, content: str = PROGRESS_TEMPLATE) -> str:
    """Write progress file and commit it. Returns relative path."""
    rel = os.path.join("spec-driven", "slug", "progress-bundle-1.md")
    full = os.path.join(repo, rel)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)
    subprocess.run(["git", "-C", repo, "add", rel], capture_output=True)
    subprocess.run(["git", "-C", repo, "commit", "-m", "add progress"], capture_output=True)
    return rel


def _write_code_file(repo: str, rel_path: str, content: str = "x") -> str:
    """Write a code file (not staged). Returns relative path."""
    full = os.path.join(repo, rel_path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)
    return rel_path


class TestCommitStep(unittest.TestCase):
    def test_commit_step_basic(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_repo(tmp)
            progress = _write_progress(repo)
            _write_code_file(repo, "src/app.ts", "console.log('hello')")
            result = commit_step(repo, "STEP-1", "feat: app [STEP-1]",
                                 ["src/app.ts"], progress)
            self.assertEqual(result["status"], "ok")
            self.assertTrue(len(result["commitHash"]) >= 7)

    def test_commit_step_hash_in_progress_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_repo(tmp)
            progress = _write_progress(repo)
            _write_code_file(repo, "src/app.ts", "console.log('hello')")
            result = commit_step(repo, "STEP-1", "feat: app [STEP-1]",
                                 ["src/app.ts"], progress)
            # Read progress file and check hash is recorded
            with open(os.path.join(repo, progress)) as f:
                content = f.read()
            self.assertIn(result["commitHash"], content)
            self.assertNotIn("| STEP-1 | done | — |", content)

    def test_commit_step_file_not_found(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_repo(tmp)
            progress = _write_progress(repo)
            result = commit_step(repo, "STEP-1", "feat: app [STEP-1]",
                                 ["nonexistent.ts"], progress)
            self.assertEqual(result["status"], "error")
            self.assertIn("not found", result["error"])

    def test_commit_step_progress_file_not_found(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_repo(tmp)
            _write_code_file(repo, "src/app.ts", "x")
            result = commit_step(repo, "STEP-1", "feat: app [STEP-1]",
                                 ["src/app.ts"], "nonexistent/progress.md")
            self.assertEqual(result["status"], "error")
            self.assertIn("not found", result["error"].lower())

    def test_commit_step_step_not_in_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_repo(tmp)
            progress = _write_progress(repo)
            _write_code_file(repo, "src/app.ts", "x")
            result = commit_step(repo, "STEP-99", "feat: app [STEP-99]",
                                 ["src/app.ts"], progress)
            self.assertEqual(result["status"], "error")
            self.assertIn("not found", result["error"].lower())

    def test_commit_step_preserves_other_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_repo(tmp)
            progress = _write_progress(repo)
            _write_code_file(repo, "src/app.ts", "x")
            commit_step(repo, "STEP-1", "feat: app [STEP-1]",
                        ["src/app.ts"], progress)
            with open(os.path.join(repo, progress)) as f:
                content = f.read()
            # STEP-2 and STEP-3 should be unchanged
            self.assertIn("| STEP-2 | pending | — | — |", content)
            self.assertIn("| STEP-3 | pending | — | — |", content)

    def test_commit_step_nested_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = _init_repo(tmp)
            progress = _write_progress(repo)
            _write_code_file(repo, "frontend/src/App.tsx", "export default App")
            result = commit_step(repo, "STEP-1", "feat: app [STEP-1]",
                                 ["frontend/src/App.tsx"], progress)
            self.assertEqual(result["status"], "ok")
            # Verify the file is in the commit
            log = subprocess.run(
                ["git", "-C", repo, "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"],
                capture_output=True, text=True,
            )
            self.assertIn("frontend/src/App.tsx", log.stdout)


if __name__ == "__main__":
    unittest.main()
