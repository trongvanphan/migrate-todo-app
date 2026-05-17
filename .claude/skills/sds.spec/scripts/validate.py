#!/usr/bin/env python3
"""Mechanical validation for the spec skill.

Graph backend:  proxies to `sds check all`, returns standard validation JSON.
Markdown backend:  returns a pass result — mechanical validation is not
    applicable to free-form markdown.  Semantic quality checks are handled
    by the qualitative subagent (spec-validation-criteria-markdown.md).

Usage:
    python validate.py --slug <slug> [--project-root <path>]
    python validate.py --help

Exit codes:
    0  All checks passed (or markdown backend — no mechanical checks).
    1  One or more findings reported.
    2  Script error (bad arguments, sds invocation failure).
"""

import argparse
import json
import shutil
import subprocess
import sys


def _detect_backend() -> str:
    """Return 'graph' if sds and dolt are both on PATH, else 'markdown'."""
    if shutil.which("sds") and shutil.which("dolt"):
        return "graph"
    return "markdown"


def _validate_graph(slug: str, project_root: str) -> dict:
    """Run sds check all and return its JSON output."""
    cmd = ["sds", "check", "all", "--slug", slug, "--project-root", project_root]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except FileNotFoundError:
        return {
            "pass": False,
            "findings": [{
                "rule": "sds-unavailable",
                "severity": "HIGH",
                "message": "sds CLI not found. Install it to enable graph validation.",
                "location": "PATH",
            }],
        }
    except subprocess.TimeoutExpired:
        return {
            "pass": False,
            "findings": [{
                "rule": "sds-timeout",
                "severity": "HIGH",
                "message": "sds check all timed out after 30s.",
                "location": "N/A",
            }],
        }

    # sds check all prints JSON to stdout regardless of exit code.
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {
            "pass": False,
            "findings": [{
                "rule": "sds-parse-error",
                "severity": "HIGH",
                "message": f"Could not parse sds output: {result.stderr.strip() or result.stdout.strip()}",
                "location": "N/A",
            }],
        }


def _validate_markdown() -> dict:
    """Markdown backend: no mechanical checks. Semantic validation is handled by the subagent."""
    return {"pass": True, "findings": []}


def main() -> int:
    parser = argparse.ArgumentParser(description="Spec skill mechanical validation.")
    parser.add_argument("--slug", required=True, help="Project slug.")
    parser.add_argument("--project-root", default=".", help="Project root directory.")
    args = parser.parse_args()

    backend = _detect_backend()
    if backend == "graph":
        output = _validate_graph(args.slug, args.project_root)
    else:
        output = _validate_markdown()

    print(json.dumps(output, indent=2))
    return 0 if output["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
