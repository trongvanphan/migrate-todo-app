#!/usr/bin/env python3
"""Test baseline: record and compare."""

import json
import subprocess
import sys
from pathlib import Path


def _git(repo: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", repo, *args],
        capture_output=True, text=True,
    )


def record(repo: str, test_cmd: str | None) -> dict:
    """Record baseline HEAD hash and test exit code."""
    r = _git(repo, "rev-parse", "HEAD")
    if r.returncode != 0:
        return {"status": "error", "error": f"rev-parse failed: {r.stderr.strip()}"}

    head = r.stdout.strip()

    if not test_cmd:
        return {"status": "ok", "hash": head, "exitCode": None, "note": "No test command provided"}

    test = subprocess.run(
        test_cmd, shell=True, cwd=repo,
        capture_output=True, text=True,
    )

    # Distinguish launch failure from test failure
    exit_code = test.returncode
    note = None
    if exit_code != 0 and ("not found" in test.stderr.lower()
                           or "permission denied" in test.stderr.lower()
                           or "no such file" in test.stderr.lower()):
        note = f"Baseline run failed to launch: {test.stderr.strip()[:200]}"
        exit_code = None

    result = {"status": "ok", "hash": head, "exitCode": exit_code}
    if note:
        result["note"] = note
    return result


def compare(repo: str, test_cmd: str, baseline_exit_code: int | None) -> dict:
    """Run tests and compare exit code against baseline."""
    if baseline_exit_code is None:
        return {"status": "skip", "reason": "No baseline exit code — regression gate skipped"}

    test = subprocess.run(
        test_cmd, shell=True, cwd=repo,
        capture_output=True, text=True,
    )

    current_code = test.returncode
    regression = current_code != 0 and current_code != baseline_exit_code

    result = {
        "status": "ok",
        "regression": regression,
        "baselineExitCode": baseline_exit_code,
        "currentExitCode": current_code,
    }

    if regression:
        # Get recent commits to help identify cause
        log = _git(repo, "log", "--oneline", "-10")
        result["recentCommits"] = log.stdout.strip() if log.returncode == 0 else ""

    return result


def main():
    import argparse
    p = argparse.ArgumentParser(description="Test baseline record/compare")
    p.add_argument("action", choices=["record", "compare"])
    p.add_argument("--repo", required=True, help="Repository root path")
    p.add_argument("--test-cmd", help="Test command to run")
    p.add_argument("--baseline-exit-code", type=int, help="Baseline exit code (for compare)")
    args = p.parse_args()

    repo = str(Path(args.repo).resolve())

    if args.action == "record":
        result = record(repo, args.test_cmd)
    elif args.action == "compare":
        if not args.test_cmd:
            p.error("compare requires --test-cmd")
        result = compare(repo, args.test_cmd, args.baseline_exit_code)

    json.dump(result, sys.stdout)
    print()
    if result.get("status") == "error":
        print(result.get("error", ""), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
