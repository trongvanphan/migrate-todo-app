# Sub-Agent: Domain Design

You produce the architectural design for one domain, satisfying its spec and the contracts it owns.

Differs from v1 design in three ways: it must (1) cross-check the contract registry, (2) list shared-kernel dependencies, (3) include an observability plan.

---

## Parameters

- `{{DOMAIN}}`
- `{{TECH_STACK}}` (read from `migration-state.json.parameters.TECH_STACK`)

---

## Output Files

- `domains/{{DOMAIN}}/design.md` (≤2000 lines)
- `state/handoff/design/{{DOMAIN}}.json`

---

## Context Budget

Read:
- `domains/{{DOMAIN}}/spec.md` (or per-feature specs aggregated)
- `domains/{{DOMAIN}}/charter.md`
- `domains/_contracts.yaml` (filter to this domain)
- `domains/_shared-kernel.md` (sections affecting this domain)
- `state/handoff/spec/{{DOMAIN}}.json`

---

## Required Sections

```markdown
# Design — {{DOMAIN}}

## Architecture overview
- Service shape: {monolith-module | standalone-service | function-set}
- Internal layers: handlers → services → repositories → adapters
- Deployment unit: {pod | function | shared-process}

## Directory structure
```
{OUTPUT_PATH}/{{DOMAIN}}/
├── api/             ← inbound: HTTP/gRPC/event handlers
├── services/        ← business logic
├── repositories/    ← data access
├── adapters/        ← outbound: clients for other domains' contracts
├── domain/          ← types, value objects, domain events
├── infra/           ← config, logging, tracing setup
└── __tests__/
```

## Contract implementation (inbound — what this domain serves)

For each contract this domain owns (from registry):

### {contract.name} v{version}
- **Handler path**: `api/{handler}.ts`
- **Service**: `services/{service}.ts`
- **Validation**: {schema source}
- **Auth**: {how requests are authenticated}
- **SLA budget allocation**: handler {X}ms + service {Y}ms + repo {Z}ms

## Outbound calls (consuming other domains' contracts)

For each outbound contract:
### {contract.name}
- **Caller path**: `adapters/{name}-client.ts`
- **Retry policy**: {N retries, exponential backoff}
- **Timeout**: {ms}
- **Circuit breaker**: {threshold}
- **Fallback**: {behavior on failure — see also 06-strangler-fig/fallback-logic.md}

## Shared kernel dependencies

From `domains/_shared-kernel.md`, list libraries this domain consumes:
| Library | Why | Version pin |
|---------|-----|-------------|

If any decision is `split` or `pending`, list as a **blocker**.

## Data model

Database tables/collections owned. Reference `domains/{{DOMAIN}}/data-migration.md` for schema diff and migration plan.

## Observability plan

**Required at scale.** For every endpoint and background job:
- **Logs**: structured JSON; required fields: `request_id`, `domain={{DOMAIN}}`, `actor`, `route`, `duration_ms`, `status`.
- **Metrics**: Prometheus counter `{{DOMAIN}}_requests_total{route, status}`, histogram `{{DOMAIN}}_request_duration_ms{route, quantile}`.
- **Traces**: OpenTelemetry span per handler; propagate `traceparent` header on outbound calls.
- **Audit**: every write produces an audit event to `audit_log` table or Kafka topic `audit.{{DOMAIN}}`.

## Error handling
- Domain errors: typed errors per FR category
- 4xx vs 5xx mapping table
- Never leak stack traces in responses

## Security
- Auth at every inbound entry point
- Input validation at handler boundary
- Output encoding for any user-influenced content
- Compliance hooks per `parameters.COMPLIANCE_SCOPE`

## Decisions log
- DEC-1: {decision} — {rationale}

## Open risks
- R-{id}: {risk} → mitigation in design/tasks
```

---

## Cross-check requirements

Before completing, validate:
1. Every FR in `spec.md` has a section in design (handler + service + test path).
2. Every contract in `_contracts.yaml` with `owner_domain={{DOMAIN}}` has an implementation section.
3. Every `outbound` contract has an adapter section.
4. Every shared-kernel `split` decision is listed as a blocker.

If validation fails, list gaps explicitly under `## Validation gaps` and DO NOT mark phase complete.

---

## State / Handoff

- Update `domains[{{DOMAIN}}].status = "design"`.
- Write `state/handoff/design/{{DOMAIN}}.json` with key decisions.

---

## Completion

```
[DOMAIN-DESIGN COMPLETE: {{DOMAIN}}]
Inbound contracts: {N}, Outbound: {N}, Shared kernel deps: {N}
Validation gaps: {N} (must be 0 to proceed)
File: domains/{{DOMAIN}}/design.md
```
