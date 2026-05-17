# Migration Artifacts

Reusable artifacts for migrating any legacy application to a modern stack using the **Spec-Driven Development (SDS)** methodology.

These files are **stack-agnostic** and **app-agnostic**. They work for Angular→React, Rails→FastAPI, monolith→microservices, or any other migration.

---

## Folder Structure

```
migration-artifacts/
├── README.md            — This file
├── SKILL.md             — Claude Code skill that orchestrates the full pipeline
├── workflow.md          — Human-readable runbook with decision trees and examples
└── sub-agents/
    ├── discovery.md     — Phase 0: Scan legacy codebase, produce structured findings
    ├── domain-decompose.md — Phase 0.5: Split findings into bounded domains
    ├── spec.md          — Phase 1: Write spec for one domain
    ├── design.md        — Phase 2: Write architecture design for one domain
    ├── tasks.md         — Phase 3: Decompose design into executable task bundles
    ├── execute.md       — Phase 4: Implement all bundles with commit discipline
    └── verify.md        — Phase 5: Verify implementation across 6 dimensions
```

---

## Quick Start

### Option A — Use the Claude Code Skill (recommended)

1. Copy `SKILL.md` into your project's `.claude/skills/migration/SKILL.md`.
2. Open Claude Code in your project.
3. Type `/migration` and follow the prompts.

### Option B — Run sub-agents manually

Each file in `sub-agents/` is a self-contained prompt. Copy it, replace the `{{PARAM}}` placeholders, and paste it into Claude Code as a task.

See `workflow.md` for the full decision tree and step-by-step examples.

---

## The 7-Phase Pipeline

| Phase | Name | Sub-agent | Output |
|-------|------|-----------|--------|
| 0 | Discovery | `discovery.md` | `discovery/` folder |
| 0.5 | Domain Decompose | `domain-decompose.md` | `discovery/domain-map.md` |
| 1 | Spec | `spec.md` | `spec-driven/{domain}/spec.md` |
| 2 | Design | `design.md` | `spec-driven/{domain}/design.md` |
| 3 | Tasks | `tasks.md` | `spec-driven/{domain}/tasks.md` + bundles |
| 4 | Execute | `execute.md` | Working code in target path |
| 5 | Verify | `verify.md` | `spec-driven/{domain}/verify-report.md` |

---

## Parameters You Must Supply

| Parameter | Description | Example |
|-----------|-------------|---------|
| `{{LEGACY_PATH}}` | Absolute path to legacy source app | `/repo/src/legacy-app` |
| `{{DOMAIN}}` | Name of the bounded domain | `auth`, `tasks`, `payments` |
| `{{TECH_STACK}}` | JSON object describing the target stack | See `workflow.md` §6 |
| `{{OUTPUT_PATH}}` | Absolute path for generated code | `/repo/apps/new-app` |

---

## Adapting for Your Project

1. **Different framework**: Change `{{TECH_STACK}}` — the sub-agents adapt their output.
2. **Single domain**: Skip discovery and domain-decompose; go straight to spec.
3. **Multiple domains**: Run spec→design→tasks→execute→verify in parallel per domain.
4. **Monorepo target**: Set `{{OUTPUT_PATH}}` to the correct package directory.

See `workflow.md` for complete examples.
