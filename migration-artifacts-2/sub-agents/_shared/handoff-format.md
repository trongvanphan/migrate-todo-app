# Handoff Format

Sub-agents pass context between phases via files, never via prompt content. This file defines the format.

---

## Location

```
state/handoff/{{PHASE}}/{{DOMAIN}}.json
```

Examples:
- `state/handoff/discovery/_global.json` (cross-domain discovery summary)
- `state/handoff/decompose/_global.json`
- `state/handoff/spec/auth.json`
- `state/handoff/design/orders.json`
- `state/handoff/strangler-fig/payments.json`

---

## Schema

```json
{
  "phase": "spec",
  "domain": "auth",
  "produced_at": "ISO timestamp",
  "produced_by": "sub-agents/02-spec/domain-spec.md",
  "summary": "≤500 char human-readable",
  "key_decisions": [
    { "id": "DEC-1", "decision": "Use OIDC, not custom JWT", "rationale": "..." }
  ],
  "artifacts": [
    { "path": "domains/auth/spec.md", "kind": "spec", "loc": 420 }
  ],
  "open_questions": [
    { "id": "Q-1", "question": "...", "blocker": false }
  ],
  "downstream_inputs": {
    "design": {
      "must_address": ["FR-3 (token rotation)", "FR-7 (MFA)"],
      "constraints": ["max p95 100ms", "stateless"]
    }
  },
  "metrics": {
    "FRs": 23,
    "epics": 4,
    "open_questions": 2
  }
}
```

---

## Rules

1. **Required fields**: `phase`, `domain`, `produced_at`, `produced_by`, `summary`, `artifacts`.
2. **Size limit**: ≤50KB per handoff file. If your handoff would exceed this, you are accumulating too much in memory; split or summarize.
3. **No raw artifact content**: handoff is metadata + decisions + pointers. Full content stays in the artifact files.
4. **Downstream consumers** read only this file plus the specific artifacts they need (listed in `artifacts`).
5. **Versioning**: never edit a handoff; produce a new one with a later timestamp. The latest by `produced_at` wins.

---

## Consumer Pattern

```python
# Pseudocode for any downstream agent
import json, pathlib

handoff_path = pathlib.Path(f"state/handoff/{prev_phase}/{domain}.json")
if not handoff_path.exists():
    raise SystemExit(f"Missing handoff from {prev_phase} for {domain}")

handoff = json.loads(handoff_path.read_text())
# Read only the specific artifacts you need:
for art in handoff["artifacts"]:
    if art["kind"] == "spec":
        spec_text = pathlib.Path(art["path"]).read_text()
```
