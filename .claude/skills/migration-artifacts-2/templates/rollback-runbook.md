# Rollback Runbook — {{DOMAIN}}

Filled-in instance of `sub-agents/_shared/rollback-runbook-template.md`. Generated per-domain by `06-strangler-fig/canary-rollout.md`.

This is the template — replace `{{...}}` with concrete values.

---

**Owner**: {{TEAM}}
**On-call**: {{PAGERDUTY_URL}}
**Last drilled**: {{DATE}}

## Triggers (Automatic)

| Metric | Threshold | Window | Action |
|--------|-----------|--------|--------|
| 5xx rate | > 0.5% | 5 min | flag kill-switch on |
| p95 latency | > {{P95_TARGET}} ms | 5 min | flag kill-switch on |
| Diff rate (unexplained) | > 0.1% | 30 min | hold + alert |

## Procedures

### Level 1 — Kill-switch (instant)
```bash
ld-cli flag update {{DOMAIN}}.kill-switch --on --comment "rollback $(date -Iseconds)"
```
Effect: all traffic → legacy within ~{{FLAG_PROPAGATION}} seconds.

### Level 2 — Routing config revert
```bash
# {{ROUTING_LAYER}} specific
{{REVERT_COMMAND}}
```

### Level 3 — Code revert
```bash
git revert -m 1 {{LAST_MERGE_SHA}}
git push origin main
```

### Level 4 — Data rollback
See `domains/{{DOMAIN}}/data-migration.md` § Rollback.

## Communication
1. Post `#incidents`: "Rolling back {{DOMAIN}}: {reason}"
2. Page tech lead if level ≥ 3.
3. Open post-mortem within 24h.

## Post-rollback
- [ ] Confirm 100% legacy via dashboard
- [ ] Error rate below threshold
- [ ] Update `migration-state.json.rollback_history`
- [ ] Schedule post-mortem ≤ 5 business days
- [ ] Update `domains[].status = "rolled_back"`
