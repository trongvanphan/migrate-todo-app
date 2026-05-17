# Sub-Agent: Domain Tasks

You decompose `{{DOMAIN}}`'s design into executable bundles. Each bundle is one PR-sized unit of work with a clear definition of done.

---

## Parameters

- `{{DOMAIN}}`

---

## Output Files

- `domains/{{DOMAIN}}/tasks.md` — bundle index
- `domains/{{DOMAIN}}/bundle-{N}.md` per bundle
- `state/handoff/tasks/{{DOMAIN}}.json`

---

## Context Budget

Read:
- `domains/{{DOMAIN}}/spec.md`
- `domains/{{DOMAIN}}/design.md`
- `domains/{{DOMAIN}}/data-migration.md` (for any DB-related bundles)
- `domains/_contracts.yaml` (filter to this domain)

---

## Bundle rules

- One bundle = one PR.
- Bundle size: aim for 200–800 LOC of net code change (excluding tests).
- Bundle should land independently green: tests pass after just this bundle merges.
- Order matters: foundational bundles first (types, infra, then handlers).
- Max 15 bundles per domain. If you produce more, the domain likely needs feature-split (re-run feature-spec).

---

## Standard bundle ordering

1. **Bundle 1 — Scaffolding**: package, build config, CI workflow, observability infra, base error types.
2. **Bundle 2 — Domain types**: value objects, domain events, schema.prisma / ORM models.
3. **Bundle 3 — Repositories**: data access layer, with unit tests using in-memory DB.
4. **Bundles 4..M — Services per FR group**: one bundle per epic, each producing services + tests.
5. **Bundles (M+1)..N — API handlers**: HTTP/gRPC handlers per contract; one bundle per contract.
6. **Bundle N+1 — Outbound adapters**: clients for other domains' contracts.
7. **Bundle N+2 — Fixtures & seed data**.
8. **Bundle N+3 — Integration tests**.

---

## Output: `domains/{{DOMAIN}}/tasks.md`

```markdown
# Tasks — {{DOMAIN}}

**Bundles**: {N}
**Estimated effort**: {person-days total}
**Critical path** (see critical-path.md): {bundles on critical path}

| # | Title | Files (LOC est) | FRs | Depends on | Owner | Est days |
|---|-------|-----------------|-----|------------|-------|----------|
| 1 | Scaffolding | ~12 / 400 | — | — | @alice | 2 |
| 2 | Domain types | ~8 / 300 | FR-1 | 1 | @alice | 1 |
| ... |

Total: {N} bundles, {sum} files, {sum} LOC, {sum} days.
```

---

## Output: `domains/{{DOMAIN}}/bundle-{N}.md`

```markdown
# Bundle {N} — {Title}

**Domain**: {{DOMAIN}}
**Estimated LOC**: {net}
**Estimated effort**: {person-days}
**Owner**: {assignee}
**Depends on bundles**: {list}
**FRs delivered**: {list}

## Files to create / modify

- `path/to/file.ts` — purpose
- `path/to/file.test.ts` — what it tests
- ...

## Acceptance criteria

- [ ] All files in list exist and compile
- [ ] Tests in this bundle pass
- [ ] Full domain test suite still passes
- [ ] Lint and typecheck clean
- [ ] PR opened against `migration/{{DOMAIN}}` with title `feat({{DOMAIN}})[BUNDLE-{N}]: {title}`

## Implementation notes
{Anything non-obvious: ordering within the bundle, gotchas, references to specific design decisions}

## Test plan

- Unit tests: {files}
- Integration tests: {files}
- Manual smoke: {if applicable}

## Out of scope

Explicit list of things NOT in this bundle (to prevent scope creep).

## Rollback

If this bundle merge breaks the integration branch:
1. Revert the merge commit.
2. Triage; reopen as a new bundle if needed.
```

---

## State / Handoff

- Update `domains[{{DOMAIN}}].status = "tasks"`.
- Handoff with bundle count + person-day total.

---

## Completion

```
[DOMAIN-TASKS COMPLETE: {{DOMAIN}}]
Bundles: {N}
Person-days: {sum}
Files: domains/{{DOMAIN}}/tasks.md + bundle-*.md
NEXT: critical-path-analysis.md
```
