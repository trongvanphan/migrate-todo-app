# Output: Graph Backend

Writes typed nodes and edges to the planning graph via the `sds` CLI, then exports `spec-driven/<slug>/spec.md` for human review. Requires `sds` and `dolt` in PATH (detected in Phase 0).

## Graph Initialization

Before the first write, initialize the graph if it does not already exist:

```bash
sds init "<slug>" --project-root "<project-root>"
```

If the graph already exists (`sds status --slug "<slug>" --project-root "<project-root>"` succeeds), skip initialization.

## CLI Failure Handling

Every `sds` command can fail. Apply these fallbacks:

| Command | Failure Fallback |
|---------|-----------------|
| `sds init` | Fall back to markdown backend for this spec. Inform the user: "Graph init failed — using markdown backend." Load output-markdown.md and proceed. |
| `sds write` | Retry once. If the retry fails, skip the node write, log which node was skipped, and continue. At finalization, any skipped nodes will be absent from the export — note them in the completion summary. |
| `sds export` | Retry once. If the retry fails, fall back to markdown backend: generate `spec-driven/<slug>/spec.md` directly from captured session data using the markdown output reference. |
| `sds check all` | Retry once. If the retry fails, skip mechanical validation and proceed to qualitative validation only. Note in the validation summary: "Mechanical checks unavailable — graph validation skipped." |

## Node Writing Pattern

All node writes use JSON on stdin. Each write returns a JSON response with the assigned `id` — capture it for edge creation.

```bash
sds write <type> --slug "<slug>" --project-root "<project-root>" <<'JSON'
{"field": "value", "provenance": "[User]"}
JSON
```

Edges use flags:

```bash
sds write edge --slug "<slug>" --project-root "<project-root>" --from <type>:<id> --to <type>:<id> --type <edge-type>
```

**Write order matters**: write nodes before the edges that reference them.

## Content Section Keys

Prose sections are stored as `content` nodes with `artifact_type: "spec"` and a `section` key. Use exactly these keys — the export renderer maps them to template headings:

| Section Key | Template Heading |
|---|---|
| `project-context` | Project Context |
| `overview` | Overview |
| `goals` | Goals |
| `users` | Users |
| `scope` | Scope |
| `success-metrics` | Success Metrics |
| `dependencies` | Dependencies |
| `open-questions` | Open Questions |
| `agent-decisions` | Agent Decisions |

Content within a section can span multiple rows. Use `sort_order` (default 0) to control ordering within a section. The content field is markdown — include sub-headings, tables, and lists as they should appear in the exported spec.

## Phase-by-Phase Output

### After Phase 1 (Core Understanding)

Write project metadata:

```bash
sds write project --slug "<slug>" --project-root "<project-root>" <<'JSON'
{"slug": "<slug>"}
JSON
```

Write content sections captured in Phase 1: `project-context`, `overview`, `goals`.

```bash
sds write content --slug "<slug>" --project-root "<project-root>" <<'JSON'
{"artifact_type": "spec", "section": "overview", "content": "## overview content as markdown ##", "provenance": "[User]"}
JSON
```

### After Phase 2 (Users and Context)

Write content sections: `users`, `dependencies` (if systems were identified).

### After Phase 3 (Functional Requirements)

Write FR nodes, then AC nodes, then edges. For each FR:

```bash
sds write fr --slug "<slug>" --project-root "<project-root>" <<'JSON'
{"title": "FR title", "description": "description text", "user_story": "As a [user], I want [X] so that [Y]", "priority": "Must Have", "goal": "Primary", "provenance": "[User]"}
JSON
```

Response: `{"type": "fr", "id": 1, ...}`. Use the returned `id` for edges.

For each AC on that FR:

```bash
sds write ac --slug "<slug>" --project-root "<project-root>" <<'JSON'
{"criterion_name": "Valid credentials", "bdd_content": "Given a registered user\nWhen they submit valid credentials\nThen they are authenticated", "provenance": "[User]"}
JSON
```

Link each AC to its parent FR:

