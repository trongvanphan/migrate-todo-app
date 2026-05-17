#!/usr/bin/env python3
"""Mechanical validation for the task skill.

Graph backend:  proxies to `sds check` commands, returns standard validation JSON.
Markdown backend:  parses tasks.md for structural completeness — frontmatter
    fields, required sections, STEP ID format, bundle file existence.

Usage:
    python validate.py --slug <slug> [--project-root <path>]
    python validate.py --help

Exit codes:
    0  All checks passed.
    1  One or more findings reported.

"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys


def _detect_backend() -> str:
    """Return 'graph' if sds and dolt are both on PATH, else 'markdown'."""
    if shutil.which("sds") and shutil.which("dolt"):
        return "graph"
    return "markdown"


def _run_sds_check(cmd: list[str]) -> dict | None:
    """Run an sds check command. Return parsed JSON or None on failure."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def _validate_graph(slug: str, project_root: str) -> dict:
    """Run sds check commands and aggregate findings."""
    findings = []
    base = ["--slug", slug, "--project-root", project_root]

    checks = [
        (["sds", "check", "cycles"] + base, "TG-1", "Circular dependency detection"),
        (["sds", "check", "conflicts"] + base, "TG-2", "Hot file conflict detection"),
        (["sds", "check", "coverage", "--frs-without-steps"] + base, "TG-3", "FR coverage"),
    ]

    for cmd, rule_id, description in checks:
        result = _run_sds_check(cmd)
        if result is None:
            findings.append({
                "rule": rule_id,
                "severity": "HIGH",
                "message": f"{description}: sds check command failed or timed out.",
                "location": "graph",
            })
        elif not result.get("pass", True):
            for finding in result.get("findings", []):
                findings.append({
                    "rule": rule_id,
                    "severity": finding.get("severity", "MEDIUM"),
                    "message": f"{description}: {finding.get('message', 'check failed')}",
                    "location": finding.get("location", "graph"),
                })

    return {
        "pass": len(findings) == 0,
        "findings": findings,
    }


