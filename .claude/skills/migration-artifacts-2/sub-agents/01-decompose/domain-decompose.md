# Sub-Agent: Domain Decompose

You read `discovery/SUMMARY.md` and `discovery/dependency-graph.json`, then declare the legacy app's domain inventory. The inventory may have anywhere from 1 to ~15 domains. Declare what you find — do not invent additional domains to hit a minimum.

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
- Minimum 1 domain. Single-domain inventories are valid for SPAs, CLIs, and single-purpose services.
- Maximum ~15. If you find more, merge related ones; flag in notes.
- When auth exists as a distinct concern with its own data and routes, declare it as its own domain. When auth is tightly fused with a single business surface (e.g. a tiny SPA that wraps Firebase Auth + one feature), it stays inside that domain.

Slug requirement: every domain's name MUST also serve as its sds spec slug. Match `[a-z0-9-]+`, ≤64 chars. Record under `migration-state.json.domains[].spec_slug`.

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
- Shared-kernel candidates: see `_shared-kernel.md` (next agent — skip if single-domain).
- Domains where `/sds.spec` would carry >20 FRs: {list} — recommend per-feature briefings.
- Cycles in dep graph that block clean decomposition: {list, references}.
```

When the inventory has exactly one domain, the next agents in Phase 01 collapse:
- `shared-kernel-inventory.md` — skip (no cross-domain sharing).
- `_migration-order.md` — write a single-line file with the one slug.
- `contract-registry.md` and `team-ownership-map.md` — still run; produce single-row outputs.

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

If the domain's spec would carry >20 FRs (rule of thumb: `loc > 200000` or >5 large sub-areas), set `feature_split: true` so the orchestrator routes Phase 02 through per-feature `/sds.spec` invocations instead of a single one.

Append `"decompose"` to `phases_complete` only after ALL domain charters are written.

---

## Completion

```
[DOMAIN-DECOMPOSE COMPLETE]
Domains: {comma-separated list of slugs}
Feature-split required: {list of slugs flagged as feature_split}
Files: domains/_index.md, domains/{SLUG}/charter.md (×{N})

NEXT (multi-domain): shared-kernel-inventory.md, contract-registry.md, team-ownership-map.md, migration-order.md
NEXT (single-domain): contract-registry.md, team-ownership-map.md, single-row migration-order.md
HUMAN GATE: domain expert reviews domains/_index.md and each charter before Phase 02.
```
