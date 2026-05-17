# sds Delegation Contract

This reference defines exactly how `migration-artifacts-2` calls each `sds.*` skill. Read this before dispatching any of Phases 02, 03, 04, 05, or 07.

The migration skill is the orchestrator. The sds skills are the engine. The migration skill never re-implements what sds already produces.

---

## Shared conventions

**Slug identity.** A migration domain's slug **is** its sds spec slug. The slug must match `[a-z0-9-]+` and be ≤64 chars. The slug is the only join key between `migration-state.json.domains[<slug>]` and `spec-driven/<slug>/`.

**Working directory.** All sds skills are invoked from the workspace root. They write under `spec-driven/<slug>/`. The migration skill writes under `discovery/`, `domains/`, `_constraints.md`, and `migration-state.json` — all at the workspace root.

**State reflection.** The sds skills never read or update `migration-state.json`. After a sds invocation returns, the migration scheduler reads the sds output (file existence + frontmatter `status`) and reflects progress into the state file. Update `last_updated` and `domains[<slug>].status` on every reflection.

**Interactive gates.** Every sds skill has mandatory user interaction gates. The orchestrator MUST NOT auto-answer them. When a gate fires inside a sds invocation, control returns to the user. The migration scheduler only resumes when the gate has been resolved.

**Failures.** When a sds skill stops with an error message, surface that error verbatim. Do not paraphrase, do not retry blindly. Most sds errors require user action (missing input, accessibility failure, conflicting flags).

---

## Phase 02 — `/sds.spec`

### Invocation

For each domain whose status is `pending` and whose `legacy-context.md` exists:

```
/sds.spec <slug> --from domains/<slug>/legacy-context.md --draft
```

`--draft` is required. It tells `/sds.spec` to synthesize a spec from the briefing and present it for user validation rather than running full interactive elicitation. The briefing is the migration's substitute for the user's tacit knowledge — without it, `/sds.spec` would ask the user everything from scratch.

### Briefing (`legacy-context.md`)

One file per domain at `domains/<slug>/legacy-context.md`, written at the end of Phase 01 from [../templates/legacy-context.md](../templates/legacy-context.md). It carries:

- Domain name and slug
- Source paths in the legacy app (files, directories)
- Existing user-facing surface (routes, screens, jobs)
- Existing API surface (endpoints, RPC methods, events) with current shapes
- Data model (tables, columns, indexes, retention)
- Cross-domain dependencies (consumed contracts, shared kernel usage)
- Known constraints (compliance, performance, integrations)
- Explicit out-of-scope items
- Migration-specific risks already identified

The briefing is **not** a spec. It is the legacy-side context that lets `/sds.spec --draft` produce a first-pass new-system spec.

### Gate

`spec-driven/<slug>/spec.md` exists with frontmatter `status: final`. Reflect to `migration-state.json`:

- `domains[<slug>].status = "spec"`
- append to `phases_complete` if every migration-target domain has reached `"spec"` or beyond.

### Fallbacks

- If the briefing covers fewer than half of the spec's Phase 1 fields, `/sds.spec` auto-falls-back to interactive mode and informs the user. The migration scheduler must wait for the interactive completion; do not retry with `--draft` again.
- If the user rejects the draft and chooses to start over, allow the rejection. Do not force `--draft` a second time.

### Multi-project legacy

When the legacy app spans multiple repositories, the migration's `legacy-context.md` lists each source repo under a `Source repositories` heading. `/sds.spec` will not auto-discover them — the briefing must explicitly reference them. Do not pass `--from` with multiple files; concatenate into the single briefing.

---

## Phase 03 — `/sds.design`

### Invocation

For each domain whose status is `"spec"`:

```
/sds.design <slug> --context _constraints.md
```

`/sds.design` accepts only one `--context` path. When the domain exposes inbound contracts (per `domains/_contracts.yaml`), the migration scheduler MUST merge the contract excerpts for this domain into `_constraints.md` before invoking — or surface the relevant contract excerpts to the user as part of the Research Scope Review gate response. Do not invoke `/sds.design` twice with different contexts.

### Constraints file (`_constraints.md`)

Written once at the start of Phase 03 if not already present. Sections:

- **Tech stack** — verbatim from `migration-state.json.parameters.TECH_STACK`.
- **Compliance scope** — verbatim from `COMPLIANCE_SCOPE`.
- **NFR baselines** — performance, availability, RTO/RPO targets that apply across all domains.
- **Architectural standards** — repo layout convention, lint/format tooling, test framework choices, error model.
- **Inter-domain contracts** — reference to `domains/_contracts.yaml` with summary of which contracts this domain consumes or owns.

### Gate

`spec-driven/<slug>/design.md` exists with frontmatter `status: final`. Reflect:

- `domains[<slug>].status = "design"`
- If the domain owns an inbound contract, the API owner must approve before Phase 04 begins. Surface to the user; do not auto-advance.

### Failure modes

- If `/sds.design` falls back to markdown backend after a graph backend failure, honor that for the rest of the run.
- If the spec was changed after design research began (sds detects this via spec hash), `/sds.design` will present a Restart prompt. Surface to the user.

---

## Phase 04 — `/sds.task`

### Invocation

For each domain whose status is `"design"`:

