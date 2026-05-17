# Sub-Agent: API-Diff Harness Setup

You scaffold the parallel-run diff harness for `{{DOMAIN}}`. The harness records or replays traffic against both legacy and new, then compares responses.

---

## Parameters

- `{{DOMAIN}}`

---

## Output Files

- `domains/{{DOMAIN}}/api-diff/harness.ts` — copy & customize `templates/api-diff-harness.ts`
- `domains/{{DOMAIN}}/api-diff/traffic-recorder.{ts|py}` — recorder
- `domains/{{DOMAIN}}/api-diff/README.md` — operator instructions

---

## Context Budget

See `sub-agents/_shared/context-budget-rules.md`. Read only the inputs explicitly listed in Parameters; do not load full discovery dumps.

---

## Architecture

```
   Production traffic (mirrored or replayed)
              │
              ▼
   ┌──────────────────────┐
   │  Harness             │
   │  - load traffic.jsonl│
   │  - for each request: │
   │      send to LEGACY  │
   │      send to NEW     │
   │      capture both    │
   │  - call diff-runner  │
   └──────────┬───────────┘
              ▼
       diff-report.json
```

---

## Recorder

The recorder captures real production traffic for replay. Two modes:

### Mode A — tap from existing routing layer

```nginx
# Add to nginx config (read-only mirror)
mirror /__mirror;
location = /__mirror {
  internal;
  proxy_pass http://recorder/{{DOMAIN}}/$request_uri;
}
```

Then run a small recorder service that appends to `traffic.jsonl`.

### Mode B — sniff from a sampled log stream

If your gateway already logs full requests (with body) and responses, build `traffic.jsonl` from that log:

```python
# domains/{{DOMAIN}}/api-diff/traffic-recorder.py
import json, sys, gzip
for line in sys.stdin:
    entry = json.loads(line)
    if entry["path"].startswith("/api/{{DOMAIN}}/"):
        print(json.dumps({
            "method": entry["method"],
            "path": entry["path"],
            "headers": redact_headers(entry["headers"]),
            "body": entry.get("body"),
            "captured_at": entry["timestamp"],
        }))
```

Redact: Authorization, Cookie, X-API-Key, any field tagged PII per `data-migration.md`.

---

## Harness setup

Copy `templates/api-diff-harness.ts` to `domains/{{DOMAIN}}/api-diff/harness.ts`. Customize:
- `LEGACY_BASE`, `NEW_BASE` env vars
- Traffic input path
- Output diff path
- Reference `domains/{{DOMAIN}}/api-diff/equivalence.yaml` (produced by `semantic-equivalence.md`)

---

## Operator README

```markdown
# API-Diff Harness — {{DOMAIN}}

## Record traffic (Mode B example)
```
gcloud logging read 'resource.type="http_load_balancer" AND httpRequest.requestUrl~"/api/{{DOMAIN}}/"' --limit 100000 --format json \
  | python traffic-recorder.py > traffic.jsonl
```

## Replay
```
LEGACY_BASE=https://legacy NEW_BASE=https://new \
  npx ts-node harness.ts traffic.jsonl > diff-results.jsonl
```

## Analyze
```
npx ts-node ../api-diff/diff-runner.ts diff-results.jsonl > diff-report.md
```
```

---

## Completion

```
[API-DIFF HARNESS-SETUP COMPLETE: {{DOMAIN}}]
Files: domains/{{DOMAIN}}/api-diff/{harness.ts,traffic-recorder.*,README.md}
```
