# Sub-Agent: Verify — Performance

You load-test the new implementation against the legacy baseline. Fail if regression exceeds 10%.

---

## Parameters

- `{{DOMAIN}}`

---

## Output Files

- `domains/{{DOMAIN}}/verify-performance.md`
- `domains/{{DOMAIN}}/perf/k6-script.js` (or `locustfile.py` if Python stack)
- `domains/{{DOMAIN}}/perf/results.json`

---

## Procedure

### 1. Capture or read baseline

If `domains/{{DOMAIN}}/canary-schedule.yaml.baseline` exists, use it.
Otherwise, run the load test against legacy and record.

### 2. Generate k6 script

```javascript
// domains/{{DOMAIN}}/perf/k6-script.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  scenarios: {
    ramp: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '1m', target: 50 },
        { duration: '3m', target: 200 },
        { duration: '1m', target: 0 },
      ],
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.005'],
    http_req_duration: ['p(95)<{p95_target}', 'p(99)<{p99_target}'],
  },
};

const BASE = __ENV.TARGET_BASE;
const endpoints = [
  // populated from domains/_contracts.yaml owner_domain={{DOMAIN}}
  { method: 'GET',  path: '/api/{{DOMAIN}}/...' },
  { method: 'POST', path: '/api/{{DOMAIN}}/...', body: {} },
];

export default function () {
  for (const ep of endpoints) {
    const res = http.request(ep.method, `${BASE}${ep.path}`,
      ep.body ? JSON.stringify(ep.body) : null,
      { headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${__ENV.TOKEN}` } });
    check(res, { 'status 2xx': r => r.status < 300 });
  }
  sleep(1);
}
```

### 3. Run against legacy and new

```bash
# Baseline
TARGET_BASE=https://legacy.example.com k6 run --out json=baseline.json domains/{{DOMAIN}}/perf/k6-script.js

# New
TARGET_BASE=https://new.example.com k6 run --out json=new.json domains/{{DOMAIN}}/perf/k6-script.js
```

### 4. Compare

For p50, p95, p99 and error rate, compute delta. Fail if any metric is >10% worse.

---

## Output

```markdown
# Verify — Performance — {{DOMAIN}}

| Metric | Legacy baseline | New | Delta | Threshold | Status |
|--------|-----------------|-----|-------|-----------|--------|
| p50_ms | 45 | 42 | -7% | ≤+10% | PASS |
| p95_ms | 180 | 210 | +17% | ≤+10% | **FAIL** |
| p99_ms | 320 | 380 | +19% | ≤+10% | **FAIL** |
| error_rate_5xx | 0.12% | 0.05% | -58% | ≤+10% | PASS |
| max_rps | 2400 | 2200 | -8% | ≥-10% | PASS |

## Hot endpoints

Endpoints with largest regression:
| Endpoint | p95 legacy | p95 new | Delta |

## Profile findings
{flame graph references, N+1 query hits, missing indexes flagged in design but not implemented}

## Findings (PERF-NNN)
```

---

## Finding Levels

- CRITICAL: any p95 latency >2x baseline, or new error rate > legacy + 1%
- HIGH: p95 regression 10-100% on any endpoint
- MEDIUM: p99 regression 10-50% on any endpoint, throughput regression 10-25%
- LOW: minor latency change, but within budget for non-critical path

---

## Completion

```
[VERIFY-PERFORMANCE: {{DOMAIN}}]
p95 delta: {X}%, p99 delta: {Y}%
Status: PASS | FAIL
File: domains/{{DOMAIN}}/verify-performance.md
```
