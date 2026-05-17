#!/usr/bin/env python3
"""Worktree lifecycle: create, reset, list, remove, remove-all."""

import json
import subprocess
import sys
from pathlib import Path


def _git(repo: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", repo, *args],
        capture_output=True, text=True,
    )


def create(repo: str, name: str, ref: str, install_cmd: str | None = None) -> dict:
    """Create a worktree at <repo>/.worktrees/<name> from ref.

    If the worktree already exists at the expected path, no-op.
    """
    wt_dir = str(Path(repo) / ".worktrees" / name)
    branch = f"exec-{name}"

    # Idempotent: if worktree dir already exists, verify it's valid
    if Path(wt_dir).is_dir():
        check = subprocess.run(
            ["git", "-C", wt_dir, "rev-parse", "--is-inside-work-tree"],
            capture_output=True, text=True,
        )
        if check.returncode == 0:
            return {"status": "exists", "worktree": wt_dir, "branch": branch}

    r = _git(repo, "worktree", "add", "-b", branch, wt_dir, ref)
    if r.returncode != 0:
        return {"status": "error", "error": r.stderr.strip()}

    # Verify creation
    check = subprocess.run(
        ["git", "-C", wt_dir, "rev-parse", "--is-inside-work-tree"],
        capture_output=True, text=True,
    )
    if check.returncode != 0:
        return {"status": "error", "error": "Worktree created but verification failed"}

    # Install dependencies if command provided
    if install_cmd:
        install = subprocess.run(
            install_cmd, shell=True, cwd=wt_dir,
            capture_output=True, text=True,
        )
        if install.returncode != 0:
            return {
                "status": "created_install_failed",
                "worktree": wt_dir,
                "branch": branch,
                "installError": install.stderr.strip(),
            }

    return {"status": "created", "worktree": wt_dir, "branch": branch}


def reset(repo: str, name: str, ref: str) -> dict:
    """Reset an existing worktree branch to a new ref."""
    wt_dir = str(Path(repo) / ".worktrees" / name)

    if not Path(wt_dir).is_dir():
        return {"status": "error", "error": f"Worktree not found: {wt_dir}"}

    r = subprocess.run(
        ["git", "-C", wt_dir, "reset", "--hard", ref],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        return {"status": "error", "error": r.stderr.strip()}

    return {"status": "ok", "worktree": wt_dir, "ref": ref}


def list_worktrees(repo: str) -> dict:
    """List worktrees under <repo>/.worktrees/."""
    wt_root = Path(repo) / ".worktrees"
    if not wt_root.is_dir():
        return {"status": "ok", "worktrees": []}

    worktrees = []
    for d in sorted(wt_root.iterdir()):
        if d.is_dir():
            worktrees.append({"name": d.name, "path": str(d)})

    return {"status": "ok", "worktrees": worktrees}


def remove(repo: str, name: str) -> dict:
    """Remove a single worktree and its branch."""
    wt_dir = str(Path(repo) / ".worktrees" / name)
    branch = f"exec-{name}"
    errors = []

    r = _git(repo, "worktree", "remove", wt_dir, "--force")
    if r.returncode != 0:
        errors.append(f"worktree remove: {r.stderr.strip()}")

    r = _git(repo, "branch", "-d", branch)
    if r.returncode != 0:
        # Try force delete if normal delete fails
        r2 = _git(repo, "branch", "-D", branch)
        if r2.returncode != 0:
            errors.append(f"branch delete: {r2.stderr.strip()}")

    if errors:
        return {"status": "partial", "errors": errors}
    return {"status": "ok", "removed": name}


def remove_all(repo: str) -> dict:
    """Remove all worktrees under <repo>/.worktrees/."""
    listing = list_worktrees(repo)
    if not listing["worktrees"]:
        return {"status": "ok", "removed": 0}

    results = []
    for wt in listing["worktrees"]:
        r = remove(repo, wt["name"])
        results.append({"name": wt["name"], **r})

    failed = [r for r in results if r["status"] != "ok"]
    return {
        "status": "ok" if not failed else "partial",
        "removed": len(results) - len(failed),
        "total": len(results),
        "failures": failed if failed else [],
    }


def main():
    import argparse
    p = argparse.ArgumentParser(description="Worktree lifecycle")
    p.add_argument("action", choices=["create", "reset", "list", "remove", "remove-all"])
    p.add_argument("--repo", required=True, help="Repository root path")
    p.add_argument("--name", help="Worktree name (e.g., 'sequential', 'bundle-2')")
    p.add_argument("--ref", help="Git ref to create from or reset to")
    p.add_argument("--install-cmd", help="Dependency install command (for create)")
    args = p.parse_args()

    repo = str(Path(args.repo).resolve())

    result: dict
    if args.action == "create":
        if not args.name or not args.ref:
            p.error("create requires --name and --ref")
        result = create(repo, args.name, args.ref, args.install_cmd)
    elif args.action == "reset":
        if not args.name or not args.ref:
            p.error("reset requires --name and --ref")
        result = reset(repo, args.name, args.ref)
    elif args.action == "list":
        result = list_worktrees(repo)
    elif args.action == "remove":
        if not args.name:
            p.error("remove requires --name")
        result = remove(repo, args.name)
    else:  # remove-all
        result = remove_all(repo)

    json.dump(result, sys.stdout)
    print()
    if result.get("status") == "error":
        print(result.get("error", ""), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
