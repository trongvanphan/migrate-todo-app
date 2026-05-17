# Output: Graph Backend

Reads execution artifacts from the planning graph via the `sds` CLI. Uses `sds context --profile review` for provenance chain traversal. Requires `sds` and `dolt` in PATH (detected in Phase 0).

## Reading Execution Artifacts

### Provenance Chain Queries

The graph backend's key differentiator: for any step, query the full provenance chain — STEP-4 was informed by Decision D-3, which was based on Finding F-7, which was constrained by NFR-2. Verify that the implementation is consistent with the full chain, not just the verify clause in isolation.

```bash
sds context STEP-N --profile review --format json --slug "<slug>" --project-root "<project-root>"
```

The `review` profile returns: step details, verify clauses, the decision chain (Decision → Finding), traced FRs/ACs, and constraint rationale. This is richer context than the markdown backend can provide.

### Coverage Checks

```bash
sds check coverage --frs-without-steps --slug "<slug>" --project-root "<project-root>"
```

Returns FRs that have no traced Steps — these are coverage gaps.

### Step and Verify Clause Queries

```bash
sds query steps --slug "<slug>" --project-root "<project-root>" --format json --with-upstream
sds query verify-clauses --slug "<slug>" --project-root "<project-root>" --format json
```

### Progress

Progress tracking uses the same per-bundle `progress-bundle-N.md` files as the markdown backend. The graph does not store execution progress — it stores planning artifacts (Steps, Bundles, VerifyClauses). Step completion status comes from the progress files.

## Building Verification Context

For each verification agent, assemble context from graph queries:

1. **Per-step provenance**: `sds context STEP-N --profile review` for each done step
2. **Coverage gaps**: `sds check coverage --frs-without-steps`
3. **Verify clauses**: `sds query verify-clauses` for all defined verification criteria
4. **Progress**: read from `progress-bundle-N.md` files (same as markdown backend)
5. **Changed files**: git log on execution branch (same as markdown backend). Gitignored paths excluded per the markdown backend filtering step.
6. **CLAUDE.md**: conventions from each project (same as markdown backend)

The graph context is passed to agents alongside the standard artifact context. Agents that support provenance chain analysis (Traceability, Completeness) receive the richer graph context. Other agents (Code Quality, Security) receive the same context as the markdown backend.

## CLI Failure Handling

| Command | Failure Fallback |
|---|---|
| `sds context --profile review` | Fall back to markdown context for this step. Note reduced provenance depth. |
| `sds check coverage` | Skip graph-powered coverage check. Rely on the Traceability agent's manual FR→STEP cross-reference. |
| `sds query verify-clauses` | Read verify clauses from bundle-N.md files instead. |

If more than 3 consecutive CLI commands fail, fall back to the markdown backend for the remainder of the session.

## Writing the Report

Same as markdown backend — write `spec-driven/<slug>/verify-report.md` using the template. The graph backend enriches the context but does not change the report format.
