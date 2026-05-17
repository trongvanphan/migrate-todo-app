# Sub-Agent: Semantic Equivalence Rules

You produce the YAML config that defines which response differences should be ignored as semantically equivalent (timestamps, generated IDs, ordering).

Without this config, every diff is flagged as a difference and the signal is unusable.

---

## Parameters

- `{{DOMAIN}}`

---

## Output Files

- `domains/{{DOMAIN}}/api-diff/equivalence.yaml`

---

## Schema

```yaml
# domains/{{DOMAIN}}/api-diff/equivalence.yaml
version: 1
domain: {{DOMAIN}}

# Apply to ALL endpoints in this domain
defaults:
  ignore_response_headers:
    - "Date"
    - "Server"
    - "X-Request-Id"
    - "X-Trace-Id"
    - "Set-Cookie"
  ignore_body_paths:
    - "$.metadata.timestamp"
    - "$.metadata.request_id"
    - "$.*.created_at"
    - "$.*.updated_at"
    - "$.*[*].id"   # if IDs are server-generated and not stable across systems
  normalize:
    timestamp_tolerance_ms: 1000
    number_precision: 4         # round to 4 decimals before compare
    array_order_independent: false   # set true if order doesn't matter
    case_insensitive_keys: false
    trim_strings: true

# Per-endpoint overrides
endpoints:
  - path: "/api/{{DOMAIN}}/list"
    method: GET
    overrides:
      array_order_independent: true   # list order may differ; treat as set
      ignore_body_paths:
        - "$.items[*].score"          # ranking differences acceptable

  - path: "/api/{{DOMAIN}}/create"
    method: POST
    overrides:
      ignore_body_paths:
        - "$.id"            # generated ID never matches
        - "$.created_at"

# Expected differences (acknowledged, not bugs)
expected_diffs:
  - path: "/api/{{DOMAIN}}/legacy-quirk"
    description: "Legacy returns 200 with empty body when not found; new returns 404. Approved."
    legacy_status: 200
    new_status: 404

# Hard mismatch (these are always real bugs, never tolerated)
hard_fail:
  status_class_change: true       # 2xx → 4xx or 4xx → 5xx etc. is always a diff
  missing_required_fields: ["id", "amount", "user_id"]
```

---

## Building the rules

1. Start with defaults (above).
2. Run harness once with no overrides — most diffs will be timestamps and generated IDs.
3. For each diff category, add a rule.
4. Iterate until "real" diff rate < 5% of total diffs (still loud, but signal-to-noise improving).
5. After 3 iterations, true behavioral diffs should be <0.1%.

---

## Acknowledged-diff workflow

If a diff is intentional (legacy bug being fixed in new), add to `expected_diffs`. Each entry requires:
- A description
- A reference to the spec FR or design decision authorizing it
- An owner

---

## Output Companion: `expected-diffs-log.md`

```markdown
# Expected Diffs — {{DOMAIN}}

| Path | Diff | Authorized by | Date |
|------|------|---------------|------|
| /legacy-quirk | 200→404 | FR-3.2 (fix legacy bug #482) | 2026-02-01 |
```

---

## Completion

```
[SEMANTIC-EQUIVALENCE COMPLETE: {{DOMAIN}}]
Rules: defaults + {N} per-endpoint + {N} expected diffs
File: domains/{{DOMAIN}}/api-diff/equivalence.yaml
```
