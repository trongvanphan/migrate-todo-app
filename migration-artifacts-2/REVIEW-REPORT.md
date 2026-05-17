# Independence Review of migration-artifacts-2/

## Verdict
**PASS WITH CAVEATS**

## Summary
`migration-artifacts-2/` is largely portable: no hardcoded user paths or repo-specific app names appear anywhere in the artifacts. After fixing the issues called out below, every sub-agent is self-contained (Parameters, Output Files, Context Budget, Completion). One CRITICAL leak referencing v1 was removed from `workflow.md`. The remaining issues are HIGH/MEDIUM polish items: a handful of sub-agents use `parameters.X` notation inconsistently with `{{X}}` placeholder usage in their bodies, and a few discovery/decompose sub-agents reference output-template placeholders (`{{DOMAIN}}`, `{{MODULE}}`) without declaring them in Parameters because the agent itself derives them. The 10 verify dimensions, the 10 phase folders (00–09), and the strangler/api-diff/decommission templates are all present and valid.

## Findings by Severity

### CRITICAL (blocks portability) — FIXED
- `workflow.md` §6 referenced `migration-artifacts/workflow.md` (v1) by relative path. Replaced with a self-contained description of the `tech-stack.json` declaration. v2 must not depend on v1 being present.
- 20 sub-agents under `06-strangler-fig/`, `07-verify/`, `08-api-diff/`, `09-decommission/`, and `05-execute/pr-strategy.md` lacked any reference to context-budget rules. Added a `## Context Budget` section pointing to `sub-agents/_shared/context-budget-rules.md`.
- 6 verify sub-agents (`code-quality`, `test-quality`, `traceability`, `compliance`, `observability`, `security`) used `{{OUTPUT_PATH}}` in their command bodies without declaring it in Parameters. Added the declaration.
- `sub-agents/05-execute/fixture-migration.md` used `{{LEGACY_PATH}}` and `{{OUTPUT_PATH}}` without declaring them. Added the declarations.

### HIGH (works but with friction)
- Inconsistent placeholder notation in some sub-agents: bodies use `{{FEATURE_FLAG_SYS}}`, `{{ROUTING_LAYER}}`, `{{LEGACY_UPSTREAM}}`, `{{NEW_UPSTREAM}}` but the Parameters section declares them as `parameters.FEATURE_FLAG_SYS`, `parameters.ROUTING_LAYER` etc. Either harmonize to `{{X}}` everywhere or document the `parameters.X` convention explicitly in `_shared/`.
  - Affected: `sub-agents/06-strangler-fig/feature-flag-wiring.md`, `sub-agents/06-strangler-fig/routing-config.md`.
- `sub-agents/01-decompose/domain-decompose.md` declares "None" in Parameters but uses `{{DOMAIN}}` in output-path templates. Should be re-stated as "this sub-agent emits one charter per discovered domain; `{{DOMAIN}}` is iterator output, not input".
- `sub-agents/00-discovery/api-routes-scan.md` and `code-map-scan.md` use `{{MODULE_SLUG}}` in output paths without declaring it. Either declare or rename to `{{MODULE}}`/use derived value.
- `sub-agents/02-spec/domain-spec.md` body uses `{{LOC}}` and `{{MODULE}}` (only `{{DOMAIN}}` declared). Should add or move to derived state.

### MEDIUM (polish)
- SKILL.md mentions the 10 verify dimensions by short name (`traceability, completeness, …`) but does not list the 10 file paths individually. Adding the explicit paths (`sub-agents/07-verify/<dim>.md`) would mirror the formatting used for phases 06, 08, 09.
- `coordinator/scheduler.md` does not reference fields like `phases_complete`, `shared_kernel`, `contracts`, `rollback_history`, or `blockers` that are declared in `migration-state.schema.json`. The algorithm references only `status` and `ramp_percent`. Consider extending the algorithm to use the richer schema (or pruning the schema to what is actually consumed).
- `README.md` mentions a generic `{{PLACEHOLDERS}}` token in narrative prose; harmless but flagged by the placeholder-consistency check.
- `templates/rollback-runbook.md` has many placeholders (e.g. `{{DATE}}`, `{{LAST_MERGE_SHA}}`, `{{REVERT_COMMAND}}`) without a dedicated "Variables" section. Templates are meant to be filled in, but listing the variables up top is a quality-of-life improvement.
- `templates/api-diff-harness.ts` imports the `yaml` package (third-party) in addition to `node:fs`/`node:readline` and uses the global `fetch`. The harness header should add a one-line install hint (`npm i -D yaml ts-node typescript @types/node`).

### LOW (nits)
- `_shared/` files (rollback-runbook-template, context-budget-rules, commit-conventions, handoff-format) have no Parameters/Output/Completion sections by design (they are reference docs), but a one-line "Usage" header would make their role explicit.
- `workflow.md` line 170 path template uses `{{F}}` (feature). Consistent naming would be `{{FEATURE}}` matching the spec sub-agent.

