---
name: migration
description: Full SDS migration orchestration skill for any legacy app. Guides Claude through the 7-phase pipeline: discovery → domain-decompose → spec → design → tasks → execute → verify. Invoke with /migration.
---

# Migration Orchestration Skill

You are orchestrating a **Spec-Driven Development (SDS) migration** of a legacy application to a modern stack. Follow this 7-phase pipeline exactly. Do not skip phases. Each phase has a gate — you must confirm output exists before proceeding.

---

## Pre-Made Decisions (fill in at invocation time)

Before starting any phase, ask the user (or read from the task description) for these values. Store them and reference them throughout:

```
LEGACY_PATH:   <absolute path to legacy source app>
OUTPUT_PATH:   <absolute path for generated new app>
APP_SIZE:      small | large
  - small: 1-2 domains, skip discovery, run phases 1-5 once
  - large: 3+ domains, run full 7-phase pipeline with parallel domain execution
DOMAINS:       <comma-separated list, or "auto" to derive from domain-decompose>
TECH_STACK:    <JSON object — see format below>
```

### TECH_STACK format

```json
{
  "language": "TypeScript",
  "runtime": "Node 20",
  "framework": "Next.js 14",
  "state": "Zustand",
  "auth": "NextAuth.js",
  "database": "PostgreSQL + Prisma",
  "testing": "Vitest + Playwright",
  "deployment": "Vercel",
  "notes": "App Router, server components by default"
}
```

Adjust for your actual stack. Every field is optional — include only what's relevant.

---

## Phase Gates

After each phase, check that the required output files exist before moving to the next phase. If a file is missing, re-run the phase. Never silently skip.

---

## Phase 0 — Discovery (large apps only)

**Skip if** `APP_SIZE=small`. For small apps, jump to Phase 1.

**Dispatch a sub-agent** using `migration-artifacts/sub-agents/discovery.md` with `{{LEGACY_PATH}}` substituted.

**Gate**: All of these files must exist before proceeding:
- `discovery/code-map.md`
- `discovery/api-routes.md`
- `discovery/db-schema.md`
- `discovery/test-as-spec.md`
- `discovery/git-log-findings.md`

---

## Phase 0.5 — Domain Decompose (large apps only)

**Skip if** `APP_SIZE=small` or `DOMAINS` is already provided.

**Dispatch a sub-agent** using `migration-artifacts/sub-agents/domain-decompose.md` with `{{LEGACY_PATH}}` substituted.

**Gate**: `discovery/domain-map.md` must exist. Read it and set `DOMAINS` from the output.

---

## Phase 1 — Spec (per domain)

For each domain in `DOMAINS`, **dispatch a sub-agent** using `migration-artifacts/sub-agents/spec.md` with:
- `{{DOMAIN}}` = domain name
- `{{LEGACY_PATH}}` = legacy path

For **large apps**, dispatch all domain spec sub-agents **in parallel**.

**Gate per domain**: `spec-driven/{{DOMAIN}}/spec.md` must exist.

---

## Phase 2 — Design (per domain)

For each domain, **dispatch a sub-agent** using `migration-artifacts/sub-agents/design.md` with:
- `{{DOMAIN}}` = domain name
- `{{TECH_STACK}}` = the JSON object from Pre-Made Decisions

For **large apps**, dispatch all domain design sub-agents **in parallel**.

**Gate per domain**: `spec-driven/{{DOMAIN}}/design.md` must exist.

---

## Phase 3 — Tasks (per domain)

For each domain, **dispatch a sub-agent** using `migration-artifacts/sub-agents/tasks.md` with:
- `{{DOMAIN}}` = domain name

For **large apps**, dispatch all domain task sub-agents **in parallel**.

**Gate per domain**: `spec-driven/{{DOMAIN}}/tasks.md` must exist, and at least one `spec-driven/{{DOMAIN}}/bundle-*.md` must exist.

---

## Phase 4 — Execute (per domain)

For each domain, **dispatch a sub-agent** using `migration-artifacts/sub-agents/execute.md` with:
- `{{DOMAIN}}` = domain name
- `{{OUTPUT_PATH}}` = output path

For **large apps with independent domains**, you may dispatch execution sub-agents in parallel if the domains have no shared code dependencies. If domains share types or utilities, execute the foundational domain first, then parallelize the rest.

**Gate per domain**: The code files referenced in the bundle must exist at `{{OUTPUT_PATH}}`. At least one passing test must exist.

---

## Phase 5 — Verify (per domain)

For each domain, **dispatch a sub-agent** using `migration-artifacts/sub-agents/verify.md` with:
- `{{DOMAIN}}` = domain name

For **large apps**, dispatch all verification sub-agents **in parallel**.

**Gate per domain**: `spec-driven/{{DOMAIN}}/verify-report.md` must exist with no unresolved CRITICAL findings.

---

## Final Synthesis

After all domains complete verification:

1. Run the full test suite: `npm test` or equivalent.
2. Run the linter: `npm run lint` or equivalent.
3. Print a summary table:

```
| Domain   | Spec | Design | Tasks | Execute | Verify | Status |
|----------|------|--------|-------|---------|--------|--------|
| auth     |  ✓   |   ✓    |   ✓   |    ✓    |   ✓    |  DONE  |
| tasks    |  ✓   |   ✓    |   ✓   |    ✓    |   ✓    |  DONE  |
```

4. Create a final commit:
```bash
git add -A
git commit -m "feat: complete migration of all domains

Co-Authored-By: Claude Sonnet 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Sub-Agent Dispatch Instructions

When dispatching sub-agents, use the Task tool (or equivalent parallel agent invocation) with these rules:

- Pass the full content of the relevant sub-agent prompt file as the task description.
- Replace all `{{PARAM}}` placeholders before dispatching.
- Set the working directory to the repo root for all sub-agents.
- Collect the output path from each sub-agent and verify the gate before proceeding.

---

## Error Handling

- If a sub-agent fails to produce its output file, retry once with a note: "The previous attempt did not produce the required output. Please try again and ensure you write the file."
- If a test suite has failures after execute, route them to the execute sub-agent for auto-fix before running verify.
- If verify finds CRITICAL findings that cannot be auto-fixed, surface them to the user before proceeding.

---

## Skill Entry Point

When the user invokes `/migration`:

1. Ask for `LEGACY_PATH`, `OUTPUT_PATH`, and `APP_SIZE` if not already provided.
2. Ask for `TECH_STACK` or offer to detect it from the legacy app.
3. Ask for `DOMAINS` or offer to auto-detect via domain-decompose.
4. Confirm all pre-made decisions with the user.
5. Begin Phase 0 (large) or Phase 1 (small).
