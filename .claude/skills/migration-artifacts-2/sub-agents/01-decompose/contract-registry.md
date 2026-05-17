# Sub-Agent: Contract Registry

You enumerate every cross-domain contract (REST, gRPC, GraphQL, event, internal RPC) and write the registry that all downstream phases reference.

---

## Parameters

None. Reads from `discovery/`, `domains/`.

---

## Output Files

- `domains/_contracts.yaml` — single source of truth for contracts
- Update `migration-state.json.contracts[]`

---

## Context Budget

Read `discovery/modules/*/api-routes.md` headers + `domains/_index.md`. Do not load full route lists; use aggregate counts.

---

## Algorithm

1. For each route/endpoint in `discovery/modules/*/api-routes.md`:
   - Map the handler file → owning domain (via `domains/_index.md`).
   - Search for callers of the endpoint. Callers in *other* domains = consumers.
2. For each cross-domain caller: emit a contract entry.
3. For each `*.proto` / `*.graphql` definition: emit a contract entry.
4. For each Kafka topic / SQS queue / event bus emission: emit a contract entry (kind=event).
5. Group by owner_domain.

---

## Output: `domains/_contracts.yaml`

```yaml
version: 1
generated_at: "{ISO}"
contracts:
  - name: auth.verify-token
    version: "1.0"
    kind: rest
    owner_domain: auth
    consumers: [orders, customers, billing, reporting]
    schema_path: contracts/auth/verify-token.openapi.yaml   # to be created in 03-design
    sla:
      p95_ms: 50
      availability: 0.999
    deprecation_date: null

  - name: catalog.product-updated
    version: "2.0"
    kind: event
    owner_domain: catalog
    consumers: [search, cart, reporting]
    schema_path: contracts/catalog/product-updated.avsc
    sla:
      delivery: at-least-once
      lag_p95_ms: 1000
    deprecation_date: null

  - name: orders.create
    version: "1.0"
    kind: rest
    owner_domain: orders
    consumers: [checkout-web, mobile-app]
    schema_path: contracts/orders/create.openapi.yaml
    sla:
      p95_ms: 300
      availability: 0.995

# ... one entry per detected contract
```

---

## Rules

- **Every cross-domain call is a contract**. No exceptions.
- **Contract = stability boundary**. Inputs and outputs must not change without a new version.
- **Versioning**: `MAJOR.MINOR`. Breaking change → new MAJOR endpoint (e.g., `/v2/auth/verify-token`).
- **Deprecation**: every contract starts with `deprecation_date: null`. Filling this field begins the sunset clock.
- **SLA**: at minimum `p95_ms` and `availability` for synchronous; `delivery` and `lag` for async.

---

## State File Update

Mirror every entry into `migration-state.json.contracts[]`. Include `schema_path` so `03-design/contract-design.md` knows where to write the OpenAPI/Protobuf.

---

## Completion

```
[CONTRACT-REGISTRY COMPLETE]
Contracts: {N total} (rest: {N}, grpc: {N}, graphql: {N}, event: {N})
File: domains/_contracts.yaml

HUMAN GATE: API owners per domain confirm contract list before Phase 03.
```
