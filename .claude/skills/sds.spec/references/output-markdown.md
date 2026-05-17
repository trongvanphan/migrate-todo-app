# Output: Markdown Backend

Writes the specification directly to `spec-driven/<slug>/spec.md` using the template. No external dependencies. This is the default backend.

## Incremental Persistence

After each phase completes, perform both actions as a paired obligation:

1. **Write the spec file** — generate/overwrite `spec-driven/<slug>/spec.md` using [assets/spec-template.md](../assets/spec-template.md) as the format guide, incorporating all content captured so far. Overwrite the file completely each time — the write is idempotent.
2. **Update the sidecar** — mark the phase complete in `spec-driven/.sessions/<slug>.spec.json`.

Write the spec before updating the sidecar — the spec write is idempotent, so if the session dies between the two, the next session re-runs the write safely.

Emit to user after each write: `Spec written to spec-driven/<slug>/spec.md`

## Finalization

Run the final overwrite of `spec-driven/<slug>/spec.md`. No additional export step is needed — the file is the artifact.

## Template

Use [assets/spec-template.md](../assets/spec-template.md) for section order, heading format, provenance tag placement, and ID formats (FR-N, AC-N.M, NFR-N). All sections with captured content are included; empty sections are omitted.

## Validation

### Mechanical checks (Layer 1)
Run: `python skills/spec/scripts/validate.py --slug "<slug>" --project-root "<project-root>"`
Returns standard validation JSON. For the markdown backend this is a pass-through — mechanical parsing of free-form markdown is not cost-effective. Semantic checks are handled entirely by Layer 2.

### Qualitative validation (Layer 2)
Delegate to a subagent. The subagent reads
[spec-validation-criteria-markdown.md](spec-validation-criteria-markdown.md)
as its first action, then validates the spec at
`spec-driven/<slug>/spec.md`.
Expected output: Validator Schema JSON.

## Edit Summaries

When the spec is rewritten during the session, present a brief conversational delta:

```
Updated spec:
- [Section]: [what changed]
- Open Questions: [N] → [M] remaining
```

Conversational only — NOT written to the spec file. Ephemeral to the session.