def _validate_markdown(slug: str, project_root: str) -> dict:
    """Markdown backend: parse tasks.md for structural completeness."""
    tasks_path = os.path.join(project_root, "spec-driven", slug, "tasks.md")
    findings = []

    # TM-1: tasks.md exists
    if not os.path.isfile(tasks_path):
        return {
            "pass": False,
            "findings": [{
                "rule": "TM-1",
                "severity": "HIGH",
                "message": f"Task file not found at {tasks_path}",
                "location": tasks_path,
            }],
        }

    with open(tasks_path, "r") as f:
        content = f.read()

    # TM-2: Frontmatter has required fields
    fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not fm_match:
        findings.append({
            "rule": "TM-2",
            "severity": "HIGH",
            "message": "Task file is missing YAML frontmatter.",
            "location": tasks_path,
        })
    else:
        fm_text = fm_match.group(1)
        required_fields = [
            "slug", "status", "design_source", "design_hash",
            "spec_source", "spec_hash", "strategy",
            "total_steps", "total_slices", "total_bundles",
        ]
        for field in required_fields:
            if f"{field}:" not in fm_text:
                findings.append({
                    "rule": "TM-2",
                    "severity": "MEDIUM",
                    "message": f"Frontmatter missing required field: {field}",
                    "location": tasks_path,
                })

    # TM-3: Required sections present
    required_sections = ["Traceability", "Conflict Analysis"]
    for section in required_sections:
        if f"## {section}" not in content:
            findings.append({
                "rule": "TM-3",
                "severity": "MEDIUM",
                "message": f"Missing required section: {section}",
                "location": tasks_path,
            })

    # TM-3b: At least one Slice header
    if not re.search(r"## Slice \d+:", content):
        findings.append({
            "rule": "TM-3",
            "severity": "MEDIUM",
            "message": "No Slice section headers found (expected '## Slice N: ...')",
            "location": tasks_path,
        })

    # TM-7: Bundle files exist (run first — TM-4/TM-5/TM-6/TM-9 need bundle content)
    bundle_dir = os.path.join(project_root, "spec-driven", slug)
    bundle_refs = re.findall(r"### Bundle (\d+):", content)
    bundle_contents = {}
    for bn in bundle_refs:
        bundle_path = os.path.join(bundle_dir, f"bundle-{bn}.md")
        if not os.path.isfile(bundle_path):
            findings.append({
                "rule": "TM-7",
                "severity": "MEDIUM",
                "message": f"Bundle file missing: bundle-{bn}.md",
                "location": bundle_path,
            })
        else:
            with open(bundle_path, "r") as bf:
                bundle_contents[bn] = bf.read()

    # TM-8: Progress bundle files exist
    for bn in bundle_refs:
        progress_path = os.path.join(bundle_dir, f"progress-bundle-{bn}.md")
        if not os.path.isfile(progress_path):
            findings.append({
                "rule": "TM-8",
                "severity": "LOW",
                "message": f"Progress file missing: progress-bundle-{bn}.md",
                "location": progress_path,
            })

    # TM-4: STEP IDs sequential (scan bundle files, not index-only tasks.md)
    all_step_ids = []
    for bn in sorted(bundle_contents.keys(), key=int):
        bcontent = bundle_contents[bn]
        all_step_ids.extend(re.findall(r"####? STEP-(\d+):", bcontent))
    for i, sid in enumerate(all_step_ids):
        expected = str(i + 1)
        if sid != expected:
            findings.append({
                "rule": "TM-4",
                "severity": "LOW",
                "message": f"STEP ID gap or misnumber: found STEP-{sid}, expected STEP-{expected}",
                "location": os.path.join(bundle_dir, "bundle files"),
            })
            break

    # TM-5, TM-6, TM-9: Check STEP content in bundle files (not index-only tasks.md)
    for bn in bundle_refs:
        if bn not in bundle_contents:
            continue
        bcontent = bundle_contents[bn]
        step_blocks = re.split(r"####? STEP-\d+:", bcontent)[1:]

        # TM-9: Bundle cohesion safety net — flag implausibly large bundles
        if len(step_blocks) > 15:
            findings.append({
                "rule": "TM-9",
                "severity": "LOW",
                "message": f"Bundle {bn} has {len(step_blocks)} STEPs — this likely indicates a missed bundle split",
                "location": os.path.join(bundle_dir, f"bundle-{bn}.md"),
            })

        # TM-5 and TM-6: Per-STEP checks
        step_ids = re.findall(r"####? STEP-(\d+):", bcontent)
        for j, block in enumerate(step_blocks):
            sid = step_ids[j] if j < len(step_ids) else str(j + 1)
            if "> **Intent**:" not in block and "**Intent**:" not in block:
                findings.append({
                    "rule": "TM-5",
                    "severity": "MEDIUM",
                    "message": f"STEP-{sid} is missing an intent block",
                    "location": os.path.join(bundle_dir, f"bundle-{bn}.md"),
                })
            if "**Verify**:" not in block:
                findings.append({
                    "rule": "TM-6",
                    "severity": "MEDIUM",
                    "message": f"STEP-{sid} is missing a verify clause",
                    "location": os.path.join(bundle_dir, f"bundle-{bn}.md"),
                })
            elif "**Level**:" not in block and "Level:" not in block:
                findings.append({
                    "rule": "TM-10",
                    "severity": "MEDIUM",
                    "message": f"STEP-{sid} verify clause missing Level field",
                    "location": os.path.join(bundle_dir, f"bundle-{bn}.md"),
                })

    return {
        "pass": len(findings) == 0,
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Task skill mechanical validation.")
    parser.add_argument("--slug", required=True, help="Project slug.")
    parser.add_argument("--project-root", default=".", help="Project root directory.")
    args = parser.parse_args()

    backend = _detect_backend()
    if backend == "graph":
        output = _validate_graph(args.slug, args.project_root)
    else:
        output = _validate_markdown(args.slug, args.project_root)

    print(json.dumps(output, indent=2))
    return 0 if output["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
