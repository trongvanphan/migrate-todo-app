# Sub-Agent: Dependency Graph

You build the module-level import graph for the entire legacy codebase. Used by `01-decompose/domain-decompose.md` and `01-decompose/migration-order.md`.

---

## Parameters

- `{{LEGACY_PATH}}`
- `{{LANGUAGE}}` — primary language: `typescript | javascript | python | java | go | ruby | mixed`

---

## Output Files

- `discovery/dependency-graph.json` — adjacency list
- `discovery/dependency-graph.dot` — Graphviz DOT for visualization
- `discovery/dependency-graph.md` — human summary (≤2000 lines)

---

## Context Budget

Stream output to file as you build. Do not accumulate the full graph in agent memory if it has >5000 nodes; emit a coarsened view at directory level.

---

## Strategy by language

| Language | Tool | Command |
|----------|------|---------|
| TypeScript / JavaScript | madge | `npx madge --json --extensions ts,tsx,js,jsx {{LEGACY_PATH}}` |
| Python | pydeps | `pydeps --show-deps --no-output -T json {{LEGACY_PATH}}` (fallback: grep imports) |
| Java | jdeps | `jdeps -dotoutput out -recursive {{LEGACY_PATH}}` |
| Go | go mod graph | `cd {{LEGACY_PATH}} && go mod graph` (intra-module: `go list -deps ./...`) |
| Ruby | rubrowser or grep | `grep -rh "require[ \"']" --include="*.rb"` |
| Mixed | dependency-cruiser | `npx depcruise --output-type json {{LEGACY_PATH}}` |

If tooling is unavailable, fall back to grep-based extraction (less accurate but always works).

---

## Step 1 — Run the dependency tool

Save raw output to `discovery/dependency-graph.raw.json`.

## Step 2 — Coarsen to module level

The raw output is file-level. Coarsen to top-level module (2-deep from `LEGACY_PATH`):

```python
# pseudocode
modules = {}
for file_a, deps in raw.items():
    mod_a = file_a.split('/')[:2]  # e.g., src/billing
    for file_b in deps:
        mod_b = file_b.split('/')[:2]
        if mod_a != mod_b:
            modules.setdefault(mod_a, set()).add(mod_b)
```

Write `discovery/dependency-graph.json`:

```json
{
  "nodes": [
    { "id": "src/auth", "loc": 12000, "files": 84 },
    { "id": "src/billing", "loc": 45000, "files": 320 }
  ],
  "edges": [
    { "from": "src/billing", "to": "src/auth", "weight": 23 }
  ],
  "cycles": [["src/orders", "src/inventory", "src/orders"]],
  "leaves": ["src/notifications"],
  "roots": ["src/auth"]
}
```

## Step 3 — DOT for visualization

```dot
digraph deps {
  rankdir=LR;
  node [shape=box, style=rounded];
  "src/auth" [label="auth\n12k LOC"];
  "src/billing" [label="billing\n45k LOC"];
  "src/billing" -> "src/auth" [label="23"];
}
```

## Step 4 — Markdown summary

```markdown
# Dependency Graph

**Nodes**: {N modules}
**Edges**: {N cross-module imports}
**Cycles**: {N}
**Leaves** (no outbound): {list}
**Roots** (no inbound): {list}

## Top dependencies (highest weight)
| From | To | Weight |
|------|-----|--------|

## Cycles (must be resolved before extraction)
1. {module_a} → {module_b} → {module_a}: shared types in {file}

## Fan-in (most depended-on modules)
| Module | Fan-in count | Implication |
|--------|--------------|-------------|

## Migration order hint
- Migrate leaves first (no outbound deps).
- Auth is usually fan-in heavy → migrate auth first if it has no outbound deps to non-stable modules.
- Break cycles before decomposing.
```

---

## Completion

```
[DEPENDENCY-GRAPH COMPLETE]
Nodes: {N}, Edges: {N}, Cycles: {N}
Files: discovery/dependency-graph.{json,dot,md}
```
