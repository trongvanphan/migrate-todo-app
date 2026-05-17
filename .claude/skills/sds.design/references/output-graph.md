# Output: Graph Backend

Reads FR and NFR nodes from the planning graph via the `sds` CLI. Writes Finding, Decision, and Standard nodes, then exports `spec-driven/<slug>/design.md` for human review. Requires `sds` and `dolt` in PATH (detected in Phase 0).

**CLI command status**: Read commands (`sds query frs`, `sds query nfrs`, `sds query content`, `sds check all`, `sds export`) exist (Phase 1). Write commands for design-stage node types (`sds write finding`, `sds write decision`, `sds write standard`) and query commands (`sds query findings`, `sds query decisions`, `sds query standards`) are Phase 2 CLI deliverables (sds-cli issue #2). They follow the established `sds write <type>` / `sds query <type>` patterns.

## Reading the Spec

Query FR, NFR, and spec-stage Constraint/Assumption/Risk nodes from the graph:

```bash
sds query frs --slug "<slug>" --project-root "<project-root>" --format json
sds query nfrs --slug "<slug>" --project-root "<project-root>" --format json
sds query constraints --slug "<slug>" --project-root "<project-root>" --format json
sds query assumptions --slug "<slug>" --project-root "<project-root>" --format json
sds query risks --slug "<slug>" --project-root "<project-root>" --format json
```

FR and NFR queries use existing Phase 1 commands. Constraint/Assumption/Risk queries are Phase 2 CLI deliverables (same `sds query <type>` pattern).

Parse the returned JSON for identifiers, priorities, descriptions, and relationships. Spec-stage Constraints, Assumptions, and Risks inform research scope and must be respected by design decisions.

If FR and NFR queries both return empty results, stop with guidance: "No spec data found in graph for slug '[slug]'. Run `/spec` to create one first." Empty Constraint/Assumption/Risk results are normal — not all specs have them.

## CLI Failure Handling

Every `sds` command can fail. Apply these fallbacks:

| Command | Failure Fallback |
| --- | --- |
| `sds query` | Fall back to markdown backend for this design. Update the session sidecar to record `backend: "markdown"` (overriding Phase 0 detection). Inform the user: "Graph query failed — falling back to markdown backend." Read `spec-driven/<slug>/spec.md` instead. Load `references/output-markdown.md` as the write reference. Use `references/design-validation-criteria-markdown.md` for validation. Any nodes already written to the graph before the failure are orphaned — do not attempt cleanup. Proceed with markdown output. The sidecar records `backend: "markdown"` — downstream skills read from markdown, not the graph. Orphaned graph nodes do not affect downstream skills because the sidecar backend field takes precedence. |
| `sds write` | Retry once. If the retry fails, skip the node write, log which node was skipped, and continue. Note skipped nodes in the completion summary. |
| `sds write edge` | Retry once. If the retry fails, skip the edge, log which edge was skipped, and continue. Skipped edges degrade provenance but do not block the design. |
| `sds export` | Retry once. If the retry fails, fall back to markdown backend: generate `spec-driven/<slug>/design.md` directly from session data using the design template in output-markdown.md. |
| `sds check all` | Retry once. If the retry fails, skip mechanical validation and proceed to qualitative validation only. Note: "Mechanical checks unavailable — graph validation skipped." If the qualitative validator also fails, apply the overall validation fallback from SKILL.md (proceed to Design Review with warning: "Both validation layers unavailable — review the design manually."). |

## Node Writing Pattern

All node writes use JSON on stdin. Each write returns a JSON response with the assigned `id` — capture it for edge creation.

```bash
sds write <type> --slug "<slug>" --project-root "<project-root>" <<'JSON'
{"field": "value"}
JSON
```

Edges use flags:

```bash
sds write edge --slug "<slug>" --project-root "<project-root>" --from <type>:<id> --to <type>:<id> --type <edge-type>
```

Write order: nodes before the edges that reference them.

## Writing Findings

For each finding:

```bash
sds write finding --slug "<slug>" --project-root "<project-root>" <<'JSON'
{
  "source": "codebase",
  "content": "The existing auth module uses JWT with 15-minute expiry and opaque refresh tokens stored in the sessions table.",
  "confidence": "high",
  "references": []
}
JSON
```

Valid `source` values: `codebase` (observed in files), `web_research` (found via documentation/article search), `training_knowledge` (model knowledge when search unavailable), `spec` (derived from the spec document — assigned by the orchestrator during the rich-context flow, not by subagents). The `references` field is an optional JSON array of URLs or file paths — include for `web_research` findings to cite the source.

Response: `{"type": "finding", "id": 1, ...}`. Capture `id`.

Link each finding to the FR or NFR that triggered the research:

```bash
sds write edge --slug "<slug>" --project-root "<project-root>" --from finding:<finding_id> --to fr:<fr_id> --type discovered-from
```

## Writing Decisions

For each architecture decision:

```bash
sds write decision --slug "<slug>" --project-root "<project-root>" <<'JSON'
{
  "title": "Use JWT with refresh tokens",
  "question": "How should we handle session management?",
  "chosen_approach": "JWT access tokens (15min) + opaque refresh tokens (7d)",
  "rationale": "Short-lived JWTs enable local validation without hitting the API on every request. Refresh tokens use the DB for revocation.",
  "alternatives_considered": "Session cookies (rejected: no API consumer support), long-lived JWTs (rejected: no revocation path)"
}
JSON
```

Response: `{"type": "decision", "id": 1, ...}`. Capture `id`.

Link each decision to the findings that informed it:

```bash
sds write edge --slug "<slug>" --project-root "<project-root>" --from decision:<decision_id> --to finding:<finding_id> --type informed-by
```

## Writing Standards

For each standard:

```bash
sds write standard --slug "<slug>" --project-root "<project-root>" <<'JSON'
{
  "domain": "security",
  "rule": "Use parameterized queries for all database access",
  "file_type": ".ts",
  "action_type": "*",
  "source_document": "auth-service/CLAUDE.md"
}
JSON
```

Standards do not require edges — they are matched to steps downstream via `file_type` and `action_type` JOINs.

## Writing Constraints (Technical)

For each technical constraint discovered during research (supplements spec-stage constraints):

```bash
sds write constraint --slug "<slug>" --project-root "<project-root>" <<'JSON'
{
  "description": "Database uses row-level locking — bulk updates must be batched",
  "category": "technical",
  "source": "codebase",
  "rationale": "Discovered in src/db/connection.ts",
  "provenance": "[Codebase]"
}
JSON
```

Link to constrained FRs: `sds write edge --slug "<slug>" --project-root "<project-root>" --from constraint:<id> --to fr:<fr_id> --type constrains`

## Writing Assumptions

For each assumption made during design:

```bash
sds write assumption --slug "<slug>" --project-root "<project-root>" <<'JSON'
{
  "description": "Existing auth middleware supports JWT validation",
  "source": "design",
  "provenance": "[Codebase]"
}
JSON
```

Link to affected FRs: `sds write edge --slug "<slug>" --project-root "<project-root>" --from assumption:<id> --to fr:<fr_id> --type affects`

## Writing Risks (Technical)

For each technical risk identified during research (supplements spec-stage risks):

```bash
sds write risk --slug "<slug>" --project-root "<project-root>" <<'JSON'
{
  "description": "No existing test patterns for async event handlers",
  "impact": "Medium",
  "probability": "High",
  "source": "codebase",
  "mitigation": "Create test utility based on src/test/helpers.ts pattern",
  "provenance": "[Codebase]"
}
JSON
```

Link to affected FRs: `sds write edge --slug "<slug>" --project-root "<project-root>" --from risk:<id> --to fr:<fr_id> --type affects`

## Write Sequence

Write all nodes and edges in this order:

1. All Finding nodes
2. All `discovered-from` edges (Finding → FR/NFR)
3. All Decision nodes
4. All `informed-by` edges (Decision → Finding)
5. All Standard nodes
6. All Constraint nodes (design-stage, `source: "codebase"` or `source: "technical"`)
7. All `constrains` edges (Constraint → FR)
8. All Assumption nodes (design-stage, `source: "design"`)
9. All `affects` edges (Assumption → FR)
10. All Risk nodes (design-stage, `source: "codebase"` or `source: "research"`)
11. All `affects` edges (Risk → FR)

## Export

After writing all nodes and edges, export to design.md for human review:

```bash
sds export --format md --slug "<slug>" --project-root "<project-root>" --output "spec-driven/<slug>/design.md"
```

The exported design.md must include these sections in order: Overview, Technical Approach, Findings, Architecture Decisions, Resolved Uncertainties, Standards, File Inventory, Dependencies and Coupling, Spec Deviations, Open Questions, Constraints (Technical), Assumptions, Risks (Technical), References. This list is the authoritative section order for graph export.

After the export, generate references/ files by querying the graph for detailed data:
- `spec-driven/<slug>/references/research.md` — query all findings grouped by aspect, include approach evaluations and resolved uncertainties
- `spec-driven/<slug>/references/standards.md` — query all standard nodes with full metadata
- `spec-driven/<slug>/references/contracts.md` — optional, only when API-related decisions exist

Update the sidecar at `spec-driven/.sessions/<slug>.design.json` after the export.

Emit: `Design written to spec-driven/<slug>/design.md`

## Finalization

Finalization steps are defined in SKILL.md under the Design Review gate. The graph backend's finalization runs the final export with `status: final` metadata.

The exported `spec-driven/<slug>/design.md` is the human-readable artifact. The graph is the authoritative source — downstream skills (`/task`) read from it.

## Validation

### Mechanical checks (Layer 1)

Run: `python "<skill-directory>/scripts/validate.py" --slug "<slug>" --project-root "<project-root>"` where `<skill-directory>` is the directory containing the design SKILL.md.

Returns standard validation JSON (`{"pass": bool, "findings": [...]}`). The graph backend calls `sds check all` to verify required fields, edge resolution, and provenance chain integrity.

### Qualitative validation (Layer 2)

Delegate to a subagent. The subagent reads [design-validation-criteria-graph.md](design-validation-criteria-graph.md) as its first action, then queries the graph via `sds` CLI using the slug and project-root. The subagent walks provenance chains (FR→Finding→Decision) individually via graph queries, not by reading the exported markdown.

Expected output: Validator Schema JSON.

Merge mechanical and qualitative findings before presenting to user.

## Edit Summaries

When the design is updated during the session (after "Adjust" at the review gate):
1. Update the relevant nodes/edges in the graph
2. Re-export to `spec-driven/<slug>/design.md`
3. Present a brief conversational delta:

```
Updated design:
- AD-3: rationale revised based on F-7
- S-4: added (extracted from company ADR)
```

Conversational only — NOT written to the graph.
