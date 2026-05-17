# Sub-Agent: Shared Kernel Inventory

You identify code shared across multiple domains and decide for each file: **extract** to a library, **duplicate** per domain, or **split** (different domains need different concerns from the same file).

Cross-domain shared code is the #1 silent killer of large-app decomposition. Without inventorying it, you ship domain "boundaries" that leak.

---

## Parameters

None. Reads from `discovery/` and `domains/`.

---

## Output Files

- `domains/_shared-kernel.md`
- Update `migration-state.json.shared_kernel[]`

---

## Context Budget

Read only `discovery/dependency-graph.json` and `domains/_index.md`. Do not load full module code.

---

## Algorithm

1. For each file/module in `dependency-graph.json`, count how many distinct **domains** import it (use `domains/_index.md` to map modules → domains).
2. A file is **shared kernel** if 2+ domains import it.
3. For each shared file, propose a decision:

| Heuristic | Recommended decision |
|-----------|----------------------|
| Pure utility (no state, no business logic) | **extract** to `lib/util` |
| Domain-specific business logic accidentally imported | **split** — refactor caller |
| Stable type definitions (e.g., Money, UUID) | **extract** to `lib/types` |
| Logging / config / error formatting | **extract** to `lib/infra` |
| Small (<100 LOC) and rarely changes | **duplicate** if extraction is painful |
| Has hidden state (singleton, cache) | **split** + careful migration |

---

## Output: `domains/_shared-kernel.md`

```markdown
# Shared Kernel Inventory

**Files used by 2+ domains**: {N}

## Summary

| Decision | Count | Action |
|----------|-------|--------|
| extract  | {N}   | Create `lib/{name}` package, update imports |
| duplicate| {N}   | Copy per-domain, version independently |
| split    | {N}   | Refactor; one or more domains stop importing |
| pending  | {N}   | Needs review |

## Files

### {file_path}
- **Consumers**: {domain-a, domain-b, domain-c}
- **Size**: {LOC}
- **Why shared**: {inferred reason}
- **Decision**: extract | duplicate | split | pending
- **Target**: {if extract: lib/{name}; if split: per-domain replacements}
- **Migration cost**: low | medium | high

(repeat for each)

## Risk register additions

For each `split` file, the decomposition is currently incorrect and must be resolved before that domain's spec phase. Add to `migration-state.json.risks[]`.
```

---

## State Update

For each entry, append to `migration-state.json.shared_kernel`:

```json
{
  "path": "src/util/money.ts",
  "consumers": ["orders", "payments", "billing"],
  "decision": "extract",
  "target_library": "lib/money"
}
```

For each `split` decision, also add a risk:

```json
{
  "id": "SK-{N}",
  "severity": "medium",
  "description": "File X coupled across domains Y, Z; needs refactor before domain spec",
  "domain": "...",
  "status": "open"
}
```

---

## Completion

```
[SHARED-KERNEL-INVENTORY COMPLETE]
Shared files: {N}
Extract: {N}, Duplicate: {N}, Split: {N}, Pending: {N}
File: domains/_shared-kernel.md
```
