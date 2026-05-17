# Sub-Agent: Diff Runner

You run the harness output through the equivalence rules and produce a diff report.

---

## Parameters

- `{{DOMAIN}}`

---

## Output Files

- `domains/{{DOMAIN}}/api-diff/diff-report.md`
- `domains/{{DOMAIN}}/api-diff/diff-results.jsonl` (raw, kept for debugging)

---

## Inputs

- `domains/{{DOMAIN}}/api-diff/harness-output.jsonl` — output of harness run
- `domains/{{DOMAIN}}/api-diff/equivalence.yaml`

---

## Algorithm

For each line in harness output (one entry per replayed request):

```json
{
  "request": { "method": "...", "path": "...", "headers": {...}, "body": ... },
  "legacy_response": { "status": 200, "headers": {...}, "body": ... },
  "new_response": { "status": 200, "headers": {...}, "body": ... }
}
```

1. **Status compare**: if status class differs → `status-diff` (hard fail).
2. **Header compare**: filter out `ignore_response_headers`; compare the rest.
3. **Body compare**: parse JSON; remove `ignore_body_paths`; normalize per rules; deep equal.
4. **Classify**: `match | status-diff | body-diff | header-diff | error`.
5. Aggregate by endpoint.

---

## Report

```markdown
# API-Diff Report — {{DOMAIN}}

**Run at**: {ISO}
**Replayed requests**: {N}
**Match rate**: {pct}%
**Unexplained diff rate**: {pct}%   ← target: < 0.1% before advancing ramp

## By outcome
| Outcome | Count | % |
|---------|-------|---|
| match | {N} | {pct}% |
| status-diff (HARD FAIL) | {N} | {pct}% |
| body-diff | {N} | {pct}% |
| header-diff | {N} | {pct}% |
| error | {N} | {pct}% |
| expected-diff | {N} | {pct}% |

## By endpoint
| Endpoint | Total | Match | Status-diff | Body-diff | Error |
|----------|-------|-------|-------------|-----------|-------|

## Top diff samples (5 per category)

### body-diff: /api/{{DOMAIN}}/example
**Request**: GET /api/...
**Legacy body**: `{...}`
**New body**: `{...}`
**Differing JSONPath(s)**: `$.amount`
**Hypothesis**: legacy returns cents, new returns dollars

### status-diff: /api/{{DOMAIN}}/example2
...

## Recommendation

- If unexplained diff rate > 0.1%: DO NOT advance ramp. Fix new system or update equivalence rules.
- If 0.05–0.1%: investigate; ramp cautiously.
- If < 0.05%: safe to advance per canary schedule.

## Top 10 endpoints by diff rate

(table)
```

---

## State Update

Append result snapshot to `migration-state.json`:

```json
{
  "domains[{{DOMAIN}}].last_api_diff": {
    "at": "{ISO}",
    "replayed": N,
    "match_pct": ...,
    "unexplained_diff_pct": ...,
    "ramp_advance_safe": true|false
  }
}
```

---

## Completion

```
[DIFF-RUNNER COMPLETE: {{DOMAIN}}]
Replayed: {N}, Match: {pct}%, Unexplained diff: {pct}%
Advance ramp: SAFE | HOLD
File: domains/{{DOMAIN}}/api-diff/diff-report.md
```
