# Sub-Agent: Routing Config

You generate working routing-layer configuration for `{{DOMAIN}}` based on `parameters.ROUTING_LAYER` and the contracts owned by this domain.

The generated config splits traffic per-endpoint between legacy and new at `{{RAMP_PERCENT}}%`.

---

## Parameters

- `{{DOMAIN}}`
- `{{RAMP_PERCENT}}` — current target ramp (read from state if not provided; default 0)
- `parameters.ROUTING_LAYER` — `nginx | alb | cloudflare-worker | envoy`

---

## Output Files

- `domains/{{DOMAIN}}/strangler/routing.{conf|tf|js|yaml}` — actual config
- `domains/{{DOMAIN}}/strangler/routing.md` — narrative

---

## Context Budget

Read only `domains/_contracts.yaml` filtered by owner_domain. Use the appropriate template from `templates/`.

---

## Per-Routing-Layer Output

### nginx (`ROUTING_LAYER=nginx`)

Start from `templates/strangler-config-nginx.conf`. Substitute:
- `{{DOMAIN}}` → domain name
- `{{LEGACY_UPSTREAM}}` → host:port of legacy
- `{{NEW_UPSTREAM}}` → host:port of new
- `{{RAMP_PERCENT}}` → integer

Output one `location` block per contract endpoint, with `split_clients` directive for weighted routing.

### AWS ALB (`ROUTING_LAYER=alb`)

Start from `templates/strangler-config-alb.tf`. Substitute and output Terraform with:
- Two target groups: `{{DOMAIN}}-legacy-tg`, `{{DOMAIN}}-new-tg`
- Listener rule with `forward` action using `weighted_target_groups`

### Cloudflare Worker (`ROUTING_LAYER=cloudflare-worker`)

Start from `templates/strangler-config-cloudflare-worker.js`. The worker:
- Reads `Cf-Migration-Cohort` header if present (sticky bucket override)
- Otherwise hashes the user_id (from JWT) modulo 100
- Routes to new if hash < `{{RAMP_PERCENT}}`

### Envoy (`ROUTING_LAYER=envoy`)

```yaml
# domains/{{DOMAIN}}/strangler/routing.yaml
route_config:
  name: {{DOMAIN}}_routes
  virtual_hosts:
  - name: {{DOMAIN}}_vh
    domains: ["*"]
    routes:
    - match: { prefix: "/api/{{DOMAIN}}/" }
      route:
        weighted_clusters:
          clusters:
          - name: {{DOMAIN}}_legacy
            weight: {{100 - RAMP_PERCENT}}
          - name: {{DOMAIN}}_new
            weight: {{RAMP_PERCENT}}
          total_weight: 100
```

---

## Per-Endpoint Override

If specific endpoints ramp at different rates (recommended), generate per-endpoint blocks. Example for nginx:

```nginx
# /api/{{DOMAIN}}/safe-read-endpoint — ramped to 50%
split_clients "${remote_addr}${request_id}" $route_safe_read {
    50%    new;
    *      legacy;
}

# /api/{{DOMAIN}}/critical-write — still at 5%
split_clients "${remote_addr}${request_id}" $route_critical_write {
    5%     new;
    *      legacy;
}
```

Sticky cohorts: use `$cookie_user_id` or `$http_x_user_id` for hashing instead of random IP-based split — this guarantees a single user does not flip between legacy and new mid-session.

---

## Narrative: `domains/{{DOMAIN}}/strangler/routing.md`

```markdown
# Routing — {{DOMAIN}}

**Routing layer**: {{ROUTING_LAYER}}
**Current ramp**: {{RAMP_PERCENT}}%
**Stickiness**: per-user_id (no mid-session flips)

## Per-endpoint ramp
| Endpoint | Current % | Reason |
|----------|-----------|--------|

## Apply
```bash
# nginx
nginx -t -c {{path}} && sudo systemctl reload nginx

# alb (terraform)
terraform plan -var ramp_percent={{RAMP_PERCENT}}
terraform apply

# cloudflare
wrangler deploy --var RAMP_PERCENT:{{RAMP_PERCENT}}

# envoy
kubectl apply -f domains/{{DOMAIN}}/strangler/routing.yaml
```

## Revert (instant)
{see rollback-runbook}
```

---

## State Update

`domains[{{DOMAIN}}].ramp_percent = {{RAMP_PERCENT}}`.
Append to `ramp_history`.

---

## Completion

```
[ROUTING-CONFIG COMPLETE: {{DOMAIN}}]
Routing layer: {{ROUTING_LAYER}}
Ramp: {{RAMP_PERCENT}}%
Files: domains/{{DOMAIN}}/strangler/routing.*

HUMAN GATE: SRE approves before apply.
```
