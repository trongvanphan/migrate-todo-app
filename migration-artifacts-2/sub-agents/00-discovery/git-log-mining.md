# Sub-Agent: Git Log Mining (per timeframe)

You mine git history within a **bounded timeframe** for implicit requirements (bug fixes, edge cases).

---

## Parameters

- `{{LEGACY_PATH}}`
- `{{TIMEFRAME}}` — e.g., `1y`, `2y`, `6m`. Default `1y`.

---

## Output Files

- `discovery/git-findings/{{TIMEFRAME}}.md` (≤2000 lines)

---

## Context Budget

If `--since` window yields >5000 commits, narrow to 6m and run again. Never load full git log.

---

## Scans

```bash
cd "{{LEGACY_PATH}}" || exit 1

# Commit activity summary
git log --since="{{TIMEFRAME}} ago" --pretty=format:"%h %ad %s" --date=short 2>/dev/null | wc -l
git log --since="{{TIMEFRAME}} ago" --pretty=format:"%ad" --date=format:"%Y-%m" 2>/dev/null | sort | uniq -c | tail -24

# Hot files (high churn = high risk)
git log --since="{{TIMEFRAME}} ago" --name-only --pretty=format: 2>/dev/null | grep -v "^$" | sort | uniq -c | sort -rn | head -50

# Top authors
git shortlog -sn --since="{{TIMEFRAME}} ago" 2>/dev/null | head -20

# Bug fix commits — hidden requirements
git log --since="{{TIMEFRAME}} ago" --pretty=format:"%h %s" --grep="fix\|bug\|hotfix\|patch\|incident\|regression" -i 2>/dev/null | head -200

# Edge-case keywords
git log --since="{{TIMEFRAME}} ago" --pretty=format:"%h %s" --grep="edge\|case\|handle\|when\|should\|must\|cannot\|prevent\|validate" -i 2>/dev/null | head -100

# Revert commits — fragile areas
git log --since="{{TIMEFRAME}} ago" --pretty=format:"%h %s" --grep="revert" -i 2>/dev/null | head -50
```

---

## Output Structure

```markdown
# Git Findings — last {{TIMEFRAME}}

**Scanned at**: {ISO}
**Total commits**: {N}
**Active authors**: {N}

## Activity timeline
{month-by-month commit count, ASCII bar}

## Hot files (top 30 by churn)
| Churn | File | Domain (guess) |
|-------|------|----------------|

Use these as risk indicators for migration.

## Top authors
| Author | Commits | Likely expertise |

## Hidden requirements from bug-fix commits

Each line below is a requirement that exists *only* in git history (no design doc, possibly no test):

- {commit-sha} fix: ... → Requirement: "system must {behavior}"
- ...

## Edge cases learned from incidents
{One-liners. Pull from commits matching "incident", "hotfix", "revert".}

## Revert hotspots
| File | Reverts | Why fragile |

## Risk assessment

Based on churn + bug-fix density:
- **High risk** (hot + many bug fixes): {file list}
- **Stable** (low churn): {file list}
```

---

## Completion

```
[GIT-LOG-MINING COMPLETE: {{TIMEFRAME}}]
Commits: {N}, Hot files: {N}, Hidden reqs extracted: {N}
File: discovery/git-findings/{{TIMEFRAME}}.md
```
