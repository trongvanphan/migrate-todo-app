# Sub-Agent: Critical Path Analysis

You compute the critical path through `{{DOMAIN}}`'s bundles and produce a Gantt-style ASCII chart.

---

## Parameters

- `{{DOMAIN}}`

---

## Output Files

- `domains/{{DOMAIN}}/critical-path.md`

---

## Context Budget

Trivial. Reads only `domains/{{DOMAIN}}/tasks.md` and bundle files for dependency lists.

---

## Algorithm

1. Build bundle DAG from `Depends on bundles` fields.
2. Each bundle has a duration in days.
3. Critical path = longest chain in days.
4. Slack per bundle = (longest path ending after this bundle) − (this bundle's earliest finish).

---

## Output

```markdown
# Critical Path — {{DOMAIN}}

**Total bundles**: {N}
**Critical path duration**: {days}
**Critical path bundles**: {comma-separated}

## Gantt (ASCII)

```
Day  →  0   2   4   6   8   10  12  14  16  18  20
B1     [==]
B2          [=]
B3              [==]
B4                  [====]                          (critical)
B5              [==========]                        (critical)
B6                      [======]                    (critical)
B7                              [==========]        (critical)
B8                  [==]
B9                                  [====]
B10                                     [======]    (critical)
```

## Bundles on critical path
| Bundle | Start day | End day | Slack | Owner |
|--------|-----------|---------|-------|-------|

## Bundles with slack (can be deprioritized if needed)
| Bundle | Slack (days) | Can be pushed by |

## Parallelization opportunities

Bundles {X, Y, Z} are independent and can be assigned to different engineers in parallel.

## Risks

- Bundle B5 owner is on PTO weeks 3-4; reassign or sequence around.
- Bundle B7 depends on contract finalization (currently HUMAN GATE open).

## Recommendation

To compress critical path:
- {options}
```

---

## Completion

```
[CRITICAL-PATH-ANALYSIS COMPLETE: {{DOMAIN}}]
Critical path: {days}
Bundles on path: {N}/{total}
File: domains/{{DOMAIN}}/critical-path.md
```
