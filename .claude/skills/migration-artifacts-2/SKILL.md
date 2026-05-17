---
name: migration-artifacts-2
description: SDS migration orchestration for any size repository — single-page app to multi-million-LOC monolith. Delegates per-domain spec, design, task, execute, and verify work to the sds.* skill suite. Adds the migration-specific concerns sds does not cover — discovery, domain decomposition, strangler-fig routing, API-diff harness, canary rollout, decommission — plus a persistent state file that coordinates parallel execution. Trigger phrases — "migrate this app", "/migration-v2", "strangler migration", "decompose this legacy app", "run the migration pipeline", "migrate to <stack>".
---

# Migration Orchestration Skill (v2, sds-delegating)

You orchestrate the migration of a legacy application to a new stack. The pipeline is **scale-adaptive**: a single-domain SPA runs through the same phases as a 4M-LOC monolith — the number of domains, concurrency, and parallelism scale to fit. You do **not** write specs, designs, tasks, code, or verification reports yourself. For every domain, you invoke the `sds.*` skill suite — one phase at a time — and treat its output files as the canonical per-domain artifacts.

This skill owns:
- Discovery of the legacy codebase (Phase 00)
- Decomposition into domains and shared kernel (Phase 01)
- Strangler-fig routing, feature flags, fallback, canary (Phase 06)
- API-diff harness against the legacy app (Phase 08)
- Decommission of legacy code (Phase 09)
- The cross-domain `migration-state.json` file
- Concurrency caps and the scheduler

This skill delegates:
- Per-domain Spec (Phase 02) → `/sds.spec`
- Per-domain Design (Phase 03) → `/sds.design`
- Per-domain Tasks (Phase 04) → `/sds.task`
- Per-domain Execute (Phase 05) → `/sds.execute`
- Per-domain Verify (Phase 07) → `/sds.verify`

Detailed delegation contract: [references/sds-delegation.md](references/sds-delegation.md). Read it before dispatching any sds phase.

---

## Pre-Made Decisions

Collected at invocation. Persisted to `migration-state.json` under `parameters`.

```
LEGACY_PATH        absolute path to legacy app
OUTPUT_PATH        absolute path for new app(s)
APP_SIZE_LOC       approximate LOC of the legacy app
TECH_STACK         target stack JSON (backend, frontend, db, auth)
TIMELINE_MONTHS    expected duration
TEAM_SIZE          engineers across all domains
DOMAINS            "auto" to derive in Phase 01, or explicit list of slugs
FEATURE_FLAG_SYS   LaunchDarkly | Unleash | Statsig | custom  (Phase 06)
ROUTING_LAYER      nginx | alb | cloudflare-worker | envoy    (Phase 06)
COMPLIANCE_SCOPE   array of: none | gdpr | soc2 | hipaa | pci | iso27001
LIVE_TRAFFIC       true | false  — when false, Phases 06, 08, 09 are skipped
```

If `COMPLIANCE_SCOPE` is unknown, ask the user. Do not invent a default — it changes Phase 07 verify rules.

If `LIVE_TRAFFIC=false` (greenfield rewrite, no production traffic to shift), Phases 06, 08, and 09 are explicitly skipped and the run completes after Phase 07.

---

## Scale Adaptation

The pipeline runs the same phases regardless of repo size; only fan-out changes.

| Repo size | Domains expected | Concurrency | Adaptation |
|---|---|---|---|
| <10K LOC, SPA or single service | 1 | All caps collapse to 1 | Phase 00 scanners run once over the whole tree (skip per-module fan-out). Phase 01 produces one domain entry. Phases 02–07 invoke sds once. |
| 10K–100K LOC, few services | 1–3 | Caps as written; usually serial | Per-module scanners apply if `LEGACY_PATH` has 4+ top-level source directories. |
| 100K–1M LOC | 3–8 | Full caps | Standard path. |
| 1M+ LOC | 5–15 | Full caps, sub-domain split | If a domain exceeds the size where one `/sds.spec` session is unwieldy (in practice, when its spec would have >20 FRs), split it into features via a per-feature briefing and run `/sds.spec` per feature. |

The "Minimum N domains" gate is removed. **A single-domain migration is valid.** The decompose phase declares the inventory it finds; the orchestrator does not invent additional domains to hit a minimum.

