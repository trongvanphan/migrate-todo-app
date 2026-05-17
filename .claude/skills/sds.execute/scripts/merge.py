#!/usr/bin/env python3
"""Merge-back operations: merge, squash, sync-base."""

import json
import subprocess
import sys
from pathlib import Path


def _git(repo: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", repo, *args],
        capture_output=True, text=True,
    )


def _conflicting_files(repo: str) -> list[str]:
    """Extract conflicting file paths from current merge state."""
    r = _git(repo, "diff", "--name-only", "--diff-filter=U")
    if r.returncode == 0 and r.stdout.strip():
        return r.stdout.strip().splitlines()
    return []


def merge(repo: str, source: str, target: str, message: str) -> dict:
    """Merge source into target with --no-ff.

    Steps: checkout target, merge source, checkout source (return to exec).
    """
    r = _git(repo, "checkout", target)
    if r.returncode != 0:
        return {"status": "error", "phase": "checkout_target", "error": r.stderr.strip()}

    r = _git(repo, "merge", source, "--no-ff", "-m", message)
    if r.returncode != 0:
        files = _conflicting_files(repo)
        if files:
            return {"status": "conflict", "conflictingFiles": files}
        return {"status": "error", "phase": "merge", "error": r.stderr.strip()}

    r = _git(repo, "checkout", source)
    if r.returncode != 0:
        return {"status": "error", "phase": "checkout_source", "error": r.stderr.strip()}

    return {"status": "ok"}


def merge_final(repo: str, source: str, target: str, message: str) -> dict:
    """Merge source into target (final bundle — return to source for cleanup).

    Same as merge() but semantically distinct: caller may handle post-merge differently.
    """
    return merge(repo, source, target, message)


def squash(repo: str, source: str, target: str, message: str) -> dict:
    """Squash-merge source into target, commit, then sync merge-base.

    Steps: checkout target, merge --squash, commit, ours-merge, checkout source.
    """
    r = _git(repo, "checkout", target)
    if r.returncode != 0:
        return {"status": "error", "phase": "checkout_target", "error": r.stderr.strip()}

    r = _git(repo, "merge", "--squash", source)
    if r.returncode != 0:
        # Squash conflicts don't create MERGE_HEAD — different recovery path
        files = _conflicting_files(repo)
        if files:
            return {"status": "squash_conflict", "conflictingFiles": files}
        return {"status": "error", "phase": "squash", "error": r.stderr.strip()}

    r = _git(repo, "commit", "-m", message)
    if r.returncode != 0:
        return {"status": "error", "phase": "commit", "error": r.stderr.strip()}

    return {"status": "ok"}


def sync_base(repo: str, source: str, target: str, message: str) -> dict:
    """Advance merge base after squash (ours-merge on target).

    Run on target branch: `git merge <source> -s ours -m <message>`
    Then return to source.
    """
    # Caller should already be on target, but ensure
    r = _git(repo, "checkout", target)
    if r.returncode != 0:
        return {"status": "error", "phase": "checkout", "error": r.stderr.strip()}

    r = _git(repo, "merge", source, "-s", "ours", "-m", message)
    if r.returncode != 0:
        # Retry once per SKILL.md spec
        _git(repo, "merge", "--abort")
        r = _git(repo, "merge", source, "-s", "ours", "-m", message)
        if r.returncode != 0:
            return {"status": "error", "phase": "sync", "error": r.stderr.strip()}

    r = _git(repo, "checkout", source)
    if r.returncode != 0:
        return {"status": "error", "phase": "checkout_source", "error": r.stderr.strip()}

    return {"status": "ok"}


def abort_merge(repo: str) -> dict:
    """Abort an in-progress merge."""
    r = _git(repo, "merge", "--abort")
    if r.returncode != 0:
        return {"status": "error", "error": r.stderr.strip()}
    return {"status": "ok"}


def hard_reset(repo: str) -> dict:
    """Reset working tree to HEAD (for squash conflict abort)."""
    r = _git(repo, "reset", "--hard", "HEAD")
    if r.returncode != 0:
        return {"status": "error", "error": r.stderr.strip()}
    return {"status": "ok"}


def main():
    import argparse
    p = argparse.ArgumentParser(description="Merge-back operations")
    p.add_argument("action", choices=["merge", "merge-final", "squash", "sync-base",
                                       "abort", "hard-reset"])
    p.add_argument("--repo", required=True, help="Repository root path")
    p.add_argument("--source", help="Source branch")
    p.add_argument("--target", help="Target branch")
    p.add_argument("--message", help="Commit/merge message")
    args = p.parse_args()

    repo = str(Path(args.repo).resolve())

    if args.action in ("merge", "merge-final", "squash", "sync-base"):
        if not args.source or not args.target or not args.message:
            p.error(f"{args.action} requires --source, --target, --message")

    actions = {
        "merge": lambda: merge(repo, args.source, args.target, args.message),
        "merge-final": lambda: merge_final(repo, args.source, args.target, args.message),
        "squash": lambda: squash(repo, args.source, args.target, args.message),
        "sync-base": lambda: sync_base(repo, args.source, args.target, args.message),
        "abort": lambda: abort_merge(repo),
        "hard-reset": lambda: hard_reset(repo),
    }

    result = actions[args.action]()

    json.dump(result, sys.stdout)
    print()
    if result.get("status") == "error":
        print(result.get("error", ""), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
