# Output: Markdown Backend

Reads the spec from `spec-driven/<slug>/spec.md`. Writes the design to `spec-driven/<slug>/design.md` plus `spec-driven/<slug>/references/` files. No external dependencies. This is the default backend.

## Reading the Spec

Read `spec-driven/<slug>/spec.md` directly. Parse FR-N, AC-N.M, and NFR-N identifiers from the document structure. Extract Open Questions, Constraints, Dependencies, and Current State sections.

If the spec file does not exist or is empty, stop with guidance: "No spec found at `spec-driven/<slug>/spec.md`. Run `/spec` to create one first."

## Writing the Design

After Phase 2 synthesis is complete, write these artifacts in order:

1. **design.md** — the primary artifact (~8-12K token target)
2. **references/research.md** — full research detail
3. **references/standards.md** — complete standards inventory
4. **references/contracts.md** — API contracts (optional, only when design involves API changes)

For any `--from` input (regardless of tier), set `spec_source` in frontmatter to the `--from` path instead of `spec-driven/<slug>/spec.md`.

### design.md

Use the template at [assets/design-template.md](../assets/design-template.md) (loaded in Phase 2 Design Draft step 9). Fill in each section following the instructions embedded in the template.

**Progressive disclosure rules** — design.md is a summary document the task skill loads in one shot:
- **Findings**: summary table only (ID, title, source, confidence, related FRs, one-sentence summary). Full content goes in references/research.md.
- **Resolved Uncertainties**: question and answer only. Supporting evidence goes in references/research.md.
- **Standards**: table of the most relevant standards. The complete inventory goes in references/standards.md.
- **Technical Approach, Architecture Decisions, File Inventory, Dependencies and Coupling**: write in full — the task skill needs complete context for these sections.
- **Constraints, Assumptions, Risks**: write in full — these are compact and the task skill needs them.

Write to `spec-driven/<slug>/design.md`. Overwrite completely — the write is idempotent.

### references/research.md

Use the template at [assets/research-template.md](../assets/research-template.md) (loaded in Phase 2 Design Draft step 9). Write full research results organized by aspect. This file carries the detail that design.md summarizes — full finding content, approach evaluations with tradeoff analysis, resolved uncertainties with evidence, and remaining uncertainties.

Write to `spec-driven/<slug>/references/research.md`.

### references/standards.md

Use the template at [assets/standards-template.md](../assets/standards-template.md) (loaded in Phase 2 Design Draft step 9). Write the complete standards inventory — every standard with full typed applicability metadata. This file is the authoritative source for standards; design.md carries a summary.

Write to `spec-driven/<slug>/references/standards.md`.

### references/contracts.md (optional)

API contract definitions when the design introduces or modifies API boundaries. Include endpoint structures, request/response shapes, error formats, and versioning approach. Only create this file when the design involves API changes.

Write to `spec-driven/<slug>/references/contracts.md`.

Update the sidecar at `spec-driven/.sessions/<slug>.design.json` after writing all files.

Emit: `Design written to spec-driven/<slug>/design.md`

## Finalization

Finalization steps are defined in SKILL.md under the Design Review gate. The markdown backend's finalization rewrites design.md with `status: final` and computes `spec_hash`.

## Validation

### Mechanical checks (Layer 1)

Run: `python "<skill-directory>/scripts/validate.py" --slug "<slug>" --project-root "<project-root>"` where `<skill-directory>` is the directory containing the design SKILL.md.

Returns standard validation JSON. For the markdown backend, mechanical checks parse the design file for structural completeness (frontmatter fields, section presence, ID format consistency, references/ file existence).

### Qualitative validation (Layer 2)

Delegate to a subagent. The subagent reads [design-validation-criteria-markdown.md](design-validation-criteria-markdown.md) as its first action, then validates the design at `spec-driven/<slug>/design.md`.

Expected output: Validator Schema JSON.

## Edit Summaries

When the design is rewritten during the session (after "Adjust" at the review gate), present a brief conversational delta:

```
Updated design:
- [Section]: [what changed]
- AD-3: [added/modified/removed]
```

Conversational only — NOT written to the design file.