For repos with a single obvious domain (a CRUD SPA, a CLI, a single-purpose service), Phase 01 produces `domains/_index.md` with one row and skips `_shared-kernel.md` (no cross-domain sharing) and `_migration-order.md` (only one domain to migrate). `_contracts.yaml` is still written when the domain exposes an inbound API.

---

## Artifact Paths

The migration produces artifacts in three trees. Do not blur them.

| Location (relative to workspace root) | Owner | Contents |
|---|---|---|
| `migration-state.json` | this skill | Cross-domain state, parameters, phase progress |
| `discovery/` | this skill | Phase 00 outputs (`SUMMARY.md`, scan results, dependency graph) |
| `domains/` | this skill | Phase 01 outputs (`_index.md`, `_contracts.yaml`, `_codeowners.md`, `_migration-order.md`, and `_shared-kernel.md` when >1 domain) plus per-domain `<slug>/charter.md`, `<slug>/legacy-context.md`, `<slug>/strangler/*`, `<slug>/api-diff-report.md`, `<slug>/verify-supplement.md` |
| `_constraints.md` | this skill | Cross-domain constraints written once at the start of Phase 03 |
| `state/` | this skill | Scheduler outputs (`next-actions.md`, `scheduler.log`) |
| `spec-driven/<slug>/` | the sds.* skills | `spec.md`, `design.md`, `tasks.md`, `bundle-N.md`, `progress-bundle-N.md`, `verify-report.md` |

The migration domain slug **is** the sds spec slug. Domains must be named with the slug format the sds skills accept: lowercase-with-hyphens, ≤64 chars, `[a-z0-9-]+`.

The workspace root is whatever directory the user invokes `/migration-v2` from. The skill writes nothing outside the six paths above plus `spec-driven/`.

---

## Concurrency Model

| Phase | Cap on concurrent domain instances | Notes |
|-------|---------------------|-------|
| 00 Discovery | 8 module-scanners (not domains) | Native scanners (read-only). |
| 01 Decompose | 1 (serial sub-agents) | Serial reasoning over discovery output. |
| 02 Spec | 4 | `/sds.spec` is interactive — parallel runs require separate sessions. |
| 03 Design | 4 | Same as Spec. |
| 04 Tasks | 8 | `/sds.task` is shorter and tolerates more parallelism. |
| 05 Execute | 4 across domains; within a domain, `/sds.execute --parallelism` controls bundle parallelism | Branch isolation is owned by sds.execute. |
| 06 Strangler-fig | 8 | Config generation independent. |
| 07 Verify | 4 | Each `/sds.verify` already spawns 6 internal agents; further parallelism risks token blowup. |
| 08 API-diff | 8 | Native harness. |
| 09 Decommission | 1, serial across domains | Safety: never decommission two domains at once. |

Phases marked "interactive" (02, 03) require human input via the sds gates. The scheduler must surface the gate to the user, not auto-answer.

The scheduler ([coordinator/scheduler.md](coordinator/scheduler.md)) enforces these caps.

---

## Phase 00 — Discovery (native)

For each top-level module of `LEGACY_PATH`, dispatch in parallel (cap=8):
- [sub-agents/00-discovery/code-map-scan.md](sub-agents/00-discovery/code-map-scan.md) with `{{MODULE}}`
- [sub-agents/00-discovery/api-routes-scan.md](sub-agents/00-discovery/api-routes-scan.md) with `{{MODULE}}`
- [sub-agents/00-discovery/test-spec-scan.md](sub-agents/00-discovery/test-spec-scan.md) with `{{MODULE}}`

For DB schemas, dispatch by schema prefix:
- [sub-agents/00-discovery/db-schema-scan.md](sub-agents/00-discovery/db-schema-scan.md) with `{{PREFIX}}`

Once per project:
- [sub-agents/00-discovery/git-log-mining.md](sub-agents/00-discovery/git-log-mining.md) with `{{TIMEFRAME}}`
- [sub-agents/00-discovery/ui-screen-crawl.md](sub-agents/00-discovery/ui-screen-crawl.md)
- [sub-agents/00-discovery/dependency-graph.md](sub-agents/00-discovery/dependency-graph.md)

After all complete:
- [sub-agents/00-discovery/discovery-synthesis.md](sub-agents/00-discovery/discovery-synthesis.md) (writes `discovery/SUMMARY.md`).

