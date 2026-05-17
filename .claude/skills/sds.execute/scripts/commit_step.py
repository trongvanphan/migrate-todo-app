#!/usr/bin/env python3
"""Commit a step's code files and record the hash in the progress file."""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def _git(repo: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", repo, *args],
        capture_output=True, text=True,
    )


def _update_progress_hash(progress_path: str, step: str, commit_hash: str) -> str | None:
    """Write commit_hash into the Commit column of the step's row. Returns error or None."""
    path = Path(progress_path)
    if not path.is_file():
        return f"Progress file not found: {progress_path}"

    lines = path.read_text().splitlines(keepends=True)
    found = False
    for i, line in enumerate(lines):
        cells = line.split("|")
        if len(cells) >= 4 and cells[1].strip() == step:
            cells[3] = f" {commit_hash} "
            lines[i] = "|".join(cells)
            found = True
            break

    if not found:
        return f"{step} not found in progress file table"

    path.write_text("".join(lines))
    return None


def commit_step(repo: str, step: str, message: str, files: list[str],
                progress_file: str | None = None) -> dict:
    """Stage files, commit, capture hash, write hash to progress file."""
    # Stage code files
    for f in files:
        full = str(Path(repo) / f)
        if not Path(full).exists():
            return {"status": "error", "error": f"File not found: {f}"}

    r = _git(repo, "add", *files)
    if r.returncode != 0:
        return {"status": "error", "error": f"git add failed: {r.stderr.strip()}"}

    # Commit
    r = _git(repo, "commit", "-m", message)
    if r.returncode != 0:
        return {"status": "error", "error": f"git commit failed: {r.stderr.strip()}"}

    # Capture hash
    r = _git(repo, "rev-parse", "--short", "HEAD")
    if r.returncode != 0:
        return {"status": "error", "error": f"rev-parse failed: {r.stderr.strip()}"}
    commit_hash = r.stdout.strip()

    # Update progress file (optional — omitted for multi-project non-artifact-home commits)
    if progress_file:
        progress_path = str(Path(repo) / progress_file)
        err = _update_progress_hash(progress_path, step, commit_hash)
        if err:
            return {"status": "error", "error": err}

    return {"status": "ok", "commitHash": commit_hash}


def main():
    p = argparse.ArgumentParser(description="Commit step code and record hash")
    sub = p.add_subparsers(dest="action")

    cs = sub.add_parser("commit-step")
    cs.add_argument("--repo", required=True, help="Repository/worktree root path")
    cs.add_argument("--step", required=True, help="Step ID (e.g., STEP-1)")
    cs.add_argument("--message", required=True, help="Commit message")
    cs.add_argument("--files", required=True, help="Comma-separated file paths to stage")
    cs.add_argument("--progress-file", help="Progress file path (relative to repo). Omit for multi-project non-artifact-home commits.")

    args = p.parse_args()
    if args.action != "commit-step":
        p.error("Only 'commit-step' action is supported")

    repo = str(Path(args.repo).resolve())
    files = [f.strip() for f in args.files.split(",") if f.strip()]
    if not files:
        print(json.dumps({"status": "error", "error": "No files specified"}))
        sys.exit(1)

    result = commit_step(repo, args.step, args.message, files, args.progress_file)
    json.dump(result, sys.stdout)
    print()
    if result["status"] == "error":
        sys.exit(1)


if __name__ == "__main__":
    main()