```
/sds.task <slug>
```

When the design indicates a strict ordering (e.g. "data migration must precede API"), pass:

```
/sds.task <slug> --strategy dependency-first
```

When the team is large and many engineers can parallelize:

```
/sds.task <slug> --strategy max-parallelism
```

When the design favors thin end-to-end slices:

```
/sds.task <slug> --strategy walking-skeleton
```

Default (no flag): `/sds.task` recommends the strategy at GATE 1 and the user confirms.

### Gate

- `spec-driven/<slug>/tasks.md` exists.
- At least `spec-driven/<slug>/bundle-1.md` and `spec-driven/<slug>/progress-bundle-1.md` exist.

Reflect: `domains[<slug>].status = "tasks"`.

### Failure modes

- If `/sds.task` produces only one bundle and the spec has multiple FRs of mixed effort, surface this to the user — it usually indicates either an overly coarse decomposition or a deliberate walking-skeleton choice.

---

## Phase 05 — `/sds.execute`

### Invocation

For each domain whose status is `"tasks"`, respecting `domains/_migration-order.md`:

```
/sds.execute <slug> --parallelism <N>
```

Where `N` is the **per-domain** parallelism cap (default 1; up to the value the user agreed at startup). Across domains, the migration scheduler limits concurrent `/sds.execute` invocations per the Concurrency Model.

When recovering from a blocker on a single step:

```
/sds.execute <slug> --step STEP-<N>
```

### Branch isolation

`/sds.execute` works on `spec-driven/<slug>/exec`. The orchestrator must not:

- check out that branch manually
- commit to it directly
- force-push it

After `/sds.execute` completes for the domain, record the branch in state:

```
domains[<slug>].branch = "spec-driven/<slug>/exec"
```

### Mode selection

- `--mode agent` (default): subagent dispatch.
- `--mode team`: human branch coordination. Use when the user has explicitly chosen team mode for this domain.

### Gate

- Every `spec-driven/<slug>/progress-bundle-N.md` shows all steps with status `done`.
- CI green on `spec-driven/<slug>/exec`.

Reflect: `domains[<slug>].status = "execute"`. If any bundle reports `blocked`, append to `domains[<slug>].blockers[]` and do **not** advance to Phase 06 or 07.

### Failure modes

- `/sds.execute` may stop at a per-bundle Review gate. Surface it; do not auto-approve. The user is reviewing risk for the live migration.
- If `--skip-review` is needed (long bundle, expensive review), require explicit user opt-in.

---

## Phase 07 — `/sds.verify`

### Invocation

For each domain whose status is `"execute"` (or `"strangler"` when live traffic):

```
/sds.verify <slug>
```

Default runs all six built-in dimensions. To narrow:

```
/sds.verify <slug> --focus traceability,security
```

### Migration supplement

`/sds.verify` does not cover four of the migration's ten dimensions: **performance**, **observability**, **compliance**, **data-parity**. Run the native sub-agents for each as needed:

- Performance: [../sub-agents/07-verify/performance.md](../sub-agents/07-verify/performance.md)
- Observability: [../sub-agents/07-verify/observability.md](../sub-agents/07-verify/observability.md)
- Compliance: [../sub-agents/07-verify/compliance.md](../sub-agents/07-verify/compliance.md) (mandatory when `COMPLIANCE_SCOPE` is non-`none`)
- Data-parity: [../sub-agents/07-verify/data-parity.md](../sub-agents/07-verify/data-parity.md) (mandatory when the migration includes a data move)

Aggregate the four supplemental dimensions into a single file `domains/<slug>/verify-supplement.md`. Use the same severity vocabulary as the sds verify report: `critical | high | medium | low | info`.

### Gate

Zero CRITICAL findings across:

- `spec-driven/<slug>/verify-report.md`
- `domains/<slug>/verify-supplement.md`

Reflect: `domains[<slug>].status = "verify"`.

### Remediation

When `/sds.verify` produces a remediation brief (`spec-driven/<slug>/remediation.md`), surface the user-selectable remediation options. Do not auto-select.

---

## Skipping rules

When `migration-state.json.parameters.LIVE_TRAFFIC = false`:

- Phase 06 (strangler-fig) is skipped. No `domains/<slug>/strangler/` directory is created.
- Phase 08 (api-diff) is skipped.
- Phase 09 (decommission) is skipped. The run completes after Phase 07.
- Mark these phases as `skipped` in `migration-state.json.phases_complete` with a `_skip_reason` sidecar field per phase.

The sds-delegated phases (02, 03, 04, 05, 07) always run. They are size-agnostic and apply to every migration regardless of live-traffic state.

---

## Reflecting sds output into state

After every sds-delegated phase, the migration scheduler does the following, in order:

1. Verify the gate condition for that phase (file existence + frontmatter `status: final` where applicable).
2. Read `migration-state.json` to memory.
3. Update `domains[<slug>].status` to the new phase value.
4. Update `domains[<slug>].last_updated` to current ISO 8601 UTC.
5. If every migration-target domain has reached this phase, append the phase name to `phases_complete`.
6. Write atomically: serialize to `.tmp`, validate against schema, rename to `migration-state.json`.

Never modify any file under `spec-driven/<slug>/` from the migration skill. The sds skills own that directory.
