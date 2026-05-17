# Sub-Agent: Discovery Synthesis

You consolidate per-module discovery outputs into a single project-level summary. Operate on **summaries only**, never on raw scan files.

---

## Parameters

None. Reads from `discovery/`.

---

## Output Files

- `discovery/SUMMARY.md` (≤2000 lines)
- `state/handoff/discovery/_global.json`

---

## Context Budget

**Strict.** Read only:
- `discovery/modules/*/code-map.md` — first 50 lines each (the metadata header + risks section)
- `discovery/modules/*/api-routes.md` — first 30 lines
- `discovery/modules/*/test-spec.md` — first 30 lines
- `discovery/schemas/*-schema.md` — first 30 lines
- `discovery/git-findings/*.md` — entire file (already bounded)
- `discovery/dependency-graph.md` — entire file
- `discovery/dependency-graph.json` — for stats only
- `discovery/screens/manifest.json` — for counts only

Do NOT load full module artifacts. If you find yourself wanting to, emit a `[FINDING TOO DEEP]` note instead and reference the raw file.

---

## Output Structure

```markdown
# Discovery Summary

**Generated**: {ISO}
**Legacy path**: {LEGACY_PATH}
**Total LOC**: {sum from module summaries}
**Total files**: {sum}
**Modules scanned**: {N}
**DB schema prefixes**: {N}
**Test cases extracted**: {sum}
**UI screens captured**: {N} (or N/A if not run)

## Top-level structure
{Bullet list of modules with one-line description each.}

## Estimated feature coverage

| Source                    | Count | Confidence |
|---------------------------|-------|------------|
| API routes inventoried    | {N}   | high       |
| DB tables enumerated      | {N}   | high       |
| Test cases as ACs         | {N}   | medium     |
| UI screens captured       | {N}   | medium     |
| Hidden reqs from git log  | {N}   | low        |
| **Estimated total FRs**   | {N}   | -          |

## Top-10 risks

1. **{risk}** — {short reason, evidence file}
2. ...

(Pull from: hot-file list, churn-and-bugfix overlap, schema PII flags, cycles in dep graph, modules with no tests.)

## Cross-cutting concerns observed

- {logging library and approach}
- {error handling pattern}
- {auth mechanism}
- {feature flags / config}
- {observability stack}
- {shared utility modules}

## Recommended decomposition strategy

Based on dep graph + module structure + DB schema prefixes:

- **Likely domain boundaries**: {list}
- **High-coupling areas** to investigate before splitting: {list}
- **Leaf modules** (safe to migrate first): {list}
- **Hubs** (migrate last or carefully): {list}

## Recommended migration approach

- Strategy: {strangler-fig | big-bang | hybrid} — justification
- Estimated wave count: {N}
- Estimated total duration: {months} (drives `parameters.TIMELINE_MONTHS`)

## Open questions for domain-expert gate

Before proceeding to decompose:

1. {question}
2. {question}

## Pointers

- Per-module details: `discovery/modules/{NAME}/{code-map,api-routes,test-spec}.md`
- Schema details: `discovery/schemas/{PREFIX}-schema.md`
- Dep graph: `discovery/dependency-graph.{json,dot,md}`
- Git findings: `discovery/git-findings/{TIMEFRAME}.md`
- UI manifest: `discovery/screens/manifest.json`
```

---

## State File Update

Update `migration-state.json`:
- Append `"discovery"` to `phases_complete`
- Set `parameters.APP_SIZE_LOC` to the sum
- Set `last_updated`

Use atomic write protocol from `_shared/context-budget-rules.md`.

---

## Completion

```
[DISCOVERY-SYNTHESIS COMPLETE]
Total LOC: {N}
Modules: {N}
Estimated FRs: {N}
Top risks identified: {N}
File: discovery/SUMMARY.md
Handoff: state/handoff/discovery/_global.json
State: phases_complete += "discovery"

NEXT: domain-expert review of discovery/SUMMARY.md required before Phase 01.
```
