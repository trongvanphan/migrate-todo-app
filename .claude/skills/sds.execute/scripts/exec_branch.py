#!/usr/bin/env python3
"""Execution branch lifecycle: create, validate, delete."""

import json
import subprocess
import sys
from pathlib import Path


def _git(repo: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", repo, *args],
        capture_output=True, text=True,
    )


def current_branch(repo: str) -> str:
    r = _git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    return r.stdout.strip() if r.returncode == 0 else ""


def branch_exists(repo: str, branch: str) -> bool:
    r = _git(repo, "rev-parse", "--verify", branch)
    return r.returncode == 0


def create(repo: str, branch: str) -> dict:
    """Create execution branch from current HEAD."""
    user_branch = current_branch(repo)
    if user_branch == "HEAD":
        return {"status": "error", "error": "Detached HEAD — checkout a named branch first"}

    if branch_exists(repo, branch):
        return {"status": "exists", "userBranch": user_branch, "execBranch": branch}

    r = _git(repo, "checkout", "-b", branch)
    if r.returncode != 0:
        return {"status": "error", "error": r.stderr.strip()}

    return {"status": "created", "userBranch": user_branch, "execBranch": branch}


def validate(repo: str, branch: str) -> dict:
    """Validate execution branch exists and check it out."""
    if not branch_exists(repo, branch):
        return {"status": "missing", "branch": branch}

    r = _git(repo, "checkout", branch)
    if r.returncode != 0:
        return {"status": "error", "error": r.stderr.strip()}

    return {"status": "ok", "branch": branch}


def delete(repo: str, branch: str) -> dict:
    """Delete execution branch (force)."""
    if not branch_exists(repo, branch):
        return {"status": "missing", "branch": branch}

    # Ensure we're not on the branch we're deleting
    if current_branch(repo) == branch:
        return {"status": "error", "error": f"Cannot delete — currently on {branch}"}

    r = _git(repo, "branch", "-D", branch)
    if r.returncode != 0:
        return {"status": "error", "error": r.stderr.strip()}

    return {"status": "deleted", "branch": branch}


def main():
    import argparse
    p = argparse.ArgumentParser(description="Execution branch lifecycle")
    p.add_argument("action", choices=["create", "validate", "delete"])
    p.add_argument("--repo", required=True, help="Repository root path")
    p.add_argument("--branch", required=True, help="Execution branch name")
    args = p.parse_args()

    repo = str(Path(args.repo).resolve())
    actions = {"create": create, "validate": validate, "delete": delete}
    result = actions[args.action](repo, args.branch)

    json.dump(result, sys.stdout)
    print()
    if result.get("status") == "error":
        print(result["error"], file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