**Gate**: `discovery/SUMMARY.md` exists AND `migration-state.json.phases_complete` contains `"discovery"`.

---

## Phase 01 — Decompose (native)

Dispatch serially:
1. [sub-agents/01-decompose/domain-decompose.md](sub-agents/01-decompose/domain-decompose.md) → writes `domains/_index.md`. Each domain's `slug` MUST be in `[a-z0-9-]+` (sds-compatible).
2. [sub-agents/01-decompose/shared-kernel-inventory.md](sub-agents/01-decompose/shared-kernel-inventory.md) → `domains/_shared-kernel.md`.
3. [sub-agents/01-decompose/contract-registry.md](sub-agents/01-decompose/contract-registry.md) → `domains/_contracts.yaml`.
4. [sub-agents/01-decompose/team-ownership-map.md](sub-agents/01-decompose/team-ownership-map.md) → `domains/_codeowners.md`.
5. [sub-agents/01-decompose/migration-order.md](sub-agents/01-decompose/migration-order.md) → `domains/_migration-order.md`.

After completion, for each domain create `domains/<slug>/legacy-context.md` from the template at [templates/legacy-context.md](templates/legacy-context.md). This briefing file is the `--from` input for `/sds.spec` in Phase 02.

**Single-domain branch**: when `domain-decompose.md` produces exactly one domain, steps 2 and 5 collapse: skip `_shared-kernel.md` (no cross-domain sharing exists) and write `_migration-order.md` as a single-line file containing the one slug. Steps 3 and 4 still run.

**Gate**: `domains/_index.md`, `domains/_contracts.yaml`, `domains/_codeowners.md`, `domains/_migration-order.md` exist. `domains/_shared-kernel.md` exists when domain count >1. Per-domain `domains/<slug>/charter.md` and `domains/<slug>/legacy-context.md` exist for every domain. State has `"decompose"` complete. **Domain expert review required** before Phase 02.

---

## Phase 02 — Spec (delegate to /sds.spec)

For each domain slug (parallel, cap=4):

```
/sds.spec <slug> --from domains/<slug>/legacy-context.md --draft
```

`--draft` is mandatory: it synthesizes a spec from the legacy briefing and presents it for user validation, rather than running full interactive elicitation from scratch. The user reviews and refines.

**Do not pre-write `spec-driven/<slug>/spec.md`** — `/sds.spec` owns that path.

**Gate per domain**: `spec-driven/<slug>/spec.md` exists with frontmatter `status: final`. Update `migration-state.json.domains[<slug>].status` to `"spec"`.

