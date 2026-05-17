# Sub-Agent: Fallback Logic

You generate the fallback middleware that catches errors from the new system and falls back to legacy. Includes circuit-breaker so a flapping new system doesn't melt down legacy.

---

## Parameters

- `{{DOMAIN}}`
- Target language (from `parameters.TECH_STACK.language`)

---

## Output Files

- `domains/{{DOMAIN}}/strangler/fallback.{ts|go|py|java}` — middleware
- `domains/{{DOMAIN}}/strangler/fallback.test.{ts|go|py|java}` — tests
- `domains/{{DOMAIN}}/strangler/fallback.md` — narrative

---

## Context Budget

See `sub-agents/_shared/context-budget-rules.md`. Read only the inputs explicitly listed in Parameters; do not load full discovery dumps.

---

## Behavior

Per request to a routed endpoint:
1. Try **new** system.
2. If new returns 5xx OR times out OR circuit is open: invoke **legacy**.
3. Record outcome in metrics: `fallback_attempts_total{domain, endpoint, outcome=new_ok|new_fail_legacy_ok|both_fail}`.
4. Update circuit-breaker state.

Circuit breaker (per endpoint):
- Threshold: 5 failures in 10 seconds opens the breaker.
- Open state: skip new, go straight to legacy. For 60 seconds.
- Half-open: send 1 request to new every 5 seconds; on success, close breaker.

---

## TypeScript template (Express)

```typescript
// domains/{{DOMAIN}}/strangler/fallback.ts
import { Request, Response, NextFunction } from 'express';
import CircuitBreaker from 'opossum';
import fetch from 'node-fetch';

const NEW_BASE = process.env['{{DOMAIN}}'.toUpperCase() + '_NEW_BASE']!;
const LEGACY_BASE = process.env['{{DOMAIN}}'.toUpperCase() + '_LEGACY_BASE']!;

const breakerOpts = {
  timeout: 3000,
  errorThresholdPercentage: 50,
  resetTimeout: 60_000,
  rollingCountTimeout: 10_000,
  rollingCountBuckets: 10,
};

const breakers = new Map<string, CircuitBreaker<any[], any>>();

function getBreaker(endpoint: string) {
  if (!breakers.has(endpoint)) {
    const b = new CircuitBreaker(
      async (req: Request) => callNew(endpoint, req),
      breakerOpts
    );
    b.fallback(async (req: Request) => callLegacy(endpoint, req));
    breakers.set(endpoint, b);
  }
  return breakers.get(endpoint)!;
}

async function callNew(endpoint: string, req: Request) {
  const res = await fetch(`${NEW_BASE}${endpoint}`, forwardOpts(req));
  if (res.status >= 500) throw new Error(`new ${res.status}`);
  return res;
}

async function callLegacy(endpoint: string, req: Request) {
  return fetch(`${LEGACY_BASE}${endpoint}`, forwardOpts(req));
}

function forwardOpts(req: Request) {
  return {
    method: req.method,
    headers: { ...req.headers, 'x-forwarded-by': '{{DOMAIN}}-fallback' } as any,
    body: ['GET', 'HEAD'].includes(req.method) ? undefined : JSON.stringify(req.body),
  };
}

export function fallbackMiddleware(endpoint: string) {
  return async (req: Request, res: Response, _next: NextFunction) => {
    const breaker = getBreaker(endpoint);
    try {
      const upstream = await breaker.fire(req);
      const body = await upstream.text();
      res.status(upstream.status).send(body);
    } catch (e) {
      res.status(502).json({ error: 'both_systems_failed' });
    }
  };
}
```

---

## Go template (chi router) — abbreviated

```go
// domains/{{DOMAIN}}/strangler/fallback.go
package strangler

import (
  "context"
  "github.com/sony/gobreaker"
  "net/http"
)

// breaker per endpoint; settings per design
// On failure, fall back to legacy handler.
// Emit metrics: fallback_attempts_total{outcome}
```

---

## Tests

Required tests:
1. New returns 200 → middleware returns 200 from new.
2. New returns 500 → middleware returns response from legacy.
3. New times out → middleware returns response from legacy.
4. After 5 new failures → breaker opens; next request goes straight to legacy without trying new.
5. Both fail → 502.

---

## Narrative

```markdown
# Fallback — {{DOMAIN}}

Middleware order: routing → flag-gate → fallback → handler.

## Metrics emitted
- `{{DOMAIN}}_fallback_attempts_total{endpoint, outcome}`
- `{{DOMAIN}}_breaker_state{endpoint, state}` (gauge: 0=closed, 1=half-open, 2=open)

## Alert thresholds
- `outcome=new_fail_legacy_ok` rate > 1% over 5min → page on-call.
- `outcome=both_fail` any → page on-call.
- Breaker open for >5 min → page.

## Tuning
{thresholds tuned during canary; document final values}
```

---

## Completion

```
[FALLBACK-LOGIC COMPLETE: {{DOMAIN}}]
Middleware + tests written
Files: domains/{{DOMAIN}}/strangler/fallback.* + tests
```
