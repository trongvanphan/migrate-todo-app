# Sub-Agent: Code Map Scan (per module)

You scan **one module** at a time and produce a bounded code-map file. Multiple instances of this agent run in parallel (cap=8), one per top-level module.

Do not scan more than one module. Do not write application code.

---

## Parameters

- `{{LEGACY_PATH}}` — absolute path to legacy application root (monolith, multi-package repo, or single-package app)
- `{{MODULE}}` — relative subdirectory (e.g., `src/billing`, `lib/orders`, `apps/web`)

---

## Output Files

- `discovery/modules/{{MODULE}}/code-map.md` (≤2000 lines; summary + sample if larger)
- `state/handoff/discovery/_module-{{MODULE_SLUG}}.json` (lightweight metadata)

Create directories if needed. `{{MODULE_SLUG}}` = `{{MODULE}}` with `/` replaced by `__`.

---

## Context Budget

See `_shared/context-budget-rules.md`. **Do not exceed 50K LOC of input.** If `{{MODULE}}` is larger, emit a directive to split into sub-modules and STOP.

---

## Pre-Check

```bash
LOC=$(find "{{LEGACY_PATH}}/{{MODULE}}" -type f \( -name "*.ts" -o -name "*.js" -o -name "*.py" -o -name "*.rb" -o -name "*.java" -o -name "*.go" -o -name "*.kt" -o -name "*.cs" \) -not -path "*/node_modules/*" -not -path "*/.git/*" -not -path "*/dist/*" -not -path "*/target/*" -not -path "*/vendor/*" 2>/dev/null | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}')
echo "Module LOC: $LOC"
```

If `LOC > 50000`: STOP. Write `discovery/modules/{{MODULE}}/_SPLIT_REQUIRED.md` listing subdirectories and their LOC; emit completion message indicating split is needed. Do NOT proceed with the full scan.

---

## Step 1 — Structure

```bash
find "{{LEGACY_PATH}}/{{MODULE}}" -maxdepth 4 -type d -not -path "*/node_modules/*" -not -path "*/.git/*" | sort
find "{{LEGACY_PATH}}/{{MODULE}}" -type f -not -path "*/node_modules/*" -not -path "*/.git/*" -not -path "*/dist/*" | sed 's/.*\.//' | sort | uniq -c | sort -rn | head -20
```

## Step 2 — LOC per subdir

```bash
find "{{LEGACY_PATH}}/{{MODULE}}" -maxdepth 2 -type d -not -path "*/node_modules/*" | while read d; do
  loc=$(find "$d" -maxdepth 1 -type f \( -name "*.ts" -o -name "*.js" -o -name "*.py" -o -name "*.java" -o -name "*.go" \) 2>/dev/null | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}')
  echo "$loc $d"
done | sort -rn | head -20
```

## Step 3 — Entry points

```bash
find "{{LEGACY_PATH}}/{{MODULE}}" -maxdepth 3 -type f \( -name "main.*" -o -name "index.*" -o -name "app.*" -o -name "server.*" -o -name "*Application.java" \) -not -path "*/node_modules/*" 2>/dev/null
```

## Step 4 — External imports (count, not list)

```bash
grep -rho "^import [^;]*\|^from [^ ]*\|require([^)]*)" "{{LEGACY_PATH}}/{{MODULE}}" --include="*.ts" --include="*.js" --include="*.py" --include="*.java" 2>/dev/null | grep -v "^import \./\|^import \.\./\|^from \." | sort | uniq -c | sort -rn | head -30
```

---

## Output

Write `discovery/modules/{{MODULE}}/code-map.md`:

```markdown
# Code Map — {{MODULE}}

**LOC**: {N}
**Files**: {N}
**Languages**: {detected, primary first}
**Scanned at**: {ISO timestamp}

## Subdirectories (top 20 by LOC)
| Path | LOC | Notable contents |
|------|-----|------------------|
| ... |

## Entry points
| File | Purpose |
|------|---------|

## Top external dependencies (by import count)
| Library | Count | Likely purpose |
|---------|-------|----------------|

## Notable file types
| Extension | Count |
|-----------|-------|

## Risks / Notes
- {one-liners flagging anything unusual: huge files, deeply nested dirs, mixed languages}
```

Then write `state/handoff/discovery/_module-{{MODULE_SLUG}}.json`:

```json
{
  "phase": "discovery",
  "domain": null,
  "module": "{{MODULE}}",
  "produced_at": "{ISO}",
  "produced_by": "sub-agents/00-discovery/code-map-scan.md",
  "summary": "Module {{MODULE}}: {N} LOC, primary language {lang}, entry points at {paths}",
  "metrics": { "loc": N, "files": N, "subdirs": N },
  "artifacts": [{ "path": "discovery/modules/{{MODULE}}/code-map.md", "kind": "code-map", "loc": N }]
}
```

---

## Completion

```
[CODE-MAP-SCAN COMPLETE: {{MODULE}}]
LOC: {N}
File: discovery/modules/{{MODULE}}/code-map.md
Handoff: state/handoff/discovery/_module-{{MODULE_SLUG}}.json
```
