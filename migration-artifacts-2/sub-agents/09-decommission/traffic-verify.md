# Sub-Agent: Decommission — Traffic Verify

Gate 1 of decommission. Verifies zero traffic is hitting legacy for this domain.

Decommission is irreversible. Every gate must pass.

---

## Parameters

- `{{DOMAIN}}`

---

## Output Files

- `decommission/{{DOMAIN}}/traffic-verified.md`

---

## Preconditions

- `domains[{{DOMAIN}}].ramp_percent == 100`
- At least 7 days have passed since reaching 100% (stable soak)
- No rollback events in `rollback_history` for this domain in the last 7 days

If any precondition fails: STOP and emit failure reason.

---

## Procedure

1. Query gateway / load balancer logs for legacy backend hits over the last 7 days:

```bash
# Examples (adapt to your stack)
# nginx access logs
awk -v d="$(date -d '7 days ago' +%Y-%m-%d)" '$4 >= "["d {print $0}' /var/log/nginx/access.log | grep "upstream=legacy-{{DOMAIN}}" | wc -l

# Cloud (gcp example)
gcloud logging read 'resource.type="http_load_balancer" AND httpRequest.requestUrl~"/api/{{DOMAIN}}/" AND jsonPayload.backend="legacy"' --freshness=7d --limit 100 | wc -l

# Prometheus: rate counter for legacy backend
curl -s 'http://prom/api/v1/query?query=sum(rate({{DOMAIN}}_legacy_backend_requests_total[7d]))'
```

2. Must return **zero** (or very low single-digit count attributable to health checks / synthetic probes — document any).

3. Confirm via two independent sources (logs + metrics).

---

## Output

```markdown
# Decommission Gate 1 — Traffic Verify — {{DOMAIN}}

**Window**: last 7 days
**Source 1 (gateway logs)**: {N} requests to legacy
**Source 2 (Prometheus rate)**: {value} req/s avg
**Synthetic probes excluded**: yes (paths: {list})

## Verdict
- PASS: zero non-synthetic legacy hits
- HOLD: non-zero hits found — investigate which clients are still on legacy

## Detail of any non-zero hits
{caller IPs, user-agents, paths}

## Action if HOLD
- Identify caller; route them via flag-gate.
- DO NOT proceed to gate 2 until this is resolved.
```

---

## State Update

If PASS, append to state:

```json
{
  "domains[{{DOMAIN}}].decommission_gate_1_traffic": {
    "verified_at": "{ISO}",
    "window_days": 7,
    "result": "pass"
  }
}
```

---

## Completion

```
[DECOMMISSION-TRAFFIC-VERIFY: {{DOMAIN}}]
Result: PASS | HOLD
File: decommission/{{DOMAIN}}/traffic-verified.md
```
