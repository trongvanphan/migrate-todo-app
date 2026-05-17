# Sub-Agent: API Routes Scan (per module)

You scan API surface for **one module** and produce a routes inventory.

---

## Parameters

- `{{LEGACY_PATH}}`
- `{{MODULE}}`

---

## Output Files

- `discovery/modules/{{MODULE}}/api-routes.md` (≤2000 lines)
- Append to `state/handoff/discovery/_module-{{MODULE_SLUG}}.json` (merge into existing if present)

---

## Context Budget

See `_shared/context-budget-rules.md`. Bounded grep; never unbounded.

---

## Scans

```bash
# REST — most frameworks
grep -rn "router\.\(get\|post\|put\|patch\|delete\)\|app\.\(get\|post\|put\|patch\|delete\)\|@\(Get\|Post\|Put\|Patch\|Delete\|Request\)Mapping\|@app\.\(get\|post\|put\|patch\|delete\)\|path=" "{{LEGACY_PATH}}/{{MODULE}}" --include="*.ts" --include="*.js" --include="*.py" --include="*.rb" --include="*.java" --include="*.go" --include="*.kt" 2>/dev/null | grep -v "node_modules" | grep -v "\.spec\." | grep -v "\.test\." | head -300

# GraphQL
find "{{LEGACY_PATH}}/{{MODULE}}" -name "*.graphql" -o -name "*.gql" 2>/dev/null | head -20

# gRPC
find "{{LEGACY_PATH}}/{{MODULE}}" -name "*.proto" 2>/dev/null | head -20

# WebSocket / SSE
grep -rn "socket\.\(on\|emit\)\|ws\.\(on\|send\)\|EventSource\|sse" "{{LEGACY_PATH}}/{{MODULE}}" --include="*.ts" --include="*.js" --include="*.py" 2>/dev/null | head -50

# Background jobs (cron, queues)
grep -rn "@Scheduled\|cron(\|@app\.task\|Sidekiq\|BullQueue\|sqs\|kafka.*consum" "{{LEGACY_PATH}}/{{MODULE}}" --include="*.ts" --include="*.py" --include="*.java" --include="*.rb" 2>/dev/null | head -50
```

---

## Output Structure

```markdown
# API Routes — {{MODULE}}

**Scanned at**: {ISO}

## REST Endpoints ({N} total)
| Method | Path | Handler | Auth? | Description |
|--------|------|---------|-------|-------------|

(If >200 routes, write top 50 by file path + counts table + reference to raw grep output stored in `discovery/modules/{{MODULE}}/api-routes.raw.txt`.)

## GraphQL ({N} files)
| File | Type count | Notable queries/mutations |

## gRPC ({N} .proto files)
| File | Services | Methods |

## WebSocket / SSE
| Channel/event | Direction | Payload shape |

## Background jobs
| Trigger | Handler | Cadence |

## External API calls (outbound)
| URL pattern | Caller file | Purpose (inferred) |

## Auth observations
- Routes without auth check: {count, examples}
- Auth mechanisms detected: {list}
```

Aggregate first. Never paste >200 raw grep lines.

---

## Completion

```
[API-ROUTES-SCAN COMPLETE: {{MODULE}}]
REST: {N}, GraphQL: {N}, gRPC: {N}, WS: {N}, Jobs: {N}
File: discovery/modules/{{MODULE}}/api-routes.md
```
