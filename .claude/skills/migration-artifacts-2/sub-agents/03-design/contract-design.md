# Sub-Agent: Contract Design

For each contract owned by `{{DOMAIN}}` per `domains/_contracts.yaml`, generate the formal schema document (OpenAPI / Protobuf / Avro / GraphQL SDL).

---

## Parameters

- `{{DOMAIN}}`

---

## Output Files

- `contracts/{{DOMAIN}}/{contract-name}.{openapi.yaml|proto|avsc|graphql}` per contract
- Update `domains/_contracts.yaml` with `schema_path` populated
- `state/handoff/design/{{DOMAIN}}__contracts.json`

---

## Context Budget

Read only:
- `domains/_contracts.yaml`
- `domains/{{DOMAIN}}/spec.md`
- `templates/contract.openapi.yaml` as starting template

---

## Per-Contract Output

For a REST contract, use `templates/contract.openapi.yaml`:

```yaml
openapi: 3.1.0
info:
  title: "{contract.name}"
  version: "{contract.version}"
  x-owner-domain: "{{DOMAIN}}"
  x-sla:
    p95_ms: {sla.p95_ms}
    availability: {sla.availability}
paths:
  /...:
    {method}:
      operationId: "..."
      parameters: [...]
      requestBody: {...}
      responses:
        "200": ...
        "400": ...
        "401": ...
        "403": ...
        "404": ...
        "500": ...
```

For gRPC:
```proto
syntax = "proto3";
package {{DOMAIN}}.v{major};
option go_package = "...";

// SLA: p95={sla.p95_ms}ms availability={sla.availability}
// Owner: {{DOMAIN}}

service {ServiceName} {
  rpc {Method}({Request}) returns ({Response});
}

message {Request} { ... }
message {Response} { ... }
```

For events (Avro / JSON Schema):
```json
{
  "type": "record",
  "namespace": "{{DOMAIN}}",
  "name": "{EventName}",
  "version": "{contract.version}",
  "fields": [...]
}
```

---

## API Versioning Rules

1. **Never break a published contract**. Breaking changes = new major version + new endpoint path / proto service.
2. **Additive changes** (new optional field): minor version bump.
3. **Deprecation**: set `deprecation_date` in registry; consumers have 90 days minimum.
4. **Versioned URL paths** for REST: `/v1/...` `/v2/...` (do not use header versioning at scale — too easy to misroute).
5. **Sunsetting**: only after all consumers (per registry) confirm migration.

---

## Validation

For each contract:
- Validate the schema file with the appropriate tool (`openapi-cli validate`, `protoc --lint`, `avro-tools`).
- Diff against legacy behavior using `discovery/modules/{M}/api-routes.md` to ensure no shape regression unless explicitly versioned.

---

## Update Registry

For each contract:
```yaml
schema_path: contracts/{{DOMAIN}}/{contract-name}.openapi.yaml
schema_validated: true
schema_validator_version: openapi-cli@6.x
```

---

## Completion

```
[CONTRACT-DESIGN COMPLETE: {{DOMAIN}}]
Contracts designed: {N}
Validation passed: {N}/{N}
Files: contracts/{{DOMAIN}}/*.{ext}

HUMAN GATE: API owner approves contracts before consumers (other domains) take dependencies.
```
