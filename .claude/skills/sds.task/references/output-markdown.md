# Output: Markdown Backend

Reads the design from `spec-driven/<slug>/design.md` and spec from `spec-driven/<slug>/spec.md`. Writes `tasks.md`, `bundle-N.md`, and `progress-bundle-N.md` files. No external dependencies. This is the default backend.

## Reading Inputs

### Design Document

Read `spec-driven/<slug>/design.md`. Extract:
- **Findings (F-N)**: source, confidence, related FRs, implications — inform intent authoring
- **Architecture Decisions (AD-N)**: chosen approach, rationale, alternatives — create `informed-by` traces
- **Standards (S-N)**: domain, file_type, action_type — match to STEPs by file type
- **File Inventory**: files to create/modify with FR associations — seed STEP file_paths
- **Dependencies and Coupling**: shared files, sequencing recommendations — inform bundling
- **Technical Approach**: per-feature-area narrative — inform slice boundaries
- **Constraints, Assumptions, Risks**: carry forward to inform intent and verify clauses
- **Test approach**: `tdd`, `test-after`, or `none` — inform verify clause generation
- **References directory**: After reading design.md, conditionally read `references/research.md`, `references/standards.md`, and `references/contracts.md` per the rules in task-guide.md § Reference File Parsing. Store results in the upstream context registry.

If `spec-driven/<slug>/design.md` does not exist, stop with guidance: "No design found at `spec-driven/<slug>/design.md`. Run `/design <slug>` to create one first."

### Spec Document

Read `spec-driven/<slug>/spec.md`. Extract:
- **FR-N**: identifiers, priorities, descriptions
- **AC-N.M**: acceptance criteria per FR — primary trace targets for STEPs
- **NFR-N**: non-functional requirements — may produce MANUAL STEPs or constrain implementation

If `spec-driven/<slug>/spec.md` does not exist and `spec_source` in the design frontmatter points elsewhere, read from that path instead. If no spec is found at either location, stop with guidance: "No spec found. Run `/spec` to create one first."

### Spec Document AC Text

After reading spec.md for FR-N/AC-N.M identifiers, extract full AC text per task-guide.md § AC Text Extraction. Store the resulting registry keyed by AC identifier. If spec.md uses table format, extract Given/When/Then columns. If prose format, extract the criterion text verbatim.

### Design Freshness

Compute SHA-256 of `spec-driven/<slug>/design.md`. If an existing `tasks.md` has a `design_hash` that differs, inform the user: "Design has changed since these tasks were generated. Regenerate?"

## Writing Tasks

After Phase 2 (bundle construction) and Phase 3 (validation) complete, write artifacts in order:

1. **bundle-N.md** — one per bundle, self-contained execution units
2. **progress-bundle-N.md** — one per bundle, initialized with all steps at `pending`
3. **tasks.md** — primary artifact using [assets/task-template.md](../assets/task-template.md)

Write order matters: bundle files first, then tasks.md with final status. If interrupted after bundle writes but before tasks.md, the sidecar still exists and enables resume. If interrupted after tasks.md, all referenced bundle files already exist.

### tasks.md

Use the task template (loaded at Phase 3) to fill in each section following the template structure.

tasks.md is always an index-only document: frontmatter, traceability table, conflict analysis, architecture decisions, and bundle headers only — no STEP entries. All STEP detail lives in the bundle-N.md files.

Write to `spec-driven/<slug>/tasks.md`. Overwrite completely — the write is idempotent.

### bundle-N.md

Each bundle file is self-contained: bundle header metadata blockquote + all STEP entries for that bundle. Include the bundle's slice context (phase name) in the header.

Write to `spec-driven/<slug>/bundle-N.md`.

### Context Preamble Assembly

For each bundle, assemble a Context preamble and insert it between the bundle header's `**Bundle Verify**` block and the first `#### STEP-N:` heading.

**Scoping algorithm** — run once per bundle, after all bundles are finalized:

1. **Collect bundle traces**: From each STEP's `[FR-N -> AC-N.M]` header line, collect the set of unique AC identifiers (`bundle_acs`) and FR identifiers (`bundle_frs`) for this bundle. MANUAL STEPs contribute nothing to these sets.

2. **Applicable ACs**: For each AC in `bundle_acs`, look up its full text in the AC text registry (built during Phase 0). Include one line per AC.

3. **Applicable Architecture Decisions**: For each AD-N in design.md's Architecture Decisions section, check if its Context or Rationale fields reference any FR in `bundle_frs` (text-search for `FR-N` tokens). Include the full AD block (title, decision, rationale). If no ADs reference any FR in `bundle_frs`, omit this section.

4. **Applicable Findings**: For each F-N in the upstream context registry, check if its Related FRs list intersects `bundle_frs`. Include the F-N title and its implication sentence(s) only — not the full finding body (approaches, uncertainties). If no findings apply, omit this section. If a finding has no Related FRs field, include it in all bundles (cannot scope; safe fallback).

