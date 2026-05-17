# Output: Graph Backend

Reads FR, AC, NFR, Finding, Decision, and Standard nodes from the planning graph via the `sds` CLI. Writes Slice, Step, VerifyClause, and Bundle nodes, then exports `spec-driven/<slug>/tasks.md` for human review. Requires `sds` and `dolt` in PATH (detected in Phase 0).

**CLI command status**: Read commands (`sds query frs`, `sds query nfrs`, `sds query findings`, `sds query decisions`, `sds query standards`) exist (Phases 1-2). Write commands for task-stage node types (`sds write slice`, `sds write step`, `sds write verify-clause`, `sds write bundle`) and check commands (`sds check cycles`, `sds check conflicts`, `sds check coverage`) are Phase 3 CLI deliverables (sds-cli issue #3). They follow the established `sds write <type>` / `sds query <type>` patterns.

## Reading Inputs

Query upstream nodes from the graph:

```bash
sds query frs --slug "<slug>" --project-root "<project-root>" --format json
sds query acs --slug "<slug>" --project-root "<project-root>" --format json
sds query nfrs --slug "<slug>" --project-root "<project-root>" --format json
sds query findings --slug "<slug>" --project-root "<project-root>" --format json
sds query decisions --slug "<slug>" --project-root "<project-root>" --format json
sds query standards --slug "<slug>" --project-root "<project-root>" --format json
sds query constraints --slug "<slug>" --project-root "<project-root>" --format json
sds query assumptions --slug "<slug>" --project-root "<project-root>" --format json
sds query risks --slug "<slug>" --project-root "<project-root>" --format json
```

Parse the returned JSON for identifiers, priorities, descriptions, relationships, and typed metadata. Findings inform intent authoring. Decisions create `informed-by` edges. Standards match to STEPs by file type.

If FR and AC queries both return empty results, stop with guidance: "No spec data found in graph for slug '[slug]'. Run `/spec` to create one first." If Finding/Decision/Standard queries return empty, stop with guidance: "No design data found. Run `/design <slug>` first."

## CLI Failure Handling

Every `sds` command can fail. Apply these fallbacks:

| Command | Failure Fallback |
| --- | --- |
| `sds query` | Fall back to markdown backend for this session. Update the session sidecar to record `backend: "markdown"`. Inform: "Graph query failed — falling back to markdown backend." Read design.md + spec.md instead. Load `references/output-markdown.md` as the write reference. Any nodes already written before the failure are orphaned — do not attempt cleanup. |
| `sds write` | Retry once. If retry fails, skip the node write, log which node was skipped, and continue. Note skipped nodes in the completion summary. If more than 3 consecutive writes fail or more than 30% of total node writes fail, fall back to markdown backend for the remainder of the session. When falling back mid-phase, retain all STEP data produced so far in memory. Switch to the markdown output reference (output-markdown.md) and write all accumulated STEPs to bundle-N.md files at the next incremental write point. Do not re-derive STEPs — the data is valid, only the persistence layer changed. |
| `sds write edge` | Retry once. If retry fails, skip the edge, log which edge was skipped, and continue. Skipped edges degrade provenance but do not block. |
| `sds export` | Retry once. If retry fails, fall back to markdown: generate tasks.md directly from session data using the task template in output-markdown.md. |
| `sds check` | Retry once. If retry fails, skip mechanical validation and proceed to qualitative validation only. Note: "Mechanical checks unavailable — graph validation skipped." |

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

## Writing Slices

For each slice:

```bash
sds write slice --slug "<slug>" --project-root "<project-root>" <<'JSON'
{
  "name": "Walking Skeleton",
  "description": "Prove the architecture end-to-end with minimal implementation",
  "stage": "skeleton",
  "execution_order": 1
}
JSON
```

Valid `stage` values: `skeleton`, `depth`, `integration`. `execution_order` is an integer — multiple slices may share a stage but must have unique execution orders.

Response: `{"type": "slice", "id": 1, ...}`. Capture `id` for step writes.

## Writing Steps

For each step:

```bash
sds write step --slug "<slug>" --project-root "<project-root>" <<'JSON'
{
  "slice_id": 1,
  "title": "Create AuthService skeleton",
  "intent": "Access token generation must use the existing JWT secret from env, not a hardcoded value.",
  "effort": "S",
  "implementation_guidance": "Create AuthService class with login()/logout() stubs. Export typed interfaces.",
  "pattern_reference": "src/services/user.ts"
}
JSON
```

`intent` is NOT NULL — every step must have intent. Structural steps use `"N/A — structural step"`.

Valid `effort` values: `XS`, `S`, `M`, `L`. XL steps should be flagged for splitting, not written.

Response: `{"type": "step", "id": 1, ...}`. Capture `id` for file paths, verify clauses, and edges.

## Writing Step File Paths

For each file path on a step:

```bash
sds write step-file-path --slug "<slug>" --project-root "<project-root>" <<'JSON'
{
  "step_id": 1,
  "file_path": "src/services/auth.ts",
  "action": "create",
  "repo_name": ""
}
JSON
```

Valid `action` values: `create`, `modify`, `delete`. `repo_name` is empty for single-project mode; set to the project name (e.g., `auth-service`) for multi-project mode.

## Writing Verify Clauses

For each verify clause on a step:

```bash
sds write verify-clause --slug "<slug>" --project-root "<project-root>" <<'JSON'
{
  "step_id": 1,
  "level": "unit",
  "condition_text": "JWT_SECRET env var set to 'test-secret'",
  "action": "call AuthService.login() with valid credentials",
  "expected_outcome": "returned token decodes with 'test-secret', not any hardcoded value"
}
JSON
```

All four fields (level, condition_text, action, expected_outcome) are NOT NULL. Derive from the step's intent — see the behavioral verify guide (loaded at Phase 0).

Response: `{"type": "verify_clause", "id": 1, ...}`. Capture `id`.

## Writing Bundles

For each bundle:

```bash
sds write bundle --slug "<slug>" --project-root "<project-root>" <<'JSON'
{
  "name": "Foundation",
  "execution_order": 1,
  "parallelism_annotation": "no"
}
JSON
```

Response: `{"type": "bundle", "id": 1, ...}`. Capture `id`.

Link steps to bundles via the junction table:

```bash
sds write bundle-step --slug "<slug>" --project-root "<project-root>" --bundle <bundle_id> --step <step_id>
```

Every step must appear in exactly one bundle.

## Edge Writing

After all nodes are written, create edges:

### traces-to (Step -> FR/AC)

```bash
sds write edge --slug "<slug>" --project-root "<project-root>" --from step:<step_id> --to ac:<ac_id> --type traces-to
```

Every non-MANUAL step must have at least one `traces-to` edge to an AC. MANUAL steps have no `traces-to` edges — they are identified by the absence of this edge type.

### depends-on (Step -> Step)

```bash
sds write edge --slug "<slug>" --project-root "<project-root>" --from step:<step_id> --to step:<dependency_id> --type depends-on
```

### informed-by (Step -> Decision)

```bash
sds write edge --slug "<slug>" --project-root "<project-root>" --from step:<step_id> --to decision:<decision_id> --type informed-by
```

Link each step to the Decisions whose approach it follows.

### applies-to (Standard -> Step)

Auto-matched by file-type JOIN: for each standard with a `file_type`, find all steps whose `step_file_paths` include files matching that type. In multi-project mode, match only within the standard's source project.

```bash
sds write edge --slug "<slug>" --project-root "<project-root>" --from standard:<standard_id> --to step:<step_id> --type applies-to
```

### verifies (VerifyClause -> Step)

Implicit via `verify_clause.step_id` FK — no explicit edge needed.

## Write Sequence

Write all nodes and edges in this order:

1. All Slice nodes
2. All Step nodes (referencing slice IDs)
3. All step_file_paths entries
4. All VerifyClause nodes (referencing step IDs)
5. All Bundle nodes
6. All bundle_steps entries
7. `traces-to` edges (Step -> AC)
8. `depends-on` edges (Step -> Step)
9. `informed-by` edges (Step -> Decision)
10. `applies-to` edges (Standard -> Step)

## Export

After writing all nodes and edges, export for human review:

```bash
sds export --format md --slug "<slug>" --project-root "<project-root>" --output "spec-driven/<slug>/tasks.md"
```

The exported tasks.md must match the template structure. After export, generate:
- `spec-driven/<slug>/bundle-N.md` per bundle
- `spec-driven/<slug>/progress-bundle-N.md` per bundle (initialized, all steps `pending`)

Update the sidecar at `spec-driven/.sessions/<slug>.task.json` after the export.

Emit: `Tasks written to spec-driven/<slug>/tasks.md`

## Finalization

Follow the GATE 3 finalization sequence in SKILL.md. Graph-specific mechanics: `sds export --format md` with `status: final` metadata produces `tasks.md`. Bundle files and progress files are generated from graph data after export. SHA-256 hashes of design and spec are included as export metadata.

The exported tasks.md is the human-readable artifact. The graph is the authoritative source — downstream skills (`/execute`) will read directly from it once task-stage write commands ship (sds-cli issue #3). Until then, the exported bundle-N.md and progress-bundle-N.md files are the downstream interface.

## Validation

### Mechanical checks (Layer 1)

Run: `python "<skill-directory>/scripts/validate.py" --slug "<slug>" --project-root "<project-root>"` where `<skill-directory>` is the directory containing the task SKILL.md.

Returns standard validation JSON. The graph backend calls `sds check` commands:
- `sds check cycles --slug "<slug>" --project-root "<project-root>"` — circular dependency detection
- `sds check conflicts --slug "<slug>" --project-root "<project-root>"` — hot file detection per repo
- `sds check coverage --frs-without-steps --slug "<slug>" --project-root "<project-root>"` — unimplemented FR detection

### Qualitative validation (Layer 2)

Delegate to a subagent. The subagent reads [task-validation-criteria.md](task-validation-criteria.md) as its first action, then queries the graph via `sds` CLI using the slug and project-root. The subagent walks provenance chains (AC->Step, Step->Decision) individually via graph queries, not by reading the exported markdown.

Expected output: Validator Schema JSON.

Merge mechanical and qualitative findings before presenting to user.

**Fallback**: If both mechanical validation (`sds check` commands) and qualitative validation (subagent) are unavailable, proceed to review with a warning: "Both validation layers unavailable — review manually."

## Edit Summaries

When tasks are updated during the session (after "Adjust" at the review gate):
1. Update the relevant nodes/edges in the graph
2. Re-export to `spec-driven/<slug>/tasks.md`
3. Present a brief conversational delta:

```
Updated tasks:
- STEP-3: intent revised, verify clause added for locked account edge case
- Bundle 2: STEP-5 moved to Bundle 3 (file conflict)
```

Conversational only — NOT written to the graph.
