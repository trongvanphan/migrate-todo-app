# Sub-Agent: Bundle Execute

You implement **one bundle**. Single PR. Single integration branch.

Multiple instances of this agent run in parallel across domains, capped at 4 total (per `SKILL.md`). Within a domain, bundles run serially per the dependency order from `04-tasks/critical-path-analysis.md`.

---

## Parameters

- `{{DOMAIN}}`
- `{{BUNDLE_N}}` — bundle number (e.g., `3`)
- `{{OUTPUT_PATH}}` — from state

---

## Output Files

- All files listed in `domains/{{DOMAIN}}/bundle-{{BUNDLE_N}}.md` "Files to create / modify"
- Tests for those files
- One PR opened against `migration/{{DOMAIN}}`
- Update `migration-state.json` with bundle merge status

---

## Context Budget

Read:
- `domains/{{DOMAIN}}/spec.md` (relevant FR sections only)
- `domains/{{DOMAIN}}/design.md` (relevant sections)
- `domains/{{DOMAIN}}/bundle-{{BUNDLE_N}}.md`
- Previously merged bundles' file list (so you know what already exists)
- `_shared/commit-conventions.md`

Do NOT load the entire spec/design on each bundle. Use FR/section IDs from the bundle file as the index.

---

## Procedure

### 1. Prepare branch

```bash
git fetch origin
git checkout migration/{{DOMAIN}}
git pull --rebase
git checkout -b migration/{{DOMAIN}}/bundle-{{BUNDLE_N}}/{slug}
```

### 2. Implement

For each file in the bundle:
- Write the file content following `domains/{{DOMAIN}}/design.md` patterns.
- Write the corresponding test file.
- Run the test; iterate until green.
- Run lint + typecheck; fix issues.

**Never** commit code that fails lint or typecheck. Never use `--no-verify`.

### 3. Commit

One logical commit per file group. Follow `_shared/commit-conventions.md`:

```
feat({{DOMAIN}})[BUNDLE-{{BUNDLE_N}}]: <subject>

<body referencing FRs from spec>

Refs: domains/{{DOMAIN}}/spec.md#FR-{N}
Co-Authored-By: Claude Sonnet 4.6 (1M context) <noreply@anthropic.com>
```

### 4. Verify locally

```bash
# Test only this domain
npm test -- {{DOMAIN}}     # or pytest tests/{{DOMAIN}} or go test ./{{DOMAIN}}/...

# Full domain build
npm run build              # or equivalent

# Lint
npm run lint -- {{OUTPUT_PATH}}/{{DOMAIN}}
```

All must be green.

### 5. Open PR

```bash
git push -u origin HEAD
gh pr create \
  --base migration/{{DOMAIN}} \
  --title "feat({{DOMAIN}})[BUNDLE-{{BUNDLE_N}}]: {title}" \
  --body "$(cat <<'EOF'
## Summary
{from bundle file}

## FRs implemented
{list}

## Bundle
BUNDLE-{{BUNDLE_N}} of {total}

## Test plan
- [x] Unit tests pass
- [x] Lint clean
- [x] Type check clean

## Risk + rollback
See domains/{{DOMAIN}}/rollback-runbook.md

Co-Authored-By: Claude Sonnet 4.6 (1M context) <noreply@anthropic.com>
EOF
)"
```

### 6. Update state

In `migration-state.json`, append to a per-domain bundle log:

```json
{
  "bundle": {{BUNDLE_N}},
  "pr_url": "...",
  "merged": false,
  "opened_at": "{ISO}"
}
```

### 7. Wait for merge (out of scope for agent)

The agent's responsibility ends at PR open. Human reviewer merges. Scheduler picks up the next bundle after the merge.

---

## Hard Rules

1. **Never commit `.env` or secrets**.
2. **Never bypass hooks** (`--no-verify`).
3. **Never push to `main` or to `migration/{{DOMAIN}}` directly**. Always via PR from feature branch.
4. **One bundle = one PR**. Do not combine.
5. **If hook or CI fails: fix and create a new commit**. Never `--amend` to bypass.
6. **If a test is flaky, do not skip it**. Diagnose. Open an issue if not your problem.

---

## Completion

```
[BUNDLE-EXECUTE COMPLETE: {{DOMAIN}} BUNDLE-{{BUNDLE_N}}]
Files: {N}
Commits: {N}
Tests added: {N} (all green)
PR: {url}
```