Full delegation details (briefing format, --draft fallback, multi-project handling): [references/sds-delegation.md](references/sds-delegation.md#phase-02).

---

## Phase 03 — Design (delegate to /sds.design)

For each domain slug whose spec is final (parallel, cap=4):

```
/sds.design <slug> --context _constraints.md
```

`_constraints.md` is written once per migration; it lists the `TECH_STACK`, `COMPLIANCE_SCOPE`, NFR baselines, and any architectural standards that apply across domains. Each `/sds.design` run reads it as additional context to its base research.

**Gate per domain**: `spec-driven/<slug>/design.md` exists with `status: final`. Update domain status to `"design"`. **API owner review required** if domain exposes inbound contracts.

Full delegation details, including how to inject contract requirements from `domains/_contracts.yaml`: [references/sds-delegation.md](references/sds-delegation.md#phase-03).

---

## Phase 04 — Tasks (delegate to /sds.task)

For each domain slug whose design is final (parallel, cap=8):

```
/sds.task <slug>
```

If a domain's design points to a known migration strategy (e.g. data migration first, then API), pass `--strategy dependency-first` when invoking.

**Gate per domain**: `spec-driven/<slug>/tasks.md` exists AND at least `spec-driven/<slug>/bundle-1.md` and `spec-driven/<slug>/progress-bundle-1.md` exist. Update domain status to `"tasks"`.

Full delegation details: [references/sds-delegation.md](references/sds-delegation.md#phase-04).

---

## Phase 05 — Execute (delegate to /sds.execute)

For each domain slug, respecting the order in `domains/_migration-order.md` (cap=4 concurrent domain instances):

```
/sds.execute <slug> --parallelism <N>
```

`N` is bounded by the Phase 05 row in the Concurrency Model. `/sds.execute` handles branch isolation on `spec-driven/<slug>/exec`, per-bundle commits with `[STEP-N]` traceability, and the merge-back gate.

After `/sds.execute` completes for a domain, the migration scheduler must record the integration branch in `migration-state.json.domains[<slug>].branch = "spec-driven/<slug>/exec"`.

**Gate per domain**: every `spec-driven/<slug>/progress-bundle-N.md` shows all steps as `done`. CI must be green on `spec-driven/<slug>/exec`. Update domain status to `"execute"`.

Failure handling: if `/sds.execute` reports a step as `blocked` and cannot recover, the migration scheduler records a blocker in `migration-state.json.domains[<slug>].blockers[]` and stops further phase advancement for that domain. Do not skip the failed bundle.

Full delegation details: [references/sds-delegation.md](references/sds-delegation.md#phase-05).

---

## Phase 06 — Strangler-Fig (native; skipped when `LIVE_TRAFFIC=false`)

For each domain (parallel, cap=8):
1. [sub-agents/06-strangler-fig/routing-config.md](sub-agents/06-strangler-fig/routing-config.md) — uses `ROUTING_LAYER`. Writes `domains/<slug>/strangler/routing.{conf|tf|js}`.
2. [sub-agents/06-strangler-fig/feature-flag-wiring.md](sub-agents/06-strangler-fig/feature-flag-wiring.md) — uses `FEATURE_FLAG_SYS`. Writes `domains/<slug>/strangler/flags.yaml`.
3. [sub-agents/06-strangler-fig/fallback-logic.md](sub-agents/06-strangler-fig/fallback-logic.md) — writes `domains/<slug>/strangler/fallback.md`.
4. [sub-agents/06-strangler-fig/canary-rollout.md](sub-agents/06-strangler-fig/canary-rollout.md) — writes `domains/<slug>/strangler/canary-schedule.yaml`.

**Gate per domain**: all four files exist. **SRE review required** before any canary ramp begins. Update domain status to `"strangler"`.

---

## Phase 07 — Verify (delegate to /sds.verify)

For each domain (parallel, cap=4):

```
/sds.verify <slug>
```

`/sds.verify` dispatches 6 parallel verification agents internally (traceability, completeness, quality, testing, regression, security). The migration skill maps these onto the broader 10-dimension scoreboard:

| sds dimension | Migration scoreboard slot |
|---|---|
| traceability | traceability |
| completeness | completeness |
| quality | code-quality |
| testing | test-quality |
| regression | regression |
| security | security |

The four remaining migration dimensions — performance, observability, compliance, data-parity — are not produced by `/sds.verify`. For each, dispatch the corresponding native sub-agent if the domain's NFRs or `COMPLIANCE_SCOPE` require it:
- [sub-agents/07-verify/performance.md](sub-agents/07-verify/performance.md)
- [sub-agents/07-verify/observability.md](sub-agents/07-verify/observability.md)
- [sub-agents/07-verify/compliance.md](sub-agents/07-verify/compliance.md)
- [sub-agents/07-verify/data-parity.md](sub-agents/07-verify/data-parity.md)

Aggregate findings into `domains/<slug>/verify-supplement.md`. The canonical verify artifact is `spec-driven/<slug>/verify-report.md`; the supplement covers only the four extra dimensions.

**Gate per domain**: zero CRITICAL findings open across `spec-driven/<slug>/verify-report.md` AND `domains/<slug>/verify-supplement.md`. Update domain status to `"verify"`.

Full delegation details: [references/sds-delegation.md](references/sds-delegation.md#phase-07).

---

## Phase 08 — API-Diff (native; skipped when `LIVE_TRAFFIC=false`)

For each domain whose design names inbound contracts (parallel, cap=8):
1. [sub-agents/08-api-diff/harness-setup.md](sub-agents/08-api-diff/harness-setup.md) — installs harness from [templates/api-diff-harness.ts](templates/api-diff-harness.ts).
2. [sub-agents/08-api-diff/semantic-equivalence.md](sub-agents/08-api-diff/semantic-equivalence.md) — defines tolerated diffs.
3. [sub-agents/08-api-diff/diff-runner.md](sub-agents/08-api-diff/diff-runner.md) — runs continuously at every canary ramp step.

**Gate per domain**: `domains/<slug>/api-diff-report.md` shows <0.1% unexplained diffs at current ramp. Update domain status to `"api-diff"`.

---

## Phase 09 — Decommission (native; skipped when `LIVE_TRAFFIC=false`)

Only run after `ramp_percent = 100` AND stable for 7+ days AND tech-lead + product approval.

Per domain, serial across domains:
1. [sub-agents/09-decommission/traffic-verify.md](sub-agents/09-decommission/traffic-verify.md)
2. [sub-agents/09-decommission/dependency-check.md](sub-agents/09-decommission/dependency-check.md)
3. [sub-agents/09-decommission/data-archival.md](sub-agents/09-decommission/data-archival.md)
4. [sub-agents/09-decommission/safe-removal.md](sub-agents/09-decommission/safe-removal.md)

**Gate per domain**: `migration-state.json.domains[<slug>].status = "decommissioned"`.

---

## State File Management

Every native sub-agent **must**:
- Read `migration-state.json` at start. Stop with error if a required precondition is unmet.
- Write back updates atomically: read → modify → write to `.tmp` → rename.
- Append to `rollback_history` on any destructive change.

The sds skills **do not** read or write `migration-state.json`. The migration scheduler is responsible for reflecting sds phase progress into the state file after each delegation returns.

Schema: [coordinator/migration-state.schema.json](coordinator/migration-state.schema.json). Validate after every write.

---

## Scheduler Loop

Between phases, and on resume, invoke [coordinator/scheduler.md](coordinator/scheduler.md). The scheduler:
1. Reads `migration-state.json`.
2. Determines the next dispatchable phase per domain, respecting `_migration-order.md` and the concurrency caps above.
3. Writes `state/next-actions.md`.

The orchestrator dispatches the listed actions. For sds-delegated phases, the action is a `/sds.<phase> <slug>` invocation, not a sub-agent path.

---

## Mandatory Human Gates

These gates require human review before the next phase begins. Surface decisions to the user; do not auto-advance.

- After 01-decompose: domain expert confirms boundaries.
- During 02-spec: `/sds.spec`'s own gates fire (gap analysis, post-elicitation validation). Do not auto-answer.
- During 03-design: `/sds.design`'s four gates fire (Research Scope, Research Findings, Design Review, Commit Decision).
- During 04-tasks: `/sds.task`'s gates fire (Decomposition Approach, Task Review, Commit Decision).
- During 05-execute: `/sds.execute`'s per-bundle review gates fire (unless `--skip-review` is explicitly chosen by the user).
- Before 06-strangler-fig: SRE approves routing config.
- Before each canary ramp: SRE approves SLO baseline.
- During 07-verify: present `/sds.verify`'s remediation choices to the user.
- Before 09-decommission: tech lead + product approve removal.

---

## Error Handling

- Sub-agent writes no output: retry once with "ensure file written" instruction. If still empty, mark phase blocked.
- State file conflict (concurrent write): the scheduler serializes; never edit state mid-flight.
- sds skill stops with an error: surface verbatim to the user; do not retry blindly. Many sds errors are user-action required (missing spec, missing slug, accessibility failure).
- Phase 07 CRITICAL finding: block phase; do not advance ramp; surface to user with the relevant report path.
- Canary SLO breach: trigger automatic rollback per `domains/<slug>/strangler/canary-schedule.yaml`. Mark `domains[<slug>].status = "rolled_back"` and append to `rollback_history` with `triggered_by = "slo_breach"`.

---

## Skill Entry Point

When the user invokes `/migration-v2`:

1. Initialize `migration-state.json` from [coordinator/migration-state.schema.json](coordinator/migration-state.schema.json) defaults.
2. Collect all Pre-Made Decisions. Persist them.
3. If `LIVE_TRAFFIC=false`, mark Phases 06, 08, 09 as `skipped` in `phases_complete` with reason `"greenfield-no-live-traffic"`.
4. Dispatch Phase 00.
5. After each phase, invoke [coordinator/scheduler.md](coordinator/scheduler.md) to compute next actions.
6. Loop until every migration-target domain has status `"decommissioned"` (live traffic) or `"verify"` (greenfield).

Before dispatching any sds phase, read [references/sds-delegation.md](references/sds-delegation.md) for the exact invocation contract.
