# Sub-Agent: Canary Rollout

You produce the canary schedule for `{{DOMAIN}}`: per-week ramp percentages, SLO gates, automatic rollback triggers, and the filled-in rollback runbook.

---

## Parameters

- `{{DOMAIN}}`

---

## Output Files

- `domains/{{DOMAIN}}/canary-schedule.yaml`
- `domains/{{DOMAIN}}/rollback-runbook.md` (use `_shared/rollback-runbook-template.md`)
- Append schedule to `migration-state.json`

---

## Schedule template

```yaml
# domains/{{DOMAIN}}/canary-schedule.yaml
domain: {{DOMAIN}}
strategy: progressive-with-soak
sticky_by: user_id

ramps:
  - week: 1
    target_percent: 1
    duration_days: 3       # soak at 1% for 3 days
    advance_if:
      error_rate_5xx_max: 0.5    # %
      p95_latency_max_ms: {p95}  # from contract SLA + 10%
      p99_latency_max_ms: {p99}
      api_diff_unexplained_max: 0.1  # %
      traffic_delta_max: 5   # % (new traffic vs legacy baseline)
    on_breach: rollback
  - week: 1
    target_percent: 10
    duration_days: 4
    advance_if:
      error_rate_5xx_max: 0.5
      p95_latency_max_ms: {p95}
      api_diff_unexplained_max: 0.1
    on_breach: rollback
  - week: 2
    target_percent: 25
    duration_days: 5
    advance_if: {...}
    on_breach: rollback
  - week: 3
    target_percent: 50
    duration_days: 7
    advance_if: {...}
    on_breach: rollback
  - week: 4
    target_percent: 100
    duration_days: 7
    advance_if: {...}
    on_breach: rollback

# Auto-rollback configuration
auto_rollback:
  enabled: true
  evaluator: "datadog | prometheus | newrelic"
  evaluation_interval_seconds: 30
  consecutive_breaches_to_trigger: 3
  notify:
    pagerduty_service: "{{DOMAIN}}-oncall"
    slack: "#{{DOMAIN}}-incidents"

# SLO baselines (from production legacy measurement; must be recorded BEFORE ramp 1%)
baseline:
  captured_at: "{ISO}"
  error_rate_5xx: 0.12   # %
  p50_latency_ms: 45
  p95_latency_ms: 180
  p99_latency_ms: 320
  rps: 2400
```

---

## Required SLO Gates

Every ramp step must define:
- `error_rate_5xx_max`: max acceptable 5xx rate %.
- `p95_latency_max_ms`: max p95.
- `p99_latency_max_ms`: max p99.
- `api_diff_unexplained_max`: from Phase 08.
- `traffic_delta_max`: catch routing misconfig.

Thresholds default to: baseline × 1.1 (10% regression budget). Tighter for revenue-critical domains.

---

## Auto-rollback rule

Trigger conditions (any):
1. Any SLO breached for `consecutive_breaches_to_trigger * evaluation_interval_seconds` (default 90s).
2. Manual override (kill-switch flag).
3. API diff exceeded threshold for >30 min.

Action: set `{{DOMAIN}}.kill-switch=true` (Phase 06 flag). Optionally also revert routing config to 0%.

---

## Rollback runbook

Generate `domains/{{DOMAIN}}/rollback-runbook.md` from `_shared/rollback-runbook-template.md` with `{{DOMAIN}}`-specific values:
- Owner team from `_codeowners.md`
- On-call rotation URL
- Specific commands for `parameters.ROUTING_LAYER` and `parameters.FEATURE_FLAG_SYS`
- Data rollback procedure from `domains/{{DOMAIN}}/data-migration.md`

---

## State Update

```json
{
  "domains[{{DOMAIN}}].canary_schedule": "domains/{{DOMAIN}}/canary-schedule.yaml",
  "domains[{{DOMAIN}}].ramp_percent": 0,
  "domains[{{DOMAIN}}].ramp_history": []
}
```

---

## Completion

```
[CANARY-ROLLOUT COMPLETE: {{DOMAIN}}]
Ramps planned: 5 (1% → 10% → 25% → 50% → 100%)
Total duration: 26 days (with soaks)
Files: domains/{{DOMAIN}}/canary-schedule.yaml + rollback-runbook.md

HUMAN GATE: SRE captures baseline metrics and approves before first ramp.
```
