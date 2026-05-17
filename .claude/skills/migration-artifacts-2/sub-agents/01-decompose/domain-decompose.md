# Sub-Agent: Domain Decompose

You read `discovery/SUMMARY.md` and `discovery/dependency-graph.json`, then split the legacy app into 5–15 bounded domains (DDD-style).

---

## Parameters

None. Reads from `discovery/`.

---

## Output Files

- `domains/_index.md` — top-level domain inventory
- `domains/{{DOMAIN}}/charter.md` for each detected domain (use `templates/domain-charter.md` as template)
- Update `migration-state.json.domains[]`

---

## Context Budget

Read only:
- `discovery/SUMMARY.md`
- `discovery/dependency-graph.json` (parse stats, not full graph)
- `domains/_index.md` if it already exists (resume case)

---

## Heuristics

A domain is a cohesive group that:
1. Shares a database schema prefix or related entities.
2. Has a clear team / ownership boundary.
3. Has bounded I/O via a small contract surface to other domains.
4. Can be deployed independently.

Signals to split:
- Different schema prefix → different domain.
- Low cross-module imports → natural boundary.
- Different release cadence → independent domain.

Signals to merge:
- Always-co-edited files (high git churn correlation).
- Shared mutable state.
- Tightly coupled in dep graph (high edge weight + bidirectional).

Caps:
- Minimum 3 domains (for large-app path).
- Maximum 15. If you find more, merge related ones; flag in notes.
- Auth is almost always its own domain.

---

## Output: `domains/_index.md`

```markdown
# Domain Index

**Total domains**: {N}
**Decomposition rationale**: {one paragraph}

| # | Domain | LOC | Schema prefix | Charter | Status |
|---|--------|-----|---------------|---------|--------|
| 1 | auth | 120k | auth_, sess_ | charter.md | pending |
| 2 | customers | 240k | cust_ | charter.md | pending |
| ... |

## Notes
- Shared-kernel candidates: see `_shared-kernel.md` (next agent).
- Domains exceeding 200K LOC must use feature-spec.md: {list}.
- Cycles in dep graph that block clean decomposition: {list, references}.
```

## Output: `domains/{{DOMAIN}}/charter.md`

Use `templates/domain-charter.md` and fill in. Include:
- Purpose (1 sentence)
- LOC, file count
- Inbound contracts (what this domain exposes)
- Outbound contracts (what this domain consumes)
- Data ownership (schema/tables)
- Team owner (placeholder if not yet known)
- Risk score (LOW | MEDIUM | HIGH) with justification

---

## State File Update

Append each domain to `migration-state.json.domains[]`:

```json
{
  "name": "{{DOMAIN}}",
  "status": "pending",
  "loc": N,
  "feature_split": false,
  "dependencies": ["other-domain"],
  "owner_team": null,
  "blockers": []
}
```

If `loc > 200000`, set `feature_split: true` and add comment "requires feature-spec.md decomp".

Append `"decompose"` to `phases_complete` only after ALL domain charters are written.

---

## Completion

```
[DOMAIN-DECOMPOSE COMPLETE]
Domains: {comma-separated list}
Feature-split required: {list of domains > 200K LOC}
Files: domains/_index.md, domains/{DOMAIN}/charter.md (×{N})

NEXT: shared-kernel-inventory.md, contract-registry.md, team-ownership-map.md, migration-order.md
HUMAN GATE: domain expert reviews domains/_index.md and each charter before Phase 02.
```