5. **Applicable Standards**: Collect all S-N identifiers from the `> **Standards**:` blockquotes of STEPs in this bundle. For each unique S-N, look up the full rule text, domain, file type, and action type from the upstream context registry (sourced from `references/standards.md` or the design.md Standards table). Include one line per standard. If no STEPs in the bundle reference any standards, omit this section.

6. **Applicable Constraints**: For each row in design.md's Constraints (Technical) table, check if the Rationale column references any FR in `bundle_frs`. Include the full row content (all columns). If no constraints apply, omit this section. If a row has no FR reference, include it in all bundles (cannot scope; safe fallback).

7. **Applicable Risks**: For each row in design.md's Risks (Technical) table, check if the Affects column references any FR in `bundle_frs`. Include the full row content (all columns). If no risks apply, omit this section. If a row has no FR reference, include it in all bundles (cannot scope; safe fallback).

8. **Applicable Contracts**: If `references/contracts.md` was read AND any endpoint in the upstream context registry is annotated with an FR in `bundle_frs`, include the full endpoint block (method, path, request/response shape). Also include if any STEP in the bundle declares a file path matching route/controller/handler/api patterns. If `references/contracts.md` was not read or no endpoints match, omit this section entirely.

**Omit-if-empty rule**: Omit any preamble section that has no applicable items. If ALL sections are empty (the bundle has only MANUAL STEPs or structural STEPs with no FR traces), omit the entire Context block — proceed directly to the first STEP heading.

**Preamble format**:

~~~
> **Context**
>
> **Applicable ACs**
> - **AC-N.M**: Given: [text] / When: [text] / Then: [text]
>
> **Architecture Decisions**
> - **AD-N: [Title]** — Decision: [text]. Rationale: [text].
>
> **Findings**
> - **F-N: [Title]** — [implication sentence]
>
> **Standards**
> - **S-N**: [rule text] (Domain: [domain] | File Type: [type])
>
> **Constraints**
> - [Constraint text] (Category: [cat] | Source: [src])
>
> **Risks**
> - [Risk text] (Impact: [level] | Mitigation: [text])
>
> **Contracts**
> - [METHOD /path] — [request/response summary]
~~~

**Error handling**:

| Condition | Behavior |
|---|---|
| AC in STEP trace not found in AC text registry | Skip that AC in the preamble. Log: "[warn] AC-N.M not found in spec — omitting from preamble." |
| Finding has no Related FRs field | Include the finding in all bundles (cannot scope). |
| AD mentions no FRs in Context or Rationale | Include the AD in all bundles (cannot scope). |
| Constraint row has no FR reference in Rationale | Include the constraint in all bundles (cannot scope). |
| Risk row has no FR reference in Affects | Include the risk in all bundles (cannot scope). |
| S-N referenced in STEP but not found in upstream context registry | Skip that standard. Log: "[warn] S-N not found in standards registry — omitting from preamble." |
| All preamble sections are empty | Omit entire Context block. |

### progress-bundle-N.md

One per bundle, initialized from the progress tracker template in task-template.md. All steps start at `pending`. The executor writes only to its own bundle's progress file.

Write to `spec-driven/<slug>/progress-bundle-N.md`.

Update the sidecar at `spec-driven/.sessions/<slug>.task.json` after writing all files.

Emit: `Tasks written to spec-driven/<slug>/tasks.md`

## Finalization

Follow the GATE 3 finalization sequence in SKILL.md. All markdown artifacts are plain file writes to `spec-driven/<slug>/` — each overwritten completely.

## Validation

### Mechanical checks (Layer 1)

Run: `python "<skill-directory>/scripts/validate.py" --slug "<slug>" --project-root "<project-root>"` where `<skill-directory>` is the directory containing the task SKILL.md.

Returns standard validation JSON. For the markdown backend, mechanical checks parse tasks.md for structural completeness (frontmatter fields, section presence, STEP ID format, bundle file existence).

### Qualitative validation (Layer 2)

Delegate to a subagent. The subagent reads [task-validation-criteria.md](task-validation-criteria.md) as its first action, then validates the tasks at `spec-driven/<slug>/tasks.md`.

Expected output: Validator Schema JSON.

Merge mechanical and qualitative findings before presenting to user.

**Fallback**: If the qualitative validator subagent fails, skip qualitative validation and present mechanical results only. If both validation layers are unavailable, proceed to review with a warning: "Both validation layers unavailable — review manually."

## Edit Summaries

When tasks are rewritten during the session (after "Adjust" at the review gate), present a brief conversational delta:

```
Updated tasks:
- STEP-3: verify clause strengthened (added boundary condition for locked accounts)
- Bundle 2: STEP-5 moved to Bundle 3 (file conflict with STEP-4)
```

Conversational only — NOT written to the task file.
