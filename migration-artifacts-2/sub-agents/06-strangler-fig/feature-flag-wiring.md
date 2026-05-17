# Sub-Agent: Feature Flag Wiring

You produce feature-flag definitions and client/server gate code for `{{DOMAIN}}` per `parameters.FEATURE_FLAG_SYS`.

Feature flags are the **fast-rollback** mechanism. They must work even if the routing layer fails.

---

## Parameters

- `{{DOMAIN}}`
- `parameters.FEATURE_FLAG_SYS` — `LaunchDarkly | Unleash | Statsig | custom`

---

## Output Files

- `domains/{{DOMAIN}}/strangler/flags.{yaml|json}` — flag definitions
- `domains/{{DOMAIN}}/strangler/flag-gate-server.{ts|py|go|java}` — server-side gate
- `domains/{{DOMAIN}}/strangler/flag-gate-client.{ts}` — client-side gate
- `domains/{{DOMAIN}}/strangler/flags.md` — narrative

---

## Context Budget

See `sub-agents/_shared/context-budget-rules.md`. Read only the inputs explicitly listed in Parameters; do not load full discovery dumps.

---

## Flag Schema

One **routing flag** per contract endpoint:
- Key: `{{DOMAIN}}.{endpoint-slug}.routing`
- Type: boolean (variants: `legacy`, `new`)
- Default: `legacy`
- Targeting: percentage rollout by `user_id` (sticky)

One **kill switch** per domain:
- Key: `{{DOMAIN}}.kill-switch`
- Type: boolean
- Default: `false` (off)
- When `true`: all routing flags forced to `legacy`. Bypass any percentage rollout.

---

## LaunchDarkly output

```yaml
# domains/{{DOMAIN}}/strangler/flags.yaml
flags:
  - key: "{{DOMAIN}}.routing"
    name: "{{DOMAIN}} routing"
    variations:
      - { value: "legacy", name: "Legacy" }
      - { value: "new", name: "New" }
    defaults:
      onVariation: 0   # legacy
      offVariation: 0
    rules:
      - clauses:
          - attribute: "in_cohort"
            op: "in"
            values: ["{{DOMAIN}}-canary"]
        variation: 1   # new
      - rollout:
          variations:
            - { variation: 0, weight: {{100000 - RAMP_PERCENT*1000}} }
            - { variation: 1, weight: {{RAMP_PERCENT*1000}} }
          bucketBy: "user_id"

  - key: "{{DOMAIN}}.kill-switch"
    name: "{{DOMAIN}} kill switch (force legacy)"
    defaults:
      onVariation: 0
      offVariation: 0
    variations:
      - { value: false, name: "off" }
      - { value: true, name: "on (force legacy)" }
```

## Unleash / Statsig: equivalent JSON

(emit the appropriate schema for the chosen system)

---

## Server-side gate (TypeScript example)

```typescript
// domains/{{DOMAIN}}/strangler/flag-gate-server.ts
import { LDClient } from '@launchdarkly/node-server-sdk';

export async function shouldRouteToNew(
  ld: LDClient,
  context: { user_id: string; cohort?: string }
): Promise<boolean> {
  const kill = await ld.boolVariation('{{DOMAIN}}.kill-switch', context, false);
  if (kill) return false;
  const variation = await ld.stringVariation('{{DOMAIN}}.routing', context, 'legacy');
  return variation === 'new';
}
```

Adapt to Go/Java/Python equivalents based on stack.

---

## Client-side gate (browser TypeScript example)

```typescript
// domains/{{DOMAIN}}/strangler/flag-gate-client.ts
import { initialize } from 'launchdarkly-js-client-sdk';

const ld = initialize(process.env.LD_CLIENT_KEY!, {
  kind: 'user',
  key: window.userId,
});

await ld.waitUntilReady();

export const route = ld.variation('{{DOMAIN}}.routing', 'legacy');
```

---

## Narrative

```markdown
# Feature Flags — {{DOMAIN}}

**Flag system**: {{FEATURE_FLAG_SYS}}
**Flags**: 2 (routing + kill-switch)
**Stickiness**: bucket by `user_id`

## Operational

- Kill-switch flip = instant rollback (no deploy).
- Routing flag % change propagates within {Y} seconds.
- All flag changes are logged to `audit_log` with actor + before/after.

## Emergency

```bash
# Force everything back to legacy in 1 command
ld-cli flag update {{DOMAIN}}.kill-switch --on
```
```

---

## State Update

Record flag keys in `migration-state.json`:

```json
{
  "domains[{{DOMAIN}}].flags": {
    "routing": "{{DOMAIN}}.routing",
    "kill_switch": "{{DOMAIN}}.kill-switch"
  }
}
```

---

## Completion

```
[FEATURE-FLAG-WIRING COMPLETE: {{DOMAIN}}]
System: {{FEATURE_FLAG_SYS}}
Flags: routing + kill-switch
Files: domains/{{DOMAIN}}/strangler/flags.* + gate code
```
