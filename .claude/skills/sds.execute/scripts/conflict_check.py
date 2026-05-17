#!/usr/bin/env python3
"""Pre-merge conflict detection using git merge-tree."""

import json
import subprocess
import sys
from pathlib import Path


def _git(repo: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", repo, *args],
        capture_output=True, text=True,
    )


def check(repo: str, ours: str, theirs: str) -> dict:
    """Check for merge conflicts without modifying the working tree.

    Uses `git merge-tree --write-tree` (Git 2.38+). This is an in-memory check.
    """
    r = _git(repo, "merge-tree", "--write-tree", ours, theirs)

    # Command not available (old git)
    if r.returncode == 127 or (r.returncode != 0 and "merge-tree" in r.stderr.lower()):
        return {"status": "unavailable", "reason": "git merge-tree --write-tree not available"}

    # merge-tree exits non-zero when conflicts exist
    if r.returncode != 0 and "CONFLICT" in r.stdout:
        # Extract conflicting file names from output
        files = []
        for line in r.stdout.splitlines():
            if line.startswith("CONFLICT"):
                # Format: "CONFLICT (content): Merge conflict in <file>"
                if " in " in line:
                    files.append(line.split(" in ", 1)[1].strip())
                # Format: "CONFLICT (add/add): Merge conflict in <file>"
                elif ":" in line:
                    after_colon = line.split(":", 1)[1].strip()
                    if after_colon.startswith("Merge conflict in "):
                        files.append(after_colon[len("Merge conflict in "):].strip())
        return {"status": "conflict", "conflictingFiles": files}

    # Non-zero exit without CONFLICT markers = tool failure, not conflict
    if r.returncode != 0:
        return {"status": "unavailable", "reason": f"merge-tree failed: {r.stderr.strip()[:200]}"}

    return {"status": "clean"}


def main():
    import argparse
    p = argparse.ArgumentParser(description="Pre-merge conflict detection")
    p.add_argument("--repo", required=True, help="Repository root path")
    p.add_argument("--ours", required=True, help="Our branch (typically user branch)")
    p.add_argument("--theirs", required=True, help="Their branch (typically exec branch)")
    args = p.parse_args()

    repo = str(Path(args.repo).resolve())
    result = check(repo, args.ours, args.theirs)

    json.dump(result, sys.stdout)
    print()


if __name__ == "__main__":
    main()
