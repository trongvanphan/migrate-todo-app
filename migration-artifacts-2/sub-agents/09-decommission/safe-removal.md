# Sub-Agent: Decommission — Safe Removal

Gate 4 (final). Remove legacy code in stages. Each stage is its own PR with explicit rollback.

---

## Parameters

- `{{DOMAIN}}`

---

## Output Files

- `decommission/{{DOMAIN}}/removal-plan.md`
- 3 PRs (one per stage)
- Final state update

---

## Context Budget

See `sub-agents/_shared/context-budget-rules.md`. Read only the inputs explicitly listed in Parameters; do not load full discovery dumps.

---

## Preconditions

All three earlier gates passed (state shows `decommission_gate_1..3 == "pass"`).

---

## Stages

### Stage A — Feature-flag-disable

The `{{DOMAIN}}.routing` flag is hard-coded to `new`. The kill-switch is removed. Legacy backend is taken out of load balancer rotation.

PR: `feat({{DOMAIN}}): disable legacy routing fallback`

```diff
- if (await ld.boolVariation('{{DOMAIN}}.kill-switch', ctx, false)) return legacy(req);
+ // legacy routing removed post-decommission
```

Remove the legacy routing config rules (`domains/{{DOMAIN}}/strangler/routing.{conf|tf|yaml}` → delete or simplify).

**Soak: 30 days**. If during this window anyone needs to roll back, the only path is reverting this PR + reactivating the LB. After 30 days, proceed.

### Stage B — Soft delete

Move legacy code to `legacy/archive/{{DOMAIN}}/`. Code is no longer built or deployed.

PR: `chore({{DOMAIN}}): soft-delete legacy code (archive only)`

```bash
mkdir -p legacy/archive/{{DOMAIN}}
git mv src/legacy/{{DOMAIN}}/* legacy/archive/{{DOMAIN}}/
# Remove from build config (package.json workspaces, go.work, Cargo.toml, etc.)
# Update CI to skip archive/
```

Update `.gitignore` of build outputs. Update `CODEOWNERS` (archive owned by `org/archived`).

**Soak: 30 days**.

### Stage C — Hard delete

PR: `chore({{DOMAIN}}): remove legacy code from archive`

```bash
git rm -r legacy/archive/{{DOMAIN}}/
```

Tag the commit before deletion:
```bash
git tag legacy-{{DOMAIN}}-pre-removal-$(date +%Y%m%d)
git push origin --tags
```

Snapshot is still retained in cold storage per Gate 3 manifest (7-year retention default).

---

## Output

```markdown
# Decommission Gate 4 — Safe Removal — {{DOMAIN}}

## Stage progression
| Stage | Status | PR | Date | Soak end |
|-------|--------|------|------|----------|
| A flag-disable | done | #{pr} | 2026-04-01 | 2026-05-01 |
| B soft-delete  | done | #{pr} | 2026-05-02 | 2026-06-01 |
| C hard-delete  | done | #{pr} | 2026-06-02 | — |

## Tags
- legacy-{{DOMAIN}}-pre-removal-{YYYYMMDD}

## Cold storage retention
{from Gate 3 manifest}

## Rollback
- After Stage A: revert PR + restore LB rotation.
- After Stage B: revert PR (moves files back from archive).
- After Stage C: restore from git tag {tag}.
- After cold-storage expiration: not recoverable. Hence the long retention.
```

---

## State Update

```json
{
  "domains[{{DOMAIN}}].status": "decommissioned",
  "domains[{{DOMAIN}}].decommission_completed_at": "{ISO}"
}
```

Append `"decommission"` to `phases_complete` if all migration-target domains are now decommissioned.

---

## Completion

```
[DECOMMISSION-SAFE-REMOVAL: {{DOMAIN}}]
Stages: A done, B done, C done
Final state: decommissioned
File: decommission/{{DOMAIN}}/removal-plan.md

DOMAIN {{DOMAIN}} MIGRATION COMPLETE.
```
