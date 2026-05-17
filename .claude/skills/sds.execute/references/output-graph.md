# Output: Graph Backend

Reads Bundle, Step, and VerifyClause nodes from the planning graph via the `sds` CLI. Uses `sds context` for selective context assembly per step. Tracks progress via `sds progress` commands. Requires `sds` and `dolt` in PATH (detected in Phase 0).

## Reading Inputs

Query Bundle and Step nodes from the graph:

```bash
sds query bundles --slug "<slug>" --project-root "<project-root>" --format json
sds query steps --slug "<slug>" --project-root "<project-root>" --format json
```

Parse the returned JSON for bundle execution order, parallelism annotations, step identifiers, file paths, intent, verify clauses, and dependencies.

If bundle query returns empty results, stop with guidance: "No bundles found in graph for slug '[slug]'. Run `/task <slug>` to create them first."

### Per-Bundle Step Details

For each bundle, query its steps:

```bash
sds query steps --bundle <bundle-id> --slug "<slug>" --project-root "<project-root>" --format json --with-upstream
```

The `--with-upstream` flag includes verify clauses, file paths, and dependency edges inline. Without it, only step metadata is returned.

## Context Assembly

The core differentiator of the graph backend. For each step dispatched to a subagent, assemble a focused context payload via graph traversal:

```bash
sds context STEP-N --profile implement --format json --slug "<slug>" --project-root "<project-root>"
```

### Context Profiles

| Profile | Includes | Use |
|---|---|---|
| `implement` | Step + decisions + constraints + standards + verify clauses + pattern refs | Step execution subagent |
| `review` | Step + verify clauses + decision chain + traced FRs + constraint rationale | Verify skill |

The execute skill uses the `implement` profile exclusively. The `review` and other profiles exist for downstream skills.

### Context Payload Structure

The `implement` profile returns:

```json
{
  "step": {
    "id": "STEP-4",
    "title": "Add JWT validation middleware",
    "intent": "Token validation must check expiry AND signature...",
    "effort": "S",
    "implementation_guidance": "Create requireAuth middleware...",
    "pattern_reference": "src/middleware/rateLimit.ts",
    "file_paths": [
      {"path": "src/middleware/auth.ts", "action": "create", "repo_name": ""}
    ]
  },
  "verify_clauses": [
    {
      "condition_text": "expired JWT (created 16 minutes ago)",
      "action": "request with Bearer token",
      "expected_outcome": "403 response (not 200)"
    }
  ],
  "decisions": [
    {
      "id": "AD-2",
      "title": "JWT for stateless auth",
      "chosen_approach": "...",
      "rationale": "..."
    }
  ],
  "standards": [
    {
      "id": "S-1",
      "domain": "security",
      "file_type": ".ts",
      "content": "..."
    }
  ],
  "constraints": [],
  "dependencies": {
    "depends_on": ["STEP-1"],
    "enables": ["STEP-6"]
  }
}
```

Pass this JSON payload to the subagent as assembled context. The subagent receives structured, scoped context — not file paths to planning documents.

### Payload Size

The 3K token target is a soft guideline. If a payload exceeds it, `sds context` logs a warning but does not truncate. Large payloads are surfaced in the execution plan confirmation (GATE 1) so the user can adjust.

## Progress Tracking

Update step status through the CLI:

```bash
sds progress update STEP-N --status in-progress --slug "<slug>" --project-root "<project-root>"
sds progress update STEP-N --status done --commit abc1234 --slug "<slug>" --project-root "<project-root>"
sds progress update STEP-N --status blocked --note "Type error after 3 attempts" --slug "<slug>" --project-root "<project-root>"
```

Query progress:

```bash
sds progress query --bundle <bundle-id> --slug "<slug>" --project-root "<project-root>" --format json
```

### Subagent Progress

Subagents update progress via their own `progress-bundle-N.md` files (same as markdown backend) — not via `sds progress`. The orchestrator reads subagent progress files and syncs to the graph after merge-back. This avoids concurrent graph writes from parallel subagents.

## CLI Failure Handling

Every `sds` command can fail. Apply these fallbacks:

| Command | Failure Fallback |
|---|---|
| `sds query bundles/steps` | Fall back to markdown backend for this session. Update session sidecar: `backend: "markdown"`. Inform: "Graph query failed — falling back to markdown backend." Read tasks.md + bundle-N.md instead. Load the markdown output backend reference per SKILL.md § Phase 1: Bundle Execution ("Load output backend reference" paragraph, first bundle only). |
| `sds context` | Retry once. If retry fails, fall back to markdown context assembly: pass the bundle file path to the subagent (equivalent to the markdown backend behavior defined in SKILL.md § Per-Bundle Dispatch, step 2). Note reduced context precision. |
| `sds progress update` | Retry once. If retry fails, write to `progress-bundle-N.md` instead (markdown fallback). Note: "Graph progress update failed — using file-based tracking." |
| `sds progress query` | Retry once. If retry fails, read `progress-bundle-N.md` instead. |

If more than 3 consecutive CLI commands fail, fall back to the markdown backend for the remainder of the session.

## Export

After execution completes, the orchestrator does not write new nodes to the graph — execution produces code commits, not graph artifacts. The progress state (step status, commit hashes) is synced to the graph via `sds progress update` after each bundle's merge-back.

## Dry-Run Output

For `--dry-run`, query the graph for bundle structure and step status:

```bash
sds query bundles --slug "<slug>" --project-root "<project-root>" --format json
sds progress query --slug "<slug>" --project-root "<project-root>" --format json
```

Present execution order, step status, and verification commands. Do not execute any steps.
