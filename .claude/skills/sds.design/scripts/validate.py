#!/usr/bin/env python3
"""Mechanical validation for the design skill.

Graph backend:  proxies to `sds check all`, returns standard validation JSON.
Markdown backend:  parses design.md for structural completeness — frontmatter
    fields, required sections, ID format consistency.

Usage:
    python validate.py --slug <slug> [--project-root <path>]
    python validate.py --help

Exit codes:
    0  All checks passed.
    1  One or more findings reported.
    2  Script error (bad arguments, sds invocation failure).
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


def _validate_markdown(slug: str, project_root: str) -> dict:
    """Markdown backend: parse design.md for structural completeness."""
    design_path = os.path.join(project_root, "spec-driven", slug, "design.md")
    findings = []

    if not os.path.isfile(design_path):
        return {
            "pass": False,
            "findings": [{
                "rule": "DM-1",
                "severity": "HIGH",
                "message": f"Design file not found at {design_path}",
                "location": design_path,
            }],
        }

    with open(design_path, "r") as f:
        content = f.read()

    # DM-2: Frontmatter exists and has required fields
    fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not fm_match:
        findings.append({
            "rule": "DM-2",
            "severity": "HIGH",
            "message": "Design file is missing YAML frontmatter.",
            "location": design_path,
        })
    else:
        fm_text = fm_match.group(1)
        for field in ["slug", "status", "spec_source", "spec_tier", "spec_hash", "test_approach", "test_capabilities", "adaptive_flow", "created_date", "last_updated"]:
            if f"{field}:" not in fm_text:
                findings.append({
                    "rule": "DM-2",
                    "severity": "MEDIUM",
                    "message": f"Frontmatter missing required field: {field}",
                    "location": design_path,
                })

    # DM-3: Required sections present
    required_sections = [
        "Overview", "Technical Approach", "Findings", "Architecture Decisions",
        "Resolved Uncertainties", "Standards", "File Inventory",
        "Dependencies and Coupling", "Spec Deviations", "Open Questions",
        "Constraints (Technical)", "Assumptions", "Risks (Technical)",
        "References",
    ]
    for section in required_sections:
        if f"## {section}" not in content:
            findings.append({
                "rule": "DM-3",
                "severity": "MEDIUM",
                "message": f"Missing required section: {section}",
                "location": design_path,
            })

    # DM-7: references/ directory exists with required files
    refs_dir = os.path.join(project_root, "spec-driven", slug, "references")
    for ref_file in ["research.md", "standards.md"]:
        ref_path = os.path.join(refs_dir, ref_file)
        if not os.path.isfile(ref_path):
            findings.append({
                "rule": "DM-7",
                "severity": "MEDIUM",
                "message": f"Missing references file: references/{ref_file}",
                "location": ref_path,
            })

    # DM-4: Finding IDs are sequential (F-1, F-2, ...)
    # Match F-N IDs in heading format (references/research.md) or table format (design.md)
    finding_ids = re.findall(r"(?:^### (F-\d+):|^\| (F-\d+) \|)", content, re.MULTILINE)
    finding_ids = [h or t for h, t in finding_ids]
    for i, fid in enumerate(finding_ids, 1):
        expected = f"F-{i}"
        if fid != expected:
            findings.append({
                "rule": "DM-4",
                "severity": "LOW",
                "message": f"Finding ID gap or misnumber: found {fid}, expected {expected}",
                "location": design_path,
            })
            break

    # DM-5: Decision IDs are sequential (AD-1, AD-2, ...)
    decision_ids = re.findall(r"### (AD-\d+):", content)
    for i, did in enumerate(decision_ids, 1):
        expected = f"AD-{i}"
        if did != expected:
            findings.append({
                "rule": "DM-5",
                "severity": "LOW",
                "message": f"Decision ID gap or misnumber: found {did}, expected {expected}",
                "location": design_path,
            })
            break

    # DM-6: Standard IDs are sequential (S-1, S-2, ...)
    # Match S-N IDs in heading format (references/standards.md) or table format (design.md)
    standard_ids = re.findall(r"(?:^### (S-\d+):|^\| (S-\d+) \|)", content, re.MULTILINE)
    standard_ids = [h or t for h, t in standard_ids]
    for i, sid in enumerate(standard_ids, 1):
        expected = f"S-{i}"
        if sid != expected:
            findings.append({
                "rule": "DM-6",
                "severity": "LOW",
                "message": f"Standard ID gap or misnumber: found {sid}, expected {expected}",
                "location": design_path,
            })
            break

    return {
        "pass": len(findings) == 0,
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Design skill mechanical validation.")
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
