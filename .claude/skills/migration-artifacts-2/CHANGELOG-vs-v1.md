# CHANGELOG: v2 vs v1

Why v1 was insufficient for large-app migrations, and what v2 changes.

| # | Capability | v1 | v2 | Why v1 fails at scale |
|---|------------|----|----|------------------------|
| 1 | **Context overflow** | Single discovery agent scans entire `LEGACY_PATH` | Per-module scanners; each bounded to ~50K LOC; synthesis works on summaries only | A 4M LOC scan exceeds any model's effective context; agent silently truncates or hallucinates |
| 2 | **Persistent state** | None — state lives in agent memory and filesystem only | `migration-state.json` schema + atomic read/modify/write protocol | Multi-month migrations cannot fit in one session; v1 forgets between invocations |
| 3 | **Resumability** | Re-run all phases or manually inspect outputs | Scheduler reads state, dispatches only pending agents | At 12-month duration, you will be interrupted dozens of times; v1 has no resume |
| 4 | **Sub-domain decomp** | Domain is the smallest unit | `feature-spec.md` splits domains over 200K LOC into features | A single "orders" domain at 800K LOC still overflows; v1 has no answer |
| 5 | **Parallel scheduler** | Manual: "dispatch in parallel" with no concurrency limit | Scheduler with per-phase caps (execute=4, verify=20, decommission=1) | Unbounded parallelism causes git lock contention, race conditions, and CI thrashing |
| 6 | **Shared kernel handling** | Not addressed | `shared-kernel-inventory.md` identifies, decides extract/duplicate/split per file | Cross-domain shared code at scale = silent coupling that breaks domain isolation |
| 7 | **Contract registry** | Not addressed | `contract-registry.md` + OpenAPI templates with versioning + SLA | Without a registry, breaking changes ship and cross-domain integration regresses |
| 8 | **Team ownership** | Not addressed | `team-ownership-map.md` → CODEOWNERS template | At 10+ engineers, "who owns this" is the #1 question; v1 leaves it ambiguous |
| 9 | **Migration order** | Mentioned in domain-decompose (basic dep graph) | Dedicated `migration-order.md` with risk weighting, parallel groups, Gantt | Wrong order = blocking integration debt and rework |
| 10 | **Strangler-fig automation** | Mentioned in `large-app-migration-strategy.md` but no artifacts | Phase 06 produces working nginx/ALB/CFW configs + feature-flag wiring + fallback middleware + canary schedule | At scale you cannot manually write 50 routing configs and 200 flags; needs generation |
| 11 | **Feature-flag wiring** | Not addressed | `feature-flag-wiring.md` outputs server + client gate code for LD/Unleash/Statsig | Without flags there is no fast rollback; v1's "revert PR" doesn't work for traffic mid-flight |
| 12 | **Fallback logic** | Not addressed | `fallback-logic.md` produces circuit-breaker middleware | New system will fail in production; v1 has no graceful degradation |
| 13 | **Canary rollout with SLO gates** | Mentioned in strategy doc; not artifact-backed | `canary-rollout.md` produces `canary-schedule.yaml` with error-rate, p95, traffic-delta thresholds and auto-rollback triggers | Without SLO gates, ramp goes by gut; bad ramps stay bad until on-call notices |
| 14 | **API diff harness** | Verify mentions API diff conceptually; no implementation | Phase 08: working harness template (`api-diff-harness.ts`), semantic-equivalence YAML rules, diff runner | At 1000s of endpoints, manual diff inspection is impossible; needs runnable harness |
| 15 | **Performance verify** | Not in v1's 6 dims | `07-verify/performance.md` (k6/locust, p50/p95/p99 vs baseline, fail >10% regression) | Code can be functionally correct and 5x slower; v1 misses this entirely |
| 16 | **Observability verify** | Not in v1's 6 dims | `07-verify/observability.md` (structured logs, trace propagation, key metrics, dashboard existence) | New system without observability = invisible incidents |
| 17 | **Compliance verify** | Not in v1's 6 dims | `07-verify/compliance.md` (PII tagging, GDPR delete-flow, audit log, SOC2 controls) | Large apps usually carry regulatory obligations; v1 cannot certify these |
| 18 | **Data-parity verify** | Not in v1's 6 dims | `07-verify/data-parity.md` (row-level diff between legacy and new DB) | Dual-write windows produce silent drift; v1 doesn't catch it |
| 19 | **Decommission phase** | Not in v1 | Phase 09: traffic-verify → dependency-check → archival → soft-delete → hard-delete with gates | Legacy code lives forever in v1; the "migration" is never actually done |
| 20 | **Rollback runbooks** | Not in v1 | `_shared/rollback-runbook-template.md` per domain, recorded in state | Without runbooks, rollback is improvised at 3am during an incident |

---

## Phase Count

- v1: **7 phases** (Discovery, Decompose, Spec, Design, Tasks, Execute, Verify)
- v2: **10 phases** (above + Strangler-Fig, API-Diff, Decommission)

## Verify Dimensions

- v1: **6** (traceability, completeness, code-quality, test-quality, regression, security)
- v2: **10** (above + performance, observability, compliance, data-parity)

## Sub-Agents

- v1: **7** sub-agents
- v2: **~40** sub-agents (per-module discovery, contract design, strangler-fig agents, expanded verify, API-diff, decommission)

## State Model

- v1: filesystem-as-state (presence of `spec.md`, `design.md` etc.)
- v2: `migration-state.json` as authoritative state; filesystem outputs are artifacts derived from state

## Concurrency Model

- v1: "dispatch in parallel" with no caps
- v2: per-phase concurrency caps enforced by scheduler

## Coverage of `large-app-migration-strategy.md`

v1 included `large-app-migration-strategy.md` as a conceptual doc but no executable artifacts for: strangler-fig routing, feature flags, API diff, canary ramps, decommission. v2 makes every concept in that doc into an executable sub-agent with templates.