```bash
sds write edge --slug "<slug>" --project-root "<project-root>" --from ac:<ac_id> --to fr:<fr_id> --type belongs-to
```

For FR→FR dependencies:

```bash
sds write edge --slug "<slug>" --project-root "<project-root>" --from fr:<dependent_id> --to fr:<dependency_id> --type depends-on
```

Write `scope` content section with In Scope and Out of Scope sub-sections only (as markdown).

For each elicited constraint, write a typed node:

```bash
sds write constraint --slug "<slug>" --project-root "<project-root>" <<'JSON'
{"description": "Must run on AWS EMR Serverless", "category": "technical", "source": "stakeholder", "rationale": "Team infrastructure standard", "provenance": "[User]"}
JSON
```

Link each constraint to the FR(s) it constrains:

```bash
sds write edge --slug "<slug>" --project-root "<project-root>" --from constraint:<id> --to fr:<fr_id> --type constrains
```

For each elicited assumption, write a typed node:

```bash
sds write assumption --slug "<slug>" --project-root "<project-root>" <<'JSON'
{"description": "Snowflake contains the same data as S3", "source": "stakeholder", "provenance": "[User]"}
JSON
```

Link each assumption to the FR(s) it affects:

```bash
sds write edge --slug "<slug>" --project-root "<project-root>" --from assumption:<id> --to fr:<fr_id> --type affects
```

For each elicited risk, write a typed node:

```bash
sds write risk --slug "<slug>" --project-root "<project-root>" <<'JSON'
{"description": "Business logic parity risk", "impact": "High", "probability": "Medium", "mitigation": "Run both systems in parallel", "source": "stakeholder", "provenance": "[Inferred]"}
JSON
```

Link each risk to the FR(s) it affects:

```bash
sds write edge --slug "<slug>" --project-root "<project-root>" --from risk:<id> --to fr:<fr_id> --type affects
```

### After Phase 4 (NFRs and Success)

For each NFR:

```bash
sds write nfr --slug "<slug>" --project-root "<project-root>" <<'JSON'
{"category": "Performance", "description": "API response time under load", "metric": "p95 response time", "target": "< 200ms", "verification_method": "Load test with k6", "provenance": "[User]"}
JSON
```

Write content sections: `success-metrics`, `open-questions`, `agent-decisions`.

### After each phase: Export and update sidecar

After writing nodes, export to spec.md for human review:

```bash
sds export --format md --slug "<slug>" --project-root "<project-root>" --output "spec-driven/<slug>/spec.md"
```

Then update the sidecar at `spec-driven/.sessions/<slug>.spec.json` to mark the phase complete.

Emit to user after each export: `Spec written to spec-driven/<slug>/spec.md`

## Finalization

If the spec file already exists (regeneration), read the current Version number and increment it (1.0 → 1.1) before the final export.

Run the final export:

```bash
sds export --format md --slug "<slug>" --project-root "<project-root>" --output "spec-driven/<slug>/spec.md"
```

The exported `spec-driven/<slug>/spec.md` is the human-readable artifact. The graph is the authoritative source — downstream skills (`/design`) read from it.

## Validation

### Mechanical checks (Layer 1)
Run: `python skills/spec/scripts/validate.py --slug "<slug>" --project-root "<project-root>"`
Returns standard validation JSON (`{"pass": bool, "findings": [...]}`).
If mechanical checks produce findings, report them.
Proceed to qualitative validation regardless.

### Qualitative validation (Layer 2)
Delegate to a subagent. The subagent reads
[spec-validation-criteria-graph.md](spec-validation-criteria-graph.md)
as its first action, then validates the exported spec at
`spec-driven/<slug>/spec.md`.
Expected output: Validator Schema JSON.

Merge mechanical and qualitative findings before presenting to user.

## Edit Summaries

When content is updated during the session, present a brief conversational delta:

```
Updated spec:
- [Section]: [what changed]
- Open Questions: [N] → [M] remaining
```

Conversational only — NOT written to the graph. Ephemeral to the session.