## Check-by-check results

1. **External path leakage** — PASS. Zero hits for `/Users/trongpv6`, `migrate-todo-app`, `todo-angular-firebase-demo`, `todo-app-migrated`.
2. **v1 dependency leakage** — Was 1 hit in `workflow.md:207`. FIXED. Now zero hits (other than `CHANGELOG-vs-v1.md`).
3. **Self-containment** — All 50+ sub-agents now have Parameters, Output Files, Context Budget reference, and Completion sections after fixes. (`_shared/*.md` exempt — they are templates.)
4. **Placeholder consistency** — Sub-agents resolved for `{{OUTPUT_PATH}}`/`{{LEGACY_PATH}}`. Six minor cases remain (listed under HIGH/MEDIUM): output-iterator placeholders and the `parameters.X` notation drift.
5. **SKILL.md references all sub-agents** — All sub-agent files are reachable from SKILL.md by phase folder; the 10 verify dimensions are listed by name on line 151 (not by full path — see MEDIUM).
6. **State file schema vs scheduler vs sub-agents** — Scheduler reads `status` and `ramp_percent`, both in schema. Scheduler does not exercise `phases_complete`, `shared_kernel`, `contracts`, `rollback_history`, `blockers` — see MEDIUM.
7. **Template validity** —
   - `api-diff-harness.ts`: imports `node:fs`, `node:readline`, `yaml`. Uses global `fetch`. Valid TS.
   - `contract.openapi.yaml`: has `openapi: 3.1.0`, `info`, `paths`, `components`. Valid OpenAPI structure.
   - `strangler-config-nginx.conf`: valid `upstream`, `server`, `location`, `split_clients` directives.
   - `strangler-config-alb.tf`: valid `aws_lb_target_group`, weighted forward action, variables block.
   - `strangler-config-cloudflare-worker.js`: exports default `fetch` handler. Valid Worker shape.
   - `codeowners.txt`: valid `path @org/team` format.
8. **10 verify dimensions exist** — PASS. All 10 files present: traceability, completeness, code-quality, test-quality, regression, security, performance, observability, compliance, data-parity.
9. **Phase numbering consistency** — PASS. SKILL.md phases 00–09 match folders `00-discovery`, `01-decompose`, `02-spec`, `03-design`, `04-tasks`, `05-execute`, `06-strangler-fig`, `07-verify`, `08-api-diff`, `09-decommission`.
10. **README accuracy** — PASS. README explicitly lists all 10 phases (line 15, 25) and describes the folder layout.

## Files fixed by this review
- `workflow.md` — removed v1 cross-reference in §6.
- `sub-agents/07-verify/code-quality.md` — added `{{OUTPUT_PATH}}` Parameter + Context Budget section.
- `sub-agents/07-verify/completeness.md` — added Context Budget section.
- `sub-agents/07-verify/data-parity.md` — added Context Budget section.
- `sub-agents/07-verify/test-quality.md` — added `{{OUTPUT_PATH}}` Parameter + Context Budget section.
- `sub-agents/07-verify/performance.md` — added Context Budget section.
- `sub-agents/07-verify/traceability.md` — added `{{OUTPUT_PATH}}` Parameter + Context Budget section.
- `sub-agents/07-verify/regression.md` — added Context Budget section.
- `sub-agents/07-verify/compliance.md` — added `{{OUTPUT_PATH}}` Parameter + Context Budget section.
- `sub-agents/07-verify/observability.md` — added `{{OUTPUT_PATH}}` Parameter + Context Budget section.
- `sub-agents/07-verify/security.md` — added `{{OUTPUT_PATH}}` Parameter + Context Budget section.
- `sub-agents/08-api-diff/diff-runner.md` — added Context Budget section.
- `sub-agents/08-api-diff/semantic-equivalence.md` — added Context Budget section.
- `sub-agents/08-api-diff/harness-setup.md` — added Context Budget section.
- `sub-agents/05-execute/pr-strategy.md` — added Context Budget section.
- `sub-agents/05-execute/fixture-migration.md` — added `{{LEGACY_PATH}}` and `{{OUTPUT_PATH}}` Parameters.
- `sub-agents/06-strangler-fig/feature-flag-wiring.md` — added Context Budget section.
- `sub-agents/06-strangler-fig/fallback-logic.md` — added Context Budget section.
- `sub-agents/06-strangler-fig/canary-rollout.md` — added Context Budget section.
- `sub-agents/09-decommission/dependency-check.md` — added Context Budget section.
- `sub-agents/09-decommission/traffic-verify.md` — added Context Budget section.
- `sub-agents/09-decommission/safe-removal.md` — added Context Budget section.
- `sub-agents/09-decommission/data-archival.md` — added Context Budget section.
