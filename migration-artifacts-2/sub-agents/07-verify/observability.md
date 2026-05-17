# Sub-Agent: Verify — Observability

You verify the new system emits the logs, traces, and metrics required by `design.md` + adds dashboards.

A new system without observability is an outage waiting to be noticed by customers.

---

## Parameters

- `{{DOMAIN}}`

---

## Output Files

- `domains/{{DOMAIN}}/verify-observability.md`

---

## Checks

### Structured logs

```bash
# Every log call must use the structured logger, not console.log / println / print
grep -rn "console\.\(log\|error\|warn\)\|println\|print(\|fmt\.Print" {{OUTPUT_PATH}}/{{DOMAIN}} 2>/dev/null | grep -v __tests__
# Should be zero

# Structured log emission with required fields
grep -rn "logger\.\(info\|warn\|error\|debug\)" {{OUTPUT_PATH}}/{{DOMAIN}} --include="*.ts" --include="*.go" --include="*.py" 2>/dev/null | head -20
# Sample: each call must include request_id, actor, route (per design)
```

### Trace propagation

```bash
# Every outbound HTTP/gRPC call must forward traceparent
grep -rn "fetch(\|axios\.\|http\.Get\|grpc\.\|client\." {{OUTPUT_PATH}}/{{DOMAIN}}/adapters/ 2>/dev/null
# Each should pass traceparent / propagation context
```

### Metrics

For each endpoint per `domains/_contracts.yaml`:
- counter `{{DOMAIN}}_requests_total{route, status}` exists in code
- histogram `{{DOMAIN}}_request_duration_ms{route}` exists

```bash
grep -rn "Counter\|Histogram\|Gauge\|prometheus\|metrics\." {{OUTPUT_PATH}}/{{DOMAIN}} 2>/dev/null
```

### Dashboards

Each domain must have a dashboard config committed at:
- `dashboards/{{DOMAIN}}.json` (Grafana) or
- `dashboards/{{DOMAIN}}.dashboard.yaml` (Datadog) or equivalent

If missing: HIGH finding.

### Alerts

Per `canary-schedule.yaml`, every SLO must have a corresponding alert rule:
- `alerts/{{DOMAIN}}-error-rate.yaml`
- `alerts/{{DOMAIN}}-p95-latency.yaml`

---

## Finding Levels

- CRITICAL: no structured logger; logs unparseable
- HIGH: missing dashboard, missing trace propagation on outbound calls, missing required metrics
- MEDIUM: logs missing one or more required fields, alerts not configured
- LOW: extra noisy logs, low-cardinality issues

---

## Output

```markdown
# Verify — Observability — {{DOMAIN}}

## Logs
- Structured logger usage: PASS | FAIL
- Required fields (request_id, actor, route, duration, status): {N}/{N} call sites compliant
- Stray print/console.log: {N}

## Traces
- Outbound calls propagating traceparent: {N}/{N}
- Sampling configured: yes | no

## Metrics
| Metric | Defined? | Exposed? |
|--------|----------|----------|
| {{DOMAIN}}_requests_total | yes | yes |
| {{DOMAIN}}_request_duration_ms | yes | yes |

## Dashboards
- dashboards/{{DOMAIN}}.json: present | MISSING

## Alerts
- error_rate: configured | MISSING
- p95_latency: configured | MISSING

## Findings (OBS-NNN)
```

---

## Completion

```
[VERIFY-OBSERVABILITY: {{DOMAIN}}]
File: domains/{{DOMAIN}}/verify-observability.md
```
