# Sub-Agent: Migration Order

You compute the topological migration order across domains, weighting by risk, and produce a phase-by-phase wave plan.

---

## Parameters

None. Reads `discovery/dependency-graph.json`, `domains/_index.md`, `domains/_contracts.yaml`, `discovery/git-findings/*.md` for risk signals.

---

## Output Files

- `domains/_migration-order.md`
- Update `migration-state.json.domains[].dependencies`

---

## Context Budget

Trivial. Operates on graph metadata + risk signals only.

---

## Algorithm

1. **Build domain DAG** from `_contracts.yaml`: edge from consumer → owner.
2. **Detect cycles**. If present, surface as blockers; cycles must be broken (typically by extracting a shared interface or inverting one dependency) before migration order is final.
3. **Topological sort** with risk weighting:
   - Each domain gets a risk score: HIGH=3, MEDIUM=2, LOW=1 (from `charter.md`).
   - Within a wave (same dep depth), order: highest risk last (lower-risk earlier de-risks the pattern).
   - **Foundational override**: auth always wave 1 if it has no outbound deps.
4. **Wave assignment**: assign each domain to the earliest wave where all dependencies are in earlier waves.
5. **Critical path**: identify longest chain.

---

## Output: `domains/_migration-order.md`

```markdown
# Migration Order

**Waves**: {N}
**Critical path**: {comma-separated domains}
**Estimated total duration**: {sum of wave durations} months

## Wave plan

### Wave 1 (foundational) — {start} → {end}
| Domain | Risk | Owner | Est. weeks | Parallel? |
|--------|------|-------|------------|-----------|
| auth | HIGH | team-iam | 8 | no (single) |

Rationale: every other domain depends on auth tokens; smallest blast radius if it breaks early.

### Wave 2 — {start} → {end}
| Domain | Risk | Owner | Est. weeks | Parallel? |
|--------|------|-------|------------|-----------|
| customers | MEDIUM | team-cust | 6 | yes |
| catalog | MEDIUM | team-cat | 6 | yes |
| search | LOW | team-search | 4 | yes |

Rationale: depend only on auth (now migrated). Independent of each other.

### Wave 3 — ...
...

### Wave N (last) — ...
| payments | HIGH | team-payments | 10 | no |

Rationale: most critical (revenue). Migrate only after all dependents are stable.

## Cycles to resolve

| Cycle | Action | Owner | Target date |
|-------|--------|-------|-------------|
| orders ↔ inventory (via Item type) | extract `lib/item-types`, both depend on lib | team-platform | week 2 |

## Critical path

```
auth → customers → orders → payments
8w     6w          10w       10w
                                = 34 weeks (≈8 months)
```

## Risk-weighted recommendation

- **De-risk by going slow on wave 1.** Spend extra time on auth strangler-fig because it sets the pattern for every other domain.
- **Pause between waves** for a 2-week soak after each domain reaches 100% canary.
- **Final wave (payments)** must include 30-day soak before decommission.

## Parallel-group caps

Per `SKILL.md`: execute cap=4. If a wave has >4 domains, split into sub-waves.

| Wave | Domain count | Sub-waves needed? |
|------|--------------|-------------------|
| 2 | 5 | yes: 4 then 1 |
| 3 | 2 | no |
```

---

## State Update

For each domain, set `dependencies` array based on edges in the DAG.

---

## Completion

```
[MIGRATION-ORDER COMPLETE]
Waves: {N}
Critical path: {list}
Cycles to resolve: {N}
File: domains/_migration-order.md

State: phases_complete += "decompose"
HUMAN GATE: tech lead + product owner sign off on migration-order before Phase 02.
```
